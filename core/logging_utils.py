"""Logging helpers for the image generation plugin."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from .constants import (
    LOG_PREFIX,
    MASK_MIN_LENGTH,
    MASK_PLACEHOLDER,
    MASK_VISIBLE_CHARS,
)


def log_prefix(component: str | None = None, task_id: str | None = None) -> str:
    """Build a consistent log prefix with optional component and task id."""
    parts = [LOG_PREFIX]
    if component:
        parts.append(f"[{component}]")
    if task_id:
        parts.append(f"[{task_id}]")
    return " ".join(parts)


def mask_sensitive(
    value: object,
    visible_chars: int = MASK_VISIBLE_CHARS,
    min_length: int = MASK_MIN_LENGTH,
    placeholder: str = MASK_PLACEHOLDER,
) -> str:
    """Mask sensitive identifiers before logging."""
    text = str(value or "")
    if len(text) <= min_length:
        return placeholder
    return f"{text[:visible_chars]}{placeholder}{text[-visible_chars:]}"


def safe_log_text(value: object, limit: int = 120) -> str:
    """Return a single-line, length-limited text summary for logs."""
    text = str(value or "").replace("\r", " ").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return f"{text[:limit]}...({len(text)} chars)"


def safe_log_error_body(value: object, limit: int = 200) -> str:
    """Return a compact provider error body summary for logs."""
    return safe_log_text(value, limit=limit)


def safe_log_url(value: object, limit: int = 80) -> str:
    """Mask URLs, data URLs, and local paths before writing logs."""
    text = str(value or "").strip()
    if not text:
        return ""

    if text.startswith("data:"):
        return f"data-url({len(text)} chars)"

    parsed = urlparse(text)
    if parsed.scheme in {"http", "https"}:
        host = parsed.netloc or "<unknown>"
        path = parsed.path or "/"
        if len(path) > limit:
            path = f"{path[:limit]}..."
        query = "?..." if parsed.query else ""
        return f"{parsed.scheme}://{host}{path}{query}"

    if parsed.scheme == "file" or os.path.isabs(text) or ":\\" in text:
        normalized_path = text.replace("\\", "/")
        filename = os.path.basename(normalized_path) or "<path>"
        return f".../{filename}"

    return safe_log_text(text, limit=limit)


def safe_log_mapping(value: object, limit: int = 120) -> str:
    """Return a compact mapping/list summary without dumping provider payloads."""
    if isinstance(value, dict):
        return f"dict(keys={list(value.keys())})"
    if isinstance(value, list):
        return f"list(len={len(value)})"
    return safe_log_text(value, limit=limit)
