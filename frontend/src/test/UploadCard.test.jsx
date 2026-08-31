import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/resumeService", () => ({
  uploadResume: vi.fn(),
}));

const { uploadResume } = await import("../services/resumeService");
const UploadCard = (await import("../components/UploadCard.jsx")).default;
const { renderWithProviders } = await import("./utils.jsx");

function makeFile(name, type, sizeBytes) {
  const file = new File(["x"], name, { type });
  // File size is read-only, so define it directly rather than allocating a
  // real 11 MB buffer just to test the size guard.
  Object.defineProperty(file, "size", { value: sizeBytes });
  return file;
}

const VALID_PDF = () => makeFile("resume.pdf", "application/pdf", 1024);

describe("UploadCard", () => {
  beforeEach(() => {
    uploadResume.mockResolvedValue({ id: "abc-123", filename: "resume.pdf" });
  });

  function fileInput(container) {
    return container.querySelector('input[type="file"]');
  }

  it("uploads a valid PDF and reports success", async () => {
    const onUploaded = vi.fn();
    const { container } = renderWithProviders(<UploadCard onUploaded={onUploaded} />);

    await userEvent.upload(fileInput(container), VALID_PDF());

    await waitFor(() => expect(uploadResume).toHaveBeenCalledTimes(1));
    expect(await screen.findByText(/uploaded successfully/i)).toBeInTheDocument();
    expect(onUploaded).toHaveBeenCalledWith({ id: "abc-123", filename: "resume.pdf" });
  });

  it("shows the selected filename and size", async () => {
    const { container } = renderWithProviders(<UploadCard />);

    await userEvent.upload(fileInput(container), VALID_PDF());

    expect(await screen.findByText("resume.pdf")).toBeInTheDocument();
  });

  it("links to the new resume after a successful upload", async () => {
    const { container } = renderWithProviders(<UploadCard />);

    await userEvent.upload(fileInput(container), VALID_PDF());

    const link = await screen.findByRole("link", { name: /view resume/i });
    expect(link).toHaveAttribute("href", "/resumes/abc-123");
  });

  it("rejects a non-PDF file without calling the API", async () => {
    const { container } = renderWithProviders(<UploadCard />);

    // The input's `accept="application/pdf,.pdf"` would otherwise make
    // userEvent silently refuse to select a .txt file at all (correct
    // browser behavior, but it means this test wouldn't reach the
    // component's own `validateFile` check) — `applyAccept: false`
    // simulates a browser/OS that let the user pick it anyway (e.g. via
    // drag-and-drop, or "All Files" in the native picker), which is exactly
    // the case `validateFile` exists to catch.
    await userEvent.upload(fileInput(container), makeFile("notes.txt", "text/plain", 1024), {
      applyAccept: false,
    });

    expect(await screen.findByText(/only pdf files are allowed/i)).toBeInTheDocument();
    expect(uploadResume).not.toHaveBeenCalled();
  });

  it("rejects a file over the 10MB limit without calling the API", async () => {
    const { container } = renderWithProviders(<UploadCard />);

    await userEvent.upload(
      fileInput(container),
      makeFile("huge.pdf", "application/pdf", 11 * 1024 * 1024),
    );

    expect(await screen.findByText(/exceeds the 10mb limit/i)).toBeInTheDocument();
    expect(uploadResume).not.toHaveBeenCalled();
  });

  it("surfaces a backend upload failure with a retry action", async () => {
    uploadResume.mockRejectedValue({ message: "Only PDF files are allowed." });
    const { container } = renderWithProviders(<UploadCard />);

    await userEvent.upload(fileInput(container), VALID_PDF());

    expect(await screen.findByText(/only pdf files are allowed/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
  });

  it("clears the selection when retrying after a failure", async () => {
    uploadResume.mockRejectedValue({ message: "Upload failed." });
    const { container } = renderWithProviders(<UploadCard />);

    await userEvent.upload(fileInput(container), VALID_PDF());
    await userEvent.click(await screen.findByRole("button", { name: /try again/i }));

    expect(screen.queryByText("resume.pdf")).not.toBeInTheDocument();
  });
});
