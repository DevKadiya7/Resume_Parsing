import { createContext } from "react";

// Split from ToastContext.jsx so that file exports only the Provider
// component (better for React Fast Refresh during development).
export const ToastContext = createContext(null);
