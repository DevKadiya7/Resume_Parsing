import { useCallback, useMemo, useState } from "react";

import ConfirmModal from "../components/ConfirmModal.jsx";
import FilterPanel from "../components/FilterPanel.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Pagination from "../components/Pagination.jsx";
import ResumeTable from "../components/ResumeTable.jsx";
import SearchBar from "../components/SearchBar.jsx";
import { useToast } from "../hooks/useToast";
import { useDebounce } from "../hooks/useDebounce";
import { useResumes } from "../hooks/useResumes";
import { deleteResume, listResumes, parseResume, searchResumes } from "../services/resumeService";

const PAGE_SIZE = 10;

export default function ResumeList() {
  const toast = useToast();
  const [page, setPage] = useState(1);
  const [searchText, setSearchText] = useState("");
  const [filters, setFilters] = useState({
    parsed: "",
    has_experience: "",
    has_projects: "",
    sort: "created_at",
    order: "desc",
  });
  const [parsingId, setParsingId] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [deleting, setDeleting] = useState(false);

  const debouncedSearch = useDebounce(searchText, 400);

  const queryParams = useMemo(() => {
    const params = {
      page,
      page_size: PAGE_SIZE,
      sort: filters.sort,
      order: filters.order,
    };
    if (filters.parsed !== "") params.parsed = filters.parsed === "true";
    if (filters.has_experience !== "") params.has_experience = filters.has_experience === "true";
    if (filters.has_projects !== "") params.has_projects = filters.has_projects === "true";
    return params;
  }, [page, filters]);

  const fetchPage = useCallback(
    (params) =>
      debouncedSearch
        ? searchResumes({ ...params, name: debouncedSearch })
        : listResumes(params),
    [debouncedSearch],
  );

  const { items, total, page_size: pageSize, loading, error, refetch } = useResumes(
    fetchPage,
    queryParams,
  );

  const handleFilterChange = (next) => {
    setFilters(next);
    setPage(1);
  };

  const handleSearchChange = (value) => {
    setSearchText(value);
    setPage(1);
  };

  const handleSortChange = (field) => {
    setFilters((current) => ({
      ...current,
      sort: field,
      order: current.sort === field && current.order === "asc" ? "desc" : "asc",
    }));
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
        title="Resumes"
        subtitle="Browse, filter, parse, and manage every uploaded resume."
        actions={
          <SearchBar
            value={searchText}
            onChange={handleSearchChange}
            placeholder="Quick search by name…"
          />
        }
      />

      <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-card">
        <FilterPanel filters={filters} onChange={handleFilterChange} />

        {error ? (
          <p className="p-6 text-sm text-red-600">{error}</p>
        ) : (
          <ResumeTable
            items={items}
            loading={loading}
            sort={filters.sort}
            order={filters.order}
            onSortChange={handleSortChange}
            onParse={handleParse}
            onDelete={setDeleteTarget}
            parsingId={parsingId}
          />
        )}

        {!loading && !error && total > 0 && (
          <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
        )}
      </div>

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
