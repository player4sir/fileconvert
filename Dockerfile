# 使用多阶段构建来减小镜像大小
# 第一阶段：构建阶段
FROM tiangolo/uwsgi-nginx-flask:python3.8 as builder

# 设置工作目录
WORKDIR /app

# 安装Tesseract OCR及其依赖项
RUN apt-get update && \
    apt-get install -y tesseract-ocr libtesseract-dev libgl1-mesa-glx && \
    # 清理apt缓存以减小镜像大小
    rm -rf /var/lib/apt/lists/*

# 复制requirements.txt并安装Python依赖
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# 第二阶段：运行阶段
FROM tiangolo/uwsgi-nginx-flask:python3.8

# 从构建阶段复制已安装的依赖项
COPY --from=builder /usr/local /usr/local
COPY --from=builder /app /app

# 设置工作目录
WORKDIR /app

# 安装必要的库和Tesseract
RUN apt-get update && \
    apt-get install -y libgl1-mesa-glx tesseract-ocr && \
    rm -rf /var/lib/apt/lists/*

# 复制应用文件
COPY . /app

# 暴露端口
EXPOSE 5000

# 设置Flask应用的环境变量
ENV FLASK_APP=app.py
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
# 安装opencv-python-headless
RUN pip install opencv-python-headless

# 使用Gunicorn代替uWSGI启动Flask应用
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
