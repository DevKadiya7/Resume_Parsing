import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterEach, vi } from "vitest";

// React Testing Library does not auto-clean when `globals` is enabled via a
// config file rather than an explicit import, so unmount between tests to stop
// one test's DOM leaking into the next.
afterEach(() => {
  cleanup();
  vi.clearAllMocks();
});
