"""
🌱 TEST DE INVENTORY ENRIQUECIDO DESDE RECOGNITION
==============================================

Test para probar la nueva funcionalidad que genera automáticamente:
- Impacto ambiental (CO2, agua, sostenibilidad)
- Consejos de consumo
- Consejos antes de consumir
- Ideas de utilización

Cuando se agregaran ingredientes desde recognition al inventory.
"""

import unittest
import time
import json
from pathlib import Path
from datetime import datetime

# Importar servicios
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService


class TestEnhancedInventoryFromRecognition(unittest.TestCase):
    """Test de funcionalidad enriquecida de inventory desde recognition"""
    
    def setUp(self):
        """Configuración para cada test"""
        self.ai_service = GeminiAdapterService()
        print(f"\n🧪 [ENHANCED INVENTORY TEST] Test setup completed")
        print(f"🕐 [ENHANCED INVENTORY TEST] Test started at: {datetime.now()}")
        
        # Datos de ejemplo como vendrían del recognition
        self.sample_recognition_data = {
            "ingredients": [
                {
                    "name": "Tomate",
                    "quantity": 3,
                    "type_unit": "unidades",
                    "storage_type": "refrigerado",
                    "expiration_time": 5,
                    "time_unit": "días",
                    "tips": "Mantener en refrigeración para mayor duración",
                    "image_path": "https://example.com/tomate.jpg"
                },
                {
                    "name": "Cebolla Roja",
                    "quantity": 2,
                    "type_unit": "unidades", 
                    "storage_type": "ambiente",
                    "expiration_time": 14,
                    "time_unit": "días",
                    "tips": "Almacenar en lugar seco y ventilado",
                    "image_path": "https://example.com/cebolla.jpg"
                }
            ]
        }
    
    def test_generate_consumption_advice_single_ingredient(self):
        """Test: Generar consejos de consumo para un ingrediente específico"""
        print(f"\n🧪 [TEST 1] Testing consumption advice generation for single ingredient")
        
        ingredient_name = "Tomate"
        description = "Tomate fresco para ensaladas"
        
        start_time = time.time()
        
        # Llamar al método de generación de consejos
        result = self.ai_service.generate_consumption_advice(ingredient_name, description)
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ [TEST 1] Duration: {duration:.2f}s")
        print(f"📋 [TEST 1] Result structure:")
        print(f"   └─ Keys: {list(result.keys())}")
        
        # Verificaciones
        self.assertIsInstance(result, dict)
        self.assertIn("consumption_advice", result)
        self.assertIn("before_consumption_advice", result)
        
        # Verificar estructura de consumption_advice
        consumption = result["consumption_advice"]
        self.assertIn("optimal_consumption", consumption)
        self.assertIn("preparation_tips", consumption)
        self.assertIn("nutritional_benefits", consumption)
        self.assertIn("recommended_portions", consumption)
        
        # Verificar estructura de before_consumption_advice
        before_consumption = result["before_consumption_advice"]
        self.assertIn("quality_check", before_consumption)
        self.assertIn("safety_tips", before_consumption)
        self.assertIn("preparation_notes", before_consumption)
        self.assertIn("special_considerations", before_consumption)
        
        print(f"✅ [TEST 1] PASSED - Consumption advice generated successfully")
        print(f"📄 [TEST 1] Sample response:")
        print(f"   🍽️ Optimal consumption: {consumption.get('optimal_consumption', 'N/A')[:100]}...")
        print(f"   🛡️ Safety tips: {before_consumption.get('safety_tips', 'N/A')[:100]}...")
    
    def test_enhanced_enrichment_simulation(self):
        """Test: Simular el enriquecimiento completo de ingredients como en inventory"""
        print(f"\n🧪 [TEST 2] Testing complete enhanced enrichment simulation")
        
        # Simular datos como vendrían del recognition
        ingredients_data = self.sample_recognition_data["ingredients"].copy()
        
        start_time = time.time()
        
        print(f"🌱 [TEST 2] Starting enhanced enrichment for {len(ingredients_data)} ingredients")
        
        # Simular el proceso de enriquecimiento
        enriched_count = 0
        
        for i, ingredient in enumerate(ingredients_data):
            ingredient_name = ingredient["name"]
            print(f"   🌱 [TEST 2] Processing ingredient {i+1}: {ingredient_name}")
            
            try:
                # 1. Impacto ambiental
                environmental_impact = self.ai_service.analyze_environmental_impact(ingredient_name)
                
                # 2. Consejos de consumo
                consumption_data = self.ai_service.generate_consumption_advice(ingredient_name)
                
                # 3. Ideas de utilización
                utilization_ideas = self.ai_service.generate_utilization_ideas(ingredient_name)
                
                # Agregar datos enriquecidos al ingrediente
                ingredient["environmental_impact"] = environmental_impact
                ingredient["consumption_advice"] = consumption_data.get("consumption_advice", {})
                ingredient["before_consumption_advice"] = consumption_data.get("before_consumption_advice", {})
                ingredient["utilization_ideas"] = utilization_ideas
                
                enriched_count += 1
                print(f"   ✅ [TEST 2] Successfully enriched: {ingredient_name}")
                
            except Exception as e:
                print(f"   ⚠️ [TEST 2] Error enriching {ingredient_name}: {str(e)}")
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"⏱️ [TEST 2] Total duration: {duration:.2f}s")
        print(f"📊 [TEST 2] Enriched {enriched_count}/{len(ingredients_data)} ingredients successfully")
        
        # Verificaciones
        self.assertEqual(enriched_count, len(ingredients_data), "All ingredients should be enriched")
        
        for ingredient in ingredients_data:
            # Verificar que cada ingrediente tiene todos los datos enriquecidos
            self.assertIn("environmental_impact", ingredient)
            self.assertIn("consumption_advice", ingredient)
            self.assertIn("before_consumption_advice", ingredient)
            self.assertIn("utilization_ideas", ingredient)
            
            # Verificar estructuras específicas
            env_impact = ingredient["environmental_impact"]
            # El método analyze_environmental_impact retorna un objeto anidado
            if "environmental_impact" in env_impact:
                actual_env_data = env_impact["environmental_impact"]
                self.assertIn("carbon_footprint", actual_env_data)
                self.assertIn("sustainability_message", actual_env_data)
            else:
                self.assertIn("carbon_footprint", env_impact)
                self.assertIn("sustainability_message", env_impact)
            
            consumption = ingredient["consumption_advice"]
            self.assertIn("optimal_consumption", consumption)
            
            before_consumption = ingredient["before_consumption_advice"] 
            self.assertIn("quality_check", before_consumption)
            
            utilization = ingredient["utilization_ideas"]
            # El método generate_utilization_ideas puede retornar un objeto anidado
            if isinstance(utilization, dict) and "utilization_ideas" in utilization:
                actual_utilization = utilization["utilization_ideas"]
                self.assertIsInstance(actual_utilization, list)
                self.assertGreater(len(actual_utilization), 0)
            else:
                self.assertIsInstance(utilization, list)
                self.assertGreater(len(utilization), 0)
        
        print(f"✅ [TEST 2] PASSED - All ingredients enriched with enhanced data")
        print(f"📋 [TEST 2] Enhanced data verification:")
        
        for i, ingredient in enumerate(ingredients_data):
            name = ingredient["name"]
            print(f"   🥕 Ingredient {i+1}: {name}")
            print(f"      └─ Environmental Impact: ✅")
            print(f"      └─ Consumption Advice: ✅")
            print(f"      └─ Before Consumption Advice: ✅")
            print(f"      └─ Utilization Ideas: {len(ingredient['utilization_ideas'])} ideas")
    
    def test_error_handling_enrichment(self):
        """Test: Verificar manejo de errores durante el enriquecimiento"""
        print(f"\n🧪 [TEST 3] Testing error handling during enrichment")
        
        # Intentar con un "ingrediente" inválido
        invalid_ingredient = ""
        
        try:
            result = self.ai_service.generate_consumption_advice(invalid_ingredient)
            print(f"📋 [TEST 3] Error handling result: {type(result)}")
            
            # Debe devolver estructura válida incluso con error
            self.assertIsInstance(result, dict)
            self.assertIn("consumption_advice", result)
            self.assertIn("before_consumption_advice", result)
            
            print(f"✅ [TEST 3] PASSED - Error handled gracefully with fallback data")
            
        except Exception as e:
            print(f"⚠️ [TEST 3] Unexpected error: {str(e)}")
            self.fail(f"Should handle errors gracefully, but got: {str(e)}")


if __name__ == "__main__":
    print("🚀 EJECUTANDO TESTS DE INVENTORY ENRIQUECIDO DESDE RECOGNITION")
    print("=" * 70)
    
    unittest.main(verbosity=2) 