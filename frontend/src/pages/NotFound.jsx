import { FiAlertTriangle } from "react-icons/fi";
import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <FiAlertTriangle className="mb-4 h-12 w-12 text-slate-300" />
      <h1 className="text-2xl font-semibold text-slate-900">Page not found</h1>
      <p className="mt-2 text-sm text-slate-500">
        The page you&rsquo;re looking for doesn&rsquo;t exist.
      </p>
      <Link
        to="/"
        className="mt-6 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}
