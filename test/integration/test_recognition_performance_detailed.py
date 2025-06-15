"""
🚀 TEST DETALLADO DE PERFORMANCE Y RESPONSES
=============================================

Test para ver responses completos y medir tiempos de reconocimiento
de ambos sistemas (foods e ingredients) con ambas imágenes.
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


class TestRecognitionPerformanceDetailed(unittest.TestCase):
    """Test detallado de performance y responses completos"""
    
    def setUp(self):
        """Configuración para cada test"""
        self.ai_service = GeminiAdapterService()
        self.foods_dir = Path(__file__).parent.parent / "images" / "foods"
        
        # Verificar que las imágenes existen
        self.ceviche_path = self.foods_dir / "ceviche_peruano.jpg"
        self.pollo_path = self.foods_dir / "pollo_con_mani.jpg"
        
        if not self.ceviche_path.exists():
            self.skipTest("❌ No se encontró ceviche_peruano.jpg")
        if not self.pollo_path.exists():
            self.skipTest("❌ No se encontró pollo_con_mani.jpg")
        
        # Para almacenar todos los resultados
        self.results = {}
    
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
    
    def _print_json_response(self, response, title):
        """Imprimir response en formato JSON limpio"""
        print(f"\n📋 {title}")
        print("=" * len(title))
        print(json.dumps(response, indent=2, ensure_ascii=False))
    
    def _measure_recognition_time(self, func, *args):
        """Medir tiempo de ejecución de una función"""
        start_time = time.time()
        result = func(*args)
        end_time = time.time()
        execution_time = end_time - start_time
        return result, execution_time
    
    def test_ceviche_foods_recognition_detailed(self):
        """Test detallado de foods recognition con ceviche"""
        print(f"\n🍽️ FOODS RECOGNITION - CEVICHE PERUANO (Ingredientes)")
        print("=" * 65)
        
        ceviche_bytes = self._load_image_as_bytes(self.ceviche_path)
        
        print(f"⏰ Iniciando reconocimiento de foods...")
        result, exec_time = self._measure_recognition_time(
            self.ai_service.recognize_foods, [ceviche_bytes]
        )
        
        print(f"✅ Completado en: {self._format_time(exec_time)}")
        
        self._print_json_response(result, "RESPONSE COMPLETO - FOODS RECOGNITION (CEVICHE)")
        
        # Guardar resultado
        self.results['ceviche_foods'] = {
            'response': result,
            'execution_time': exec_time,
            'foods_count': len(result.get('foods', []))
        }
        
        print(f"\n📊 ANÁLISIS:")
        print(f"   • Tiempo de procesamiento: {self._format_time(exec_time)}")
        print(f"   • Foods detectados: {len(result.get('foods', []))}")
        print(f"   • Comportamiento esperado: NO debería detectar foods ❌")
        
        if len(result.get('foods', [])) == 0:
            print(f"   • ✅ CORRECTO: No detectó ingredientes como foods")
        else:
            print(f"   • ⚠️ INESPERADO: Detectó ingredientes como foods")
    
    def test_ceviche_ingredients_recognition_detailed(self):
        """Test detallado de ingredients recognition con ceviche"""
        print(f"\n🥕 INGREDIENTS RECOGNITION - CEVICHE PERUANO (Ingredientes)")
        print("=" * 70)
        
        ceviche_bytes = self._load_image_as_bytes(self.ceviche_path)
        
        print(f"⏰ Iniciando reconocimiento de ingredients...")
        result, exec_time = self._measure_recognition_time(
            self.ai_service.recognize_ingredients, [ceviche_bytes]
        )
        
        print(f"✅ Completado en: {self._format_time(exec_time)}")
        
        self._print_json_response(result, "RESPONSE COMPLETO - INGREDIENTS RECOGNITION (CEVICHE)")
        
        # Guardar resultado
        self.results['ceviche_ingredients'] = {
            'response': result,
            'execution_time': exec_time,
            'ingredients_count': len(result.get('ingredients', []))
        }
        
        print(f"\n📊 ANÁLISIS:")
        print(f"   • Tiempo de procesamiento: {self._format_time(exec_time)}")
        print(f"   • Ingredients detectados: {len(result.get('ingredients', []))}")
        print(f"   • Comportamiento esperado: SÍ debería detectar ingredients ✅")
        
        if len(result.get('ingredients', [])) > 0:
            print(f"   • ✅ CORRECTO: Detectó ingredientes")
            for i, ing in enumerate(result.get('ingredients', [])):
                print(f"     {i+1}. {ing.get('name', 'N/A')} - {ing.get('quantity', 'N/A')} {ing.get('type_unit', '')}")
        else:
            print(f"   • ⚠️ INESPERADO: No detectó ingredientes")
    
    def test_pollo_foods_recognition_detailed(self):
        """Test detallado de foods recognition con pollo"""
        print(f"\n🍽️ FOODS RECOGNITION - POLLO CON MANÍ (Comida Preparada)")
        print("=" * 65)
        
        pollo_bytes = self._load_image_as_bytes(self.pollo_path)
        
        print(f"⏰ Iniciando reconocimiento de foods...")
        result, exec_time = self._measure_recognition_time(
            self.ai_service.recognize_foods, [pollo_bytes]
        )
        
        print(f"✅ Completado en: {self._format_time(exec_time)}")
        
        self._print_json_response(result, "RESPONSE COMPLETO - FOODS RECOGNITION (POLLO)")
        
        # Guardar resultado
        self.results['pollo_foods'] = {
            'response': result,
            'execution_time': exec_time,
            'foods_count': len(result.get('foods', []))
        }
        
        print(f"\n📊 ANÁLISIS:")
        print(f"   • Tiempo de procesamiento: {self._format_time(exec_time)}")
        print(f"   • Foods detectados: {len(result.get('foods', []))}")
        print(f"   • Comportamiento esperado: SÍ debería detectar foods ✅")
        
        if len(result.get('foods', [])) > 0:
            print(f"   • ✅ CORRECTO: Detectó comida preparada")
            for i, food in enumerate(result.get('foods', [])):
                print(f"     {i+1}. {food.get('name', 'N/A')} - {food.get('category', 'N/A')} - {food.get('calories', 'N/A')} cal")
        else:
            print(f"   • ⚠️ INESPERADO: No detectó comida preparada")
    
    def test_pollo_ingredients_recognition_detailed(self):
        """Test detallado de ingredients recognition con pollo"""
        print(f"\n🥕 INGREDIENTS RECOGNITION - POLLO CON MANÍ (Comida Preparada)")
        print("=" * 70)
        
        pollo_bytes = self._load_image_as_bytes(self.pollo_path)
        
        print(f"⏰ Iniciando reconocimiento de ingredients...")
        result, exec_time = self._measure_recognition_time(
            self.ai_service.recognize_ingredients, [pollo_bytes]
        )
        
        print(f"✅ Completado en: {self._format_time(exec_time)}")
        
        self._print_json_response(result, "RESPONSE COMPLETO - INGREDIENTS RECOGNITION (POLLO)")
        
        # Guardar resultado
        self.results['pollo_ingredients'] = {
            'response': result,
            'execution_time': exec_time,
            'ingredients_count': len(result.get('ingredients', []))
        }
        
        print(f"\n📊 ANÁLISIS:")
        print(f"   • Tiempo de procesamiento: {self._format_time(exec_time)}")
        print(f"   • Ingredients detectados: {len(result.get('ingredients', []))}")
        print(f"   • Comportamiento esperado: NO debería detectar ingredients ❌")
        
        if len(result.get('ingredients', [])) == 0:
            print(f"   • ✅ CORRECTO: No detectó comida preparada como ingredients")
        else:
            print(f"   • ⚠️ INESPERADO: Detectó comida preparada como ingredients")
            for i, ing in enumerate(result.get('ingredients', [])):
                print(f"     {i+1}. {ing.get('name', 'N/A')}")
    
    def test_performance_summary(self):
        """Resumen final de performance y validaciones"""
        print(f"\n🚀 RESUMEN FINAL DE PERFORMANCE")
        print("=" * 40)
        
        if not self.results:
            print("❌ No hay resultados para mostrar")
            return
        
        print(f"\n⏱️ TIEMPOS DE EJECUCIÓN:")
        print("-" * 30)
        
        total_time = 0
        for test_name, data in self.results.items():
            exec_time = data['execution_time']
            total_time += exec_time
            print(f"   • {test_name:25}: {self._format_time(exec_time)}")
        
        print(f"   • {'TOTAL':25}: {self._format_time(total_time)}")
        print(f"   • {'PROMEDIO':25}: {self._format_time(total_time / len(self.results))}")
        
        print(f"\n📊 RESUMEN DE DETECCIONES:")
        print("-" * 35)
        
        # Extraer conteos
        ceviche_foods = self.results.get('ceviche_foods', {}).get('foods_count', 0)
        ceviche_ingredients = self.results.get('ceviche_ingredients', {}).get('ingredients_count', 0)
        pollo_foods = self.results.get('pollo_foods', {}).get('foods_count', 0)
        pollo_ingredients = self.results.get('pollo_ingredients', {}).get('ingredients_count', 0)
        
        print(f"   • Ceviche → Foods: {ceviche_foods} (esperado: 0)")
        print(f"   • Ceviche → Ingredients: {ceviche_ingredients} (esperado: >0)")
        print(f"   • Pollo → Foods: {pollo_foods} (esperado: >0)")
        print(f"   • Pollo → Ingredients: {pollo_ingredients} (esperado: 0)")
        
        print(f"\n✅ VALIDACIONES:")
        print("-" * 20)
        
        validations = []
        
        # Validar comportamientos esperados
        if ceviche_foods == 0:
            validations.append("✅ Ceviche NO detectado como food")
        else:
            validations.append("❌ Ceviche incorrectamente detectado como food")
        
        if ceviche_ingredients > 0:
            validations.append("✅ Ceviche SÍ detectado como ingredients")
        else:
            validations.append("❌ Ceviche NO detectado como ingredients")
        
        if pollo_foods > 0:
            validations.append("✅ Pollo SÍ detectado como food")
        else:
            validations.append("❌ Pollo NO detectado como food")
        
        if pollo_ingredients == 0:
            validations.append("✅ Pollo NO detectado como ingredients")
        else:
            validations.append("❌ Pollo incorrectamente detectado como ingredients")
        
        for validation in validations:
            print(f"   {validation}")
        
        # Calcular score de éxito
        success_count = sum(1 for v in validations if v.startswith("✅"))
        success_rate = (success_count / len(validations)) * 100
        
        print(f"\n🎯 SCORE DE ÉXITO: {success_rate:.1f}% ({success_count}/{len(validations)})")
        
        if success_rate == 100:
            print("🎉 ¡PERFECTO! Todos los sistemas funcionan correctamente")
        elif success_rate >= 75:
            print("👍 Buen rendimiento, revisar casos fallidos")
        else:
            print("⚠️ Hay problemas que necesitan atención")


if __name__ == '__main__':
    # Ejecutar tests en orden específico
    suite = unittest.TestSuite()
    
    # Agregar tests en orden
    suite.addTest(TestRecognitionPerformanceDetailed('test_ceviche_foods_recognition_detailed'))
    suite.addTest(TestRecognitionPerformanceDetailed('test_ceviche_ingredients_recognition_detailed'))
    suite.addTest(TestRecognitionPerformanceDetailed('test_pollo_foods_recognition_detailed'))
    suite.addTest(TestRecognitionPerformanceDetailed('test_pollo_ingredients_recognition_detailed'))
    suite.addTest(TestRecognitionPerformanceDetailed('test_performance_summary'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite) 