from flask import Flask, request, send_file, jsonify
from werkzeug.utils import secure_filename
from pdf2docx import Converter
import os
import tempfile
import time
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
ALLOWED_EXTENSIONS = {'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/convert", methods=["POST"])
def convert():
    if "file" not in request.files:
        return jsonify({"error": "请上传文件"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "请选择文件"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "文件类型不允许，仅支持PDF文件"}), 400

    MAX_FILESIZE = 10 * 1024 * 1024  # 10MB
    if file.content_length > MAX_FILESIZE:
        return jsonify({"error": "文件大小超过最大限制 (10MB)"}), 400

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            filename = secure_filename(file.filename)
            filename = f"{filename}_{secrets.token_hex(8)}"  
            temp_file_path = os.path.join(temp_dir, filename)
            file.save(temp_file_path)

            output_path = os.path.join(temp_dir, "converted.docx")
            cv = Converter(temp_file_path)
            start_time = time.time()
            cv.convert(output_path, start=0, end=None)
            cv.close()
            end_time = time.time()

            if not os.path.exists(output_path):
                return jsonify({"error": "转换失败"}), 500

            return send_file(output_path, as_attachment=True)
    except Exception as e:
        return jsonify({"error": "转换失败"}), 500

if __name__ == "__main__":
    app.run(debug=False)
