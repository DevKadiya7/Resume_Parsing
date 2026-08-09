"""Use-case orchestration for classifying a stored resume.

Fetches the resume record, reads its PDF, extracts the text, and hands that
to `MLModelService` — the same shape as `ResumeParsingService`, keeping the
API route a thin adapter with no ML logic in it.
"""

import asyncio
import uuid
from pathlib import Path

from app.core.logger import get_logger
from app.exceptions.custom_exceptions import ResumeNotFoundException, StorageException
from app.models.resume import Resume
from app.repositories.resume_repository import ResumeRepository
from app.schemas.classification import ClassificationResponse, RolePredictionSchema
from app.services.extractors import text_extractor
from app.services.ml_model_service import MLModelService

logger = get_logger(__name__)

DEFAULT_TOP_K = 3


class ResumeClassificationService:
    """Coordinates resume retrieval, text extraction, and model prediction."""

    def __init__(
        self,
        resume_repository: ResumeRepository,
        ml_model_service: MLModelService,
    ) -> None:
        self._resume_repository = resume_repository
        self._ml_model_service = ml_model_service

    async def classify_resume(
        self, resume_id: uuid.UUID, top_k: int = DEFAULT_TOP_K
    ) -> ClassificationResponse:
        """Classify the resume identified by `resume_id`.

        The model is scored against the PDF's full extracted text rather than
        the parsed entities, because that is what it was trained on — feeding
        it a condensed summary of skills would be a different input
        distribution. A resume therefore does not need to be parsed first.
        """
        resume = await self._get_resume_or_404(resume_id)

        logger.info("Classification started: resume_id=%s top_k=%d", resume_id, top_k)

        pdf_bytes = await self._read_pdf_bytes(resume)
        # Both extraction and scoring are blocking and CPU-bound; off the
        # event loop so one classification cannot stall unrelated requests.
        text = await asyncio.to_thread(text_extractor.extract_text, pdf_bytes)
        predictions = await asyncio.to_thread(self._ml_model_service.predict, text, top_k)

        best = predictions[0]
        logger.info(
            "Classification completed: resume_id=%s role=%s confidence=%.4f",
            resume_id,
            best.role,
            best.confidence,
        )

        return ClassificationResponse(
            resume_id=resume_id,
            predicted_role=best.role,
            confidence=best.confidence,
            top_predictions=[
                RolePredictionSchema(role=prediction.role, confidence=prediction.confidence)
                for prediction in predictions
            ],
            classifier_version=self._ml_model_service.model_version(),
        )

    async def _get_resume_or_404(self, resume_id: uuid.UUID) -> Resume:
        resume = await self._resume_repository.get_by_id(resume_id)
        if resume is None:
            raise ResumeNotFoundException("Resume not found.")
        return resume

    @staticmethod
    async def _read_pdf_bytes(resume: Resume) -> bytes:
        try:
            return await asyncio.to_thread(Path(resume.storage_path).read_bytes)
        except OSError as exc:
            logger.exception("Stored resume file missing on disk: resume_id=%s", resume.id)
            raise StorageException("The stored resume file could not be read from disk.") from exc
