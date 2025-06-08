"""
🔍 Tests para endpoints de detalles individuales del inventario

Este archivo contiene tests de ejemplo para verificar el funcionamiento
de los endpoints de detalles completos de ingredientes y food items.

Para ejecutar estos tests:
1. Asegurar que el backend esté corriendo
2. Tener un usuario válido para obtener JWT token
3. Tener ingredientes y food items en el inventario
4. Ejecutar: python -m pytest test/inventory_detail_test.py -v
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

def test_get_ingredient_detail():
    """
    Test para obtener detalles completos de un ingrediente específico.
    """
    ingredient_name = "Tomate"  # Cambiar por un ingrediente que exista en tu inventario
    
    print(f"\n🔍 Testing ingredient detail for: {ingredient_name}")
    
    response = requests.get(
        f"{BASE_URL}/inventory/ingredients/{ingredient_name}/detail",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Ingredient detail retrieved successfully!")
        print(f"   • Name: {data.get('name')}")
        print(f"   • Total quantity: {data.get('total_quantity')} {data.get('type_unit')}")
        print(f"   • Stack count: {data.get('stack_count')}")
        print(f"   • Storage type: {data.get('storage_type')}")
        print(f"   • Environmental impact available: {'environmental_impact' in data}")
        print(f"   • Utilization ideas count: {len(data.get('utilization_ideas', []))}")
        print(f"   • Enriched with: {', '.join(data.get('enriched_with', []))}")
        
        # Verificar estructura de stacks
        stacks = data.get('stacks', [])
        print(f"   • Stacks details:")
        for i, stack in enumerate(stacks):
            print(f"     Stack {i+1}: {stack.get('quantity')} {stack.get('type_unit')}, expires in {stack.get('days_to_expire')} days")
        
        return True
    elif response.status_code == 404:
        print(f"❌ Ingredient '{ingredient_name}' not found in inventory")
        print("💡 Make sure the ingredient exists in your inventory first")
        return False
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_get_food_detail():
    """
    Test para obtener detalles completos de un food item específico.
    Nota: Necesitas tener un food item en tu inventario para que este test funcione.
    """
    food_name = "Pasta con Tomate"  # Cambiar por una comida que exista
    added_at = "2025-01-01T12:00:00Z"  # Cambiar por el timestamp real
    
    print(f"\n🍽️ Testing food detail for: {food_name}")
    
    response = requests.get(
        f"{BASE_URL}/inventory/foods/{food_name}/{added_at}/detail",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Food detail retrieved successfully!")
        print(f"   • Name: {data.get('name')}")
        print(f"   • Category: {data.get('category')}")
        print(f"   • Serving quantity: {data.get('serving_quantity')}")
        print(f"   • Total calories: {data.get('total_calories')}")
        print(f"   • Calories per serving: {data.get('calories_per_serving')}")
        print(f"   • Days to expire: {data.get('days_to_expire')}")
        print(f"   • Nutritional analysis available: {'nutritional_analysis' in data}")
        print(f"   • Consumption ideas count: {len(data.get('consumption_ideas', []))}")
        print(f"   • Storage advice available: {'storage_advice' in data}")
        print(f"   • Enriched with: {', '.join(data.get('enriched_with', []))}")
        
        # Verificar main ingredients
        main_ingredients = data.get('main_ingredients', [])
        print(f"   • Main ingredients: {', '.join(main_ingredients) if isinstance(main_ingredients, list) else main_ingredients}")
        
        return True
    elif response.status_code == 404:
        print(f"❌ Food item '{food_name}' added at '{added_at}' not found in inventory")
        print("💡 Make sure the food item exists with the correct added_at timestamp")
        return False
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_ingredient_detail_not_found():
    """
    Test para verificar manejo de error cuando un ingrediente no existe.
    """
    non_existent_ingredient = "IngredienteInexistente123"
    
    print(f"\n🚫 Testing ingredient detail for non-existent ingredient: {non_existent_ingredient}")
    
    response = requests.get(
        f"{BASE_URL}/inventory/ingredients/{non_existent_ingredient}/detail",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ Correctly returned 404 for non-existent ingredient")
        error_data = response.json()
        print(f"   • Error message: {error_data.get('error')}")
        return True
    else:
        print(f"❌ Expected 404, but got {response.status_code}")
        return False

def test_food_detail_not_found():
    """
    Test para verificar manejo de error cuando un food item no existe.
    """
    non_existent_food = "ComidaInexistente123"
    fake_added_at = "2025-01-01T00:00:00Z"
    
    print(f"\n🚫 Testing food detail for non-existent food: {non_existent_food}")
    
    response = requests.get(
        f"{BASE_URL}/inventory/foods/{non_existent_food}/{fake_added_at}/detail",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 404:
        print("✅ Correctly returned 404 for non-existent food item")
        error_data = response.json()
        print(f"   • Error message: {error_data.get('error')}")
        return True
    else:
        print(f"❌ Expected 404, but got {response.status_code}")
        return False

def run_all_tests():
    """
    Ejecuta todos los tests de detalles del inventario.
    """
    print("=" * 60)
    print("🔍 INICIANDO TESTS DE DETALLES DEL INVENTARIO")
    print("=" * 60)
    
    results = []
    
    # Tests principales
    results.append(("Ingredient Detail", test_get_ingredient_detail()))
    results.append(("Food Detail", test_get_food_detail()))
    
    # Tests de errores
    results.append(("Ingredient Not Found", test_ingredient_detail_not_found()))
    results.append(("Food Not Found", test_food_detail_not_found()))
    
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
        print("🎉 ¡Todos los tests de detalles del inventario pasaron exitosamente!")
    else:
        print("⚠️ Algunos tests fallaron. Revisa los detalles arriba.")
    
    return passed == total

if __name__ == "__main__":
    print("🔍 Tests de Endpoints de Detalles del Inventario")
    print("=" * 60)
    print("📋 Estos tests verifican:")
    print("   • Obtener detalles completos de ingredientes específicos")
    print("   • Obtener detalles completos de food items específicos") 
    print("   • Manejo de errores para items no encontrados")
    print("   • Estructura y contenido de las respuestas enriquecidas")
    print()
    print("🚨 IMPORTANTE:")
    print(f"   • Cambia TEST_USER_TOKEN por tu JWT token válido")
    print(f"   • Asegúrate de tener ingredientes y food items en tu inventario")
    print(f"   • El backend debe estar corriendo en {BASE_URL}")
    print()
    
    if TEST_USER_TOKEN == "your_jwt_token_here":
        print("❌ Por favor, actualiza TEST_USER_TOKEN con un token válido antes de ejecutar los tests")
    else:
        run_all_tests() 