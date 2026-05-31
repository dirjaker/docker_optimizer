"""CLI 入口 - 命令行 Dockerfile 分析工具"""

import argparse
import sys
from pathlib import Path

from image_analyzer import analyze_dockerfile
from optimizer import generate_suggestions, rewrite_dockerfile
from reporter import print_terminal, to_markdown, to_html


def main():
    parser = argparse.ArgumentParser(
        description="Docker Image Optimizer - 分析并优化 Dockerfile",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s analyze Dockerfile
  %(prog)s analyze Dockerfile --format markdown --output report.md
  %(prog)s analyze Dockerfile --rewrite --output Dockerfile.optimized
  %(prog)s serve --port 8000
        """,
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    # analyze 命令
    analyze_parser = subparsers.add_parser("analyze", help="分析 Dockerfile")
    analyze_parser.add_argument("dockerfile", help="Dockerfile 路径")
    analyze_parser.add_argument(
        "--format", "-f", choices=["terminal", "markdown", "html"],
        default="terminal", help="输出格式 (默认: terminal)",
    )
    analyze_parser.add_argument("--output", "-o", help="输出文件路径")
    analyze_parser.add_argument("--rewrite", "-r", action="store_true", help="生成优化后的 Dockerfile")

    # serve 命令
    serve_parser = subparsers.add_parser("serve", help="启动 API 服务")
    serve_parser.add_argument("--host", default="0.0.0.0", help="监听地址")
    serve_parser.add_argument("--port", type=int, default=8000, help="端口")

    args = parser.parse_args()

    if args.command == "analyze":
        _run_analyze(args)
    elif args.command == "serve":
        _run_serve(args)
    else:
        parser.print_help()
        sys.exit(1)


def _run_analyze(args):
    path = args.dockerfile
    if not Path(path).exists():
        print(f"错误: 文件 '{path}' 不存在", file=sys.stderr)
        sys.exit(1)

    result = analyze_dockerfile(path)
    suggestions = generate_suggestions(result)
    result.suggestions = suggestions

    # 输出格式
    if args.format == "markdown":
        content = to_markdown(result, suggestions)
    elif args.format == "html":
        content = to_html(result, suggestions)
    else:
        content = None

    if content:
        if args.output:
            Path(args.output).write_text(content)
            print(f"报告已保存到: {args.output}")
        else:
            print(content)
    else:
        print_terminal(result)

    # 重写 Dockerfile
    if args.rewrite:
        optimized = rewrite_dockerfile(result)
        out_path = args.output or f"{path}.optimized"
        Path(out_path).write_text(optimized)
        print(f"优化后的 Dockerfile 已保存到: {out_path}")


def _run_serve(args):
    try:
        import uvicorn
    except ImportError:
        print("请安装 uvicorn: pip install uvicorn", file=sys.stderr)
        sys.exit(1)

    print(f"启动 Docker Image Optimizer API at http://{args.host}:{args.port}")
    uvicorn.run("api:app", host=args.host, port=args.port, reload=True)


if __name__ == "__main__":
    main()
