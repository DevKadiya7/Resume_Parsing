import {
  FiChevronDown,
  FiChevronUp,
  FiDownload,
  FiEye,
  FiPlayCircle,
  FiTrash2,
  FiZap,
} from "react-icons/fi";
import { Link } from "react-router-dom";

import { downloadResume } from "../services/resumeService";
import { formatDate } from "../utils/formatDate";
import { formatFileSize } from "../utils/formatFileSize";
import { formatConfidence, formatRoleLabel } from "../utils/formatRole";
import EmptyState from "./EmptyState.jsx";
import LoadingSpinner from "./LoadingSpinner.jsx";
import { ParsedBadge, StatusBadge } from "./StatusBadge.jsx";
import { TableSkeleton } from "./Skeleton.jsx";

const SORTABLE_COLUMNS = [
  { field: "filename", label: "Filename" },
  { field: "created_at", label: "Upload Date" },
  { field: "status", label: "Status" },
];

function SortHeader({ field, label, sort, order, onSortChange }) {
  const isActive = sort === field;
  return (
    <button
      type="button"
      onClick={() => onSortChange(field)}
      className="flex items-center gap-1 text-left text-xs font-semibold uppercase tracking-wide text-slate-500 hover:text-slate-700"
    >
      {label}
      {isActive &&
        (order === "asc" ? (
          <FiChevronUp className="h-3.5 w-3.5" />
        ) : (
          <FiChevronDown className="h-3.5 w-3.5" />
        ))}
    </button>
  );
}

export default function ResumeTable({
  items,
  loading,
  sort,
  order,
  onSortChange,
  onParse,
  onDelete,
  onClassify,
  parsingId,
  classifyingId,
  // Results for rows classified during this session, keyed by resume id. The
  // list endpoint does not return a role — the backend stores classifications
  // nowhere — so this column is populated only by actions taken here rather
  // than by inventing a value.
  classifications = {},
}) {
  if (loading) {
    return (
      <div className="p-5">
        <TableSkeleton rows={6} columns={6} />
      </div>
    );
  }

  if (!items || items.length === 0) {
    return (
      <EmptyState
        title="No resumes found"
        message="Try adjusting your filters, or upload a new resume to get started."
      />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[720px] divide-y divide-slate-200 text-sm">
        <thead className="bg-slate-50">
          <tr>
            {SORTABLE_COLUMNS.map(({ field, label }) =>
              onSortChange ? (
                <th key={field} className="px-4 py-3">
                  <SortHeader
                    field={field}
                    label={label}
                    sort={sort}
                    order={order}
                    onSortChange={onSortChange}
                  />
                </th>
              ) : (
                <th
                  key={field}
                  className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500"
                >
                  {label}
                </th>
              ),
            )}
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              Parsed
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              AI Role
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
              Size
            </th>
            <th className="px-4 py-3 text-right text-xs font-semibold uppercase tracking-wide text-slate-500">
              Actions
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 bg-white">
          {items.map((resume) => (
            <tr key={resume.id} className="hover:bg-slate-50">
              <td className="max-w-[220px] truncate px-4 py-3 font-medium text-slate-700">
                {resume.filename}
              </td>
              <td className="px-4 py-3 text-slate-500">{formatDate(resume.created_at)}</td>
              <td className="px-4 py-3">
                <StatusBadge status={resume.status} />
              </td>
              <td className="px-4 py-3">
                <ParsedBadge isParsed={resume.is_parsed} />
              </td>
              <td className="px-4 py-3">
                {classifications[resume.id] ? (
                  <div className="min-w-0">
                    <p className="truncate text-xs font-medium text-slate-700">
                      {formatRoleLabel(classifications[resume.id].predicted_role)}
                    </p>
                    <p className="tabular-nums text-xs text-slate-400">
                      {formatConfidence(classifications[resume.id].confidence)}
                    </p>
                  </div>
                ) : (
                  <span className="text-xs text-slate-300">—</span>
                )}
              </td>
              <td className="px-4 py-3 text-slate-500">{formatFileSize(resume.file_size)}</td>
              <td className="px-4 py-3">
                <div className="flex items-center justify-end gap-1.5">
                  <button
                    type="button"
                    title="Classify with AI"
                    disabled={classifyingId === resume.id}
                    onClick={() => onClassify(resume.id)}
                    className="rounded-lg p-2 text-slate-500 hover:bg-primary-50 hover:text-primary-600 disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    {classifyingId === resume.id ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <FiZap className="h-4 w-4" />
                    )}
                  </button>
                  <button
                    type="button"
                    title={resume.is_parsed ? "Already parsed" : "Parse resume"}
                    disabled={resume.is_parsed || parsingId === resume.id}
                    onClick={() => onParse(resume.id)}
                    className="rounded-lg p-2 text-slate-500 hover:bg-primary-50 hover:text-primary-600 disabled:cursor-not-allowed disabled:opacity-30"
                  >
                    {parsingId === resume.id ? (
                      <LoadingSpinner size="sm" />
                    ) : (
                      <FiPlayCircle className="h-4 w-4" />
                    )}
                  </button>
                  <Link
                    to={`/resumes/${resume.id}`}
                    title="View details"
                    className="rounded-lg p-2 text-slate-500 hover:bg-primary-50 hover:text-primary-600"
                  >
                    <FiEye className="h-4 w-4" />
                  </Link>
                  <button
                    type="button"
                    title="Download PDF"
                    onClick={() => downloadResume(resume.id)}
                    className="rounded-lg p-2 text-slate-500 hover:bg-primary-50 hover:text-primary-600"
                  >
                    <FiDownload className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    title="Delete resume"
                    onClick={() => onDelete(resume)}
                    className="rounded-lg p-2 text-slate-500 hover:bg-red-50 hover:text-red-600"
                  >
                    <FiTrash2 className="h-4 w-4" />
                  </button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
