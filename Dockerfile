FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     && rm -rf /var/lib/apt/lists/*

# 复制项目文件
COPY requirements.txt .
COPY src/ src/

# 创建配置目录
RUN mkdir -p config

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 设置环境变量
ENV PYTHONPATH=/app

# 暴露端口
EXPOSE 7860

# 启动命令
CMD ["python", "src/main.py"] 