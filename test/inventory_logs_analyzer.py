#!/usr/bin/env python3
"""
🔍 ANALIZADOR DE LOGS PARA DEBUGGING DE IMAGE_PATH
=================================================

Script para analizar los logs del sistema de inventario y detectar
problemas con las imágenes de ingredientes desde reconocimiento.

Uso:
    python test/inventory_logs_analyzer.py
"""

import re
import sys
from pathlib import Path

# Agregar el proyecto al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class InventoryLogsAnalyzer:
    """Analizador de logs para detectar problemas con image_path"""
    
    def __init__(self):
        self.log_patterns = {
            'image_debug': r'🔍 \[IMAGE_PATH DEBUG\]',
            'image_recovery': r'🔍 \[IMAGE RECOVERY\]',
            'ingredient_processing': r'📦 \[ADD INGREDIENTS \d+\]',
            'missing_image': r'Adding fallback image_path',
            'existing_image': r'Using existing image_path',
            'recognition_complete': r'🎉 All \d+ ingredients processed',
            'inventory_from_recognition': r'INVENTORY FROM RECOGNITION ENHANCED',
        }
    
    def analyze_image_path_flow(self, log_content: str):
        """Analiza el flujo completo de image_path desde reconocimiento hasta inventario"""
        print("🔍 ANALIZANDO FLUJO DE IMAGE_PATH")
        print("=" * 50)
        
        # 1. Buscar procesamiento de reconocimiento
        recognition_matches = re.findall(
            r'🎉 All (\d+) ingredients processed with optimized recognition flow!',
            log_content
        )
        
        if recognition_matches:
            print(f"✅ Reconocimiento completado: {recognition_matches[-1]} ingredientes procesados")
        else:
            print("❌ No se encontró confirmación de reconocimiento completado")
        
        # 2. Buscar logs de imagen en reconocimiento
        image_ready_matches = re.findall(
            r'🖼️ Image ready for (.+?)(?:\n|$)',
            log_content
        )
        
        if image_ready_matches:
            print(f"✅ Imágenes generadas durante reconocimiento: {len(image_ready_matches)}")
            for i, ingredient in enumerate(image_ready_matches[:5]):  # Primeros 5
                print(f"   • {ingredient}")
            if len(image_ready_matches) > 5:
                print(f"   ... y {len(image_ready_matches) - 5} más")
        else:
            print("❌ No se encontraron confirmaciones de imágenes generadas")
        
        # 3. Buscar logs de inventario desde reconocimiento
        inventory_matches = re.findall(
            r'📥 \[INVENTORY FROM RECOGNITION ENHANCED\] (.+?)(?:\n|$)',
            log_content
        )
        
        if inventory_matches:
            print(f"✅ Procesamiento de inventario desde reconocimiento: {len(inventory_matches)} logs")
        else:
            print("❌ No se encontró procesamiento de inventario desde reconocimiento")
        
        # 4. Buscar debug específico de image_path
        debug_matches = re.findall(
            r'🔍 \[IMAGE_PATH DEBUG\] (.+?)(?:\n|$)',
            log_content
        )
        
        if debug_matches:
            print(f"✅ Logs de debug de image_path: {len(debug_matches)}")
            for debug in debug_matches[:10]:  # Primeros 10
                print(f"   📝 {debug}")
        else:
            print("❌ No se encontraron logs de debug de image_path")
        
        # 5. Buscar recuperación de imágenes
        recovery_matches = re.findall(
            r'🔍 \[IMAGE RECOVERY\] (.+?)(?:\n|$)',
            log_content
        )
        
        if recovery_matches:
            print(f"✅ Logs de recuperación de imágenes: {len(recovery_matches)}")
            for recovery in recovery_matches[:5]:
                print(f"   🔄 {recovery}")
        else:
            print("❌ No se encontraron logs de recuperación de imágenes")
        
        # 6. Identificar ingredientes problemáticos
        fallback_matches = re.findall(
            r'Adding fallback image_path for: (.+?)(?:\n|$)',
            log_content
        )
        
        if fallback_matches:
            print(f"⚠️ Ingredientes que usaron imagen fallback: {len(fallback_matches)}")
            for ingredient in fallback_matches:
                print(f"   🔸 {ingredient}")
        
        print("\n" + "=" * 50)
    
    def analyze_request_structure(self, log_content: str):
        """Analiza la estructura de las peticiones para identificar problemas"""
        print("📝 ANALIZANDO ESTRUCTURA DE PETICIONES")
        print("=" * 50)
        
        # Buscar estructura de ingredientes en petición
        ingredient_keys_matches = re.findall(
            r'Ingredient \d+ keys: \[(.+?)\]',
            log_content
        )
        
        if ingredient_keys_matches:
            print(f"✅ Estructuras de ingredientes encontradas: {len(ingredient_keys_matches)}")
            
            # Analizar si tienen image_path
            has_image_path = []
            for keys_str in ingredient_keys_matches:
                keys = [k.strip().strip("'\"") for k in keys_str.split(',')]
                has_image_path.append('image_path' in keys)
            
            print(f"📊 Ingredientes con 'image_path' key: {sum(has_image_path)}/{len(has_image_path)}")
            
            if sum(has_image_path) == 0:
                print("❌ PROBLEMA: Ningún ingrediente tiene la key 'image_path'")
            elif sum(has_image_path) < len(has_image_path):
                print("⚠️ PROBLEMA: Algunos ingredientes no tienen la key 'image_path'")
            else:
                print("✅ Todos los ingredientes tienen la key 'image_path'")
        
        # Buscar valores específicos de image_path
        has_image_path_matches = re.findall(
            r'has image_path: (True|False)',
            log_content
        )
        
        if has_image_path_matches:
            true_count = has_image_path_matches.count('True')
            false_count = has_image_path_matches.count('False')
            
            print(f"📊 Análisis de presencia de image_path:")
            print(f"   ✅ Con image_path: {true_count}")
            print(f"   ❌ Sin image_path: {false_count}")
        
        print("\n" + "=" * 50)
    
    def generate_recommendations(self):
        """Genera recomendaciones basadas en el análisis"""
        print("💡 RECOMENDACIONES")
        print("=" * 50)
        
        print("1. 🔍 Verificar que el reconocimiento esté generando image_path:")
        print("   - Buscar logs: '🖼️ Image ready for [ingrediente]'")
        print("   - Confirmar: '✅ Basic data ready for [ingrediente]: Image ✅'")
        
        print("\n2. 📤 Verificar que el frontend envíe image_path:")
        print("   - Buscar logs: 'has image_path: True'")
        print("   - Revisar estructura de petición JSON")
        
        print("\n3. 🔄 Activar recuperación automática de imágenes:")
        print("   - Los logs de '🔍 [IMAGE RECOVERY]' deberían mostrar recuperación")
        print("   - Verificar que el servicio esté configurado correctamente")
        
        print("\n4. 🚨 Investigar puntos de falla:")
        print("   - Si hay '✅ Using existing image_path' vs '⚠️ Adding fallback'")
        print("   - Verificar logs de persistencia en base de datos")
        
        print("\n" + "=" * 50)


def main():
    """Función principal del analizador"""
    analyzer = InventoryLogsAnalyzer()
    
    print("🔍 ANALIZADOR DE LOGS DE INVENTARIO")
    print("Buscando problemas con image_path en ingredientes desde reconocimiento")
    print()
    
    # Simular análisis con datos de ejemplo
    print("📝 Para usar este analizador:")
    print("1. Ejecuta una operación de reconocimiento + agregar al inventario")
    print("2. Copia los logs del servidor")
    print("3. Pasa el contenido a analyzer.analyze_image_path_flow(log_content)")
    print()
    
    # Generar recomendaciones generales
    analyzer.generate_recommendations()
    
    # Ejemplo de uso con logs en vivo
    print("\n" + "=" * 60)
    print("📋 EJEMPLO DE USO CON LOGS EN VIVO:")
    print("=" * 60)
    
    example_usage = '''
# En tu script de prueba o terminal:
import requests

# 1. Ejecutar reconocimiento
response = requests.post("/api/recognition/ingredients", ...)

# 2. Agregar al inventario  
response = requests.post("/api/inventory/ingredients/from-recognition", ...)

# 3. Capturar logs del servidor y analizar
analyzer = InventoryLogsAnalyzer()
with open("server_logs.txt") as f:
    log_content = f.read()
    
analyzer.analyze_image_path_flow(log_content)
analyzer.analyze_request_structure(log_content)
'''
    
    print(example_usage)


if __name__ == "__main__":
    main() 