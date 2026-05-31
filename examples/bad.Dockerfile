# 未优化的 Dockerfile 示例
FROM python:3.11

WORKDIR /app

# 复制所有文件（包括 .git、node_modules 等）
COPY . .

# 更新包管理器并安装依赖
RUN apt-get update
RUN apt-get install -y curl wget git
RUN apt-get install -y build-essential

# 安装 Python 依赖
RUN pip install -r requirements.txt
RUN pip install gunicorn

# 暴露端口
EXPOSE 8000

# 启动应用
CMD ["python", "app.py"]
