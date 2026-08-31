import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/resumeService", () => ({
  getResumeDetails: vi.fn(),
  deleteResume: vi.fn(),
  downloadResume: vi.fn(),
  parseResume: vi.fn(),
}));
vi.mock("../services/classificationService", () => ({
  classifyResume: vi.fn(),
}));

const { getResumeDetails } = await import("../services/resumeService");
const { classifyResume } = await import("../services/classificationService");
const ResumeDetails = (await import("../pages/ResumeDetails.jsx")).default;
const { CLASSIFICATION_RESULT, RESUME_DETAILS, renderWithProviders } = await import("./utils.jsx");

const RESUME_ID = RESUME_DETAILS.resume.id;

function renderPage() {
  return renderWithProviders(<ResumeDetails />, {
    route: `/resumes/${RESUME_ID}`,
    path: "/resumes/:id",
  });
}

describe("ResumeDetails", () => {
  beforeEach(() => {
    getResumeDetails.mockResolvedValue(RESUME_DETAILS);
    classifyResume.mockResolvedValue(CLASSIFICATION_RESULT);
  });

  it("renders parsed resume data across every section", async () => {
    renderPage();

    expect(await screen.findByText("jane_doe_resume.pdf")).toBeInTheDocument();
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
    expect(screen.getByText("jane.doe@example.com")).toBeInTheDocument();
    expect(screen.getByText("San Francisco, CA")).toBeInTheDocument();
    // "Python" appears both as a skill badge and in the project's tech list.
    expect(screen.getAllByText("Python").length).toBeGreaterThan(0);
    expect(screen.getByText(/MIT/)).toBeInTheDocument();
    expect(screen.getByText(/Google/)).toBeInTheDocument();
    expect(screen.getByText(/Resume Parser/)).toBeInTheDocument();
    expect(screen.getByText(/AWS Certified Solutions Architect/)).toBeInTheDocument();
  });

  it("shows a loading state before data arrives", () => {
    getResumeDetails.mockReturnValue(new Promise(() => {}));
    renderPage();

    expect(screen.getByRole("status", { name: /loading/i })).toBeInTheDocument();
  });

  it("shows an error state when the API fails", async () => {
    getResumeDetails.mockRejectedValue({ message: "Could not reach the server." });
    renderPage();

    expect(await screen.findByText(/resume not found/i)).toBeInTheDocument();
    expect(screen.getByText(/could not reach the server/i)).toBeInTheDocument();
  });

  it("renders empty-section messages when parsed data is empty", async () => {
    getResumeDetails.mockResolvedValue({
      ...RESUME_DETAILS,
      parsed: {
        personal_info: {},
        skills: [],
        education: [],
        experience: [],
        projects: [],
        certifications: [],
        social_profiles: [],
      },
    });
    renderPage();

    expect(await screen.findByText(/no skills detected/i)).toBeInTheDocument();
    expect(screen.getByText(/no education entries detected/i)).toBeInTheDocument();
    expect(screen.getByText(/no experience entries detected/i)).toBeInTheDocument();
    expect(screen.getByText(/no projects detected/i)).toBeInTheDocument();
    expect(screen.getByText(/no certifications detected/i)).toBeInTheDocument();
  });

  it("prompts to parse when the resume has not been parsed", async () => {
    getResumeDetails.mockResolvedValue({
      resume: { ...RESUME_DETAILS.resume, is_parsed: false },
      parsed: null,
    });
    renderPage();

    expect(await screen.findByText(/not parsed yet/i)).toBeInTheDocument();
  });

  it("classifies on demand and renders the real prediction", async () => {
    renderPage();
    await screen.findByText("jane_doe_resume.pdf");

    await userEvent.click(screen.getByRole("button", { name: /classify resume/i }));

    await waitFor(() => expect(classifyResume).toHaveBeenCalledWith(RESUME_ID, 3));
    // "Data Engineer" legitimately renders twice: as the panel's headline
    // and as the first row of "Top predictions".
    expect(await screen.findAllByText("Data Engineer")).toHaveLength(2);
    expect(screen.getAllByText("8.1%").length).toBeGreaterThan(0);
  });

  it("does not classify automatically on page load", async () => {
    renderPage();
    await screen.findByText("jane_doe_resume.pdf");

    expect(classifyResume).not.toHaveBeenCalled();
  });

  it("surfaces a classification failure without breaking the page", async () => {
    classifyResume.mockRejectedValue({
      status: 503,
      message: "Resume classification service is currently unavailable.",
    });
    renderPage();
    await screen.findByText("jane_doe_resume.pdf");

    await userEvent.click(screen.getByRole("button", { name: /classify resume/i }));

    expect(await screen.findByText(/unable to classify this resume/i)).toBeInTheDocument();
    // The rest of the resume is still rendered.
    expect(screen.getByText("Jane Doe")).toBeInTheDocument();
  });

  it("offers classification even when the resume is not parsed", async () => {
    getResumeDetails.mockResolvedValue({
      resume: { ...RESUME_DETAILS.resume, is_parsed: false },
      parsed: null,
    });
    renderPage();
    await screen.findByText(/not parsed yet/i);

    expect(screen.getByRole("button", { name: /classify resume/i })).toBeInTheDocument();
  });
});
