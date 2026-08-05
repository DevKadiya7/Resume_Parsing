import { FiAlertCircle, FiCheckCircle, FiInfo, FiX } from "react-icons/fi";

const STYLES = {
  success: {
    wrapper: "bg-green-50 text-green-800 ring-1 ring-inset ring-green-600/20",
    icon: FiCheckCircle,
    iconClass: "text-green-500",
  },
  error: {
    wrapper: "bg-red-50 text-red-800 ring-1 ring-inset ring-red-600/20",
    icon: FiAlertCircle,
    iconClass: "text-red-500",
  },
  info: {
    wrapper: "bg-blue-50 text-blue-800 ring-1 ring-inset ring-blue-600/20",
    icon: FiInfo,
    iconClass: "text-blue-500",
  },
};

export default function Toast({ message, type = "info", onDismiss }) {
  const style = STYLES[type] || STYLES.info;
  const Icon = style.icon;

  return (
    <div
      role="alert"
      className={`animate-fade-in flex items-start gap-3 rounded-lg px-4 py-3 shadow-lg ${style.wrapper}`}
    >
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${style.iconClass}`} />
      <p className="flex-1 text-sm font-medium">{message}</p>
      <button
        type="button"
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="shrink-0 rounded p-0.5 opacity-60 hover:opacity-100"
      >
        <FiX className="h-4 w-4" />
      </button>
    </div>
  );
}
