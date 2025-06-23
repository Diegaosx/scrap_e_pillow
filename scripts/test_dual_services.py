#!/usr/bin/env python3
"""
Script para testar os dois serviços Flask separados
"""

import requests
import json
import time

# URLs dos serviços
MAIN_SERVICE_URL = "http://localhost:5000"
PILLOW_SERVICE_URL = "http://localhost:5001"
NGINX_URL = "http://localhost"  # Através do nginx

def test_health_checks():
    """Testa os health checks de ambos os serviços"""
    print("🔍 Testando Health Checks...")
    
    # Teste direto do serviço principal
    try:
        response = requests.get(f"{MAIN_SERVICE_URL}/health")
        print(f"✅ Main Service Health: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Main Service Health Error: {e}")
    
    # Teste direto do serviço Pillow
    try:
        response = requests.get(f"{PILLOW_SERVICE_URL}/health")
        print(f"✅ Pillow Service Health: {response.status_code}")
        print(f"   Response: {response.json()}")
    except Exception as e:
        print(f"❌ Pillow Service Health Error: {e}")

def test_web_scraping():
    """Testa funcionalidade de web scraping (serviço principal)"""
    print("\n🌐 Testando Web Scraping...")
    
    test_data = {
        "url": "https://example.com"
    }
    
    try:
        response = requests.post(f"{MAIN_SERVICE_URL}/extract-links", json=test_data)
        print(f"✅ Web Scraping: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Links encontrados: {data.get('count', 0)}")
    except Exception as e:
        print(f"❌ Web Scraping Error: {e}")

def test_image_processing():
    """Testa funcionalidade de processamento de imagens (serviço Pillow)"""
    print("\n🖼️ Testando Processamento de Imagens...")
    
    # Teste de conversão base64 para upload
    test_data = {
        "base64_string": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "image_name": "test_image",
        "directory": "test"
    }
    
    try:
        response = requests.post(f"{PILLOW_SERVICE_URL}/convert_and_upload", json=test_data)
        print(f"✅ Image Processing: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Image URL: {data.get('file_url', 'N/A')}")
    except Exception as e:
        print(f"❌ Image Processing Error: {e}")

def test_nginx_routing():
    """Testa o roteamento através do nginx"""
    print("\n🔀 Testando Roteamento Nginx...")
    
    # Teste rota principal através do nginx
    try:
        response = requests.get(f"{NGINX_URL}/health")
        print(f"✅ Nginx -> Main Service: {response.status_code}")
    except Exception as e:
        print(f"❌ Nginx -> Main Service Error: {e}")
    
    # Teste rota Pillow através do nginx
    test_data = {
        "base64_string": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
        "image_name": "nginx_test",
        "directory": "nginx"
    }
    
    try:
        response = requests.post(f"{NGINX_URL}/convert_and_upload", json=test_data)
        print(f"✅ Nginx -> Pillow Service: {response.status_code}")
    except Exception as e:
        print(f"❌ Nginx -> Pillow Service Error: {e}")

def test_youtube_api():
    """Testa funcionalidade do YouTube API (serviço principal)"""
    print("\n📺 Testando YouTube API...")
    
    test_data = {
        "query": "python tutorial",
        "maxResults": 5
    }
    
    try:
        response = requests.post(f"{MAIN_SERVICE_URL}/search_videos", json=test_data)
        print(f"✅ YouTube API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   Videos encontrados: {len(data.get('videoIds', []))}")
    except Exception as e:
        print(f"❌ YouTube API Error: {e}")

def main():
    """Executa todos os testes"""
    print("🚀 Iniciando testes dos serviços Flask duais...\n")
    
    test_health_checks()
    test_web_scraping()
    test_image_processing()
    test_nginx_routing()
    test_youtube_api()
    
    print("\n✨ Testes concluídos!")
    print("\n📋 Resumo dos serviços:")
    print("   • Serviço Principal (Main): http://localhost:5000")
    print("   • Serviço Pillow: http://localhost:5001")
    print("   • Nginx (Load Balancer): http://localhost:80")
    print("\n🔧 Para iniciar os serviços:")
    print("   docker-compose -f docker-compose-dual.yml up -d")

if __name__ == "__main__":
    main()
