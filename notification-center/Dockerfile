FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    default-mysql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制源代码
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/
COPY init_db.py .

# 创建日志目录
RUN mkdir -p /app/logs /app/config

# 暴露端口
EXPOSE 8000

# 启动脚本
CMD ["sh", "-c", "python init_db.py && uvicorn src.main:app --host 0.0.0.0 --port 8000"]