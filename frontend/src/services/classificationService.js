import api from "./api";

/**
 * Wraps the Phase 2 classification endpoint.
 *
 * Kept in its own module rather than added to `resumeService.js` because it
 * is backed by a different subsystem (the exported ML model) with its own
 * failure mode — a 503 when the model artifacts are missing or incompatible,
 * which no other resume endpoint can return.
 */

/**
 * Classify a resume into a role/industry.
 *
 * @param {string} id     Resume UUID.
 * @param {number} topK   How many predictions to return (1..number of classes).
 * @returns {Promise<import("../types/classification").ClassificationResponse>}
 */
export function classifyResume(id, topK = 3) {
  return api
    .post(`/resumes/${id}/classify`, null, { params: { top_k: topK } })
    .then((res) => res.data);
}
