"""
Configuração do Swagger para documentação da API
"""

from flask import jsonify
from app import app

@app.route('/swagger.json', methods=['GET'])
def swagger_spec():
    """Especificação OpenAPI/Swagger da API"""
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Flask Super API",
            "description": "API unificada com 129+ rotas para processamento de imagens, web scraping, Telegram, YouTube e muito mais",
            "version": "2.0.0",
            "contact": {
                "name": "Flask Super API",
                "url": "https://github.com/seu-usuario/flask-super-api"
            }
        },
        "servers": [
            {
                "url": "/",
                "description": "Servidor atual"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "summary": "Health Check",
                    "description": "Verifica o status da API",
                    "responses": {
                        "200": {
                            "description": "API funcionando",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string"},
                                            "timestamp": {"type": "string"},
                                            "version": {"type": "string"},
                                            "features": {
                                                "type": "array",
                                                "items": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/upload": {
                "post": {
                    "summary": "Upload de arquivo",
                    "description": "Faz upload de um arquivo de imagem",
                    "requestBody": {
                        "content": {
                            "multipart/form-data": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "file": {
                                            "type": "string",
                                            "format": "binary"
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Upload realizado com sucesso"
                        }
                    }
                }
            },
            "/process-image": {
                "post": {
                    "summary": "Processar imagem",
                    "description": "Processa uma imagem adicionando texto e elementos",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string"},
                                        "titulo": {"type": "string"},
                                        "titulo_position": {
                                            "type": "array",
                                            "items": {"type": "integer"}
                                        },
                                        "data": {"type": "string"},
                                        "data_position": {
                                            "type": "array", 
                                            "items": {"type": "integer"}
                                        }
                                    },
                                    "required": ["url", "titulo", "titulo_position"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Imagem processada com sucesso"
                        }
                    }
                }
            },
            "/scrape": {
                "post": {
                    "summary": "Web Scraping",
                    "description": "Extrai dados de uma página web",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "url": {"type": "string"},
                                        "selector": {"type": "string"}
                                    },
                                    "required": ["url"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Dados extraídos com sucesso"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "Error": {
                    "type": "object",
                    "properties": {
                        "error": {"type": "string"}
                    }
                }
            }
        }
    }
    
    return jsonify(spec)

@app.route('/docs', methods=['GET'])
def swagger_ui():
    """Interface Swagger UI"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Flask Super API - Documentação</title>
        <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui.css" />
        <style>
            .swagger-ui .topbar { 
                background-color: #667eea; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            .swagger-ui .topbar .download-url-wrapper { display: none; }
            .swagger-ui .info .title { color: #333; }
        </style>
    </head>
    <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@3.25.0/swagger-ui-bundle.js"></script>
        <script>
            SwaggerUIBundle({
                url: '/swagger.json',
                dom_id: '#swagger-ui',
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                layout: "BaseLayout",
                deepLinking: true,
                showExtensions: true,
                showCommonExtensions: true
            });
        </script>
    </body>
    </html>
    '''
