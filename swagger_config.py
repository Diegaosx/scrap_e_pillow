"""
Configuração do Swagger/OpenAPI para documentação automática das rotas
"""

from flask_restx import fields

# Modelos para documentação
image_processing_model = {
    'url': fields.String(required=True, description='URL da imagem a ser processada'),
    'titulo': fields.String(required=True, description='Título a ser adicionado'),
    'titulo_position': fields.List(fields.Integer, description='Posição do título [x, y]'),
    'data': fields.String(description='Data a ser adicionada'),
    'data_position': fields.List(fields.Integer, description='Posição da data [x, y]'),
    'orcamento': fields.String(description='Orçamento a ser adicionado'),
    'orcamento_position': fields.List(fields.Integer, description='Posição do orçamento [x, y]'),
    'categoria': fields.String(description='Categoria a ser adicionada'),
    'categoria_position': fields.List(fields.Integer, description='Posição da categoria [x, y]'),
    'image_name': fields.String(description='Nome do arquivo de saída', default='processed_image.jpg')
}

web_scraping_model = {
    'url': fields.String(required=True, description='URL do site a ser analisado'),
    'selector': fields.String(description='Seletor CSS para extrair elementos', default='title'),
    'conteudo': fields.String(description='Classe CSS do conteúdo específico')
}

youtube_search_model = {
    'query': fields.String(required=True, description='Termo de busca (separar múltiplos por vírgula)'),
    'maxResults': fields.Integer(description='Número máximo de resultados', default=20),
    'order': fields.String(description='Ordenação dos resultados', default='date'),
    'regionCode': fields.String(description='Código da região', default='br')
}

telegram_model = {
    'chat_id': fields.String(description='ID do chat/grupo'),
    'message': fields.String(description='Mensagem a ser enviada')
}

chart_model = [
    {
        'total_last_7_days': fields.Float(required=True, description='Total dos últimos 7 dias'),
        'total_previous_7_days': fields.Float(required=True, description='Total dos 7 dias anteriores')
    },
    {
        'total_last_15_days': fields.Float(required=True, description='Total dos últimos 15 dias'),
        'total_previous_15_days': fields.Float(required=True, description='Total dos 15 dias anteriores')
    },
    {
        'total_last_30_days': fields.Float(required=True, description='Total dos últimos 30 dias'),
        'total_previous_30_days': fields.Float(required=True, description='Total dos 30 dias anteriores')
    }
]

cloud_upload_model = {
    'base64_string': fields.String(required=True, description='String base64 da imagem'),
    'image_name': fields.String(required=True, description='Nome da imagem'),
    'directory': fields.String(description='Diretório de destino', default='uploads')
}

audio_processing_model = {
    'media_url': fields.String(required=True, description='URL do arquivo de áudio criptografado'),
    'media_key': fields.String(required=True, description='Chave de descriptografia em base64')
}

tts_model = {
    'text': fields.String(required=True, description='Texto para conversão em áudio'),
    'voice': fields.String(description='Voz a ser utilizada', default='pt-BR-Antonio'),
    'filename': fields.String(description='Nome do arquivo de saída', default='narracao')
}

# Respostas padrão
success_response = {
    'message': fields.String(description='Mensagem de sucesso'),
    'data': fields.Raw(description='Dados retornados')
}

error_response = {
    'error': fields.String(description='Mensagem de erro'),
    'code': fields.Integer(description='Código do erro')
}

health_response = {
    'status': fields.String(description='Status da API'),
    'timestamp': fields.String(description='Timestamp da verificação'),
    'version': fields.String(description='Versão da API'),
    'features': fields.List(fields.String, description='Funcionalidades disponíveis')
}
