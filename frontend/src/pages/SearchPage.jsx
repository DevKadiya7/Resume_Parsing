import { useMemo, useState } from "react";
import { FiSearch, FiX } from "react-icons/fi";
import { useForm } from "react-hook-form";

import ConfirmModal from "../components/ConfirmModal.jsx";
import EmptyState from "../components/EmptyState.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Pagination from "../components/Pagination.jsx";
import ResumeTable from "../components/ResumeTable.jsx";
import { useToast } from "../hooks/useToast";
import { useResumes } from "../hooks/useResumes";
import { deleteResume, parseResume, searchResumes } from "../services/resumeService";
import { SEARCH_FIELDS } from "../utils/constants";

const PAGE_SIZE = 10;
const EMPTY_VALUES = Object.fromEntries(SEARCH_FIELDS.map((field) => [field.name, ""]));

export default function SearchPage() {
  const toast = useToast();
  const { register, handleSubmit, reset, watch } = useForm({ defaultValues: EMPTY_VALUES });
  const [criteria, setCriteria] = useState(null);
  const [page, setPage] = useState(1);
  const [parsingId, setParsingId] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const hasAnyValue = Object.values(watch()).some((value) => value?.trim());

  const queryParams = useMemo(
    () => (criteria ? { ...criteria, page, page_size: PAGE_SIZE } : null),
    [criteria, page],
  );

  const fetcher = useMemo(() => (criteria ? searchResumes : () => Promise.resolve(null)), [
    criteria,
  ]);

  const { items, total, page_size: pageSize, loading, error, refetch } = useResumes(
    fetcher,
    queryParams || {},
  );

  const onSubmit = (values) => {
    const nonEmpty = Object.fromEntries(
      Object.entries(values)
        .map(([key, value]) => [key, value.trim()])
        .filter(([, value]) => value),
    );
    if (Object.keys(nonEmpty).length === 0) {
      toast.error("Enter at least one field to search.");
      return;
    }
    setCriteria(nonEmpty);
    setPage(1);
  };

  const handleClear = () => {
    reset(EMPTY_VALUES);
    setCriteria(null);
    setPage(1);
  };

  const handleParse = async (id) => {
    setParsingId(id);
    try {
      await parseResume(id);
      toast.success("Resume parsed successfully.");
      refetch();
    } catch (err) {
      toast.error(err.message || "Failed to parse resume.");
    } finally {
      setParsingId(null);
    }
  };

  const confirmDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteResume(deleteTarget.id);
      toast.success(`"${deleteTarget.filename}" deleted.`);
      setDeleteTarget(null);
      refetch();
    } catch (err) {
      toast.error(err.message || "Failed to delete resume.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div>
      <PageHeader
        title="Search Resumes"
        subtitle="Find candidates by name, skill, company, degree, college, or email."
      />

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mb-6 grid grid-cols-1 gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-card sm:grid-cols-2 lg:grid-cols-3"
      >
        {SEARCH_FIELDS.map((field) => (
          <label key={field.name} className="flex flex-col gap-1 text-xs font-medium text-slate-500">
            {field.label}
            <input
              type="text"
              {...register(field.name)}
              placeholder={`e.g. ${field.label.toLowerCase()}`}
              className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-700 focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </label>
        ))}

        <div className="flex items-end gap-2 sm:col-span-2 lg:col-span-3">
          <button
            type="submit"
            className="flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
          >
            <FiSearch className="h-4 w-4" />
            Search
          </button>
          {(criteria || hasAnyValue) && (
            <button
              type="button"
              onClick={handleClear}
              className="flex items-center gap-2 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              <FiX className="h-4 w-4" />
              Clear
            </button>
          )}
        </div>
      </form>

      {!criteria ? (
        <EmptyState
          icon={FiSearch}
          title="Search for resumes"
          message="Fill in one or more fields above and press Search."
        />
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card">
          {error ? (
            <p className="p-6 text-sm text-red-600">{error}</p>
          ) : (
            <ResumeTable
              items={items}
              loading={loading}
              onParse={handleParse}
              onDelete={setDeleteTarget}
              parsingId={parsingId}
            />
          )}

          {!loading && !error && total > 0 && (
            <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
          )}
        </div>
      )}

      <ConfirmModal
        open={Boolean(deleteTarget)}
        danger
        title="Delete this resume?"
        message={
          deleteTarget && `"${deleteTarget.filename}" and all of its parsed data will be removed permanently.`
        }
        confirmLabel="Delete"
        loading={deleting}
        onConfirm={confirmDelete}
        onCancel={() => setDeleteTarget(null)}
      />
    </div>
  );
}
