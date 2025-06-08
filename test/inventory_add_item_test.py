"""
🎯 Tests para endpoint de agregar items al inventario

Este archivo contiene tests para verificar el funcionamiento
del endpoint unificado para agregar items (ingredientes y comidas) al inventario.

Para ejecutar estos tests:
1. Asegurar que el backend esté corriendo
2. Tener un usuario válido para obtener JWT token
3. Ejecutar: python -m pytest test/inventory_add_item_test.py -v
"""
import requests
import json

# Configuración base
BASE_URL = "http://localhost:3000/api"
TEST_USER_TOKEN = "your_jwt_token_here"  # Reemplazar con token válido

headers = {
    "Authorization": f"Bearer {TEST_USER_TOKEN}",
    "Content-Type": "application/json"
}

def test_add_ingredient_success():
    """
    Test para agregar un ingrediente exitosamente.
    """
    print(f"\n🥬 Testing add ingredient to inventory")
    
    ingredient_data = {
        "name": "Tomate Cherry Test",
        "quantity": 250,
        "unit": "gramos",
        "storage_type": "refrigerador",
        "category": "ingredient",
        "image_url": "https://example.com/tomate.jpg"
    }
    
    print(f"🔗 URL: {BASE_URL}/inventory/add_item")
    print(f"📋 Data: {ingredient_data}")
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=ingredient_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Ingredient added successfully!")
        print(f"   • Message: {data.get('message')}")
        print(f"   • Item type: {data.get('item_type')}")
        print(f"   • Name: {data.get('item_data', {}).get('name')}")
        print(f"   • Quantity: {data.get('item_data', {}).get('quantity')} {data.get('item_data', {}).get('unit')}")
        print(f"   • Expiration: {data.get('item_data', {}).get('expiration_date')}")
        print(f"   • Tips: {data.get('item_data', {}).get('tips', '')[:50]}...")
        print(f"   • Enriched fields: {data.get('item_data', {}).get('enriched_fields')}")
        
        # Verificar estructura de respuesta
        assert data.get('item_type') == 'ingredient'
        assert data.get('item_data', {}).get('name') == ingredient_data['name']
        assert 'enriched_fields' in data.get('item_data', {})
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_add_food_success():
    """
    Test para agregar una comida exitosamente.
    """
    print(f"\n🍽️ Testing add food to inventory")
    
    food_data = {
        "name": "Ensalada César Test",
        "quantity": 1,
        "unit": "porciones",
        "storage_type": "refrigerador",
        "category": "food",
        "image_url": None
    }
    
    print(f"🔗 URL: {BASE_URL}/inventory/add_item")
    print(f"📋 Data: {food_data}")
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=food_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Food added successfully!")
        print(f"   • Message: {data.get('message')}")
        print(f"   • Item type: {data.get('item_type')}")
        print(f"   • Name: {data.get('item_data', {}).get('name')}")
        print(f"   • Serving quantity: {data.get('item_data', {}).get('serving_quantity')}")
        print(f"   • Expiration: {data.get('item_data', {}).get('expiration_date')}")
        print(f"   • Main ingredients: {data.get('item_data', {}).get('main_ingredients')}")
        print(f"   • Category: {data.get('item_data', {}).get('category')}")
        print(f"   • Calories: {data.get('item_data', {}).get('calories')}")
        print(f"   • Enriched fields: {data.get('item_data', {}).get('enriched_fields')}")
        
        # Verificar estructura de respuesta
        assert data.get('item_type') == 'food'
        assert data.get('item_data', {}).get('name') == food_data['name']
        assert 'enriched_fields' in data.get('item_data', {})
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_add_ingredient_without_image():
    """
    Test para agregar ingrediente sin imagen URL.
    """
    print(f"\n🥕 Testing add ingredient without image")
    
    ingredient_data = {
        "name": "Zanahoria Test",
        "quantity": 500,
        "unit": "gramos",
        "storage_type": "despensa",
        "category": "ingredient"
        # No incluir image_url
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=ingredient_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Ingredient without image added successfully!")
        print(f"   • Name: {data.get('item_data', {}).get('name')}")
        print(f"   • Image path: {data.get('item_data', {}).get('image_path', 'EMPTY')}")
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_validation_missing_required_fields():
    """
    Test para validar campos requeridos faltantes.
    """
    print(f"\n❌ Testing validation - missing required fields")
    
    invalid_data = {
        "name": "Test Item",
        # Faltan quantity, unit, storage_type, category
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=invalid_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        error_data = response.json()
        print("✅ Missing fields correctly rejected!")
        print(f"   • Error: {error_data.get('error')}")
        print(f"   • Details: {error_data.get('details')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_validation_invalid_quantity():
    """
    Test para validar cantidad inválida.
    """
    print(f"\n❌ Testing validation - invalid quantity")
    
    invalid_data = {
        "name": "Test Item",
        "quantity": -5,  # Cantidad negativa
        "unit": "gramos",
        "storage_type": "refrigerador",
        "category": "ingredient"
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=invalid_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Invalid quantity correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_validation_invalid_unit():
    """
    Test para validar unidad inválida.
    """
    print(f"\n❌ Testing validation - invalid unit")
    
    invalid_data = {
        "name": "Test Item",
        "quantity": 100,
        "unit": "invalid_unit",  # Unidad inválida
        "storage_type": "refrigerador",
        "category": "ingredient"
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=invalid_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Invalid unit correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_validation_invalid_storage_type():
    """
    Test para validar tipo de almacenamiento inválido.
    """
    print(f"\n❌ Testing validation - invalid storage type")
    
    invalid_data = {
        "name": "Test Item",
        "quantity": 100,
        "unit": "gramos",
        "storage_type": "invalid_storage",  # Storage type inválido
        "category": "ingredient"
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=invalid_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Invalid storage type correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_validation_invalid_category():
    """
    Test para validar categoría inválida.
    """
    print(f"\n❌ Testing validation - invalid category")
    
    invalid_data = {
        "name": "Test Item",
        "quantity": 100,
        "unit": "gramos",
        "storage_type": "refrigerador",
        "category": "invalid_category"  # Categoría inválida
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers,
        json=invalid_data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Invalid category correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_no_json_data():
    """
    Test para verificar error cuando no se envía JSON.
    """
    print(f"\n❌ Testing no JSON data")
    
    response = requests.post(
        f"{BASE_URL}/inventory/add_item",
        headers=headers
        # No enviar data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ No JSON data correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_different_units():
    """
    Test para verificar diferentes unidades válidas.
    """
    print(f"\n📏 Testing different valid units")
    
    test_units = [
        ("kg", "ingredient"),
        ("litros", "ingredient"),
        ("unidades", "ingredient"),
        ("porciones", "food"),
        ("ml", "ingredient")
    ]
    
    results = []
    
    for unit, category in test_units:
        print(f"\n   Testing unit: {unit} (category: {category})")
        
        data = {
            "name": f"Test {unit} Item",
            "quantity": 1,
            "unit": unit,
            "storage_type": "refrigerador",
            "category": category
        }
        
        response = requests.post(
            f"{BASE_URL}/inventory/add_item",
            headers=headers,
            json=data
        )
        
        if response.status_code == 201:
            result_data = response.json()
            print(f"     ✅ Unit {unit} accepted")
            print(f"        └─ Name: {result_data.get('item_data', {}).get('name')}")
            results.append(True)
        else:
            print(f"     ❌ Unit {unit} rejected: {response.status_code}")
            results.append(False)
    
    all_passed = all(results)
    if all_passed:
        print("\n✅ All units test passed!")
    else:
        print("\n❌ Some units test failed!")
    
    return all_passed

def run_all_tests():
    """
    Ejecuta todos los tests del endpoint add_item.
    """
    print("=" * 60)
    print("🎯 INICIANDO TESTS DE ADD ITEM AL INVENTARIO")
    print("=" * 60)
    
    results = []
    
    # Tests principales
    results.append(("Add Ingredient Success", test_add_ingredient_success()))
    results.append(("Add Food Success", test_add_food_success()))
    results.append(("Add Ingredient Without Image", test_add_ingredient_without_image()))
    
    # Tests de validación
    results.append(("Missing Required Fields", test_validation_missing_required_fields()))
    results.append(("Invalid Quantity", test_validation_invalid_quantity()))
    results.append(("Invalid Unit", test_validation_invalid_unit()))
    results.append(("Invalid Storage Type", test_validation_invalid_storage_type()))
    results.append(("Invalid Category", test_validation_invalid_category()))
    results.append(("No JSON Data", test_no_json_data()))
    
    # Tests adicionales
    results.append(("Different Units", test_different_units()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE TESTS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
        if success:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} tests pasaron")
    
    if passed == total:
        print("🎉 ¡Todos los tests de add item pasaron exitosamente!")
    else:
        print("⚠️ Algunos tests fallaron. Revisa los detalles arriba.")
    
    return passed == total

if __name__ == "__main__":
    print("🎯 Tests de Add Item al Inventario")
    print("=" * 60)
    print("🎯 Estos tests verifican:")
    print("   • Agregar ingredientes al inventario")
    print("   • Agregar comidas al inventario")
    print("   • Enriquecimiento con IA")
    print("   • Validaciones de campos")
    print("   • Manejo de errores")
    print()
    print("🚨 IMPORTANTE:")
    print(f"   • Cambia TEST_USER_TOKEN por tu JWT token válido")
    print(f"   • El backend debe estar corriendo en {BASE_URL}")
    print()
    
    if TEST_USER_TOKEN == "your_jwt_token_here":
        print("❌ Por favor, actualiza TEST_USER_TOKEN con un token válido antes de ejecutar los tests")
    else:
        try:
            run_all_tests()
        except Exception as e:
            print(f"❌ Error ejecutando tests: {e}") 