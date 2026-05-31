# 优化后的 Dockerfile 示例
# 使用多阶段构建，精简镜像

# === 构建阶段 ===
FROM python:3.12-slim AS builder

WORKDIR /app

# 先复制依赖文件，利用缓存
COPY requirements.txt .

# 安装依赖（禁用缓存）
RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

# === 运行阶段 ===
FROM python:3.12-slim

WORKDIR /app

# 从构建阶段复制已安装的依赖
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /app .

# 创建非 root 用户
RUN useradd -m -r appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 使用 gunicorn 启动
CMD ["python", "-m", "gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
