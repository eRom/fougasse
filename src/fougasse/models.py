"""Pydantic models for Fougasse data structures."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class MemoryType(str, Enum):
    """Types of memories Fougasse can store."""

    TEXT = "text"
    CODE = "code"
    TASK = "task"
    APPOINTMENT = "appointment"
    IDEA = "idea"
    CONVERSATION = "conversation"
    TOPIC = "topic"


class MemoryCreate(BaseModel):
    """Input model for creating a new memory."""

    content: str = Field(..., min_length=1, max_length=102400)
    type: MemoryType = MemoryType.TEXT
    tags: list[str] = Field(default_factory=list, max_length=20)
    vault_id: str = Field(default="default", max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    source_agent: str | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        for tag in v:
            if len(tag) > 64:
                msg = f"Tag '{tag[:20]}...' exceeds 64 characters"
                raise ValueError(msg)
            if not tag.replace("-", "").replace("_", "").isalnum():
                msg = f"Tag '{tag}' must be alphanumeric with hyphens/underscores"
                raise ValueError(msg)
        return [t.lower() for t in v]


class Memory(BaseModel):
    """Full memory model as stored."""

    id: str
    content: str
    type: MemoryType
    tags: list[str] = Field(default_factory=list)
    vault_id: str
    source_agent: str | None = None
    metadata: dict[str, Any] | None = None
    vitality_score: float = 1.0
    access_count: int = 0
    is_archived: bool = False
    created_at: datetime
    updated_at: datetime


class SearchQuery(BaseModel):
    """Input model for searching memories."""

    query: str = Field(..., min_length=1, max_length=10000)
    vault_id: str | None = None
    type_filter: MemoryType | None = None
    tags_filter: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=100)
    min_score: float | None = None
    include_archived: bool = False


class SearchResultItem(BaseModel):
    """A single search result with score."""

    memory: Memory
    score: float
    match_sources: list[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Search response with results and metadata."""

    results: list[SearchResultItem] = Field(default_factory=list)
    total_count: int = 0
    query: str = ""
    search_time_ms: float = 0.0


class VaultCreate(BaseModel):
    """Input model for creating a vault."""

    name: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    description: str | None = None


class Vault(BaseModel):
    """Vault model."""

    id: str
    name: str
    description: str | None = None
    created_at: datetime
    memory_count: int = 0


class FougasseStatus(BaseModel):
    """Server status response."""

    version: str
    memory_count: int = 0
    vault_count: int = 0
    active_memories: int = 0
    archived_memories: int = 0
    db_size_bytes: int = 0
    uptime_seconds: float = 0.0


class MemoryUpdate(BaseModel):
    """Input model for updating a memory."""

    content: str | None = Field(default=None, max_length=102400)
    type: MemoryType | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return v
        for tag in v:
            if len(tag) > 64:
                msg = f"Tag '{tag[:20]}...' exceeds 64 characters"
                raise ValueError(msg)
        return [t.lower() for t in v]


def utcnow() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(UTC)
