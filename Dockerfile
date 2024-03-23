FROM tiangolo/uwsgi-nginx-flask:python3.8

# 设置工作目录
WORKDIR /app

# 复制应用文件
COPY . /app

# 安装Tesseract OCR及其依赖项
RUN apt-get update && \
    apt-get install -y tesseract-ocr libtesseract-dev

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露端口
EXPOSE 5000

# 设置Flask应用的环境变量
ENV FLASK_APP=app.py

# 启动Flask应用
CMD ["flask", "run", "--host=0.0.0.0"]
