/** Formats an ISO datetime/date string for display; returns "—" for empty input. */
export function formatDate(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/** Formats an ISO datetime string with a time component. */
export function formatDateTime(value) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/** Formats a `start - end` (or `start - Present`) date range for education/experience entries. */
export function formatDateRange(start, end, isCurrent) {
  const startLabel = formatDate(start);
  if (isCurrent) return `${startLabel} — Present`;
  if (!end) return startLabel;
  return `${startLabel} — ${formatDate(end)}`;
}
