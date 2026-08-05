import { useCallback, useRef, useState } from "react";
import { FiAlertCircle, FiCheckCircle, FiFile, FiUploadCloud } from "react-icons/fi";
import { Link } from "react-router-dom";

import { uploadResume } from "../services/resumeService";
import { MAX_FILE_SIZE_BYTES } from "../utils/constants";
import { formatFileSize } from "../utils/formatFileSize";
import LoadingSpinner from "./LoadingSpinner.jsx";

function validateFile(candidate) {
  if (!candidate) return "No file selected.";
  const isPdf =
    candidate.type === "application/pdf" || candidate.name.toLowerCase().endsWith(".pdf");
  if (!isPdf) return "Only PDF files are allowed.";
  if (candidate.size > MAX_FILE_SIZE_BYTES) return "File size exceeds the 10MB limit.";
  return null;
}

/** Drag-and-drop (or click-to-browse) PDF upload with a live progress bar. */
export default function UploadCard({ onUploaded }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const [file, setFile] = useState(null);
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState("idle"); // idle | uploading | success | error
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState(null);

  const startUpload = useCallback(
    async (candidate) => {
      const validationError = validateFile(candidate);
      if (validationError) {
        setFile(candidate);
        setStatus("error");
        setErrorMessage(validationError);
        return;
      }

      setFile(candidate);
      setStatus("uploading");
      setProgress(0);
      setErrorMessage("");

      try {
        const data = await uploadResume(candidate, (event) => {
          if (event.total) {
            setProgress(Math.round((event.loaded / event.total) * 100));
          }
        });
        setStatus("success");
        setResult(data);
        onUploaded?.(data);
      } catch (err) {
        setStatus("error");
        setErrorMessage(err.message || "Upload failed. Please try again.");
      }
    },
    [onUploaded],
  );

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    const dropped = event.dataTransfer.files?.[0];
    if (dropped) startUpload(dropped);
  };

  const handleBrowse = (event) => {
    const selected = event.target.files?.[0];
    if (selected) startUpload(selected);
    event.target.value = ""; // allow re-selecting the same file later
  };

  const reset = () => {
    setFile(null);
    setStatus("idle");
    setProgress(0);
    setErrorMessage("");
    setResult(null);
  };

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-card">
      <div
        onDragOver={(event) => {
          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => status !== "uploading" && inputRef.current?.click()}
        role="button"
        tabIndex={0}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-14 text-center transition-colors ${
          dragOver
            ? "border-primary-500 bg-primary-50"
            : "border-slate-300 hover:border-primary-400 hover:bg-slate-50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={handleBrowse}
        />
        <FiUploadCloud className="mb-3 h-10 w-10 text-primary-500" />
        <p className="text-sm font-medium text-slate-700">
          Drag &amp; drop a PDF resume here, or click to browse
        </p>
        <p className="mt-1 text-xs text-slate-400">PDF only, up to 10MB</p>
      </div>

      {file && (
        <div className="mt-5 rounded-lg border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <FiFile className="h-5 w-5 shrink-0 text-slate-400" />
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-slate-700">{file.name}</p>
              <p className="text-xs text-slate-400">{formatFileSize(file.size)}</p>
            </div>
            {status === "uploading" && <LoadingSpinner size="sm" />}
            {status === "success" && <FiCheckCircle className="h-5 w-5 text-green-500" />}
            {status === "error" && <FiAlertCircle className="h-5 w-5 text-red-500" />}
          </div>

          {status === "uploading" && (
            <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-slate-100">
              <div
                className="h-full rounded-full bg-primary-600 transition-all"
                style={{ width: `${progress}%` }}
              />
            </div>
          )}

          {status === "error" && <p className="mt-3 text-sm text-red-600">{errorMessage}</p>}

          {status === "success" && result && (
            <div className="mt-3 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
              <p className="text-sm text-green-700">Uploaded successfully.</p>
              <div className="flex gap-2">
                <Link
                  to={`/resumes/${result.id}`}
                  className="rounded-lg bg-primary-600 px-3 py-1.5 text-center text-xs font-medium text-white hover:bg-primary-700"
                >
                  View resume
                </Link>
                <button
                  type="button"
                  onClick={reset}
                  className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
                >
                  Upload another
                </button>
              </div>
            </div>
          )}

          {status === "error" && (
            <button
              type="button"
              onClick={reset}
              className="mt-3 rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-600 hover:bg-slate-50"
            >
              Try again
            </button>
          )}
        </div>
      )}
    </div>
  );
}
