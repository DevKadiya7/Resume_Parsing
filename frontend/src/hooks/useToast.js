import { useContext } from "react";

import { ToastContext } from "../context/toastCore.js";

/** Access the global toast API: `toast.success(msg)`, `.error(msg)`, `.info(msg)`. */
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
