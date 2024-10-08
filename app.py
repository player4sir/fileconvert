from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from pdf2docx import Converter
import os
import tempfile
import img2pdf
from typing import List
from werkzeug.utils import secure_filename
import logging
from PIL import Image, UnidentifiedImageError
import io

app = FastAPI()

# Constants
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

async def handle_file_upload(file: UploadFile, allowed_extensions: tuple):
    if not file:
        raise HTTPException(status_code=400, detail="没有文件部分")
    if file.filename == '':
        raise HTTPException(status_code=400, detail="没有选择文件")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail=f"文件必须是以下类型之一: {', '.join(allowed_extensions)}")
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过限制 {MAX_FILE_SIZE // (1024 * 1024)} MB")
    return contents

async def cleanup(*file_paths):
    for path in file_paths:
        try:
            os.unlink(path)
        except Exception as e:
            logger.error(f"清理临时文件失败 {path}: {str(e)}")

@app.post('/pdf_to_word')
async def convert_pdf_to_word(pdf: UploadFile = File(...)):
    logger.info(f"开始PDF到Word转换，文件名: {pdf.filename}")
    contents = await handle_file_upload(pdf, ('.pdf',))

    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    word_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.docx')
    
    try:
        pdf_temp.write(contents)
        pdf_temp.flush()
        
        cv = Converter(pdf_temp.name)
        cv.convert(word_temp.name, start=0, end=None)
        cv.close()
        
        logger.info(f"完成PDF到Word转换，文件名: {pdf.filename}")
        
        async def background_cleanup():
            await cleanup(pdf_temp.name, word_temp.name)
        
        return FileResponse(word_temp.name, filename='converted.docx', background=background_cleanup)
    except Exception as e:
        await cleanup(pdf_temp.name, word_temp.name)
        logger.error(f"PDF到Word转换失败，文件名 {pdf.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f'转换失败: {str(e)}')

@app.post('/image_to_pdf')
async def convert_images_to_pdf(
    images: List[UploadFile] = File(...),
    orientation: str = Form('portrait'),
    margin: int = Form(8)
):
    logger.info(f"开始图片到PDF转换，共 {len(images)} 张图片")
    total_size = 0
    image_paths = []
    pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    
    try:
        for file in images:
            if file and allowed_file(file.filename):
                contents = await file.read()
                total_size += len(contents)
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail=f"总文件大小超过限制 {MAX_FILE_SIZE // (1024 * 1024)} MB")
                
                logger.info(f"处理文件: {file.filename}, 大小: {len(contents)} bytes")
                
                # Try to open the image using PIL to verify it's a valid image
                try:
                    img = Image.open(io.BytesIO(contents))
                    img.verify()  # Verify that it's a valid image
                    logger.info(f"成功验证图片: {file.filename}, 格式: {img.format}, 大小: {img.size}")
                    img.close()
                    
                    # If it's a valid image, save it as PNG
                    temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    img = Image.open(io.BytesIO(contents))
                    img.save(temp_image.name, format='PNG')
                    temp_image.flush()
                    image_paths.append(temp_image.name)
                    logger.info(f"成功保存图片为PNG: {temp_image.name}")
                except UnidentifiedImageError as img_error:
                    logger.warning(f"无法识别图片格式 {file.filename}: {str(img_error)}")
                    # Fallback: try to convert the image directly without verification
                    temp_image = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    with open(temp_image.name, 'wb') as f:
                        f.write(contents)
                    image_paths.append(temp_image.name)
                    logger.info(f"已保存未验证的图片: {temp_image.name}")
                except Exception as img_error:
                    logger.error(f"处理图片文件时出错 {file.filename}: {str(img_error)}")
                    raise HTTPException(status_code=400, detail=f"处理图片文件时出错: {file.filename}")
            else:
                raise HTTPException(status_code=400, detail="不允许的文件类型")
        
        # Rest of the function remains the same
        a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
        layout_fun = img2pdf.get_layout_fun(pagesize=a4inpt)
        if orientation == 'landscape':
            a4inpt = (a4inpt[1], a4inpt[0])
        with open(pdf_temp.name, "wb") as f:
            f.write(img2pdf.convert(image_paths, layout_fun=layout_fun))
        
        logger.info(f"完成图片到PDF转换，共 {len(images)} 张图片")
        
        async def background_cleanup():
            await cleanup(pdf_temp.name, *image_paths)
        
        return FileResponse(pdf_temp.name, filename='converted.pdf', background=background_cleanup)
    except Exception as e:
        await cleanup(pdf_temp.name, *image_paths)
        logger.error(f"图片到PDF转换失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f'转换失败: {str(e)}')