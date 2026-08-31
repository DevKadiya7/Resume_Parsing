import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/resumeService", () => ({
  listResumes: vi.fn(),
  searchResumes: vi.fn(),
  deleteResume: vi.fn(),
  parseResume: vi.fn(),
  downloadResume: vi.fn(),
}));
vi.mock("../services/classificationService", () => ({
  classifyResume: vi.fn(),
}));

const { listResumes, searchResumes, deleteResume } = await import("../services/resumeService");
const { classifyResume } = await import("../services/classificationService");
const ResumeList = (await import("../pages/ResumeList.jsx")).default;
const { CLASSIFICATION_RESULT, renderWithProviders } = await import("./utils.jsx");

const RESUME = {
  id: "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  filename: "jane_doe_resume.pdf",
  status: "UPLOADED",
  file_size: 245678,
  content_type: "application/pdf",
  is_parsed: true,
  created_at: "2026-08-05T10:15:30Z",
  updated_at: "2026-08-05T10:15:35Z",
};

const PAGE = { page: 1, page_size: 10, total: 1, items: [RESUME] };

describe("ResumeList", () => {
  beforeEach(() => {
    listResumes.mockResolvedValue(PAGE);
    searchResumes.mockResolvedValue(PAGE);
    deleteResume.mockResolvedValue({});
    classifyResume.mockResolvedValue(CLASSIFICATION_RESULT);
  });

  it("renders resumes returned by the API", async () => {
    renderWithProviders(<ResumeList />);

    expect(await screen.findByText("jane_doe_resume.pdf")).toBeInTheDocument();
    expect(listResumes).toHaveBeenCalled();
  });

  it("shows an empty state when there are no resumes", async () => {
    listResumes.mockResolvedValue({ page: 1, page_size: 10, total: 0, items: [] });
    renderWithProviders(<ResumeList />);

    expect(await screen.findByText(/no resumes found/i)).toBeInTheDocument();
  });

  it("shows an error message when loading fails", async () => {
    listResumes.mockRejectedValue({ message: "Could not reach the server." });
    renderWithProviders(<ResumeList />);

    expect(await screen.findByText(/could not reach the server/i)).toBeInTheDocument();
  });

  it("searches through the backend when a query is typed", async () => {
    renderWithProviders(<ResumeList />);
    await screen.findByText("jane_doe_resume.pdf");

    await userEvent.type(screen.getByPlaceholderText(/quick search by name/i), "jane");

    // Debounced by 400ms in the page.
    await waitFor(
      () => expect(searchResumes).toHaveBeenCalledWith(expect.objectContaining({ name: "jane" })),
      { timeout: 2000 },
    );
  });

  it("classifies a row and shows the predicted role in the table", async () => {
    renderWithProviders(<ResumeList />);
    await screen.findByText("jane_doe_resume.pdf");

    await userEvent.click(screen.getByTitle(/classify with ai/i));

    await waitFor(() => expect(classifyResume).toHaveBeenCalledWith(RESUME.id));
    expect(await screen.findByText("Data Engineer")).toBeInTheDocument();
    expect(screen.getByText("8.1%")).toBeInTheDocument();
  });

  it("shows a dash in the AI Role column before classification", async () => {
    renderWithProviders(<ResumeList />);
    await screen.findByText("jane_doe_resume.pdf");

    const row = screen.getByText("jane_doe_resume.pdf").closest("tr");
    expect(within(row).getByText("—")).toBeInTheDocument();
  });

  it("reports a classification failure without breaking the table", async () => {
    classifyResume.mockRejectedValue({ message: "Service unavailable." });
    renderWithProviders(<ResumeList />);
    await screen.findByText("jane_doe_resume.pdf");

    await userEvent.click(screen.getByTitle(/classify with ai/i));

    await waitFor(() => expect(classifyResume).toHaveBeenCalled());
    expect(screen.getByText("jane_doe_resume.pdf")).toBeInTheDocument();
  });

  it("deletes a resume after confirmation", async () => {
    renderWithProviders(<ResumeList />);
    await screen.findByText("jane_doe_resume.pdf");

    await userEvent.click(screen.getByTitle(/delete resume/i));
    await userEvent.click(await screen.findByRole("button", { name: /^delete$/i }));

    await waitFor(() => expect(deleteResume).toHaveBeenCalledWith(RESUME.id));
  });
});
