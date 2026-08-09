FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 创建需要的目录
RUN mkdir -p logs

# 复制项目文件到容器中
COPY . /app

# 安装项目依赖
RUN pip install --no-cache-dir ".[server]" && pip cache purge

# 设置环境变量
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=7777
ENV HOST=0.0.0.0

# 暴露端口（默认7777，可通过运行时环境变量修改）
EXPOSE 7777

# 运行项目
CMD ["sh", "-c", "exec gunicorn --bind ${HOST:-0.0.0.0}:${PORT:-7777} --threads 4 --access-logfile - --error-logfile - app:app"]
