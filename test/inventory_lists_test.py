"""
📋 Tests para endpoints de listas específicas del inventario

Este archivo contiene tests para verificar el funcionamiento
de los endpoints que devuelven solo ingredientes o solo food items.

Para ejecutar estos tests:
1. Asegurar que el backend esté corriendo
2. Tener un usuario válido para obtener JWT token
3. Tener ingredientes y food items en el inventario
4. Ejecutar: python -m pytest test/inventory_lists_test.py -v
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

def test_get_ingredients_list():
    """
    Test para obtener la lista específica de ingredientes.
    """
    print(f"\n📋 Testing ingredients list endpoint")
    
    response = requests.get(
        f"{BASE_URL}/inventory/ingredients/list",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Ingredients list retrieved successfully!")
        print(f"   • Total ingredients: {data.get('total_ingredients')}")
        print(f"   • Total stacks: {data.get('total_stacks')}")
        
        # Verificar estructura
        ingredients = data.get('ingredients', [])
        if ingredients:
            print(f"   • First ingredient: {ingredients[0].get('name')}")
            print(f"   • Has summary: {'summary' in data}")
            
            # Verificar estructura de cada ingrediente
            for i, ingredient in enumerate(ingredients[:3]):  # Solo los primeros 3
                name = ingredient.get('name')
                stacks = ingredient.get('stacks', [])
                total_quantity = ingredient.get('total_quantity')
                print(f"     Ingredient {i+1}: {name}")
                print(f"       • Total quantity: {total_quantity} {ingredient.get('type_unit')}")
                print(f"       • Stack count: {len(stacks)}")
                print(f"       • Storage: {ingredient.get('storage_type')}")
            
            # Verificar resumen
            summary = data.get('summary', {})
            print(f"   • Summary stats:")
            print(f"     • Average stacks per ingredient: {summary.get('average_stacks_per_ingredient')}")
            
        else:
            print("   • No ingredients found (empty inventory)")
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_get_foods_list():
    """
    Test para obtener la lista específica de food items.
    """
    print(f"\n🍽️ Testing foods list endpoint")
    
    response = requests.get(
        f"{BASE_URL}/inventory/foods/list",
        headers=headers
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("✅ Foods list retrieved successfully!")
        print(f"   • Total foods: {data.get('total_foods')}")
        print(f"   • Total servings: {data.get('total_servings')}")
        print(f"   • Total calories: {data.get('total_calories')}")
        
        # Verificar estructura
        foods = data.get('foods', [])
        if foods:
            print(f"   • First food: {foods[0].get('name')}")
            print(f"   • Has summary: {'summary' in data}")
            
            # Verificar estructura de cada food item
            for i, food in enumerate(foods[:3]):  # Solo los primeros 3
                name = food.get('name')
                category = food.get('category')
                servings = food.get('serving_quantity')
                calories = food.get('calories')
                status = food.get('status')
                print(f"     Food {i+1}: {name}")
                print(f"       • Category: {category}")
                print(f"       • Servings: {servings}")
                print(f"       • Calories: {calories}")
                print(f"       • Status: {status}")
                print(f"       • Days to expire: {food.get('days_to_expire')}")
            
            # Verificar resumen y categorías
            summary = data.get('summary', {})
            categories = summary.get('categories', {})
            print(f"   • Summary stats:")
            print(f"     • Average calories per food: {summary.get('average_calories_per_food')}")
            print(f"     • Categories found: {len(categories)}")
            
            for category, stats in list(categories.items())[:3]:  # Primeras 3 categorías
                print(f"       • {category}: {stats.get('count')} items, {stats.get('total_calories')} calories")
            
        else:
            print("   • No food items found (empty inventory)")
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_ingredients_vs_foods_separation():
    """
    Test para verificar que los endpoints devuelven solo el tipo correcto.
    """
    print(f"\n🔍 Testing separation between ingredients and foods")
    
    # Obtener ambas listas
    ingredients_response = requests.get(f"{BASE_URL}/inventory/ingredients/list", headers=headers)
    foods_response = requests.get(f"{BASE_URL}/inventory/foods/list", headers=headers)
    
    if ingredients_response.status_code == 200 and foods_response.status_code == 200:
        ingredients_data = ingredients_response.json()
        foods_data = foods_response.json()
        
        print("✅ Both endpoints responded successfully!")
        
        # Verificar que ingredients solo devuelve ingredientes
        has_foods_field = 'foods' in ingredients_data
        has_ingredients_field = 'ingredients' in ingredients_data
        print(f"   • Ingredients endpoint:")
        print(f"     • Has 'ingredients' field: {has_ingredients_field}")
        print(f"     • Has 'foods' field: {has_foods_field}")
        
        # Verificar que foods solo devuelve food items
        has_ingredients_field_in_foods = 'ingredients' in foods_data
        has_foods_field_in_foods = 'foods' in foods_data
        print(f"   • Foods endpoint:")
        print(f"     • Has 'foods' field: {has_foods_field_in_foods}")
        print(f"     • Has 'ingredients' field: {has_ingredients_field_in_foods}")
        
        # Verificar la separación correcta
        correct_separation = (
            has_ingredients_field and not has_foods_field and
            has_foods_field_in_foods and not has_ingredients_field_in_foods
        )
        
        if correct_separation:
            print("✅ Separation is correct - each endpoint returns only its specific type")
        else:
            print("❌ Separation issue - endpoints might be returning mixed data")
        
        return correct_separation
    else:
        print(f"❌ One or both endpoints failed")
        print(f"Ingredients status: {ingredients_response.status_code}")
        print(f"Foods status: {foods_response.status_code}")
        return False

def test_compare_with_general_inventory():
    """
    Test para comparar las listas específicas con el inventario general.
    """
    print(f"\n📊 Testing comparison with general inventory endpoint")
    
    # Obtener inventario general
    general_response = requests.get(f"{BASE_URL}/inventory", headers=headers)
    ingredients_response = requests.get(f"{BASE_URL}/inventory/ingredients/list", headers=headers)
    foods_response = requests.get(f"{BASE_URL}/inventory/foods/list", headers=headers)
    
    if all(r.status_code == 200 for r in [general_response, ingredients_response, foods_response]):
        general_data = general_response.json()
        ingredients_data = ingredients_response.json()
        foods_data = foods_response.json()
        
        print("✅ All endpoints responded successfully!")
        
        # Comparar cantidades
        general_ingredients = general_data.get('ingredients', [])
        specific_ingredients = ingredients_data.get('ingredients', [])
        specific_foods = foods_data.get('foods', [])
        
        print(f"   • General inventory ingredients: {len(general_ingredients)}")
        print(f"   • Specific ingredients list: {len(specific_ingredients)}")
        print(f"   • Specific foods list: {len(specific_foods)}")
        
        # Verificar consistencia en ingredientes
        ingredients_match = len(general_ingredients) == len(specific_ingredients)
        print(f"   • Ingredients count match: {ingredients_match}")
        
        if ingredients_match and general_ingredients and specific_ingredients:
            # Verificar algunos nombres
            general_names = {ing.get('name') for ing in general_ingredients}
            specific_names = {ing.get('name') for ing in specific_ingredients}
            names_match = general_names == specific_names
            print(f"   • Ingredient names match: {names_match}")
        
        return True
    else:
        print(f"❌ Some endpoints failed")
        return False

def run_all_tests():
    """
    Ejecuta todos los tests de listas específicas del inventario.
    """
    print("=" * 60)
    print("📋 INICIANDO TESTS DE LISTAS ESPECÍFICAS DEL INVENTARIO")
    print("=" * 60)
    
    results = []
    
    # Tests principales
    results.append(("Ingredients List", test_get_ingredients_list()))
    results.append(("Foods List", test_get_foods_list()))
    
    # Tests de comparación
    results.append(("Separation Verification", test_ingredients_vs_foods_separation()))
    results.append(("Consistency Check", test_compare_with_general_inventory()))
    
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
        print("🎉 ¡Todos los tests de listas específicas pasaron exitosamente!")
    else:
        print("⚠️ Algunos tests fallaron. Revisa los detalles arriba.")
    
    return passed == total

if __name__ == "__main__":
    print("📋 Tests de Endpoints de Listas Específicas del Inventario")
    print("=" * 60)
    print("📋 Estos tests verifican:")
    print("   • Endpoint de lista solo de ingredientes")
    print("   • Endpoint de lista solo de food items") 
    print("   • Separación correcta entre tipos")
    print("   • Consistencia con el inventario general")
    print("   • Estructura y contenido de las respuestas")
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