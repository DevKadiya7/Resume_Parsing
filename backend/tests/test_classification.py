"""Tests for the resume classification service and endpoint.

Split in two: unit tests drive `MLModelService` directly (loading, caching,
validation, failure modes), and integration tests drive the HTTP endpoint
through the app the way a client would.

The real Phase 1 artifacts are used rather than stand-ins, because the thing
most worth protecting is that the *shipped* artifacts still load and predict
in this environment — a mock would pass happily while a broken export sat in
`ml/artifacts/`.
"""

import json
import shutil
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

from app.api import deps
from app.core.config import Settings, get_settings
from app.db.database import get_db
from app.exceptions.custom_exceptions import InvalidTopKException, ModelUnavailableException
from app.main import app
from app.services.ml_model_service import MLModelService, clean_text
from tests.conftest import TEN_MB, _override_get_db
from tests.fixtures.pdf_builder import FULL_RESUME_TEXT, build_pdf

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "ml" / "artifacts"
UPLOAD_URL = "/api/v1/resumes/upload"

DATA_ENGINEER_RESUME = """
Senior Data Engineer with 7 years building batch and streaming pipelines.
Expert in Apache Spark, Airflow, Kafka, Snowflake, dbt and PySpark. Migrated
on-premise Hadoop workloads to Databricks on AWS and designed star-schema
dimensional models powering executive analytics. Strong SQL and Python.
Built incremental ingestion frameworks handling late-arriving events, authored
dbt models with automated data quality tests, and orchestrated interdependent
Airflow DAGs with SLA monitoring and automated backfill support.
"""

pytestmark = pytest.mark.skipif(
    not (ARTIFACTS_DIR / "role_classifier.joblib").is_file(),
    reason="Phase 1 model artifacts are not present in backend/ml/artifacts",
)


@pytest.fixture
def ml_service() -> MLModelService:
    """A model service pointed at the real Phase 1 artifacts."""
    return MLModelService(ARTIFACTS_DIR)


@pytest.fixture
def corrupted_artifacts(tmp_path: Path) -> Path:
    """A copy of the artifacts with the model file replaced by garbage."""
    destination = tmp_path / "corrupted"
    shutil.copytree(ARTIFACTS_DIR, destination)
    (destination / "role_classifier.joblib").write_bytes(b"this is not a joblib file")
    return destination


# --------------------------------------------------------------------------
# MLModelService — loading and caching
# --------------------------------------------------------------------------


def test_model_loads_successfully(ml_service: MLModelService) -> None:
    assert ml_service.is_loaded is False  # lazy: nothing loaded by construction

    predictions = ml_service.predict(DATA_ENGINEER_RESUME, top_k=1)

    assert ml_service.is_loaded is True
    assert len(predictions) == 1


def test_model_is_loaded_only_once(ml_service: MLModelService, monkeypatch) -> None:
    """The second prediction must reuse the cached bundle, not reload it."""
    load_count = {"n": 0}
    original_load = ml_service._load_bundle

    def counting_load():
        load_count["n"] += 1
        return original_load()

    monkeypatch.setattr(ml_service, "_load_bundle", counting_load)

    ml_service.predict(DATA_ENGINEER_RESUME, top_k=1)
    ml_service.predict(DATA_ENGINEER_RESUME, top_k=1)
    ml_service.predict("backend developer python fastapi postgresql docker", top_k=1)

    assert load_count["n"] == 1


def test_concurrent_first_requests_load_once(ml_service: MLModelService, monkeypatch) -> None:
    """Threads racing on the first prediction must not each load the artifacts."""
    import threading

    load_count = {"n": 0}
    original_load = ml_service._load_bundle

    def slow_counting_load():
        load_count["n"] += 1
        return original_load()

    monkeypatch.setattr(ml_service, "_load_bundle", slow_counting_load)

    barrier = threading.Barrier(4)

    def worker() -> None:
        barrier.wait()  # maximize the chance of a genuine race
        ml_service.predict(DATA_ENGINEER_RESUME, top_k=1)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert load_count["n"] == 1


# --------------------------------------------------------------------------
# MLModelService — prediction behaviour
# --------------------------------------------------------------------------


def test_prediction_returns_real_sorted_scores(ml_service: MLModelService) -> None:
    predictions = ml_service.predict(DATA_ENGINEER_RESUME, top_k=5)

    assert len(predictions) == 5
    confidences = [p.confidence for p in predictions]
    assert confidences == sorted(confidences, reverse=True), "must be sorted by confidence"
    assert all(0.0 <= c <= 1.0 for c in confidences)
    # Distinct values prove these are model outputs, not a placeholder constant.
    assert len(set(confidences)) > 1


def test_prediction_matches_training_expectation(ml_service: MLModelService) -> None:
    """A clear data-engineering resume should classify as DATA-ENGINEER."""
    predictions = ml_service.predict(DATA_ENGINEER_RESUME, top_k=3)
    assert predictions[0].role == "DATA-ENGINEER"


def test_top_k_controls_result_count(ml_service: MLModelService) -> None:
    for k in (1, 3, 10):
        assert len(ml_service.predict(DATA_ENGINEER_RESUME, top_k=k)) == k


def test_top_k_may_equal_class_count(ml_service: MLModelService) -> None:
    num_classes = ml_service.num_classes()
    assert len(ml_service.predict(DATA_ENGINEER_RESUME, top_k=num_classes)) == num_classes


@pytest.mark.parametrize("bad_top_k", [0, -1, 999])
def test_invalid_top_k_is_rejected(ml_service: MLModelService, bad_top_k: int) -> None:
    with pytest.raises(InvalidTopKException):
        ml_service.predict(DATA_ENGINEER_RESUME, top_k=bad_top_k)


def test_empty_text_is_rejected(ml_service: MLModelService) -> None:
    with pytest.raises(ModelUnavailableException):
        ml_service.predict("   \n\t  ", top_k=1)


def test_clean_text_matches_training_contract() -> None:
    """The API's cleaner must agree with the generated training-time one.

    `clean_text` is duplicated in the app to avoid importing pandas at
    runtime; this asserts the copy has not drifted from the generated
    `serving_features.clean_resume`, and that the golden samples still
    produce the predictions recorded at training time.
    """
    contract_path = ARTIFACTS_DIR / "serving_contract.json"
    if not contract_path.is_file():
        pytest.skip("serving_contract.json not exported")

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    service = MLModelService(ARTIFACTS_DIR)

    for sample in contract["samples"]:
        prediction = service.predict(sample["text"], top_k=1)[0]
        assert prediction.role == sample["expected_prediction"], (
            f"golden sample drifted: expected {sample['expected_prediction']}, "
            f"got {prediction.role}"
        )


def test_clean_text_preserves_technical_tokens() -> None:
    cleaned = clean_text("Skilled in C++, C#, Node.js, CI/CD and Python 3.12!")
    for token in ("c++", "c#", "node.js", "ci/cd"):
        assert token in cleaned


def test_clean_text_strips_contact_details() -> None:
    cleaned = clean_text("Contact me at jane@example.com or https://example.com/jane")
    assert "jane@example.com" not in cleaned
    assert "https" not in cleaned


# --------------------------------------------------------------------------
# MLModelService — failure modes
# --------------------------------------------------------------------------


def test_missing_artifacts_raise_model_unavailable(tmp_path: Path) -> None:
    service = MLModelService(tmp_path / "does-not-exist")
    with pytest.raises(ModelUnavailableException):
        service.predict(DATA_ENGINEER_RESUME)


def test_partially_missing_artifacts_raise_model_unavailable(tmp_path: Path) -> None:
    """A directory with only some artifacts is as unusable as an empty one."""
    destination = tmp_path / "partial"
    shutil.copytree(ARTIFACTS_DIR, destination)
    (destination / "label_encoder.joblib").unlink()

    service = MLModelService(destination)
    with pytest.raises(ModelUnavailableException):
        service.predict(DATA_ENGINEER_RESUME)


def test_corrupted_artifact_raises_model_unavailable(corrupted_artifacts: Path) -> None:
    service = MLModelService(corrupted_artifacts)
    with pytest.raises(ModelUnavailableException):
        service.predict(DATA_ENGINEER_RESUME)


def test_version_mismatch_warns_but_serves(tmp_path: Path, caplog) -> None:
    """A non-strict service logs the mismatch and keeps serving."""
    destination = tmp_path / "old-version"
    shutil.copytree(ARTIFACTS_DIR, destination)
    metadata_path = destination / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["sklearn_version"] = "0.1.0"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    service = MLModelService(destination, strict_version_check=False)
    predictions = service.predict(DATA_ENGINEER_RESUME, top_k=1)

    assert len(predictions) == 1
    assert any("version mismatch" in record.message.lower() for record in caplog.records)


def test_version_mismatch_is_fatal_when_strict(tmp_path: Path) -> None:
    destination = tmp_path / "old-version-strict"
    shutil.copytree(ARTIFACTS_DIR, destination)
    metadata_path = destination / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    metadata["sklearn_version"] = "0.1.0"
    metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

    service = MLModelService(destination, strict_version_check=True)
    with pytest.raises(ModelUnavailableException):
        service.predict(DATA_ENGINEER_RESUME)


def test_unexpected_scoring_error_becomes_model_unavailable(
    ml_service: MLModelService, monkeypatch
) -> None:
    """An unexpected failure inside the model must not leak as a 500/traceback."""
    ml_service.predict(DATA_ENGINEER_RESUME, top_k=1)  # force load

    def exploding_predict_proba(_features):
        raise RuntimeError("simulated internal model failure")

    monkeypatch.setattr(ml_service._bundle.model, "predict_proba", exploding_predict_proba)

    with pytest.raises(ModelUnavailableException):
        ml_service.predict(DATA_ENGINEER_RESUME, top_k=1)


# --------------------------------------------------------------------------
# API endpoint
# --------------------------------------------------------------------------


async def _upload_resume(client: AsyncClient, text: str = FULL_RESUME_TEXT) -> str:
    files = {"file": ("resume.pdf", build_pdf(text), "application/pdf")}
    response = await client.post(UPLOAD_URL, files=files)
    assert response.status_code == 201
    return response.json()["id"]


async def test_classify_endpoint_returns_prediction(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, DATA_ENGINEER_RESUME)

    response = await client.post(f"/api/v1/resumes/{resume_id}/classify")

    assert response.status_code == 200
    body = response.json()
    assert body["resume_id"] == resume_id
    assert isinstance(body["predicted_role"], str) and body["predicted_role"]
    assert isinstance(body["confidence"], float)
    assert 0.0 <= body["confidence"] <= 1.0
    assert len(body["top_predictions"]) == 3  # DEFAULT_TOP_K
    assert body["top_predictions"][0]["role"] == body["predicted_role"]
    assert body["top_predictions"][0]["confidence"] == body["confidence"]
    assert body["classifier_version"]


async def test_classify_endpoint_sorts_predictions(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client, DATA_ENGINEER_RESUME)

    response = await client.post(f"/api/v1/resumes/{resume_id}/classify?top_k=5")

    assert response.status_code == 200
    confidences = [p["confidence"] for p in response.json()["top_predictions"]]
    assert confidences == sorted(confidences, reverse=True)


@pytest.mark.parametrize("top_k", [1, 3, 10])
async def test_classify_endpoint_honours_top_k(client: AsyncClient, top_k: int) -> None:
    resume_id = await _upload_resume(client, DATA_ENGINEER_RESUME)

    response = await client.post(f"/api/v1/resumes/{resume_id}/classify?top_k={top_k}")

    assert response.status_code == 200
    assert len(response.json()["top_predictions"]) == top_k


async def test_classify_unknown_resume_returns_404(client: AsyncClient) -> None:
    unknown_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    response = await client.post(f"/api/v1/resumes/{unknown_id}/classify")

    assert response.status_code == 404
    assert response.json()["success"] is False


async def test_classify_invalid_uuid_returns_422(client: AsyncClient) -> None:
    response = await client.post("/api/v1/resumes/not-a-uuid/classify")
    assert response.status_code == 422


@pytest.mark.parametrize("bad_top_k", [0, -5])
async def test_classify_rejects_non_positive_top_k(client: AsyncClient, bad_top_k: int) -> None:
    resume_id = await _upload_resume(client)

    response = await client.post(f"/api/v1/resumes/{resume_id}/classify?top_k={bad_top_k}")

    assert response.status_code == 422


async def test_classify_rejects_top_k_above_class_count(client: AsyncClient) -> None:
    resume_id = await _upload_resume(client)

    response = await client.post(f"/api/v1/resumes/{resume_id}/classify?top_k=500")

    assert response.status_code == 422
    assert "top_k" in response.json()["message"]


async def test_classify_empty_pdf_returns_422(client: AsyncClient) -> None:
    """An empty PDF has no text to classify — a client error, not a model fault."""
    from tests.fixtures.pdf_builder import build_empty_pdf

    files = {"file": ("empty.pdf", build_empty_pdf(), "application/pdf")}
    upload = await client.post(UPLOAD_URL, files=files)
    resume_id = upload.json()["id"]

    response = await client.post(f"/api/v1/resumes/{resume_id}/classify")

    assert response.status_code == 422


async def test_classify_never_leaks_internal_details(client: AsyncClient) -> None:
    """Error bodies must not expose filesystem paths or tracebacks."""
    unknown_id = "3fa85f64-5717-4562-b3fc-2c963f66afa6"

    body = (await client.post(f"/api/v1/resumes/{unknown_id}/classify")).json()

    message = json.dumps(body)
    for leak in ("Traceback", "site-packages", "joblib", "C:\\\\", "/app/"):
        assert leak not in message


# --------------------------------------------------------------------------
# API endpoint — model unavailable
# --------------------------------------------------------------------------


@pytest.fixture
async def client_without_model(tmp_path: Path):
    """A client whose ML service points at an empty artifacts directory."""
    from app.db.database import Base
    from tests.conftest import test_engine

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    empty_artifacts = tmp_path / "no-artifacts"
    empty_artifacts.mkdir()

    def _override_get_settings() -> Settings:
        return Settings(
            APP_NAME="Resume Parsing Service",
            DEBUG=False,
            DATABASE_URL="sqlite+aiosqlite:///:memory:",
            UPLOAD_DIRECTORY=str(tmp_path),
            MAX_FILE_SIZE=TEN_MB,
            ML_ARTIFACTS_DIRECTORY=str(empty_artifacts),
        )

    deps.reset_ml_model_service()
    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_settings] = _override_get_settings

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    app.dependency_overrides.clear()
    deps.reset_ml_model_service()  # don't leak the broken service into other tests
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def test_classify_returns_503_when_model_missing(client_without_model: AsyncClient) -> None:
    resume_id = await _upload_resume(client_without_model, DATA_ENGINEER_RESUME)

    response = await client_without_model.post(f"/api/v1/resumes/{resume_id}/classify")

    assert response.status_code == 503
    body = response.json()
    assert body["success"] is False
    assert "unavailable" in body["message"].lower()
    # The message must not reveal where the artifacts were expected to be.
    assert "artifacts" not in body["message"].lower()
