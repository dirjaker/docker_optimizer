"""优化器 - 生成优化建议、重写 Dockerfile"""

import re
from pathlib import Path

from models import AnalysisResult, OptimizationSuggestion
from image_analyzer import SLIM_ALTERNATIVES


def generate_suggestions(result: AnalysisResult) -> list[OptimizationSuggestion]:
    """基于分析结果生成优化建议"""
    suggestions = []
    priority = 1

    # 1. 精简基础镜像
    base = result.base_image
    alt = SLIM_ALTERNATIVES.get(base) or SLIM_ALTERNATIVES.get(base.split(":")[0], "")
    if alt:
        suggestions.append(OptimizationSuggestion(
            title="使用精简基础镜像",
            description=f"将 `{base}` 替换为 `{alt}`，预计可减少 60-80% 基础镜像体积。",
            priority=priority,
            estimated_savings="60-80% 基础镜像体积",
            example_before=f"FROM {base}",
            example_after=f"FROM {alt}",
        ))
        priority += 1

    # 2. 多阶段构建
    if not result.has_multistage:
        suggestions.append(OptimizationSuggestion(
            title="使用多阶段构建",
            description="将编译/构建和运行分离，最终镜像只包含运行时依赖。",
            priority=priority,
            estimated_savings="40-70% 总镜像体积",
            example_before="FROM python:3.11\nCOPY . .\nRUN pip install . && pip install build-tools",
            example_after="FROM python:3.11-slim AS builder\nCOPY . .\nRUN pip install .\n\nFROM python:3.11-slim\nCOPY --from=builder /app /app",
        ))
        priority += 1

    # 3. 合并 RUN 指令
    run_count = sum(1 for l in result.layers if l.instruction.instruction == "RUN")
    if run_count > 3:
        suggestions.append(OptimizationSuggestion(
            title="合并 RUN 指令",
            description=f"当前有 {run_count} 个 RUN 指令，每个创建一层。合并可减少层数和体积。",
            priority=priority,
            estimated_savings="每合并一层约 1-5MB",
            example_before="RUN apt-get update\nRUN apt-get install -y curl\nRUN rm -rf /var/lib/apt/lists/*",
            example_after="RUN apt-get update && \\\n    apt-get install -y curl && \\\n    rm -rf /var/lib/apt/lists/*",
        ))
        priority += 1

    # 4. 清理缓存
    suggestions.append(OptimizationSuggestion(
        title="清理包管理器缓存",
        description="在安装包后清理缓存，减少层体积。",
        priority=priority,
        estimated_savings="10-50MB",
        example_before="RUN apt-get update && apt-get install -y curl",
        example_after="RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*",
    ))
    priority += 1

    # 5. .dockerignore
    if not result.has_dockerignore:
        suggestions.append(OptimizationSuggestion(
            title="添加 .dockerignore",
            description="排除不必要的文件（.git、node_modules 等）减少构建上下文大小。",
            priority=priority,
            estimated_savings="减少构建上下文传输时间",
            example_before="# 无 .dockerignore",
            example_after=".git\nnode_modules\n__pycache__\n*.pyc\n.env\n.vscode",
        ))
        priority += 1

    # 6. pip --no-cache-dir
    for layer in result.layers:
        if "pip install" in layer.instruction.arguments and "--no-cache-dir" not in layer.instruction.arguments:
            suggestions.append(OptimizationSuggestion(
                title="pip 禁用缓存",
                description="使用 `--no-cache-dir` 避免 pip 缓存占用空间。",
                priority=priority,
                estimated_savings="10-30MB",
                example_before="RUN pip install -r requirements.txt",
                example_after="RUN pip install --no-cache-dir -r requirements.txt",
            ))
            priority += 1
            break

    # 7. 使用 BuildKit 缓存挂载
    suggestions.append(OptimizationSuggestion(
        title="使用 BuildKit 缓存挂载",
        description="利用 `--mount=type=cache` 避免重复下载包。",
        priority=priority,
        estimated_savings="加速构建，减少网络传输",
        example_before="RUN apt-get update && apt-get install -y curl",
        example_after="RUN --mount=type=cache,target=/var/cache/apt \\\n    apt-get update && apt-get install -y curl",
    ))

    return sorted(suggestions, key=lambda s: s.priority)


def rewrite_dockerfile(result: AnalysisResult) -> str:
    """生成优化后的 Dockerfile"""
    path = Path(result.dockerfile_path)
    original = path.read_text()
    lines = original.split("\n")
    optimized = []
    base = result.base_image
    alt = SLIM_ALTERNATIVES.get(base) or SLIM_ALTERNATIVES.get(base.split(":")[0], "")

    run_buffer = []
    in_run_block = False

    for line in lines:
        stripped = line.strip()

        # 替换基础镜像
        if stripped.upper().startswith("FROM "):
            if alt and not result.has_multistage:
                optimized.append(f"FROM {alt}")
            else:
                optimized.append(line)
            continue

        # 处理 RUN 指令
        if stripped.upper().startswith("RUN "):
            cmd = stripped[4:].strip()
            run_buffer.append(cmd)
            in_run_block = True
            continue

        # 非 RUN 指令，先输出合并的 RUN
        if in_run_block:
            _flush_run_buffer(optimized, run_buffer)
            run_buffer = []
            in_run_block = False

        # 清理 COPY 的不必要文件
        if stripped.upper().startswith("COPY "):
            optimized.append(line)
            continue

        optimized.append(line)

    # 最后如果有残留 RUN
    if run_buffer:
        _flush_run_buffer(optimized, run_buffer)

    # 添加 .dockerignore 提示
    if not result.has_dockerignore:
        optimized.append("")
        optimized.append("# NOTE: 请创建 .dockerignore 文件排除不必要的文件")

    return "\n".join(optimized) + "\n"


def _flush_run_buffer(output: list[str], commands: list[str]):
    """合并多个 RUN 命令为一个"""
    if len(commands) == 1:
        output.append(f"RUN {commands[0]}")
    elif len(commands) > 1:
        merged = " && \\\n    ".join(commands)
        output.append(f"RUN {merged}")
