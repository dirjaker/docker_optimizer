# Docker Image Optimizer — 开发指南

本文档面向开发者，介绍如何搭建开发环境、理解代码结构、运行测试和参与贡献。

---

## 1. 环境搭建

### 1.1 前置条件

- Python 3.11+
- Conda（推荐）或 venv
- Docker Engine（仅用于测试，非必需）

### 1.2 安装步骤

```bash
# 克隆仓库
git clone https://github.com/dirjaker/docker_optimizer.git
cd docker_optimizer

# 创建并激活虚拟环境
conda create -n docker_optimizer python=3.12 -y
conda activate docker_optimizer

# 安装依赖
pip install -r requirements.txt
```

### 1.3 依赖说明

| 包名 | 用途 | 是否核心 |
|------|------|---------|
| `fastapi>=0.104.0` | REST API 框架 | 是 |
| `uvicorn>=0.24.0` | ASGI 服务器 | 是 |
| `python-multipart>=0.0.6` | 文件上传支持 | 是 |
| `pydantic>=2.0.0` | 数据校验和序列化 | 是 |
| `pyyaml>=6.0` | YAML 配置解析 | 是 |
| `rich>=13.0.0` | 终端美化输出 | 否（自动降级） |
| `py2app>=0.28.0` | macOS 打包 | 否（仅 macOS） |

---

## 2. 运行方式

### 2.1 CLI 分析

```bash
# 终端输出分析
python cli.py analyze examples/bad.Dockerfile

# Markdown 报告
python cli.py analyze examples/bad.Dockerfile -f markdown -o report.md

# HTML 报告
python cli.py analyze examples/bad.Dockerfile -f html -o report.html

# 分析并重写
python cli.py analyze examples/bad.Dockerfile -r -o Dockerfile.optimized
```

### 2.2 REST API 服务

```bash
# 默认端口 8000
python cli.py serve

# 自定义端口
python cli.py serve --host 127.0.0.1 --port 9000
```

启动后访问 `http://localhost:8000/docs` 查看 OpenAPI 文档。

### 2.3 Web Dashboard

```bash
cd src/web
python app.py
# 访问 http://localhost:8080
```

### 2.4 macOS GUI

```bash
python src/macos/app.py
```

---

## 3. 代码结构

```
docker_optimizer/
├── models.py                # 数据模型（全部 dataclass + Enum）
│   ├── Severity             # 严重度枚举
│   ├── IssueType            # 问题类型枚举（10 种）
│   ├── DockerInstruction    # Dockerfile 指令
│   ├── LayerInfo            # 镜像层信息
│   ├── Issue                # 检测到的问题
│   ├── OptimizationSuggestion # 优化建议
│   └── AnalysisResult       # 分析结果（全链路数据载体）
│
├── image_analyzer.py        # 分析引擎（核心模块）
│   ├── SLIM_ALTERNATIVES    # 精简镜像映射表
│   ├── IMAGE_SIZE_ESTIMATES # 镜像大小估算表
│   ├── parse_dockerfile()   # 指令解析（含续行处理）
│   ├── extract_base_image() # 基础镜像提取
│   ├── detect_multistage()  # 多阶段构建检测
│   ├── build_layers()       # 层信息构建
│   ├── detect_issues()      # 问题检测（8 条规则）
│   └── analyze_dockerfile() # 主入口
│
├── optimizer.py             # 优化引擎
│   ├── generate_suggestions() # 生成优化建议（7 类）
│   ├── rewrite_dockerfile()   # 重写 Dockerfile
│   └── _flush_run_buffer()    # RUN 合并辅助
│
├── reporter.py              # 报告生成器
│   ├── print_terminal()     # Rich 终端输出
│   ├── to_markdown()        # Markdown 报告
│   └── to_html()            # HTML 报告
│
├── api.py                   # FastAPI REST API
│   ├── POST /analyze        # 文本分析
│   ├── POST /analyze/file   # 文件上传分析
│   └── GET /health          # 健康检查
│
├── cli.py                   # CLI 入口
│   ├── analyze 子命令       # Dockerfile 分析
│   └── serve 子命令         # API 服务
│
├── config.yaml              # 可配置规则和参数
│
└── src/
    ├── web/
    │   ├── app.py           # Web Dashboard（FastAPI + 静态页面）
    │   └── static/
    │       └── index.html   # 前端页面（单文件，暗色主题）
    └── macos/
        └── app.py           # macOS GUI（tkinter）
```

### 3.1 数据流

```
Dockerfile 文件
    │
    ▼
parse_dockerfile()  →  list[DockerInstruction]
    │
    ▼
analyze_dockerfile()  →  AnalysisResult
    │                     ├── base_image
    │                     ├── layers
    │                     ├── issues
    │                     ├── estimated_size_mb
    │                     └── has_multistage
    ▼
generate_suggestions()  →  list[OptimizationSuggestion]
    │
    ▼
rewrite_dockerfile()  →  str (优化后的 Dockerfile)
    │
    ▼
reporter  →  Terminal / Markdown / HTML
```

---

## 4. 添加新检测规则

### 4.1 步骤

1. 在 `models.py` 的 `IssueType` 枚举中新增类型
2. 在 `image_analyzer.py` 的 `detect_issues()` 函数中添加检测逻辑
3. 在 `optimizer.py` 的 `generate_suggestions()` 中添加对应建议
4. 在 `config.yaml` 的 `analysis.rules` 中添加开关
5. 更新文档

### 4.2 示例：添加"未固定 apt 包版本"检测

```python
# 1. models.py - 新增枚举
class IssueType(str, Enum):
    # ... 已有类型
    APT_NO_VERSION_PIN = "apt_no_version_pin"

# 2. image_analyzer.py - detect_issues() 中添加
for inst in instructions:
    if inst.instruction == "RUN" and "apt-get install" in inst.arguments:
        if "=" not in inst.arguments.split("install")[1]:
            issues.append(Issue(
                issue_type=IssueType.APT_NO_VERSION_PIN,
                severity=Severity.INFO,
                title="apt 包未固定版本",
                description="安装的 apt 包未指定版本号，可能导致构建不可重复。",
                line_number=inst.line_number,
                suggestion="使用 `apt-get install -y curl=7.88.1-9` 固定版本。",
            ))

# 3. config.yaml - 添加开关
analysis:
  rules:
    apt_no_version_pin: true
```

---

## 5. 添加新镜像映射

在 `image_analyzer.py` 中添加两个映射：

```python
# 精简镜像映射
SLIM_ALTERNATIVES["rust:1.75"] = "rust:1.75-slim"

# 大小估算
IMAGE_SIZE_ESTIMATES["rust:1.75"] = 1600
IMAGE_SIZE_ESTIMATES["rust:1.75-slim"] = 200
```

---

## 6. 代码规范

### 6.1 风格

- 遵循 PEP 8
- 使用类型注解（type hints）
- 函数和类使用 docstring
- 字符串使用双引号
- 使用 `dataclass` 定义数据模型（而非手动 `__init__`）

### 6.2 命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 模块文件 | snake_case | `image_analyzer.py` |
| 类名 | PascalCase | `AnalysisResult` |
| 函数名 | snake_case | `detect_issues()` |
| 常量 | UPPER_SNAKE_CASE | `SLIM_ALTERNATIVES` |
| 枚举值 | UPPER_SNAKE_CASE | `LARGE_BASE_IMAGE` |

---

## 7. 测试建议

### 7.1 使用示例文件测试

```bash
# 测试坏的 Dockerfile（应检测到多个问题）
python cli.py analyze examples/bad.Dockerfile

# 测试好的 Dockerfile（应无问题或极少问题）
python cli.py analyze examples/good.Dockerfile
```

### 7.2 手动构造测试用例

```bash
# 临时创建测试 Dockerfile
cat > /tmp/test.Dockerfile << 'EOF'
FROM ubuntu:latest
RUN apt-get update
RUN apt-get install -y python3
RUN pip install flask
COPY . /app
CMD ["python3", "/app/main.py"]
EOF

python cli.py analyze /tmp/test.Dockerfile
```

---

## 8. 贡献流程

1. Fork 仓库
2. 从 `dev` 分支创建特性分支：`git checkout -b feat/xxx dev`
3. 提交变更：`git commit -m "feat: 添加 xxx 功能"`
4. 推送到 Fork：`git push origin feat/xxx`
5. 创建 Pull Request 到 `dev` 分支

### 提交信息规范

使用 Conventional Commits 格式：

| 前缀 | 说明 | 示例 |
|------|------|------|
| `feat:` | 新功能 | `feat: 添加 Python 包版本检测` |
| `fix:` | Bug 修复 | `fix: 修复续行解析错误` |
| `docs:` | 文档更新 | `docs: 更新技术文档` |
| `refactor:` | 重构 | `refactor: 统一 API 分析逻辑` |
| `style:` | 代码风格 | `style: 格式化代码` |
| `test:` | 测试 | `test: 添加解析器单元测试` |
