"""Loading and serving of the Phase 1 resume classification model.

This is the only module that touches the model artifacts. It owns loading,
compatibility validation, and raw prediction; it knows nothing about
resumes, the database, or HTTP. `ResumeClassificationService` sits above it
and supplies the text.

Loading is lazy and happens at most once per process: artifacts are ~2.7 MB
and unpickling an XGBoost booster is not free, so paying that cost at import
time would slow every startup — including deployments that never classify
anything. The first request pays it; every later request reuses the cached
bundle.
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import sklearn

from app.core.logger import get_logger
from app.exceptions.custom_exceptions import InvalidTopKException, ModelUnavailableException

logger = get_logger(__name__)

# app/services/ml_model_service.py -> app/services -> app -> backend
_BACKEND_ROOT = Path(__file__).resolve().parents[2]

MODEL_FILENAME = "role_classifier.joblib"
VECTORIZER_FILENAME = "tfidf_vectorizer.joblib"
LABEL_ENCODER_FILENAME = "label_encoder.joblib"
METADATA_FILENAME = "metadata.json"

REQUIRED_ARTIFACTS = (
    MODEL_FILENAME,
    VECTORIZER_FILENAME,
    LABEL_ENCODER_FILENAME,
    METADATA_FILENAME,
)

# Text normalization must match training exactly, or the vectorizer sees
# tokens it was never fitted on and confidence degrades silently.
#
# This mirrors `clean_resume` in the generated
# `ml/artifacts/serving_features.py`. It is duplicated rather than imported
# because that generated module imports pandas at module scope purely for
# the engineered-feature helpers, and the shipped model uses TF-IDF only —
# importing it would pull pandas into the API runtime for four regexes.
# `tests/test_classification.py::test_clean_text_matches_training_contract`
# asserts the two implementations agree, so the duplication cannot drift
# unnoticed.
_URL = re.compile(r"http\S+|www\.\S+")
_EMAIL = re.compile(r"\S+@\S+")
_NON_ALPHANUM = re.compile(r"[^a-z0-9+#./ ]")
_MULTI_SPACE = re.compile(r"\s+")


def clean_text(text: str) -> str:
    """Normalize resume text the same way training did.

    Keeps `+`, `#`, `.` and `/` so tokens like `c++`, `c#`, `node.js` and
    `ci/cd` survive — stripping them collapses the vocabulary that most
    distinguishes one technical role from another.
    """
    text = str(text).lower()
    text = _URL.sub(" ", text)
    text = _EMAIL.sub(" ", text)
    text = _NON_ALPHANUM.sub(" ", text)
    return _MULTI_SPACE.sub(" ", text).strip()


@dataclass(frozen=True)
class RolePrediction:
    """One predicted class and its confidence score."""

    role: str
    confidence: float


@dataclass(frozen=True)
class _ModelBundle:
    """The artifacts needed to serve a prediction, loaded together."""

    model: Any
    vectorizer: Any
    label_encoder: Any
    metadata: dict[str, Any]

    @property
    def num_classes(self) -> int:
        return len(self.label_encoder.classes_)

    @property
    def version(self) -> str:
        return (
            f"{self.metadata.get('model_name', 'unknown')} "
            f"({self.metadata.get('training_date', 'unknown')})"
        )


class MLModelService:
    """Lazily loads the classification artifacts and serves predictions.

    Thread-safe: FastAPI dispatches sync work across a thread pool, so two
    requests can race on the first classification. Double-checked locking
    keeps the fast path lock-free once loaded, while guaranteeing the
    artifacts are read exactly once.
    """

    def __init__(
        self, artifacts_directory: str | Path, *, strict_version_check: bool = False
    ) -> None:
        directory = Path(artifacts_directory)
        # Resolve a relative path against the backend root rather than the
        # process CWD, so the artifacts are found whether uvicorn is launched
        # from backend/, from the repo root, or from inside a container.
        if not directory.is_absolute():
            directory = _BACKEND_ROOT / directory
        self._artifacts_directory = directory
        self._strict_version_check = strict_version_check
        self._bundle: _ModelBundle | None = None
        self._lock = threading.Lock()

    @property
    def is_loaded(self) -> bool:
        """Whether the artifacts are already in memory (no loading triggered)."""
        return self._bundle is not None

    @property
    def artifacts_directory(self) -> Path:
        return self._artifacts_directory

    def num_classes(self) -> int:
        """Number of classes the loaded model can predict (loads if needed)."""
        return self._get_bundle().num_classes

    def model_version(self) -> str:
        """Human-readable model identity, for logging and API responses."""
        return self._get_bundle().version

    def predict(self, text: str, top_k: int = 3) -> list[RolePrediction]:
        """Classify `text`, returning the `top_k` roles by descending confidence.

        Raises `ModelUnavailableException` if the artifacts cannot be loaded
        or the model fails to score, and `InvalidTopKException` if `top_k`
        exceeds the number of classes the model knows.
        """
        bundle = self._get_bundle()

        if top_k < 1 or top_k > bundle.num_classes:
            raise InvalidTopKException(
                f"top_k must be between 1 and {bundle.num_classes} (got {top_k})."
            )

        cleaned = clean_text(text)
        if not cleaned:
            raise ModelUnavailableException("Cannot classify empty resume text.")

        try:
            features = bundle.vectorizer.transform([cleaned])
            scores = self._score(bundle.model, features)
        except Exception as exc:
            # Includes a feature-shape mismatch, i.e. artifacts that were not
            # exported together — unrecoverable at request time.
            logger.exception("Classification failed while scoring")
            raise ModelUnavailableException(
                "Resume classification service is currently unavailable."
            ) from exc

        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            RolePrediction(
                role=str(bundle.label_encoder.inverse_transform([index])[0]),
                confidence=round(float(scores[index]), 6),
            )
            for index in top_indices
        ]

    @staticmethod
    def _score(model: Any, features: Any) -> np.ndarray:
        """Return a per-class score vector that sums to 1.

        `predict_proba` is used when available. Margin-based models (e.g.
        LinearSVC) expose only `decision_function`, whose raw margins are not
        comparable across resumes, so they are softmaxed into a bounded,
        rankable score. Either way the values are *relative* confidences, not
        calibrated probabilities.
        """
        if hasattr(model, "predict_proba"):
            return np.asarray(model.predict_proba(features)[0], dtype=float)

        margins = np.asarray(model.decision_function(features)[0], dtype=float)
        exponentiated = np.exp(margins - margins.max())
        return exponentiated / exponentiated.sum()

    def _get_bundle(self) -> _ModelBundle:
        """Return the cached bundle, loading it on first use."""
        # Fast path: already loaded, no lock needed. Assignment of
        # `self._bundle` is atomic, so a concurrent reader sees either the
        # old None or the fully-built bundle, never a partial object.
        if self._bundle is not None:
            return self._bundle

        with self._lock:
            # Re-check inside the lock: another thread may have loaded it
            # while this one waited.
            if self._bundle is None:
                self._bundle = self._load_bundle()
            return self._bundle

    def _load_bundle(self) -> _ModelBundle:
        """Read, validate, and return the artifact bundle."""
        directory = self._artifacts_directory
        logger.info("Loading classification model artifacts from %s", directory)

        missing = [name for name in REQUIRED_ARTIFACTS if not (directory / name).is_file()]
        if missing:
            logger.error("Model artifacts missing from %s: %s", directory, ", ".join(missing))
            raise ModelUnavailableException(
                "Resume classification service is currently unavailable."
            )

        try:
            metadata = json.loads((directory / METADATA_FILENAME).read_text(encoding="utf-8"))
            model = joblib.load(directory / MODEL_FILENAME)
            vectorizer = joblib.load(directory / VECTORIZER_FILENAME)
            label_encoder = joblib.load(directory / LABEL_ENCODER_FILENAME)
        except Exception as exc:
            logger.exception("Failed to load model artifacts from %s", directory)
            raise ModelUnavailableException(
                "Resume classification service is currently unavailable."
            ) from exc

        bundle = _ModelBundle(
            model=model,
            vectorizer=vectorizer,
            label_encoder=label_encoder,
            metadata=metadata,
        )
        self._validate(bundle)

        logger.info(
            "Classification model loaded: %s | algorithm=%s | classes=%d | features=%d",
            bundle.version,
            metadata.get("algorithm", "unknown"),
            bundle.num_classes,
            metadata.get("feature_count", -1),
        )
        return bundle

    def _validate(self, bundle: _ModelBundle) -> None:
        """Check the loaded artifacts are mutually consistent and usable here."""
        if not hasattr(bundle.model, "predict"):
            raise ModelUnavailableException(
                "Resume classification service is currently unavailable."
            )
        if bundle.num_classes < 2:
            logger.error("Label encoder exposes %d classes", bundle.num_classes)
            raise ModelUnavailableException(
                "Resume classification service is currently unavailable."
            )

        self._check_sklearn_version(bundle.metadata.get("sklearn_version"))

    def _check_sklearn_version(self, trained_version: str | None) -> None:
        """Compare training and serving scikit-learn versions.

        A pickled estimator is not guaranteed to load, or to behave
        identically, across scikit-learn versions. A patch-level difference
        is tolerated silently; anything larger is surfaced — as a hard 503
        when `ML_STRICT_VERSION_CHECK` is on, otherwise as a warning, since
        refusing all traffic over a usually-benign difference is its own
        outage.
        """
        runtime_version = sklearn.__version__
        if not trained_version:
            logger.warning("Model metadata records no sklearn_version; skipping version check")
            return

        if trained_version == runtime_version:
            logger.info("scikit-learn version matches training: %s", runtime_version)
            return

        trained_minor = trained_version.split(".")[:2]
        runtime_minor = runtime_version.split(".")[:2]
        message = (
            f"scikit-learn version mismatch: model trained with {trained_version}, "
            f"serving with {runtime_version}"
        )

        if trained_minor != runtime_minor:
            if self._strict_version_check:
                logger.error("%s — refusing to serve (ML_STRICT_VERSION_CHECK enabled)", message)
                raise ModelUnavailableException(
                    "Resume classification service is currently unavailable."
                )
            logger.warning("%s — predictions may be unreliable", message)
        else:
            logger.warning("%s (patch-level only)", message)
