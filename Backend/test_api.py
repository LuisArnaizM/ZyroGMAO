#!/usr/bin/env python3
"""
Script para probar los endpoints de la API
"""
import sys
import urllib.request
import json

def test_endpoint(url, description):
    """Probar un endpoint de la API"""
    print(f"\n🔍 Probando: {description}")
    print(f"URL: {url}")
    
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
            result = json.loads(data.decode('utf-8'))
            print(f"✅ Status: {response.status}")
            print(f"📄 Response: {json.dumps(result, indent=2)}")
            return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

def main():
    base_url = "http://localhost:8001"
    
    # Lista de endpoints para probar
    endpoints = [
        ("/health", "Health Check"),
        ("/", "Root endpoint"),
        ("/api/v1/assets/", "Assets endpoint (sin autenticación - debería fallar)")
    ]
    
    print("🚀 Iniciando pruebas de API...")
    
    success_count = 0
    for endpoint, description in endpoints:
        if test_endpoint(f"{base_url}{endpoint}", description):
            success_count += 1
    
    print(f"\n📊 Resultados: {success_count}/{len(endpoints)} endpoints funcionando")

if __name__ == "__main__":
    main()
