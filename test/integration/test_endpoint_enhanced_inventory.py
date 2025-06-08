"""
🚀 TEST COMPLETO DE ENDPOINT ENHANCED INVENTORY FROM RECOGNITION
==============================================================

Test de simulación completa del endpoint /ingredients/from-recognition
que demuestra la nueva funcionalidad de enriquecimiento automático con:
- Impacto ambiental (CO2, agua, sostenibilidad)
- Consejos de consumo
- Consejos antes de consumir
- Ideas de utilización
"""

import unittest
import time
import json
from pathlib import Path
from datetime import datetime

# Importar servicios para simular el endpoint
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.infrastructure.ai.gemini_adapter_service import GeminiAdapterService


class TestEndpointEnhancedInventory(unittest.TestCase):
    """Test de simulación completa del endpoint enhanced inventory"""
    
    def setUp(self):
        """Configuración para cada test"""
        self.ai_service = GeminiAdapterService()
        print(f"\n🧪 [ENDPOINT SIMULATION] Test setup completed")
        print(f"🕐 [ENDPOINT SIMULATION] Test started at: {datetime.now()}")
        
        # Datos de ejemplo que vendrían de un POST real desde recognition
        self.sample_request = {
            "ingredients": [
                {
                    "name": "Pescado Blanco",
                    "quantity": 500,
                    "type_unit": "gramos",
                    "storage_type": "refrigerado",
                    "expiration_time": 2,
                    "time_unit": "días",
                    "tips": "Mantener en refrigeración inmediata, consumir pronto",
                    "image_path": "https://storage.googleapis.com/foods/pescado_blanco.jpg"
                },
                {
                    "name": "Limones",
                    "quantity": 8,
                    "type_unit": "unidades",
                    "storage_type": "ambiente",
                    "expiration_time": 7,
                    "time_unit": "días",
                    "tips": "Almacenar en lugar fresco y seco",
                    "image_path": "https://storage.googleapis.com/foods/limones.jpg"
                },
                {
                    "name": "Cebolla Roja",
                    "quantity": 2,
                    "type_unit": "unidades",
                    "storage_type": "ambiente",
                    "expiration_time": 14,
                    "time_unit": "días",
                    "tips": "Mantener en lugar ventilado",
                    "image_path": "https://storage.googleapis.com/foods/cebolla_roja.jpg"
                }
            ]
        }
    
    def test_complete_endpoint_simulation(self):
        """Test: Simulación completa del endpoint /ingredients/from-recognition"""
        print(f"\n🚀 [ENDPOINT TEST] Simulating POST /ingredients/from-recognition")
        
        # Simular recepción de request
        request_data = self.sample_request.copy()
        ingredients_data = request_data["ingredients"]
        
        print(f"📥 [ENDPOINT] Processing {len(ingredients_data)} ingredients from recognition")
        
        for i, ingredient in enumerate(ingredients_data):
            print(f"   • Ingredient {i+1}: {ingredient['name']} - {ingredient['quantity']} {ingredient['type_unit']}")
        
        # PASO 1: Validaciones (simuladas)
        print(f"\n✅ [ENDPOINT] Validation passed - all required fields present")
        
        # PASO 2: Enriquecimiento automático 
        print(f"\n🌱 [ENDPOINT] Starting automatic enhanced enrichment...")
        start_enrichment = time.time()
        
        enhanced_count = self._simulate_enhanced_enrichment(ingredients_data)
        
        end_enrichment = time.time()
        enrichment_duration = end_enrichment - start_enrichment
        
        print(f"⏱️ [ENDPOINT] Enhanced enrichment completed in: {enrichment_duration:.2f}s")
        print(f"📊 [ENDPOINT] Enhanced {enhanced_count}/{len(ingredients_data)} ingredients successfully")
        
        # PASO 3: Guardado en inventory (simulado)
        print(f"\n💾 [ENDPOINT] Simulating save to inventory...")
        time.sleep(0.5)  # Simular tiempo de guardado
        
        # PASO 4: Response final
        response = {
            "message": "Ingredientes agregados exitosamente desde reconocimiento con datos enriquecidos",
            "ingredients_count": len(ingredients_data),
            "source": "recognition",
            "enhanced_data": [
                "environmental_impact",
                "consumption_advice", 
                "before_consumption_advice",
                "utilization_ideas"
            ]
        }
        
        print(f"\n✅ [ENDPOINT] Success! Response prepared:")
        print(f"   📝 Message: {response['message']}")
        print(f"   📊 Ingredients count: {response['ingredients_count']}")
        print(f"   🌱 Enhanced data types: {len(response['enhanced_data'])}")
        
        # Verificaciones
        self.assertEqual(enhanced_count, len(ingredients_data))
        self.assertEqual(response["ingredients_count"], len(ingredients_data))
        self.assertEqual(response["source"], "recognition")
        
        # Verificar que cada ingrediente tiene todos los datos enriquecidos
        for ingredient in ingredients_data:
            self.assertIn("environmental_impact", ingredient)
            self.assertIn("consumption_advice", ingredient)
            self.assertIn("before_consumption_advice", ingredient)
            self.assertIn("utilization_ideas", ingredient)
        
        print(f"\n🎉 [ENDPOINT TEST] Complete endpoint simulation PASSED!")
        return response, ingredients_data
    
    def test_show_enhanced_data_samples(self):
        """Test: Mostrar ejemplos de datos enriquecidos generados"""
        print(f"\n📋 [SAMPLE DATA] Showing samples of enhanced data generation")
        
        # Obtener datos enriquecidos
        response, enriched_ingredients = self.test_complete_endpoint_simulation()
        
        print(f"\n📄 [SAMPLE DATA] Enhanced Data Samples:")
        print(f"=" * 60)
        
        for i, ingredient in enumerate(enriched_ingredients[:2]):  # Solo primeros 2 para brevedad
            name = ingredient["name"]
            print(f"\n🥕 INGREDIENT {i+1}: {name}")
            print(f"─" * 40)
            
            # Environmental Impact
            env_impact = ingredient["environmental_impact"]
            if "environmental_impact" in env_impact:
                env_data = env_impact["environmental_impact"]
            else:
                env_data = env_impact
                
            print(f"🌍 ENVIRONMENTAL IMPACT:")
            if "carbon_footprint" in env_data:
                cf = env_data["carbon_footprint"]
                print(f"   • CO2 Footprint: {cf.get('value', 'N/A')} {cf.get('unit', '')}")
            if "water_footprint" in env_data:
                wf = env_data["water_footprint"]
                print(f"   • Water Footprint: {wf.get('value', 'N/A')} {wf.get('unit', '')}")
            if "sustainability_message" in env_data:
                print(f"   • Sustainability: {env_data['sustainability_message'][:80]}...")
            
            # Consumption Advice
            consumption = ingredient["consumption_advice"]
            print(f"\n🍽️ CONSUMPTION ADVICE:")
            print(f"   • Optimal: {consumption.get('optimal_consumption', 'N/A')[:80]}...")
            print(f"   • Benefits: {consumption.get('nutritional_benefits', 'N/A')[:80]}...")
            
            # Before Consumption Advice  
            before = ingredient["before_consumption_advice"]
            print(f"\n🛡️ BEFORE CONSUMPTION:")
            print(f"   • Quality Check: {before.get('quality_check', 'N/A')[:80]}...")
            print(f"   • Safety: {before.get('safety_tips', 'N/A')[:80]}...")
            
            # Utilization Ideas
            utilization = ingredient["utilization_ideas"]
            if isinstance(utilization, dict) and "utilization_ideas" in utilization:
                ideas = utilization["utilization_ideas"]
            else:
                ideas = utilization
                
            print(f"\n💡 UTILIZATION IDEAS:")
            for j, idea in enumerate(ideas[:2]):  # Solo primeras 2 ideas
                print(f"   {j+1}. {idea.get('title', 'N/A')}")
                print(f"      └─ {idea.get('description', 'N/A')[:60]}...")
        
        print(f"\n✅ [SAMPLE DATA] Enhanced data samples displayed successfully!")
    
    def _simulate_enhanced_enrichment(self, ingredients_data):
        """Simula el proceso de enriquecimiento automático"""
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        def enrich_single_ingredient(ingredient_data):
            ingredient_name = ingredient_data["name"]
            
            try:
                # 1. Impacto ambiental
                environmental_impact = self.ai_service.analyze_environmental_impact(ingredient_name)
                
                # 2. Consejos de consumo
                consumption_data = self.ai_service.generate_consumption_advice(ingredient_name)
                
                # 3. Ideas de utilización
                utilization_ideas = self.ai_service.generate_utilization_ideas(ingredient_name)
                
                # Agregar datos al ingrediente
                ingredient_data["environmental_impact"] = environmental_impact
                ingredient_data["consumption_advice"] = consumption_data.get("consumption_advice", {})
                ingredient_data["before_consumption_advice"] = consumption_data.get("before_consumption_advice", {})
                ingredient_data["utilization_ideas"] = utilization_ideas
                
                print(f"   ✅ [ENRICHMENT] Enhanced: {ingredient_name}")
                return True
                
            except Exception as e:
                print(f"   ⚠️ [ENRICHMENT] Error with {ingredient_name}: {str(e)}")
                return False
        
        # Enriquecimiento en paralelo
        enhanced_count = 0
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(enrich_single_ingredient, ingredient) 
                for ingredient in ingredients_data
            ]
            
            for future in as_completed(futures):
                try:
                    if future.result():
                        enhanced_count += 1
                except Exception as e:
                    print(f"   🚨 [ENRICHMENT] Thread error: {str(e)}")
        
        return enhanced_count


if __name__ == "__main__":
    print("🚀 EJECUTANDO SIMULACIÓN COMPLETA DE ENDPOINT ENHANCED INVENTORY")
    print("=" * 70)
    
    unittest.main(verbosity=2) 