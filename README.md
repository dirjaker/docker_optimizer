<div align="center">

# 🐳 Docker Optimizer

### Docker 镜像优化分析工具

[![优化](https://img.shields.io/badge/优化-5-blue?style=flat-square)]()
[![检测](https://img.shields.io/badge/检测-8-green?style=flat-square)]()
[![框架](https://img.shields.io/badge/框架-Click+Rich-orange?style=flat-square)]()
[![更新](https://img.shields.io/badge/更新-2025.06-red?style=flat-square)]()

*镜像层分析 · 多阶段构建建议 · 安全扫描 · 体积优化 · CI 集成*

</div>

---

# Docker Image Optimizer

分析 Docker 镜像层，检测问题，给出优化建议，帮助减小镜像体积。

## ✨ 特性

- **Dockerfile 解析** - 完整解析 Dockerfile 指令和参数
- **问题检测** - 自动检测 10+ 种常见优化问题
- **优化建议** - 生成具体的优化建议和示例代码
- **Dockerfile 重写** - 自动生成优化后的 Dockerfile
- **多格式报告** - 支持终端/Markdown/HTML 输出
- **API 服务** - FastAPI 在线分析接口

## 🚀 快速开始

### 安装

```bash
cd docker_optimizer
pip install -r requirements.txt
```

### CLI 使用

```bash
# 分析 Dockerfile（终端输出）
python cli.py analyze Dockerfile

# 生成 Markdown 报告
python cli.py analyze Dockerfile -f markdown -o report.md

# 生成 HTML 报告
python cli.py analyze Dockerfile -f html -o report.html

# 生成优化后的 Dockerfile
python cli.py analyze Dockerfile --rewrite -o Dockerfile.optimized

# 启动 API 服务
python cli.py serve --port 8000
```

### API 使用

```bash
# 启动服务
python cli.py serve

# 分析 Dockerfile
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"dockerfile_content": "FROM python:3.11\nCOPY . .\nRUN pip install .", "format": "markdown"}'

# 上传文件分析
curl -X POST http://localhost:8000/analyze/file \
  -F "file=@Dockerfile"
```

## 🔍 检测规则

| 规则 | 严重度 | 说明 |
|------|--------|------|
| 大基础镜像 | ⚠️ WARNING | 检测可替换的精简镜像 |
| 未清理缓存 | ⚠️ WARNING | apt/pip 缓存未清理 |
| 未多阶段构建 | ⚠️ WARNING | 检测编译工具但无多阶段构建 |
| 无 .dockerignore | 🔵 INFO | 缺少 .dockerignore 文件 |
| RUN 未合并 | 🔵 INFO | 多个连续 RUN 指令未合并 |
| 使用 latest 标签 | ⚠️ WARNING | 基础镜像使用 latest 标签 |
| 以 root 运行 | 🔵 INFO | 未指定非 root 用户 |
| pip 未禁用缓存 | 🔵 INFO | pip install 未使用 --no-cache-dir |

## 📊 优化示例

### 优化前

```dockerfile
FROM python:3.11
WORKDIR /app
COPY . .
RUN apt-get update
RUN apt-get install -y curl
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["python", "app.py"]
```

### 优化后

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /app .
RUN useradd -m appuser
USER appuser
EXPOSE 8000
CMD ["python", "app.py"]
```

**预计节省**: 60-80% 基础镜像体积

## 🛠 技术栈

- **Python** - Dockerfile 解析和逻辑
- **FastAPI** - Web API 服务
- **Rich** - 终端美化输出
- **PyYAML** - 配置文件解析
- **Pydantic** - 数据验证

## 📁 项目结构

```
docker_optimizer/
├── models.py          # 数据模型
├── image_analyzer.py  # Dockerfile 分析器
├── optimizer.py       # 优化建议生成器
├── reporter.py        # 报告生成器
├── api.py             # FastAPI 服务
├── cli.py             # CLI 入口
├── config.yaml        # 配置文件
├── requirements.txt   # 依赖
├── examples/          # 示例 Dockerfile
│   ├── bad.Dockerfile
│   └── good.Dockerfile
└── README.md
```

