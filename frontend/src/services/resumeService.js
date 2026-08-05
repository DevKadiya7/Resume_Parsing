import api from "./api";
import { API_BASE_URL } from "../utils/constants";

/**
 * One function per backend endpoint. Every list/search caller gets back
 * `{ page, page_size, total, items }` straight from the API — pagination
 * state lives in the calling hook/component, not here.
 */

export function uploadResume(file, onUploadProgress) {
  const formData = new FormData();
  formData.append("file", file);
  return api
    .post("/resumes/upload", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      onUploadProgress,
    })
    .then((res) => res.data);
}

export function listResumes(params) {
  return api.get("/resumes", { params }).then((res) => res.data);
}

export function searchResumes(params) {
  return api.get("/resumes/search", { params }).then((res) => res.data);
}

export function getStatistics() {
  return api.get("/resumes/statistics").then((res) => res.data);
}

export function getResume(id) {
  return api.get(`/resumes/${id}`).then((res) => res.data);
}

export function getResumeDetails(id) {
  return api.get(`/resumes/${id}/details`).then((res) => res.data);
}

export function parseResume(id) {
  return api.post(`/resumes/${id}/parse`).then((res) => res.data);
}

export function getParsedData(id) {
  return api.get(`/resumes/${id}/parsed`).then((res) => res.data);
}

export function deleteResume(id) {
  return api.delete(`/resumes/${id}`).then((res) => res.data);
}

/** Direct URL to the download endpoint (the server sets Content-Disposition). */
export function getDownloadUrl(id) {
  return `${API_BASE_URL}/resumes/${id}/download`;
}

/** Triggers a browser download without navigating away from the current page. */
export function downloadResume(id) {
  const link = document.createElement("a");
  link.href = getDownloadUrl(id);
  link.rel = "noopener noreferrer";
  document.body.appendChild(link);
  link.click();
  link.remove();
}
