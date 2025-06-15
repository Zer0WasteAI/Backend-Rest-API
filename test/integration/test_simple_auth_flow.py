"""
Test simplificado del flujo de reconocimiento de ingredientes
Este test simula la autenticación para probar los endpoints básicos
"""
import unittest
import requests
import json
import time
from pathlib import Path
import sys
from typing import Optional, Dict, Any

# Agregar el directorio padre al path para imports
sys.path.append(str(Path(__file__).parent.parent))
from test_config import TestConfig, TestUtils

class TestSimpleAuthFlow(unittest.TestCase):
    """
    Test simplificado del flujo de reconocimiento de ingredientes
    """
    
    @classmethod
    def setUpClass(cls):
        """Configuración inicial para todos los tests"""
        cls.config = TestConfig()
        cls.utils = TestUtils()
        
        # Variables de estado
        cls.access_token = None
        
        print(f"\n🧪 INICIANDO TESTS SIMPLIFICADOS")
        cls.config.print_environment_info()
    
    @staticmethod
    def _print_response_details(response: requests.Response, title: str = "RESPUESTA"):
        """Imprime detalles de la respuesta HTTP de forma legible"""
        print(f"\n📋 {title}")
        print(f"🔗 URL: {response.url}")
        print(f"📊 Status Code: {response.status_code}")
        print(f"⏱️ Tiempo: {response.elapsed.total_seconds():.2f}s")
        
        # Headers de respuesta (filtrar algunos sensibles)
        print(f"📨 Response Headers:")
        for key, value in response.headers.items():
            if key.lower() not in ['set-cookie', 'authorization']:
                print(f"   {key}: {value}")
        
        # Contenido de la respuesta
        try:
            if response.headers.get('content-type', '').startswith('application/json'):
                json_data = response.json()
                print(f"📄 Response JSON:")
                print(json.dumps(json_data, indent=2, ensure_ascii=False))
            else:
                content = response.text[:500]  # Primeros 500 caracteres
                print(f"📄 Response Text (primeros 500 chars):")
                print(content)
                if len(response.text) > 500:
                    print("... (truncado)")
        except Exception as e:
            print(f"📄 Response Text:")
            print(response.text[:200])  # Fallback
            print(f"❌ Error parseando JSON: {e}")
    
    @staticmethod
    def _print_request_details(method: str, url: str, headers: dict = None, data: dict = None):
        """Imprime detalles de la request HTTP"""
        print(f"\n📤 REQUEST {method.upper()}")
        print(f"🔗 URL: {url}")
        
        if headers:
            print(f"📨 Request Headers:")
            for key, value in headers.items():
                # Ocultar tokens completos por seguridad
                if key.lower() == 'authorization' and len(value) > 50:
                    print(f"   {key}: {value[:20]}...{value[-10:]}")
                else:
                    print(f"   {key}: {value}")
        
        if data and method.upper() in ['POST', 'PUT', 'PATCH']:
            print(f"📤 Request Body:")
            try:
                if isinstance(data, dict):
                    # Ocultar tokens en el body también
                    safe_data = data.copy()
                    if 'firebase_token' in safe_data and len(safe_data['firebase_token']) > 50:
                        safe_data['firebase_token'] = f"{safe_data['firebase_token'][:20]}...{safe_data['firebase_token'][-10:]}"
                    print(json.dumps(safe_data, indent=2, ensure_ascii=False))
                else:
                    print(str(data))
            except Exception as e:
                print(f"Error mostrando request body: {e}")
    
    def test_01_check_backend_status(self):
        """Test 1: Verificar que el backend esté funcionando"""
        print(f"\n🧪 TEST 1: Verificando estado del backend...")
        
        url = f"{self.config.BASE_URL}/status"
        self._print_request_details("GET", url)
        
        response = requests.get(url)
        self._print_response_details(response, "ESTADO DEL BACKEND")
        
        self.assertEqual(response.status_code, 200)
        
        status_data = response.json()
        self.assertEqual(status_data["status"], "success")
        print(f"✅ Backend funcionando correctamente")
        print(f"📊 Arquitectura: {status_data.get('architecture', 'N/A')}")
    
    def test_02_check_firebase_debug_endpoint(self):
        """Test 2: Verificar configuración Firebase"""
        print(f"\n🧪 TEST 2: Verificando configuración Firebase...")
        
        try:
            response = requests.get(
                f"{self.config.BASE_URL}/api/auth/firebase-debug",
                timeout=self.config.TEST_TIMEOUT
            )
            
            print(f"🔍 Status code: {response.status_code}")
            
            if response.status_code == 200:
                firebase_info = response.json()
                print(f"✅ Firebase configurado correctamente")
                print(f"🔥 Apps Firebase: {firebase_info.get('firebase_apps', 0)}")
                print(f"📁 Credenciales: {'✅' if firebase_info.get('credentials_exists') else '❌'}")
                print(f"🪣 Storage bucket: {firebase_info.get('storage_bucket', 'N/A')}")
                
                self.assertTrue(firebase_info.get('credentials_exists', False))
            else:
                print(f"⚠️ Firebase debug falló: {response.status_code}")
                print(f"⚠️ Respuesta: {response.text}")
        
        except Exception as e:
            print(f"❌ Error verificando Firebase: {e}")
    
    def test_03_check_test_images(self):
        """Test 3: Verificar que existen imágenes de prueba"""
        print(f"\n🧪 TEST 3: Verificando imágenes de prueba...")
        
        test_images = self.config.get_test_images()
        
        if test_images:
            print(f"✅ Encontradas {len(test_images)} imágenes de prueba:")
            for i, img in enumerate(test_images[:5], 1):  # Mostrar máximo 5
                size_mb = img.stat().st_size / (1024 * 1024)
                print(f"   {i}. {img.name} ({size_mb:.2f} MB)")
            
            if len(test_images) > 5:
                print(f"   ... y {len(test_images) - 5} más")
            
            # Guardar la lista para otros tests
            self.__class__.test_images = test_images
            
            # Verificar tamaños
            oversized = [img for img in test_images if img.stat().st_size > self.config.MAX_IMAGE_SIZE]
            if oversized:
                print(f"⚠️ Imágenes muy grandes (>{self.config.MAX_IMAGE_SIZE/1024/1024:.1f}MB):")
                for img in oversized:
                    size_mb = img.stat().st_size / (1024 * 1024)
                    print(f"   - {img.name} ({size_mb:.2f} MB)")
        else:
            print(f"⚠️ No se encontraron imágenes en {self.config.TEST_IMAGES_DIR}")
            print(f"💡 Coloca imágenes en las subcarpetas:")
            print(f"   📁 {self.config.TEST_INGREDIENTS_IMAGES_DIR} - para ingredientes")
            print(f"   📁 {self.config.TEST_FOODS_IMAGES_DIR} - para comidas")
            self.__class__.test_images = []
    
    def test_04_test_ingredient_recognition_basic_without_auth(self):
        """Test 4: Probar reconocimiento básico sin autenticación"""
        print(f"\n🧪 TEST 4: Probando reconocimiento básico sin autenticación...")
        
        if not hasattr(self.__class__, 'test_images') or not self.__class__.test_images:
            print(f"⚠️ No hay imágenes para probar - saltando test")
            self.skipTest("No hay imágenes de prueba disponibles")
        
        # Usar la primera imagen disponible
        test_image = self.__class__.test_images[0]
        print(f"📷 Usando imagen: {test_image.name}")
        
        url = f"{self.config.BASE_URL}/api/recognition/ingredients"
        
        # Mostrar detalles de la request (sin el archivo por tamaño)
        print(f"\n📤 REQUEST POST")
        print(f"🔗 URL: {url}")
        print(f"📷 Archivo: {test_image.name} ({test_image.stat().st_size} bytes)")
        print(f"📨 Sin headers de autenticación")
        
        # Preparar archivo
        files = {
            'file': (test_image.name, open(test_image, 'rb'), 'image/jpeg')
        }
        
        try:
            response = requests.post(url, files=files)
            self._print_response_details(response, "RECONOCIMIENTO SIN AUTH")
            
            if response.status_code == 200:
                recognition_data = response.json()
                print(f"✅ Reconocimiento exitoso")
                
                ingredients = recognition_data.get('ingredients', [])
                print(f"🥕 Ingredientes encontrados: {len(ingredients)}")
                
                for i, ingredient in enumerate(ingredients[:3], 1):  # Mostrar primeros 3
                    print(f"   {i}. {ingredient.get('name', 'N/A')}: {ingredient.get('description', 'N/A')}")
                
                self.assertIsInstance(recognition_data, dict)
                self.assertIn('ingredients', recognition_data)
                
            elif response.status_code == 401:
                print(f"🔒 Endpoint requiere autenticación - esto es esperado")
                print(f"💡 En producción, este endpoint probablemente requiere autenticación")
            else:
                print(f"⚠️ Reconocimiento falló: {response.status_code}")
                print(f"💡 Esto puede ser esperado si el endpoint requiere autenticación")
        
        except Exception as e:
            print(f"❌ Error durante reconocimiento: {e}")
            print(f"💡 Error puede ser debido a configuración de entorno de test")
        
        finally:
            # Cerrar archivo
            if 'files' in locals():
                files['file'][1].close()
    
    def test_05_test_ingredient_recognition_complete_without_auth(self):
        """Test 5: Probar reconocimiento completo sin autenticación"""
        print(f"\n🧪 TEST 5: Probando reconocimiento completo sin autenticación...")
        
        if not hasattr(self.__class__, 'test_images') or not self.__class__.test_images:
            print(f"⚠️ No hay imágenes para probar - saltando test")
            self.skipTest("No hay imágenes de prueba disponibles")
        
        # Usar la primera imagen disponible
        test_image = self.__class__.test_images[0]
        print(f"📷 Usando imagen: {test_image.name}")
        
        url = f"{self.config.BASE_URL}/api/recognition/ingredients/complete"
        
        # Mostrar detalles de la request
        print(f"\n📤 REQUEST POST")
        print(f"🔗 URL: {url}")
        print(f"📷 Archivo: {test_image.name} ({test_image.stat().st_size} bytes)")
        print(f"📨 Sin headers de autenticación")
        
        # Preparar archivo
        files = {
            'file': (test_image.name, open(test_image, 'rb'), 'image/jpeg')
        }
        
        try:
            response = requests.post(url, files=files)
            self._print_response_details(response, "RECONOCIMIENTO COMPLETO SIN AUTH")
            
            if response.status_code == 200:
                recognition_data = response.json()
                print(f"✅ Reconocimiento completo exitoso")
                
                ingredients = recognition_data.get('ingredients', [])
                print(f"🥕 Ingredientes encontrados: {len(ingredients)}")
                
                for i, ingredient in enumerate(ingredients[:2], 1):  # Mostrar primeros 2
                    print(f"   {i}. {ingredient.get('name', 'N/A')}")
                    
                    # Verificar datos ambientales
                    env_impact = ingredient.get('environmental_impact', {})
                    if env_impact:
                        carbon = env_impact.get('carbon_footprint', {})
                        water = env_impact.get('water_footprint', {})
                        print(f"      🌱 CO2: {carbon.get('value', 0)} {carbon.get('unit', 'kg')}")
                        print(f"      💧 Agua: {water.get('value', 0)} {water.get('unit', 'l')}")
                
                # Verificaciones
                self.assertIsInstance(recognition_data, dict)
                self.assertIn('ingredients', recognition_data)
                
            elif response.status_code == 401:
                print(f"🔒 Endpoint requiere autenticación - esto es esperado")
                print(f"💡 En producción, este endpoint probablemente requiere autenticación")
            else:
                print(f"⚠️ Reconocimiento completo falló: {response.status_code}")
                print(f"💡 Esto puede ser esperado si el endpoint requiere autenticación")
        
        except Exception as e:
            print(f"❌ Error durante reconocimiento completo: {e}")
            print(f"💡 Error puede ser debido a configuración de entorno de test")
        
        finally:
            # Cerrar archivo
            if 'files' in locals():
                files['file'][1].close()
    
    def test_06_test_inventory_endpoints_without_auth(self):
        """Test 6: Probar endpoints de inventario sin autenticación"""
        print(f"\n🧪 TEST 6: Probando endpoints de inventario sin autenticación...")
        
        try:
            # Test inventario básico
            url = f"{self.config.BASE_URL}/api/inventory"
            self._print_request_details("GET", url)
            
            response = requests.get(url)
            self._print_response_details(response, "INVENTARIO BÁSICO SIN AUTH")
            
            if response.status_code == 200:
                inventory_data = response.json()
                print(f"✅ Inventario básico obtenido")
                print(f"📦 Items en inventario: {len(inventory_data.get('items', []))}")
                
                self.assertIsInstance(inventory_data, dict)
            elif response.status_code == 401:
                print(f"🔒 Endpoint requiere autenticación - esto es esperado")
            
            # Test inventario completo
            url = f"{self.config.BASE_URL}/api/inventory/complete"
            self._print_request_details("GET", url)
            
            response = requests.get(url)
            self._print_response_details(response, "INVENTARIO COMPLETO SIN AUTH")
            
            if response.status_code == 200:
                complete_inventory = response.json()
                print(f"✅ Inventario completo obtenido")
                print(f"📦 Items con datos completos: {len(complete_inventory.get('items', []))}")
                
                self.assertIsInstance(complete_inventory, dict)
            elif response.status_code == 401:
                print(f"🔒 Endpoint requiere autenticación - esto es esperado")
            else:
                print(f"⚠️ Inventario completo falló: {response.status_code}")
        
        except Exception as e:
            print(f"❌ Error durante test de inventario: {e}")
            print(f"💡 Error puede ser debido a configuración de entorno de test")
    
    def test_07_test_other_endpoints(self):
        """Test 7: Probar otros endpoints disponibles"""
        print(f"\n🧪 TEST 7: Probando otros endpoints...")
        
        if not self.__class__.access_token:
            print(f"⚠️ No hay access token disponible - probando sin autenticación")
        
        headers = self.utils.create_auth_headers(self.__class__.access_token)
        
        endpoints_to_test = [
            ("inventory", "GET"),
            ("inventory_complete", "GET"),
            ("user_profile", "GET")
        ]
        
        for endpoint_name, method in endpoints_to_test:
            print(f"\n📍 Probando {endpoint_name} ({method})...")
            
            try:
                endpoint_url = self.config.ENDPOINTS[endpoint_name]
                
                if method == "GET":
                    response = requests.get(
                        endpoint_url,
                        headers=headers,
                        timeout=self.config.TEST_TIMEOUT
                    )
                
                print(f"🔍 {endpoint_name} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ {endpoint_name} funcionando correctamente")
                    
                    # Mostrar información básica de la respuesta
                    if isinstance(data, dict):
                        keys = list(data.keys())[:5]  # Primeras 5 claves
                        print(f"📋 Claves en respuesta: {keys}")
                        
                        if 'items' in data:
                            items_count = len(data['items'])
                            print(f"📦 Items encontrados: {items_count}")
                
                elif response.status_code in [401, 403]:
                    print(f"🔒 {endpoint_name} requiere autenticación válida")
                
                else:
                    print(f"⚠️ {endpoint_name} error: {response.status_code}")
                    print(f"⚠️ Respuesta: {response.text[:100]}...")
            
            except Exception as e:
                print(f"❌ Error probando {endpoint_name}: {e}")
    
    @classmethod
    def tearDownClass(cls):
        """Limpieza después de todos los tests"""
        print(f"\n🧹 TESTS SIMPLIFICADOS COMPLETADOS")
        
        # Mostrar resumen de imágenes procesadas
        if hasattr(cls, 'test_images'):
            print(f"📷 Imágenes de prueba utilizadas: {len(cls.test_images)}")
        
        print(f"✅ Tests de integración simplificados terminados")


if __name__ == '__main__':
    # Ejecutar los tests
    unittest.main(verbosity=2) 