
from flask import Flask,request, send_file，jsonify
from pdf2docx import Converter
from docx2pdf import convert
import os
import tempfile
import img2pdf
from werkzeug.utils import secure_filename


app = Flask(__name__)


# pdf转换为word
@app.route('/pdf_to_word', methods=['POST'])
def convert_pdf_to_word():
    # 假设前端通过表单上传了PDF文件
    pdf_file = request.files['pdf']  
    # 创建临时文件保存PDF文件
    pdf_temp = tempfile.NamedTemporaryFile(delete=False)
    pdf_file.save(pdf_temp.name)
    word_temp = None
    cv = None
    try:
        # 创建临时文件保存Word文档
        word_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx', mode='w+b')       
        # 使用pdf2docx库转换PDF为Word
        cv = Converter(pdf_temp.name)
        cv.convert(word_temp.name, start=0, end=None)    
        # 返回Word文档
        word_temp.seek(0)
        return send_file(word_temp.name, as_attachment=True, download_name='converted.docx')
    except Exception as e:
         response_message = str(e)
         app.logger.error(f"Conversion failed: {response_message}")
         return jsonify({'error': response_message}), 500
    finally:
        # 删除临时的PDF和Word文件
        if cv:
            cv.close()
        if pdf_temp:
            os.unlink(pdf_temp.name)
        if word_temp:
            os.unlink(word_temp.name)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/image_to_pdf', methods=['POST'])
def convert_images_to_pdf():
    # 检查是否有文件被上传
    if 'images' not in request.files:
        return "没有文件部分", 400
    
    files = request.files.getlist('images')
    image_paths = []
    
    for file in files:
        if file and allowed_file(file.filename):
            # 保存图片到临时文件
            filename = secure_filename(file.filename)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png', mode='w+b')
            file.save(temp_file.name)
            image_paths.append(temp_file.name)
        else:
            return "文件类型不允许", 400
    
    try:
        # 创建临时文件保存PDF文档
        pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w+b')    
        # 获取用户设置的页面方向和边距
        orientation = request.form.get('orientation', 'portrait')  # 默认为纵向
        margin = int(request.form.get('margin', 8))  # 默认边距为0    
        # 设置PDF的布局
        a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))  # A4大小，单位转换为点
        layout_fun = img2pdf.get_layout_fun(pagesize=a4inpt)       
        if orientation == 'landscape':
            # 如果用户选择横向，交换页面尺寸的宽高
            a4inpt = (a4inpt[1], a4inpt[0])  
        # 使用img2pdf库将所有图片合并为一个PDF
        with open(pdf_temp.name, "wb") as f:
            f.write(img2pdf.convert(image_paths, layout_fun=layout_fun))    
        # 返回PDF文档
        pdf_temp.seek(0)
        return send_file(pdf_temp.name, as_attachment=True, download_name='converted.pdf')
    finally:
        # 删除临时的图片文件和PDF文件
        for path in image_paths:
            os.unlink(path)
        os.unlink(pdf_temp.name)
        
@app.route('/word_to_pdf', methods=['POST'])
def convert_word_to_pdf():
    # Assume the front end uploads a Word file through a form
    word_file = request.files['word']
    # Create a temporary file to save the Word file
    word_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx', mode='w+b')
    word_file.save(word_temp.name)
    pdf_temp = None
    
    try:
        # Create a temporary file to save the PDF document
        pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf', mode='w+b')
        # Use docx2pdf to convert Word to PDF
        convert(word_temp.name, pdf_temp.name)
        # Return the PDF document
        pdf_temp.seek(0)
        return send_file(pdf_temp.name, as_attachment=True, download_name='converted.pdf')
    except Exception as e:
        response_message = str(e)
        app.logger.error(f"Conversion failed: {response_message}")
        return jsonify({'error': response_message}), 500
    finally:
        # Delete the temporary Word and PDF files
        if word_temp:
            os.unlink(word_temp.name)
        if pdf_temp:
            os.unlink(pdf_temp.name)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
