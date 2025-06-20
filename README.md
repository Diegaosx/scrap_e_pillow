# 🚀 Flask Super API - Repositório Unificado

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![API Routes](https://img.shields.io/badge/API%20Routes-129+-red.svg)](#rotas-disponíveis)

> **O repositório Flask mais completo do Brasil!** 🇧🇷

Uma API unificada com **129+ rotas** que combina processamento de imagens, web scraping, integração com Telegram, YouTube, geração de gráficos, processamento de áudio e muito mais!

## 📋 Índice

- [🌟 Características](#-características)
- [🚀 Quick Start](#-quick-start)
- [📊 Rotas Disponíveis](#-rotas-disponíveis)
- [🛠️ Instalação](#️-instalação)
- [🐳 Docker](#-docker)
- [📖 Documentação](#-documentação)
- [🔧 Configuração](#-configuração)
- [🧪 Testes](#-testes)
- [🤝 Contribuição](#-contribuição)

## 🌟 Características

### 🎨 **Processamento de Imagens Avançado**
- ✅ Redimensionamento inteligente sem distorção
- ✅ Adição de texto com fontes personalizadas
- ✅ Marcas d'água e sobreposições
- ✅ Conversão entre formatos (JPEG, PNG, WebP, GIF)
- ✅ Detecção facial com AWS Rekognition
- ✅ Análise de gênero com DeepFace
- ✅ Screenshots automatizados com Selenium

### 🕷️ **Web Scraping Massivo**
- ✅ **100+ sites** pré-configurados
- ✅ Sites de notícias brasileiros (G1, UOL, Estadão, R7)
- ✅ Sites internacionais (CNN, NYTimes, ESPN)
- ✅ Selenium para sites dinâmicos
- ✅ Extração de metadados e JSON-LD
- ✅ APIs de terceiros integradas
- ✅ Rate limiting inteligente

### 📱 **Integração Telegram Completa**
- ✅ Gerenciamento de grupos e canais
- ✅ Detecção automática de admin
- ✅ Cache inteligente de grupos
- ✅ Suporte a Telethon e python-telegram-bot
- ✅ Envio de mensagens e mídia

### 📺 **YouTube API Avançada**
- ✅ Busca de vídeos com filtros
- ✅ Extração de comentários
- ✅ Scraping de canais
- ✅ Múltiplas APIs (RapidAPI)
- ✅ Análise de tendências

### 📊 **Gráficos e Visualizações**
- ✅ Gráficos de barras, linhas e pizza
- ✅ Matplotlib integrado
- ✅ Exportação em base64
- ✅ Dados financeiros e estatísticos

### 🎵 **Processamento de Áudio**
- ✅ Text-to-Speech (Google Cloud)
- ✅ Conversão de formatos de áudio
- ✅ Descriptografia de mídia WhatsApp
- ✅ Processamento com FFmpeg

### ☁️ **Cloud Storage**
- ✅ AWS S3 integrado
- ✅ Cloudflare R2 suportado
- ✅ Conversão automática para WebP
- ✅ URLs públicas automáticas

### 🔒 **Recursos de Produção**
- ✅ Rate limiting configurável
- ✅ CORS habilitado
- ✅ Logs estruturados
- ✅ Health checks
- ✅ Docker multi-stage otimizado
- ✅ Nginx como reverse proxy
- ✅ Redis para cache
- ✅ Usuário não-root no Docker

## 🚀 Quick Start

### Opção 1: Docker (Recomendado)

\`\`\`bash
# Clonar o repositório
git clone https://github.com/seu-usuario/flask-super-api.git
cd flask-super-api

# Executar com Docker Compose
docker-compose up -d

# A API estará disponível em http://localhost:5000
\`\`\`

### Opção 2: Instalação Local

\`\`\`bash
# Clonar o repositório
git clone https://github.com/seu-usuario/flask-super-api.git
cd flask-super-api

# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Executar a aplicação
python app.py
\`\`\`

### Teste Rápido

\`\`\`bash
# Verificar se a API está funcionando
curl http://localhost:5000/health

# Resposta esperada:
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "version": "2.0.0",
  "features": ["image_processing", "web_scraping", "telegram_bot", ...]
}
\`\`\`

## 📊 Rotas Disponíveis

### 🏥 **Saúde e Informações (2 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/health` | GET | Health check da API |
| `/home` | GET | Página inicial com interface |

### 📤 **Upload e Processamento Básico (6 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/upload` | POST | Upload básico de arquivos |
| `/resize` | POST | Redimensionamento básico |
| `/add-text` | POST | Adicionar texto à imagem |
| `/convert` | POST | Converter formato de imagem |
| `/thumbnail` | POST | Criar thumbnail |
| `/watermark` | POST | Adicionar marca d'água |

### 🎨 **Processamento Avançado Pillow (13 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/process-image` | POST | Processamento completo |
| `/imagem-com-imagem` | POST | Combinar imagens |
| `/centralizado` | POST | Texto centralizado |
| `/resize-image` | POST | Redimensionar com fundo |
| `/resize-image-novo` | POST | Suporte a GIF |
| `/sem-distorcer-imagem` | POST | Redimensionar sem distorção |
| `/detect-gender` | POST | Detecção de gênero |
| `/screenshot` | GET | Screenshot automatizado |
| `/crop-center` | POST | Corte centralizado |
| `/analyze-image` | POST | Análise AWS Rekognition |
| ... | ... | ... |

### 🕷️ **Web Scraping (90+ rotas)**
| Categoria | Rotas | Exemplos |
|-----------|-------|----------|
| **Genérico** | 3 | `/scrape`, `/extract-links` |
| **Notícias BR** | 30+ | `/g1-esporte`, `/uol-title`, `/estadao` |
| **Internacional** | 20+ | `/info-nytimes`, `/cnn-image`, `/espn-titulo` |
| **Programação TV** | 5+ | `/programacao-aracaju` |
| **APIs Específicas** | 15+ | `/scrape_with_api` |
| **Keywords/SEO** | 10+ | `/busca-links-keywords` |
| **Workana** | 2 | `/workana-projects` |

### 📱 **Telegram (3 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/grupos-admin` | GET | Listar grupos admin |
| `/force-update` | GET | Limpar updates |
| `/teste-conexao` | GET | Testar conexão |

### 📺 **YouTube (6 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/youtube/procura_videos` | POST | Buscar vídeos |
| `/youtube/comentarios` | POST | Extrair comentários |
| `/search_videos` | POST | Busca alternativa |
| `/comments` | POST | Comentários múltiplos |
| `/youtube-scrap` | POST | Scraping de canal |

### 📊 **Gráficos (2 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/generate_chart2` | POST | Gráficos locais |
| `/generate_chart` | POST | Gráficos via API |

### 🎵 **Áudio/TTS (2 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/process_audio` | POST | Processar áudio |
| `/narracao` | POST | Text-to-Speech |

### ☁️ **Cloud Storage (3 rotas)**
| Rota | Método | Descrição |
|------|--------|-----------|
| `/convert_and_upload` | POST | Upload para S3/R2 |
| `/get-image` | POST | Obter imagem via URL |

## 🛠️ Instalação

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose (opcional)
- Redis (opcional, para cache)
- Chrome/Chromium (para Selenium)

### Dependências Principais

\`\`\`txt
Flask==2.3.3
Pillow==10.0.1
requests==2.31.0
beautifulsoup4==4.12.2
selenium==4.15.2
boto3==1.29.7
python-telegram-bot==20.6
matplotlib==3.8.2
\`\`\`

### Instalação Completa

\`\`\`bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/flask-super-api.git
cd flask-super-api

# 2. Instalar dependências do sistema (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y chromium-browser chromium-chromedriver ffmpeg

# 3. Criar ambiente virtual
python -m venv venv
source venv/bin/activate

# 4. Instalar dependências Python
pip install -r requirements.txt

# 5. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas configurações

# 6. Executar
python app.py
\`\`\`

## 🐳 Docker

### Docker Compose (Recomendado)

\`\`\`yaml
version: '3.8'
services:
  flask-super-api:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
    volumes:
      - ./uploads:/home/app/uploads
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - flask-super-api

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
\`\`\`

### Comandos Docker

\`\`\`bash
# Construir e executar
docker-compose up -d

# Ver logs
docker-compose logs -f flask-super-api

# Parar serviços
docker-compose down

# Rebuild
docker-compose up -d --build
\`\`\`

## 📖 Documentação

### Swagger UI
Acesse a documentação interativa em: **http://localhost:5000/docs/**

### Exemplos de Uso

#### 1. Processamento de Imagem
\`\`\`bash
curl -X POST http://localhost:5000/process-image \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/image.jpg",
    "titulo": "Meu Título",
    "titulo_position": [50, 50],
    "data": "2024-01-15",
    "data_position": [50, 100]
  }'
\`\`\`

#### 2. Web Scraping
\`\`\`bash
curl -X POST http://localhost:5000/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "selector": "h1"
  }'
\`\`\`

#### 3. Upload para Cloud
\`\`\`bash
curl -X POST http://localhost:5000/convert_and_upload \
  -H "Content-Type: application/json" \
  -d '{
    "base64_string": "data:image/jpeg;base64,/9j/4AAQ...",
    "image_name": "minha_imagem",
    "directory": "uploads"
  }'
\`\`\`

## 🔧 Configuração

### Variáveis de Ambiente

Crie um arquivo `.env` baseado no `.env.example`:

\`\`\`env
# Flask
FLASK_ENV=production
SECRET_KEY=sua-chave-secreta-aqui

# AWS/Cloudflare R2
S3_BUCKET=seu-bucket
S3_ENDPOINT_URL=https://seu-endpoint.r2.cloudflarestorage.com
S3_ACCESS_KEY=sua-access-key
S3_SECRET_KEY=sua-secret-key

# Telegram
BOT_TOKEN=seu-bot-token

# YouTube
YOUTUBE_API_KEY=sua-api-key

# RapidAPI
RAPIDAPI_KEY=sua-rapidapi-key

# Redis (opcional)
REDIS_URL=redis://localhost:6379/0
\`\`\`

### Rate Limiting

A API inclui rate limiting configurado:

```python
# Limites padrão
"200 per day", "50 per hour"

# Rotas específicas
"/upload": "10 per minute"
"/scrape": "30 per minute"
