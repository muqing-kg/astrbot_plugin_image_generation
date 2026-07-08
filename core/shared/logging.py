"""Logging helpers for the image generation plugin."""

from __future__ import annotations

import os
import re
from urllib.parse import parse_qsl, urlparse

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


_SENSITIVE_ASSIGNMENT_RE = re.compile(
    r"(?i)\b(authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password)"
    r"([\"']?\s*[:=]\s*[\"']?)"
    r"([^\"'\s,}]+)"
)
_BEARER_RE = re.compile(r"(?i)\bBearer\s+([A-Za-z0-9._~+\-/=]{8,})")
_DATA_URL_RE = re.compile(r"data:image/[a-zA-Z0-9.+-]+;base64,[A-Za-z0-9+/=\s]+")
_LONG_BASE64_RE = re.compile(r"\b[A-Za-z0-9+/]{120,}={0,2}\b")
SENSITIVE_LOG_FIELD_NAMES = {
    "authorization",
    "api-key",
    "apikey",
    "api_key",
    "access-token",
    "accesstoken",
    "access_token",
    "refresh-token",
    "refreshtoken",
    "refresh_token",
    "token",
    "secret",
    "password",
    "x-goog-api-key",
}


def is_sensitive_log_field(name: object) -> bool:
    """Return whether a field name should always be masked in debug logs."""
    normalized = str(name or "").strip().lower()
    if normalized in SENSITIVE_LOG_FIELD_NAMES:
        return True
    normalized = normalized.replace("_", "-")
    return normalized in SENSITIVE_LOG_FIELD_NAMES


def safe_log_error_body(value: object, limit: int = 200) -> str:
    """Return a compact provider error body summary for logs.

    The plugin keeps provider error bodies readable for administrators, but still
    removes values that are almost always secrets or binary payloads.
    """
    text = str(value or "")
    text = _DATA_URL_RE.sub(lambda m: f"data-url({len(m.group(0))} chars)", text)
    text = _LONG_BASE64_RE.sub(lambda m: f"base64({len(m.group(0))} chars)", text)
    text = _BEARER_RE.sub(lambda m: f"Bearer {mask_sensitive(m.group(1))}", text)

    def _mask_assignment(match: re.Match[str]) -> str:
        return f"{match.group(1)}{match.group(2)}{mask_sensitive(match.group(3))}"

    text = _SENSITIVE_ASSIGNMENT_RE.sub(_mask_assignment, text)
    return safe_log_text(text, limit=limit)


def _query_summary(query: str, max_keys: int = 6) -> str:
    """Return query parameter names without values for URL logs."""
    if not query:
        return ""
    keys: list[str] = []
    for key, _ in parse_qsl(query, keep_blank_values=True):
        if key and key not in keys:
            keys.append(key)
    if not keys:
        return f"query_len={len(query)}"
    visible = keys[:max_keys]
    suffix = f",+{len(keys) - max_keys}" if len(keys) > max_keys else ""
    return f"query_keys={','.join(visible)}{suffix};query_len={len(query)}"


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
        query = f"?<{_query_summary(parsed.query)}>" if parsed.query else ""
        return f"{parsed.scheme}://{host}{path}{query}"

    if parsed.scheme == "file" or os.path.isabs(text) or ":\\" in text:
        normalized_path = text.replace("\\", "/")
        return safe_log_text(normalized_path, limit=max(limit, 160))

    return safe_log_text(text, limit=limit)


def safe_log_mapping(value: object, limit: int = 120) -> str:
    """Return a compact mapping/list summary without dumping provider payloads."""
    if isinstance(value, dict):
        return f"dict(keys={list(value.keys())})"
    if isinstance(value, list):
        return f"list(len={len(value)})"
    return safe_log_text(value, limit=limit)


def format_seconds(value: float | None) -> str:
    """Format seconds using Chinese units for human-facing logs."""
    if value is None:
        return "未知"
    return f"{max(0.0, value):.2f}秒"


def format_sub_request(index: int | None, count: int | None) -> str:
    """Format a generation sub-request index for task logs."""
    if not index or not count or count <= 1:
        return ""
    return f"子请求={max(1, index)}/{max(1, count)}"


def format_optional(value: object, empty: str = "无", limit: int = 120) -> str:
    """Format optional values for readable Chinese logs."""
    text = safe_log_text(value, limit=limit)
    return text if text else empty


def format_log_fields(**fields: object) -> str:
    """Format optional key-value fields for debug logs."""
    parts: list[str] = []
    for key, value in fields.items():
        if value is None or value == "":
            continue
        parts.append(f"{key}={safe_log_text(value, 160)}")
    return ", ".join(parts)


def format_cn_log_fields(**fields: object) -> str:
    """Format optional fields with Chinese labels for readable logs."""
    parts: list[str] = []
    for key, value in fields.items():
        if value is None or value == "":
            continue
        parts.append(f"{key}={safe_log_text(value, 160)}")
    return "，".join(parts)


def format_log_event(event: str, **fields: object) -> str:
    """Format a stable event name followed by optional Chinese fields."""
    details = format_cn_log_fields(**fields)
    if not details:
        return f"事件={safe_log_text(event, 80)}"
    return f"事件={safe_log_text(event, 80)}，{details}"
