import { RESUME_STATUS_STYLES } from "../utils/constants";

export function StatusBadge({ status }) {
  const style = RESUME_STATUS_STYLES[status] || "bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-500/20";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${style}`}>
      {status}
    </span>
  );
}

export function ParsedBadge({ isParsed }) {
  return isParsed ? (
    <span className="inline-flex items-center rounded-full bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700 ring-1 ring-inset ring-green-600/20">
      Parsed
    </span>
  ) : (
    <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700 ring-1 ring-inset ring-amber-600/20">
      Pending
    </span>
  );
}
