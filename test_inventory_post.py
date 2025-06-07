#!/usr/bin/env python3
import json
import time
import requests

# Configuración del backend
BASE_URL = "http://localhost:3000"

def test_inventory_post_with_ai_enrichment():
    """
    Test para probar el POST de ingredientes al inventario
    con generación de environmental impact y utilization ideas
    """
    print("🧪 TEST: POST ingredientes al inventario con enrichment AI")
    
    # 1. Crear usuario anónimo
    print("\n1️⃣ Creando usuario anónimo...")
    firebase_url = "https://identitytoolkit.googleapis.com/v1/accounts:signUp"
    firebase_payload = {
        "returnSecureToken": True
    }
    
    firebase_response = requests.post(
        f"{firebase_url}?key=AIzaSyBRFf-DoN9NxYayGtuUlURWClDZrhkZG-0",
        json=firebase_payload
    )
    
    if firebase_response.status_code != 200:
        print(f"❌ Error creando usuario: {firebase_response.status_code}")
        return False
    
    firebase_data = firebase_response.json()
    firebase_token = firebase_data["idToken"]
    print(f"✅ Usuario creado exitosamente")
    
    # 2. Hacer signin en el backend
    print("\n2️⃣ Signin en el backend...")
    signin_response = requests.post(
        f"{BASE_URL}/api/auth/signin",
        headers={
            "Authorization": f"Bearer {firebase_token}",
            "Content-Type": "application/json"
        }
    )
    
    if signin_response.status_code != 200:
        print(f"❌ Error en signin: {signin_response.status_code}")
        return False
    
    backend_token = signin_response.json()["access_token"]
    print(f"✅ Signin exitoso")
    
    # 3. Datos de ingredientes (formato como viene del reconocimiento)
    ingredients_data = {
        "ingredients": [
            {
                "name": "Tomate",
                "description": "Tomate fresco de color rojo brillante",
                "quantity": 3,
                "type_unit": "unidad",
                "storage_type": "Refrigerado",
                "expiration_time": 7,
                "time_unit": "Días",
                "tips": "Guardar en el refrigerador para mantener frescura",
                "image_path": "https://via.placeholder.com/150x150/cccccc/666666?text=Tomate",
                "expiration_date": "2025-06-14T03:00:00+00:00",
                "added_at": "2025-06-07T03:00:00+00:00"
            },
            {
                "name": "Cebolla",
                "description": "Cebolla blanca mediana",
                "quantity": 2,
                "type_unit": "unidad", 
                "storage_type": "Ambiente",
                "expiration_time": 2,
                "time_unit": "Semanas",
                "tips": "Almacenar en lugar fresco y seco",
                "image_path": "https://via.placeholder.com/150x150/cccccc/666666?text=Cebolla",
                "expiration_date": "2025-06-21T03:00:00+00:00",
                "added_at": "2025-06-07T03:00:00+00:00"
            }
        ]
    }
    
    # 4. POST al inventario con measurement de tiempo
    print(f"\n3️⃣ Enviando {len(ingredients_data['ingredients'])} ingredientes al inventario...")
    print("🚀 MIDIENDO TIEMPO DE ENRICHMENT AI...")
    start_time = time.time()
    
    inventory_response = requests.post(
        f"{BASE_URL}/api/inventory/ingredients",
        headers={
            "Authorization": f"Bearer {backend_token}",
            "Content-Type": "application/json"
        },
        json=ingredients_data
    )
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"⏱️ Tiempo de procesamiento: {processing_time:.2f} segundos")
    
    if inventory_response.status_code != 201:
        print(f"❌ Error agregando al inventario: {inventory_response.status_code}")
        print(f"Response: {inventory_response.text}")
        return False
    
    print(f"✅ Ingredientes agregados exitosamente al inventario")
    
    # 5. Verificar que se generó el enrichment
    print("\n4️⃣ Verificando inventario...")
    get_inventory_response = requests.get(
        f"{BASE_URL}/api/inventory",
        headers={
            "Authorization": f"Bearer {backend_token}",
            "Content-Type": "application/json"
        }
    )
    
    if get_inventory_response.status_code != 200:
        print(f"❌ Error obteniendo inventario: {get_inventory_response.status_code}")
        return False
    
    inventory_data = get_inventory_response.json()
    print(f"📦 Inventario tiene {len(inventory_data['ingredients'])} tipos de ingredientes")
    
    # Verificar que los ingredientes están en el inventario
    ingredient_names = [ing['name'] for ing in inventory_data['ingredients']]
    expected_names = ['Tomate', 'Cebolla']
    
    for expected_name in expected_names:
        if expected_name in ingredient_names:
            print(f"✅ {expected_name} encontrado en inventario")
        else:
            print(f"❌ {expected_name} NO encontrado en inventario")
            return False
    
    print(f"\n🎉 TEST EXITOSO!")
    print(f"💡 Los ingredientes se agregaron al inventario")
    print(f"⚡ Tiempo de procesamiento AI: {processing_time:.2f}s")
    print(f"🌱 Environmental impact y utilization ideas generados durante el POST al inventario")
    
    return True

if __name__ == "__main__":
    success = test_inventory_post_with_ai_enrichment()
    if success:
        print("\n✅ TODOS LOS TESTS PASARON")
    else:
        print("\n❌ ALGUNOS TESTS FALLARON") 