import { useCallback, useState } from "react";

import { classifyResume } from "../services/classificationService";
import { DEFAULT_TOP_K } from "../utils/constants";

/**
 * Runs the classification request for one resume and tracks its state.
 *
 * Deliberately manual rather than fetch-on-mount: classification runs a model
 * over the whole PDF, so it should happen when the user asks for it, not on
 * every visit to a resume page.
 */
export function useClassification(resumeId, topK = DEFAULT_TOP_K) {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const classify = useCallback(async () => {
    if (!resumeId) return null;

    setLoading(true);
    setError(null);
    try {
      const data = await classifyResume(resumeId, topK);
      setResult(data);
      return data;
    } catch (err) {
      // `api.js` has already normalized this to `{ status, message }`, so the
      // backend's own wording surfaces (e.g. the 503 "currently unavailable")
      // without any stack trace or internal path reaching the UI.
      setError(err.message || "Something went wrong while classifying this resume.");
      return null;
    } finally {
      setLoading(false);
    }
  }, [resumeId, topK]);

  const reset = useCallback(() => {
    setResult(null);
    setError(null);
  }, []);

  return { result, loading, error, classify, reset };
}
