#!/usr/bin/env python3
"""
Script para limpiar imports innecesarios después de remover @api_response
"""
import os
import re
import glob

def clean_imports(file_path):
    """Remover imports innecesarios de api_response y ServiceType"""
    print(f"🧹 Cleaning imports: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remover imports de api_response y ResponseHelper si no se usan
    if '@api_response' not in content and 'api_response(' not in content:
        # Remover import completo si solo tiene api_response
        content = re.sub(r'from src\.shared\.decorators\.response_handler import api_response, ResponseHelper\n', '', content)
        content = re.sub(r'from src\.shared\.decorators\.response_handler import ResponseHelper, api_response\n', '', content)
        
        # O remover solo api_response del import
        content = re.sub(r'from src\.shared\.decorators\.response_handler import api_response, ', 'from src.shared.decorators.response_handler import ', content)
        content = re.sub(r'from src\.shared\.decorators\.response_handler import ([^,]+), api_response\n', r'from src.shared.decorators.response_handler import \1\n', content)
    
    # Remover ServiceType si no se usa
    if 'ServiceType.' not in content:
        content = re.sub(r'from src\.shared\.messages\.response_messages import ServiceType\n', '', content)
        # Si hay otros imports en esa línea
        content = re.sub(r'from src\.shared\.messages\.response_messages import ([^,]+), ServiceType\n', r'from src.shared.messages.response_messages import \1\n', content)
        content = re.sub(r'from src\.shared\.messages\.response_messages import ServiceType, ([^\n]+)\n', r'from src.shared.messages.response_messages import \1\n', content)
    
    # Solo escribir si hay cambios
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Cleaned: {file_path}")
    else:
        print(f"📝 No changes: {file_path}")

def main():
    """Limpiar imports en todos los controladores"""
    controllers_path = "/Users/rafaelprimo/Backend-Rest-API/src/interface/controllers"
    
    controller_files = glob.glob(os.path.join(controllers_path, "*.py"))
    controller_files = [f for f in controller_files if not f.endswith('__init__.py')]
    
    print(f"🧹 Cleaning imports in {len(controller_files)} controller files")
    
    for file_path in controller_files:
        try:
            clean_imports(file_path)
        except Exception as e:
            print(f"❌ Error cleaning {file_path}: {e}")
    
    print("\n🎉 Import cleanup completed!")

if __name__ == "__main__":
    main()
