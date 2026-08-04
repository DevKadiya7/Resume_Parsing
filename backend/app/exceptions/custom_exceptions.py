"""Application-specific exceptions.

These are raised by the service/repository layers and translated into
consistent JSON error responses by the handlers registered in
`app.middleware.exception_handler`. Routes and services never build
`JSONResponse` objects themselves; they only raise these types.
"""

from fastapi import status


class AppException(Exception):
    """Base class for all application-raised, client-facing errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class MissingFileException(AppException):
    """Raised when no file (or an empty file) was provided."""

    status_code = status.HTTP_400_BAD_REQUEST


class InvalidFileTypeException(AppException):
    """Raised when the uploaded file is not a PDF."""

    status_code = status.HTTP_400_BAD_REQUEST


class FileTooLargeException(AppException):
    """Raised when the uploaded file exceeds the configured size limit."""

    status_code = status.HTTP_400_BAD_REQUEST


class StorageException(AppException):
    """Raised when the file cannot be written to disk or persisted to the DB."""

    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class ResumeNotFoundException(AppException):
    """Raised when a resume_id does not correspond to any stored resume."""

    status_code = status.HTTP_404_NOT_FOUND


class CorruptedPdfException(AppException):
    """Raised when the stored PDF cannot be opened or read by PyMuPDF."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class EncryptedPdfException(AppException):
    """Raised when the stored PDF is password-protected and cannot be read."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class EmptyPdfException(AppException):
    """Raised when the stored PDF has no extractable text content."""

    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY


class DuplicateParseException(AppException):
    """Raised when a resume that has already been parsed is parsed again."""

    status_code = status.HTTP_409_CONFLICT


class ParsedDataNotFoundException(AppException):
    """Raised when parsed data is requested for a resume that hasn't been parsed yet."""

    status_code = status.HTTP_404_NOT_FOUND


class InvalidQueryParameterException(AppException):
    """Raised when a request includes an unrecognized query parameter or an

    otherwise-invalid combination of listing/search/filter options.
    """

    status_code = status.HTTP_400_BAD_REQUEST


class ResumeFileNotFoundException(AppException):
    """Raised when a resume's PDF is requested for download but is missing on disk.

    Distinct from `StorageException`: for a download request this is a
    "the resource you asked for isn't there" condition (404), whereas the
    same underlying condition during parsing is a server-side data
    integrity failure (500).
    """

    status_code = status.HTTP_404_NOT_FOUND
