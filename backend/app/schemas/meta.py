"""Response schemas for the top-level meta endpoints (`/`, `/health`)."""

from pydantic import BaseModel, ConfigDict


class RootResponse(BaseModel):
    message: str


class HealthResponse(BaseModel):
    """Liveness/readiness snapshot — see `app.main.health`."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "healthy",
                "version": "0.1.0",
                "environment": "production",
                "uptime_seconds": 3672.41,
                "database": "connected",
                "upload_directory": "ok",
            }
        }
    )

    status: str
    version: str
    environment: str
    uptime_seconds: float
    database: str
    upload_directory: str
