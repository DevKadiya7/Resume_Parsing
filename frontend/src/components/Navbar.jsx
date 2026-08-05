import { FiMenu, FiUploadCloud } from "react-icons/fi";
import { Link } from "react-router-dom";

export default function Navbar({ onToggleSidebar }) {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation"
          className="rounded-lg p-2 text-slate-500 hover:bg-slate-100 lg:hidden"
        >
          <FiMenu className="h-5 w-5" />
        </button>
        <Link to="/" className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary-600 text-sm font-bold text-white">
            R
          </span>
          <span className="hidden text-base font-semibold text-slate-900 sm:inline">
            Resume Parsing Service
          </span>
        </Link>
      </div>

      <Link
        to="/upload"
        className="flex items-center gap-2 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-primary-700 sm:px-4"
      >
        <FiUploadCloud className="h-4 w-4" />
        <span className="hidden sm:inline">Upload Resume</span>
      </Link>
    </header>
  );
}
