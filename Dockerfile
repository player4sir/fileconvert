# 使用 Python 官方的 slim 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录下的所有文件复制到容器的 /app 目录中
COPY . /app

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口号（如果你的 Flask 应用监听了其他端口，请修改此处）
EXPOSE 5000

# 设置环境变量
ENV FLASK_APP=app.py

# 启动 Flask 应用
CMD ["flask", "run", "--host=0.0.0.0"]