import { SORT_FIELDS, SORT_ORDERS } from "../utils/constants";

const TRISTATE_OPTIONS = [
  { value: "", label: "Any" },
  { value: "true", label: "Yes" },
  { value: "false", label: "No" },
];

function Select({ label, value, options, onChange }) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-slate-500">
      {label}
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-sm text-slate-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Structural filters + sort controls for the Resume List page. */
export default function FilterPanel({ filters, onChange }) {
  const patch = (key) => (value) => onChange({ ...filters, [key]: value });

  return (
    <div className="flex flex-wrap items-end gap-4 border-b border-slate-200 bg-slate-50/60 px-4 py-3">
      <Select
        label="Parsed"
        value={filters.parsed}
        options={TRISTATE_OPTIONS}
        onChange={patch("parsed")}
      />
      <Select
        label="Has experience"
        value={filters.has_experience}
        options={TRISTATE_OPTIONS}
        onChange={patch("has_experience")}
      />
      <Select
        label="Has projects"
        value={filters.has_projects}
        options={TRISTATE_OPTIONS}
        onChange={patch("has_projects")}
      />
      <Select
        label="Sort by"
        value={filters.sort}
        options={SORT_FIELDS}
        onChange={patch("sort")}
      />
      <Select
        label="Order"
        value={filters.order}
        options={SORT_ORDERS}
        onChange={patch("order")}
      />
    </div>
  );
}
