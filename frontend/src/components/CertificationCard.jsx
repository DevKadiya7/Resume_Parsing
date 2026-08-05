import { FiAward } from "react-icons/fi";

import { formatDate } from "../utils/formatDate";

export default function CertificationCard({ certification }) {
  const { name, issuer, date } = certification;

  return (
    <div className="flex gap-3 rounded-lg border border-slate-200 p-4">
      <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
        <FiAward className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-slate-800">{name || "Certification"}</p>
        <p className="text-sm text-slate-600">{issuer || "Issuer not specified"}</p>
        {date && <p className="mt-1 text-xs text-slate-400">{formatDate(date)}</p>}
      </div>
    </div>
  );
}
