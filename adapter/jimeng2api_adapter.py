from __future__ import annotations

import base64
import time
from typing import Any

from astrbot.api import logger

from ..core.adapters.base import BaseImageAdapter
from ..core.shared.constants import UNSPECIFIED_OPTION
from ..core.shared.logging import safe_log_error_body, safe_log_mapping, safe_log_url
from ..core.shared.types import GenerationRequest, ImageCapability


class Jimeng2APIAdapter(BaseImageAdapter):
    """Jimeng2API image generation adapter."""

    def get_capabilities(self) -> ImageCapability:
        """Return adapter capabilities."""
        return self._get_configured_capabilities()

    # generate() is provided by the base class via the template method pattern.

    async def _generate_once(
        self, request: GenerationRequest
    ) -> tuple[list[bytes] | None, str | None]:
        """Execute one image generation request."""
        start_time = time.time()
        session = self._get_session()
        prefix = self._get_log_prefix(request.task_id)

        prompt_text = request.prompt
        if prompt_text is None:
            return None, "缺少提示词"
        if not isinstance(prompt_text, str):
            logger.warning(f"{prefix} prompt 非字符串类型: {type(prompt_text)}")
            prompt_text = str(prompt_text)

        base_url = self.base_url or "http://localhost:5100"
        headers = {
            "Authorization": f"Bearer {self._get_current_api_key()}",
        }

        try:
            if request.images:
                # Image-to-image uses JSON with data URLs for the image list.
                url = f"{base_url.rstrip('/')}/v1/images/compositions"
                headers["Content-Type"] = "application/json"

                images_as_urls: list[str] = []
                for img in request.images:
                    mime = img.mime_type or "image/jpeg"
                    b64 = base64.b64encode(img.data).decode("ascii")
                    images_as_urls.append(f"data:{mime};base64,{b64}")

                payload: dict[str, object] = {
                    "model": self.model or "jimeng-4.5",
                    "prompt": prompt_text,
                    "images": images_as_urls,
                }
                if request.aspect_ratio and request.aspect_ratio != UNSPECIFIED_OPTION:
                    payload["ratio"] = request.aspect_ratio
                if request.resolution and request.resolution != UNSPECIFIED_OPTION:
                    payload["resolution"] = request.resolution.lower()
                self._log_request_overview(request, url, payload=payload)
                self._log_debug_json("请求", payload, request.task_id)

                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    proxy=self.proxy,
                    timeout=self._get_timeout(),
                ) as resp:
                    duration = time.time() - start_time
                    self._log_response_status(request, resp.status, duration)
                    if resp.status != 200:
                        error_text = await resp.text()
                        self._log_debug_json_text("响应", error_text, request.task_id)
                        self._log_api_error(
                            request,
                            resp.status,
                            duration,
                            error_text,
                            label="Compositions 错误",
                        )
                        return None, self._format_api_error_message(
                            resp.status,
                            error_text,
                        )

                    data_json = await self._read_response_json(resp, request.task_id)
                    if self.debug_request_logging:
                        logger.debug(
                            f"{prefix} Compositions 响应摘要: {safe_log_mapping(data_json)}"
                        )
                    return await self._extract_images(data_json, request.task_id)
            else:
                # Text-to-image request.
                url = f"{base_url.rstrip('/')}/v1/images/generations"
                headers["Content-Type"] = "application/json"

                payload = {
                    "model": self.model or "jimeng-4.5",
                    "prompt": prompt_text,
                    "response_format": "url",  # Use URLs by default, then download them.
                }
                if request.aspect_ratio and request.aspect_ratio != UNSPECIFIED_OPTION:
                    payload["ratio"] = request.aspect_ratio
                if request.resolution and request.resolution != UNSPECIFIED_OPTION:
                    payload["resolution"] = request.resolution.lower()
                self._log_request_overview(request, url, payload=payload)
                self._log_debug_json("请求", payload, request.task_id)

                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    proxy=self.proxy,
                    timeout=self._get_timeout(),
                ) as resp:
                    duration = time.time() - start_time
                    self._log_response_status(request, resp.status, duration)
                    if resp.status != 200:
                        error_text = await resp.text()
                        self._log_debug_json_text("响应", error_text, request.task_id)
                        self._log_api_error(
                            request,
                            resp.status,
                            duration,
                            error_text,
                            label="Generations 错误",
                        )
                        return None, self._format_api_error_message(
                            resp.status,
                            error_text,
                        )

                    data_json = await self._read_response_json(resp, request.task_id)
                    if self.debug_request_logging:
                        logger.debug(
                            f"{prefix} Generations 响应摘要: {safe_log_mapping(data_json)}"
                        )
                    return await self._extract_images(data_json, request.task_id)

        except Exception as e:
            duration = time.time() - start_time
            self._log_request_exception(request, duration, e)
            return None, safe_log_error_body(e)

    async def _extract_images(
        self, response: dict, task_id: str | None = None
    ) -> tuple[list[bytes] | None, str | None]:
        """Extract image bytes from the response payload."""
        prefix = self._get_log_prefix(task_id)
        if response is None:
            return None, "响应为空"
        if "data" not in response:
            return None, f"响应中未找到 data 字段: {safe_log_mapping(response)}"

        data = response.get("data")
        if data is None:
            return None, "data 字段为 None"

        images = []
        for item in data:
            if "b64_json" in item:
                images.append(base64.b64decode(item["b64_json"]))
            elif "url" in item:
                async with self._get_session().get(
                    item["url"], proxy=self.proxy, timeout=self._get_download_timeout()
                ) as resp:
                    if resp.status == 200:
                        images.append(await resp.read())
                    else:
                        logger.error(
                            f"{prefix} 下载图像失败 ({resp.status}): {safe_log_url(item['url'])}"
                        )

        if not images:
            return None, "未找到有效的图片数据"

        return images, None

    async def receive_token(self) -> dict[str, Any]:
        """Receive credits for all configured API keys."""
        results = {}
        if not self.api_keys:
            return {"error": "未配置 API Key"}

        base_url = self.base_url or "http://localhost:5100"
        url = f"{base_url.rstrip('/')}/token/receive"

        for i, key in enumerate(self.api_keys):
            headers = {
                "Authorization": f"Bearer {key}",
            }
            try:
                async with self._get_session().post(
                    url,
                    headers=headers,
                    proxy=self.proxy,
                    timeout=self._get_download_timeout(),
                ) as resp:
                    resp_json = await resp.json()
                    status_code = resp.status
                    results[f"key_{i}"] = {"status": status_code, "data": resp_json}
                    if status_code == 200:
                        logger.info(
                            f"{self._get_log_prefix()} API Key (索引 {i}) 积分领取成功: {safe_log_mapping(resp_json)}"
                        )
                    else:
                        logger.warning(
                            f"{self._get_log_prefix()} API Key (索引 {i}) 积分领取失败 ({status_code}): {safe_log_mapping(resp_json)}"
                        )
            except Exception as e:
                logger.error(
                    f"{self._get_log_prefix()} API Key (索引 {i}) 积分领取请求异常: {safe_log_error_body(e)}"
                )
                results[f"key_{i}"] = {"error": safe_log_error_body(e)}

        return results
