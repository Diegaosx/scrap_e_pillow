import re
from base64 import b64decode
import boto3
import io
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from urllib.parse import urlparse, urljoin, quote, urlencode
from flask import Flask, request, jsonify, send_file, after_this_request
from bs4 import BeautifulSoup
import requests
import json
import random
import time
import os
import logging
from datetime import datetime
import tempfile
import shutil
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from io import BytesIO

app = Flask(__name__)
CORS(app)

# Rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100 per day", "30 per hour"]
)
limiter.init_app(app)

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurações
UPLOAD_FOLDER = 'uploads_pillow'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB max file size para processamento de imagens

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

# Funções auxiliares
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

# ================================
# ROTAS DE SAÚDE E INFORMAÇÕES
# ================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint para o serviço Pillow"""
    return jsonify({
        "status": "healthy",
        "service": "pillow-image-processing",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "features": [
            "image_processing", "text_overlay", "image_resize", 
            "format_conversion", "watermark", "thumbnail_generation",
            "cloud_storage_upload"
        ]
    })

# ================================
# ROTAS DE PROCESSAMENTO DE IMAGENS
# ================================

@app.route('/upload', methods=['POST'])
@limiter.limit("20 per minute")
def upload_file():
    """Upload de arquivo de imagem"""
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
@limiter.limit("30 per minute")
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
@limiter.limit("25 per minute")
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
@limiter.limit("20 per minute")
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
@limiter.limit("40 per minute")
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
@limiter.limit("15 per minute")
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
# ROTAS AVANÇADAS DO PILLOW
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
        
        # Processar textos (texto1 a texto5)
        for i in range(1, 6):
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
                    # Criar máscara circular
                    mask = Image.new('L', img2_size, 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse([0, 0, img2_size[0], img2_size[1]], fill=255)
                    
                    # Aplicar máscara
                    img2_with_alpha = img2.convert('RGBA')
                    img2_with_alpha.putalpha(mask)
                    
                    # Posição da segunda imagem
                    img2_position = tuple(data.get('imagem2_position', [0, 0]))
                    
                    # Colar imagem com transparência
                    img.paste(img2_with_alpha, img2_position, img2_with_alpha)
                else:
                    # Sem border radius, colar normalmente
                    img2_position = tuple(data.get('imagem2_position', [0, 0]))
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
    app.run(debug=True, host='0.0.0.0', port=5001)  # Porta 5001 para Pillow
