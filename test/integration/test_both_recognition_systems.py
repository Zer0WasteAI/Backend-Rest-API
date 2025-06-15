"""
🧪 TEST COMPREHENSIVO DE AMBOS SISTEMAS DE RECONOCIMIENTO
========================================================

Test completo para validar:
1. Foods recognition con ceviche_peruano.jpg y pollo_con_mani.jpg
2. Ingredients recognition con ambas imágenes
3. Validación de comportamiento esperado
"""

import unittest
from pathlib import Path
from io import BytesIO

# Importar el servicio directamente
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService


class TestBothRecognitionSystems(unittest.TestCase):
    """Test comprehensivo de ambos sistemas de reconocimiento"""
    
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
    
    def _load_image_as_bytes(self, image_path: Path):
        """Cargar imagen como BytesIO"""
        with open(image_path, 'rb') as f:
            image_data = f.read()
        return BytesIO(image_data)
    
    def test_foods_recognition_comprehensive(self):
        """Test comprehensivo del sistema de foods recognition"""
        print(f"\n🍽️ TEST COMPREHENSIVO: FOODS RECOGNITION")
        print("=" * 50)
        
        # Test 1: ceviche_peruano.jpg (ingredientes crudos - NO debe detectar foods)
        print(f"\n📷 TEST 1: ceviche_peruano.jpg (ingredientes crudos)")
        print("-" * 40)
        
        ceviche_bytes = self._load_image_as_bytes(self.ceviche_path)
        result_ceviche = self.ai_service.recognize_foods([ceviche_bytes])
        foods_ceviche = result_ceviche.get("foods", [])
        
        print(f"🍽️ Foods detectados: {len(foods_ceviche)}")
        
        if len(foods_ceviche) == 0:
            print("✅ CORRECTO: No detectó ingredientes crudos como comidas")
        else:
            print("❌ ERROR: Detectó ingredientes como comidas:")
            for i, food in enumerate(foods_ceviche):
                print(f"   {i+1}. {food.get('name', 'Sin nombre')}")
        
        # Test 2: pollo_con_mani.jpg (comida preparada - SÍ debe detectar foods)
        print(f"\n📷 TEST 2: pollo_con_mani.jpg (comida preparada)")
        print("-" * 40)
        
        pollo_bytes = self._load_image_as_bytes(self.pollo_path)
        result_pollo = self.ai_service.recognize_foods([pollo_bytes])
        foods_pollo = result_pollo.get("foods", [])
        
        print(f"🍽️ Foods detectados: {len(foods_pollo)}")
        
        if len(foods_pollo) > 0:
            print("✅ CORRECTO: Detectó comida preparada:")
            for i, food in enumerate(foods_pollo):
                print(f"   {i+1}. {food.get('name', 'Sin nombre')}")
                print(f"      Categoría: {food.get('category', 'N/A')}")
                print(f"      Calorías: {food.get('calories', 'N/A')}")
        else:
            print("❌ ERROR: No detectó comida preparada cuando debería")
        
        # Verificaciones
        self.assertEqual(len(foods_ceviche), 0, 
                        "ceviche_peruano.jpg (ingredientes) NO debe ser detectado como food")
        self.assertGreater(len(foods_pollo), 0, 
                          "pollo_con_mani.jpg (comida preparada) SÍ debe ser detectado como food")
        
        print(f"\n🎉 FOODS RECOGNITION: TODOS LOS TESTS PASARON")
    
    def test_ingredients_recognition_comprehensive(self):
        """Test comprehensivo del sistema de ingredients recognition"""
        print(f"\n🥕 TEST COMPREHENSIVO: INGREDIENTS RECOGNITION")
        print("=" * 55)
        
        # Test 1: ceviche_peruano.jpg (ingredientes crudos - SÍ debe detectar ingredients)
        print(f"\n📷 TEST 1: ceviche_peruano.jpg (ingredientes crudos)")
        print("-" * 40)
        
        ceviche_bytes = self._load_image_as_bytes(self.ceviche_path)
        result_ceviche = self.ai_service.recognize_ingredients([ceviche_bytes])
        ingredients_ceviche = result_ceviche.get("ingredients", [])
        
        print(f"🥕 Ingredientes detectados: {len(ingredients_ceviche)}")
        
        if len(ingredients_ceviche) > 0:
            print("✅ CORRECTO: Detectó ingredientes crudos:")
            for i, ing in enumerate(ingredients_ceviche):
                print(f"   {i+1}. {ing.get('name', 'Sin nombre')}")
                print(f"      Cantidad: {ing.get('quantity', 'N/A')} {ing.get('type_unit', '')}")
                print(f"      Almacenamiento: {ing.get('storage_type', 'N/A')}")
        else:
            print("❌ ERROR: No detectó ingredientes cuando debería")
        
        # Test 2: pollo_con_mani.jpg (comida preparada - NO debe detectar ingredients)
        print(f"\n📷 TEST 2: pollo_con_mani.jpg (comida preparada)")
        print("-" * 40)
        
        pollo_bytes = self._load_image_as_bytes(self.pollo_path)
        result_pollo = self.ai_service.recognize_ingredients([pollo_bytes])
        ingredients_pollo = result_pollo.get("ingredients", [])
        
        print(f"🥕 Ingredientes detectados: {len(ingredients_pollo)}")
        
        if len(ingredients_pollo) == 0:
            print("✅ CORRECTO: No detectó comida preparada como ingredientes")
        else:
            print("❌ ERROR: Detectó comida preparada como ingredientes:")
            for i, ing in enumerate(ingredients_pollo):
                print(f"   {i+1}. {ing.get('name', 'Sin nombre')}")
        
        # Verificaciones
        self.assertGreater(len(ingredients_ceviche), 0, 
                          "ceviche_peruano.jpg (ingredientes) SÍ debe ser detectado como ingredients")
        self.assertEqual(len(ingredients_pollo), 0, 
                        "pollo_con_mani.jpg (comida preparada) NO debe ser detectado como ingredients")
        
        print(f"\n🎉 INGREDIENTS RECOGNITION: TODOS LOS TESTS PASARON")
    
    def test_cross_validation_matrix(self):
        """Matrix de validación cruzada completa"""
        print(f"\n🔄 MATRIX DE VALIDACIÓN CRUZADA")
        print("=" * 40)
        
        # Cargar ambas imágenes
        ceviche_bytes = self._load_image_as_bytes(self.ceviche_path)
        pollo_bytes = self._load_image_as_bytes(self.pollo_path)
        
        print(f"\n📊 RESULTADOS MATRIX:")
        print(f"{'':20} {'Ceviche (Ingred.)':18} {'Pollo (Comida)':18}")
        print("-" * 60)
        
        # Foods recognition
        foods_ceviche = self.ai_service.recognize_foods([ceviche_bytes]).get("foods", [])
        foods_pollo = self.ai_service.recognize_foods([pollo_bytes]).get("foods", [])
        
        ceviche_foods_status = "❌ NO" if len(foods_ceviche) == 0 else f"⚠️ SÍ ({len(foods_ceviche)})"
        pollo_foods_status = "✅ SÍ" if len(foods_pollo) > 0 else f"❌ NO"
        
        print(f"{'Foods Recognition:':<20} {ceviche_foods_status:<18} {pollo_foods_status:<18}")
        
        # Ingredients recognition
        ingredients_ceviche = self.ai_service.recognize_ingredients([ceviche_bytes]).get("ingredients", [])
        ingredients_pollo = self.ai_service.recognize_ingredients([pollo_bytes]).get("ingredients", [])
        
        ceviche_ing_status = "✅ SÍ" if len(ingredients_ceviche) > 0 else f"❌ NO"
        pollo_ing_status = "❌ NO" if len(ingredients_pollo) == 0 else f"⚠️ SÍ ({len(ingredients_pollo)})"
        
        print(f"{'Ingredients Recog.:':<20} {ceviche_ing_status:<18} {pollo_ing_status:<18}")
        
        print(f"\n📋 LEYENDA:")
        print(f"   ✅ = Comportamiento correcto esperado")
        print(f"   ❌ = Comportamiento correcto esperado (NO detecta)")
        print(f"   ⚠️ = Comportamiento inesperado")
        
        # Verificaciones finales
        print(f"\n🔍 VERIFICACIONES:")
        
        # Verificar que ceviche NO se detecta como food
        if len(foods_ceviche) == 0:
            print("✅ Ceviche (ingredientes) correctamente NO detectado como food")
        else:
            print("❌ ERROR: Ceviche detectado como food cuando son ingredientes")
            self.fail("Ceviche (ingredientes) no debe detectarse como food")
        
        # Verificar que pollo SÍ se detecta como food
        if len(foods_pollo) > 0:
            print("✅ Pollo (comida) correctamente detectado como food")
        else:
            print("❌ ERROR: Pollo no detectado como food cuando es comida preparada")
            self.fail("Pollo (comida preparada) debe detectarse como food")
        
        # Verificar que ceviche SÍ se detecta como ingredients
        if len(ingredients_ceviche) > 0:
            print("✅ Ceviche (ingredientes) correctamente detectado como ingredients")
        else:
            print("❌ ERROR: Ceviche no detectado como ingredients")
            self.fail("Ceviche (ingredientes) debe detectarse como ingredients")
        
        # Verificar que pollo NO se detecta como ingredients
        if len(ingredients_pollo) == 0:
            print("✅ Pollo (comida) correctamente NO detectado como ingredients")
        else:
            print("❌ ERROR: Pollo detectado como ingredients cuando es comida preparada")
            self.fail("Pollo (comida preparada) no debe detectarse como ingredients")
        
        print(f"\n🎉 MATRIX DE VALIDACIÓN: TODOS LOS COMPORTAMIENTOS CORRECTOS")


if __name__ == '__main__':
    unittest.main() 