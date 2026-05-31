"""FastAPI 服务 - 在线分析 Dockerfile"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import tempfile
import os

from image_analyzer import analyze_dockerfile
from optimizer import generate_suggestions, rewrite_dockerfile
from reporter import to_markdown, to_html

app = FastAPI(
    title="Docker Image Optimizer API",
    description="分析 Dockerfile 并提供优化建议",
    version="1.0.0",
)


class AnalyzeRequest(BaseModel):
    dockerfile_content: str
    format: Optional[str] = "json"  # json / markdown / html


class IssueResponse(BaseModel):
    issue_type: str
    severity: str
    title: str
    description: str
    line_number: Optional[int] = None
    suggestion: str = ""


class SuggestionResponse(BaseModel):
    title: str
    description: str
    priority: int
    estimated_savings: str = ""


class AnalysisResponse(BaseModel):
    base_image: str
    total_layers: int
    estimated_size_mb: Optional[float] = None
    has_multistage: bool
    has_dockerignore: bool
    issues: list[IssueResponse]
    suggestions: list[SuggestionResponse]
    optimized_dockerfile: Optional[str] = None
    report: Optional[str] = None


@app.get("/")
def root():
    return {
        "service": "Docker Image Optimizer",
        "version": "1.0.0",
        "endpoints": {
            "POST /analyze": "分析 Dockerfile 内容",
            "POST /analyze/file": "上传 Dockerfile 文件分析",
        },
    }


@app.post("/analyze", response_model=AnalysisResponse)
def analyze(req: AnalyzeRequest):
    """分析 Dockerfile 内容"""
    # 写入临时文件
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

        return AnalysisResponse(
            base_image=result.base_image,
            total_layers=result.total_layers,
            estimated_size_mb=result.estimated_size_mb,
            has_multistage=result.has_multistage,
            has_dockerignore=result.has_dockerignore,
            issues=[
                IssueResponse(
                    issue_type=i.issue_type.value,
                    severity=i.severity.value,
                    title=i.title,
                    description=i.description,
                    line_number=i.line_number,
                    suggestion=i.suggestion,
                )
                for i in result.issues
            ],
            suggestions=[
                SuggestionResponse(
                    title=s.title,
                    description=s.description,
                    priority=s.priority,
                    estimated_savings=s.estimated_savings,
                )
                for s in suggestions
            ],
            optimized_dockerfile=optimized,
            report=report,
        )
    finally:
        os.unlink(tmp_path)


@app.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_file(
    file: UploadFile = File(...),
    format: str = "json",
):
    """上传 Dockerfile 文件进行分析"""
    content = await file.read()
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(400, "文件必须是 UTF-8 编码的文本文件")

    return analyze(AnalyzeRequest(dockerfile_content=text, format=format))


@app.get("/health")
def health():
    return {"status": "ok"}
