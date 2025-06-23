import re
from base64 import b64decode
import boto3
import io
from urllib.parse import urlparse, urljoin, quote, urlencode
from flask import Flask, request, jsonify, send_file, render_template, redirect
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
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
limiter.init_app(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads_main'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp', 'mp3', 'wav', 'ogg'}
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
def complete_url(base_url, link):
    """Completa URLs relativas e corrige links baseados no domínio."""
    if link.startswith("http"):
        return link
    elif link.startswith("//"):
        return 'https:' + link
    else:
        return urljoin(base_url, link)

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

# ================================
# ROTAS DE SAÚDE E INFORMAÇÕES
# ================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint para o serviço principal"""
    return jsonify({
        "status": "healthy",
        "service": "main-api-services",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0",
        "features": [
            "web_scraping", "telegram_bot", "youtube_api", 
            "text_to_speech", "chart_generation", "cloud_storage",
            "face_detection", "screenshot_capture"
        ],
        "pillow_service": "http://localhost:5001"
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
# ROTAS DE WEB SCRAPING
# ================================

@app.route('/scrape_website', methods=['POST'])
def scrape_website():
    data = request.json
    url = data.get('url', '')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36 Edge/102.0.0.0'
    }

    try:
        with requests.Session() as s:
            s.headers.update(headers)
            response = s.get(url)
        
        soup = BeautifulSoup(response.text, 'html.parser')

        # Obtendo apenas a parte do protocolo e domínio da URL
        parsed_url = urlparse(url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        if 'moneytimes.com.br' in url:
            news_items = soup.find_all('div', class_='news-item')
            for news_item in news_items:
                links = news_item.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    if not href.startswith(('http', 'https')):
                        href = base_url + href
                    return jsonify({"link": href})  # Retorne o primeiro link encontrado
        
        else:
            parent_tag = data.get('parent_tag', '')
            parent_class = data.get('parent_class', '')
            link_tag = data.get('link', 'a')  # Default to 'a' tag if not specified
            if parent_tag and parent_class:
                parents = soup.find_all(parent_tag, class_=parent_class)
            else:
                parents = [soup]

            for parent in parents:
                element = parent.find(link_tag, href=True)
                if element:
                    link = element.get('href', 'Href not found')
                    if not link.startswith(('http', 'https')):
                        link = base_url + link
                    return jsonify({"link": link})  # Retorne o primeiro link encontrado
        
        return jsonify({"error": "Link not found"}), 404  # Retorne um erro se nenhum link for encontrado

    except Exception as e:
        return jsonify({"error": str(e)}), 400

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

# ================================
# ROTAS DE ÁUDIO E TTS
# ================================

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

# Importar configurações do Swagger
try:
    import swagger_docs
except ImportError:
    print("Swagger docs não disponível")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # Porta 5000 para serviços principais
