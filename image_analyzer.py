"""镜像分析器 - 解析 Dockerfile、分析层、检测问题"""

import os
import re
from pathlib import Path
from typing import Optional

from models import (
    AnalysisResult, DockerInstruction, Issue, IssueType, LayerInfo,
    OptimizationSuggestion, Severity,
)

# 常见大镜像 -> 精简替代
SLIM_ALTERNATIVES = {
    "python:3.11": "python:3.11-slim",
    "python:3.12": "python:3.12-slim",
    "python:3.10": "python:3.10-slim",
    "python:3": "python:3-slim",
    "python": "python:slim",
    "node:18": "node:18-slim",
    "node:20": "node:20-slim",
    "node:22": "node:22-slim",
    "node": "node:slim",
    "ruby:3.2": "ruby:3.2-slim",
    "openjdk:17": "eclipse-temurin:17-jre-alpine",
    "openjdk:21": "eclipse-temurin:21-jre-alpine",
    "golang:1.21": "golang:1.21-alpine",
    "golang:1.22": "golang:1.22-alpine",
    "php:8.2": "php:8.2-cli-alpine",
    "ubuntu:22.04": "ubuntu:22.04 (consider alpine if possible)",
}

# 镜像大小估算（MB）
IMAGE_SIZE_ESTIMATES = {
    "ubuntu:22.04": 77, "ubuntu:latest": 77, "ubuntu": 77,
    "debian:bookworm": 117, "debian:latest": 117, "debian": 117,
    "python:3.11": 920, "python:3.11-slim": 130, "python:3.11-alpine": 50,
    "python:3.12": 950, "python:3.12-slim": 140, "python:3.12-alpine": 52,
    "node:18": 990, "node:18-slim": 180, "node:18-alpine": 120,
    "node:20": 1000, "node:20-slim": 185, "node:20-alpine": 125,
    "node:22": 1010, "node:22-slim": 190, "node:22-alpine": 128,
    "ruby:3.2": 880, "ruby:3.2-slim": 140, "ruby:3.2-alpine": 55,
    "golang:1.21": 810, "golang:1.21-alpine": 260,
    "golang:1.22": 820, "golang:1.22-alpine": 265,
    "openjdk:17": 470, "openjdk:21": 480,
    "eclipse-temurin:17-jre-alpine": 170, "eclipse-temurin:21-jre-alpine": 180,
    "alpine:3.18": 7, "alpine:3.19": 7, "alpine:latest": 7, "alpine": 7,
    "nginx:latest": 142, "nginx:alpine": 42,
    "postgres:16": 380, "mysql:8": 450,
    "redis:latest": 117, "redis:alpine": 32,
}


def parse_dockerfile(path: str) -> list[DockerInstruction]:
    """解析 Dockerfile，提取指令"""
    instructions = []
    content = Path(path).read_text()
    
    # 处理续行
    lines = content.split("\n")
    merged_lines = []
    buffer = ""
    for line in lines:
        stripped = line.rstrip()
        if stripped.endswith("\\"):
            buffer += stripped[:-1] + " "
        else:
            buffer += stripped
            merged_lines.append(buffer)
            buffer = ""
    if buffer:
        merged_lines.append(buffer)
    
    for i, line in enumerate(merged_lines, 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.match(r"^([A-Z]+)\s+(.*)", line, re.DOTALL)
        if match:
            instructions.append(DockerInstruction(
                line_number=i,
                instruction=match.group(1),
                arguments=match.group(2).strip(),
                raw=line,
            ))
    return instructions


def extract_base_image(instructions: list[DockerInstruction]) -> str:
    """提取基础镜像"""
    for inst in instructions:
        if inst.instruction == "FROM":
            parts = inst.arguments.split()
            return parts[0] if parts else "unknown"
    return "unknown"


def detect_multistage(instructions: list[DockerInstruction]) -> bool:
    """检测是否使用多阶段构建"""
    from_count = sum(1 for i in instructions if i.instruction == "FROM")
    return from_count > 1


def build_layers(instructions: list[DockerInstruction]) -> list[LayerInfo]:
    """构建层信息"""
    layers = []
    for idx, inst in enumerate(instructions):
        desc = ""
        cacheable = True
        if inst.instruction == "RUN":
            desc = f"运行命令: {inst.arguments[:60]}..."
            # 涉及 apt update 等可能影响缓存
            if "apt-get update" in inst.arguments:
                cacheable = False
        elif inst.instruction == "COPY":
            desc = f"复制文件: {inst.arguments[:60]}"
        elif inst.instruction == "ADD":
            desc = f"添加文件: {inst.arguments[:60]}"
        elif inst.instruction == "FROM":
            desc = f"基础镜像: {inst.arguments}"
        else:
            desc = f"{inst.instruction}: {inst.arguments[:60]}"

        layers.append(LayerInfo(
            index=idx,
            instruction=inst,
            cacheable=cacheable,
            description=desc,
        ))
    return layers


def estimate_image_size(base_image: str) -> Optional[float]:
    """估算镜像大小"""
    return IMAGE_SIZE_ESTIMATES.get(base_image)


def check_dockerignore(dockerfile_path: str) -> bool:
    """检查是否存在 .dockerignore"""
    directory = Path(dockerfile_path).parent
    return (directory / ".dockerignore").exists()


def detect_issues(
    instructions: list[DockerInstruction],
    base_image: str,
    has_multistage: bool,
    has_dockerignore: bool,
) -> list[Issue]:
    """检测常见问题"""
    issues = []

    # 1. 大基础镜像
    image_base = base_image.split(":")[0]
    image_tag = base_image
    if image_base in SLIM_ALTERNATIVES or image_tag in SLIM_ALTERNATIVES:
        alt = SLIM_ALTERNATIVES.get(image_tag) or SLIM_ALTERNATIVES.get(image_base, "")
        issues.append(Issue(
            issue_type=IssueType.LARGE_BASE_IMAGE,
            severity=Severity.WARNING,
            title="使用了较大的基础镜像",
            description=f"基础镜像 `{base_image}` 体积较大，建议使用精简版本。",
            line_number=next(
                (i.line_number for i in instructions if i.instruction == "FROM"), None
            ),
            suggestion=f"使用 `{alt}` 替代 `{base_image}`，可减少 60-80% 体积。",
        ))

    # 2. latest 标签
    if ":" not in base_image or base_image.endswith(":latest"):
        issues.append(Issue(
            issue_type=IssueType.LATEST_TAG,
            severity=Severity.WARNING,
            title="使用 latest 标签",
            description="使用 `latest` 标签会导致构建不可重复。",
            line_number=next(
                (i.line_number for i in instructions if i.instruction == "FROM"), None
            ),
            suggestion="固定版本标签，如 `python:3.12-slim` 而非 `python:latest`。",
        ))

    # 3. 未清理包管理器缓存
    for inst in instructions:
        if inst.instruction == "RUN" and "apt-get install" in inst.arguments:
            if "rm -rf /var/lib/apt/lists" not in inst.arguments:
                issues.append(Issue(
                    issue_type=IssueType.CACHE_NOT_CLEANED,
                    severity=Severity.WARNING,
                    title="未清理 apt 缓存",
                    description="RUN 指令中安装了包但未清理 apt 缓存。",
                    line_number=inst.line_number,
                    suggestion="在安装后添加 `&& rm -rf /var/lib/apt/lists/*`。",
                ))
        if inst.instruction == "RUN" and "pip install" in inst.arguments:
            if "--no-cache-dir" not in inst.arguments:
                issues.append(Issue(
                    issue_type=IssueType.CACHE_NOT_CLEANED,
                    severity=Severity.INFO,
                    title="pip 未禁用缓存",
                    description="pip install 未使用 `--no-cache-dir`。",
                    line_number=inst.line_number,
                    suggestion="添加 `--no-cache-dir` 参数减少缓存体积。",
                ))

    # 4. 未使用多阶段构建
    has_build_tools = any(
        "gcc" in i.arguments or "make" in i.arguments or "build-essential" in i.arguments
        for i in instructions if i.instruction == "RUN"
    )
    if not has_multistage and has_build_tools:
        issues.append(Issue(
            issue_type=IssueType.NO_MULTISTAGE,
            severity=Severity.WARNING,
            title="未使用多阶段构建",
            description="检测到编译工具但未使用多阶段构建，编译工具会留在最终镜像中。",
            suggestion="使用多阶段构建，编译阶段和运行阶段分离。",
        ))

    # 5. 无 .dockerignore
    if not has_dockerignore:
        issues.append(Issue(
            issue_type=IssueType.NO_DOCKERIGNORE,
            severity=Severity.INFO,
            title="未找到 .dockerignore",
            description="没有 .dockerignore 可能导致不必要的文件被复制到镜像中。",
            suggestion="创建 .dockerignore 排除 .git、node_modules、__pycache__ 等。",
        ))

    # 6. RUN 命令未合并
    run_indices = [
        i for i, inst in enumerate(instructions) if inst.instruction == "RUN"
    ]
    consecutive_runs = 0
    for i in range(len(run_indices) - 1):
        if run_indices[i + 1] - run_indices[i] == 1:
            consecutive_runs += 1
    if consecutive_runs >= 2:
        issues.append(Issue(
            issue_type=IssueType.RUN_NOT_MERGED,
            severity=Severity.INFO,
            title="多个连续 RUN 指令未合并",
            description=f"检测到 {consecutive_runs + 1} 个连续 RUN 指令，每个 RUN 创建一个新层。",
            suggestion="使用 `&&` 将多个命令合并到一个 RUN 指令中。",
        ))

    # 7. 以 root 用户运行
    has_user = any(i.instruction == "USER" for i in instructions)
    if not has_user:
        issues.append(Issue(
            issue_type=IssueType.ROOT_USER,
            severity=Severity.INFO,
            title="容器以 root 用户运行",
            description="未指定 USER 指令，容器默认以 root 运行。",
            suggestion="添加 `USER` 指令使用非 root 用户。",
        ))

    return issues


def analyze_dockerfile(path: str) -> AnalysisResult:
    """分析 Dockerfile 的主入口"""
    instructions = parse_dockerfile(path)
    base_image = extract_base_image(instructions)
    has_multistage = detect_multistage(instructions)
    has_dockerignore = check_dockerignore(path)
    layers = build_layers(instructions)
    issues = detect_issues(instructions, base_image, has_multistage, has_dockerignore)

    return AnalysisResult(
        dockerfile_path=path,
        base_image=base_image,
        total_layers=len(layers),
        issues=issues,
        layers=layers,
        estimated_size_mb=estimate_image_size(base_image),
        has_multistage=has_multistage,
        has_dockerignore=has_dockerignore,
    )
