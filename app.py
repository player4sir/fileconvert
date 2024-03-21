from flask import Flask, request, send_file
from pdf2docx import Converter
import os
import tempfile

import pdfplumber
from pptx import Presentation
from pptx.util import Inches, Pt
from io import BytesIO
from PIL import Image


app = Flask(__name__)

# pdf转换为word
@app.route('/convert_to_word', methods=['POST'])
def convert_pdf_to_word():
    # 假设前端通过表单上传了PDF文件
    pdf_file = request.files['pdf']
    # 创建临时文件保存PDF库库
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
    return send_file(word_temp.name, as_attachment=True, download_name='converted.docx')

@app.route('/convert_to_pptx', methods=['POST'])
def convert_pdf_to_pptx():
    # 假设前端通过表单上传了PDF文件
    pdf_file = request.files['pdf']
    # 创建临时文件保存PDF
    pdf_temp = tempfile.NamedTemporaryFile(delete=False)
    pdf_file.save(pdf_temp.name)
    
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
    pptx_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pptx')
    ppt.save(pptx_temp.name)
    
    # 删除临时的PDF文件
    os.unlink(pdf_temp.name)
    
    # 返回pptx文件
    pptx_temp.seek(0)
    return send_file(pptx_temp.name, as_attachment=True, download_name='converted.pptx')

    


if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
