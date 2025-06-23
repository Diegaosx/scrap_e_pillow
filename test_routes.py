"""
Script para testar as principais rotas da API
"""

import requests
import json

def test_api_routes(base_url="http://localhost:5000"):
    """Testa as principais rotas da API"""
    
    print(f"🧪 Testando API em: {base_url}")
    print("=" * 50)
    
    # Teste 1: Health Check
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✅ Health Check: OK")
            data = response.json()
            print(f"   Status: {data.get('status')}")
            print(f"   Versão: {data.get('version')}")
        else:
            print(f"❌ Health Check: Falhou ({response.status_code})")
    except Exception as e:
        print(f"❌ Health Check: Erro - {e}")
    
    # Teste 2: Página inicial
    try:
        response = requests.get(f"{base_url}/home")
        if response.status_code == 200:
            print("✅ Página inicial: OK")
        else:
            print(f"❌ Página inicial: Falhou ({response.status_code})")
    except Exception as e:
        print(f"❌ Página inicial: Erro - {e}")
    
    # Teste 3: Documentação Swagger
    try:
        response = requests.get(f"{base_url}/swagger.json")
        if response.status_code == 200:
            print("✅ Swagger JSON: OK")
        else:
            print(f"❌ Swagger JSON: Falhou ({response.status_code})")
    except Exception as e:
        print(f"❌ Swagger JSON: Erro - {e}")
    
    # Teste 4: Web Scraping básico
    try:
        payload = {
            "url": "https://httpbin.org/html",
            "selector": "h1"
        }
        response = requests.post(f"{base_url}/scrape", json=payload)
        if response.status_code == 200:
            print("✅ Web Scraping: OK")
        else:
            print(f"❌ Web Scraping: Falhou ({response.status_code})")
    except Exception as e:
        print(f"❌ Web Scraping: Erro - {e}")
    
    print("=" * 50)
    print("🎉 Testes concluídos!")

if __name__ == "__main__":
    # Teste local
    test_api_routes("http://localhost:5000")
    
    # Teste no seu domínio (substitua pela sua URL)
    # test_api_routes("https://seu-dominio.com")
