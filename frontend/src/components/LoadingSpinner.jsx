const SIZES = {
  sm: "h-4 w-4 border-2",
  md: "h-8 w-8 border-2",
  lg: "h-12 w-12 border-[3px]",
};

export default function LoadingSpinner({ size = "md", className = "" }) {
  return (
    <div
      role="status"
      aria-label="Loading"
      className={`inline-block animate-spin rounded-full border-primary-600 border-t-transparent ${SIZES[size]} ${className}`}
    />
  );
}
