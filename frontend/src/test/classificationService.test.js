import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("../services/api", () => ({
  default: { post: vi.fn() },
}));

const api = (await import("../services/api")).default;
const { classifyResume } = await import("../services/classificationService");

describe("classifyResume", () => {
  beforeEach(() => {
    api.post.mockResolvedValue({ data: { predicted_role: "DATA-ENGINEER" } });
  });

  it("posts to the resume's classify endpoint", async () => {
    await classifyResume("abc-123");

    expect(api.post).toHaveBeenCalledWith("/resumes/abc-123/classify", null, {
      params: { top_k: 3 },
    });
  });

  it("passes a custom top_k through as a query parameter", async () => {
    await classifyResume("abc-123", 5);

    expect(api.post).toHaveBeenCalledWith("/resumes/abc-123/classify", null, {
      params: { top_k: 5 },
    });
  });

  it("unwraps the response body", async () => {
    const result = await classifyResume("abc-123");
    expect(result).toEqual({ predicted_role: "DATA-ENGINEER" });
  });

  it("propagates errors so callers can surface them", async () => {
    api.post.mockRejectedValue({ status: 503, message: "unavailable" });

    await expect(classifyResume("abc-123")).rejects.toMatchObject({ status: 503 });
  });
});
