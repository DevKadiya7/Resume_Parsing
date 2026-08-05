import { FiCode } from "react-icons/fi";

import SkillBadge from "./SkillBadge.jsx";

export default function ProjectCard({ project }) {
  const { name, description, technologies } = project;
  const techList = technologies
    ? technologies
        .split(",")
        .map((tech) => tech.trim())
        .filter(Boolean)
    : [];

  return (
    <div className="flex gap-3 rounded-lg border border-slate-200 p-4">
      <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-primary-50 text-primary-600">
        <FiCode className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="font-medium text-slate-800">{name || "Untitled project"}</p>
        {description && <p className="mt-1 text-sm text-slate-600">{description}</p>}
        {techList.length > 0 && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {techList.map((tech) => (
              <SkillBadge key={tech} skill={tech} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
