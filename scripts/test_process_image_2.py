#!/usr/bin/env python3
"""
Teste específico para a nova rota /process-image-2
"""

import requests
import json

def test_process_image_2():
    """Testa a nova rota /process-image-2"""
    
    BASE_URL = "http://localhost:5000"
    
    # Payload de teste baseado no exemplo fornecido
    payload = {
        "url": "https://s3.diegao.com.br/redegram/following.png",
        "image_name": "perfil-56976.jpg",
        "texto1": "sbt",
        "texto1_position": [120, 20],
        "texto1_font_size": 14,
        "texto1_max_chars": 38,
        "texto1_color": "#000000",
        "texto2": "34221",
        "texto2_position": [153, 93],
        "texto2_font_size": 15,
        "texto2_max_chars": 10,
        "texto2_color": "#000000",
        "texto3": "14063485",
        "texto3_position": [237, 93],
        "texto3_font_size": 15,
        "texto3_max_chars": 10,
        "texto3_color": "#000000",
        "texto4": "313",
        "texto4_position": [333, 93],
        "texto4_font_size": 15,
        "texto4_max_chars": 10,
        "texto4_color": "#000000",
        "texto5": "Bem-vindo ao perfil oficial do SBT.",
        "texto5_position": [30, 200],
        "texto5_font_size": 15,
        "texto5_max_chars": 100,
        "texto5_color": "#000000",
        "imagem2_url": "https://s3.diegao.com.br/redegram/foto-perfil-56976.webp",
        "imagem2_size": [80, 80],
        "imagem2_position": [18, 65],
        "imagem2_border_radius": 200
    }
    
    print("🧪 Testando rota /process-image-2...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/process-image-2", 
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ Rota /process-image-2 funcionando!")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print(f"   Tamanho da resposta: {len(response.content)} bytes")
            
            # Salvar imagem de teste
            with open("test_output.jpg", "wb") as f:
                f.write(response.content)
            print("   Imagem salva como: test_output.jpg")
            
            return True
        else:
            print(f"❌ Erro na rota /process-image-2: {response.status_code}")
            print(f"   Resposta: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar /process-image-2: {e}")
        return False

def test_swagger():
    """Testa se o Swagger está funcionando"""
    
    BASE_URL = "http://localhost:5000"
    
    print("🧪 Testando Swagger...")
    
    try:
        # Testar swagger.json
        response = requests.get(f"{BASE_URL}/swagger.json")
        if response.status_code == 200:
            print("✅ Swagger JSON funcionando!")
            data = response.json()
            print(f"   Título: {data.get('info', {}).get('title')}")
            print(f"   Versão: {data.get('info', {}).get('version')}")
            print(f"   Rotas disponíveis: {len(data.get('paths', {}))}")
        else:
            print(f"❌ Erro no Swagger JSON: {response.status_code}")
            return False
        
        # Testar interface Swagger
        response = requests.get(f"{BASE_URL}/docs")
        if response.status_code == 200:
            print("✅ Interface Swagger funcionando!")
            print("   Acesse: http://localhost:5000/docs")
        else:
            print(f"❌ Erro na interface Swagger: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Erro ao testar Swagger: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testando novas funcionalidades...\n")
    
    swagger_ok = test_swagger()
    print()
    
    process_image_2_ok = test_process_image_2()
    print()
    
    if swagger_ok and process_image_2_ok:
        print("🎉 Todos os testes passaram!")
    else:
        print("⚠️ Alguns testes falharam. Verifique os logs.")
