"""
Core module for image generation plugin
图像生成插件的核心模块
"""

from .base_adapter import BaseImageAdapter
from .config_manager import (
    ConfigManager,
    GenerationSettings,
    ImageAuditSettings,
    PluginConfig,
    PromptAuditSettings,
    SafetyAuditSettings,
    UsageSettings,
)
from .constants import (
    DEFAULT_ASPECT_RATIO,
    DEFAULT_MAX_RETRY_ATTEMPTS,
    DEFAULT_RESOLUTION,
    DEFAULT_TIMEOUT,
    GEMINI_DEFAULT_BASE_URL,
    GEMINI_SAFETY_CATEGORIES,
    GITEE_AI_DEFAULT_BASE_URL,
    JIMENG_DEFAULT_BASE_URL,
    LOG_PREFIX,
    OPENAI_DEFAULT_BASE_URL,
    RESOLUTION_1K_MAP,
    RESOLUTION_2K_MAP,
    SUPPORTED_ASPECT_RATIOS,
    SUPPORTED_RESOLUTIONS,
)
from .generation_executor import GenerationExecutor
from .generation_task_models import (
    GenerationTaskCreationError,
    GenerationTaskItem,
    GenerationTaskItemStatus,
    GenerationTaskRecord,
    GenerationTaskStatus,
)
from .generation_task_store import GenerationTaskStore
from .generator import ImageGenerator
from .image_processor import ImageProcessor
from .llm_tool import (
    ImageGenerationTool,
    ImageTaskTool,
    PresetEditTool,
    PresetQueryTool,
    adjust_tool_parameters,
)
from .logging_utils import (
    log_prefix,
    mask_sensitive,
    safe_log_error_body,
    safe_log_mapping,
    safe_log_text,
    safe_log_url,
)
from .safety_auditor import SafetyAuditor
from .task_manager import TaskManager
from .types import (
    AdapterConfig,
    AdapterMetadata,
    AdapterType,
    GenerationRequest,
    GenerationResult,
    ImageCapability,
    ImageData,
)
from .usage_manager import UsageManager
from .utils import (
    convert_image_format,
    convert_images_batch,
    detect_mime_type,
    validate_aspect_ratio,
    validate_resolution,
)

__all__ = [
    # 基类和核心组件
    "BaseImageAdapter",
    "ImageGenerator",
    "GenerationExecutor",
    "TaskManager",
    # 新增管理器
    "ConfigManager",
    "UsageManager",
    "ImageProcessor",
    # 配置数据类
    "PluginConfig",
    "UsageSettings",
    "GenerationSettings",
    "PromptAuditSettings",
    "ImageAuditSettings",
    "SafetyAuditSettings",
    # LLM 工具
    "ImageGenerationTool",
    "ImageTaskTool",
    "PresetQueryTool",
    "PresetEditTool",
    "adjust_tool_parameters",
    "SafetyAuditor",
    # 数据类型
    "AdapterConfig",
    "AdapterMetadata",
    "AdapterType",
    "GenerationRequest",
    "GenerationResult",
    "GenerationTaskCreationError",
    "GenerationTaskItem",
    "GenerationTaskItemStatus",
    "GenerationTaskRecord",
    "GenerationTaskStatus",
    "GenerationTaskStore",
    "ImageCapability",
    "ImageData",
    # 工具函数
    "convert_image_format",
    "convert_images_batch",
    "detect_mime_type",
    "log_prefix",
    "mask_sensitive",
    "safe_log_error_body",
    "safe_log_mapping",
    "safe_log_text",
    "safe_log_url",
    "validate_aspect_ratio",
    "validate_resolution",
    # 常量
    "LOG_PREFIX",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRY_ATTEMPTS",
    "DEFAULT_ASPECT_RATIO",
    "DEFAULT_RESOLUTION",
    "GEMINI_DEFAULT_BASE_URL",
    "GEMINI_SAFETY_CATEGORIES",
    "OPENAI_DEFAULT_BASE_URL",
    "GITEE_AI_DEFAULT_BASE_URL",
    "JIMENG_DEFAULT_BASE_URL",
    "RESOLUTION_1K_MAP",
    "RESOLUTION_2K_MAP",
    "SUPPORTED_ASPECT_RATIOS",
    "SUPPORTED_RESOLUTIONS",
]
