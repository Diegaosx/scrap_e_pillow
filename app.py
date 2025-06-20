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
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account
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
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
import mimetypes

# Permite aninhar loops (necessário para Flask + asyncio)
nest_asyncio.apply()

app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

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

# Configurações do Telegram
BOT_TOKEN = '7396481184:AAE8waz49F5bwMFkglP5VkrMRtHNjjNrAwQ'
TELEGRAM_API = f'https://api.telegram.org/bot{BOT_TOKEN}'

# Configurações do YouTube API
API_KEY = 'AIzaSyCEfJTgoJGTWFv3bexgDBHUHJ7A1pfgsWc'

# Configurações RapidAPI
RAPIDAPI_KEY = "c07b08be60msha21942a75c7f85bp180e93jsnac1f9d6be72f"
RAPIDAPI_HOST = "youtube-v2.p.rapidapi.com"
RAPIDAPI_KEY_ALT = "4989426de3msha0e5e9fde1c2567p19f24djsn63c29c30d86e"
RAPIDAPI_HOST_ALT = "youtube-api-full.p.rapidapi.com"

# Configurações AWS Rekognition
rekognition = boto3.client('rekognition', region_name='us-east-1')
IMAGES_DIR = '/home/pillow/imagens-binarias'

# Cache para armazenar grupos admin
admin_groups_cache = defaultdict(dict)
CACHE_TIMEOUT = 3600  # 1 hora

# User agents para web scraping
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/100.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',
    'Mozilla/5.0 (iPad; CPU OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1'
]

# Inicializa uma sessão
session = requests.Session()

# Funções auxiliares
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def complete_url(base_url, link):
    """Completa URLs relativas e corrige links baseados no domínio."""
    if link.startswith("http"):
        return link
    elif link.startswith("//"):
        return 'https:' + link
    else:
        return urljoin(base_url, link)

def get_instagram_page(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.get(url)
    page_source = driver.page_source
    driver.quit()

    soup = BeautifulSoup(page_source, 'html.parser')
    page_title = soup.title.string if soup.title else "Título não encontrado"
    
    return page_title

def decrypt_media(media_key_base64, encrypted_file_path, decrypted_file_path):
    try:
        media_key = b64decode(media_key_base64)
        logger.info(f"Chave decodificada (tamanho: {len(media_key)} bytes): {media_key.hex()}")

        cipher = AES.new(media_key, AES.MODE_CBC, b'\x00' * 16)

        with open(encrypted_file_path, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()

        logger.info(f"Tamanho do arquivo criptografado original: {len(encrypted_data)} bytes")

        if len(encrypted_data) % 16 != 0:
            padding_needed = 16 - (len(encrypted_data) % 16)
            logger.warning(f"Arquivo criptografado ajustado para múltiplo do tamanho do bloco. Padding adicionado: {padding_needed} bytes")
            encrypted_data = pad(encrypted_data, 16)

        decrypted_data = cipher.decrypt(encrypted_data)

        try:
            decrypted_data = unpad(decrypted_data, 16)
        except ValueError as e:
            logger.error(f"Erro ao remover padding: {e}")
            return False

        with open(decrypted_file_path, 'wb') as decrypted_file:
            decrypted_file.write(decrypted_data)

        logger.info(f"Arquivo descriptografado salvo em: {decrypted_file_path}")
        return True

    except Exception as e:
        logger.error(f"Erro na descriptografia: {e}")
        return False

def init_driver():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def search_videos(term, max_results=20, order='date', video_definition='any', video_duration='any', region_code='br'):
    url = "https://youtube-api-full.p.rapidapi.com/api/searchVideos"
    
    query_params = {
        "maxResults": max_results,
        "order": order,
        "videoDefinition": video_definition,
        "videoDuration": video_duration,
        "query": term,
        "regionCode": region_code
    }
    
    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY_ALT,
        "X-RapidAPI-Host": RAPIDAPI_HOST_ALT
    }
    
    try:
        response = requests.get(url, headers=headers, params=query_params)
        response.raise_for_status()
        
        if response.status_code == 200:
            data = response.json()
            videos = data.get("messages", {}).get("items", [])
            video_ids = [video['id']['videoId'] for video in videos if video.get('id', {}).get('videoId')]
            return video_ids
        else:
            return []
    
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    
    return []

def check_comments(video_id, max_results):
    url = "https://youtube-api-full.p.rapidapi.com/api/comments"
    querystring = {"part": "snippet", "textFormat": "html", "videoId": video_id, "maxResults": max_results}

    headers = {
        "X-Rapidapi-Key": RAPIDAPI_KEY_ALT,
        "X-Rapidapi-Host": RAPIDAPI_HOST_ALT
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        if 'items' in data.get('messages', {}):
            comments = []
            for item in data['messages']['items']:
                comment = item['snippet']['topLevelComment']['snippet'].get('textDisplay')
                if comment:
                    comments.append(comment)
            return comments
    return None

def draw_text(draw, text, position, font, color, max_chars, max_length=200):
    x, y = position
    if len(text) > max_length:
        text = text[:max_length].rstrip() + '...'

    words = text.split()
    current_line = ''
    lines = []
    for word in words:
        if len(current_line) + len(word) + 1 <= max_chars:
            current_line += word + ' '
        else:
            lines.append(current_line)
            current_line = word + ' '
    lines.append(current_line)
    for line in lines:
        draw.text((x, y), line.rstrip(), font=font, fill=color)
        y += 45

def process_position(position, text, font, img):
    draw = ImageDraw.Draw(img)
    if position[0] == 'centro':
        text_width, _ = draw.textsize(text, font=font)
        position[0] = (img.width - text_width) // 2
    if position[1] == 'centro':
        _, text_height = draw.textsize(text, font=font)
        position[1] = (img.height - text_height) // 2
    return position

def draw_text_with_background(draw, text, position, font, text_color, background_color, padding, max_chars):
    text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
    
    image_center_x, image_center_y = draw.im.size
    image_center_x /= 2
    image_center_y /= 2

    x, y = position
    padding_horizontal, padding_vertical = padding

    if x == 'centro':
        x = image_center_x - text_width / 2
    if y == 'centro':
        y = image_center_y - text_height / 2

    bg_x = x - padding_horizontal
    bg_y = y - padding_vertical
    bg_width = text_width + 2 * padding_horizontal
    bg_height = text_height + 2 * padding_vertical

    draw.rectangle([bg_x, bg_y, bg_x + bg_width, bg_y + bg_height], fill=background_color)
    draw.text((x, y), text, fill=text_color, font=font)

def adjust_image_aspect_ratio(img, target_width=1200, target_height=752):
    img_aspect_ratio = img.width / img.height
    target_aspect_ratio = target_width / target_height

    if img_aspect_ratio > target_aspect_ratio:
        scale_factor = target_height / img.height
    else:
        scale_factor = target_width / img.width

    img_resized = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.Resampling.LANCZOS)

    if img_resized.width > 1200:
        left = (img_resized.width - 1200) / 2
        top = 0
        right = left + 1200
        bottom = 752
    else:
        top = (img_resized.height - 752) / 2
        left = 0
        bottom = top + 752
        right = 1200

    img_cropped = img_resized.crop((left, top, right, bottom))
    return img_cropped

def generate_bar_chart(labels, values):
    plt.figure(figsize=(8, 4))
    plt.bar(labels, values, color=['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'])
    plt.title("Comparação de Gastos por Período (Barras)")
    plt.ylabel("Total de Gastos")
    plt.xticks(rotation=45, ha='right')
    return save_plot_to_base64()

def generate_line_chart(labels, values):
    plt.figure(figsize=(8, 4))
    plt.plot(labels, values, marker='o', color='#36A2EB')
    plt.title("Tendência de Gastos ao Longo do Tempo (Linhas)")
    plt.ylabel("Total de Gastos")
    plt.xticks(rotation=45, ha='right')
    return save_plot_to_base64()

def generate_pie_chart(labels, values):
    plt.figure(figsize=(6, 6))
    plt.pie(values, labels=labels, autopct='%1.1f%%', colors=['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF', '#FF9F40'])
    plt.title("Proporção de Gastos por Período (Pizza)")
    return save_plot_to_base64()

def save_plot_to_base64():
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close()
    return image_base64

# Comentar as importações que causam conflito
# from deepface import DeepFace

# Adicionar no início do arquivo, após as outras importações:
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
except ImportError:
    DEEPFACE_AVAILABLE = False
    print("DeepFace não disponível. Funcionalidade de detecção de gênero desabilitada.")

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
@limiter.limit("10 per minute")
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

@app.route('/resize', methods=['POST'])
@limiter.limit("20 per minute")
def resize_image_basic():
    """Redimensionamento básico de imagem"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        width = int(request.form.get('width', 800))
        height = int(request.form.get('height', 600))
        
        if file and allowed_file(file.filename):
            img = Image.open(file.stream)
            img_resized = img.resize((width, height), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img_resized.save(output, format='JPEG')
            output.seek(0)
            
            return send_file(output, mimetype='image/jpeg', as_attachment=True, 
                           download_name=f'resized_{file.filename}')
        
        return jsonify({'error': 'Arquivo inválido'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/add-text', methods=['POST'])
@limiter.limit("15 per minute")
def add_text_to_image():
    """Adicionar texto a uma imagem"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        text = request.form.get('text', 'Sample Text')
        font_size = int(request.form.get('font_size', 40))
        color = request.form.get('color', '#FFFFFF')
        
        if file and allowed_file(file.filename):
            img = Image.open(file.stream)
            draw = ImageDraw.Draw(img)
            
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', font_size)
            except:
                font = ImageFont.load_default()
            
            # Converter cor hex para RGB
            color_rgb = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            
            # Posição centralizada
            text_width, text_height = draw.textbbox((0, 0), text, font=font)[2:]
            x = (img.width - text_width) // 2
            y = (img.height - text_height) // 2
            
            draw.text((x, y), text, fill=color_rgb, font=font)
            
            output = io.BytesIO()
            img.save(output, format='JPEG')
            output.seek(0)
            
            return send_file(output, mimetype='image/jpeg', as_attachment=True,
                           download_name=f'text_{file.filename}')
        
        return jsonify({'error': 'Arquivo inválido'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/convert', methods=['POST'])
@limiter.limit("10 per minute")
def convert_image_format():
    """Converter formato de imagem"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        target_format = request.form.get('format', 'JPEG').upper()
        
        if file and allowed_file(file.filename):
            img = Image.open(file.stream)
            
            if target_format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            output = io.BytesIO()
            img.save(output, format=target_format)
            output.seek(0)
            
            mimetype = f'image/{target_format.lower()}'
            extension = target_format.lower()
            
            return send_file(output, mimetype=mimetype, as_attachment=True,
                           download_name=f'converted.{extension}')
        
        return jsonify({'error': 'Arquivo inválido'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/thumbnail', methods=['POST'])
@limiter.limit("20 per minute")
def create_thumbnail():
    """Criar thumbnail de imagem"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        size = int(request.form.get('size', 150))
        
        if file and allowed_file(file.filename):
            img = Image.open(file.stream)
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format='JPEG')
            output.seek(0)
            
            return send_file(output, mimetype='image/jpeg', as_attachment=True,
                           download_name=f'thumb_{file.filename}')
        
        return jsonify({'error': 'Arquivo inválido'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/watermark', methods=['POST'])
@limiter.limit("10 per minute")
def add_watermark():
    """Adicionar marca d'água"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        watermark_text = request.form.get('watermark', '© 2024')
        opacity = float(request.form.get('opacity', 0.5))
        
        if file and allowed_file(file.filename):
            img = Image.open(file.stream).convert('RGBA')
            
            # Criar camada de marca d'água
            watermark = Image.new('RGBA', img.size, (255, 255, 255, 0))
            draw = ImageDraw.Draw(watermark)
            
            try:
                font = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 30)
            except:
                font = ImageFont.load_default()
            
            text_width, text_height = draw.textbbox((0, 0), watermark_text, font=font)[2:]
            x = img.width - text_width - 10
            y = img.height - text_height - 10
            
            draw.text((x, y), watermark_text, fill=(255, 255, 255, int(255 * opacity)), font=font)
            
            # Combinar imagens
            watermarked = Image.alpha_composite(img, watermark)
            watermarked = watermarked.convert('RGB')
            
            output = io.BytesIO()
            watermarked.save(output, format='JPEG')
            output.seek(0)
            
            return send_file(output, mimetype='image/jpeg', as_attachment=True,
                           download_name=f'watermarked_{file.filename}')
        
        return jsonify({'error': 'Arquivo inválido'}), 400
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================================
# ROTAS DO PILLOW (PROCESSAMENTO AVANÇADO)
# ================================

@app.route('/process-image', methods=['POST'])
def process_image():
    data = request.json
    image_url = data['url']
    image_name = data.get('image_name', 'modified_image.jpg')
    titulo_font_size = int(data.get('titulo_font_size', 45))
    titulo_max_chars = int(data.get('titulo_max_chars', 38))
    titulo_color = data.get('titulo_color', '#FFFFFF')
    titulo_color = tuple(int(titulo_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(img)
    font_path_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font_data = ImageFont.truetype(font_path_bold, size=25)
    font_orcamento = ImageFont.truetype(font_path_bold, size=40)
    font_titulo = ImageFont.truetype(font_path_bold, size=titulo_font_size)
    font_categoria = ImageFont.truetype(font_path_bold, size=25)
    draw_text(draw, data['data'], data['data_position'], font_data, (255, 255, 255), 38)
    draw_text(draw, data['orcamento'], data['orcamento_position'], font_orcamento, (255, 255, 255), 38)
    draw_text(draw, data['titulo'], data['titulo_position'], font_titulo, titulo_color, titulo_max_chars)
    draw_text(draw, data['categoria'], data['categoria_position'], font_categoria, (255, 255, 255), 38)
    secondary_img_url = data.get('secondary_image_url')
    if secondary_img_url:
        sec_img_response = requests.get(secondary_img_url)
        sec_img = Image.open(BytesIO(sec_img_response.content))
        sec_img_size = tuple(data.get('secondary_image_size', [100, 100]))
        sec_img = sec_img.resize(sec_img_size, Image.Resampling.LANCZOS)
        sec_img_position = tuple(data.get('secondary_image_position', [300, 300]))
        img.paste(sec_img, sec_img_position, sec_img)
    temp_path = image_name
    img.save(temp_path)
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

@app.route('/imagem-com-imagem', methods=['POST'])
def imagem_com_imagem():
    data = request.json
    image_url = data['url']
    image_name = data.get('image_name', 'custom_image.jpg')

    titulo_font_size = int(data.get('titulo_font_size', 45))
    titulo_color = data.get('titulo_color', '#FFFFFF')
    titulo_background_color = data.get('titulo_background_color', '#000000')
    titulo_padding = tuple(data.get('titulo_padding', [10, 5]))
    titulo_max_chars = int(data.get('titulo_max_chars', 70))

    data_font_size = int(data.get('data_font_size', 20))
    data_color = data.get('data_color', '#FFFFFF')

    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    draw = ImageDraw.Draw(img)

    font_path_bold = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
    font_titulo = ImageFont.truetype(font_path_bold, size=titulo_font_size)
    font_data = ImageFont.truetype(font_path_bold, size=data_font_size)

    draw_text_with_background(draw, data['titulo'], data['titulo_position'], font_titulo, titulo_color, titulo_background_color, titulo_padding, titulo_max_chars)
    draw_text_with_background(draw, data['data'], data['data_position'], font_data, data_color, titulo_background_color, titulo_padding, titulo_max_chars)

    secondary_img_url = data.get('secondary_image_url')
    if secondary_img_url:
        sec_img_response = requests.get(secondary_img_url)
        sec_img = Image.open(BytesIO(sec_img_response.content))
        sec_img_size = tuple(data.get('secondary_image_size', [100, 100]))
        sec_img = sec_img.resize(sec_img_size, Image.Resampling.LANCZOS)
        sec_img_position = tuple(data.get('secondary_image_position', [300, 300]))
        img.paste(sec_img, sec_img_position, sec_img)

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    temp_path = image_name
    img.save(temp_path)

    @after_this_request
    def remove_file(response):
        try:
            os.remove(temp_path)
        except Exception as error:
            app.logger.error("Erro ao remover o arquivo temporário", error)
        return response

    return send_file(temp_path, mimetype='image/jpeg', as_attachment=True, download_name=temp_path)

@app.route('/resize-image', methods=['POST'])
def resize_image():
    data = request.json
    image_url = data['url']
    image_name = data.get('image_name', 'resized_image.jpg')

    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))

    if img.height > img.width:
        new_height = int((img.height * 1200) / img.width)
        img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
        new_img = Image.new('RGB', (1200, 752), (255, 255, 255))
        y_position = int((752 - new_height) / 2)
        new_img.paste(img, (0, max(0, y_position)))
        img = new_img
    else:
        img = img.resize((1200, 752), Image.Resampling.LANCZOS)

    if img.mode == 'RGBA':
        img = img.convert('RGB')

    temp_path = image_name
    img.save(temp_path)

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

@app.route('/resize-image-novo', methods=['POST'])
def resize_image_novo():
    try:
        data = request.json
        image_url = data['url']
        image_name = data.get('image_name', 'resized_image.jpg')

        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        if img.format == "GIF":
            frames = [frame.copy() for frame in ImageSequence.Iterator(img)]
            img = frames[0]

        if img.height > img.width:
            new_height = int((img.height * 1200) / img.width)
            img = img.resize((1200, new_height), Image.Resampling.LANCZOS)
            new_img = Image.new('RGB', (1200, 752), (255, 255, 255))
            y_position = int((752 - new_height) / 2)
            new_img.paste(img, (0, max(0, y_position)))
            img = new_img
        else:
            img = img.resize((1200, 752), Image.Resampling.LANCZOS)

        if img.mode in ['P', 'RGBA']:
            img = img.convert('RGB')

        temp_path = image_name
        img.save(temp_path)

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
        return jsonify({"error": str(e)})

@app.route('/imagem-com-texto', methods=['POST'])
def imagem_com_texto():
    try:
        data = request.json
        background_url = data['background_url']
        text = data['text']
        text_color = data.get('text_color', '#000000')
        font_size = int(data.get('font_size', 24))
        image_name = data.get('image_name', 'custom_image.jpg')

        response = requests.get(background_url)
        background_img = Image.open(BytesIO(response.content))

        font_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        font = ImageFont.truetype(font_path, font_size)
        draw = ImageDraw.Draw(background_img)

        text_width, text_height = draw.textsize(text, font=font)
        x_position = (background_img.width - text_width) / 2
        y_position = (background_img.height - text_height) / 2

        draw.text((x_position, y_position), text, font=font, fill=text_color)

        temp_path = image_name
        background_img.save(temp_path)

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
        return jsonify({"error": str(e)})

@app.route('/sem-distorcer-imagem', methods=['POST'])
def sem_distorcer_imagem():
    try:
        data = request.json
        image_url = data['url']
        image_name = data.get('image_name', 'resized_image.webp')

        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        target_width, target_height = 1200, 752
        img_aspect_ratio = img.width / img.height
        target_aspect_ratio = target_width / target_height

        if img_aspect_ratio > target_aspect_ratio:
            scale_factor = target_height / img.height
        else:
            scale_factor = target_width / img.width

        img_resized = img.resize((int(img.width * scale_factor), int(img.height * scale_factor)), Image.Resampling.LANCZOS)

        if img_resized.width > 1200:
            left = (img_resized.width - 1200) / 2
            top = 0
            right = left + 1200
            bottom = 752
        else:
            top = (img_resized.height - 752) / 2
            left = 0
            bottom = top + 752
            right = 1200

        img_cropped = img_resized.crop((left, top, right, bottom))

        temp_path = image_name
        img_cropped.save(temp_path, 'WEBP')

        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_path)
            except Exception as error:
                app.logger.error("Erro ao remover o arquivo temporário", error)
            return response

        response = send_file(temp_path, mimetype='image/webp')
        response.headers['Content-Disposition'] = f'attachment; filename={image_name}'
        return response

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/imagem-binaria', methods=['POST'])
def imagem_binaria():
    try:
        data = request.json
        image_data = data['image_data']
        image_name = data.get('image_name', 'default_image.jpg')

        image_bytes = base64.b64decode(image_data)
        img = Image.open(BytesIO(image_bytes))

        save_path = os.path.join('/caminho/para/salvar', image_name)
        img.save(save_path)

        return jsonify({'message': 'Image saved successfully', 'path': save_path}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/detect-gender', methods=['POST'])
def detect_gender():
    if not DEEPFACE_AVAILABLE:
        return jsonify({"error": "DeepFace não está disponível nesta instalação"}), 503
    
    try:
        data = request.json
        image_url = data.get('url')

        if not image_url:
            return jsonify({"error": "Image URL is required"}), 400

        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))

        if img.mode != 'RGB':
            img = img.convert('RGB')

        img_path = "temp_image.jpg"
        img.save(img_path)

        result = DeepFace.analyze(img_path, actions=['gender'])

        os.remove(img_path)

        if isinstance(result, list):
            gender_confidence = result[0]['gender']
        else:
            gender_confidence = result['gender']

        if gender_confidence['Man'] > 70:
            gender = "Homem"
        elif gender_confidence['Woman'] > 70:
            gender = "Mulher"
        else:
            gender = "Indeterminado"

        return jsonify({
            "gender": gender,
            "confidence": {
                "Homem": gender_confidence['Man'],
                "Mulher": gender_confidence['Woman']
            }
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/screenshot', methods=['GET'])
def screenshot():
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')

        driver = webdriver.Chrome(options=options)
        driver.get("https://thispersondoesnotexist.com")

        screenshot_path = os.path.join(IMAGES_DIR, "screenshot.png")
        driver.save_screenshot(screenshot_path)

        driver.quit()

        gmt_time = datetime.now(pytz.utc)
        gmt_time_str = gmt_time.strftime("%Y-%m-%d %H:%M:%S %Z")

        recife_tz = pytz.timezone('America/Recife')
        recife_time = gmt_time.astimezone(recife_tz)
        recife_time_str = recife_time.strftime("%Y-%m-%d %H:%M:%S %Z")

        image_url = "https://imagem-post.diegao.com.br/imagens-binarias/screenshot.png"
        return jsonify({
            "message": "Screenshot saved successfully",
            "url": image_url,
            "gmt_time": gmt_time_str,
            "recife_time": recife_time_str
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/crop-center-maior', methods=['POST'])
def crop_center_maior():
    try:
        data = request.json
        image_name = data.get('image_name', 'screenshot.png')
        prefix = data.get('prefix', '')

        image_path = os.path.join(IMAGES_DIR, image_name)
        img = Image.open(image_path)

        width, height = img.size
        new_width = new_height = min(width, height)
        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2

        img_cropped = img.crop((left, top, right, bottom))

        new_image_name = f"{prefix}-{image_name}"
        new_image_path = os.path.join(IMAGES_DIR, new_image_name)

        img_cropped.save(new_image_path)

        return jsonify({"message": "Image cropped and saved successfully", "path": new_image_path}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/crop-center', methods=['POST'])
def crop_center():
    try:
        data = request.json
        image_name = data.get('image_name', 'screenshot.png')
        prefix = data.get('prefix', '')

        image_path = os.path.join(IMAGES_DIR, image_name)
        img = Image.open(image_path)

        width, height = img.size
        new_width = new_height = min(width, height)
        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2

        img_cropped = img.crop((left, top, right, bottom))
        img_resized = img_cropped.resize((52, 52), Image.Resampling.LANCZOS)

        new_image_name = f"{prefix}-{image_name}"
        new_image_path = os.path.join(IMAGES_DIR, new_image_name)

        img_resized.save(new_image_path)

        @after_this_request
        def remove_file(response):
            try:
                os.remove(new_image_path)
            except Exception as error:
                app.logger.error("Erro ao remover o arquivo temporário", error)
            return response

        return send_file(new_image_path, mimetype='image/png', as_attachment=True, download_name=new_image_name)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/analyze-image', methods=['POST'])
def analyze_image():
    try:
        data = request.json
        image_url = data.get('url')

        if not image_url:
            return jsonify({"error": "Image URL is required"}), 400

        response = requests.get(image_url)
        img_bytes = response.content

        rekog_response = rekognition.detect_faces(
            Image={'Bytes': img_bytes},
            Attributes=['GENDER', 'EMOTIONS', 'AGE_RANGE']
        )

        faces_info = []
        for face_detail in rekog_response['FaceDetails']:
            face_info = {
                "confidence": face_detail['Confidence'],
                "gender": face_detail['Gender']['Value'],
                "gender_confidence": face_detail['Gender']['Confidence'],
                "age_range": {
                    "low": face_detail['AgeRange']['Low'],
                    "high": face_detail['AgeRange']['High']
                },
                "emotions": {emotion['Type']: emotion['Confidence'] for emotion in face_detail['Emotions']}
            }
            faces_info.append(face_info)

        return jsonify({"faces": faces_info}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================
# ROTAS DE WEB SCRAPING
# ================================

@app.route('/scrape', methods=['POST'])
@limiter.limit("30 per minute")
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

@app.route('/extract-links', methods=['POST'])
@limiter.limit("20 per minute")
def extract_links():
    """Extrair links de uma página"""
    try:
        data = request.json
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL é obrigatória'}), 400
        
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text(strip=True)
            full_url = urljoin(url, href)
            links.append({
                'url': full_url,
                'text': text,
                'href': href
            })
        
        return jsonify({
            'url': url,
            'links': links,
            'count': len(links)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/fragmentado', methods=['POST'])
def fragmentado():
    data = request.json
    url = data.get('url', '')
    classe_conteudo = data.get('conteudo', '')

    if not url or not classe_conteudo:
        return jsonify({"error": "URL and content class are required"}), 400

    try:
        session = requests.Session()
        session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        response = session.get(url)

        detected_encoding = chardet.detect(response.content)['encoding']
        response_text = response.content.decode(detected_encoding)

        soup = BeautifulSoup(response_text, 'html.parser')

        time.sleep(2)

        content_elements = soup.find_all(class_=classe_conteudo)

        combined_content = ""
        for content_div in content_elements:
            domain = urlparse(url).netloc
            for a_tag in content_div.find_all('a', href=True):
                link = a_tag['href']
                link = urljoin(url, link)
                if urlparse(link).netloc == domain:
                    new_tag = soup.new_tag("b")
                    new_tag.string = a_tag.get_text()
                    a_tag.replace_with(new_tag)

            for tag in content_div.find_all(['script', 'style', 'iframe']):
                tag.decompose()

            combined_content += html.unescape(str(content_div))

        return jsonify({"conteudo": combined_content})

    except Exception as e:
        print(f"Erro ao processar o conteúdo: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/info-post', methods=['POST'])
def info_post():
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    session = requests.Session()

    try:
        session.headers.update({'User-Agent': random.choice(USER_AGENTS)})
        response = session.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        time.sleep(2)

        result = {}
        for key, value in data.items():
            if key != 'url':
                if key == 'direito-imagem':
                    direito_imagem_values = value.split(',')
                    direito_imagem_content = ''
                    for di_value in direito_imagem_values:
                        di_value = di_value.strip()
                        if di_value == 'figcaption':
                            figcaption = soup.find('figcaption')
                            if figcaption:
                                direito_imagem_content = ' '.join([x.strip() for x in figcaption.stripped_strings])
                                break
                        elif di_value in ['og:description', 'description']:
                            meta_tag = soup.find('meta', {'property': di_value}) or soup.find('meta', {'name': di_value})
                            if meta_tag:
                                direito_imagem_content = meta_tag.get('content', '')
                                break
                        else:
                            element = soup.find(class_=di_value)
                            if element:
                                direito_imagem_content = element.text.strip()
                                break
                    result[key] = direito_imagem_content if direito_imagem_content else "© 2025"
                elif key == 'imagem':
                    image_values = value.split(',')
                    image_content = ''
                    for image_value in image_values:
                        image_value = image_value.strip()
                        if image_value == 'twitter:image':
                            meta_tag = soup.find('meta', {'name': 'twitter:image'})
                            if meta_tag:
                                image_content = meta_tag.get('content', '')
                                break
                        else:
                            picture_element = soup.find('picture', class_=image_value)
                            if picture_element:
                                img_element = picture_element.find('img')
                                if img_element:
                                    image_content = complete_url(url, img_element['src']).split('?')[0]
                                    break
                            else:
                                img_elements = soup.find_all('img', class_=image_value)
                                if img_elements:
                                    image_content = [complete_url(url, img['src']).split('?')[0] for img in img_elements]
                                    break
                    result[key] = image_content if image_content else "© 2025"
                elif key == 'titulo':
                    element = soup.find('h1', class_=value) or soup.find('title')
                    if element:
                        result[key] = element.text.strip()
                    else:
                        result[key] = "© 2025"
                elif key == 'conteudo':
                    element = soup.find(id=value) or soup.find(class_=value)
                    if element:
                        result[key] = element.text.strip()
                    else:
                        result[key] = "© 2025"
                else:
                    elements = soup.find_all(class_=value) or soup.find_all(id=value)
                    if elements:
                        result[key] = [element.text.strip() for element in elements]
                    else:
                        result[key] = "© 2025"

        favicon_link = soup.find("link", rel=lambda x: x and 'icon' in x.lower())
        if favicon_link:
            result['favicon'] = complete_url(url, favicon_link['href'])
        else:
            result['favicon'] = "Favicon not found"

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================
# ROTAS DO TELEGRAM
# ================================

@app.route('/grupos-admin', methods=['GET'])
def list_admin_groups():
    try:
        bot_info = requests.get(f"{TELEGRAM_API}/getMe").json()
        if not bot_info.get('ok'):
            return jsonify({'status': 'error', 'message': 'Falha ao obter informações do bot'}), 500

        bot_id = bot_info['result']['id']
        
        updates = requests.get(f"{TELEGRAM_API}/getUpdates?offset=0&limit=100").json()
        if not updates.get('ok'):
            return jsonify({'status': 'error', 'message': 'Falha ao obter updates'}), 500

        admin_chats = []
        processed_chats = set()

        for update in updates.get('result', []):
            chat = None
            
            if 'my_chat_member' in update:
                chat = update['my_chat_member']['chat']
            elif 'message' in update:
                chat = update['message']['chat']
            elif 'channel_post' in update:
                chat = update['channel_post']['chat']
            
            if chat and chat['id'] not in processed_chats:
                processed_chats.add(chat['id'])
                
                if chat['type'] in ['group', 'supergroup', 'channel']:
                    try:
                        member_info = requests.get(
                            f"{TELEGRAM_API}/getChatMember",
                            params={'chat_id': chat['id'], 'user_id': bot_id}
                        ).json()
                        
                        if member_info.get('result', {}).get('status') in ['administrator', 'creator']:
                            group_data = {
                                'id': chat['id'],
                                'title': chat.get('title'),
                                'username': chat.get('username'),
                                'type': chat['type']
                            }
                            admin_chats.append(group_data)
                    except Exception as e:
                        print(f"Erro ao verificar chat {chat.get('title', chat['id'])}: {str(e)}")
                        continue

        return jsonify({
            'status': 'success',
            'bot': f"@{bot_info['result']['username']}",
            'count': len(admin_chats),
            'groups': admin_chats,
            'updates_processed': len(updates.get('result', []))
        })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/force-update', methods=['GET'])
def force_update():
    try:
        updates = requests.get(f"{TELEGRAM_API}/getUpdates").json()
        if updates.get('result'):
            last_id = updates['result'][-1]['update_id']
            requests.get(f"{TELEGRAM_API}/getUpdates?offset={last_id+1}")
        
        return jsonify({
            'status': 'success',
            'message': 'Updates limpos. Adicione o bot a um novo grupo e chame /grupos-admin novamente.'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/teste-conexao', methods=['GET'])
def teste_conexao():
    loop = asyncio.get_event_loop()
    try:
        me = loop.run_until_complete(bot.get_me())
        updates = loop.run_until_complete(bot.get_updates())
        return jsonify({
            'bot': me.username,
            'updates_count': len(updates),
            'first_update': str(updates[0]) if updates else None
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ================================
# ROTAS DE GRÁFICOS
# ================================

@app.route('/generate_chart2', methods=['POST'])
def generate_chart2():
    try:
        data = request.json

        total_last_7_days = float(data[0]['total_last_7_days'])
        total_previous_7_days = float(data[0]['total_previous_7_days'])
        total_last_15_days = float(data[1]['total_last_15_days'])
        total_previous_15_days = float(data[1]['total_previous_15_days'])
        total_last_30_days = float(data[2]['total_last_30_days'])
        total_previous_30_days = float(data[2]['total_previous_30_days'])

        labels = [
            "Últimos 7 dias", "7 dias anteriores",
            "Últimos 15 dias", "15 dias anteriores",
            "Últimos 30 dias", "30 dias anteriores"
        ]
        values = [
            total_last_7_days, total_previous_7_days,
            total_last_15_days, total_previous_15_days,
            total_last_30_days, total_previous_30_days
        ]

        bar_chart = generate_bar_chart(labels, values)
        line_chart = generate_line_chart(labels, values)
        pie_chart = generate_pie_chart(labels, values)

        return jsonify({
            "bar_chart": bar_chart,
            "line_chart": line_chart,
            "pie_chart": pie_chart
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/generate_chart', methods=['POST'])
def generate_chart():
    try:
        data = request.json
        
        response = requests.post(
            'https://charts-n8n.vercel.app/api/charts',
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            message_7_days = result["message_7"]
            message_15_days = result["message_15"]
            message_30_days = result["message_30"]
            
            bar_chart_7 = result["bar_chart_7"]
            
            return jsonify(result)
        else:
            return jsonify({"error": f"Falha ao chamar o serviço: {response.status_code}"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# ================================
# ROTAS DE ÁUDIO E TTS
# ================================

@app.route('/process_audio', methods=['POST'])
def process_audio():
    try:
        data = request.json
        media_url = data.get('media_url')
        media_key_base64 = data.get('media_key')

        if not media_url or not media_key_base64:
            logger.error("Parâmetros 'media_url' e 'media_key' são obrigatórios")
            return jsonify({"error": "Parâmetros 'media_url' e 'media_key' são obrigatórios"}), 400

        encrypted_file_path = 'encrypted_media.enc'
        headers = {'Authorization': 'Bearer YOUR_ACCESS_TOKEN'}
        response = requests.get(media_url, headers=headers)

        if response.status_code == 200:
            with open(encrypted_file_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Arquivo criptografado baixado e salvo em: {encrypted_file_path}")
            logger.info(f"Tamanho do arquivo baixado: {os.path.getsize(encrypted_file_path)} bytes")
        else:
            logger.error(f"Erro ao baixar o arquivo. Status code: {response.status_code}")
            return jsonify({"error": "Erro ao baixar o arquivo", "status_code": response.status_code}), 500

        decrypted_file_path = 'decrypted_media.ogg'
        success = decrypt_media(media_key_base64, encrypted_file_path, decrypted_file_path)

        if not success:
            logger.error("Erro ao descriptografar o arquivo.")
            return jsonify({"error": "Erro ao descriptografar o arquivo"}), 500

        mp3_file_path = 'final_audio.mp3'
        command = ['ffmpeg', '-i', decrypted_file_path, mp3_file_path]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        if result.returncode == 0:
            logger.info(f"Arquivo convertido para MP3 e salvo em: {mp3_file_path}")
        else:
            logger.error(f"Erro ao converter para MP3: {result.stderr.decode('utf-8')}")
            return jsonify({"error": "Erro ao converter para MP3"}), 500

        logger.info("Processamento concluído com sucesso. Retornando o arquivo MP3.")
        return send_file(mp3_file_path, mimetype='audio/mpeg')

    except Exception as e:
        logger.error(f"Erro inesperado: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/narracao', methods=['POST'])
def narracao():
    data = request.get_json()
    text = data.get("text")
    filename = data.get("filename", "narracao.mp3")
    voice = data.get("voice", "pt-BR-Antonio")

    if not text:
        return jsonify({"error": "Texto é necessário"}), 400

    url = f"https://streamlined-edge-tts.p.rapidapi.com/tts?text={quote(text)}&voice={voice}"
    headers = {
        "x-rapidapi-host": "streamlined-edge-tts.p.rapidapi.com",
        "x-rapidapi-key": "c07b08be60msha21942a75c7f85bp180e93jsnac1f9d6be72f"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        audio_content = io.BytesIO(response.content)
        audio_content.seek(0)
        return send_file(audio_content, mimetype='audio/mpeg', download_name=f"{filename}.mp3")

    except requests.exceptions.HTTPError as http_err:
        return jsonify({"error": str(http_err)}), response.status_code
    except Exception as err:
        return jsonify({"error": str(err)}), 500

# ================================
# ROTAS DO YOUTUBE
# ================================

@app.route('/youtube/procura_videos', methods=['POST'])
def youtube_procura_videos():
    RAPIDAPI_KEY = "c07b08be60msha21942a75c7f85bp180e93jsnac1f9d6be72f"
    RAPIDAPI_HOST = "youtube-v2.p.rapidapi.com"

    data = request.get_json()

    queries = data.get('query', '').split(',')
    country = data.get('country', 'br')
    lang = data.get('lang', 'pt')
    order_by_options = data.get('order_by', ['today', 'this_week'])

    if not queries or not any(queries):
        return jsonify({"error": "At least one query is required"}), 400

    max_attempts = 4
    attempts = 0

    for order_by in order_by_options:
        for query in queries:
            query = query.strip()

            while attempts < max_attempts:
                url = f'https://{RAPIDAPI_HOST}/search/?query={query}&lang={lang}&order_by={order_by}&country={country}'
                headers = {
                    'x-rapidapi-host': RAPIDAPI_HOST,
                    'x-rapidapi-key': RAPIDAPI_KEY
                }

                try:
                    response = requests.get(url, headers=headers)
                    response.raise_for_status()

                    data = response.json()
                    videos = data.get('videos', [])
                    continuation_token = data.get('continuation_token', None)

                    if videos:
                        video_ids = [video['video_id'] for video in videos if 'video_id' in video]
                        return jsonify({
                            "number_of_videos": len(video_ids),
                            "query": query,
                            "country": country,
                            "lang": lang,
                            "continuation_token": continuation_token,
                            "videos": video_ids
                        })

                    break

                except requests.exceptions.HTTPError as http_err:
                    print(f"HTTP error occurred: {http_err}")
                    attempts += 1
                except Exception as err:
                    print(f"Other error occurred: {err}")
                    attempts += 1

                if attempts >= max_attempts:
                    return jsonify({"error": "Maximum attempts reached, please try again later"}), 429

    return jsonify({"message": "No videos found for any query in any order"}), 404

@app.route('/youtube/comentarios', methods=['POST'])
def youtube_comentarios():
    RAPIDAPI_KEY = "c07b08be60msha21942a75c7f85bp180e93jsnac1f9d6be72f"
    RAPIDAPI_HOST = "youtube-v2.p.rapidapi.com"

    data = request.get_json()

    video_ids = data.get('videoIds', '').split(',')
    max_results = data.get('maxResults', 100)

    all_comments = []

    for video_id in video_ids:
        video_id = video_id.strip()

        url = f'https://{RAPIDAPI_HOST}/video/comments?video_id={video_id}'
        headers = {
            'x-rapidapi-host': RAPIDAPI_HOST,
            'x-rapidapi-key': RAPIDAPI_KEY
        }

        attempts = 0

        try:
            while attempts < 5:
                response = requests.get(url, headers=headers)
                response.raise_for_status()

                data = response.json()
                comments = data.get('comments', [])
                continuation_token = data.get('continuation_token', None)

                all_comments.extend(comments)

                if continuation_token is None or len(all_comments) >= max_results:
                    break

                url = f'https://{RAPIDAPI_HOST}/video/comments/continuation?video_id={video_id}&continuation_token={continuation_token}'

                time.sleep(5)
                attempts += 1

            return jsonify({
                "video_id": video_id,
                "total_number_of_comments": data.get("total_number_of_comments"),
                "number_of_comments": len(all_comments),
                "comments": [{"author": comment['author_name'], "text": comment['text']} for comment in all_comments]
            })

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")
            return jsonify({"error": "Failed to retrieve comments"}), 500
        except Exception as err:
            print(f"Other error occurred: {err}")
            return jsonify({"error": "An unexpected error occurred"}), 500

    return jsonify({"message": "No comments found for any video"}), 404

@app.route('/comments', methods=['POST'])
def get_comments():
    data = request.get_json()
    
    if 'videoIds' not in data or 'maxResults' not in data:
        return jsonify({"error": "Campos 'videoIds' e 'maxResults' são necessários"}), 400
    
    video_ids_str = data['videoIds']
    max_results = data['maxResults']
    
    video_ids = [video_id.strip() for video_id in video_ids_str.split(',')]
    
    all_comments = {}
    
    for video_id in video_ids:
        comments = check_comments(video_id, max_results)
        if comments:
            all_comments[video_id] = comments
    
    return jsonify(all_comments)

@app.route('/search_videos', methods=['POST'])
def search_videos_route():
    try:
        data = request.get_json()
        
        max_results = data.get('maxResults', 20)
        order = data.get('order', 'date')
        video_definition = data.get('videoDefinition', 'any')
        video_duration = data.get('videoDuration', 'any')
        region_code = data.get('regionCode', 'br')
        query = data.get('query', '')
        
        search_terms = query.split(',')
        
        all_video_ids = []
        
        for term in search_terms:
            term = term.strip()
            video_ids = search_videos(term, max_results, order, video_definition, video_duration, region_code)
            all_video_ids.extend(video_ids)
        
        return jsonify({"videoIds": all_video_ids}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/youtube-scrap', methods=['POST'])
def youtube_scrap():
    try:
        data = request.get_json()
        url = data.get("url", None)

        if not url:
            return jsonify({"error": "A URL do canal é obrigatória"}), 400

        driver = init_driver()
        driver.get(url)

        time.sleep(3)

        video_element = driver.find_element(By.CSS_SELECTOR, 'ytd-thumbnail a#thumbnail')
        video_url = 'https://www.youtube.com' + video_element.get_attribute('href')

        thumbnail_element = video_element.find_element(By.CSS_SELECTOR, 'img')
        thumbnail_url = thumbnail_element.get_attribute('src')

        title_element = driver.find_element(By.CSS_SELECTOR, 'h3 a#video-title-link yt-formatted-string')
        video_title = title_element.text

        driver.quit()

        return jsonify({
            "video_url": video_url,
            "thumbnail_url": thumbnail_url,
            "video_title": video_title
        }), 200

    except Exception as e:
        driver.quit()
        return jsonify({"error": str(e)}), 500

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

@app.route('/get-image', methods=['POST'])
def get_image():
    try:
        data = request.get_json()
        
        if 'image_url' not in data:
            return jsonify({"error": "A URL da imagem não foi fornecida no corpo da requisição."}), 400

        image_url = data['image_url']
        
        response = requests.get(image_url)
        
        if response.status_code != 200:
            return jsonify({"error": "Não foi possível obter a imagem."}), 400

        return send_file(BytesIO(response.content), mimetype='image/jpeg', as_attachment=False)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================================
# ROTAS ADICIONAIS DE WEB SCRAPING
# ================================

@app.route('/programacao-aracaju', methods=['POST'])
def programacao_aracaju():
    data = request.get_json()
    url = data.get("url")

    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Não foi possível acessar a página"}), 500

    soup = BeautifulSoup(response.text, 'html.parser')

    items = []
    program_list = soup.select('.container-programs ul.program-item li')
    for li in program_list:
        title_elem = li.select_one('.channel-program-item-title')
        start_time_elem = li.select_one('.container-hour .hour-program:first-child')
        end_time_elem = li.select_one('.container-hour .hour-program:last-child')

        if title_elem and start_time_elem and end_time_elem:
            title = title_elem.get_text(strip=True)
            start_time = start_time_elem.get_text(strip=True)
            end_time = end_time_elem.get_text(strip=True)
            items.append({"titulo": title, "horario": f"{start_time} - {end_time}"})
        else:
            print("Elemento não encontrado em um dos itens:", li)

    return jsonify(items)

@app.route('/programacao-aracaju-streaming', methods=['POST'])
def programacao_aracaju_streaming():
    data = request.get_json()
    url = data.get("url")

    response = requests.get(url)
    if response.status_code != 200:
        return jsonify({"error": "Não foi possível acessar a página"}), 500

    soup = BeautifulSoup(response.text, 'html.parser')

    streaming_now_item = soup.find('li', class_='cell-item streaming-now')

    if streaming_now_item:
        title_elem = streaming_now_item.find(class_='channel-program-item-title')
        start_time_elem = streaming_now_item.select_one('.container-hour .hour-program:first-child')
        end_time_elem = streaming_now_item.select_one('.container-hour .hour-program:last-child')

        if title_elem and start_time_elem and end_time_elem:
            title = title_elem.get_text(strip=True)
            start_time = start_time_elem.get_text(strip=True)
            end_time = end_time_elem.get_text(strip=True)
            streaming_now = {
                "titulo": title,
                "horario": f"{start_time} - {end_time}"
            }
            return jsonify({"streaming_now": streaming_now})
    
    return jsonify({"streaming_now": None})

# ================================
# ROTAS FINAIS E EXECUÇÃO
# ================================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
