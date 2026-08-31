import { FiInfo, FiTrendingUp } from "react-icons/fi";
import { Link } from "react-router-dom";

import PageHeader from "../components/PageHeader.jsx";

/**
 * Placeholder for resume-to-job-description ranking.
 *
 * The backend exposes no matching endpoint — `/api/v1/resumes/*` provides
 * upload, parse, list, search, statistics, download, delete, and classify,
 * and nothing that scores a resume against a job description. Rather than
 * render an interface that produces invented match percentages, this page
 * states plainly that the capability does not exist yet and points at the
 * search and classification features that do.
 *
 * The layout below is deliberately the real one this page would use, so
 * wiring it up later is a matter of replacing the notice with results.
 */
export default function CandidateRanking() {
  return (
    <div>
      <PageHeader
        title="Candidate Ranking"
        subtitle="Rank candidates against a job description."
      />

      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
        <div className="flex items-start gap-3 rounded-lg border border-blue-200 bg-blue-50 p-4">
          <FiInfo className="mt-0.5 h-5 w-5 shrink-0 text-blue-600" />
          <div>
            <h2 className="text-sm font-semibold text-blue-900">
              Job-description matching is not available yet
            </h2>
            <p className="mt-1 text-sm leading-relaxed text-blue-800">
              This feature needs a backend endpoint that scores each resume against a job
              description. That endpoint has not been built, and this page will not show
              estimated or placeholder scores in its absence — a ranking that looks real but
              is not would be worse than no ranking at all.
            </p>
          </div>
        </div>

        <div className="mt-6">
          <h3 className="text-sm font-semibold text-slate-800">What you can use today</h3>
          <ul className="mt-3 space-y-2.5 text-sm text-slate-600">
            <li className="flex items-start gap-2">
              <FiTrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-primary-600" />
              <span>
                <Link to="/resumes" className="font-medium text-primary-700 hover:underline">
                  AI role classification
                </Link>{" "}
                — predict each candidate&apos;s most likely role, with confidence scores.
              </span>
            </li>
            <li className="flex items-start gap-2">
              <FiTrendingUp className="mt-0.5 h-4 w-4 shrink-0 text-primary-600" />
              <span>
                <Link to="/search" className="font-medium text-primary-700 hover:underline">
                  Multi-field search
                </Link>{" "}
                — filter candidates by skill, company, degree, college, name, or email.
              </span>
            </li>
          </ul>
        </div>

        <p className="mt-6 border-t border-slate-100 pt-4 text-xs text-slate-400">
          To enable this page, add a matching endpoint to the backend and point it at a
          scoring service; the ranking table can then replace this notice.
        </p>
      </div>
    </div>
  );
}
