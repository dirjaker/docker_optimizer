"""报告生成器 - Markdown/HTML/终端输出"""

from datetime import datetime
from models import AnalysisResult, OptimizationSuggestion, Severity

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    HAS_RICH = True
except ImportError:
    HAS_RICH = False


SEVERITY_COLORS = {
    Severity.CRITICAL: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "blue",
}

SEVERITY_ICONS = {
    Severity.CRITICAL: "🔴",
    Severity.WARNING: "🟡",
    Severity.INFO: "🔵",
}


def print_terminal(result: AnalysisResult):
    """终端输出报告"""
    if HAS_RICH:
        _print_rich(result)
    else:
        _print_plain(result)


def _print_rich(result: AnalysisResult):
    console = Console()
    console.print()
    console.print(Panel(
        f"[bold]Docker 镜像分析报告[/bold]\n"
        f"文件: {result.dockerfile_path}\n"
        f"基础镜像: {result.base_image}\n"
        f"层数: {result.total_layers}\n"
        f"估算大小: {result.estimated_size_mb or '未知'} MB\n"
        f"多阶段构建: {'✅' if result.has_multistage else '❌'}\n"
        f".dockerignore: {'✅' if result.has_dockerignore else '❌'}",
        title="📋 分析概览",
        border_style="blue",
    ))

    # 问题表
    if result.issues:
        table = Table(title="⚠️  检测到的问题")
        table.add_column("严重度", width=6)
        table.add_column("问题", style="bold")
        table.add_column("行号", width=6)
        table.add_column("建议")
        for issue in result.issues:
            icon = SEVERITY_ICONS.get(issue.severity, "")
            table.add_row(
                icon, issue.title,
                str(issue.line_number or "-"), issue.suggestion[:80],
            )
        console.print(table)

    # 优化建议
    if result.suggestions:
        console.print()
        console.print("[bold green]💡 优化建议[/bold green]")
        for s in result.suggestions:
            console.print(f"  {s.priority}. [bold]{s.title}[/bold]")
            console.print(f"     {s.description}")
            if s.estimated_savings:
                console.print(f"     预计节省: [cyan]{s.estimated_savings}[/cyan]")

    console.print()


def _print_plain(result: AnalysisResult):
    print(f"\n{'='*60}")
    print(f"Docker 镜像分析报告")
    print(f"{'='*60}")
    print(f"文件: {result.dockerfile_path}")
    print(f"基础镜像: {result.base_image}")
    print(f"层数: {result.total_layers}")
    print(f"估算大小: {result.estimated_size_mb or '未知'} MB")
    print(f"多阶段构建: {'是' if result.has_multistage else '否'}")
    print(f".dockerignore: {'是' if result.has_dockerignore else '否'}")

    if result.issues:
        print(f"\n检测到的问题 ({len(result.issues)}):")
        for issue in result.issues:
            print(f"  [{issue.severity.value.upper()}] {issue.title}")
            print(f"    {issue.suggestion}")

    if result.suggestions:
        print(f"\n优化建议:")
        for s in result.suggestions:
            print(f"  {s.priority}. {s.title} - {s.estimated_savings}")
    print()


def to_markdown(result: AnalysisResult, suggestions: list[OptimizationSuggestion] = None) -> str:
    """生成 Markdown 报告"""
    lines = [
        "# Docker 镜像分析报告",
        "",
        f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**文件**: `{result.dockerfile_path}`",
        "",
        "## 📋 概览",
        "",
        f"| 项目 | 值 |",
        f"|------|-----|",
        f"| 基础镜像 | `{result.base_image}` |",
        f"| 层数 | {result.total_layers} |",
        f"| 估算大小 | {result.estimated_size_mb or '未知'} MB |",
        f"| 多阶段构建 | {'✅' if result.has_multistage else '❌'} |",
        f"| .dockerignore | {'✅' if result.has_dockerignore else '❌'} |",
        "",
    ]

    if result.issues:
        lines.append("## ⚠️ 检测到的问题\n")
        for issue in result.issues:
            icon = SEVERITY_ICONS.get(issue.severity, "")
            lines.append(f"### {icon} {issue.title}\n")
            lines.append(f"- **严重度**: {issue.severity.value}")
            if issue.line_number:
                lines.append(f"- **行号**: {issue.line_number}")
            lines.append(f"- **描述**: {issue.description}")
            lines.append(f"- **建议**: {issue.suggestion}")
            lines.append("")

    suggestions = suggestions or result.suggestions
    if suggestions:
        lines.append("## 💡 优化建议\n")
        for s in suggestions:
            lines.append(f"### {s.priority}. {s.title}\n")
            lines.append(f"{s.description}\n")
            if s.estimated_savings:
                lines.append(f"**预计节省**: {s.estimated_savings}\n")
            if s.example_before:
                lines.append("**优化前**:")
                lines.append(f"```dockerfile\n{s.example_before}\n```\n")
            if s.example_after:
                lines.append("**优化后**:")
                lines.append(f"```dockerfile\n{s.example_after}\n```\n")

    lines.append("---\n*由 Docker Image Optimizer 生成*")
    return "\n".join(lines)


def to_html(result: AnalysisResult, suggestions: list[OptimizationSuggestion] = None) -> str:
    """生成 HTML 报告"""
    md = to_markdown(result, suggestions)
    # 简单的 HTML 包装
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Docker 镜像分析报告</title>
<style>
body {{ font-family: -apple-system, sans-serif; max-width: 900px; margin: 40px auto; padding: 0 20px; line-height: 1.6; }}
h1 {{ color: #2563eb; }}
h2 {{ color: #1e40af; border-bottom: 1px solid #e5e7eb; padding-bottom: 8px; }}
code {{ background: #f3f4f6; padding: 2px 6px; border-radius: 4px; }}
pre {{ background: #1e293b; color: #e2e8f0; padding: 16px; border-radius: 8px; overflow-x: auto; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #e5e7eb; padding: 8px 12px; text-align: left; }}
th {{ background: #f9fafb; }}
</style></head><body>
<pre>{md}</pre>
</body></html>"""
