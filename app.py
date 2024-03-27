import cv2
from flask import Flask, jsonify, request, send_file
import pandas as pd
from pdf2docx import Converter
import os
import tempfile

import pdfplumber
from pptx import Presentation
from pptx.util import Inches, Pt
from io import BytesIO
from PIL import Image
import img2pdf
from werkzeug.utils import secure_filename
import openpyxl
from img2table.document import Image as Img
from img2table.ocr import TesseractOCR


app = Flask(__name__)

tessdata_prefix = os.environ.get('TESSDATA_PREFIX')

# pdf转换为word
@app.route('/pdf_to_word', methods=['POST'])
def convert_pdf_to_word():
    # 假设前端通过表单上传了PDF文件
    pdf_file = request.files['pdf']
    # 创建临时文件保存PDF文件
    pdf_temp = tempfile.NamedTemporaryFile(delete=False)
    pdf_file.save(pdf_temp.name)
    
    try:
        # 创建临时文件保存Word文档
        word_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx', mode='w+b')
        
        # 使用pdf2docx库转换PDF为Word
        cv = Converter(pdf_temp.name)
        cv.convert(word_temp.name, start=0, end=None)
        cv.close()
        
        # 返回Word文档
        word_temp.seek(0)
        return send_file(word_temp.name, as_attachment=True, download_name='converted.docx')
    finally:
        # 删除临时的PDF和Word文件
        os.unlink(pdf_temp.name)
        os.unlink(word_temp.name)

@app.route('/image_to_pdf', methods=['POST'])
def convert_images_to_pdf():
    # 允许的图片文件扩展名
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
    def allowed_file(filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
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
        
        # 使用img2pdf库将所有图片合并为一个PDF
        with open(pdf_temp.name, "wb") as f:
            f.write(img2pdf.convert(image_paths))     
        # 返回PDF文档
        pdf_temp.seek(0)
        return send_file(pdf_temp.name, as_attachment=True, download_name='converted.pdf')
    finally:
        # 删除临时的图片文件和PDF文件
        for path in image_paths:
            os.unlink(path)
        os.unlink(pdf_temp.name)

@app.route('/pdf_to_pptx', methods=['POST'])
def convert_pdf_to_pptx():
    # 假设前端通过表单上传了PDF文件
    pdf_file = request.files['pdf']
    # 创建临时文件保存PDF
    pdf_temp = tempfile.NamedTemporaryFile(delete=False)
    pdf_file.save(pdf_temp.name)   
    pptx_temp = None  # 初始化pptx_temp变量
    try:
        # 创建PPT对象
        ppt = Presentation()   
        # 使用pdfplumber打开PDF文件
        with pdfplumber.open(pdf_temp.name) as pdf:
            # 遍历PDF中的每一页
            for page in pdf.pages:
                # 检查页面是否包含文本
                text = page.extract_text()
                if text:
                    # 为文本创建新的幻灯片
                    slide = ppt.slides.add_slide(ppt.slide_layouts[5])
                    txBox = slide.shapes.add_textbox(Inches(1), Inches(1), Inches(8), Inches(5))
                    tf = txBox.text_frame
                    p = tf.add_paragraph()
                    p.text = text
                    p.font.size = Pt(12)              
                # 检查页面是否包含表格
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        # 为表格创建新的幻灯片
                        slide = ppt.slides.add_slide(ppt.slide_layouts[5])
                        # 添加表格到幻灯片
                        rows, cols = len(table), len(table[0])
                        top = Inches(2)
                        left = Inches(1)
                        width = Inches(8)
                        height = Inches(0.8)
                        table_shape = slide.shapes.add_table(rows, cols, left, top, width, height).table
                        # 设置单元格文本
                        for r_idx, row in enumerate(table):
                            for c_idx, cell in enumerate(row):
                                table_shape.cell(r_idx, c_idx).text = cell               
                # 检查页面是否包含图片
                images = page.images
                if images:
                    for image in images:
                        # 为图片创建新的幻灯片
                        slide = ppt.slides.add_slide(ppt.slide_layouts[6])
                        im = Image.open(BytesIO(page.extract_image(image)['image']))
                        image_stream = BytesIO()
                        im.save(image_stream, format='PNG')
                        image_stream.seek(0)
                        left = Inches(1)
                        top = Inches(1)
                        slide.shapes.add_picture(image_stream, left, top, width=Inches(5.5), height=Inches(4.5))     
        # 创建临时文件保存pptx
        pptx_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx', mode='w+b')
        ppt.save(pptx_temp.name)
        
        # 返回pptx文件
        pptx_temp.seek(0)
        return send_file(pptx_temp.name, as_attachment=True, download_name='converted.pptx')
    finally:
        # 删除临时的PDF和PPTX文件
        os.unlink(pdf_temp.name)
        if pptx_temp:  # 检查pptx_temp是否已初始化
            os.unlink(pptx_temp.name)

@app.route("/pdf_to_excel", methods=["POST"])
def pdf_to_excel():
    # 假设前端通过表单上传了PDF文件
    pdf_file = request.files['pdf']
    # 创建临时文件保存PDF文件
    pdf_temp = tempfile.NamedTemporaryFile(delete=False)
    pdf_file.save(pdf_temp.name)  
    try:
        # 创建临时文件保存Excel文档
        excel_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', mode='w+b')
        
        # 使用pdfplumber打开PDF文件
        with pdfplumber.open(pdf_temp.name) as pdf:
            # 创建Excel文件
            wb = openpyxl.Workbook()
            ws = wb.active
            # 遍历PDF文件中的所有页
            for page in pdf.pages:
                # 提取当前页的表格
                table = page.extract_table()
                # 检查页面是否包含表格数据
                if table:
                    # 将表格数据写入Excel工作表
                    for row in table:
                        ws.append(row)
        
        # 保存Excel文件到临时文件
        wb.save(excel_temp.name)
        wb.close()
        
        # 返回Excel文档
        excel_temp.seek(0)
        return send_file(excel_temp.name, as_attachment=True, download_name='converted.xlsx')
    finally:
        # 删除临时的PDF和Excel文件
        os.unlink(pdf_temp.name)
        os.unlink(excel_temp.name)


@app.route('/image_to_xlsx', methods=['POST'])
def convert_image_to_xlsx():
    if 'image' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    # 创建临时文件保存图像
    image_temp = tempfile.NamedTemporaryFile(delete=False)
    file.save(image_temp.name)
    excel_temp = None  # 在 try 块之前初始化 excel_temp
    try:
        # 使用OpenCV读取图像
        img = cv2.imread(image_temp.name)
        if img is None:
            raise FileNotFoundError(f"无法加载图像: {image_temp.name}")
        # 初始化Tesseract OCR
        ocr = TesseractOCR(n_threads=1, lang="chi_sim+eng")  # 支持中文和英文
        # 加载图像
        image = Img(img, detect_rotation=False)
        # 提取表格
        tables = image.extract_tables(ocr=ocr)
        if not tables:  # 如果没有提取到表格，提前退出函数
            return jsonify({'error': '图像中没有检测到表格'}), 400
        # 创建临时文件保存Excel文件
        excel_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', mode='w+b')
        # 将表格转换为数据框并保存为Excel文件
        with pd.ExcelWriter(excel_temp.name) as writer:
            for i, table in enumerate(tables):
                df = table.to_dataframe()
                df.to_excel(writer, sheet_name=f'Table {i}', index=False)

        # 返回Excel文件
        excel_temp.seek(0)
        return send_file(excel_temp.name, as_attachment=True, download_name='converted.xlsx')
    except Exception as e:
        # 处理异常
        return jsonify({'error': str(e)}), 500
    finally:
        # 删除临时的图像文件
        os.unlink(image_temp.name)
        # 检查 excel_temp 是否已创建，如果是，则删除
        if excel_temp and os.path.exists(excel_temp.name):
            os.unlink(excel_temp.name)




# if __name__ == '__main__':
#     app.run(debug=False, host='0.0.0.0', port=5000)
