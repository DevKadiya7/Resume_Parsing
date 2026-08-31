// API base URL — must include the /api/v1 prefix (see .env.example).
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

export const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB, mirrors the backend's limit

export const SORT_FIELDS = [
  { value: "created_at", label: "Upload date" },
  { value: "filename", label: "Filename" },
  { value: "status", label: "Status" },
];

export const SORT_ORDERS = [
  { value: "desc", label: "Descending" },
  { value: "asc", label: "Ascending" },
];

export const RESUME_STATUS_STYLES = {
  UPLOADED: "bg-blue-50 text-blue-700 ring-1 ring-inset ring-blue-600/20",
  FAILED: "bg-red-50 text-red-700 ring-1 ring-inset ring-red-600/20",
};

// The backend's /resumes/search endpoint accepts more fields than this
// (job_title, certification, github, linkedin, portfolio, phone) — the
// Search page surfaces exactly the fields called for in the spec.
export const SEARCH_FIELDS = [
  { name: "name", label: "Name" },
  { name: "skill", label: "Skill" },
  { name: "company", label: "Company" },
  { name: "degree", label: "Degree" },
  { name: "college", label: "College" },
  { name: "email", label: "Email" },
];

// How many predictions the classification endpoint returns by default. The
// backend caps top_k at the model's class count (34) and rejects anything
// larger with a 422.
export const DEFAULT_TOP_K = 3;

export const SOCIAL_PLATFORM_LABELS = {
  LINKEDIN: "LinkedIn",
  GITHUB: "GitHub",
  TWITTER: "Twitter",
  MEDIUM: "Medium",
  PORTFOLIO: "Portfolio",
};
