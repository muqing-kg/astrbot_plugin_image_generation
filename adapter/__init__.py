"""
Adapter module for image generation plugin
图像生成插件的适配器模块
"""

from .agnes_ai_adapter import AgnesAIAdapter
from .custom_http_adapter import CustomHTTPAdapter
from .gemini_adapter import GeminiAdapter
from .gitee_ai_adapter import GiteeAIAdapter
from .grok_adapter import GrokAdapter
from .jimeng2api_adapter import Jimeng2APIAdapter
from .openai_adapter import OpenAIAdapter
from .openai_chat_adapter import OpenAIChatAdapter
from .siliconflow_adapter import SiliconFlowAdapter
from .volcengine_ark_adapter import VolcengineArkAdapter

__all__ = [
    "AgnesAIAdapter",
    "CustomHTTPAdapter",
    "GeminiAdapter",
    "OpenAIChatAdapter",
    "GiteeAIAdapter",
    "OpenAIAdapter",
    "SiliconFlowAdapter",
    "VolcengineArkAdapter",
    "Jimeng2APIAdapter",
    "GrokAdapter",
]
