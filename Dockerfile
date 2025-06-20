# Multi-stage build para otimizar o tamanho da imagem
FROM python:3.11-slim as builder

# Instalar dependências do sistema necessárias para compilação
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Criar ambiente virtual
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Estágio final
FROM python:3.11-slim

# Instalar dependências do sistema para runtime
RUN apt-get update && apt-get install -y \
    # Para Selenium
    chromium \
    chromium-driver \
    # Para processamento de imagem
    libgl1-mesa-glx \
    libglib2.0-0 \
    # Para fontes
    fonts-dejavu-core \
    # Para ffmpeg (áudio)
    ffmpeg \
    # Limpeza
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copiar ambiente virtual do builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app
USER app
WORKDIR /home/app

# Copiar código da aplicação
COPY --chown=app:app . .

# Criar diretórios necessários
RUN mkdir -p uploads temp logs

# Variáveis de ambiente
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/home/app
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Expor porta
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Comando para iniciar a aplicação
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100", "app:app"]
