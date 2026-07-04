"""LLM tool task result handling for image generation."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable, Coroutine
from contextlib import suppress
from typing import Any

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain
from astrbot.api.star import Context
from astrbot.core.agent.message import TextPart
from astrbot.core.agent.tool import ToolSet
from astrbot.core.cron.events import CronMessageEvent
from astrbot.core.platform.message_session import MessageSession
from astrbot.core.provider.entities import ProviderRequest
from astrbot.core.tools.message_tools import SendMessageToUserTool
from astrbot.core.utils.history_saver import persist_agent_history

from .config_manager import ConfigManager
from .logging_utils import log_prefix, safe_log_text
from .task_manager import GenerationTaskRecord, GenerationTaskStatus, TaskManager


IMAGE_GENERATION_TASK_WOKE_SYSTEM_PROMPT = (
    "You are an autonomous proactive agent.\n\n"
    "You are awakened because an image generation task you initiated earlier has completed.\n"
    "# IMPORTANT RULES\n"
    "1. This is NOT a normal chat turn. Do NOT greet the user. Do NOT ask questions unless strictly necessary.\n"
    "2. You MUST use the `send_message_to_user` tool to send the final image generation result to the user; otherwise the user will not see it.\n"
    "3. If the task succeeded, send the generated image(s) to the user with type='image' and the provided local path. You may add a short plain text note if helpful.\n"
    "4. If the task failed, send a concise failure message to the user.\n"
    "5. Do not call `generate_image` again for this completed task. Do not repeat the same image unless necessary.\n"
    "6. If generated images are attached in this request, review them before deciding the final wording. If images are not attached, use the provided image paths.\n"
    "# IMAGE GENERATION TASK CONTEXT\n"
    "The following JSON object describes the completed image generation task:\n"
    "{generation_task_result}"
)


class LLMResultHandler:
    """Handle LLM tool task submission text and task-result AI delivery."""

    def __init__(
        self,
        *,
        context: Context,
        config_manager: ConfigManager,
        task_manager: TaskManager,
        create_background_task: Callable[
            [Coroutine[Any, Any, Any], str | None], asyncio.Task
        ],
    ) -> None:
        self.context = context
        self.config_manager = config_manager
        self.task_manager = task_manager
        self._create_background_task = create_background_task

    def attach_task_wakeup(
        self,
        record: GenerationTaskRecord,
        *,
        source_event: AstrMessageEvent | None,
    ) -> None:
        """Attach an AI wakeup task to a completed LLM image generation task."""
        if not source_event:
            return

        def _on_done(current_record: GenerationTaskRecord) -> None:
            if current_record.status in {
                GenerationTaskStatus.CANCELLING,
                GenerationTaskStatus.CANCELLED,
            }:
                logger.debug(
                    f"{log_prefix('Task', record.task_id)} 生图任务已取消，跳过 AI 结果唤醒"
                )
                return
            self._create_background_task(
                self.wake_ai_for_generation_task_result(
                    task_id=record.task_id,
                    source_event=source_event,
                ),
                f"image_generation_ai_wakeup:{record.task_id}",
            )

        self.task_manager.add_generation_task_done_callback(record.task_id, _on_done)

    def format_tool_start_result(
        self,
        *,
        prompt: str,
        reference_image_count: int,
        preset: str | None,
        preset_label: str = "预设",
        presets: list[str] | None = None,
        personas: list[str] | None = None,
        aspect_ratio: str,
        resolution: str,
        image_count: int,
        task_id: str,
    ) -> str:
        """Format the successful LLM tool result for the agent."""
        model = ""
        if self.config_manager.adapter_config:
            model = (
                f"{self.config_manager.adapter_config.name}/"
                f"{self.config_manager.adapter_config.model}"
            )

        template_summary_parts = []
        preset_names = "、".join(presets or [])
        persona_names = "、".join(personas or [])
        if preset_names:
            template_summary_parts.append(f"预设={preset_names}")
        if persona_names:
            template_summary_parts.append(f"人设={persona_names}")
        if not template_summary_parts and preset:
            template_summary_parts.append(f"{preset_label}={preset}")

        lines = [
            "✅ 生图任务已提交，正在后台执行。",
            f"任务ID: {task_id}",
            "状态: 排队/运行中（尚未完成）",
            f"数量: {image_count}张",
            f"模式: {'图生图' if reference_image_count else '文生图'}",
            f"参考图: {reference_image_count}张",
            f"宽高比: {aspect_ratio}，分辨率: {resolution}",
        ]
        if model:
            lines.append(f"模型: {model}")
        if template_summary_parts:
            lines.append("模板: " + "，".join(template_summary_parts))
        if prompt:
            lines.append(f"提示词摘要: {safe_log_text(prompt, 120)}")

        lines.extend(
            [
                "",
                "给 AI 的处理要求:",
                "- 这只是任务提交成功，不代表图片已经生成完成。",
                "- 任务完成后，插件会自动把成功图片或失败原因返回给你继续处理。",
                "- 建议不要给用户发送任何消息;如果一定要发送的话，在符合上下文和人设的情况下告知用户进行等待。",
                "- 不要重复调用 generate_image，也不要声称已经看到最终图片。",
            ]
        )
        return "\n".join(lines)

    def _build_task_result_payload(
        self,
        record: GenerationTaskRecord,
        *,
        supports_image_input: bool,
    ) -> dict[str, Any]:
        """Build structured task result context for the awakened AI."""
        payload: dict[str, Any] = {
            "task_id": record.task_id,
            "source": record.source,
            "status": record.status.value,
            "status_label": record.status_label,
            "prompt": record.prompt_summary,
            "reference_image_count": record.reference_image_count,
            "requested_count": record.requested_count,
            "current_index": record.current_index,
            "aspect_ratio": record.aspect_ratio,
            "resolution": record.resolution,
            "preset_label": record.preset_label,
            "preset": record.preset or "",
            "result_count": record.result_count,
            "result_paths": record.result_paths,
            "error": record.error,
            "message": record.message,
            "images_attached_to_model": supports_image_input
            and bool(record.result_paths),
        }
        if record.duration_seconds is not None:
            payload["duration_seconds"] = round(record.duration_seconds, 2)
        return payload

    def _build_fallback_chain(self, record: GenerationTaskRecord) -> MessageChain:
        """Build a direct user-facing fallback message when AI handling fails."""
        chain = MessageChain()
        if record.error:
            chain.message(f"❌ 生成失败: {record.error}")
            return chain

        if not record.result_paths:
            chain.message("❌ 生成失败: 未能获取生成图片")
            return chain

        for file_path in record.result_paths:
            chain.file_image(file_path)
        info_parts = [f"🧾 任务ID: {record.task_id}"]
        if record.result_count:
            info_parts.append(f"🖼️ 数量: {record.result_count}张")
        chain.message("\n" + "\n".join(info_parts))
        return chain

    async def _send_fallback(
        self,
        record: GenerationTaskRecord,
        *,
        reason: str,
    ) -> None:
        """Directly send task result if the awakened AI cannot handle it."""
        logger.warning(
            f"{log_prefix('Task', record.task_id)} AI 处理生图结果失败，改为直接发送: {safe_log_text(reason, 200)}"
        )
        await self.context.send_message(
            record.unified_msg_origin,
            self._build_fallback_chain(record),
        )

    async def wake_ai_for_generation_task_result(
        self,
        *,
        task_id: str,
        source_event: AstrMessageEvent,
    ) -> None:
        """Wake the main agent to process a completed image generation task."""
        record = self.task_manager.get_generation_task(task_id)
        if not record:
            logger.warning(
                f"{log_prefix('Task', task_id)} 生图任务记录不存在，无法唤醒 AI"
            )
            return
        if record.status == GenerationTaskStatus.CANCELLED:
            logger.debug(f"{log_prefix('Task', task_id)} 生图任务已取消，不唤醒 AI")
            return
        if record.unified_msg_origin != source_event.unified_msg_origin:
            await self._send_fallback(
                record,
                reason="任务会话与来源事件不一致",
            )
            return

        try:
            await self._run_generation_result_agent(
                record,
                source_event=source_event,
            )
        except Exception as exc:
            logger.error(
                f"{log_prefix('Task', task_id)} 唤醒 AI 处理生图结果异常: {exc}",
                exc_info=True,
            )
            await self._send_fallback(record, reason=str(exc))

    async def _run_generation_result_agent(
        self,
        record: GenerationTaskRecord,
        *,
        source_event: AstrMessageEvent,
    ) -> None:
        """Run a proactive agent turn with the completed task result."""
        from astrbot.core.astr_main_agent import (
            MainAgentBuildConfig,
            _get_session_conv,
            build_main_agent,
        )

        session = MessageSession.from_str(record.unified_msg_origin)
        cron_event = CronMessageEvent(
            context=self.context,
            session=session,
            message=f"图像生成任务 {record.task_id} 已完成",
            sender_id=(
                str(source_event.get_self_id())
                if hasattr(source_event, "get_self_id")
                else "astrbot"
            ),
            sender_name="ImageGeneration",
            message_type=session.message_type,
        )
        cron_event.role = source_event.role
        cron_event.plugins_name = source_event.plugins_name

        cfg = self.context.get_config(umo=record.unified_msg_origin)
        provider_settings = cfg.get("provider_settings", {})
        tool_call_timeout = provider_settings.get("tool_call_timeout", 120)
        provider = self.context.get_using_provider(record.unified_msg_origin)
        supports_image_input = bool(
            provider
            and "image" in provider.provider_config.get("modalities", [])
            and record.result_paths
        )
        payload = self._build_task_result_payload(
            record,
            supports_image_input=supports_image_input,
        )

        req = ProviderRequest()
        req.conversation = await _get_session_conv(
            event=cron_event,
            plugin_context=self.context,
        )
        history_context = json.loads(req.conversation.history or "[]")
        if history_context:
            req.contexts = history_context
            context_dump = req._print_friendly_context()
            req.contexts = []
            req.system_prompt += (
                "\n\nBellow is you and user previous conversation history:\n"
                "---\n"
                f"{context_dump}\n"
                "---\n"
            )

        req.system_prompt += IMAGE_GENERATION_TASK_WOKE_SYSTEM_PROMPT.format(
            generation_task_result=json.dumps(payload, ensure_ascii=False)
        )
        req.prompt = (
            "Proceed according to your system instructions. "
            "Output using same language as previous conversation. "
            "Use `send_message_to_user` to deliver the image generation result now. "
            "If the task succeeded, send the generated image file(s) from the provided path(s). "
            "If it failed, send the error message."
        )
        req.extra_user_content_parts.append(
            TextPart(
                text=(
                    "<image_generation_task_result>\n"
                    f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n"
                    "</image_generation_task_result>"
                )
            )
        )
        if supports_image_input:
            req.image_urls = list(record.result_paths)
        else:
            for path in record.result_paths:
                req.extra_user_content_parts.append(
                    TextPart(text=f"[Generated image path: {path}]")
                )

        req.func_tool = ToolSet()
        req.func_tool.add_tool(
            self.context.get_llm_tool_manager().get_builtin_tool(SendMessageToUserTool)
        )

        config = MainAgentBuildConfig(
            tool_call_timeout=tool_call_timeout,
            llm_safety_mode=False,
            streaming_response=False,
            provider_settings=provider_settings,
            computer_use_runtime="none",
            add_cron_tools=False,
        )
        result = await build_main_agent(
            event=cron_event,
            plugin_context=self.context,
            config=config,
            provider=provider,
            req=req,
            apply_reset=False,
        )
        if not result:
            await self._send_fallback(record, reason="无法构建主 Agent")
            return

        # build_main_agent 会按人设/插件设置合并默认工具；这里在 reset 前裁剪，
        # 确保本次主动唤醒只允许 AI 使用 send_message_to_user 交付结果。
        result.provider_request.func_tool = ToolSet()
        result.provider_request.func_tool.add_tool(
            self.context.get_llm_tool_manager().get_builtin_tool(SendMessageToUserTool)
        )
        if result.reset_coro:
            await result.reset_coro

        sent_by_ai = False
        runner = result.agent_runner
        async for agent_resp in runner.step_until_done(30):
            if agent_resp.type != "tool_call_result":
                continue
            chain = agent_resp.data.get("chain")
            if not chain:
                continue
            content = chain.get_plain_text(with_other_comps_mark=True)
            if "Message sent to session" in content:
                sent_by_ai = True
                break

        llm_resp = runner.get_final_llm_resp()
        if not sent_by_ai:
            await self._send_fallback(
                record,
                reason="AI 未通过 send_message_to_user 发送结果",
            )

        summary_note = (
            f"[ImageGenerationTask] task_id={record.task_id}, "
            f"status={record.status.value}, result_count={record.result_count}, "
            f"error={record.error or ''}"
        )
        if llm_resp and llm_resp.completion_text:
            summary_note += f" AI response: {llm_resp.completion_text}"
        with suppress(Exception):
            await persist_agent_history(
                self.context.conversation_manager,
                event=cron_event,
                req=req,
                summary_note=summary_note,
            )
