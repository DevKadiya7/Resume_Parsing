import { useCallback, useEffect, useState } from "react";

const EMPTY_PAGE = { items: [], total: 0, page: 1, page_size: 20 };

/**
 * Paginated fetching shared by the Resume List and Search pages — both
 * consume `listResumes`/`searchResumes`, which return the identical
 * `{ page, page_size, total, items }` envelope, so one hook covers both.
 *
 * `params` is stringified for the effect's dependency check since callers
 * pass a fresh object literal every render; comparing by value (not
 * reference) avoids either an infinite loop or hand-rolled memoization at
 * every call site.
 */
export function useResumes(fetcher, params) {
  const [data, setData] = useState(EMPTY_PAGE);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [reloadToken, setReloadToken] = useState(0);
  const paramsKey = JSON.stringify(params);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetcher(params)
      .then((result) => {
        if (!cancelled) setData(result);
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load resumes.");
          setData(EMPTY_PAGE);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
    // `params` is intentionally represented by `paramsKey` below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetcher, paramsKey, reloadToken]);

  const refetch = useCallback(() => setReloadToken((token) => token + 1), []);

  return { ...data, loading, error, refetch };
}
