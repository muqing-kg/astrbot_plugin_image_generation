"""Image processing helpers for download, extraction, and temporary storage."""

from __future__ import annotations

import base64
import hashlib
import ntpath
import os
import posixpath
import re
import time
from collections.abc import Iterable
from io import BytesIO
from typing import TYPE_CHECKING, Any
from urllib.parse import unquote, urlparse

from PIL import Image, UnidentifiedImageError

import astrbot.api.message_components as Comp
from astrbot.api import logger
from astrbot.core.utils.astrbot_path import get_astrbot_workspaces_path
from astrbot.core.utils.io import download_image_by_url

from ..shared.logging import (
    log_prefix,
    mask_sensitive,
    safe_log_error_body,
    safe_log_url,
)
from ..shared.types import ImageData

if TYPE_CHECKING:
    from astrbot.api.event import AstrMessageEvent


LOG = log_prefix("ImageProcessor")
ALLOWED_IMAGE_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
        "image/heic",
        "image/heif",
    }
)
PIL_VERIFIABLE_IMAGE_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/webp",
    }
)
GENERATED_IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
_BASE64_PAYLOAD_RE = re.compile(r"^[A-Za-z0-9+/=\s]+$")


class ImageProcessor:
    """Download, extract, validate, and store image files."""

    def __init__(
        self,
        temp_dir: str,
        max_image_size_mb: int,
        local_base_dir: str | None = None,
        allowed_local_base_dirs: Iterable[str | os.PathLike[str] | None] | None = None,
    ) -> None:
        self._temp_dir = os.path.realpath(temp_dir)
        self._max_image_size_mb = max_image_size_mb
        self._local_base_dir = (
            os.path.realpath(local_base_dir) if local_base_dir else ""
        )
        base_dirs: list[str | os.PathLike[str] | None] = [
            self._local_base_dir,
            self._temp_dir,
        ]
        if allowed_local_base_dirs:
            base_dirs.extend(allowed_local_base_dirs)
        self._allowed_local_base_dirs = self._normalize_allowed_base_dirs(base_dirs)
        os.makedirs(self._temp_dir, exist_ok=True)

    def update_settings(self, max_image_size_mb: int | None = None) -> None:
        """Update runtime image processing settings."""
        if max_image_size_mb is not None:
            self._max_image_size_mb = max_image_size_mb

    @property
    def temp_dir(self) -> str:
        """Return the temporary directory path."""
        return self._temp_dir

    def workspace_dir_for_origin(self, unified_msg_origin: str | None) -> str | None:
        """Return the AstrBot local workspace path for a session origin."""
        origin = str(unified_msg_origin or "").strip()
        if not origin:
            return None
        normalized_origin = re.sub(r"[^A-Za-z0-9._-]+", "_", origin)
        normalized_origin = normalized_origin or "unknown"
        return os.path.realpath(
            os.path.join(get_astrbot_workspaces_path(), normalized_origin)
        )

    def _normalize_allowed_base_dirs(
        self,
        paths: Iterable[str | os.PathLike[str] | None],
    ) -> tuple[str, ...]:
        """Normalize and deduplicate allowed local directory roots."""
        result: list[str] = []
        seen: set[str] = set()
        for raw_path in paths:
            if not raw_path:
                continue
            path = os.path.realpath(os.fspath(raw_path))
            normalized = os.path.normcase(path)
            if normalized in seen:
                continue
            seen.add(normalized)
            result.append(path)
        return tuple(result)

    def _is_path_within_allowed_dirs(
        self,
        path: str,
        allowed_base_dirs: tuple[str, ...],
    ) -> bool:
        """Return whether path is inside one of the configured safe roots."""
        normalized_path = os.path.normcase(os.path.realpath(path))
        for base_dir in allowed_base_dirs:
            normalized_base = os.path.normcase(os.path.realpath(base_dir))
            try:
                if (
                    os.path.commonpath([normalized_base, normalized_path])
                    == normalized_base
                ):
                    return True
            except ValueError:
                continue
        return False

    def _resolve_local_path(
        self,
        value: str,
        *,
        workspace_dir: str | None = None,
    ) -> str | None:
        """Resolve a safe local image path inside workspace/temp/plugin data dirs."""
        value = self._normalize_local_path_value(value)
        if not value:
            return None

        parsed = urlparse(value)
        if (
            parsed.scheme
            and parsed.scheme.lower() != "file"
            and not self._is_absolute_path(value)
        ):
            return None

        allowed_base_dirs = self._allowed_local_base_dirs
        if workspace_dir:
            allowed_base_dirs = self._normalize_allowed_base_dirs(
                (*allowed_base_dirs, workspace_dir)
            )
        candidates: list[str] = []
        if self._is_absolute_path(value):
            candidates.append(value)
        elif self._local_base_dir and value.replace("\\", "/").startswith("files/"):
            candidates.append(os.path.join(self._local_base_dir, value))
        elif workspace_dir:
            candidates.append(os.path.join(workspace_dir, value))

        for candidate in candidates:
            path = os.path.realpath(candidate)
            if not self._is_path_within_allowed_dirs(path, allowed_base_dirs):
                logger.warning(
                    f"{LOG} 本地参考图路径不在允许目录内: {safe_log_url(path)}"
                )
                continue
            if os.path.exists(path) and os.path.isfile(path):
                return path
            logger.warning(f"{LOG} 本地参考图不存在或不是文件: {safe_log_url(path)}")
        return None

    def _is_absolute_path(self, value: str) -> bool:
        """Return whether a value is a Linux/Windows absolute path."""
        return os.path.isabs(value) or ntpath.isabs(value) or posixpath.isabs(value)

    def _is_network_url(self, value: str) -> bool:
        """Return whether a value is an HTTP(S) image source."""
        scheme = urlparse(value).scheme.lower()
        return scheme in {"http", "https"}

    def _normalize_local_path_value(self, value: str) -> str:
        """Normalize local file paths, including file:// URI values."""
        value = value.strip()
        if not value.lower().startswith("file:"):
            return value

        parsed = urlparse(value)
        if parsed.scheme.lower() != "file":
            return value

        netloc = unquote(parsed.netloc)
        path = unquote(parsed.path)
        if netloc and netloc.lower() != "localhost" and path:
            path = f"//{netloc}{path}"
        elif netloc and netloc.lower() != "localhost":
            path = netloc

        # AstrBot or platform adapters may pass file:///E:\\path or file:///E:/path.
        if len(path) >= 3 and path[0] == "/" and path[2] == ":":
            path = path[1:]
        return os.path.normpath(path)

    def _decode_inline_image_payload(self, value: str) -> bytes | None:
        """Decode base64://, data URI, or bare base64 image payloads."""
        text = value.strip()
        if not text:
            return None

        lower = text.lower()
        payload = ""
        if lower.startswith("base64://"):
            payload = text[9:]
        elif lower.startswith("data:image/") and ";base64," in lower:
            payload = text.split(",", 1)[1]
        elif (
            len(text) >= 64
            and len(text) % 4 == 0
            and _BASE64_PAYLOAD_RE.fullmatch(text)
            and ("/" in text or "+" in text or "=" in text)
        ):
            # Some bridges only provide bare base64 without a scheme prefix.
            payload = text
        else:
            return None

        compact = "".join(payload.split())
        if not compact:
            return None
        try:
            padding = "=" * (-len(compact) % 4)
            return base64.b64decode(compact + padding, validate=False)
        except Exception:
            return None

    async def _load_image_bytes_via_media_resolver(self, value: str) -> bytes | None:
        """Use AstrBot MediaResolver for non-HTTP image references when available."""
        try:
            from astrbot.core.utils.media_utils import MediaResolver
        except Exception:
            return None

        try:
            return await MediaResolver(value, media_type="image").to_bytes()
        except Exception as exc:
            logger.debug(
                f"{LOG} MediaResolver 解析失败: {safe_log_url(value)} ({safe_log_error_body(exc)})"
            )
            return None

    async def download_image(
        self,
        url: str,
        *,
        workspace_dir: str | None = None,
    ) -> ImageData | None:
        """Download or read an image and return normalized image data."""
        try:
            url = url.strip()
            if not url:
                return None

            data: bytes | None = None
            source_url = url if self._is_network_url(url) else None

            if inline_data := self._decode_inline_image_payload(url):
                data = inline_data
                source_url = None
            elif local_path := self._resolve_local_path(url, workspace_dir=workspace_dir):
                source_url = None
                with open(local_path, "rb") as f:
                    data = f.read()
            elif self._is_network_url(url):
                # Use the plugin temporary directory for downloaded references.
                file_name = f"ref_{hashlib.md5(url.encode()).hexdigest()[:10]}"
                path = os.path.join(self._temp_dir, file_name)
                path = await download_image_by_url(url, path=path)
                if path:
                    with open(path, "rb") as f:
                        data = f.read()
            else:
                # Fallback for file://, base64-like, and platform temporary media refs.
                data = await self._load_image_bytes_via_media_resolver(url)
                source_url = None
                if data is None:
                    logger.warning(f"{LOG} 不支持的图片来源: {safe_log_url(url)}")
                    return None

            if not data:
                return None

            if len(data) > self._max_image_size_mb * 1024 * 1024:
                logger.warning(f"{LOG} 图片超过大小限制 ({self._max_image_size_mb}MB)")
                return None

            return self.validate_image_data(
                data,
                source_url=source_url,
                log_source=url,
            )
        except Exception as exc:
            logger.error(
                f"{LOG} 获取图片失败: {safe_log_url(url)} ({safe_log_error_body(exc)})"
            )
        return None

    def validate_image_data(
        self,
        data: bytes,
        *,
        source_url: str | None = None,
        log_source: str | None = None,
    ) -> ImageData | None:
        """Validate bytes as a supported image and return normalized image data."""
        mime = self._detect_mime_type(data)
        if not self._is_valid_image_data(data, mime):
            logger.warning(
                f"{LOG} 参考图文件类型不支持或内容不是有效图片: {safe_log_url(log_source or source_url or '<bytes>')}"
            )
            return None
        return ImageData(data=data, mime_type=mime, source_url=source_url)

    def _detect_mime_type(self, data: bytes) -> str:
        """Detect the image MIME type from magic bytes."""
        if data.startswith(b"\xff\xd8"):
            return "image/jpeg"
        elif data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        elif data.startswith((b"GIF87a", b"GIF89a")):
            return "image/gif"
        elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
            return "image/webp"
        elif len(data) > 12 and data[4:8] == b"ftyp":
            brand = data[8:12]
            if brand in (b"heic", b"heix", b"heim", b"heis"):
                return "image/heic"
            if brand in (b"mif1", b"msf1", b"heif"):
                return "image/heif"
        return "application/octet-stream"

    def _is_valid_image_data(self, data: bytes, mime: str) -> bool:
        """Return whether bytes are a supported, real image payload."""
        if mime not in ALLOWED_IMAGE_MIME_TYPES:
            return False
        if mime not in PIL_VERIFIABLE_IMAGE_MIME_TYPES:
            return True
        try:
            with Image.open(BytesIO(data)) as image:
                image.verify()
        except (UnidentifiedImageError, OSError, ValueError):
            return False
        return True

    def _normalize_user_id(self, user_id: Any) -> str:
        """Normalize a platform user id string for avatar lookup."""
        if user_id is None:
            return ""
        return str(user_id).strip()

    def _looks_like_qq_uin(self, user_id: str) -> bool:
        """Return whether user_id looks like a QQ number for qlogo fallback."""
        cleaned = self._normalize_user_id(user_id)
        if not cleaned.isdigit():
            return False
        # QQ UIN is typically 5-11 digits; keep a slightly wider bound.
        return 5 <= len(cleaned) <= 12

    def _event_hints_wechat_name(self, event: AstrMessageEvent | None) -> bool:
        """Return whether platform id/name strings look WeChat-branded.

        Real WeChatBridge sessions commonly look like:
        - platform_name / meta.name = aiocqhttp
        - platform_id / meta.id = "微信-xxx" (user-configured adapter id)
        - unified_msg_origin = "aiocqhttp:GroupMessage:..."
        So do NOT treat bare aiocqhttp as WeChat; rely on id/display markers.
        """
        if event is None:
            return False
        hints: list[str] = []
        for attr in ("get_platform_name", "get_platform", "get_platform_id"):
            fn = getattr(event, attr, None)
            if callable(fn):
                try:
                    value = fn()
                except Exception:
                    value = None
                if value is not None:
                    hints.append(str(value))
        for attr in (
            "platform_name",
            "platform",
            "platform_id",
            "unified_msg_origin",
        ):
            value = getattr(event, attr, None)
            if value is not None:
                hints.append(str(value))
        # PlatformMetadata may carry the user-facing adapter id that contains 微信.
        for meta_attr in ("platform_meta", "platform"):
            meta = getattr(event, meta_attr, None)
            if meta is None:
                continue
            for attr in ("id", "name", "adapter_display_name", "description"):
                value = getattr(meta, attr, None)
                if value is not None:
                    hints.append(str(value))
        message_obj = getattr(event, "message_obj", None)
        if message_obj is not None:
            for attr in ("platform_name", "platform", "self_id", "type"):
                value = getattr(message_obj, attr, None)
                if value is not None:
                    hints.append(str(value))
        blob = " ".join(hints).lower()
        tokens = (
            "wechat",
            "weixin",
            "微信",
            "wechatbridge",
            "wxbot",
            "wx-bot",
        )
        return any(token in blob for token in tokens)

    def _payload_forbids_qlogo(self, payload: Any) -> bool:
        """Detect WeChatBridge-style payloads that must never fall back to QQ CDN."""
        key_markers = {
            "avatar_proxy_url",
            "wx_avatar_url",
        }
        value_markers = (
            "wx.qlogo.cn",
            "wx.qlogo",
            "/avatar/",
            "wechatbridge",
        )

        def walk(obj: Any, depth: int = 0) -> bool:
            if depth > 4 or obj is None:
                return False
            if isinstance(obj, dict):
                for key, value in obj.items():
                    key_l = str(key).lower()
                    if key_l in key_markers:
                        return True
                    if isinstance(value, str):
                        lower = value.lower()
                        if any(token in lower for token in value_markers):
                            return True
                    elif walk(value, depth + 1):
                        return True
                return False
            if isinstance(obj, list):
                return any(walk(item, depth + 1) for item in obj[:8])
            if isinstance(obj, str):
                lower = obj.lower()
                return any(token in lower for token in value_markers)
            return False

        return walk(payload)

    def _extract_avatar_urls(self, payload: Any) -> list[str]:
        """Collect avatar URL candidates from OneBot user/member payloads."""
        urls: list[str] = []
        seen: set[str] = set()

        def add(value: Any) -> None:
            if not isinstance(value, str):
                return
            cleaned = value.strip()
            if not cleaned or cleaned in seen:
                return
            lower = cleaned.lower()
            if not (
                lower.startswith("http://")
                or lower.startswith("https://")
                or lower.startswith("file:")
                or lower.startswith("base64://")
                or lower.startswith("data:image/")
            ):
                return
            seen.add(cleaned)
            urls.append(cleaned)

        def walk(obj: Any, depth: int = 0) -> None:
            if depth > 3 or obj is None:
                return
            if isinstance(obj, dict):
                # Prefer inline/DB remote avatar fields, then local proxy.
                for key in (
                    "avatar_base64",
                    "avatar_data_url",
                    "avatar_url",
                    "wx_avatar_url",
                    "avatar",
                    "avatar_proxy_url",
                    "user_avatar",
                    "headimg",
                    "head_img",
                    "icon",
                    "url",
                ):
                    if key in obj:
                        add(obj.get(key))
                data = obj.get("data")
                if isinstance(data, (dict, list)):
                    walk(data, depth + 1)
                return
            if isinstance(obj, list):
                for item in obj[:5]:
                    walk(item, depth + 1)

        walk(payload)
        return urls

    async def _resolve_platform_avatar_urls(
        self,
        event: AstrMessageEvent | None,
        user_id: str,
    ) -> tuple[list[str], bool]:
        """Resolve avatar URLs via platform bot APIs.

        Returns:
            (urls, forbid_qlogo)
            forbid_qlogo is True when the platform response looks like WeChatBridge
            (or other non-QQ avatar sources) and QQ CDN must not be used.
        """
        if event is None:
            return [], False
        uid = self._normalize_user_id(user_id)
        if not uid:
            return [], False

        bot = getattr(event, "bot", None)
        api = getattr(bot, "api", None)
        call_action = getattr(api, "call_action", None)
        if not callable(call_action):
            return [], False

        user_id_value: object = int(uid) if uid.isdigit() else uid
        actions: list[tuple[str, dict[str, object]]] = [
            ("get_stranger_info", {"user_id": user_id_value}),
            ("get_user_info", {"user_id": user_id_value}),
        ]
        # Avoid duplicate string/int variants when they are the same.
        if not uid.isdigit():
            pass
        elif str(user_id_value) != uid:
            actions.extend(
                [
                    ("get_stranger_info", {"user_id": uid}),
                    ("get_user_info", {"user_id": uid}),
                ]
            )

        group_id = None
        try:
            if hasattr(event, "get_group_id"):
                group_id = event.get_group_id()
        except Exception:
            group_id = None
        if group_id not in (None, "", 0, "0"):
            group_id_value: object = (
                int(group_id) if str(group_id).isdigit() else group_id
            )
            actions.append(
                (
                    "get_group_member_info",
                    {"group_id": group_id_value, "user_id": user_id_value},
                )
            )
            if uid.isdigit() and str(user_id_value) != uid:
                actions.append(
                    (
                        "get_group_member_info",
                        {"group_id": group_id_value, "user_id": uid},
                    )
                )

        forbid_qlogo = self._event_hints_wechat_name(event)
        collected: list[str] = []
        seen: set[str] = set()
        for action, params in actions:
            try:
                result = await call_action(action, **params)
            except Exception:
                continue
            if self._payload_forbids_qlogo(result):
                forbid_qlogo = True
            for url in self._extract_avatar_urls(result):
                if url in seen:
                    continue
                seen.add(url)
                collected.append(url)
            if collected:
                # First successful avatar payload is enough.
                break
        return collected, forbid_qlogo

    async def get_avatar(
        self,
        user_id: str,
        event: AstrMessageEvent | None = None,
    ) -> ImageData | None:
        """Fetch a user's avatar as validated ImageData.

        Prefer platform APIs (WeChatBridge returns DB remote avatar URLs, usually wx.qlogo).
        Fall back to QQ qlogo CDN only when safe:
        - user id looks like a QQ UIN, and
        - platform payload/name does not indicate WeChatBridge/WeChat.
        """
        uid = self._normalize_user_id(user_id)
        if not uid:
            return None

        try:
            candidates, forbid_qlogo = await self._resolve_platform_avatar_urls(
                event, uid
            )
            if (
                self._looks_like_qq_uin(uid)
                and not forbid_qlogo
                and not self._event_hints_wechat_name(event)
            ):
                candidates.append(
                    f"https://q4.qlogo.cn/headimg_dl?dst_uin={uid}&spec=640"
                )

            # Keep order, drop duplicates.
            # Prefer inline base64/data first, then local avatar proxy, then remote.
            seen: set[str] = set()
            ordered: list[str] = []
            inline_first: list[str] = []
            proxy_first: list[str] = []
            others: list[str] = []
            for url in candidates:
                if url in seen:
                    continue
                seen.add(url)
                lower = url.lower()
                if lower.startswith("data:image/") or lower.startswith("base64://"):
                    inline_first.append(url)
                elif (
                    "/avatar/" in lower
                    or "host.docker.internal" in lower
                    or "avatar_proxy" in lower
                ):
                    proxy_first.append(url)
                else:
                    others.append(url)
            ordered = inline_first + proxy_first + others

            if not ordered:
                logger.debug(
                    f"{LOG} 未找到可用头像源 (user_id={mask_sensitive(uid)}, "
                    f"forbid_qlogo={forbid_qlogo})"
                )
                return None

            for url in ordered:
                attempts = 3 if (
                    "/avatar/" in url.lower()
                    or "host.docker.internal" in url.lower()
                ) else 1
                for attempt in range(attempts):
                    if attempt > 0:
                        # Wait for bridge background prefetch; cold cache may 404 first.
                        time.sleep(0.55 * attempt)
                    image = await self.download_image(url)
                    if image is not None:
                        return image
                    # Lightweight fallback for pure HTTP when download_image path fails.
                    if not url.lower().startswith(("http://", "https://")):
                        break
                    file_name = f"avatar_{uid}_{abs(hash(url)) % 10_000_000}.jpg"
                    path = os.path.join(self._temp_dir, file_name)
                    path = await download_image_by_url(url, path=path)
                    if not path:
                        continue
                    with open(path, "rb") as f:
                        data = f.read()
                    validated = self.validate_image_data(data, log_source=url)
                    if validated is not None:
                        return validated
            logger.debug(
                f"{LOG} 头像下载失败 (user_id={mask_sensitive(uid)}, "
                f"candidates={len(ordered)}, forbid_qlogo={forbid_qlogo})"
            )
        except Exception as e:
            logger.debug(
                f"{LOG} 获取头像失败 (user_id={mask_sensitive(uid)}): {safe_log_error_body(e)}"
            )
        return None

    def _message_body_leading_component(self, event: AstrMessageEvent):
        """Return the first non-reply, non-empty message component."""
        if not event.message_obj or not event.message_obj.message:
            return None

        for component in event.message_obj.message:
            if isinstance(component, Comp.Reply):
                continue
            if isinstance(component, Comp.Plain) and not component.text.strip():
                continue
            return component
        return None

    def _has_reply_from_bot(self, event: AstrMessageEvent, bot_self_id: str) -> bool:
        """Return whether the current event replies to a bot-sent message."""
        if not bot_self_id or not event.message_obj or not event.message_obj.message:
            return False

        for component in event.message_obj.message:
            if not isinstance(component, Comp.Reply):
                continue
            for value in (
                getattr(component, "sender_id", None),
                getattr(component, "qq", None),
            ):
                if value is not None and str(value).strip() == bot_self_id:
                    return True
        return False

    def _should_skip_leading_bot_at(
        self,
        event: AstrMessageEvent,
        bot_self_id: str,
    ) -> bool:
        """Return whether the leading bot mention is only the command trigger."""
        if not bot_self_id or self._has_reply_from_bot(event, bot_self_id):
            return False

        leading_component = self._message_body_leading_component(event)
        if not isinstance(leading_component, Comp.At):
            return False

        return str(leading_component.qq).strip() == bot_self_id

    def _iter_image_source_candidates(self, component: Any) -> list[str]:
        """Collect candidate image sources from an Image-like component."""
        candidates: list[str] = []
        seen: set[str] = set()
        for attr in ("url", "file", "path"):
            value = getattr(component, attr, None)
            if not isinstance(value, str):
                continue
            cleaned = value.strip()
            if not cleaned or cleaned in seen:
                continue
            seen.add(cleaned)
            candidates.append(cleaned)
        return candidates

    def _looks_like_platform_file_id(self, value: str) -> bool:
        """Return whether a value looks like a OneBot/CQ cache file id."""
        text = value.strip()
        if not text:
            return False
        lower = text.lower()
        if lower.startswith(
            ("http://", "https://", "file:", "base64://", "data:image/")
        ):
            return False
        if self._is_absolute_path(text):
            return False
        return len(text) >= 8

    async def _resolve_platform_image_ref(
        self,
        event: AstrMessageEvent | None,
        image_ref: str,
    ) -> str | None:
        """Resolve a platform image id into a downloadable URL/path when possible."""
        if event is None:
            return None
        bot = getattr(event, "bot", None)
        api = getattr(bot, "api", None)
        call_action = getattr(api, "call_action", None)
        if not callable(call_action):
            return None

        candidates = [image_ref]
        base_name, ext = os.path.splitext(image_ref)
        if ext and base_name and base_name not in candidates:
            candidates.append(base_name)

        actions: list[tuple[str, dict[str, object]]] = []
        for candidate in candidates:
            actions.extend(
                [
                    ("get_image", {"file": candidate}),
                    ("get_image", {"file_id": candidate}),
                    ("get_image", {"id": candidate}),
                    ("get_image", {"image": candidate}),
                    ("get_file", {"file_id": candidate}),
                    ("get_file", {"file": candidate}),
                ]
            )

        group_id = None
        try:
            if hasattr(event, "get_group_id"):
                group_id = event.get_group_id()
        except Exception:
            group_id = None
        group_id_value: object = group_id
        if isinstance(group_id, str) and group_id.isdigit():
            group_id_value = int(group_id)
        if group_id_value:
            for candidate in candidates:
                actions.append(
                    (
                        "get_group_file_url",
                        {"group_id": group_id_value, "file_id": candidate},
                    )
                )
        for candidate in candidates:
            actions.append(("get_private_file_url", {"file_id": candidate}))

        for action, params in actions:
            try:
                result = await call_action(action, **params)
            except Exception:
                continue
            data = result
            if isinstance(result, dict) and isinstance(result.get("data"), dict):
                data = result["data"]
            if not isinstance(data, dict):
                continue
            for key in ("url", "file", "path"):
                value = data.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return None

    async def _image_data_from_component(
        self,
        component: Any,
        *,
        workspace_dir: str | None = None,
        event: AstrMessageEvent | None = None,
    ) -> ImageData | None:
        """Resolve one message Image component into validated image data."""
        # Prefer AstrBot's built-in resolver when available; it understands
        # file://, base64://, data URI, local paths, and temporary URLs.
        convert = getattr(component, "convert_to_file_path", None)
        if callable(convert):
            try:
                path = await convert()
                if isinstance(path, str) and path.strip():
                    if image := await self.download_image(
                        path,
                        workspace_dir=workspace_dir,
                    ):
                        return image
            except Exception as exc:
                logger.debug(
                    f"{LOG} Image.convert_to_file_path 失败: {safe_log_error_body(exc)}"
                )

        candidates = self._iter_image_source_candidates(component)
        for candidate in candidates:
            if image := await self.download_image(
                candidate,
                workspace_dir=workspace_dir,
            ):
                return image

        # WeChat/aiocqhttp bridges often only provide a CQ cache file id.
        for candidate in candidates:
            if not self._looks_like_platform_file_id(candidate):
                continue
            resolved = await self._resolve_platform_image_ref(event, candidate)
            if not resolved:
                continue
            if image := await self.download_image(
                resolved,
                workspace_dir=workspace_dir,
            ):
                return image
        return None

    async def _extract_images_from_reply_component(
        self,
        component: Any,
        *,
        workspace_dir: str | None = None,
        event: AstrMessageEvent | None = None,
    ) -> list[ImageData]:
        """Extract images embedded in a Reply component chain."""
        images_data: list[ImageData] = []
        for attr in ("chain", "message", "origin", "content"):
            payload = getattr(component, attr, None)
            if not isinstance(payload, list):
                continue
            for sub_comp in payload:
                if not isinstance(sub_comp, Comp.Image):
                    continue
                if image := await self._image_data_from_component(
                    sub_comp,
                    workspace_dir=workspace_dir,
                    event=event,
                ):
                    images_data.append(image)
            if images_data:
                break
        return images_data

    async def _extract_quoted_images_via_astrbot(
        self,
        event: AstrMessageEvent,
        *,
        workspace_dir: str | None = None,
    ) -> list[ImageData]:
        """Fallback to AstrBot quoted-message parser for reply images."""
        try:
            from astrbot.core.utils.quoted_message_parser import (
                extract_quoted_message_images,
            )
        except Exception:
            return []

        try:
            image_refs = await extract_quoted_message_images(event)
        except Exception as exc:
            logger.warning(
                f"{LOG} 引用消息图片回退解析失败: {safe_log_error_body(exc)}"
            )
            return []

        images_data: list[ImageData] = []
        for ref in image_refs or []:
            if not isinstance(ref, str) or not ref.strip():
                continue
            cleaned = ref.strip()
            image = await self.download_image(cleaned, workspace_dir=workspace_dir)
            if image is None and self._looks_like_platform_file_id(cleaned):
                resolved = await self._resolve_platform_image_ref(event, cleaned)
                if resolved:
                    image = await self.download_image(
                        resolved,
                        workspace_dir=workspace_dir,
                    )
            if image:
                images_data.append(image)
            else:
                logger.warning(
                    f"{LOG} 引用消息参考图获取失败: {safe_log_url(cleaned)}"
                )
        return images_data


    def _reply_message_id(self, component: Any) -> str | None:
        """Return the replied message id from a Reply component when available."""
        for attr in ("id", "message_id", "msg_id"):
            value = getattr(component, attr, None)
            if value is None:
                continue
            cleaned = str(value).strip()
            if cleaned:
                return cleaned
        return None

    def _iter_dict_image_refs(self, payload: Any) -> list[str]:
        """Collect image file/url/path refs from a OneBot get_msg-like payload."""
        refs: list[str] = []
        seen: set[str] = set()

        def add(value: Any) -> None:
            if not isinstance(value, str):
                return
            cleaned = value.strip()
            if not cleaned or cleaned in seen:
                return
            seen.add(cleaned)
            refs.append(cleaned)

        def walk_segments(segments: Any) -> None:
            if not isinstance(segments, list):
                return
            for seg in segments:
                if not isinstance(seg, dict):
                    continue
                if str(seg.get("type") or "").lower() != "image":
                    continue
                data = seg.get("data") if isinstance(seg.get("data"), dict) else {}
                for key in ("url", "file", "path"):
                    add(data.get(key))
                    add(seg.get(key))

        if not isinstance(payload, dict):
            return refs

        data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
        if not isinstance(data, dict):
            return refs

        walk_segments(data.get("message"))
        walk_segments(data.get("message_chain"))
        raw_message = data.get("raw_message")
        if isinstance(raw_message, str) and "CQ:image" in raw_message:
            # Best-effort CQ parse for file=...
            import re as _re

            for match in _re.finditer(r"CQ:image,[^\]]*file=([^,\]]+)", raw_message):
                add(match.group(1))
        return refs

    async def _extract_images_via_get_msg(
        self,
        event: AstrMessageEvent,
        *,
        workspace_dir: str | None = None,
    ) -> list[ImageData]:
        """Fallback: resolve reply id via OneBot get_msg (WeChatBridge supports this)."""
        bot = getattr(event, "bot", None)
        api = getattr(bot, "api", None)
        call_action = getattr(api, "call_action", None)
        if not callable(call_action):
            return []

        reply_ids: list[str] = []
        for component in getattr(getattr(event, "message_obj", None), "message", None) or []:
            if not isinstance(component, Comp.Reply):
                continue
            reply_id = self._reply_message_id(component)
            if reply_id and reply_id not in reply_ids:
                reply_ids.append(reply_id)
        if not reply_ids:
            return []

        # WeChatBridge may still be recovering the quoted inbound image.
        # One short retry is enough for the common race; keep QQ path single-shot.
        attempts = 2 if self._event_hints_wechat_name(event) else 1
        images_data: list[ImageData] = []
        for reply_id in reply_ids:
            payload = None
            for attempt in range(attempts):
                for action, params in (
                    ("get_msg", {"message_id": reply_id}),
                    ("get_msg", {"id": reply_id}),
                    ("get_message", {"message_id": reply_id}),
                ):
                    try:
                        payload = await call_action(action, **params)
                        break
                    except Exception:
                        continue
                if payload is not None and self._iter_dict_image_refs(payload):
                    break
                if attempt + 1 < attempts:
                    try:
                        import asyncio as _asyncio

                        await _asyncio.sleep(0.8)
                    except Exception:
                        pass
                    payload = None
            if payload is None:
                logger.debug(f"{LOG} get_msg 无结果: reply_id={reply_id}")
                continue

            for ref in self._iter_dict_image_refs(payload):
                image = await self.download_image(ref, workspace_dir=workspace_dir)
                if image is None and self._looks_like_platform_file_id(ref):
                    resolved = await self._resolve_platform_image_ref(event, ref)
                    if resolved:
                        image = await self.download_image(
                            resolved,
                            workspace_dir=workspace_dir,
                        )
                if image:
                    images_data.append(image)
                else:
                    logger.warning(
                        f"{LOG} get_msg 参考图获取失败: {safe_log_url(ref)}"
                    )
        return images_data

    async def fetch_images_from_event(
        self,
        event: AstrMessageEvent,
        avatar_user_ids: set[str] | None = None,
    ) -> list[ImageData]:
        """Extract direct, replied, and mentioned-user images from an event."""
        images_data: list[ImageData] = []
        if avatar_user_ids is None:
            avatar_user_ids = set()

        if not event.message_obj or not event.message_obj.message:
            return images_data

        workspace_dir = self.workspace_dir_for_origin(
            getattr(event, "unified_msg_origin", None)
        )
        bot_self_id = str(event.get_self_id()) if hasattr(event, "get_self_id") else ""
        should_skip_leading_bot_at = self._should_skip_leading_bot_at(
            event,
            bot_self_id,
        )
        leading_bot_at_skipped = False
        has_reply_component = False
        reply_images_found = False
        direct_images_found = False

        for component in event.message_obj.message:
            try:
                if isinstance(component, Comp.Image):
                    # Handle directly sent images.
                    if image := await self._image_data_from_component(
                        component,
                        workspace_dir=workspace_dir,
                        event=event,
                    ):
                        direct_images_found = True
                        images_data.append(image)
                elif isinstance(component, Comp.Reply):
                    # Handle images inside replied messages.
                    has_reply_component = True
                    reply_images = await self._extract_images_from_reply_component(
                        component,
                        workspace_dir=workspace_dir,
                        event=event,
                    )
                    if reply_images:
                        reply_images_found = True
                        images_data.extend(reply_images)
                elif isinstance(component, Comp.At):
                    # Handle mentioned-user avatars.
                    if hasattr(component, "qq") and component.qq != "all":
                        uid = str(component.qq).strip()
                        if (
                            should_skip_leading_bot_at
                            and not leading_bot_at_skipped
                            and uid == bot_self_id
                        ):
                            leading_bot_at_skipped = True
                            continue
                        if uid in avatar_user_ids:
                            continue
                        avatar_user_ids.add(uid)
                        avatar_image = await self.get_avatar(uid, event=event)
                        if avatar_image is not None:
                            images_data.append(avatar_image)
                        else:
                            logger.warning(
                                f"{LOG} 未能获取被 @ 用户头像作为参考图: "
                                f"user_id={mask_sensitive(uid)}"
                            )
            except Exception as e:
                logger.error(
                    f"{LOG} 提取消息组件图片失败: {safe_log_error_body(e)}",
                    exc_info=True,
                )
                continue

        # WeChatBridge / aiocqhttp often only embeds reply id, and may put the
        # refilled image as a top-level Image segment or only via get_msg.
        # Skip fallback when Reply.chain already had images, or when a top-level
        # Image (bridge refill) already supplied the reference.
        if has_reply_component and not reply_images_found and not direct_images_found:
            fallback_images = await self._extract_quoted_images_via_astrbot(
                event,
                workspace_dir=workspace_dir,
            )
            if fallback_images:
                images_data.extend(fallback_images)
                logger.info(
                    f"{LOG} 已通过引用消息回退解析获取 {len(fallback_images)} 张参考图"
                )
            else:
                get_msg_images = await self._extract_images_via_get_msg(
                    event,
                    workspace_dir=workspace_dir,
                )
                if get_msg_images:
                    images_data.extend(get_msg_images)
                    logger.info(
                        f"{LOG} 已通过 get_msg 回退解析获取 {len(get_msg_images)} 张参考图"
                    )
                elif not images_data:
                    logger.warning(f"{LOG} 检测到引用消息，但未能提取到任何参考图")

        return images_data

    def save_generated_image(self, task_id: str, img_bytes: bytes) -> str | None:
        """Save generated image bytes to the temporary directory."""
        try:
            mime = self._detect_mime_type(img_bytes)
            extension = GENERATED_IMAGE_EXTENSIONS.get(mime, ".png")
            file_name = f"gen_{task_id}_{int(time.time())}_{hashlib.md5(img_bytes).hexdigest()[:6]}{extension}"
            file_path = os.path.join(self._temp_dir, file_name)
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            return file_path
        except Exception as exc:
            logger.error(
                f"{LOG} 保存图片失败: {safe_log_error_body(exc)}", exc_info=True
            )
            return None
