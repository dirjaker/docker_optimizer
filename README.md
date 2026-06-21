<div align="center">

<img src="assets/banner.svg" width="100%" alt="Docker 镜像优化器">

<br>

### ⚡ Docker 镜像优化器

[![Stars](https://img.shields.io/github/stars/dirjaker/docker_optimizer?style=flat-square&label=Stars&color=FFD700)](https://github.com/dirjaker/docker_optimizer/stargazers)
[![Forks](https://img.shields.io/github/forks/dirjaker/docker_optimizer?style=flat-square&label=Forks&color=4A90D9)](https://github.com/dirjaker/docker_optimizer/network/members)
[![Contributors](https://img.shields.io/github/contributors/dirjaker/docker_optimizer?style=flat-square&label=Contributors&color=8B4513)](https://github.com/dirjaker/docker_optimizer/graphs/contributors)
[![License](https://img.shields.io/github/license/dirjaker/docker_optimizer?style=flat-square&label=License&color=20B2AA)](https://github.com/dirjaker/docker_optimizer/blob/dev/LICENSE)

**一款基于规则引擎的 Dockerfile 静态分析工具，自动检测 10+ 种优化问题并生成精简后的 Dockerfile。**

</div>

---

## ✨ 功能特性

| 功能 | 描述 |
|------|------|
| 🔍 **层分析** | 逐层解析镜像构建过程，定位体积瓶颈 |
| ⚠️ **问题检测** | 自动检测 10+ 种常见 Dockerfile 问题和反模式 |
| 💡 **优化建议** | 生成针对性的优化建议，附带优化前后对比和预估节省量 |
| 📝 **Dockerfile 重写** | 自动优化 Dockerfile，替换精简镜像、合并 RUN 指令 |
| 🔒 **安全检测** | 检测 root 用户运行、latest 标签等安全隐患 |
| 📊 **多格式报告** | 支持终端（Rich 美化）、Markdown、HTML 三种输出格式 |
| 🌐 **Web Dashboard** | 内置 Web 界面，支持在线粘贴分析和可视化结果展示 |
| 🖥️ **macOS GUI** | 基于 tkinter 的桌面客户端，一键分析 Dockerfile |

## 🚀 快速开始

### 安装

```bash
# 克隆项目
git clone https://github.com/dirjaker/docker_optimizer.git
cd docker_optimizer

# 创建虚拟环境
conda create -n docker_optimizer python=3.12 -y
conda activate docker_optimizer

# 安装依赖
pip install -r requirements.txt
```

### CLI 使用

```bash
# 分析 Dockerfile（终端输出）
python cli.py analyze Dockerfile

# 生成 Markdown 报告
python cli.py analyze Dockerfile --format markdown --output report.md

# 生成 HTML 报告
python cli.py analyze Dockerfile --format html --output report.html

# 分析并自动重写优化
python cli.py analyze Dockerfile --rewrite --output Dockerfile.optimized

# 启动 API 服务
python cli.py serve --host 0.0.0.0 --port 8000
```

### API 使用

```bash
# 启动 API 服务
python cli.py serve --port 8000

# 通过 curl 分析 Dockerfile
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"dockerfile_content": "FROM python:3.11\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt", "format": "markdown"}'

# 上传文件分析
curl -X POST http://localhost:8000/analyze/file \
  -F "file=@Dockerfile"
```

### Web Dashboard

```bash
# 启动 Web Dashboard（默认端口 8080）
cd src/web && python app.py

# 浏览器访问 http://localhost:8080
```

## 📋 检测规则

| 规则 | 检测逻辑 | 严重度 |
|------|----------|--------|
| 大基础镜像 | 匹配精简镜像映射表（30+ 常见镜像） | 🟡 WARNING |
| latest 标签 | 使用 `latest` 或未指定标签 | 🟡 WARNING |
| apt 缓存未清理 | `apt-get install` 后无 `rm -rf /var/lib/apt/lists` | 🟡 WARNING |
| pip 缓存未禁用 | `pip install` 缺少 `--no-cache-dir` | 🔵 INFO |
| 未使用多阶段构建 | 检测到编译工具（gcc/make）但未多阶段分离 | 🟡 WARNING |
| 无 .dockerignore | 同目录下缺少 `.dockerignore` 文件 | 🔵 INFO |
| RUN 未合并 | 3+ 个连续 RUN 指令未合并为单条 | 🔵 INFO |
| 以 root 运行 | 未指定 USER 指令 | 🔵 INFO |

## 🛠️ 技术栈

| 层级 | 技术 |
|------|------|
| **语言** | Python 3.11+ |
| **数据模型** | dataclass + Enum |
| **Web 框架** | FastAPI + Uvicorn |
| **数据校验** | Pydantic |
| **终端美化** | Rich |
| **CLI** | argparse |
| **配置管理** | PyYAML |
| **Dockerfile 解析** | 正则表达式（re 标准库） |
| **输出格式** | Terminal / Markdown / HTML |

## 📁 项目结构

```
docker_optimizer/
├── cli.py                 # CLI 入口（analyze / serve 子命令）
├── api.py                 # FastAPI REST API 服务
├── image_analyzer.py      # Dockerfile 解析 + 问题检测引擎
├── optimizer.py           # 优化建议生成 + Dockerfile 重写
├── reporter.py            # 多格式报告生成器（Terminal/Markdown/HTML）
├── models.py              # 数据模型定义（dataclass + Enum）
├── config.yaml            # 可配置的规则开关和参数
├── requirements.txt       # Python 依赖
├── assets/
│   └── banner.svg         # 项目 Banner
├── docs/
│   ├── 技术文档.md         # 中文技术设计文档
│   ├── DEVELOPMENT.md     # 开发指南
│   └── CHANGELOG.md       # 变更日志
├── examples/
│   ├── bad.Dockerfile     # 未优化示例
│   └── good.Dockerfile    # 优化后示例
└── src/
    ├── web/
    │   ├── app.py         # Web Dashboard 后端
    │   └── static/
    │       └── index.html # Web Dashboard 前端
    └── macos/
        └── app.py         # macOS GUI 客户端
```

## 📝 开发路线

- [x] 镜像层分析器
- [x] 问题检测引擎（10 种规则）
- [x] 优化建议生成
- [x] Dockerfile 自动重写
- [x] CLI 工具
- [x] REST API 服务
- [x] Web Dashboard
- [x] macOS 桌面客户端
- [ ] CI/CD 集成
- [ ] 多镜像批量分析
- [ ] 可视化层大小饼图
- [ ] Docker 插件支持

## 📚 文档

- [技术设计文档](docs/技术文档.md) — 系统架构、核心模块设计、面试 FAQ
- [开发指南](docs/DEVELOPMENT.md) — 环境搭建、代码规范、贡献流程
- [变更日志](docs/CHANGELOG.md) — 版本变更记录
- [代码审查报告](REVIEW.md) — 安全漏洞与代码质量分析

## 📄 许可证

[MIT License](LICENSE)

---

<div align="center">

🔗 **GitHub**: [dirjaker/docker_optimizer](https://github.com/dirjaker/docker_optimizer)

⭐ 如果这个项目对你有帮助，请给一个 Star 支持一下！

</div>
