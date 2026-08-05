import { useEffect, useState } from "react";
import { FiCheckCircle, FiClock, FiFileText, FiTrendingUp } from "react-icons/fi";
import { Link } from "react-router-dom";

import EmptyState from "../components/EmptyState.jsx";
import { CardSkeleton, Skeleton } from "../components/Skeleton.jsx";
import SkillBadge from "../components/SkillBadge.jsx";
import StatCard from "../components/StatCard.jsx";
import { ParsedBadge, StatusBadge } from "../components/StatusBadge.jsx";
import { useToast } from "../hooks/useToast";
import { getStatistics, listResumes } from "../services/resumeService";
import { formatDate } from "../utils/formatDate";

export default function Dashboard() {
  const toast = useToast();
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    Promise.all([
      getStatistics(),
      listResumes({ page: 1, page_size: 5, sort: "created_at", order: "desc" }),
    ])
      .then(([statistics, recentPage]) => {
        if (cancelled) return;
        setStats(statistics);
        setRecent(recentPage.items);
      })
      .catch((err) => {
        if (!cancelled) toast.error(err.message || "Failed to load dashboard data.");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-slate-900 sm:text-2xl">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          An overview of everything uploaded and parsed so far.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          <>
            <CardSkeleton />
            <CardSkeleton />
            <CardSkeleton />
          </>
        ) : (
          <>
            <StatCard
              icon={FiFileText}
              label="Total Resumes"
              value={stats?.total_resumes ?? 0}
              accent="primary"
            />
            <StatCard
              icon={FiCheckCircle}
              label="Parsed"
              value={stats?.parsed ?? 0}
              accent="green"
            />
            <StatCard icon={FiClock} label="Pending" value={stats?.pending ?? 0} accent="amber" />
          </>
        )}
      </div>

      <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="mb-4 flex items-center gap-2">
            <FiTrendingUp className="h-4 w-4 text-primary-600" />
            <h2 className="text-sm font-semibold text-slate-800">Top Skills</h2>
          </div>
          {loading ? (
            <div className="flex flex-wrap gap-2">
              {Array.from({ length: 6 }).map((_, i) => (
                <Skeleton key={i} className="h-6 w-16" />
              ))}
            </div>
          ) : stats?.top_skills?.length ? (
            <div className="flex flex-wrap gap-2">
              {stats.top_skills.map((entry) => (
                <div key={entry.skill} className="flex items-center gap-1.5">
                  <SkillBadge skill={entry.skill} />
                  <span className="text-xs text-slate-400">×{entry.count}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-slate-400">No skills recorded yet.</p>
          )}
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-semibold text-slate-800">Recent Uploads</h2>
            <Link to="/resumes" className="text-xs font-medium text-primary-600 hover:underline">
              View all
            </Link>
          </div>

          {loading ? (
            <div className="space-y-3">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-10 w-full" />
              ))}
            </div>
          ) : recent.length === 0 ? (
            <EmptyState
              title="No resumes yet"
              message="Upload your first resume to see it here."
            />
          ) : (
            <ul className="divide-y divide-slate-100">
              {recent.map((resume) => (
                <li key={resume.id} className="flex items-center justify-between py-3">
                  <div className="min-w-0">
                    <Link
                      to={`/resumes/${resume.id}`}
                      className="truncate text-sm font-medium text-slate-700 hover:text-primary-600"
                    >
                      {resume.filename}
                    </Link>
                    <p className="text-xs text-slate-400">{formatDate(resume.created_at)}</p>
                  </div>
                  <div className="flex shrink-0 items-center gap-2">
                    <StatusBadge status={resume.status} />
                    <ParsedBadge isParsed={resume.is_parsed} />
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>
    </div>
  );
}
