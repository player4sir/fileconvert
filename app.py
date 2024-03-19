from flask import Flask, request, send_file
from pdf2docx import Converter
import os
import tempfile

app = Flask(__name__)

@app.route('/convert', methods=['POST'])
def convert_pdf_to_word():
    # 假设前端通过表单上传了PDF文件
    pdf_file = request.files['pdf']
    # 创建临时文件保存PDF
    pdf_temp = tempfile.NamedTemporaryFile(delete=False)
    pdf_file.save(pdf_temp.name)
    
    # 创建临时文件保存Word文档
    word_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    
    # 使用pdf2docx库转换PDF为Word
    cv = Converter(pdf_temp.name)
    cv.convert(word_temp.name, start=0, end=None)
    cv.close()
    
    # 删除临时的PDF文件
    os.unlink(pdf_temp.name)
    
    # 返回Word文档
    word_temp.seek(0)
    return send_file(word_temp.name, as_attachment=True, attachment_filename='converted.docx')

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
