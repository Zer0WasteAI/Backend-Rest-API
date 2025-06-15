"""
🎯 TEST DE PRECISIÓN CON IMÁGENES ESPECÍFICAS
===========================================

Test para evaluar la precisión del reconocimiento con:
- ensalada.jpg (comida preparada)
- pollo_con_mani.jpg (comida preparada) 
- ceviche_peruano.jpg (ingredientes crudos)

Con logs detallados de responses y análisis de precisión.
"""

import unittest
import time
import json
from pathlib import Path
from io import BytesIO
from datetime import datetime

# Importar el servicio directamente
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService


class TestPrecisionSpecificImages(unittest.TestCase):
    """Test de precisión con imágenes específicas"""
    
    def setUp(self):
        """Configuración para cada test"""
        self.ai_service = GeminiAdapterService()
        self.foods_dir = Path(__file__).parent.parent / "images" / "foods"
        
        # Imágenes específicas a probar
        self.ensalada_path = self.foods_dir / "ensalada.jpg"
        self.pollo_path = self.foods_dir / "pollo_con_mani.jpg"
        self.ceviche_path = self.foods_dir / "ceviche_peruano.jpg"
        
        # Verificar que las imágenes existen
        for path in [self.ensalada_path, self.pollo_path, self.ceviche_path]:
            if not path.exists():
                self.skipTest(f"❌ No se encontró {path.name}")
        
        print(f"\n🎯 INICIANDO TEST DE PRECISIÓN")
        print(f"📅 Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
    
    def _load_image_as_bytes(self, image_path: Path):
        """Cargar imagen como BytesIO"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return BytesIO(image_data)
    
    def _format_time(self, seconds):
        """Formatear tiempo en forma legible"""
        if seconds < 1:
            return f"{seconds*1000:.0f}ms"
        else:
            return f"{seconds:.2f}s"
    
    def _print_detailed_response(self, response, title, exec_time):
        """Imprimir response detallado con formato"""
        print(f"\n📋 {title}")
        print("=" * len(title))
        print(f"⏱️ Tiempo de procesamiento: {self._format_time(exec_time)}")
        print("\n🔍 RESPONSE COMPLETO:")
        print("-" * 40)
        print(json.dumps(response, indent=2, ensure_ascii=False))
        print("-" * 40)
    
    def _measure_and_analyze(self, func, image_bytes, image_name, recognition_type):
        """Medir tiempo y analizar response"""
        print(f"\n⏰ Iniciando {recognition_type} para {image_name}...")
        
        start_time = time.time()
        result = func([image_bytes])
        end_time = time.time()
        exec_time = end_time - start_time
        
        print(f"✅ Completado en: {self._format_time(exec_time)}")
        return result, exec_time
    
    def test_ensalada_recognition_detailed(self):
        """Test detallado con ensalada.jpg (comida preparada)"""
        print(f"\n🥗 ANÁLISIS DETALLADO: ENSALADA.JPG")
        print("=" * 50)
        print("📷 Tipo esperado: COMIDA PREPARADA")
        print("🎯 Debe detectar: Foods ✅ | No debe detectar: Ingredients ❌")
        
        ensalada_bytes = self._load_image_as_bytes(self.ensalada_path)
        
        # Test Foods Recognition
        foods_result, foods_time = self._measure_and_analyze(
            self.ai_service.recognize_foods, 
            ensalada_bytes, 
            "ensalada.jpg", 
            "FOODS Recognition"
        )
        
        self._print_detailed_response(
            foods_result, 
            "FOODS RECOGNITION - ENSALADA", 
            foods_time
        )
        
        # Test Ingredients Recognition
        ingredients_result, ingredients_time = self._measure_and_analyze(
            self.ai_service.recognize_ingredients, 
            ensalada_bytes, 
            "ensalada.jpg", 
            "INGREDIENTS Recognition"
        )
        
        self._print_detailed_response(
            ingredients_result, 
            "INGREDIENTS RECOGNITION - ENSALADA", 
            ingredients_time
        )
        
        # Análisis de precisión
        foods_count = len(foods_result.get('foods', []))
        ingredients_count = len(ingredients_result.get('ingredients', []))
        
        print(f"\n📊 ANÁLISIS DE PRECISIÓN - ENSALADA:")
        print(f"   • Foods detectados: {foods_count} (esperado: >0)")
        print(f"   • Ingredients detectados: {ingredients_count} (esperado: 0)")
        
        if foods_count > 0:
            print(f"   • ✅ CORRECTO: Detectó ensalada como comida preparada")
            for i, food in enumerate(foods_result.get('foods', [])):
                print(f"     {i+1}. {food.get('name', 'N/A')}")
                print(f"        Categoría: {food.get('category', 'N/A')}")
                print(f"        Calorías: {food.get('calories', 'N/A')}")
        else:
            print(f"   • ❌ ERROR: No detectó ensalada como comida")
        
        if ingredients_count == 0:
            print(f"   • ✅ CORRECTO: No detectó ensalada como ingredientes")
        else:
            print(f"   • ⚠️ INESPERADO: Detectó ensalada como ingredientes")
    
    def test_pollo_con_mani_recognition_detailed(self):
        """Test detallado con pollo_con_mani.jpg (comida preparada)"""
        print(f"\n🍗 ANÁLISIS DETALLADO: POLLO_CON_MANI.JPG")
        print("=" * 55)
        print("📷 Tipo esperado: COMIDA PREPARADA")
        print("🎯 Debe detectar: Foods ✅ | No debe detectar: Ingredients ❌")
        
        pollo_bytes = self._load_image_as_bytes(self.pollo_path)
        
        # Test Foods Recognition
        foods_result, foods_time = self._measure_and_analyze(
            self.ai_service.recognize_foods, 
            pollo_bytes, 
            "pollo_con_mani.jpg", 
            "FOODS Recognition"
        )
        
        self._print_detailed_response(
            foods_result, 
            "FOODS RECOGNITION - POLLO CON MANÍ", 
            foods_time
        )
        
        # Test Ingredients Recognition
        ingredients_result, ingredients_time = self._measure_and_analyze(
            self.ai_service.recognize_ingredients, 
            pollo_bytes, 
            "pollo_con_mani.jpg", 
            "INGREDIENTS Recognition"
        )
        
        self._print_detailed_response(
            ingredients_result, 
            "INGREDIENTS RECOGNITION - POLLO CON MANÍ", 
            ingredients_time
        )
        
        # Análisis de precisión
        foods_count = len(foods_result.get('foods', []))
        ingredients_count = len(ingredients_result.get('ingredients', []))
        
        print(f"\n📊 ANÁLISIS DE PRECISIÓN - POLLO CON MANÍ:")
        print(f"   • Foods detectados: {foods_count} (esperado: >0)")
        print(f"   • Ingredients detectados: {ingredients_count} (esperado: 0)")
        
        if foods_count > 0:
            print(f"   • ✅ CORRECTO: Detectó pollo como comida preparada")
            for i, food in enumerate(foods_result.get('foods', [])):
                print(f"     {i+1}. {food.get('name', 'N/A')}")
                print(f"        Categoría: {food.get('category', 'N/A')}")
                print(f"        Calorías: {food.get('calories', 'N/A')}")
                print(f"        Ingredientes: {', '.join(food.get('main_ingredients', []))}")
        else:
            print(f"   • ❌ ERROR: No detectó pollo como comida")
        
        if ingredients_count == 0:
            print(f"   • ✅ CORRECTO: No detectó pollo como ingredientes")
        else:
            print(f"   • ⚠️ INESPERADO: Detectó pollo como ingredientes")
    
    def test_ceviche_ingredients_recognition_detailed(self):
        """Test detallado con ceviche_peruano.jpg (ingredientes crudos)"""
        print(f"\n🐟 ANÁLISIS DETALLADO: CEVICHE_PERUANO.JPG")
        print("=" * 55)
        print("📷 Tipo esperado: INGREDIENTES CRUDOS")
        print("🎯 Debe detectar: Ingredients ✅ | No debe detectar: Foods ❌")
        
        ceviche_bytes = self._load_image_as_bytes(self.ceviche_path)
        
        # Test Ingredients Recognition
        ingredients_result, ingredients_time = self._measure_and_analyze(
            self.ai_service.recognize_ingredients, 
            ceviche_bytes, 
            "ceviche_peruano.jpg", 
            "INGREDIENTS Recognition"
        )
        
        self._print_detailed_response(
            ingredients_result, 
            "INGREDIENTS RECOGNITION - CEVICHE INGREDIENTES", 
            ingredients_time
        )
        
        # Test Foods Recognition
        foods_result, foods_time = self._measure_and_analyze(
            self.ai_service.recognize_foods, 
            ceviche_bytes, 
            "ceviche_peruano.jpg", 
            "FOODS Recognition"
        )
        
        self._print_detailed_response(
            foods_result, 
            "FOODS RECOGNITION - CEVICHE INGREDIENTES", 
            foods_time
        )
        
        # Análisis de precisión
        ingredients_count = len(ingredients_result.get('ingredients', []))
        foods_count = len(foods_result.get('foods', []))
        
        print(f"\n📊 ANÁLISIS DE PRECISIÓN - CEVICHE INGREDIENTES:")
        print(f"   • Ingredients detectados: {ingredients_count} (esperado: >0)")
        print(f"   • Foods detectados: {foods_count} (esperado: 0)")
        
        if ingredients_count > 0:
            print(f"   • ✅ CORRECTO: Detectó ingredientes crudos")
            for i, ing in enumerate(ingredients_result.get('ingredients', [])):
                print(f"     {i+1}. {ing.get('name', 'N/A')}")
                print(f"        Cantidad: {ing.get('quantity', 'N/A')} {ing.get('type_unit', '')}")
                print(f"        Almacenamiento: {ing.get('storage_type', 'N/A')}")
        else:
            print(f"   • ❌ ERROR: No detectó ingredientes crudos")
        
        if foods_count == 0:
            print(f"   • ✅ CORRECTO: No detectó ingredientes como comida")
        else:
            print(f"   • ⚠️ INESPERADO: Detectó ingredientes como comida")
            for i, food in enumerate(foods_result.get('foods', [])):
                print(f"     {i+1}. {food.get('name', 'N/A')}")
    
    def test_precision_summary(self):
        """Resumen final de precisión y performance"""
        print(f"\n🎯 RESUMEN FINAL DE PRECISIÓN")
        print("=" * 40)
        print("📊 Resultados esperados:")
        print("   • Ensalada → Foods: ✅ | Ingredients: ❌")
        print("   • Pollo → Foods: ✅ | Ingredients: ❌") 
        print("   • Ceviche → Ingredients: ✅ | Foods: ❌")
        print("\n💡 Todos los tests completados. Revisa los logs detallados arriba.")


if __name__ == '__main__':
    # Ejecutar tests en orden específico
    unittest.main(verbosity=2) 