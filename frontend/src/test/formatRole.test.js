import { describe, expect, it } from "vitest";

import { formatConfidence, formatRoleLabel } from "../utils/formatRole";

describe("formatRoleLabel", () => {
  it("humanizes the model's screaming-kebab labels", () => {
    expect(formatRoleLabel("DATA-ENGINEER")).toBe("Data Engineer");
    expect(formatRoleLabel("INFORMATION-TECHNOLOGY")).toBe("Information Technology");
    expect(formatRoleLabel("HR")).toBe("Hr");
  });

  it("handles underscores and extra separators", () => {
    expect(formatRoleLabel("FULLSTACK_DEVELOPER")).toBe("Fullstack Developer");
    expect(formatRoleLabel("BUSINESS--DEVELOPMENT")).toBe("Business Development");
  });

  it("falls back to a dash for missing values", () => {
    expect(formatRoleLabel("")).toBe("—");
    expect(formatRoleLabel(null)).toBe("—");
    expect(formatRoleLabel(undefined)).toBe("—");
  });
});

describe("formatConfidence", () => {
  it("renders a fraction as a one-decimal percentage", () => {
    expect(formatConfidence(0.081383)).toBe("8.1%");
    expect(formatConfidence(0.924)).toBe("92.4%");
    expect(formatConfidence(1)).toBe("100.0%");
    expect(formatConfidence(0)).toBe("0.0%");
  });

  it("falls back to a dash for non-numeric values", () => {
    expect(formatConfidence(null)).toBe("—");
    expect(formatConfidence(undefined)).toBe("—");
    expect(formatConfidence(Number.NaN)).toBe("—");
  });
});
