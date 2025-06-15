"""
Configuración y utilidades para tests de integración
"""
import os
import sys
from pathlib import Path

# Agregar la raíz del proyecto al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestConfig:
    """Configuración centralizada para tests"""
    
    # URLs y endpoints
    BASE_URL = "http://localhost:3000"
    API_BASE = f"{BASE_URL}/api"
    
    # Directorios
    TEST_DIR = Path(__file__).parent
    TEST_IMAGES_DIR = TEST_DIR / "images"
    TEST_INGREDIENTS_IMAGES_DIR = TEST_IMAGES_DIR / "ingredients"
    TEST_FOODS_IMAGES_DIR = TEST_IMAGES_DIR / "foods"
    PROJECT_ROOT = TEST_DIR.parent
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH = PROJECT_ROOT / "src/config/firebase_credentials.json"
    
    # Endpoints específicos
    ENDPOINTS = {
        "status": f"{BASE_URL}/status",
        "firebase_signin": f"{API_BASE}/auth/firebase-signin",
        "recognition_basic": f"{API_BASE}/recognition/ingredients",
        "recognition_complete": f"{API_BASE}/recognition/ingredients/complete",
        "inventory": f"{API_BASE}/inventory",
        "inventory_complete": f"{API_BASE}/inventory/complete",
        "recipes": f"{API_BASE}/recipes",
        "user_profile": f"{API_BASE}/user/profile"
    }
    
    # Configuración de tests
    TEST_TIMEOUT = 30  # segundos
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
    
    @classmethod
    def get_test_images(cls, category=None):
        """
        Obtiene todas las imágenes de prueba disponibles
        
        Args:
            category (str): 'ingredients', 'foods', o None para todas
        """
        # Crear directorios si no existen
        cls.TEST_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEST_INGREDIENTS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        cls.TEST_FOODS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
        
        # Determinar qué directorios buscar
        search_dirs = []
        if category == 'ingredients':
            search_dirs = [cls.TEST_INGREDIENTS_IMAGES_DIR]
        elif category == 'foods':
            search_dirs = [cls.TEST_FOODS_IMAGES_DIR]
        elif category is None:
            # Buscar en ambos subdirectorios y en la raíz
            search_dirs = [
                cls.TEST_IMAGES_DIR,
                cls.TEST_INGREDIENTS_IMAGES_DIR, 
                cls.TEST_FOODS_IMAGES_DIR
            ]
        else:
            search_dirs = [cls.TEST_IMAGES_DIR]
        
        test_images = []
        for search_dir in search_dirs:
            if search_dir.exists():
                for ext in cls.SUPPORTED_IMAGE_FORMATS:
                    # Solo en el directorio específico, no recursivo para la raíz
                    if search_dir == cls.TEST_IMAGES_DIR:
                        test_images.extend(search_dir.glob(f"{ext}"))
                        test_images.extend(search_dir.glob(f"{ext.upper()}"))
                    else:
                        test_images.extend(search_dir.glob(f"*{ext}"))
                        test_images.extend(search_dir.glob(f"*{ext.upper()}"))
        
        return sorted(test_images)
    
    @classmethod
    def validate_environment(cls):
        """Valida que el entorno esté configurado correctamente para tests"""
        issues = []
        
        # Verificar credenciales Firebase
        if not cls.FIREBASE_CREDENTIALS_PATH.exists():
            issues.append(f"Credenciales Firebase no encontradas: {cls.FIREBASE_CREDENTIALS_PATH}")
        
        # Verificar carpetas de imágenes
        if not cls.TEST_IMAGES_DIR.exists():
            issues.append(f"Carpeta de imágenes no existe: {cls.TEST_IMAGES_DIR}")
        
        # Verificar que hay imágenes para probar
        test_images = cls.get_test_images()
        if not test_images:
            issues.append(f"No hay imágenes de prueba en: {cls.TEST_IMAGES_DIR}")
            issues.append(f"Subcarpetas esperadas: {cls.TEST_INGREDIENTS_IMAGES_DIR}, {cls.TEST_FOODS_IMAGES_DIR}")
        
        return issues
    
    @classmethod
    def print_environment_info(cls):
        """Imprime información del entorno de tests"""
        print(f"\n🔧 CONFIGURACIÓN DE ENTORNO DE TESTS")
        print(f"📁 Directorio de tests: {cls.TEST_DIR}")
        print(f"📁 Directorio de imágenes: {cls.TEST_IMAGES_DIR}")
        print(f"   📁 Ingredientes: {cls.TEST_INGREDIENTS_IMAGES_DIR}")
        print(f"   📁 Comidas: {cls.TEST_FOODS_IMAGES_DIR}")
        print(f"🔗 URL base del API: {cls.BASE_URL}")
        print(f"🔥 Credenciales Firebase: {cls.FIREBASE_CREDENTIALS_PATH}")
        
        # Mostrar imágenes disponibles por categoría
        ingredients_images = cls.get_test_images('ingredients')
        foods_images = cls.get_test_images('foods')
        all_images = cls.get_test_images()
        
        print(f"📷 Imágenes de prueba disponibles:")
        print(f"   🥕 Ingredientes: {len(ingredients_images)}")
        print(f"   🍽️ Comidas: {len(foods_images)}")
        print(f"   📊 Total: {len(all_images)}")
        
        if all_images:
            print(f"   Ejemplos:")
            for img in all_images[:3]:  # Mostrar primeras 3
                category = "ingredientes" if "ingredients" in str(img) else "comidas" if "foods" in str(img) else "raíz"
                print(f"      - {img.name} ({category})")
            if len(all_images) > 3:
                print(f"      ... y {len(all_images) - 3} más")
        else:
            print(f"⚠️ No hay imágenes de prueba disponibles")
        
        # Mostrar problemas si los hay
        issues = cls.validate_environment()
        if issues:
            print(f"\n⚠️ PROBLEMAS DETECTADOS:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ Entorno configurado correctamente")


class TestUtils:
    """Utilidades comunes para tests"""
    
    @staticmethod
    def create_auth_headers(token: str = None) -> dict:
        """Crea headers de autenticación"""
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    @staticmethod
    def create_multipart_headers(token: str = None) -> dict:
        """Crea headers para requests multipart"""
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    @staticmethod
    def format_response_summary(response_data: dict) -> str:
        """Crea un resumen legible de una respuesta"""
        if not isinstance(response_data, dict):
            return f"Tipo de respuesta: {type(response_data)}"
        
        summary = []
        
        # Información de ingredientes si existe
        if 'ingredients' in response_data:
            ingredients = response_data['ingredients']
            summary.append(f"🥕 Ingredientes: {len(ingredients)}")
            
            for i, ing in enumerate(ingredients[:3], 1):
                name = ing.get('name', 'N/A')
                summary.append(f"   {i}. {name}")
        
        # Información de inventario si existe
        if 'items' in response_data:
            items = response_data['items']
            summary.append(f"📦 Items: {len(items)}")
        
        # Información de usuario si existe
        if 'user' in response_data:
            user = response_data['user']
            summary.append(f"👤 Usuario: {user.get('uid', 'N/A')}")
        
        # Información de tokens si existe
        if 'access_token' in response_data:
            token = response_data['access_token']
            summary.append(f"🔑 Access Token: {len(token)} chars")
        
        # Información de estado si existe
        if 'status' in response_data:
            status = response_data['status']
            summary.append(f"📊 Estado: {status}")
        
        # Campos adicionales
        other_fields = [k for k in response_data.keys() 
                       if k not in ['ingredients', 'items', 'user', 'access_token', 'status']]
        if other_fields:
            summary.append(f"📋 Otros campos: {', '.join(other_fields)}")
        
        return '\n'.join(summary) if summary else "Sin información específica"
    
    @staticmethod
    def format_firebase_response(response_data: dict) -> str:
        """Formatea específicamente respuestas de Firebase"""
        if not isinstance(response_data, dict):
            return f"Respuesta no es dict: {type(response_data)}"
        
        summary = ["🔥 FIREBASE RESPONSE DETAILS:"]
        
        # Información de usuario
        if 'user' in response_data:
            user = response_data['user']
            summary.append(f"👤 Usuario:")
            summary.append(f"   UID: {user.get('uid', 'N/A')}")
            summary.append(f"   Email: {user.get('email', 'N/A')}")
            summary.append(f"   Proveedor: {user.get('providerData', 'N/A')}")
            summary.append(f"   Anónimo: {user.get('isAnonymous', 'N/A')}")
        
        # Token de acceso
        if 'access_token' in response_data:
            token = response_data['access_token']
            summary.append(f"🔑 Access Token:")
            summary.append(f"   Longitud: {len(token)} caracteres")
            summary.append(f"   Preview: {token[:30]}...")
        
        # ID Token si existe
        if 'id_token' in response_data:
            id_token = response_data['id_token']
            summary.append(f"🆔 ID Token:")
            summary.append(f"   Longitud: {len(id_token)} caracteres")
        
        # Refresh token si existe
        if 'refresh_token' in response_data:
            refresh_token = response_data['refresh_token']
            summary.append(f"🔄 Refresh Token:")
            summary.append(f"   Longitud: {len(refresh_token)} caracteres")
        
        # Claims personalizados
        if 'custom_claims' in response_data:
            claims = response_data['custom_claims']
            summary.append(f"📋 Custom Claims: {claims}")
        
        # Otros campos
        other_fields = [k for k in response_data.keys() 
                       if k not in ['user', 'access_token', 'id_token', 'refresh_token', 'custom_claims']]
        if other_fields:
            summary.append(f"📄 Otros campos: {', '.join(other_fields)}")
        
        return '\n'.join(summary)
    
    @staticmethod
    def format_error_response(response_data: dict, status_code: int) -> str:
        """Formatea respuestas de error de manera legible"""
        summary = [f"❌ ERROR RESPONSE (Status: {status_code})"]
        
        if isinstance(response_data, dict):
            # Mensaje de error
            if 'error' in response_data:
                error = response_data['error']
                if isinstance(error, dict):
                    summary.append(f"   Mensaje: {error.get('message', 'N/A')}")
                    summary.append(f"   Código: {error.get('code', 'N/A')}")
                    summary.append(f"   Tipo: {error.get('type', 'N/A')}")
                else:
                    summary.append(f"   Error: {error}")
            
            # Mensaje general
            if 'message' in response_data:
                summary.append(f"   Mensaje: {response_data['message']}")
            
            # Detalles adicionales
            if 'details' in response_data:
                summary.append(f"   Detalles: {response_data['details']}")
        
        else:
            summary.append(f"   Contenido: {str(response_data)[:200]}")
        
        return '\n'.join(summary)
    
    @staticmethod
    def validate_ingredient_structure(ingredient: dict) -> bool:
        """Valida la estructura básica de un ingrediente"""
        required_fields = ['name', 'description']
        return all(field in ingredient for field in required_fields)
    
    @staticmethod
    def validate_complete_ingredient_structure(ingredient: dict) -> bool:
        """Valida la estructura completa de un ingrediente (con datos ambientales)"""
        basic_valid = TestUtils.validate_ingredient_structure(ingredient)
        if not basic_valid:
            return False
        
        # Verificar campos adicionales
        return (
            'environmental_impact' in ingredient and
            'utilization_ideas' in ingredient
        )
    
    @staticmethod
    def print_ingredient_info(ingredient: dict, index: int = None):
        """Imprime información de un ingrediente de forma formateada"""
        prefix = f"   {index}. " if index is not None else "   "
        
        print(f"{prefix}{ingredient.get('name', 'N/A')}")
        print(f"       📝 {ingredient.get('description', 'N/A')}")
        
        # Mostrar información ambiental si existe
        env_impact = ingredient.get('environmental_impact', {})
        if env_impact:
            carbon = env_impact.get('carbon_footprint', {})
            water = env_impact.get('water_footprint', {})
            if carbon:
                print(f"       🌱 CO2: {carbon.get('value', 0)} {carbon.get('unit', 'kg')}")
            if water:
                print(f"       💧 Agua: {water.get('value', 0)} {water.get('unit', 'l')}")
        
        # Mostrar ideas de utilización si existen
        utilization = ingredient.get('utilization_ideas', [])
        if utilization:
            print(f"       💡 Ideas de utilización: {len(utilization)}")
            for idea in utilization[:2]:  # Mostrar primeras 2
                title = idea.get('title', 'N/A')
                idea_type = idea.get('type', 'N/A')
                print(f"          - {title} ({idea_type})")
    
    @staticmethod
    def print_detailed_response_analysis(response_data: dict, response_type: str = "API"):
        """Análisis detallado de una respuesta para debugging"""
        print(f"\n🔍 ANÁLISIS DETALLADO DE RESPUESTA {response_type}")
        print(f"📊 Tipo de datos: {type(response_data)}")
        
        if isinstance(response_data, dict):
            print(f"📋 Campos principales: {list(response_data.keys())}")
            print(f"📏 Número de campos: {len(response_data)}")
            
            # Análisis por tipo de respuesta
            if 'ingredients' in response_data:
                ingredients = response_data['ingredients']
                print(f"🥕 ANÁLISIS DE INGREDIENTES:")
                print(f"   Cantidad: {len(ingredients)}")
                
                if ingredients:
                    first_ing = ingredients[0]
                    print(f"   Estructura del primero: {list(first_ing.keys())}")
                    
                    # Verificar consistencia
                    all_keys = set()
                    for ing in ingredients:
                        all_keys.update(ing.keys())
                    print(f"   Todos los campos únicos: {sorted(all_keys)}")
            
            elif 'user' in response_data:
                user = response_data['user']
                print(f"👤 ANÁLISIS DE USUARIO:")
                print(f"   Campos: {list(user.keys()) if isinstance(user, dict) else 'No es dict'}")
            
            elif 'items' in response_data:
                items = response_data['items']
                print(f"📦 ANÁLISIS DE INVENTARIO:")
                print(f"   Cantidad de items: {len(items)}")
        
        else:
            print(f"📄 Contenido (primeros 300 chars): {str(response_data)[:300]}")


if __name__ == '__main__':
    # Mostrar información del entorno cuando se ejecuta directamente
    TestConfig.print_environment_info() 