"""Pydantic V2 models for BibTeX references and RAG vector search."""

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class BibReference(BaseModel):
    """Validated external dependency or research reference stored before RAG indexing."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    cite_key: str = Field(..., min_length=1, max_length=128)
    title: str = Field(..., min_length=1, max_length=512)
    url: str = Field(..., min_length=1, max_length=2048)
    access_date: str = Field(..., min_length=1, max_length=64)
    notes: str | None = Field(default=None, max_length=4096)
    raw_bibtex: str | None = Field(default=None, max_length=8192)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("url", "access_date", "cite_key", "title")
    @classmethod
    def validate_non_blank(cls, value: str) -> str:
        """Ensure required reference fields are non-empty after stripping whitespace."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("Reference field must not be empty or whitespace.")
        return stripped


class ReferenceSearchResult(BaseModel):
    """Result returned from reference or vector similarity lookup."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    reference: BibReference
    distance: float = Field(default=0.0, ge=0.0)
