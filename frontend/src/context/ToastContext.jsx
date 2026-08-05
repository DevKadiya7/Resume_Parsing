import { useCallback, useState } from "react";

import ToastContainer from "../components/ToastContainer.jsx";
import { ToastContext } from "./toastCore.js";

let nextId = 1;

/**
 * Global toast notifications. A Context is the right fit here (rather than
 * local state per page) because success/error toasts need to be fired from
 * deeply nested components — an upload card, a delete-confirmation flow, a
 * parse action inside a table row — without threading callbacks through
 * every layer in between.
 */
export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);

  const dismiss = useCallback((id) => {
    setToasts((current) => current.filter((toast) => toast.id !== id));
  }, []);

  const show = useCallback(
    (message, type = "info", duration = 4000) => {
      const id = nextId++;
      setToasts((current) => [...current, { id, message, type }]);
      if (duration > 0) {
        setTimeout(() => dismiss(id), duration);
      }
      return id;
    },
    [dismiss],
  );

  const toast = {
    success: (message, duration) => show(message, "success", duration),
    error: (message, duration) => show(message, "error", duration),
    info: (message, duration) => show(message, "info", duration),
  };

  return (
    <ToastContext.Provider value={toast}>
      {children}
      <ToastContainer toasts={toasts} onDismiss={dismiss} />
    </ToastContext.Provider>
  );
}
