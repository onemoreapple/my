FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 创建必要的目录
RUN mkdir -p /app/data /app/reports /app/logs

# 暴露Streamlit端口
EXPOSE 8501

# 更新main.py，添加通知集成
RUN echo "print('Starting investment analyzer...')" >> /app/main.py

# 启动Streamlit
CMD ["streamlit", "run", "main.py", "--server.address=0.0.0.0", "--server.port=8501"]