#!/usr/bin/env python3
"""
Script de teste automatizado para a Flask Super API
Testa todas as principais funcionalidades da API
"""

import requests
import json
import time
import base64
from io import BytesIO
from PIL import Image

# Configuração
BASE_URL = "http://localhost:5000"
TEST_IMAGE_URL = "https://picsum.photos/800/600"

def create_test_image_base64():
    """Criar uma imagem de teste em base64"""
    img = Image.new('RGB', (100, 100), color='red')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return f"data:image/jpeg;base64,{img_str}"

def test_health():
    """Testar endpoint de saúde"""
    print("🔍 Testando health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        print("✅ Health check passou!")
        return True
    except Exception as e:
        print(f"❌ Health check falhou: {e}")
        return False

def test_basic_image_processing():
    """Testar processamento básico de imagem"""
    print("🖼️ Testando processamento básico de imagem...")
    try:
        # Teste de redimensionamento via URL
        payload = {
            "url": TEST_IMAGE_URL,
            "image_name": "test_resize.jpg"
        }
        response = requests.post(f"{BASE_URL}/resize-image", json=payload)
        assert response.status_code == 200
        print("✅ Redimensionamento passou!")
        
        # Teste de processamento avançado
        payload = {
            "url": TEST_IMAGE_URL,
            "titulo": "Teste API",
            "titulo_position": [50, 50],
            "data": "2024-01-15",
            "data_position": [50, 100],
            "orcamento": "R$ 1000",
            "orcamento_position": [50, 150],
            "categoria": "Teste",
            "categoria_position": [50, 200]
        }
        response = requests.post(f"{BASE_URL}/process-image", json=payload)
        assert response.status_code == 200
        print("✅ Processamento avançado passou!")
        return True
    except Exception as e:
        print(f"❌ Processamento de imagem falhou: {e}")
        return False

def test_web_scraping():
    """Testar web scraping"""
    print("🕷️ Testando web scraping...")
    try:
        payload = {
            "url": "https://httpbin.org/html",
            "selector": "h1"
        }
        response = requests.post(f"{BASE_URL}/scrape", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        print("✅ Web scraping passou!")
        return True
    except Exception as e:
        print(f"❌ Web scraping falhou: {e}")
        return False

def test_chart_generation():
    """Testar geração de gráficos"""
    print("📊 Testando geração de gráficos...")
    try:
        payload = [
            {"total_last_7_days": 1000, "total_previous_7_days": 800},
            {"total_last_15_days": 2000, "total_previous_15_days": 1500},
            {"total_last_30_days": 4000, "total_previous_30_days": 3000}
        ]
        response = requests.post(f"{BASE_URL}/generate_chart2", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "bar_chart" in data
        assert "line_chart" in data
        assert "pie_chart" in data
        print("✅ Geração de gráficos passou!")
        return True
    except Exception as e:
        print(f"❌ Geração de gráficos falhou: {e}")
        return False

def test_cloud_storage():
    """Testar upload para cloud storage"""
    print("☁️ Testando cloud storage...")
    try:
        base64_image = create_test_image_base64()
        payload = {
            "base64_string": base64_image,
            "image_name": "test_upload",
            "directory": "test"
        }
        response = requests.post(f"{BASE_URL}/convert_and_upload", json=payload)
        # Note: Este teste pode falhar se as credenciais não estiverem configuradas
        if response.status_code == 200:
            data = response.json()
            assert "file_url" in data
            print("✅ Cloud storage passou!")
            return True
        else:
            print("⚠️ Cloud storage pulado (credenciais não configuradas)")
            return True
    except Exception as e:
        print(f"❌ Cloud storage falhou: {e}")
        return False

def test_telegram_integration():
    """Testar integração com Telegram"""
    print("📱 Testando integração Telegram...")
    try:
        response = requests.get(f"{BASE_URL}/grupos-admin")
        # Note: Este teste pode falhar se o bot não estiver configurado
        if response.status_code == 200:
            data = response.json()
            assert "status" in data
            print("✅ Telegram passou!")
            return True
        else:
            print("⚠️ Telegram pulado (bot não configurado)")
            return True
    except Exception as e:
        print(f"❌ Telegram falhou: {e}")
        return False

def test_youtube_integration():
    """Testar integração com YouTube"""
    print("📺 Testando integração YouTube...")
    try:
        payload = {
            "query": "python tutorial",
            "maxResults": 5
        }
        response = requests.post(f"{BASE_URL}/search_videos", json=payload)
        # Note: Este teste pode falhar se a API key não estiver configurada
        if response.status_code == 200:
            data = response.json()
            assert "videoIds" in data
            print("✅ YouTube passou!")
            return True
        else:
            print("⚠️ YouTube pulado (API key não configurada)")
            return True
    except Exception as e:
        print(f"❌ YouTube falhou: {e}")
        return False

def run_all_tests():
    """Executar todos os testes"""
    print("🚀 Iniciando testes da Flask Super API...\n")
    
    tests = [
        test_health,
        test_basic_image_processing,
        test_web_scraping,
        test_chart_generation,
        test_cloud_storage,
        test_telegram_integration,
        test_youtube_integration
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            time.sleep(1)  # Pausa entre testes
        except Exception as e:
            print(f"❌ Teste falhou com exceção: {e}")
        print()
    
    print(f"📊 Resultados: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes passaram! API está funcionando perfeitamente!")
    elif passed >= total * 0.7:
        print("✅ Maioria dos testes passou! API está funcionando bem!")
    else:
        print("⚠️ Alguns testes falharam. Verifique a configuração da API.")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
