"""
Web Dashboard for Docker Optimizer
Provides a dashboard for analyzing and optimizing Dockerfiles.
"""
import sys
import tempfile
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from image_analyzer import analyze_dockerfile
from optimizer import generate_suggestions, rewrite_dockerfile
from reporter import to_markdown, to_html

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Docker Optimizer Dashboard",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/api/health")
async def health():
    return {"status": "ok"}


class AnalyzeRequest(BaseModel):
    dockerfile_content: str
    format: Optional[str] = "json"


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest):
    with tempfile.NamedTemporaryFile(mode="w", suffix="Dockerfile", delete=False) as f:
        f.write(req.dockerfile_content)
        tmp_path = f.name

    try:
        result = analyze_dockerfile(tmp_path)
        suggestions = generate_suggestions(result)
        result.suggestions = suggestions
        optimized = rewrite_dockerfile(result)

        report = None
        if req.format == "markdown":
            report = to_markdown(result, suggestions)
        elif req.format == "html":
            report = to_html(result, suggestions)

        return {
            "base_image": result.base_image,
            "total_layers": result.total_layers,
            "estimated_size_mb": result.estimated_size_mb,
            "has_multistage": result.has_multistage,
            "has_dockerignore": result.has_dockerignore,
            "issues": [
                {
                    "issue_type": i.issue_type.value,
                    "severity": i.severity.value,
                    "title": i.title,
                    "description": i.description,
                    "line_number": i.line_number,
                    "suggestion": i.suggestion,
                }
                for i in result.issues
            ],
            "suggestions": [
                {
                    "title": s.title,
                    "description": s.description,
                    "priority": s.priority,
                    "estimated_savings": s.estimated_savings,
                    "example_before": s.example_before,
                    "example_after": s.example_after,
                }
                for s in suggestions
            ],
            "optimized_dockerfile": optimized,
            "report": report,
        }
    finally:
        os.unlink(tmp_path)


@app.get("/api/rules")
async def get_rules():
    return {
        "rules": [
            {"id": "large_base_image", "severity": "warning", "title": "Large base image detected"},
            {"id": "cache_not_cleaned", "severity": "warning", "title": "Package cache not cleaned"},
            {"id": "no_multistage", "severity": "warning", "title": "No multi-stage build"},
            {"id": "unnecessary_files", "severity": "info", "title": "Unnecessary files included"},
            {"id": "no_dockerignore", "severity": "info", "title": "Missing .dockerignore"},
            {"id": "run_not_merged", "severity": "info", "title": "RUN instructions not merged"},
            {"id": "latest_tag", "severity": "warning", "title": "Using latest tag"},
            {"id": "root_user", "severity": "info", "title": "Running as root"},
        ]
    }


def run_dashboard(host: str = "0.0.0.0", port: int = 8080):
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_dashboard()
