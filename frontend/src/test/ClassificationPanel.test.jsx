import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import ClassificationPanel from "../components/ClassificationPanel.jsx";
import { CLASSIFICATION_RESULT, renderWithProviders } from "./utils.jsx";

describe("ClassificationPanel", () => {
  it("offers a classify action before anything has run", () => {
    renderWithProviders(<ClassificationPanel onClassify={vi.fn()} />);

    expect(screen.getByRole("button", { name: /classify resume/i })).toBeInTheDocument();
    expect(screen.queryByText(/predicted role/i)).not.toBeInTheDocument();
  });

  it("calls onClassify when the button is clicked", async () => {
    const onClassify = vi.fn();
    renderWithProviders(<ClassificationPanel onClassify={onClassify} />);

    await userEvent.click(screen.getByRole("button", { name: /classify resume/i }));

    expect(onClassify).toHaveBeenCalledTimes(1);
  });

  it("shows a loading state while analyzing", () => {
    renderWithProviders(<ClassificationPanel loading onClassify={vi.fn()} />);

    expect(screen.getByText(/analyzing resume/i)).toBeInTheDocument();
    expect(screen.getByRole("status", { name: /loading/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /classify resume/i })).not.toBeInTheDocument();
  });

  it("renders the predicted role and confidence from the API response", () => {
    renderWithProviders(
      <ClassificationPanel result={CLASSIFICATION_RESULT} onClassify={vi.fn()} />,
    );

    // "DATA-ENGINEER" must be humanized for display. It legitimately appears
    // twice — as the headline and as the first top-predictions row.
    expect(screen.getAllByText("Data Engineer")).toHaveLength(2);
    // 0.081383 -> 8.1%
    expect(screen.getAllByText("8.1%").length).toBeGreaterThan(0);
  });

  it("renders every top-K prediction, humanized and with its own score", () => {
    renderWithProviders(
      <ClassificationPanel result={CLASSIFICATION_RESULT} onClassify={vi.fn()} />,
    );

    expect(screen.getByText("Qa Engineer")).toBeInTheDocument();
    expect(screen.getByText("Devops Engineer")).toBeInTheDocument();
    expect(screen.getByText("7.0%")).toBeInTheDocument();
    expect(screen.getByText("5.9%")).toBeInTheDocument();
  });

  it("sizes the confidence bar to the real score, not a rescaled one", () => {
    renderWithProviders(
      <ClassificationPanel result={CLASSIFICATION_RESULT} onClassify={vi.fn()} />,
    );

    const mainBar = screen.getByRole("progressbar", { name: /prediction confidence/i });
    expect(mainBar).toHaveAttribute("aria-valuenow", "8.1");
  });

  it("explains why confidence values look low", () => {
    renderWithProviders(
      <ClassificationPanel result={CLASSIFICATION_RESULT} onClassify={vi.fn()} />,
    );

    expect(screen.getByText(/not calibrated probabilities/i)).toBeInTheDocument();
  });

  it("shows a friendly error with a retry action on failure", async () => {
    const onClassify = vi.fn();
    renderWithProviders(
      <ClassificationPanel
        error="Resume classification service is currently unavailable."
        onClassify={onClassify}
      />,
    );

    expect(screen.getByText(/unable to classify this resume/i)).toBeInTheDocument();
    expect(
      screen.getByText(/resume classification service is currently unavailable/i),
    ).toBeInTheDocument();

    await userEvent.click(screen.getByRole("button", { name: /try again/i }));
    expect(onClassify).toHaveBeenCalledTimes(1);
  });

  it("allows re-running once a result exists", async () => {
    const onClassify = vi.fn();
    renderWithProviders(
      <ClassificationPanel result={CLASSIFICATION_RESULT} onClassify={onClassify} />,
    );

    await userEvent.click(screen.getByRole("button", { name: /re-run/i }));
    expect(onClassify).toHaveBeenCalledTimes(1);
  });
});
