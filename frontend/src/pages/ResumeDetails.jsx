import { useCallback, useEffect, useState } from "react";
import {
  FiAward,
  FiBookOpen,
  FiBriefcase,
  FiCode,
  FiDownload,
  FiPlayCircle,
  FiTrash2,
} from "react-icons/fi";
import { useNavigate, useParams } from "react-router-dom";

import CertificationCard from "../components/CertificationCard.jsx";
import ConfirmModal from "../components/ConfirmModal.jsx";
import EducationCard from "../components/EducationCard.jsx";
import EmptyState from "../components/EmptyState.jsx";
import ExperienceCard from "../components/ExperienceCard.jsx";
import LoadingSpinner from "../components/LoadingSpinner.jsx";
import ProjectCard from "../components/ProjectCard.jsx";
import SkillBadge from "../components/SkillBadge.jsx";
import SocialLinks from "../components/SocialLinks.jsx";
import { ParsedBadge, StatusBadge } from "../components/StatusBadge.jsx";
import { useToast } from "../hooks/useToast";
import {
  deleteResume,
  downloadResume,
  getResumeDetails,
  parseResume,
} from "../services/resumeService";
import { formatDateTime } from "../utils/formatDate";
import { formatFileSize } from "../utils/formatFileSize";

function Section({ icon: Icon, title, children }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
      <div className="mb-4 flex items-center gap-2">
        <Icon className="h-4 w-4 text-primary-600" />
        <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
      </div>
      {children}
    </section>
  );
}

export default function ResumeDetails() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [parsing, setParsing] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(() => {
    setLoading(true);
    setError(null);
    getResumeDetails(id)
      .then(setData)
      .catch((err) => setError(err.message || "Failed to load this resume."))
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    load();
  }, [load]);

  const handleParse = async () => {
    setParsing(true);
    try {
      await parseResume(id);
      toast.success("Resume parsed successfully.");
      load();
    } catch (err) {
      toast.error(err.message || "Failed to parse resume.");
    } finally {
      setParsing(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      await deleteResume(id);
      toast.success("Resume deleted.");
      navigate("/resumes");
    } catch (err) {
      toast.error(err.message || "Failed to delete resume.");
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center py-24">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <EmptyState
        title="Resume not found"
        message={error || "This resume doesn't exist or may have been deleted."}
      />
    );
  }

  const { resume, parsed } = data;

  return (
    <div>
      <div className="mb-6 flex flex-col gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-card sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <h1 className="truncate text-lg font-semibold text-slate-900">{resume.filename}</h1>
          <div className="mt-1.5 flex flex-wrap items-center gap-2">
            <StatusBadge status={resume.status} />
            <ParsedBadge isParsed={resume.is_parsed} />
            <span className="text-xs text-slate-400">{formatFileSize(resume.file_size)}</span>
            <span className="text-xs text-slate-400">
              Uploaded {formatDateTime(resume.created_at)}
            </span>
          </div>
        </div>

        <div className="flex shrink-0 flex-wrap gap-2">
          {!resume.is_parsed && (
            <button
              type="button"
              onClick={handleParse}
              disabled={parsing}
              className="flex items-center gap-2 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:opacity-50"
            >
              {parsing ? <LoadingSpinner size="sm" /> : <FiPlayCircle className="h-4 w-4" />}
              Parse
            </button>
          )}
          <button
            type="button"
            onClick={() => downloadResume(resume.id)}
            className="flex items-center gap-2 rounded-lg border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
          >
            <FiDownload className="h-4 w-4" />
            Download
          </button>
          <button
            type="button"
            onClick={() => setConfirmDeleteOpen(true)}
            className="flex items-center gap-2 rounded-lg border border-red-200 px-3 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
          >
            <FiTrash2 className="h-4 w-4" />
            Delete
          </button>
        </div>
      </div>

      {!parsed ? (
        <EmptyState
          icon={FiPlayCircle}
          title="Not parsed yet"
          message="Parse this resume to extract personal info, skills, education, experience, projects, certifications, and social profiles."
        />
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
          <Section icon={FiBookOpen} title="Personal Information">
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Full name</dt>
                <dd className="text-right font-medium text-slate-800">
                  {parsed.personal_info.full_name || "—"}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Email</dt>
                <dd className="text-right font-medium text-slate-800">
                  {parsed.personal_info.email || "—"}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Phone</dt>
                <dd className="text-right font-medium text-slate-800">
                  {parsed.personal_info.phone || "—"}
                </dd>
              </div>
              <div className="flex justify-between gap-4">
                <dt className="text-slate-500">Address</dt>
                <dd className="text-right font-medium text-slate-800">
                  {parsed.personal_info.address || "—"}
                </dd>
              </div>
              {parsed.personal_info.summary && (
                <div className="pt-2">
                  <dt className="mb-1 text-slate-500">Summary</dt>
                  <dd className="text-slate-700">{parsed.personal_info.summary}</dd>
                </div>
              )}
            </dl>

            {parsed.social_profiles.length > 0 && (
              <div className="mt-4 border-t border-slate-100 pt-4">
                <SocialLinks profiles={parsed.social_profiles} />
              </div>
            )}
          </Section>

          <Section icon={FiCode} title="Skills">
            {parsed.skills.length === 0 ? (
              <p className="text-sm text-slate-400">No skills detected.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {parsed.skills.map((skill) => (
                  <SkillBadge key={skill} skill={skill} />
                ))}
              </div>
            )}
          </Section>

          <Section icon={FiBookOpen} title="Education">
            {parsed.education.length === 0 ? (
              <p className="text-sm text-slate-400">No education entries detected.</p>
            ) : (
              <div className="space-y-3">
                {parsed.education.map((education, index) => (
                  <EducationCard key={index} education={education} />
                ))}
              </div>
            )}
          </Section>

          <Section icon={FiBriefcase} title="Experience">
            {parsed.experience.length === 0 ? (
              <p className="text-sm text-slate-400">No experience entries detected.</p>
            ) : (
              <div className="space-y-3">
                {parsed.experience.map((experience, index) => (
                  <ExperienceCard key={index} experience={experience} />
                ))}
              </div>
            )}
          </Section>

          <Section icon={FiCode} title="Projects">
            {parsed.projects.length === 0 ? (
              <p className="text-sm text-slate-400">No projects detected.</p>
            ) : (
              <div className="space-y-3">
                {parsed.projects.map((project, index) => (
                  <ProjectCard key={index} project={project} />
                ))}
              </div>
            )}
          </Section>

          <Section icon={FiAward} title="Certifications">
            {parsed.certifications.length === 0 ? (
              <p className="text-sm text-slate-400">No certifications detected.</p>
            ) : (
              <div className="space-y-3">
                {parsed.certifications.map((certification, index) => (
                  <CertificationCard key={index} certification={certification} />
                ))}
              </div>
            )}
          </Section>
        </div>
      )}

      <ConfirmModal
        open={confirmDeleteOpen}
        danger
        title="Delete this resume?"
        message={`"${resume.filename}" and all of its parsed data will be removed permanently.`}
        confirmLabel="Delete"
        loading={deleting}
        onConfirm={handleDelete}
        onCancel={() => setConfirmDeleteOpen(false)}
      />
    </div>
  );
}
