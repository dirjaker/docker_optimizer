# Changelog

本文件记录 Docker Image Optimizer 的所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [未发布]

### 计划
- CI/CD 集成
- 多镜像批量分析
- 可视化层大小饼图
- Docker 插件支持

---

## [1.0.0] - 2026-06-21

### 新增
- **Dockerfile 分析引擎** (`image_analyzer.py`)
  - 正则解析 Dockerfile 指令（含 `\` 续行处理）
  - 精简镜像映射表（`SLIM_ALTERNATIVES`，覆盖 16+ 常见镜像）
  - 镜像大小估算表（`IMAGE_SIZE_ESTIMATES`，覆盖 30+ 镜像）
  - 8 种问题检测规则：
    - 大基础镜像检测
    - latest 标签检测
    - apt 缓存未清理检测
    - pip 缓存未禁用检测
    - 未使用多阶段构建检测
    - 无 .dockerignore 检测
    - RUN 指令未合并检测
    - 以 root 用户运行检测

- **优化建议引擎** (`optimizer.py`)
  - 7 类优化建议，按优先级排序
  - 每条建议含优化前后代码对比和预估节省量
  - Dockerfile 自动重写功能（替换基础镜像、合并 RUN、添加 .dockerignore 提示）

- **报告生成器** (`reporter.py`)
  - 终端输出（Rich 美化，自动降级为纯文本）
  - Markdown 报告生成
  - HTML 报告生成

- **REST API 服务** (`api.py`)
  - `POST /analyze` — Dockerfile 内容分析
  - `POST /analyze/file` — 文件上传分析
  - `GET /` — 服务信息
  - `GET /health` — 健康检查
  - 支持 json/markdown/html 三种输出格式
  - 自动生成 OpenAPI 文档

- **CLI 工具** (`cli.py`)
  - `analyze` 子命令：分析 Dockerfile，支持多格式输出和重写
  - `serve` 子命令：启动 API 服务

- **Web Dashboard** (`src/web/`)
  - 暗色主题 Web 界面
  - 统计卡片、问题列表、优化建议可视化
  - 优化后 Dockerfile 预览和报告切换

- **macOS GUI** (`src/macos/`)
  - tkinter 桌面客户端
  - Dockerfile 输入、一键分析、结果展示
  - 内置 Web 服务启停控制

- **数据模型** (`models.py`)
  - `Severity` 枚举（INFO / WARNING / CRITICAL）
  - `IssueType` 枚举（10 种问题类型）
  - `DockerInstruction` — Dockerfile 指令
  - `LayerInfo` — 镜像层信息
  - `Issue` — 检测到的问题（含行号定位）
  - `OptimizationSuggestion` — 优化建议
  - `AnalysisResult` — 分析结果

- **配置系统** (`config.yaml`)
  - 检测规则开关
  - 层数/大小警告阈值
  - 输出格式配置
  - API 服务配置
  - 自定义精简镜像映射

- **示例文件**
  - `examples/bad.Dockerfile` — 未优化示例
  - `examples/good.Dockerfile` — 优化后示例

- **项目文档**
  - README.md（功能介绍、快速开始、使用说明）
  - 技术文档（系统架构、核心模块设计、面试 FAQ）
  - 开发指南（环境搭建、代码规范、贡献流程）
  - 代码审查报告（安全漏洞、代码质量分析）

### 安全修复
- CORS 限制为本地来源（默认 `localhost,127.0.0.1`）
- Web Dashboard 默认绑定 `0.0.0.0:8080`
- API 中的 `exec`/`eval` 添加沙箱保护

### 已知问题
- API 服务默认绑定 `0.0.0.0`（生产环境需修改为 `127.0.0.1`）
- CLI 的 `serve` 子命令默认开启 `reload=True`（生产环境需关闭）
- HTML 报告存在潜在 XSS 风险（需对嵌入内容做 HTML 转义）
- `api.py` 和 `src/web/app.py` 的分析端点存在代码重复
