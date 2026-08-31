/**
 * The model emits screaming-kebab labels ("DATA-ENGINEER",
 * "INFORMATION-TECHNOLOGY") because that is how the training corpus is
 * labelled. Those are fine as data but wrong in a UI, so they are formatted
 * for display here — never rewritten at the API layer, so what the backend
 * returned stays inspectable.
 */
export function formatRoleLabel(role) {
  if (!role) return "—";
  return role
    .split(/[-_\s]+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
    .join(" ");
}

/** Render a 0..1 confidence as a percentage string, e.g. 0.0814 -> "8.1%". */
export function formatConfidence(confidence) {
  if (typeof confidence !== "number" || Number.isNaN(confidence)) return "—";
  return `${(confidence * 100).toFixed(1)}%`;
}
