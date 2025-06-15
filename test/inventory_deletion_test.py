"""
🗑️ Tests para endpoints de eliminación del inventario

Este archivo contiene tests de ejemplo para verificar el funcionamiento
de los endpoints de eliminación de ingredientes y food items.

Para ejecutar estos tests:
1. Asegurar que el backend esté corriendo
2. Tener un usuario válido para obtener JWT token
3. Ejecutar: python -m pytest test/inventory_deletion_test.py -v
"""
import requests
import json
from datetime import datetime, timedelta

# Configuración base
BASE_URL = "http://localhost:3000/api"
TEST_USER_TOKEN = "your_jwt_token_here"  # Reemplazar con token válido

headers = {
    "Authorization": f"Bearer {TEST_USER_TOKEN}",
    "Content-Type": "application/json"
}

def test_delete_ingredient_complete():
    """
    Test para eliminar un ingrediente completo del inventario.
    
    Prerequisitos:
    - Debe existir un ingrediente llamado 'Test Ingredient' en el inventario
    """
    ingredient_name = "Test Ingredient"
    
    print(f"🧪 Testing DELETE complete ingredient: {ingredient_name}")
    
    # Ejecutar eliminación
    response = requests.delete(
        f"{BASE_URL}/inventory/ingredients/{ingredient_name}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Verificaciones
    if response.status_code == 200:
        data = response.json()
        assert data["ingredient"] == ingredient_name
        assert data["deleted"] == "all_stacks"
        print("✅ Test PASSED: Ingredient deleted completely")
    elif response.status_code == 404:
        print("⚠️  Test INFO: Ingredient not found (expected if doesn't exist)")
    else:
        print(f"❌ Test FAILED: Unexpected status code {response.status_code}")

def test_delete_ingredient_stack():
    """
    Test para eliminar un stack específico de ingrediente.
    
    Prerequisitos:
    - Debe existir un stack del ingrediente con added_at específico
    """
    ingredient_name = "Test Ingredient"
    # Usar una fecha de ejemplo - debe coincidir con un stack real
    added_at = "2025-01-01T10:00:00Z"
    
    print(f"🧪 Testing DELETE ingredient stack: {ingredient_name} at {added_at}")
    
    # Ejecutar eliminación
    response = requests.delete(
        f"{BASE_URL}/inventory/ingredients/{ingredient_name}/{added_at}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Verificaciones
    if response.status_code == 200:
        data = response.json()
        assert data["ingredient"] == ingredient_name
        assert data["deleted_stack_added_at"] == added_at
        print("✅ Test PASSED: Ingredient stack deleted")
    elif response.status_code == 404:
        print("⚠️  Test INFO: Ingredient stack not found (expected if doesn't exist)")
    else:
        print(f"❌ Test FAILED: Unexpected status code {response.status_code}")

def test_delete_food_item():
    """
    Test para eliminar un food item específico.
    
    Prerequisitos:
    - Debe existir un food item con added_at específico
    """
    food_name = "Test Food"
    # Usar una fecha de ejemplo - debe coincidir con un food item real
    added_at = "2025-01-01T10:00:00Z"
    
    print(f"🧪 Testing DELETE food item: {food_name} at {added_at}")
    
    # Ejecutar eliminación
    response = requests.delete(
        f"{BASE_URL}/inventory/foods/{food_name}/{added_at}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Verificaciones
    if response.status_code == 200:
        data = response.json()
        assert data["food"] == food_name
        assert data["deleted_added_at"] == added_at
        print("✅ Test PASSED: Food item deleted")
    elif response.status_code == 404:
        print("⚠️  Test INFO: Food item not found (expected if doesn't exist)")
    else:
        print(f"❌ Test FAILED: Unexpected status code {response.status_code}")

def test_delete_nonexistent_ingredient():
    """
    Test para verificar que se maneje correctamente un ingrediente inexistente.
    """
    nonexistent_ingredient = "NonExistent Ingredient"
    
    print(f"🧪 Testing DELETE nonexistent ingredient: {nonexistent_ingredient}")
    
    response = requests.delete(
        f"{BASE_URL}/inventory/ingredients/{nonexistent_ingredient}",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    # Debe retornar 404
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    print("✅ Test PASSED: Correctly handled nonexistent ingredient")

def test_unauthorized_access():
    """
    Test para verificar que se requiera autenticación.
    """
    ingredient_name = "Any Ingredient"
    
    print(f"🧪 Testing unauthorized access")
    
    # Hacer request sin token
    response = requests.delete(
        f"{BASE_URL}/inventory/ingredients/{ingredient_name}",
        headers={"Content-Type": "application/json"}  # Sin Authorization header
    )
    
    print(f"Status Code: {response.status_code}")
    
    # Debe retornar 401 Unauthorized
    assert response.status_code == 401
    print("✅ Test PASSED: Correctly requires authentication")

def get_inventory_for_testing():
    """
    Helper para obtener el inventario actual y ver qué items están disponibles para testing.
    """
    print("📋 Getting current inventory for testing...")
    
    response = requests.get(
        f"{BASE_URL}/inventory",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"📊 Found {len(data.get('ingredients', []))} ingredient types")
        
        # Mostrar ingredientes disponibles
        for ingredient in data.get('ingredients', []):
            print(f"   • {ingredient['name']}: {len(ingredient.get('stacks', []))} stacks")
            for stack in ingredient.get('stacks', []):
                print(f"     └─ Added at: {stack.get('added_at')}")
        
        return data
    else:
        print(f"❌ Error getting inventory: {response.status_code}")
        return None

if __name__ == "__main__":
    print("🗑️ INVENTORY DELETION TESTS")
    print("=" * 50)
    
    # Verificar configuración
    if TEST_USER_TOKEN == "your_jwt_token_here":
        print("⚠️  WARNING: Please set a valid JWT token in TEST_USER_TOKEN")
        print("   You can get a token by logging in through the auth endpoint")
        exit(1)
    
    try:
        # Obtener inventario actual para referencia
        get_inventory_for_testing()
        print()
        
        # Ejecutar tests
        print("🚀 Running deletion tests...")
        
        # Test casos positivos (pueden fallar si no hay datos)
        test_delete_ingredient_stack()
        print()
        
        test_delete_food_item()
        print()
        
        test_delete_ingredient_complete()
        print()
        
        # Test casos negativos (deben pasar siempre)
        test_delete_nonexistent_ingredient()
        print()
        
        test_unauthorized_access()
        print()
        
        print("🎉 All tests completed!")
        print("   Note: Some tests may show INFO messages if test data doesn't exist")
        
    except Exception as e:
        print(f"🚨 Test execution failed: {str(e)}")
        print("   Make sure the backend is running and the JWT token is valid")

# Ejemplos de comandos curl para testing manual
CURL_EXAMPLES = """
# 🔧 Manual testing with curl:

# 1. Get inventory to see available items
curl -X GET \\
  http://localhost:3000/api/inventory \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 2. Delete a specific ingredient stack
curl -X DELETE \\
  http://localhost:3000/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Delete complete ingredient (all stacks)
curl -X DELETE \\
  http://localhost:3000/api/inventory/ingredients/Tomate \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 4. Delete a food item
curl -X DELETE \\
  http://localhost:3000/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T10:00:00Z \\
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
""" 