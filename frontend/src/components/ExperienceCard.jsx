import { FiBriefcase } from "react-icons/fi";

import { formatDateRange } from "../utils/formatDate";

export default function ExperienceCard({ experience }) {
  const { company, job_title: jobTitle, location, start_date, end_date, is_current, description } =
    experience;

  return (
    <div className="flex gap-3 rounded-lg border border-slate-200 p-4">
      <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
        <FiBriefcase className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-slate-800">{jobTitle || "Role not specified"}</p>
        <p className="text-sm text-slate-600">
          {company || "Company not specified"}
          {location && <span className="text-slate-400"> · {location}</span>}
        </p>
        <p className="mt-1 text-xs text-slate-400">
          {formatDateRange(start_date, end_date, is_current)}
        </p>
        {description && <p className="mt-2 text-sm text-slate-600">{description}</p>}
      </div>
    </div>
  );
}
