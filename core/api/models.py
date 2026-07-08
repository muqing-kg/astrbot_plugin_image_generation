"""Public API result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class PublicAPIResultCode(str, Enum):
    """Stable result codes returned by the inter-plugin public API."""

    ACCEPTED = "accepted"
    GENERATOR_NOT_INITIALIZED = "generator_not_initialized"
    API_KEY_MISSING = "api_key_missing"
    TEMPLATE_NOT_FOUND = "template_not_found"
    EMPTY_PROMPT = "empty_prompt"
    RATE_LIMITED = "rate_limited"
    PROMPT_BLOCKED = "prompt_blocked"
    QUEUE_FULL = "queue_full"
    REJECTED = "rejected"
    TASK_MANAGER_CLOSED = "task_manager_closed"
    TASK_ID_CONFLICT = "task_id_conflict"
    CANCEL_REQUESTED = "cancel_requested"
    CANCEL_FAILED = "cancel_failed"
    NOT_FOUND = "not_found"
    TIMEOUT = "timeout"
    SUCCEEDED = "succeeded"
    NO_RESULT = "no_result"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"

    @classmethod
    def from_task_status(cls, status: str) -> PublicAPIResultCode:
        """Map task status values to public API result codes."""
        try:
            return cls(status)
        except ValueError:
            return cls.FAILED


@dataclass(frozen=True)
class ImageGenerationTaskSnapshot:
    """Stable snapshot of one image generation task for external plugins."""

    task_id: str
    status: str
    active: bool
    source: str
    requested_count: int
    result_count: int
    reference_image_count: int
    aspect_ratio: str
    resolution: str
    result_paths: list[str]
    error: str
    message: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    duration_seconds: float | None
    request_stats: dict[str, int] = field(default_factory=dict)
    items: list[dict[str, Any]] = field(default_factory=list)
    finished_request_count: int = 0
    running_request_count: int = 0
    pending_request_count: int = 0
    failed_request_count: int = 0
    cancelled_request_count: int = 0


@dataclass(frozen=True)
class ImageGenerationSubmitResult:
    """Result returned after submitting an image generation task."""

    ok: bool
    code: str
    message: str
    task_id: str | None = None
    error: str = ""


@dataclass(frozen=True)
class ImageGenerationResult:
    """Result returned after waiting for generated image files."""

    ok: bool
    code: str
    message: str
    task_id: str
    paths: list[str]
    error: str = ""


@dataclass(frozen=True)
class ImageGenerationOperationResult:
    """Result returned for task operations such as cancellation."""

    ok: bool
    code: str
    message: str
    task_id: str | None = None
    error: str = ""


__all__ = (
    "ImageGenerationOperationResult",
    "ImageGenerationResult",
    "ImageGenerationSubmitResult",
    "ImageGenerationTaskSnapshot",
    "PublicAPIResultCode",
)
