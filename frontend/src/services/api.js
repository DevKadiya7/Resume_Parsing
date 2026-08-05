import axios from "axios";

import { API_BASE_URL } from "../utils/constants";

/**
 * Shared Axios instance for every backend call. Kept separate from
 * `resumeService.js` so base URL/timeout/interceptor configuration lives in
 * exactly one place, regardless of how many resource-specific service
 * modules end up using it.
 */
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

// Normalizes every failure (network error, timeout, or a backend error
// response) into a single shape — `{ message, status }` — so components
// never need to know whether `error.response` exists before reading a
// message out of it.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status ?? null;
    const message =
      error.response?.data?.message ||
      (error.code === "ECONNABORTED"
        ? "The request timed out. Please try again."
        : null) ||
      (!error.response
        ? "Could not reach the server. Is the backend running?"
        : null) ||
      error.message ||
      "Something went wrong.";

    return Promise.reject({ status, message, original: error });
  },
);

export default api;
