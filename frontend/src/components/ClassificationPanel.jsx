import { FiAlertTriangle, FiCpu, FiRefreshCw, FiZap } from "react-icons/fi";

import { formatConfidence, formatRoleLabel } from "../utils/formatRole";
import LoadingSpinner from "./LoadingSpinner.jsx";

/**
 * A single prediction row: label, score, and a bar sized to the real score.
 *
 * The bar width is the model's actual confidence, deliberately not rescaled
 * to make the top prediction look full. Normalising it would render an 8%
 * prediction as a confident-looking full bar, which would misrepresent the
 * model — see the caption below the list for why the numbers run low.
 */
function PredictionRow({ prediction, isTop }) {
  const percent = Math.max(0, Math.min(100, prediction.confidence * 100));

  return (
    <li className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-3">
        <span
          className={`truncate text-sm ${
            isTop ? "font-semibold text-slate-900" : "text-slate-600"
          }`}
        >
          {formatRoleLabel(prediction.role)}
        </span>
        <span
          className={`shrink-0 tabular-nums text-sm ${
            isTop ? "font-semibold text-primary-700" : "text-slate-500"
          }`}
        >
          {formatConfidence(prediction.confidence)}
        </span>
      </div>
      <div
        className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100"
        role="progressbar"
        aria-valuenow={Number(percent.toFixed(1))}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={`${formatRoleLabel(prediction.role)} confidence`}
      >
        <div
          className={`h-full rounded-full ${isTop ? "bg-primary-600" : "bg-slate-300"}`}
          style={{ width: `${percent}%` }}
        />
      </div>
    </li>
  );
}

export default function ClassificationPanel({
  result,
  loading,
  error,
  onClassify,
  disabled = false,
  disabledReason,
}) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-card">
      <div className="mb-4 flex items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <FiCpu className="h-4 w-4 text-primary-600" />
          <h2 className="text-sm font-semibold text-slate-800">AI Role Classification</h2>
        </div>

        {(result || error) && !loading && (
          <button
            type="button"
            onClick={onClassify}
            className="flex items-center gap-1.5 rounded-lg px-2 py-1 text-xs font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-700"
          >
            <FiRefreshCw className="h-3.5 w-3.5" />
            Re-run
          </button>
        )}
      </div>

      {loading && (
        <div className="flex flex-col items-center justify-center gap-3 py-8" aria-live="polite">
          <LoadingSpinner />
          <p className="text-sm text-slate-500">Analyzing resume…</p>
        </div>
      )}

      {!loading && error && (
        <div className="rounded-lg border border-amber-200 bg-amber-50 p-4" aria-live="polite">
          <div className="flex items-start gap-2">
            <FiAlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-600" />
            <div className="min-w-0">
              <p className="text-sm font-medium text-amber-900">Unable to classify this resume.</p>
              <p className="mt-0.5 text-sm text-amber-700">{error}</p>
              <button
                type="button"
                onClick={onClassify}
                className="mt-3 rounded-lg border border-amber-300 bg-white px-3 py-1.5 text-xs font-medium text-amber-800 hover:bg-amber-100"
              >
                Try again
              </button>
            </div>
          </div>
        </div>
      )}

      {!loading && !error && !result && (
        <div className="py-2">
          <p className="text-sm text-slate-500">
            Predict this candidate&apos;s most likely role using the trained classification
            model.
          </p>
          <button
            type="button"
            onClick={onClassify}
            disabled={disabled}
            title={disabled ? disabledReason : undefined}
            className="mt-3 flex items-center gap-2 rounded-lg bg-primary-600 px-3 py-2 text-sm font-medium text-white hover:bg-primary-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            <FiZap className="h-4 w-4" />
            Classify resume
          </button>
          {disabled && disabledReason && (
            <p className="mt-2 text-xs text-slate-400">{disabledReason}</p>
          )}
        </div>
      )}

      {!loading && !error && result && (
        <div className="space-y-5">
          <div>
            <p className="text-xs uppercase tracking-wide text-slate-400">Predicted role</p>
            <p className="mt-1 text-xl font-semibold text-slate-900">
              {formatRoleLabel(result.predicted_role)}
            </p>
          </div>

          <div>
            <div className="mb-2 flex items-baseline justify-between">
              <p className="text-xs uppercase tracking-wide text-slate-400">Confidence</p>
              <p className="tabular-nums text-sm font-semibold text-primary-700">
                {formatConfidence(result.confidence)}
              </p>
            </div>
            <div
              className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100"
              role="progressbar"
              aria-valuenow={Number((result.confidence * 100).toFixed(1))}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Prediction confidence"
            >
              <div
                className="h-full rounded-full bg-primary-600"
                style={{ width: `${Math.max(0, Math.min(100, result.confidence * 100))}%` }}
              />
            </div>
          </div>

          {result.top_predictions?.length > 1 && (
            <div>
              <p className="mb-2.5 text-xs uppercase tracking-wide text-slate-400">
                Top predictions
              </p>
              <ul className="space-y-3">
                {result.top_predictions.map((prediction, index) => (
                  <PredictionRow
                    key={prediction.role}
                    prediction={prediction}
                    isTop={index === 0}
                  />
                ))}
              </ul>
            </div>
          )}

          {/* Without this, an 8% top score reads as a broken model rather than
              a normal result for a 34-way choice. */}
          <p className="border-t border-slate-100 pt-3 text-xs leading-relaxed text-slate-400">
            Scores are relative across all categories the model knows and sum to 100%, so they
            run lower than a yes/no confidence would. They rank candidates reliably but are not
            calibrated probabilities.
            {result.classifier_version && (
              <>
                {" "}
                <span className="block pt-1">Model: {result.classifier_version}</span>
              </>
            )}
          </p>
        </div>
      )}
    </section>
  );
}
