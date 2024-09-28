from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
from pdf2docx import Converter
from docx2pdf import convert
import os
import tempfile
import img2pdf
from typing import List
from werkzeug.utils import secure_filename
import logging
from contextlib import contextmanager

app = FastAPI()

# Constants
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@contextmanager
def temporary_file(suffix=None):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        yield temp_file
    finally:
        temp_file.close()
        os.unlink(temp_file.name)

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

async def handle_file_upload(file: UploadFile, allowed_extensions: tuple):
    if not file:
        raise HTTPException(status_code=400, detail="No file part")
    if file.filename == '':
        raise HTTPException(status_code=400, detail="No selected file")
    if not file.filename.lower().endswith(allowed_extensions):
        raise HTTPException(status_code=400, detail=f"File must be one of: {', '.join(allowed_extensions)}")
    
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File size exceeds the limit of {MAX_FILE_SIZE // (1024 * 1024)} MB")
    return contents

@app.post('/pdf_to_word')
async def convert_pdf_to_word(pdf: UploadFile = File(...)):
    logger.info(f"Starting PDF to Word conversion for file: {pdf.filename}")
    contents = await handle_file_upload(pdf, ('.pdf',))

    try:
        with temporary_file(suffix='.pdf') as pdf_temp, temporary_file(suffix='.docx') as word_temp:
            pdf_temp.write(contents)
            pdf_temp.flush()
            cv = Converter(pdf_temp.name)
            cv.convert(word_temp.name, start=0, end=None)
            cv.close()
            logger.info(f"Completed PDF to Word conversion for file: {pdf.filename}")
            return FileResponse(word_temp.name, filename='converted.docx')
    except Exception as e:
        logger.error(f"PDF to Word conversion failed for file {pdf.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Conversion failed: {str(e)}')

@app.post('/image_to_pdf')
async def convert_images_to_pdf(
    images: List[UploadFile] = File(...),
    orientation: str = Form('portrait'),
    margin: int = Form(8)
):
    logger.info(f"Starting Image to PDF conversion for {len(images)} images")
    total_size = 0
    image_paths = []
    
    try:
        for file in images:
            if file and allowed_file(file.filename):
                contents = await file.read()
                total_size += len(contents)
                if total_size > MAX_FILE_SIZE:
                    raise HTTPException(status_code=400, detail=f"Total file size exceeds the limit of {MAX_FILE_SIZE // (1024 * 1024)} MB")
                
                with temporary_file(suffix='.png') as temp_file:
                    temp_file.write(contents)
                    temp_file.flush()
                    image_paths.append(temp_file.name)
            else:
                raise HTTPException(status_code=400, detail="File type not allowed")
        
        with temporary_file(suffix='.pdf') as pdf_temp:
            a4inpt = (img2pdf.mm_to_pt(210), img2pdf.mm_to_pt(297))
            layout_fun = img2pdf.get_layout_fun(pagesize=a4inpt)
            if orientation == 'landscape':
                a4inpt = (a4inpt[1], a4inpt[0])
            with open(pdf_temp.name, "wb") as f:
                f.write(img2pdf.convert(image_paths, layout_fun=layout_fun))
            logger.info(f"Completed Image to PDF conversion for {len(images)} images")
            return FileResponse(pdf_temp.name, filename='converted.pdf')
    except Exception as e:
        logger.error(f"Image to PDF conversion failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Conversion failed: {str(e)}')

@app.post('/word_to_pdf')
async def convert_word_to_pdf(word: UploadFile = File(...)):
    logger.info(f"Starting Word to PDF conversion for file: {word.filename}")
    contents = await handle_file_upload(word, ('.doc', '.docx'))

    try:
        with temporary_file(suffix='.docx') as word_temp, temporary_file(suffix='.pdf') as pdf_temp:
            word_temp.write(contents)
            word_temp.flush()
            convert(word_temp.name, pdf_temp.name)
            logger.info(f"Completed Word to PDF conversion for file: {word.filename}")
            return FileResponse(pdf_temp.name, filename='converted.pdf')
    except Exception as e:
        logger.error(f"Word to PDF conversion failed for file {word.filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=f'Conversion failed: {str(e)}')
