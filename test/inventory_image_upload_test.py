"""
📤 Tests para endpoint de upload de imágenes del inventario

Este archivo contiene tests para verificar el funcionamiento
del endpoint especializado de upload de imágenes del inventario.

Para ejecutar estos tests:
1. Asegurar que el backend esté corriendo
2. Tener un usuario válido para obtener JWT token
3. Tener imágenes de test disponibles
4. Ejecutar: python -m pytest test/inventory_image_upload_test.py -v
"""
import requests
import io
from PIL import Image
import tempfile
import os

# Configuración base
BASE_URL = "http://localhost:3000/api"
TEST_USER_TOKEN = "your_jwt_token_here"  # Reemplazar con token válido

headers = {
    "Authorization": f"Bearer {TEST_USER_TOKEN}"
}

def create_test_image(format='JPEG'):
    """Crea una imagen de test en memoria"""
    # Crear imagen simple de test
    image = Image.new('RGB', (100, 100), color='red')
    
    # Guardar en buffer
    image_buffer = io.BytesIO()
    image.save(image_buffer, format=format)
    image_buffer.seek(0)
    
    return image_buffer

def test_upload_recognition_image():
    """
    Test para subir imagen para reconocimiento.
    """
    print(f"\n📤 Testing recognition image upload")
    
    # Crear imagen de test
    image_buffer = create_test_image()
    
    files = {
        'image': ('test_recognition.jpg', image_buffer, 'image/jpeg')
    }
    
    data = {
        'upload_type': 'recognition'
    }
    
    print(f"🔗 URL: {BASE_URL}/inventory/upload_image")
    print(f"📋 Upload type: recognition")
    
    response = requests.post(
        f"{BASE_URL}/inventory/upload_image",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Recognition image uploaded successfully!")
        print(f"   • Storage path: {data.get('upload_info', {}).get('storage_path')}")
        print(f"   • Folder: {data.get('upload_info', {}).get('folder')}")
        print(f"   • Public URL: {data.get('upload_info', {}).get('public_url')}")
        
        # Verificar que se guardó en la carpeta correcta
        storage_path = data.get('upload_info', {}).get('storage_path', '')
        assert 'recognitions' in storage_path, "Image should be in recognitions folder"
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_upload_ingredient_image():
    """
    Test para subir imagen de ingrediente manual.
    """
    print(f"\n🥬 Testing ingredient image upload")
    
    # Crear imagen de test
    image_buffer = create_test_image()
    
    files = {
        'image': ('test_ingredient.jpg', image_buffer, 'image/jpeg')
    }
    
    data = {
        'upload_type': 'ingredient',
        'item_name': 'Tomate Test'
    }
    
    print(f"🔗 URL: {BASE_URL}/inventory/upload_image")
    print(f"📋 Upload type: ingredient")
    print(f"🏷️ Item name: {data['item_name']}")
    
    response = requests.post(
        f"{BASE_URL}/inventory/upload_image",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Ingredient image uploaded successfully!")
        print(f"   • Storage path: {data.get('upload_info', {}).get('storage_path')}")
        print(f"   • Folder: {data.get('upload_info', {}).get('folder')}")
        print(f"   • Item name: {data.get('upload_info', {}).get('item_name')}")
        print(f"   • Public URL: {data.get('upload_info', {}).get('public_url')}")
        
        # Verificar que se guardó en la carpeta correcta
        storage_path = data.get('upload_info', {}).get('storage_path', '')
        assert 'items' in storage_path, "Image should be in items folder"
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_upload_food_image():
    """
    Test para subir imagen de comida manual.
    """
    print(f"\n🍽️ Testing food image upload")
    
    # Crear imagen de test
    image_buffer = create_test_image()
    
    files = {
        'image': ('test_food.jpg', image_buffer, 'image/jpeg')
    }
    
    data = {
        'upload_type': 'food',
        'item_name': 'Pasta con Tomate Test'
    }
    
    print(f"🔗 URL: {BASE_URL}/inventory/upload_image")
    print(f"📋 Upload type: food")
    print(f"🏷️ Item name: {data['item_name']}")
    
    response = requests.post(
        f"{BASE_URL}/inventory/upload_image",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print("✅ Food image uploaded successfully!")
        print(f"   • Storage path: {data.get('upload_info', {}).get('storage_path')}")
        print(f"   • Folder: {data.get('upload_info', {}).get('folder')}")
        print(f"   • Item name: {data.get('upload_info', {}).get('item_name')}")
        print(f"   • Public URL: {data.get('upload_info', {}).get('public_url')}")
        
        # Verificar que se guardó en la carpeta correcta
        storage_path = data.get('upload_info', {}).get('storage_path', '')
        assert 'items' in storage_path, "Image should be in items folder"
        
        return True
    else:
        print(f"❌ Error: {response.status_code}")
        print(f"Response: {response.text}")
        return False

def test_upload_invalid_type():
    """
    Test para verificar validación de tipos inválidos.
    """
    print(f"\n❌ Testing invalid upload type validation")
    
    # Crear imagen de test
    image_buffer = create_test_image()
    
    files = {
        'image': ('test_invalid.jpg', image_buffer, 'image/jpeg')
    }
    
    data = {
        'upload_type': 'invalid_type'  # Tipo inválido
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/upload_image",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Invalid type correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_upload_no_file():
    """
    Test para verificar validación cuando no hay archivo.
    """
    print(f"\n❌ Testing no file validation")
    
    data = {
        'upload_type': 'ingredient'
    }
    
    response = requests.post(
        f"{BASE_URL}/inventory/upload_image",
        headers=headers,
        data=data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ No file correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_upload_no_type():
    """
    Test para verificar validación cuando no hay upload_type.
    """
    print(f"\n❌ Testing no upload_type validation")
    
    # Crear imagen de test
    image_buffer = create_test_image()
    
    files = {
        'image': ('test_no_type.jpg', image_buffer, 'image/jpeg')
    }
    
    # No incluir upload_type
    data = {}
    
    response = requests.post(
        f"{BASE_URL}/inventory/upload_image",
        headers=headers,
        files=files,
        data=data
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 400:
        print("✅ Missing upload_type correctly rejected!")
        print(f"   • Error: {response.json().get('error')}")
        return True
    else:
        print(f"❌ Expected 400 error but got: {response.status_code}")
        return False

def test_folder_organization():
    """
    Test para verificar que las imágenes se organizan en las carpetas correctas.
    """
    print(f"\n📂 Testing folder organization")
    
    upload_tests = [
        ('recognition', 'recognitions'),
        ('ingredient', 'items'),
        ('food', 'items')
    ]
    
    results = []
    
    for upload_type, expected_folder in upload_tests:
        print(f"\n   Testing {upload_type} -> {expected_folder}")
        
        # Crear imagen de test
        image_buffer = create_test_image()
        
        files = {
            'image': (f'test_{upload_type}.jpg', image_buffer, 'image/jpeg')
        }
        
        data = {
            'upload_type': upload_type,
            'item_name': f'Test {upload_type}'
        }
        
        response = requests.post(
            f"{BASE_URL}/inventory/upload_image",
            headers=headers,
            files=files,
            data=data
        )
        
        if response.status_code == 201:
            upload_info = response.json().get('upload_info', {})
            storage_path = upload_info.get('storage_path', '')
            folder = upload_info.get('folder', '')
            
            # Verificar estructura de carpeta
            folder_correct = expected_folder in storage_path
            folder_field_correct = folder == expected_folder
            
            print(f"     • Storage path: {storage_path}")
            print(f"     • Folder field: {folder}")
            print(f"     • Folder in path: {folder_correct}")
            print(f"     • Folder field correct: {folder_field_correct}")
            
            results.append(folder_correct and folder_field_correct)
        else:
            print(f"     ❌ Upload failed: {response.status_code}")
            results.append(False)
    
    all_correct = all(results)
    if all_correct:
        print("\n✅ All folder organization tests passed!")
    else:
        print("\n❌ Some folder organization tests failed!")
    
    return all_correct

def run_all_tests():
    """
    Ejecuta todos los tests de upload de imágenes del inventario.
    """
    print("=" * 60)
    print("📤 INICIANDO TESTS DE UPLOAD DE IMÁGENES DEL INVENTARIO")
    print("=" * 60)
    
    results = []
    
    # Tests principales
    results.append(("Recognition Upload", test_upload_recognition_image()))
    results.append(("Ingredient Upload", test_upload_ingredient_image()))
    results.append(("Food Upload", test_upload_food_image()))
    
    # Tests de validación
    results.append(("Invalid Type Validation", test_upload_invalid_type()))
    results.append(("No File Validation", test_upload_no_file()))
    results.append(("No Type Validation", test_upload_no_type()))
    
    # Test de organización
    results.append(("Folder Organization", test_folder_organization()))
    
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
        print("🎉 ¡Todos los tests de upload de imágenes pasaron exitosamente!")
    else:
        print("⚠️ Algunos tests fallaron. Revisa los detalles arriba.")
    
    return passed == total

if __name__ == "__main__":
    print("📤 Tests de Upload de Imágenes del Inventario")
    print("=" * 60)
    print("📤 Estos tests verifican:")
    print("   • Upload de imágenes para reconocimiento")
    print("   • Upload de imágenes de ingredientes y comidas manuales")
    print("   • Validaciones de tipos y archivos")
    print("   • Organización automática en carpetas")
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
        except ImportError as e:
            if "PIL" in str(e):
                print("❌ Pillow no está instalado. Instálalo con: pip install Pillow")
            else:
                print(f"❌ Error de importación: {e}")
        except Exception as e:
            print(f"❌ Error ejecutando tests: {e}") 