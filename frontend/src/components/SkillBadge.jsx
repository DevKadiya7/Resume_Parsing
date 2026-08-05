export default function SkillBadge({ skill }) {
  return (
    <span className="inline-flex items-center rounded-md bg-primary-50 px-2.5 py-1 text-xs font-medium text-primary-700 ring-1 ring-inset ring-primary-600/20">
      {skill}
    </span>
  );
}
