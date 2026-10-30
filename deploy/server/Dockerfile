FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIPE_GEN=/app/assets \
    PIPE_BASE=/app/assets/template.docx \
    BRIDGE_HOST=0.0.0.0 \
    BRIDGE_PORT=8732 \
    PROJECT_KEEP_DAYS=7

# pillow：图片规整；pillow-heif：让服务器也能吃 iPhone 的 HEIC（Windows 上走的是系统 WIC）
RUN pip install --no-cache-dir pillow pillow-heif

WORKDIR /app
COPY app/ /app/

# 生成物落在这里（compose 里挂成卷，方便备份/清理）
RUN mkdir -p /app/pipeline/projects

EXPOSE 8732
CMD ["python", "/app/pipeline/bridge.py", "--host", "0.0.0.0", "--port", "8732"]
