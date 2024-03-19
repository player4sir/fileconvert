from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from pdf2docx import Converter
import requests
import json

app = Flask(__name__)

# 微信云托管环境 ID
ENV_ID = 'prod-8gl0hz7v942c14d3'

@app.route('/pdf_to_word', methods=['POST'])
def pdf_to_word():
    # 获取 PDF 文件链接
    pdf_url = request.form.get('pdf_url')

    # 下载 PDF 文件
    try:
        pdf_data = download_file(pdf_url)
    except Exception as e:
        return jsonify({'error': f'下载 PDF 文件失败: {e}'}), 500

    # 将 PDF 转换为 Word
    try:
        cv = Converter(pdf_data)
        docx_data = cv.convert()
        cv.close()
    except Exception as e:
        return jsonify({'error': f'转换 PDF 文件失败: {e}'}), 500

    # 上传 Word 文件到云托管存储
    try:
        word_url = upload_file(docx_data, 'word-file.docx')
    except Exception as e:
        return jsonify({'error': f'上传 Word 文件失败: {e}'}), 500

    # 返回 Word 文件链接
    return jsonify({'word_url': word_url})

def download_file(url):
    response = requests.get(url)
    response.raise_for_status()  # 如果下载失败，则抛出异常
    return response.content

def upload_file(data, file_name):
    # 获取上传链接和签名
    upload_url, signature, security_token, file_id = get_upload_info(file_name)

    # 构造请求数据
    files = {
        'key': (None, file_name),
        'Signature': (None, signature),
        'x-cos-security-token': (None, security_token),
        'x-cos-meta-fileid': (None, file_id),
        'file': (file_name, data)
    }

    # 发送 POST 请求
    response = requests.post(upload_url, files=files)

    # 检查响应状态码
    if response.status_code != 200:
        raise Exception(f'上传文件失败: {response.text}')

    # 返回文件链接
    return upload_url + '/' + file_name

def get_upload_info(file_name):
    # 构造请求数据
    data = {
        'env': ENV_ID,
        'path': file_name
    }

    # 发送 POST 请求
    response = requests.post('http://api.weixin.qq.com/tcb/uploadfile', json=data)

    # 检查响应状态码
    if response.status_code != 200:
        raise Exception(f'获取上传信息失败: {response.text}')

    # 解析响应数据
    res = json.loads(response.text)

    # 返回上传链接、签名、安全令牌和文件 ID
    return res['url'], res['authorization'], res['token'], res['cos_file_id']

if __name__ == '__main__':
    app.run(debug=True)
