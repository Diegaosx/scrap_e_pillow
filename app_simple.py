import re
from base64 import b64decode
import boto3
import io
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from urllib.parse import urlparse, urljoin, quote, urlencode
from flask import Flask, request, jsonify, send_file, after_this_request, send_from_directory, render_template, redirect
from bs4 import BeautifulSoup
import requests
import json
import random
import time
import xml.etree.ElementTree as ET
import html
import chardet
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from requests_html import HTMLSession
import asyncio
from requests_html import AsyncHTMLSession
from io import BytesIO
import hashlib
import subprocess
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import os
import logging
from lxml import html as lxml_html
import subprocess
from telethon import TelegramClient, types
import nest_asyncio
from telegram import Bot, Update
from collections import defaultdict
import matplotlib.pyplot as plt
import base64
from datetime import datetime
import pytz
import tempfile
import shutil
from werkzeug.utils import secure_filename
from flask_cors import CORS
import mimetypes
import textwrap

# Permite aninhar loops (necessário para Flask + asyncio)
nest_asyncio.apply()

app = Flask(__name__)
CORS(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Criar pasta de uploads se não existir
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Configurações do S3 (Cloudflare R2)
S3_BUCKET = 'diegao'
S3_REGION = 'us-east-1'
S3_ENDPOINT_URL = 'https://4830cafc5dff5d7c50b8623b89b9b8c9.r2.cloudflarestorage.com'
S3_ACCESS_KEY = 'f60e9da5ad3f0eeabab24de5dc987edf'
S3_SECRET_KEY = '98d4417c42008d3bfc726ddab4a32d46d2612f164cc5b14e82acca5401a598b0'

# Configurando o cliente do S3
s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY
)

# User agents para web scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1'
]

# Funções auxiliares
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def add_border_radius(img, border_radius):
    """Adiciona border radius circular a uma imagem"""
    # Criar máscara circular
    mask = Image.new('L', img.size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle((0, 0) + img.size, fill=255, radius=border_radius)
    
    # Converter imagem para RGBA se necessário
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    # Aplicar máscara
    img.putalpha(mask)
    return img

# ================================
# ROTAS DE SAÚDE E INFORMAÇÕES
# ================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": [
            "image_processing", "web_scraping", "telegram_bot", 
            "youtube_api", "text_to_speech", "chart_generation",
            "cloud_storage", "face_detection", "screenshot_capture"
        ]
    })

@app.route('/home', methods=['GET'])
def home():
    """Página inicial com interface HTML"""
    return render_template('index.html')

@app.route('/', methods=['GET'])
def index():
    """Redirecionar para a página inicial"""
    return redirect('/home')

# ================================
# ROTAS DE UPLOAD E PROCESSAMENTO BÁSICO
# ================================

@app.route('/upload', methods=['POST'])
def upload_file():
    """Upload de arquivo básico"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = str(int(time.time()))
            filename = f"{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            return jsonify({
                'message': 'Arquivo enviado com sucesso',
                'filename': filename,
                'path': filepath
            })
        
        return jsonify({'error': 'Tipo de arquivo não permitido'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process-image-2', methods=['POST'])
def process_image_2():
    """Processamento avançado de imagem com múltiplos textos e imagem secundária com border radius"""
    try:
        data = request.json
        image_url = data['url']
        image_name = data.get('image_name', 'processed_image_2.jpg')
        
        # Baixar imagem principal
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        
        # Converter para RGB se necessário
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        draw = ImageDraw.Draw(img)
        font_path_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        
        # Processar textos (texto1 a texto99)
        for i in range(1, 100):
            texto_key = f'texto{i}'
            if texto_key in data:
                texto = data[texto_key]
                position = data.get(f'{texto_key}_position', [0, 0])
                font_size = int(data.get(f'{texto_key}_font_size', 14))
                max_chars = int(data.get(f'{texto_key}_max_chars', 50))
                color = data.get(f'{texto_key}_color', '#000000')
                
                # Converter cor hex para RGB
                color_rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
                
                # Carregar fonte
                try:
                    font = ImageFont.truetype(font_path_bold, size=font_size)
                except:
                    font = ImageFont.load_default()
                
                # Limitar texto se necessário
                if len(texto) > max_chars:
                    texto = texto[:max_chars] + '...'
                
                # Desenhar texto
                draw.text(tuple(position), texto, fill=color_rgb, font=font)
        
        # Processar segunda imagem se fornecida
        if 'imagem2_url' in data:
            try:
                img2_response = requests.get(data['imagem2_url'])
                img2 = Image.open(BytesIO(img2_response.content))
                
                # Redimensionar segunda imagem
                img2_size = tuple(data.get('imagem2_size', [100, 100]))
                img2 = img2.resize(img2_size, Image.Resampling.LANCZOS)
                
                # Aplicar border radius se especificado
                border_radius = data.get('imagem2_border_radius', 0)
                if border_radius > 0:
                    img2 = add_border_radius(img2, border_radius)
                
                # Posição da segunda imagem
                img2_position = tuple(data.get('imagem2_position', [0, 0]))
                
                # Colar imagem com transparência se tiver border radius
                if border_radius > 0:
                    img.paste(img2, img2_position, img2)
                else:
                    img.paste(img2, img2_position)
                    
            except Exception as e:
                print(f"Erro ao processar segunda imagem: {e}")
        
        # Salvar imagem temporariamente
        temp_path = image_name
        img.save(temp_path, 'JPEG', quality=95)
        
        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_path)
            except Exception as error:
                app.logger.error("Erro ao remover o arquivo temporário", error)
            return response
        
        response = send_file(temp_path, mimetype='image/jpeg')
        response.headers['Content-Disposition'] = f'attachment; filename={image_name}'
        return response
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================================
# ROTAS DE WEB SCRAPING
# ================================

@app.route('/scrape', methods=['POST'])
def scrape_website():
    """Web scraping genérico"""
    try:
        data = request.json
        url = data.get('url')
        selector = data.get('selector', 'title')
        
        if not url:
            return jsonify({'error': 'URL é obrigatória'}), 400
        
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        elements = soup.select(selector)
        results = [elem.get_text(strip=True) for elem in elements]
        
        return jsonify({
            'url': url,
            'selector': selector,
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================================
# ROTAS DE CLOUD STORAGE
# ================================

@app.route('/convert_and_upload', methods=['POST'])
def convert_and_upload():
    data = request.json
    base64_string = data.get('base64_string', '')
    image_name = data.get('image_name', 'default_image')
    directory = data.get('directory', 'bandse')

    if not base64_string:
        return jsonify({"error": "Base64 string is required"}), 400

    try:
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))

        webp_image = io.BytesIO()
        image.save(webp_image, format="webp")
        webp_image.seek(0)

        webp_image_name = f'{image_name}.webp'

        s3_path = f'{directory}/{webp_image_name}'

        s3_client.upload_fileobj(
            webp_image,
            S3_BUCKET,
            s3_path,
            ExtraArgs={'ACL': 'public-read', 'ContentType': 'image/webp'}
        )

        image_url = f'https://s3.diegao.com.br/{s3_path}'

        return jsonify({
            "file_url": image_url,
            "message": "Image converted to webp and uploaded successfully"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
