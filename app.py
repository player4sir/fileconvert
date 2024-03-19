from flask import Flask, request, jsonify, url_for, send_file
from pdf2docx import Converter
import os
import logging

app = Flask(__name__)

# Use environment variable for upload folder
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/app/uploads")

# Allowed file extensions
ALLOWED_EXTENSIONS = {"pdf"}

# Configure logging
logging.basicConfig(filename="app.log", level=logging.INFO)


def allowed_file(filename):
    """Checks if file extension is allowed"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/ptw", methods=["POST"])
def convert_pdf_to_word():
    """API endpoint to convert PDF to Word document"""

    # Check if file is uploaded
    if "file" not in request.files:
        logging.warning("No PDF file uploaded")
        return jsonify({"error": "未上传 PDF 文件"}), 400

    # Get uploaded file
    pdf_file = request.files["file"]

    # Check file extension
    if not allowed_file(pdf_file.filename):
        logging.warning("Unsupported file type uploaded")
        return jsonify({"error": "不支持的文件类型"}), 400

    # Save file to local storage
    filename = pdf_file.filename
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    pdf_file.save(filepath)

    try:
        # Convert PDF to Word
        converter = Converter(filepath)
        docx_filepath = os.path.splitext(filepath)[0] + ".docx"
        converter.convert(docx_filepath)

        # Generate download URL
        download_url = url_for("download_file", filename=os.path.basename(docx_filepath))

        logging.info(f"Successfully converted {filename} to {docx_filepath}")
        return jsonify({"download_url": download_url})

    except Exception as e:
        logging.error(f"Conversion failed: {str(e)}")
        return jsonify({"error": f"转换失败：{str(e)}"}), 500

    finally:
        # Close converter
        converter.close()

        # You can choose to keep the uploaded file for logging or debugging
        # and implement a separate process to clean up old files.
        os.remove(filepath)


# New route for downloading the converted file
@app.route("/download/<filename>")
def download_file(filename):
    """Downloads the converted Word document"""
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        logging.error(f"File not found: {filename}")
        return jsonify({"error": "文件未找到"}), 404


if __name__ == "__main__":
    # Create upload folder if it doesn't exist
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    app.run(host='0.0.0.0',port=5000,debug=False)