# 第一阶段：构建阶段
FROM python:3.8-slim-buster as builder

# 设置工作目录
WORKDIR /app

# 将当前目录内容复制到容器的/app目录下
COPY . /app

# 安装在requirements.txt中列出的Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行阶段
FROM python:3.8-slim-buster

# 设置工作目录
WORKDIR /app

# 从构建阶段复制构建产物到运行阶段
COPY --from=builder /app/requirements.txt /app/requirements.txt
COPY --from=builder /app/app.py /app/app.py
COPY --from=builder /app/static /app/static
COPY --from=builder /app/templates /app/templates

# 安装在requirements.txt中列出的Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露容器的5000端口
EXPOSE 5000

# 运行Flask应用
CMD ["python", "app.py"]
