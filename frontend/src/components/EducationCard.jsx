import { FiBookOpen } from "react-icons/fi";

import { formatDateRange } from "../utils/formatDate";

export default function EducationCard({ education }) {
  const { institution, degree, field_of_study: fieldOfStudy, start_date, end_date, grade } =
    education;

  return (
    <div className="flex gap-3 rounded-lg border border-slate-200 p-4">
      <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
        <FiBookOpen className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-slate-800">
          {degree || "Degree not specified"}
          {fieldOfStudy && <span className="text-slate-500"> · {fieldOfStudy}</span>}
        </p>
        <p className="text-sm text-slate-600">{institution || "Institution not specified"}</p>
        <p className="mt-1 text-xs text-slate-400">
          {formatDateRange(start_date, end_date, false)}
          {grade && ` · Grade: ${grade}`}
        </p>
      </div>
    </div>
  );
}
