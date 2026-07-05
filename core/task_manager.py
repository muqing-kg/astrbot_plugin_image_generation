from __future__ import annotations

import asyncio
import functools
import inspect
import json
import os
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from astrbot.api import logger

from .logging_utils import (
    format_optional,
    format_seconds,
    log_prefix,
    mask_sensitive,
    safe_log_error_body,
    safe_log_text,
)


LOG = log_prefix("TaskManager")
DEFAULT_GENERATION_TASK_HISTORY_LIMIT = 100


class GenerationTaskStatus(str, Enum):
    """Lifecycle states for image generation tasks."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLING = "cancelling"
    CANCELLED = "cancelled"


class GenerationTaskCreationError(Exception):
    """Error raised when a generation task cannot be accepted."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


ACTIVE_GENERATION_STATUSES = {
    GenerationTaskStatus.QUEUED,
    GenerationTaskStatus.RUNNING,
    GenerationTaskStatus.CANCELLING,
}

TERMINAL_GENERATION_STATUSES = {
    GenerationTaskStatus.SUCCEEDED,
    GenerationTaskStatus.FAILED,
    GenerationTaskStatus.CANCELLED,
}

ACTIVE_GENERATION_ITEM_STATUSES = {"pending", "running"}

GENERATION_TASK_STATUS_LABELS = {
    GenerationTaskStatus.QUEUED: "排队中",
    GenerationTaskStatus.RUNNING: "运行中",
    GenerationTaskStatus.SUCCEEDED: "已完成",
    GenerationTaskStatus.FAILED: "失败",
    GenerationTaskStatus.CANCELLING: "取消中",
    GenerationTaskStatus.CANCELLED: "已取消",
}


@dataclass
class GenerationTaskItem:
    """Per-request generation result metadata."""

    index: int
    status: str = "pending"
    result_count: int = 0
    error: str = ""
    retry_attempts: int = 0
    max_retry_attempts: int = 0


@dataclass(frozen=True)
class GenerationQueueItem:
    """Queued generation task entry."""

    task_id: str
    coro_factory: Callable[[], Coroutine[Any, Any, Any]]


@dataclass
class GenerationTaskRecord:
    """In-memory metadata for one image generation task."""

    task_id: str
    source: str
    unified_msg_origin: str
    prompt_summary: str
    reference_image_count: int
    requested_count: int
    aspect_ratio: str
    resolution: str
    preset: str | None = None
    preset_label: str = "预设"
    status: GenerationTaskStatus = GenerationTaskStatus.QUEUED
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str = "任务已提交"
    error: str = ""
    result_count: int = 0
    result_paths: list[str] = field(default_factory=list)
    current_index: int = 0
    retry_attempt: int = 0
    max_retry_attempts: int = 0
    items: dict[int, GenerationTaskItem] = field(default_factory=dict)
    usage_scope: str = ""
    reserved_count: int = 0
    is_usage_limit_admin: bool = False
    quota_released: bool = False
    quota_settled: bool = False
    task: asyncio.Task | None = field(default=None, repr=False, compare=False)

    @property
    def is_active(self) -> bool:
        """Return whether the task can still change state."""
        return self.status in ACTIVE_GENERATION_STATUSES

    @property
    def status_label(self) -> str:
        """Return a user-facing status label."""
        return GENERATION_TASK_STATUS_LABELS.get(self.status, self.status.value)

    @property
    def duration_seconds(self) -> float | None:
        """Return active execution duration, excluding queued time."""
        if not self.started_at:
            return None
        end_time = self.finished_at or datetime.now()
        return max(0.0, (end_time - self.started_at).total_seconds())

    @property
    def queued_seconds(self) -> float:
        """Return time spent since creation."""
        end_time = self.started_at or self.finished_at or datetime.now()
        return max(0.0, (end_time - self.created_at).total_seconds())

    @property
    def request_stats(self) -> dict[str, int]:
        """Return normalized sub-request progress statistics."""
        statuses = [item.status for item in self.items.values()]
        succeeded = statuses.count("succeeded")
        failed = statuses.count("failed")
        cancelled = statuses.count("cancelled")
        running = statuses.count("running")
        pending = statuses.count("pending")
        finished = succeeded + failed + cancelled
        total = max(self.requested_count, len(statuses))
        return {
            "total": total,
            "finished": finished,
            "succeeded": succeeded,
            "failed": failed,
            "cancelled": cancelled,
            "running": running,
            "pending": pending,
            "result_count": self.result_count or len(self.result_paths),
        }


def _task_name(name: str) -> str:
    """Return a compact task name for logs."""
    return safe_log_text(name, 80)


def _task_elapsed(record: GenerationTaskRecord) -> str:
    """Return a compact task timing summary for logs."""
    queued = record.queued_seconds
    duration = record.duration_seconds
    if duration is None:
        return f"排队={format_seconds(queued)}"
    return f"排队={format_seconds(queued)}，耗时={format_seconds(duration)}"


def _task_creation_summary(record: GenerationTaskRecord) -> str:
    """Return a compact creation summary for generation task logs."""
    return (
        f"来源={safe_log_text(record.source)}，"
        f"用户={mask_sensitive(record.unified_msg_origin)}，"
        f"数量={record.requested_count}张，"
        f"参考图={record.reference_image_count}张，"
        f"{record.preset_label}={format_optional(record.preset)}，"
        f"宽高比={safe_log_text(record.aspect_ratio)}，"
        f"分辨率={safe_log_text(record.resolution)}"
    )


GenerationTaskCallback = Callable[[GenerationTaskRecord], Any]
GenerationCoroutineFactory = Callable[[], Coroutine[Any, Any, Any]]


class TaskManager:
    """Unified task manager for background, scheduled, and generation tasks."""

    def __init__(
        self,
        generation_history_limit: int = DEFAULT_GENERATION_TASK_HISTORY_LIMIT,
        max_queued_generation_tasks: int = 20,
        persistence_file: str | Path | None = None,
    ):
        self.background_tasks: set[asyncio.Task] = set()
        self._loop_tasks: dict[str, asyncio.Task] = {}
        self._daily_tasks: dict[str, asyncio.Task] = {}
        self._last_run_dates: dict[str, str] = {}
        self._startup_tasks: list[
            tuple[str, Callable[[], Coroutine[Any, Any, Any]]]
        ] = []
        self._startup_completed: bool = False
        self._generation_tasks: dict[str, GenerationTaskRecord] = {}
        self._generation_terminal_callbacks: dict[
            str, list[GenerationTaskCallback]
        ] = {}
        self._generation_done_callbacks: dict[str, list[GenerationTaskCallback]] = {}
        self._generation_done_events: dict[str, asyncio.Event] = {}
        self._generation_terminal_notifying: set[str] = set()
        self._generation_terminal_notified: set[str] = set()
        self._generation_notification_tasks: dict[str, asyncio.Task] = {}
        self._generation_history_limit = max(1, generation_history_limit)
        self._generation_queue: asyncio.Queue[GenerationQueueItem | None] = (
            asyncio.Queue()
        )
        self._max_queued_generation_tasks = max(1, max_queued_generation_tasks)
        self._generation_workers: set[asyncio.Task] = set()
        self._running_generation_tasks: set[asyncio.Task] = set()
        self._generation_worker_target_count = 0
        self._generation_worker_sequence = 0
        self._accepting_generation_tasks = False
        self._generation_shutdown = False
        self._generation_persistence_file = (
            Path(persistence_file) if persistence_file else None
        )

    def create_task(
        self, coro: Coroutine[Any, Any, Any], name: str | None = None
    ) -> asyncio.Task:
        """Create a generic background task."""
        task = asyncio.create_task(coro)
        if name:
            task.set_name(name)
        self.background_tasks.add(task)
        task.add_done_callback(self.background_tasks.discard)
        return task

    def create_generation_task(
        self,
        coro_factory: GenerationCoroutineFactory,
        *,
        task_id: str,
        source: str,
        unified_msg_origin: str,
        prompt: str,
        reference_image_count: int,
        requested_count: int,
        aspect_ratio: str,
        resolution: str,
        preset: str | None = None,
        preset_label: str = "预设",
        usage_scope: str = "",
        reserved_count: int = 0,
        is_usage_limit_admin: bool = False,
        terminal_callback: GenerationTaskCallback | None = None,
    ) -> GenerationTaskRecord:
        """Create and enqueue an image generation task."""
        if not self._accepting_generation_tasks or self._generation_shutdown:
            raise GenerationTaskCreationError(
                "task_manager_closed",
                "生图任务队列暂不可用，请稍后再试",
            )
        if task_id in self._generation_tasks:
            raise GenerationTaskCreationError(
                "task_id_conflict",
                f"生图任务 ID 冲突: {task_id}",
            )

        if self._queued_generation_task_count() >= self._max_queued_generation_tasks:
            raise GenerationTaskCreationError(
                "queue_full",
                "生图任务队列已满，请稍后再试",
            )

        safe_requested_count = max(1, requested_count)
        record = GenerationTaskRecord(
            task_id=task_id,
            source=source,
            unified_msg_origin=unified_msg_origin,
            prompt_summary=safe_log_text(prompt, 80),
            reference_image_count=reference_image_count,
            requested_count=safe_requested_count,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            preset=preset,
            preset_label=preset_label,
            items={
                index: GenerationTaskItem(index=index)
                for index in range(1, safe_requested_count + 1)
            },
            usage_scope=usage_scope,
            reserved_count=max(0, reserved_count),
            is_usage_limit_admin=bool(is_usage_limit_admin),
        )
        self._generation_tasks[task_id] = record
        self._generation_terminal_notified.discard(task_id)
        if terminal_callback:
            self.add_generation_task_terminal_callback(task_id, terminal_callback)
        self._trim_generation_history()

        self._generation_queue.put_nowait(
            GenerationQueueItem(task_id=task_id, coro_factory=coro_factory)
        )
        self._save_generation_tasks()
        logger.info(
            f"{log_prefix('Task', task_id)} 已提交生图任务: "
            f"{_task_creation_summary(record)}"
        )
        logger.debug(
            f"{log_prefix('Task', task_id)} 生图任务提示词摘要: "
            f"提示词={safe_log_text(prompt, 80)}"
        )
        return record

    def load_generation_history(self) -> None:
        """Load persisted generation task history from disk."""
        if not self._generation_persistence_file:
            return
        persistence_file = self._generation_persistence_file
        if not persistence_file.exists():
            return

        try:
            with persistence_file.open(encoding="utf-8") as f:
                payload = json.load(f)
        except Exception as exc:
            logger.error(f"{LOG} 加载生图任务历史失败: {exc}", exc_info=True)
            corrupt_path = persistence_file.with_name(
                f"{persistence_file.name}.{datetime.now().strftime('%Y%m%d%H%M%S')}.corrupt"
            )
            try:
                os.replace(persistence_file, corrupt_path)
            except Exception as rename_exc:
                logger.error(
                    f"{LOG} 保留损坏生图任务历史失败: {rename_exc}",
                    exc_info=True,
                )
            self._generation_tasks = {}
            return

        raw_tasks = payload.get("tasks", []) if isinstance(payload, dict) else []
        if isinstance(raw_tasks, dict):
            raw_tasks = list(raw_tasks.values())
        if not isinstance(raw_tasks, list):
            raw_tasks = []

        restored_tasks: dict[str, GenerationTaskRecord] = {}
        history_changed = False
        now = datetime.now()
        for raw_record in raw_tasks:
            if not isinstance(raw_record, dict):
                history_changed = True
                continue
            record = self._generation_record_from_dict(raw_record)
            if not record:
                history_changed = True
                continue
            if record.status in ACTIVE_GENERATION_STATUSES:
                record.status = GenerationTaskStatus.CANCELLED
                record.message = "插件重启导致任务中断"
                record.error = "插件重启导致任务中断"
                record.finished_at = record.finished_at or now
                self._mark_unfinished_generation_items(
                    record,
                    status="cancelled",
                    error=record.error,
                )
                history_changed = True
            restored_tasks[record.task_id] = record

        self._generation_tasks = restored_tasks
        self._generation_terminal_callbacks.clear()
        self._generation_done_callbacks.clear()
        self._generation_done_events.clear()
        self._generation_terminal_notifying.clear()
        self._generation_terminal_notified = {
            task_id
            for task_id, record in restored_tasks.items()
            if record.status in TERMINAL_GENERATION_STATUSES
        }
        self._generation_notification_tasks.clear()
        history_changed = self._trim_generation_history() or history_changed
        if history_changed:
            self._save_generation_tasks()
        logger.info(f"{LOG} 已加载生图任务历史: {len(self._generation_tasks)} 条")

    def flush_generation_history(self) -> None:
        """Persist the current generation task history immediately."""
        self._save_generation_tasks()

    def configure_generation_queue(self, *, max_queued_generation_tasks: int) -> None:
        """Update generation queue capacity for newly submitted tasks.

        Args:
            max_queued_generation_tasks: Maximum number of queued, not-running tasks.
        """
        self._max_queued_generation_tasks = max(1, max_queued_generation_tasks)

    def _queued_generation_task_count(self) -> int:
        """Return the number of queued generation tasks that are still active."""
        return sum(
            1
            for record in self._generation_tasks.values()
            if record.status == GenerationTaskStatus.QUEUED
        )

    def _save_generation_tasks(self) -> None:
        """Persist serializable generation task metadata to disk."""
        if not self._generation_persistence_file:
            return
        payload = {
            "version": 1,
            "updated_at": datetime.now().isoformat(),
            "tasks": [
                self._generation_record_to_dict(record)
                for record in self._generation_tasks.values()
            ],
        }
        target_file = self._generation_persistence_file
        temp_file = target_file.with_name(f"{target_file.name}.tmp")
        try:
            target_file.parent.mkdir(parents=True, exist_ok=True)
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
            os.replace(temp_file, target_file)
        except Exception as exc:
            logger.error(f"{LOG} 保存生图任务历史失败: {exc}", exc_info=True)
            try:
                if temp_file.exists():
                    temp_file.unlink()
            except Exception:
                pass

    def _generation_record_to_dict(
        self,
        record: GenerationTaskRecord,
    ) -> dict[str, Any]:
        """Convert a generation task record to JSON-safe metadata."""
        return {
            "task_id": record.task_id,
            "source": record.source,
            "unified_msg_origin": record.unified_msg_origin,
            "prompt_summary": record.prompt_summary,
            "reference_image_count": record.reference_image_count,
            "requested_count": record.requested_count,
            "result_count": record.result_count,
            "aspect_ratio": record.aspect_ratio,
            "resolution": record.resolution,
            "preset": record.preset,
            "preset_label": record.preset_label,
            "status": record.status.value,
            "message": record.message,
            "error": record.error,
            "created_at": self._datetime_to_str(record.created_at),
            "started_at": self._datetime_to_str(record.started_at),
            "finished_at": self._datetime_to_str(record.finished_at),
            "result_paths": list(record.result_paths),
            "current_index": record.current_index,
            "retry_attempt": record.retry_attempt,
            "max_retry_attempts": record.max_retry_attempts,
            "items": [
                self._generation_item_to_dict(item)
                for item in sorted(record.items.values(), key=lambda item: item.index)
            ],
            "usage_scope": record.usage_scope,
            "reserved_count": record.reserved_count,
            "quota_released": record.quota_released,
            "quota_settled": record.quota_settled,
        }

    def _generation_item_to_dict(self, item: GenerationTaskItem) -> dict[str, Any]:
        """Convert one generation sub-request item to JSON-safe metadata."""
        return {
            "index": item.index,
            "status": item.status,
            "result_count": item.result_count,
            "error": item.error,
            "retry_attempts": item.retry_attempts,
            "max_retry_attempts": item.max_retry_attempts,
        }

    def _generation_record_from_dict(
        self,
        raw_record: dict[str, Any],
    ) -> GenerationTaskRecord | None:
        """Restore one generation task record from persisted metadata."""
        task_id = str(raw_record.get("task_id") or "").strip()
        if not task_id:
            return None
        requested_count = self._safe_int(raw_record.get("requested_count"), 1, 1)
        try:
            status = GenerationTaskStatus(str(raw_record.get("status") or "failed"))
        except ValueError:
            status = GenerationTaskStatus.FAILED

        record = GenerationTaskRecord(
            task_id=task_id,
            source=str(raw_record.get("source") or "历史记录"),
            unified_msg_origin=str(raw_record.get("unified_msg_origin") or ""),
            prompt_summary=safe_log_text(raw_record.get("prompt_summary") or "", 80),
            reference_image_count=self._safe_int(
                raw_record.get("reference_image_count"),
                0,
                0,
            ),
            requested_count=requested_count,
            aspect_ratio=str(raw_record.get("aspect_ratio") or ""),
            resolution=str(raw_record.get("resolution") or ""),
            preset=(
                str(raw_record.get("preset")) if raw_record.get("preset") else None
            ),
            preset_label=str(raw_record.get("preset_label") or "预设"),
            status=status,
            created_at=self._str_to_datetime(raw_record.get("created_at"))
            or datetime.now(),
            started_at=self._str_to_datetime(raw_record.get("started_at")),
            finished_at=self._str_to_datetime(raw_record.get("finished_at")),
            message=safe_log_error_body(raw_record.get("message") or "", 300),
            error=safe_log_error_body(raw_record.get("error") or "", 300),
            result_count=self._safe_int(raw_record.get("result_count"), 0, 0),
            result_paths=self._safe_str_list(raw_record.get("result_paths")),
            current_index=self._safe_int(raw_record.get("current_index"), 0, 0),
            retry_attempt=self._safe_int(raw_record.get("retry_attempt"), 0, 0),
            max_retry_attempts=self._safe_int(
                raw_record.get("max_retry_attempts"),
                0,
                0,
            ),
            items=self._generation_items_from_raw(
                raw_record.get("items"),
                requested_count,
            ),
            usage_scope=str(raw_record.get("usage_scope") or ""),
            reserved_count=self._safe_int(raw_record.get("reserved_count"), 0, 0),
            quota_released=bool(raw_record.get("quota_released", False)),
            quota_settled=bool(raw_record.get("quota_settled", False)),
        )
        return record

    def _generation_items_from_raw(
        self,
        raw_items: Any,
        requested_count: int,
    ) -> dict[int, GenerationTaskItem]:
        """Restore sub-request items from list or legacy dict forms."""
        items: dict[int, GenerationTaskItem] = {}
        iterable: list[Any]
        if isinstance(raw_items, dict):
            iterable = list(raw_items.values())
        elif isinstance(raw_items, list):
            iterable = raw_items
        else:
            iterable = []

        for raw_item in iterable:
            if not isinstance(raw_item, dict):
                continue
            index = self._safe_int(raw_item.get("index"), 0, 1)
            if index <= 0:
                continue
            items[index] = GenerationTaskItem(
                index=index,
                status=str(raw_item.get("status") or "pending"),
                result_count=self._safe_int(raw_item.get("result_count"), 0, 0),
                error=safe_log_error_body(raw_item.get("error") or "", 200),
                retry_attempts=self._safe_int(raw_item.get("retry_attempts"), 0, 0),
                max_retry_attempts=self._safe_int(
                    raw_item.get("max_retry_attempts"),
                    0,
                    0,
                ),
            )

        for index in range(1, max(1, requested_count) + 1):
            items.setdefault(index, GenerationTaskItem(index=index))
        return items

    def _datetime_to_str(self, value: datetime | None) -> str | None:
        """Serialize a datetime to ISO text."""
        return value.isoformat() if value else None

    def _str_to_datetime(self, value: Any) -> datetime | None:
        """Parse an ISO datetime string defensively."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    def _safe_int(self, value: Any, default: int, minimum: int) -> int:
        """Coerce a value to int and clamp it to a minimum."""
        if isinstance(value, bool):
            return default
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(minimum, parsed)

    def _safe_str_list(self, value: Any) -> list[str]:
        """Return only string entries from a persisted list."""
        if not isinstance(value, list):
            return []
        return [str(item) for item in value if isinstance(item, str) and item]

    def start_generation_workers(self, worker_count: int) -> None:
        """Start generation workers and allow new generation tasks.

        Args:
            worker_count: Target number of complete generation tasks to run at once.
        """
        self._generation_shutdown = False
        self._accepting_generation_tasks = True
        self.update_generation_worker_count(worker_count)

    def update_generation_worker_count(self, worker_count: int) -> None:
        """Resize generation workers without cancelling running generation tasks.

        Args:
            worker_count: New target worker count.
        """
        target_count = max(1, worker_count)
        self._generation_worker_target_count = target_count

        live_workers = {task for task in self._generation_workers if not task.done()}
        self._generation_workers = live_workers
        while len(self._generation_workers) < target_count:
            self._generation_worker_sequence += 1
            worker_index = self._generation_worker_sequence
            task = asyncio.create_task(
                self._generation_worker_loop(worker_index),
                name=f"image_generation_worker:{worker_index}",
            )
            self._generation_workers.add(task)
            task.add_done_callback(self._generation_workers.discard)

        extra_count = len(self._generation_workers) - target_count
        for _ in range(max(0, extra_count)):
            self._generation_queue.put_nowait(None)

    async def _generation_worker_loop(self, worker_index: int) -> None:
        """Run queued generation tasks one at a time."""
        logger.debug(f"{LOG} 生图任务 worker {worker_index} 已启动")
        try:
            while True:
                queue_item = await self._generation_queue.get()
                try:
                    if queue_item is None:
                        if (
                            self._generation_shutdown
                            or len(self._generation_workers)
                            > self._generation_worker_target_count
                        ):
                            break
                        continue
                    await self._run_generation_queue_item(queue_item)
                finally:
                    self._generation_queue.task_done()
        except asyncio.CancelledError:
            raise
        finally:
            logger.debug(f"{LOG} 生图任务 worker {worker_index} 已退出")

    async def _run_generation_queue_item(
        self,
        queue_item: GenerationQueueItem,
    ) -> None:
        """Execute one queued generation task if it is still active."""
        record = self._generation_tasks.get(queue_item.task_id)
        if not record:
            return
        if record.status == GenerationTaskStatus.CANCELLED:
            return
        if record.status == GenerationTaskStatus.CANCELLING:
            self.mark_generation_task_cancelled(queue_item.task_id)
            return
        if record.status in TERMINAL_GENERATION_STATUSES:
            return

        self.mark_generation_task_running(queue_item.task_id)
        try:
            coro = queue_item.coro_factory()
        except Exception as exc:
            self.mark_generation_task_failed(
                queue_item.task_id,
                f"任务创建执行协程失败: {exc}",
            )
            logger.error(
                f"{log_prefix('Task', queue_item.task_id)} 生图任务创建执行协程失败: {exc}",
                exc_info=True,
            )
            return

        task = asyncio.create_task(
            self._run_generation_task(queue_item.task_id, coro),
            name=f"image_generation:{queue_item.task_id}",
        )
        record.task = task
        self._running_generation_tasks.add(task)
        task.add_done_callback(self._running_generation_tasks.discard)
        task.add_done_callback(
            functools.partial(self._on_generation_task_done, queue_item.task_id)
        )
        try:
            await task
        finally:
            if record.task is task:
                record.task = None

    def add_generation_task_terminal_callback(
        self,
        task_id: str,
        callback: GenerationTaskCallback,
    ) -> None:
        """Register a callback that runs before public completion notification.

        Args:
            task_id: Generation task ID to observe.
            callback: Callback receiving the terminal task record.
        """
        record = self._generation_tasks.get(task_id)
        if record and record.status in TERMINAL_GENERATION_STATUSES:
            if task_id in self._generation_terminal_notified:
                self._dispatch_generation_callback(callback, record, "终态业务回调")
                return
            self._generation_terminal_callbacks.setdefault(task_id, []).append(callback)
            self._notify_generation_task_terminal(task_id)
            return
        self._generation_terminal_callbacks.setdefault(task_id, []).append(callback)

    def add_generation_task_done_callback(
        self,
        task_id: str,
        callback: GenerationTaskCallback,
    ) -> None:
        """Register a callback that runs once after a task reaches terminal state.

        Args:
            task_id: Generation task ID to observe.
            callback: Callback receiving the terminal task record.
        """
        record = self._generation_tasks.get(task_id)
        if record and record.status in TERMINAL_GENERATION_STATUSES:
            if task_id in self._generation_terminal_notified:
                self._dispatch_generation_callback(callback, record, "完成回调")
                return
            self._generation_done_callbacks.setdefault(task_id, []).append(callback)
            self._notify_generation_task_terminal(task_id)
            return
        self._generation_done_callbacks.setdefault(task_id, []).append(callback)

    async def wait_generation_task_done(
        self,
        task_id: str,
        *,
        timeout_seconds: float | None = None,
    ) -> GenerationTaskRecord | None:
        """Wait for a generation task to reach terminal state.

        Args:
            task_id: Generation task ID to wait for.
            timeout_seconds: Optional maximum wait time in seconds.

        Returns:
            The terminal task record, or ``None`` when the task disappears or times out.
        """
        record = self._generation_tasks.get(task_id)
        if not record:
            return None
        if (
            record.status in TERMINAL_GENERATION_STATUSES
            and task_id in self._generation_terminal_notified
        ):
            return record

        event = self._generation_done_events.setdefault(task_id, asyncio.Event())
        if record.status in TERMINAL_GENERATION_STATUSES:
            self._notify_generation_task_terminal(task_id)
        try:
            if timeout_seconds is None:
                await event.wait()
            else:
                await asyncio.wait_for(event.wait(), timeout=max(0.0, timeout_seconds))
        except asyncio.TimeoutError:
            return None
        return self._generation_tasks.get(task_id)

    def _dispatch_generation_callback(
        self,
        callback: GenerationTaskCallback,
        record: GenerationTaskRecord,
        label: str,
    ) -> None:
        """Run a generation callback and isolate callback failures."""
        try:
            result = callback(record)
        except Exception as exc:
            logger.error(
                f"{log_prefix('Task', record.task_id)} 生图任务{label}异常: {exc}",
                exc_info=True,
            )
            return

        if inspect.isawaitable(result):
            self.create_task(
                self._await_generation_callback(record.task_id, result, label),
                name=f"image_generation_{label}:{record.task_id}",
            )

    async def _await_generation_callback(
        self,
        task_id: str,
        awaitable: Any,
        label: str,
    ) -> None:
        """Await an asynchronous generation callback with error isolation."""
        try:
            await awaitable
        except Exception as exc:
            logger.error(
                f"{log_prefix('Task', task_id)} 生图任务{label}异步异常: {exc}",
                exc_info=True,
            )

    async def _run_generation_callback_ordered(
        self,
        callback: GenerationTaskCallback,
        record: GenerationTaskRecord,
        label: str,
    ) -> None:
        """Run and await one generation callback with error isolation."""
        try:
            result = callback(record)
            if inspect.isawaitable(result):
                await result
        except Exception as exc:
            logger.error(
                f"{log_prefix('Task', record.task_id)} 生图任务{label}异常: {exc}",
                exc_info=True,
            )

    def _run_generation_callback_inline(
        self,
        callback: GenerationTaskCallback,
        record: GenerationTaskRecord,
        label: str,
    ) -> Any | None:
        """Run one callback synchronously and return its awaitable part if any."""
        try:
            result = callback(record)
        except Exception as exc:
            logger.error(
                f"{log_prefix('Task', record.task_id)} 生图任务{label}异常: {exc}",
                exc_info=True,
            )
            return None
        return result if inspect.isawaitable(result) else None

    def _notify_generation_task_terminal(self, task_id: str) -> None:
        """Schedule terminal callbacks, public callbacks, and waiters once."""
        if (
            task_id in self._generation_terminal_notified
            or task_id in self._generation_terminal_notifying
        ):
            return
        record = self._generation_tasks.get(task_id)
        if not record or record.status not in TERMINAL_GENERATION_STATUSES:
            return

        self._generation_terminal_notifying.add(task_id)
        pending_awaitables: list[Any] = []
        while terminal_callbacks := self._generation_terminal_callbacks.pop(
            task_id,
            [],
        ):
            for callback in terminal_callbacks:
                awaitable = self._run_generation_callback_inline(
                    callback,
                    record,
                    "终态业务回调",
                )
                if awaitable is not None:
                    pending_awaitables.append(awaitable)

        if pending_awaitables:
            task = self.create_task(
                self._notify_generation_task_terminal_async(
                    task_id,
                    pending_awaitables,
                ),
                name=f"image_generation_terminal_notify:{task_id}",
            )
            self._generation_notification_tasks[task_id] = task
            task.add_done_callback(
                functools.partial(self._on_generation_notification_done, task_id)
            )
            return

        self._complete_generation_terminal_notification(task_id)

    async def _notify_generation_task_terminal_async(
        self,
        task_id: str,
        pending_awaitables: list[Any],
    ) -> None:
        """Await asynchronous terminal callbacks before public notifications."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status not in TERMINAL_GENERATION_STATUSES:
            return

        for awaitable in pending_awaitables:
            await self._await_generation_callback(
                task_id,
                awaitable,
                "终态业务回调",
            )

        while terminal_callbacks := self._generation_terminal_callbacks.pop(
            task_id,
            [],
        ):
            for callback in terminal_callbacks:
                await self._run_generation_callback_ordered(
                    callback,
                    record,
                    "终态业务回调",
                )

        self._complete_generation_terminal_notification(task_id)

    def _complete_generation_terminal_notification(self, task_id: str) -> None:
        """Run public completion callbacks and release waiters."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status not in TERMINAL_GENERATION_STATUSES:
            self._generation_terminal_notifying.discard(task_id)
            return

        # Terminal callbacks may update quota settlement flags.
        self._save_generation_tasks()

        while done_callbacks := self._generation_done_callbacks.pop(task_id, []):
            for callback in done_callbacks:
                self._dispatch_generation_callback(callback, record, "完成回调")

        self._generation_terminal_notified.add(task_id)
        self._generation_terminal_notifying.discard(task_id)
        if event := self._generation_done_events.get(task_id):
            event.set()

        self._trim_generation_history()
        self._save_generation_tasks()

    def _on_generation_notification_done(
        self,
        task_id: str,
        task: asyncio.Task,
    ) -> None:
        """Cleanup notification task bookkeeping and log unexpected failures."""
        self.background_tasks.discard(task)
        self._generation_terminal_notifying.discard(task_id)
        if self._generation_notification_tasks.get(task_id) is task:
            self._generation_notification_tasks.pop(task_id, None)
        if task.cancelled():
            return
        try:
            task.result()
        except Exception as exc:
            logger.error(
                f"{log_prefix('Task', task_id)} 生图任务终态通知异常: {exc}",
                exc_info=True,
            )

    async def _wait_generation_notifications(self) -> None:
        """Wait for in-flight terminal notifications before shutdown cleanup."""
        tasks = [
            task
            for task in self._generation_notification_tasks.values()
            if not task.done()
        ]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _run_generation_task(
        self, task_id: str, coro: Coroutine[Any, Any, Any]
    ) -> None:
        """Run a tracked generation coroutine and close unhandled states."""
        try:
            await coro
            record = self.get_generation_task(task_id)
            if record and record.is_active:
                self.mark_generation_task_succeeded(task_id, message="任务已完成")
        except asyncio.CancelledError:
            self.mark_generation_task_cancelled(task_id, "任务已取消")
            raise
        except Exception as exc:
            self.mark_generation_task_failed(task_id, f"任务执行异常: {exc}")
            logger.error(
                f"{log_prefix('Task', task_id)} 生图任务执行异常: {exc}",
                exc_info=True,
            )

    def _on_generation_task_done(self, task_id: str, _task: asyncio.Task) -> None:
        """Detach asyncio task references when a generation task finishes."""
        if record := self._generation_tasks.get(task_id):
            record.task = None

    def _mark_unfinished_generation_items(
        self,
        record: GenerationTaskRecord,
        *,
        status: str,
        error: str = "",
    ) -> None:
        """Mark pending or running sub-requests with a final item status."""
        safe_error = safe_log_error_body(error, 200) if error else ""
        for item in record.items.values():
            if item.status not in ACTIVE_GENERATION_ITEM_STATUSES:
                continue
            item.status = status
            if safe_error and not item.error:
                item.error = safe_error

    def _enter_generation_terminal_status(
        self,
        task_id: str,
        status: GenerationTaskStatus,
        *,
        message: str,
        error: str = "",
        result_count: int = 0,
        result_paths: list[str] | None = None,
    ) -> GenerationTaskRecord | None:
        """Move a task into terminal state exactly once."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status in TERMINAL_GENERATION_STATUSES:
            return None

        record.status = status
        record.finished_at = record.finished_at or datetime.now()
        record.message = safe_log_error_body(message, 300)
        record.error = safe_log_error_body(error, 300) if error else ""
        if result_paths is not None:
            record.result_paths = list(result_paths)
        final_result_count = (
            result_count or len(record.result_paths) or record.result_count
        )
        record.result_count = max(0, final_result_count)

        if status == GenerationTaskStatus.CANCELLED:
            self._mark_unfinished_generation_items(
                record,
                status="cancelled",
                error=message,
            )
        elif status == GenerationTaskStatus.FAILED:
            self._mark_unfinished_generation_items(
                record,
                status="failed",
                error=record.error or message,
            )
        return record

    def mark_generation_task_running(self, task_id: str) -> None:
        """Mark a generation task as actively running."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status == GenerationTaskStatus.CANCELLING:
            return
        if record.status in TERMINAL_GENERATION_STATUSES:
            return
        record.status = GenerationTaskStatus.RUNNING
        record.started_at = record.started_at or datetime.now()
        record.message = "任务运行中"
        logger.debug(
            f"{log_prefix('Task', task_id)} 生图任务开始运行: "
            f"排队={format_seconds(record.queued_seconds)}"
        )
        self._save_generation_tasks()

    def update_generation_task_references(
        self,
        task_id: str,
        *,
        reference_image_count: int,
    ) -> None:
        """Update prepared reference image metadata for a generation task."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status in TERMINAL_GENERATION_STATUSES:
            return
        record.reference_image_count = max(0, reference_image_count)

    def update_generation_task_retry_status(
        self,
        task_id: str,
        *,
        current_index: int,
        retry_attempt: int,
        max_retry_attempts: int,
    ) -> None:
        """Update the currently running generation retry attempt."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status in TERMINAL_GENERATION_STATUSES:
            return
        record.current_index = max(1, current_index)
        record.retry_attempt = max(0, retry_attempt)
        record.max_retry_attempts = max(0, max_retry_attempts)
        item = record.items.setdefault(
            record.current_index,
            GenerationTaskItem(index=record.current_index, status="running"),
        )
        item.status = "running"
        item.retry_attempts = max(item.retry_attempts, record.retry_attempt)
        item.max_retry_attempts = max(
            item.max_retry_attempts, record.max_retry_attempts
        )

    def update_generation_task_item_result(
        self,
        task_id: str,
        *,
        index: int,
        status: str,
        result_count: int = 0,
        error: str = "",
    ) -> None:
        """Record per-request generation result details."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status in TERMINAL_GENERATION_STATUSES:
            return
        safe_index = max(1, index)
        item = record.items.setdefault(
            safe_index,
            GenerationTaskItem(index=safe_index),
        )
        item.status = status
        item.result_count = max(0, result_count)
        item.error = safe_log_error_body(error, 200) if error else ""

    def update_generation_task_progress(
        self,
        task_id: str,
        *,
        current_index: int,
        result_count: int,
        message: str,
    ) -> None:
        """Update image count progress for one generation task."""
        record = self._generation_tasks.get(task_id)
        if not record or record.status in TERMINAL_GENERATION_STATUSES:
            return
        record.current_index = max(1, current_index)
        record.result_count = max(0, result_count)
        record.message = message

    def mark_generation_task_cancelling(
        self,
        task_id: str,
        message: str = "正在取消任务",
    ) -> bool:
        """Move an active task into cancelling state.

        Args:
            task_id: Generation task ID to cancel.
            message: User-facing cancellation progress message.

        Returns:
            Whether the task was changed to cancelling state.
        """
        record = self._generation_tasks.get(task_id)
        if not record or record.status in TERMINAL_GENERATION_STATUSES:
            return False
        if record.status == GenerationTaskStatus.CANCELLING:
            return True
        record.status = GenerationTaskStatus.CANCELLING
        record.message = message
        return True

    def mark_generation_task_succeeded(
        self,
        task_id: str,
        *,
        result_count: int = 0,
        result_paths: list[str] | None = None,
        message: str = "任务已完成",
    ) -> None:
        """Mark a generation task as successful."""
        record = self._enter_generation_terminal_status(
            task_id,
            GenerationTaskStatus.SUCCEEDED,
            message=message,
            result_count=result_count,
            result_paths=result_paths,
        )
        if not record:
            return
        logger.info(
            f"{log_prefix('Task', task_id)} 生图任务完成: "
            f"来源={safe_log_text(record.source)}，{_task_elapsed(record)}，"
            f"结果={record.result_count}张"
        )
        self._save_generation_tasks()
        self._notify_generation_task_terminal(task_id)

    def mark_generation_task_failed(self, task_id: str, error: str) -> None:
        """Mark a generation task as failed."""
        record = self._enter_generation_terminal_status(
            task_id,
            GenerationTaskStatus.FAILED,
            message="任务失败",
            error=error,
        )
        if not record:
            return
        logger.warning(
            f"{log_prefix('Task', task_id)} 生图任务失败: "
            f"{_task_elapsed(record)}，错误={record.error}"
        )
        self._save_generation_tasks()
        self._notify_generation_task_terminal(task_id)

    def mark_generation_task_cancelled(
        self, task_id: str, reason: str = "任务已取消"
    ) -> None:
        """Mark a generation task as cancelled."""
        record = self._enter_generation_terminal_status(
            task_id,
            GenerationTaskStatus.CANCELLED,
            message=reason,
        )
        if not record:
            return
        logger.info(
            f"{log_prefix('Task', task_id)} 生图任务已取消: "
            f"{_task_elapsed(record)}，原因={format_optional(reason)}"
        )
        self._save_generation_tasks()
        self._notify_generation_task_terminal(task_id)

    def mark_generation_task_quota_released(self, task_id: str) -> None:
        """Mark that the task's reserved quota has been released."""
        if record := self._generation_tasks.get(task_id):
            record.quota_released = True
            self._save_generation_tasks()

    def mark_generation_task_quota_settled(self, task_id: str) -> None:
        """Mark that the task's reserved quota has been settled."""
        if record := self._generation_tasks.get(task_id):
            record.quota_settled = True
            record.quota_released = True
            self._save_generation_tasks()

    def mark_unfinished_generation_task_items_cancelled(
        self,
        task_id: str,
        reason: str = "任务已取消",
    ) -> None:
        """Mark pending or running sub-requests as cancelled."""
        record = self._generation_tasks.get(task_id)
        if not record:
            return
        self._mark_unfinished_generation_items(
            record,
            status="cancelled",
            error=reason,
        )

    def get_generation_task(self, task_id: str) -> GenerationTaskRecord | None:
        """Return a tracked image generation task by id."""
        return self._generation_tasks.get(task_id)

    def list_generation_tasks(
        self,
        *,
        unified_msg_origin: str | None = None,
        include_finished: bool = True,
        limit: int = 10,
    ) -> list[GenerationTaskRecord]:
        """List tracked generation tasks from newest to oldest."""
        tasks = list(reversed(self._generation_tasks.values()))
        if unified_msg_origin is not None:
            tasks = [t for t in tasks if t.unified_msg_origin == unified_msg_origin]
        if not include_finished:
            tasks = [t for t in tasks if t.is_active]
        return tasks[: max(1, limit)]

    def cancel_generation_task(
        self,
        task_id: str,
        *,
        unified_msg_origin: str | None = None,
    ) -> tuple[bool, str]:
        """Request cancellation for one generation task."""
        record = self._generation_tasks.get(task_id)
        if not record:
            return False, f"❌ 任务不存在: {task_id}"
        if (
            unified_msg_origin is not None
            and record.unified_msg_origin != unified_msg_origin
        ):
            return False, "❌ 不能取消其他会话的生图任务"
        if record.status == GenerationTaskStatus.CANCELLING:
            return True, f"⏳ 任务正在取消中: {task_id}"
        if not record.is_active:
            return False, f"❌ 任务已结束，当前状态: {record.status_label}"

        self.mark_generation_task_cancelling(task_id)
        logger.debug(f"{log_prefix('Task', task_id)} 收到取消生图任务请求")
        if record.task and not record.task.done():
            record.task.cancel()
            return True, f"✅ 已请求取消任务: {task_id}"

        self.mark_generation_task_cancelled(task_id)
        return True, f"✅ 任务已取消: {task_id}"

    def cleanup_generation_tasks(self, *, unified_msg_origin: str | None = None) -> int:
        """Remove finished generation task records."""
        removed = 0
        for task_id, record in list(self._generation_tasks.items()):
            if record.is_active:
                continue
            if (
                unified_msg_origin is not None
                and record.unified_msg_origin != unified_msg_origin
            ):
                continue
            del self._generation_tasks[task_id]
            self._generation_terminal_callbacks.pop(task_id, None)
            self._generation_done_callbacks.pop(task_id, None)
            self._generation_done_events.pop(task_id, None)
            self._generation_terminal_notifying.discard(task_id)
            self._generation_terminal_notified.discard(task_id)
            self._generation_notification_tasks.pop(task_id, None)
            removed += 1
        if removed:
            self._save_generation_tasks()
        return removed

    def _trim_generation_history(self) -> bool:
        """Keep finished task history bounded while preserving active tasks."""
        overflow = len(self._generation_tasks) - self._generation_history_limit
        if overflow <= 0:
            return False

        changed = False
        for task_id, record in list(self._generation_tasks.items()):
            if overflow <= 0:
                break
            if record.is_active:
                continue
            del self._generation_tasks[task_id]
            self._generation_terminal_callbacks.pop(task_id, None)
            self._generation_done_callbacks.pop(task_id, None)
            self._generation_done_events.pop(task_id, None)
            self._generation_terminal_notifying.discard(task_id)
            self._generation_terminal_notified.discard(task_id)
            self._generation_notification_tasks.pop(task_id, None)
            overflow -= 1
            changed = True
        return changed

    def start_loop_task(
        self,
        name: str,
        coro_func: Callable[[], Coroutine[Any, Any, Any]],
        interval_seconds: float,
        run_immediately: bool = True,
    ) -> None:
        """启动一个周期性的定时任务。

        Args:
            name: 任务名称，用于唯一标识和日志记录。
            coro_func: 返回协程的函数（任务的主逻辑）。
            interval_seconds: 执行间隔（秒）。
            run_immediately: 是否在启动时立即执行一次。
        """
        if name in self._loop_tasks:
            self.stop_loop_task(name)

        log_name = _task_name(name)

        async def _loop():
            if run_immediately:
                try:
                    await coro_func()
                except Exception as e:
                    logger.error(
                        f"{LOG} 定时任务 {log_name} 初始执行失败: {e}",
                        exc_info=True,
                    )

            while True:
                try:
                    await asyncio.sleep(interval_seconds)
                    await coro_func()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        f"{LOG} 定时任务 {log_name} 执行出错: {e}",
                        exc_info=True,
                    )

        task = asyncio.create_task(_loop(), name=f"loop_{name}")
        self._loop_tasks[name] = task
        self.background_tasks.add(task)
        task.add_done_callback(functools.partial(self._on_loop_task_done, name))
        logger.debug(f"{LOG} 定时任务 {log_name} 已启动 (间隔: {interval_seconds}s)")

    def stop_loop_task(self, name: str) -> None:
        """停止指定的定时任务。"""
        if task := self._loop_tasks.pop(name, None):
            if not task.done():
                task.cancel()
            logger.debug(f"{LOG} 定时任务 {_task_name(name)} 已停止")

    def _on_loop_task_done(self, name: str, task: asyncio.Task) -> None:
        """定时任务结束时的回调。"""
        self.background_tasks.discard(task)
        self._loop_tasks.pop(name, None)

    def register_startup_task(
        self,
        name: str,
        coro_func: Callable[[], Coroutine[Any, Any, Any]],
    ) -> None:
        """注册一个启动时执行的任务。

        Args:
            name: 任务名称，用于日志记录。
            coro_func: 返回协程的函数（任务的主逻辑）。
        """
        self._startup_tasks.append((name, coro_func))
        logger.debug(f"{LOG} 已注册启动任务: {_task_name(name)}")

    async def run_startup_tasks(self) -> None:
        """执行所有注册的启动任务。

        此方法应在插件初始化完成后调用一次。
        """
        if self._startup_completed:
            logger.warning(f"{LOG} 启动任务已执行过，跳过重复执行")
            return

        if not self._startup_tasks:
            logger.debug(f"{LOG} 没有注册的启动任务")
            self._startup_completed = True
            return

        logger.debug(f"{LOG} 开始执行 {len(self._startup_tasks)} 个启动任务")

        for name, coro_func in self._startup_tasks:
            log_name = _task_name(name)
            try:
                logger.debug(f"{LOG} 执行启动任务: {log_name}")
                await coro_func()
                logger.debug(f"{LOG} 启动任务 {log_name} 执行完成")
            except Exception as e:
                logger.error(
                    f"{LOG} 启动任务 {log_name} 执行失败: {e}",
                    exc_info=True,
                )

        self._startup_completed = True
        logger.debug(f"{LOG} 所有启动任务执行完毕")

    def start_daily_task(
        self,
        name: str,
        coro_func: Callable[[], Coroutine[Any, Any, Any]],
        check_interval_seconds: float = 60.0,
        run_immediately: bool = False,
    ) -> None:
        """启动一个每日任务，在日期变更时执行。

        Args:
            name: 任务名称，用于唯一标识和日志记录。
            coro_func: 返回协程的函数（任务的主逻辑）。
            check_interval_seconds: 检查日期变更的间隔（秒），默认 60 秒。
            run_immediately: 是否在启动时立即执行一次（无论日期）。
        """
        if name in self._daily_tasks:
            self.stop_daily_task(name)

        log_name = _task_name(name)

        async def _daily_loop():
            # 初始化上次执行日期
            if run_immediately:
                try:
                    await coro_func()
                    self._last_run_dates[name] = datetime.now().strftime("%Y-%m-%d")
                    logger.debug(f"{LOG} 每日任务 {log_name} 初始执行完成")
                except Exception as e:
                    logger.error(
                        f"{LOG} 每日任务 {log_name} 初始执行失败: {e}",
                        exc_info=True,
                    )
            else:
                # 记录当前日期，避免启动当天重复执行
                self._last_run_dates[name] = datetime.now().strftime("%Y-%m-%d")

            while True:
                try:
                    await asyncio.sleep(check_interval_seconds)
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    last_run_date = self._last_run_dates.get(name)

                    if current_date != last_run_date:
                        logger.info(
                            f"{LOG} 检测到日期变更 ({last_run_date} -> {current_date})，执行每日任务 {log_name}"
                        )
                        try:
                            await coro_func()
                            self._last_run_dates[name] = current_date
                            logger.info(f"{LOG} 每日任务 {log_name} 执行完成")
                        except Exception as e:
                            logger.error(
                                f"{LOG} 每日任务 {log_name} 执行出错: {e}",
                                exc_info=True,
                            )
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(
                        f"{LOG} 每日任务 {log_name} 循环出错: {e}",
                        exc_info=True,
                    )

        task = asyncio.create_task(_daily_loop(), name=f"daily_{name}")
        self._daily_tasks[name] = task
        self.background_tasks.add(task)
        task.add_done_callback(functools.partial(self._on_daily_task_done, name))
        logger.debug(
            f"{LOG} 每日任务 {log_name} 已启动 (检查间隔: {check_interval_seconds}s)"
        )

    def stop_daily_task(self, name: str) -> None:
        """停止指定的每日任务。"""
        if task := self._daily_tasks.pop(name, None):
            if not task.done():
                task.cancel()
            self._last_run_dates.pop(name, None)
            logger.debug(f"{LOG} 每日任务 {_task_name(name)} 已停止")

    def _on_daily_task_done(self, name: str, task: asyncio.Task) -> None:
        """每日任务结束时的回调。"""
        self.background_tasks.discard(task)
        self._daily_tasks.pop(name, None)
        self._last_run_dates.pop(name, None)

    async def cancel_all(self):
        """取消所有正在运行的任务。"""
        self._accepting_generation_tasks = False
        self._generation_shutdown = True

        queued_task_ids: list[str] = []
        while True:
            try:
                queue_item = self._generation_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            try:
                if queue_item is not None:
                    queued_task_ids.append(queue_item.task_id)
            finally:
                self._generation_queue.task_done()

        for task_id in queued_task_ids:
            self.mark_generation_task_cancelled(
                task_id,
                "插件卸载/重启导致任务中断",
            )

        await self._wait_generation_notifications()

        for task in list(self._running_generation_tasks):
            if not task.done():
                task.cancel()

        if self._running_generation_tasks:
            await asyncio.gather(
                *self._running_generation_tasks,
                return_exceptions=True,
            )

        await self._wait_generation_notifications()

        for _ in list(self._generation_workers):
            self._generation_queue.put_nowait(None)

        for worker in list(self._generation_workers):
            if not worker.done():
                worker.cancel()

        if self._generation_workers:
            await asyncio.gather(*self._generation_workers, return_exceptions=True)

        for task in list(self.background_tasks):
            if not task.done():
                task.cancel()

        if self.background_tasks:
            await asyncio.gather(*self.background_tasks, return_exceptions=True)

        self.background_tasks.clear()
        self._loop_tasks.clear()
        self._daily_tasks.clear()
        self._last_run_dates.clear()
        self._generation_workers.clear()
        self._running_generation_tasks.clear()
        self._generation_terminal_notifying.clear()
        self._generation_notification_tasks.clear()
        self._generation_worker_target_count = 0
        self._save_generation_tasks()
        logger.debug(f"{LOG} 所有后台任务已取消")
