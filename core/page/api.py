"""Backend API handlers for the plugin Dashboard Page."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import mimetypes
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from astrbot.api.web import (
    PluginUploadFile,
    error_response,
    file_response,
    json_response,
    request,
)

from ..shared.logging import safe_log_text
from ..shared.types import ImageCapability
from ..tasks.models import GenerationTaskRecord

PLUGIN_NAME = "astrbot_plugin_image_generation"
PAGE_PREVIEW_MAX_BYTES = 12 * 1024 * 1024
PAGE_IMAGE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/heic": ".heic",
    "image/heif": ".heif",
}
PAGE_IMAGE_MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".heic": "image/heic",
    ".heif": "image/heif",
}


class ImageGenerationPageAPI:
    """Register and serve backend endpoints used by the Dashboard Page."""

    def __init__(self, plugin: Any) -> None:
        self.plugin = plugin

    def register(self) -> None:
        """Register backend APIs used by the plugin Dashboard Page."""
        page_routes = [
            ("/page/state", self.page_state, ["GET"], "Image generation Page state"),
            (
                "/page/stats",
                self.page_stats,
                ["GET"],
                "Image generation Page statistics",
            ),
            ("/page/tasks", self.page_tasks, ["GET"], "Image generation Page tasks"),
            (
                "/page/tasks/<task_id>",
                self.page_task_detail,
                ["GET"],
                "Image generation Page task detail",
            ),
            (
                "/page/tasks/<task_id>/cancel",
                self.page_cancel_task,
                ["POST"],
                "Cancel image generation Page task",
            ),
            (
                "/page/tasks/<task_id>/images/<image_index>/download",
                self.page_download_task_image,
                ["GET"],
                "Download generated image from Page",
            ),
            (
                "/page/tasks/<task_id>/images/<image_index>/preview",
                self.page_preview_task_image,
                ["GET"],
                "Preview generated image from Page",
            ),
            (
                "/page/gallery",
                self.page_gallery,
                ["GET"],
                "Image generation Page gallery",
            ),
            (
                "/page/reference/upload",
                self.page_upload_reference,
                ["POST"],
                "Upload reference image from Page",
            ),
            (
                "/page/generate",
                self.page_generate,
                ["POST"],
                "Submit image generation task from Page",
            ),
        ]
        for route, handler, methods, description in page_routes:
            self.plugin.context.register_web_api(
                f"/{PLUGIN_NAME}{route}",
                handler,
                methods,
                description,
            )

    def _page_datetime(self, value: Any) -> str | None:
        """Serialize a datetime-like value for Page JSON responses."""
        return value.isoformat(timespec="seconds") if value else None

    def _page_task_payload(
        self,
        record: GenerationTaskRecord,
        *,
        include_detail: bool = False,
    ) -> dict[str, Any]:
        """Build a safe JSON payload for one generation task record."""
        request_stats = record.request_stats
        result_count = record.result_count or len(record.result_paths)
        finished = request_stats.get("finished", 0)
        total = request_stats.get("total", record.requested_count)
        progress_percent = int((finished / total) * 100) if total else 0
        template_fields = self._parse_template_fields(
            record.preset, record.preset_label
        )
        payload: dict[str, Any] = {
            "task_id": record.task_id,
            "status": record.status.value,
            "status_label": record.status_label,
            "active": record.is_active,
            "source": record.source,
            "unified_msg_origin": str(record.unified_msg_origin or "").strip(),
            "model": record.model or "",
            "message": record.message,
            "error": record.error,
            "prompt_summary": record.prompt_summary,
            "reference_image_count": record.reference_image_count,
            "requested_count": record.requested_count,
            "result_count": result_count,
            "aspect_ratio": record.aspect_ratio,
            "resolution": record.resolution,
            "preset": record.preset or "",
            "preset_label": record.preset_label,
            "presets": template_fields["presets"],
            "personas": template_fields["personas"],
            "template_summary": template_fields["template_summary"],
            "template_label": template_fields["template_label"],
            "created_at": self._page_datetime(record.created_at),
            "started_at": self._page_datetime(record.started_at),
            "finished_at": self._page_datetime(record.finished_at),
            "duration_seconds": record.duration_seconds,
            "queued_seconds": record.queued_seconds,
            "current_index": record.current_index,
            "retry_attempt": record.retry_attempt,
            "max_retry_attempts": record.max_retry_attempts,
            "request_stats": request_stats,
            "progress_percent": max(0, min(progress_percent, 100)),
            "result_images": [
                self._page_image_payload(record, index, path)
                for index, path in enumerate(record.result_paths, 1)
            ],
        }
        if include_detail:
            payload["prompt"] = record.prompt or record.prompt_summary or ""
            payload["items"] = [
                {
                    "index": item.index,
                    "status": item.status.value,
                    "result_count": item.result_count,
                    "error": item.error,
                    "retry_attempts": item.retry_attempts,
                    "max_retry_attempts": item.max_retry_attempts,
                }
                for item in sorted(
                    record.items.values(), key=lambda task_item: task_item.index
                )
            ]
        return payload

    def _uploaded_image_path(self, token: str) -> Path | None:
        """Resolve one Page upload token to a safe local path."""
        safe_token = str(token or "").strip()
        if not safe_token or any(part in safe_token for part in ("/", "\\", "..")):
            return None
        path = (self.plugin.page_upload_dir / safe_token).resolve()
        try:
            path.relative_to(self.plugin.page_upload_dir.resolve())
        except ValueError:
            return None
        if not path.is_file():
            return None
        return path

    def _result_image_path(
        self,
        record: GenerationTaskRecord,
        image_index: str | int,
    ) -> Path | None:
        """Resolve one generated image index to a safe result path."""
        try:
            index = int(str(image_index).strip())
        except (TypeError, ValueError):
            return None
        if index < 1 or index > len(record.result_paths):
            return None
        path = Path(record.result_paths[index - 1]).resolve()
        allowed_roots = [
            self.plugin.image_temp_dir.resolve(),
            self.plugin.astrbot_temp_dir.resolve(),
        ]
        for root in allowed_roots:
            try:
                path.relative_to(root)
                if path.is_file():
                    return path
            except ValueError:
                continue
        return None

    def _page_image_mime_type(self, path: Path) -> str:
        """Infer a safe image MIME type from a result path."""
        suffix = path.suffix.lower()
        if suffix in PAGE_IMAGE_MIME_TYPES:
            return PAGE_IMAGE_MIME_TYPES[suffix]
        guessed, _ = mimetypes.guess_type(path.name)
        if guessed and guessed.startswith("image/"):
            return guessed
        return "application/octet-stream"

    def _page_image_payload(
        self,
        record: GenerationTaskRecord,
        index: int,
        path_value: str,
    ) -> dict[str, Any]:
        """Build a safe JSON payload for one generated image entry."""
        filename = Path(path_value).name
        path = self._result_image_path(record, index)
        size = path.stat().st_size if path else 0
        return {
            "index": index,
            "filename": filename,
            "extension": Path(filename).suffix.lower().lstrip("."),
            "mime_type": self._page_image_mime_type(Path(filename)),
            "size": size,
            "available": bool(path),
            "download_endpoint": (
                f"page/tasks/{record.task_id}/images/{index}/download"
            ),
            "preview_endpoint": (f"page/tasks/{record.task_id}/images/{index}/preview"),
        }

    def _parse_page_datetime(self, value: Any) -> datetime | None:
        """Parse an ISO datetime string from Page query parameters."""
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            return datetime.fromisoformat(raw.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        except ValueError:
            return None

    def _gallery_items_for_record(
        self,
        record: GenerationTaskRecord,
    ) -> list[dict[str, Any]]:
        """Build gallery items from one generation task record."""
        generated_at = (
            self._page_datetime(record.finished_at)
            or self._page_datetime(record.started_at)
            or self._page_datetime(record.created_at)
        )
        items: list[dict[str, Any]] = []
        for index, path_value in enumerate(record.result_paths, 1):
            image = self._page_image_payload(record, index, path_value)
            items.append(
                {
                    "id": f"{record.task_id}:{index}",
                    "task_id": record.task_id,
                    "status": record.status.value,
                    "status_label": record.status_label,
                    "source": record.source,
                    "model": record.model or "",
                    "prompt_summary": record.prompt_summary,
                    "preset": record.preset or "",
                    "preset_label": record.preset_label,
                    "aspect_ratio": record.aspect_ratio,
                    "resolution": record.resolution,
                    "created_at": self._page_datetime(record.created_at),
                    "finished_at": self._page_datetime(record.finished_at),
                    "generated_at": generated_at,
                    "image_index": index,
                    **image,
                }
            )
        return items

    def _count_top(
        self, counter: Counter[str], *, limit: int = 8
    ) -> list[dict[str, Any]]:
        """Convert a counter into a sorted top-N list for charts."""
        return [
            {"name": name, "count": count}
            for name, count in counter.most_common(max(1, limit))
            if name
        ]

    def _record_stamp(self, record: GenerationTaskRecord) -> datetime | None:
        """Pick the best timestamp for statistics aggregation."""
        return record.finished_at or record.started_at or record.created_at

    def _build_trend_series(
        self,
        stamps: list[datetime],
        *,
        days: int,
        now: datetime | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Build a continuous trend series for the selected stats range.

        Args:
            stamps: Task timestamps inside the filtered window.
            days: Selected range in days. ``1`` uses hourly buckets; other
                positive values use daily buckets; ``0`` spans all history.
            now: Optional clock override for deterministic tests.

        Returns:
            A tuple of ``(granularity, points)`` where each point contains
            ``key``, ``label``, ``count``, and optional ``date``/``hour``.
        """
        current = now or datetime.now()
        if days == 1:
            end_hour = current.replace(minute=0, second=0, microsecond=0)
            start_hour = end_hour - timedelta(hours=23)
            bucket_counts: Counter[str] = Counter()
            for stamp in stamps:
                hour_key = stamp.replace(minute=0, second=0, microsecond=0)
                if hour_key < start_hour or hour_key > end_hour:
                    continue
                bucket_counts[hour_key.strftime("%Y-%m-%d %H:00")] += 1
            points: list[dict[str, Any]] = []
            cursor = start_hour
            while cursor <= end_hour:
                key = cursor.strftime("%Y-%m-%d %H:00")
                points.append(
                    {
                        "key": key,
                        "date": cursor.date().isoformat(),
                        "hour": cursor.hour,
                        "label": cursor.strftime("%H:00"),
                        "count": bucket_counts.get(key, 0),
                    }
                )
                cursor += timedelta(hours=1)
            return "hour", points

        if days > 0:
            end_day = current.date()
            start_day = end_day - timedelta(days=days - 1)
        else:
            if not stamps:
                end_day = current.date()
                start_day = end_day
            else:
                start_day = min(stamp.date() for stamp in stamps)
                end_day = max(stamp.date() for stamp in stamps)
                if end_day < current.date():
                    end_day = current.date()

        day_counts: Counter[str] = Counter()
        for stamp in stamps:
            day_key = stamp.date().isoformat()
            if stamp.date() < start_day or stamp.date() > end_day:
                continue
            day_counts[day_key] += 1

        points = []
        cursor_day = start_day
        while cursor_day <= end_day:
            key = cursor_day.isoformat()
            points.append(
                {
                    "key": key,
                    "date": key,
                    "label": cursor_day.strftime("%m-%d"),
                    "count": day_counts.get(key, 0),
                }
            )
            cursor_day += timedelta(days=1)
        return "day", points

    def _page_stats_payload(self, *, days: int = 7) -> dict[str, Any]:
        """Aggregate generation statistics from tracked task history."""
        safe_days = max(0, int(days or 0))
        now = datetime.now()
        since = now - timedelta(days=safe_days) if safe_days > 0 else None
        if safe_days == 1:
            since = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=23)
        records = self.plugin.task_manager.list_generation_tasks(
            include_finished=True,
            limit=1000,
        )
        filtered: list[GenerationTaskRecord] = []
        for record in records:
            stamp = self._record_stamp(record)
            if since and stamp and stamp < since:
                continue
            filtered.append(record)

        status_counter: Counter[str] = Counter()
        source_counter: Counter[str] = Counter()
        model_counter: Counter[str] = Counter()
        model_success_counter: Counter[str] = Counter()
        model_terminal_counter: Counter[str] = Counter()
        user_counter: Counter[str] = Counter()
        stamps: list[datetime] = []
        total_images = 0
        available_images = 0
        total_duration = 0.0
        duration_samples = 0
        active_count = 0
        success_count = 0
        failed_count = 0
        cancelled_count = 0

        for record in filtered:
            model_name = record.model or "unknown"
            status_counter[record.status.value] += 1
            source_counter[record.source or "unknown"] += 1
            model_counter[model_name] += 1
            user_counter[
                str(record.unified_msg_origin or "").strip() or "anonymous"
            ] += 1
            stamp = self._record_stamp(record)
            if stamp:
                stamps.append(stamp)
            if record.is_active:
                active_count += 1
            if record.status.value == "succeeded":
                success_count += 1
                model_success_counter[model_name] += 1
                model_terminal_counter[model_name] += 1
            elif record.status.value == "failed":
                failed_count += 1
                model_terminal_counter[model_name] += 1
            elif record.status.value == "cancelled":
                cancelled_count += 1
                model_terminal_counter[model_name] += 1
            total_images += record.result_count or len(record.result_paths)
            for index, path_value in enumerate(record.result_paths, 1):
                if self._result_image_path(record, index):
                    available_images += 1
            if record.duration_seconds is not None:
                total_duration += float(record.duration_seconds)
                duration_samples += 1

        terminal_count = success_count + failed_count + cancelled_count
        success_rate = (
            round((success_count / terminal_count) * 100, 1) if terminal_count else 0.0
        )
        avg_duration = (
            round(total_duration / duration_samples, 2) if duration_samples else 0.0
        )
        granularity, trend_points = self._build_trend_series(
            stamps,
            days=safe_days,
            now=now,
        )
        return {
            "days": safe_days,
            "trend_granularity": granularity,
            "summary": {
                "total_tasks": len(filtered),
                "active_tasks": active_count,
                "success_tasks": success_count,
                "failed_tasks": failed_count,
                "cancelled_tasks": cancelled_count,
                "success_rate": success_rate,
                "total_images": total_images,
                "available_images": available_images,
                "avg_duration_seconds": avg_duration,
                "unique_users": len(
                    [name for name in user_counter if name != "anonymous"]
                ),
                "unique_models": len(
                    [name for name in model_counter if name != "unknown"]
                ),
            },
            "status_distribution": self._count_top(status_counter, limit=10),
            "source_distribution": self._count_top(source_counter, limit=10),
            "model_distribution": [
                {
                    "name": name,
                    "count": count,
                    "success_count": model_success_counter.get(name, 0),
                    "terminal_count": model_terminal_counter.get(name, 0),
                    "success_rate": (
                        round(
                            (
                                model_success_counter.get(name, 0)
                                / model_terminal_counter[name]
                            )
                            * 100,
                            1,
                        )
                        if model_terminal_counter.get(name, 0)
                        else 0.0
                    ),
                }
                for name, count in model_counter.most_common(10)
                if name
            ],
            "user_distribution": self._count_top(user_counter, limit=10),
            "trend": trend_points,
        }

    async def page_state(self):
        """Return plugin state used to initialize the Dashboard Page.

        Returns:
            A JSON response with model, template, capability, and runtime state.
        """
        plugin = self.plugin
        adapter_config = plugin.config_manager.adapter_config
        capabilities = (
            plugin.generator.adapter.get_capabilities()
            if plugin.generator and plugin.generator.adapter
            else ImageCapability.NONE
        )
        current_model = (
            f"{adapter_config.name}/{adapter_config.model}" if adapter_config else ""
        )
        available_models: list[str] = []
        for provider in getattr(plugin.config_manager, "_all_provider_configs", []):
            provider_name = provider.name.strip()
            for model in provider.available_models:
                available_models.append(
                    f"{provider_name}/{model}" if provider_name else model
                )
        return json_response(
            {
                "initialized": bool(plugin.generator and plugin.generator.adapter),
                "has_api_key": plugin.has_required_api_key(),
                "current_model": current_model,
                "available_models": available_models,
                "default_image_count": plugin.config_manager.default_image_count,
                "max_image_count": plugin.config_manager.max_image_count,
                "default_aspect_ratio": plugin.config_manager.default_aspect_ratio,
                "default_resolution": plugin.config_manager.default_resolution,
                "supports_image_to_image": bool(
                    capabilities & ImageCapability.IMAGE_TO_IMAGE
                ),
                "supports_aspect_ratio": bool(
                    capabilities & ImageCapability.ASPECT_RATIO
                ),
                "supports_resolution": bool(capabilities & ImageCapability.RESOLUTION),
                "presets": [
                    {"name": name, "summary": safe_log_text(value, 120)}
                    for name, value in plugin.config_manager.presets.items()
                ],
                "personas": [
                    {
                        "name": name,
                        "summary": safe_log_text(persona.prompt, 120),
                        "has_image": bool(persona.image),
                    }
                    for name, persona in plugin.config_manager.personas.items()
                ],
                "queue": {
                    "can_accept": plugin.task_manager.can_accept_generation_task(),
                    "max_running": plugin.config_manager.max_running_generation_tasks,
                    "max_queued": plugin.config_manager.max_queued_generation_tasks,
                },
                "history": {
                    "enabled": plugin.config_manager.enable_generation_task_history,
                    "limit": plugin.config_manager.generation_task_history_limit,
                    "retention_days": plugin.config_manager.generation_task_history_retention_days,
                },
            }
        )

    async def page_stats(self):
        """Return aggregated dashboard statistics for the overview page.

        Returns:
            A JSON response with summary cards and chart-ready distributions.
        """
        days_raw = str(request.query.get("days", "7") or "7").strip()
        try:
            days = max(0, int(days_raw))
        except ValueError:
            return error_response("days 必须是非负整数", status_code=400)
        return json_response(self._page_stats_payload(days=days))

    def _parse_template_fields(
        self,
        preset: str | None,
        preset_label: str | None,
    ) -> dict[str, Any]:
        """Parse stored template summary into preset and persona names.

        Args:
            preset: Stored template summary text (names or labeled summary).
            preset_label: Stored template category label.

        Returns:
            A dict with presets, personas, and display values.
        """
        summary = str(preset or "").strip()
        label = str(preset_label or "").strip()
        presets: list[str] = []
        personas: list[str] = []

        if summary:
            if "预设:" in summary or "人设:" in summary:
                for part in summary.split("；"):
                    chunk = part.strip()
                    if chunk.startswith("预设:"):
                        names = chunk[len("预设:") :].strip()
                        if names:
                            presets.extend(
                                [
                                    name.strip()
                                    for name in names.replace(",", "、").split("、")
                                    if name.strip()
                                ]
                            )
                    elif chunk.startswith("人设:"):
                        names = chunk[len("人设:") :].strip()
                        if names:
                            personas.extend(
                                [
                                    name.strip()
                                    for name in names.replace(",", "、").split("、")
                                    if name.strip()
                                ]
                            )
            elif label in {"预设", "preset"}:
                presets = [
                    name.strip()
                    for name in summary.replace(",", "、").split("、")
                    if name.strip()
                ]
            elif label in {"人设", "persona"}:
                personas = [
                    name.strip()
                    for name in summary.replace(",", "、").split("、")
                    if name.strip()
                ]
            elif label in {"预设/人设", "preset/persona"}:
                # Older mixed labels without structured text: keep as summary only.
                pass
            else:
                # Unknown label: treat the summary as a generic template name list.
                presets = [
                    name.strip()
                    for name in summary.replace(",", "、").split("、")
                    if name.strip()
                ]

        display_parts: list[str] = []
        if presets:
            display_parts.append(f"预设: {'、'.join(presets)}")
        if personas:
            display_parts.append(f"人设: {'、'.join(personas)}")
        display = "；".join(display_parts) if display_parts else summary

        return {
            "presets": presets,
            "personas": personas,
            "template_summary": display or summary,
            "template_label": label
            or (
                "预设/人设"
                if presets and personas
                else ("预设" if presets else ("人设" if personas else ""))
            ),
        }

    async def page_tasks(self):
        """Return generation tasks for the Dashboard Page.

        Returns:
            A JSON response containing filtered and paginated task summaries.
        """
        status_filter = str(request.query.get("status", "all") or "all").strip()
        source_filter = str(request.query.get("source", "") or "").strip().lower()
        model_filter = str(request.query.get("model", "") or "").strip().lower()
        keyword = str(request.query.get("keyword", "") or "").strip().lower()
        days_raw = str(request.query.get("days", "0") or "0").strip()
        try:
            days = max(0, int(days_raw))
        except ValueError:
            return error_response("days 必须是非负整数", status_code=400)
        limit = max(1, min(request.query.get("limit", 30, type=int), 200))
        offset = max(0, request.query.get("offset", 0, type=int))
        since = self._parse_page_datetime(request.query.get("since"))
        until = self._parse_page_datetime(request.query.get("until"))
        if days > 0 and since is None:
            since = datetime.now() - timedelta(days=days)

        # Scan full local history so the queue can page through all saved tasks.
        scan_limit = min(
            5000,
            max(
                self.plugin.config_manager.generation_task_history_limit,
                limit + offset,
                200,
            ),
        )
        records = self.plugin.task_manager.list_generation_tasks(
            include_finished=True,
            limit=scan_limit,
        )

        filtered: list[GenerationTaskRecord] = []
        model_names: set[str] = set()
        source_names: set[str] = set()
        for record in records:
            record_model = str(record.model or "").strip()
            record_source = str(record.source or "").strip()
            if record_model:
                model_names.add(record_model)
            if record_source:
                source_names.add(record_source)

            if status_filter == "active":
                if not record.is_active:
                    continue
            elif status_filter not in {"", "all"}:
                if record.status.value != status_filter:
                    continue

            if source_filter and source_filter not in record_source.lower():
                continue
            if model_filter and model_filter not in record_model.lower():
                continue

            record_time = record.finished_at or record.started_at or record.created_at
            if since and record_time and record_time < since:
                continue
            if until and record_time and record_time > until:
                continue

            if keyword:
                haystack = " ".join(
                    [
                        record.task_id,
                        record.prompt_summary or "",
                        record.prompt or "",
                        record.preset or "",
                        record.preset_label or "",
                        record.source or "",
                        record.model or "",
                        record.status.value,
                        record.unified_msg_origin or "",
                        record.message or "",
                        record.error or "",
                    ]
                ).lower()
                if keyword not in haystack:
                    continue
            filtered.append(record)

        total = len(filtered)
        page_records = filtered[offset : offset + limit]
        return json_response(
            {
                "tasks": [self._page_task_payload(record) for record in page_records],
                "total": total,
                "offset": offset,
                "limit": limit,
                "models": sorted(model_names),
                "sources": sorted(source_names),
            }
        )

    async def page_task_detail(self, task_id: str):
        """Return one generation task detail for the Dashboard Page.

        Args:
            task_id: Generation task ID from the route.

        Returns:
            A JSON response with task detail or an error response.
        """
        normalized_task_id = str(task_id or "").strip()
        record = self.plugin.task_manager.get_generation_task(normalized_task_id)
        if not record:
            return error_response(f"任务不存在: {normalized_task_id}", status_code=404)
        return json_response(
            {"task": self._page_task_payload(record, include_detail=True)}
        )

    async def page_cancel_task(self, task_id: str):
        """Cancel an active generation task from the Dashboard Page.

        Args:
            task_id: Generation task ID from the route.

        Returns:
            A JSON response with operation status.
        """
        normalized_task_id = str(task_id or "").strip()
        ok, message = self.plugin.task_manager.cancel_generation_task(
            normalized_task_id
        )
        status_code = 200 if ok else 400
        return json_response(
            {"ok": ok, "message": message, "task_id": normalized_task_id},
            status_code=status_code,
        )

    async def page_download_task_image(self, task_id: str, image_index: str):
        """Download one generated image file through a safe Page endpoint.

        Args:
            task_id: Generation task ID from the route.
            image_index: 1-based image index in the task result list.

        Returns:
            A file response or an error response.
        """
        normalized_task_id = str(task_id or "").strip()
        record = self.plugin.task_manager.get_generation_task(normalized_task_id)
        if not record:
            return error_response(f"任务不存在: {normalized_task_id}", status_code=404)
        path = self._result_image_path(record, image_index)
        if not path:
            return error_response("图片不存在或不可访问", status_code=404)
        return file_response(path, filename=path.name)

    async def page_preview_task_image(self, task_id: str, image_index: str):
        """Return a small inline preview payload for one generated image.

        Args:
            task_id: Generation task ID from the route.
            image_index: 1-based image index in the task result list.

        Returns:
            A JSON response with a data URL preview, or an error response.
        """
        normalized_task_id = str(task_id or "").strip()
        record = self.plugin.task_manager.get_generation_task(normalized_task_id)
        if not record:
            return error_response(f"任务不存在: {normalized_task_id}", status_code=404)
        path = self._result_image_path(record, image_index)
        if not path:
            return error_response("图片不存在或不可访问", status_code=404)
        size = path.stat().st_size
        if size > PAGE_PREVIEW_MAX_BYTES:
            return error_response(
                "图片过大，请改用下载查看",
                status_code=413,
                data={
                    "download_endpoint": (
                        f"page/tasks/{normalized_task_id}/images/{image_index}/download"
                    ),
                    "size": size,
                },
            )
        mime_type = self._page_image_mime_type(path)
        data = path.read_bytes()
        return json_response(
            {
                "task_id": normalized_task_id,
                "image_index": int(str(image_index).strip()),
                "filename": path.name,
                "mime_type": mime_type,
                "size": size,
                "data_url": (
                    f"data:{mime_type};base64,{base64.b64encode(data).decode('ascii')}"
                ),
            }
        )

    async def page_gallery(self):
        """Return generated image gallery items from task history.

        Returns:
            A JSON response containing filtered gallery image entries.
        """
        status_filter = str(request.query.get("status", "all") or "all").strip()
        model_filter = str(request.query.get("model", "") or "").strip().lower()
        keyword = str(request.query.get("keyword", "") or "").strip().lower()
        days_raw = str(request.query.get("days", "0") or "0").strip()
        try:
            days = max(0, int(days_raw))
        except ValueError:
            return error_response("days 必须是非负整数", status_code=400)
        limit = max(1, min(request.query.get("limit", 60, type=int), 200))
        offset = max(0, request.query.get("offset", 0, type=int))
        since = self._parse_page_datetime(request.query.get("since"))
        until = self._parse_page_datetime(request.query.get("until"))
        if days > 0 and since is None:
            since = datetime.now() - timedelta(days=days)

        # Scan more task records than page size because one task can yield
        # multiple gallery images.
        scan_limit = min(1000, max((limit + offset) * 5, 200))
        records = self.plugin.task_manager.list_generation_tasks(
            include_finished=True,
            limit=scan_limit,
        )
        items: list[dict[str, Any]] = []
        model_names: set[str] = set()
        for record in records:
            record_model = str(record.model or "").strip()
            if record_model:
                model_names.add(record_model)
            if (
                status_filter not in {"", "all"}
                and record.status.value != status_filter
            ):
                continue
            if model_filter and model_filter not in record_model.lower():
                continue
            record_time = record.finished_at or record.started_at or record.created_at
            if since and record_time and record_time < since:
                continue
            if until and record_time and record_time > until:
                continue
            if keyword:
                haystack = " ".join(
                    [
                        record.task_id,
                        record.prompt_summary or "",
                        record.preset or "",
                        record.source or "",
                        record.model or "",
                        record.status.value,
                    ]
                ).lower()
                if keyword not in haystack:
                    continue
            items.extend(self._gallery_items_for_record(record))

        total = len(items)
        page_items = items[offset : offset + limit]
        return json_response(
            {
                "items": page_items,
                "total": total,
                "offset": offset,
                "limit": limit,
                "available_count": sum(
                    1 for item in page_items if item.get("available")
                ),
                "models": sorted(model_names),
            }
        )

    async def page_upload_reference(self):
        """Upload and validate one reference image for Page generation.

        Returns:
            A JSON response containing an opaque upload token.
        """
        files = await request.files()
        upload = files.get("file")
        if not isinstance(upload, PluginUploadFile):
            return error_response("缺少上传文件", status_code=400)
        data = await upload.read()
        max_bytes = (
            self.plugin.config_manager.usage_settings.max_image_size_mb * 1024 * 1024
        )
        if not data:
            return error_response("上传文件为空", status_code=400)
        if len(data) > max_bytes:
            return error_response(
                f"参考图超过大小限制 ({self.plugin.config_manager.usage_settings.max_image_size_mb}MB)",
                status_code=400,
            )
        image_data = self.plugin.image_processor.validate_image_data(
            data,
            log_source=upload.filename or "Page upload",
        )
        if not image_data:
            return error_response("上传文件不是受支持的图片", status_code=400)
        suffix = PAGE_IMAGE_EXTENSIONS.get(image_data.mime_type, ".png")
        digest = hashlib.md5(data).hexdigest()[:12]
        token = (
            f"upload_{int(asyncio.get_running_loop().time() * 1000)}_{digest}{suffix}"
        )
        target = (self.plugin.page_upload_dir / token).resolve()
        try:
            target.relative_to(self.plugin.page_upload_dir.resolve())
        except ValueError:
            return error_response("上传路径无效", status_code=400)
        with target.open("wb") as output:
            output.write(data)
        return json_response(
            {
                "token": token,
                "filename": Path(upload.filename or token).name,
                "mime_type": image_data.mime_type,
                "size": len(data),
            }
        )

    async def page_generate(self):
        """Submit one image generation task from the Dashboard Page.

        Returns:
            A JSON response with submitted task information.
        """
        plugin = self.plugin
        payload = await request.json(default={})
        if not isinstance(payload, dict):
            return error_response("请求体必须是 JSON 对象", status_code=400)
        prompt = str(payload.get("prompt") or "").strip()
        image_count = plugin.normalize_image_count(payload.get("image_count"))
        aspect_ratio = str(
            payload.get("aspect_ratio") or plugin.config_manager.default_aspect_ratio
        ).strip()
        resolution = str(
            payload.get("resolution") or plugin.config_manager.default_resolution
        ).strip()
        model = str(payload.get("model") or "").strip()
        presets = payload.get("presets") or None
        personas = payload.get("personas") or None
        upload_tokens = payload.get("reference_tokens") or []
        reference_sources = [
            str(path)
            for token in upload_tokens
            if (path := self._uploaded_image_path(str(token)))
        ]
        if model and model != (
            f"{plugin.config_manager.adapter_config.name}/{plugin.config_manager.adapter_config.model}"
            if plugin.config_manager.adapter_config
            else ""
        ):
            plugin.config_manager.save_model_setting(model)
            plugin.config_manager.reload()
            plugin.reload_runtime_settings()
            if plugin.generator and plugin.config_manager.adapter_config:
                await plugin.generator.update_adapter(
                    plugin.config_manager.adapter_config
                )
                plugin.generation_executor.update_generator(plugin.generator)

        # Page generation runs from Dashboard auth context. Prefer the signed-in
        # WebUI username so overview statistics can attribute tasks correctly.
        webui_username = str(getattr(request, "username", None) or "").strip()
        page_user_origin = (
            f"webui:{webui_username}" if webui_username else "webui:admin"
        )

        result = await plugin.public_api.submit_generation_task(
            prompt=prompt,
            source="Page",
            unified_msg_origin=page_user_origin,
            image_count=image_count,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            reference_image_sources=reference_sources,
            presets=presets,
            personas=personas,
            is_admin=True,
        )
        if not result.ok:
            return error_response(
                result.message,
                status_code=400,
                data={"code": result.code, "error": result.error},
            )
        record = plugin.task_manager.get_generation_task(result.task_id or "")
        return json_response(
            {
                "ok": True,
                "message": result.message,
                "task_id": result.task_id,
                "task": self._page_task_payload(record) if record else None,
            }
        )
