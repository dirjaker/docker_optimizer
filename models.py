"""数据模型 - 镜像信息、层信息、优化建议"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class IssueType(str, Enum):
    LARGE_BASE_IMAGE = "large_base_image"
    CACHE_NOT_CLEANED = "cache_not_cleaned"
    NO_MULTISTAGE = "no_multistage"
    UNNECESSARY_FILES = "unnecessary_files"
    NO_DOCKERIGNORE = "no_dockerignore"
    RUN_NOT_MERGED = "run_not_merged"
    NO_BUILDKIT_CACHE = "no_buildkit_cache"
    LATEST_TAG = "latest_tag"
    ROOT_USER = "root_user"
    APT_NO_VERSION_PIN = "apt_no_version_pin"


@dataclass
class DockerInstruction:
    """Dockerfile 指令"""
    line_number: int
    instruction: str  # FROM, RUN, COPY, etc.
    arguments: str
    raw: str


@dataclass
class LayerInfo:
    """镜像层信息"""
    index: int
    instruction: DockerInstruction
    estimated_size_mb: Optional[float] = None
    cacheable: bool = True
    description: str = ""


@dataclass
class Issue:
    """检测到的问题"""
    issue_type: IssueType
    severity: Severity
    title: str
    description: str
    line_number: Optional[int] = None
    suggestion: str = ""


@dataclass
class OptimizationSuggestion:
    """优化建议"""
    title: str
    description: str
    priority: int  # 1=最高
    estimated_savings: str = ""
    example_before: str = ""
    example_after: str = ""


@dataclass
class AnalysisResult:
    """分析结果"""
    dockerfile_path: str
    base_image: str
    total_layers: int
    issues: list[Issue] = field(default_factory=list)
    suggestions: list[OptimizationSuggestion] = field(default_factory=list)
    layers: list[LayerInfo] = field(default_factory=list)
    estimated_size_mb: Optional[float] = None
    has_multistage: bool = False
    has_dockerignore: bool = False
