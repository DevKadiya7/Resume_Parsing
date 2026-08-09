"""Pydantic v2 schemas for the resume classification API."""

import uuid

from pydantic import BaseModel, ConfigDict, Field


class RolePredictionSchema(BaseModel):
    """A single predicted role and how confident the model is in it."""

    role: str = Field(description="Predicted category, e.g. 'DATA-ENGINEER'")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Relative confidence in [0, 1]. Scores across all classes sum to 1, "
            "but they are not calibrated probabilities — use them to rank, not "
            "as a literal likelihood."
        ),
    )


class ClassificationResponse(BaseModel):
    """Result of classifying one resume."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resume_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                "predicted_role": "DATA-ENGINEER",
                "confidence": 0.612431,
                "top_predictions": [
                    {"role": "DATA-ENGINEER", "confidence": 0.612431},
                    {"role": "ML-ENGINEER", "confidence": 0.104882},
                    {"role": "BACKEND-DEVELOPER", "confidence": 0.061237},
                ],
                "classifier_version": "XGBoost (balanced) (tuned) (2026-08-09T17:32:03+00:00)",
            }
        }
    )

    resume_id: uuid.UUID
    predicted_role: str = Field(
        description="Highest-confidence role — the first of top_predictions"
    )
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in predicted_role")
    top_predictions: list[RolePredictionSchema] = Field(
        description="Predictions sorted by descending confidence, length = top_k"
    )
    classifier_version: str = Field(
        description="Model name and training date, for reproducing a given result"
    )
