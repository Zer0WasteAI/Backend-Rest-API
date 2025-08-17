#!/usr/bin/env python3
"""
🍽️ Test de Reconocimiento Simplificado de Comidas
===============================================

Este script prueba el nuevo endpoint /foods con el flujo simplificado:
1. Upload de imágenes → URLs firmadas
2. Reconocimiento de comidas → Respuesta inmediata con datos
3. Verificación de imágenes → Las imágenes se generan automáticamente en background

Uso: python3 test/food_recognition_simplified_test.py
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuración
BASE_URL = "http://localhost:5000/api"
AUTH_TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6IjAyNzdjNzZjNjQ1OGI4ZGRiZjQzMzNhNmJkNjlhM2U2NGI4OTNkYzQiLCJ0eXAiOiJKV1QifQ.eyJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vemVyby13YXN0ZS1haS0yMDI0IiwiYXVkIjoiemVyby13YXN0ZS1haS0yMDI0IiwiYXV0aF90aW1lIjoxNzM0NDE1MzI5LCJ1c2VyX2lkIjoiT1E3VEZzWXB4QVpCZk55THNsb1ZKWElteSIsInN1YiI6Ik9RN1RGc1lweEFaQmZOeUxzbG9WSlhJbXlSTTEiLCJpYXQiOjE3MzQ0MTUzMjksImV4cCI6MTczNDQxODkyOSwiZmlyZWJhc2UiOnsiaWRlbnRpdGllcyI6e30sInNpZ25faW5fcHJvdmlkZXIiOiJhbm9ueW1vdXMifX0.example"  # Token de prueba

def upload_image(image_path):
    """Upload una imagen y retorna la URL firmada"""
    print(f"📤 [UPLOAD] Uploading: {image_path}")
    
    url = f"{BASE_URL}/image_management/upload_image"
    headers = {"Authorization": AUTH_TOKEN}
    
    files = {
        'image': ('test_food.jpg', open(image_path, 'rb'), 'image/jpeg')
    }
    data = {
        'item_name': f'test_food_{int(time.time())}',
        'image_type': 'food'
    }
    
    try:
        response = requests.post(url, headers=headers, files=files, data=data)
        response.raise_for_status()
        
        result = response.json()
        image_url = result['image']['image_path']
        print(f"✅ [UPLOAD] Success: {image_url}")
        return image_url
        
    except requests.exceptions.RequestException as e:
        print(f"🚨 [UPLOAD] Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"🚨 [UPLOAD] Response: {e.response.text}")
        return None
    finally:
        files['image'][1].close()

def recognize_foods(image_urls):
    """Llamar al endpoint simplificado de reconocimiento de comidas"""
    print(f"🍽️ [FOODS] Starting recognition with {len(image_urls)} images")
    
    url = f"{BASE_URL}/recognition/foods"
    headers = {
        "Authorization": AUTH_TOKEN,
        "Content-Type": "application/json"
    }
    
    payload = {
        "images_paths": image_urls
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ [FOODS] Recognition successful!")
        print(f"📋 [FOODS] Recognition ID: {result.get('recognition_id')}")
        print(f"🍽️ [FOODS] Foods found: {len(result.get('foods', []))}")
        print(f"🎨 [FOODS] Images status: {result.get('images_status')}")
        print(f"💬 [FOODS] Message: {result.get('message')}")
        
        # Mostrar cada comida reconocida
        for i, food in enumerate(result.get('foods', []), 1):
            print(f"\n🍽️ [FOOD {i}] {food.get('name', 'Sin nombre')}")
            print(f"   📝 Description: {food.get('description', 'N/A')}")
            print(f"   🥗 Main ingredients: {food.get('main_ingredients', [])}")
            print(f"   🏷️ Category: {food.get('category', 'N/A')}")
            print(f"   🔥 Calories: {food.get('calories', 'N/A')}")
            print(f"   🏠 Storage: {food.get('storage_type', 'N/A')}")
            print(f"   ⏰ Expires: {food.get('expiration_date', 'N/A')}")
            print(f"   🖼️ Image: {food.get('image_path', 'Generating...')}")
            
            if food.get('allergy_alert'):
                print(f"   ⚠️ ALLERGY ALERT: {food.get('allergens', [])}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"🚨 [FOODS] Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"🚨 [FOODS] Response: {e.response.text}")
        return None

def check_images_status(recognition_id):
    """Verificar el estado de las imágenes (opcional)"""
    print(f"🎨 [IMAGES] Checking status for: {recognition_id}")
    
    url = f"{BASE_URL}/recognition/{recognition_id}/images"
    headers = {"Authorization": AUTH_TOKEN}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ [IMAGES] Status check successful!")
        print(f"🎨 [IMAGES] Status: {result.get('images_status')}")
        print(f"📊 [IMAGES] Progress: {result.get('progress_percentage', 0)}%")
        print(f"🖼️ [IMAGES] Ready: {result.get('images_ready', 0)}")
        print(f"⏳ [IMAGES] Generating: {result.get('images_generating', 0)}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"🚨 [IMAGES] Error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"🚨 [IMAGES] Response: {e.response.text}")
        return None

def main():
    print("🍽️ ===== TEST DE RECONOCIMIENTO SIMPLIFICADO DE COMIDAS =====")
    print()
    
    # 1. Buscar imágenes de prueba
    test_images_dir = Path("test/images/foods")
    if not test_images_dir.exists():
        print(f"❌ Directory not found: {test_images_dir}")
        print("💡 Tip: Create test/images/foods/ and add some food images")
        return
    
    image_files = list(test_images_dir.glob("*.jpg")) + list(test_images_dir.glob("*.jpeg")) + list(test_images_dir.glob("*.png"))
    
    if not image_files:
        print(f"❌ No images found in: {test_images_dir}")
        print("💡 Tip: Add some .jpg, .jpeg, or .png files to test/images/foods/")
        return
    
    # Usar máximo 3 imágenes para el test
    selected_images = image_files[:3]
    print(f"📸 Found {len(image_files)} images, using {len(selected_images)} for test:")
    for img in selected_images:
        print(f"   - {img.name}")
    print()
    
    # 2. Upload de imágenes
    print("📤 ===== STEP 1: UPLOADING IMAGES =====")
    image_urls = []
    
    for image_path in selected_images:
        url = upload_image(image_path)
        if url:
            image_urls.append(url)
        else:
            print(f"❌ Failed to upload: {image_path}")
    
    if not image_urls:
        print("❌ No images uploaded successfully. Exiting.")
        return
    
    print(f"✅ Successfully uploaded {len(image_urls)} images")
    print()
    
    # 3. Reconocimiento de comidas (simplificado)
    print("🍽️ ===== STEP 2: SIMPLIFIED FOOD RECOGNITION =====")
    recognition_result = recognize_foods(image_urls)
    
    if not recognition_result:
        print("❌ Food recognition failed. Exiting.")
        return
    
    recognition_id = recognition_result.get('recognition_id')
    print()
    
    # 4. Verificar estado de imágenes (opcional)
    if recognition_id:
        print("🎨 ===== STEP 3: CHECKING IMAGES STATUS (OPTIONAL) =====")
        print("⏳ Waiting 10 seconds for image generation to start...")
        time.sleep(10)
        
        for attempt in range(6):  # Check por 30 segundos máximo
            print(f"\n🔍 [ATTEMPT {attempt + 1}/6] Checking images status...")
            status_result = check_images_status(recognition_id)
            
            if status_result and status_result.get('images_status') == 'ready':
                print("🎉 All images are ready!")
                print("\n🖼️ Updated foods with images:")
                for i, food in enumerate(status_result.get('foods', []), 1):
                    print(f"   {i}. {food.get('name')}: {food.get('image_path', 'No image')}")
                break
            elif status_result:
                progress = status_result.get('progress_percentage', 0)
                print(f"⏳ Still generating... ({progress}% complete)")
                if attempt < 5:  # No wait on last attempt
                    print("   Waiting 5 seconds before next check...")
                    time.sleep(5)
            else:
                print("❌ Failed to check status")
                break
    
    print("\n🎉 ===== TEST COMPLETED =====")
    print("✅ Simplified food recognition flow tested successfully!")
    print("🎨 Images are being generated automatically in background")
    print("📱 Frontend would show immediate results and optionally poll for images")

if __name__ == "__main__":
    main() 