#!/usr/bin/env python3
"""
Script para arreglar los tests de Recipe añadiendo image_path=None
"""
import re

def fix_recipe_constructor(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar patrones de Recipe( que no tengan image_path
    pattern = r'recipe = Recipe\((.*?)\)'
    matches = list(re.finditer(pattern, content, re.DOTALL))
    
    fixed_content = content
    offset = 0
    
    for match in matches:
        constructor_args = match.group(1)
        
        # Si ya tiene image_path, no lo tocamos
        if 'image_path=' in constructor_args:
            continue
            
        # Si termina con description=description, agregamos image_path
        if 'description=description' in constructor_args and not 'image_path=' in constructor_args:
            new_constructor_args = constructor_args.replace(
                'description=description', 
                'description=description,\n            image_path=None'
            )
            
            new_match_text = f'recipe = Recipe({new_constructor_args})'
            
            start_pos = match.start() + offset
            end_pos = match.end() + offset
            
            fixed_content = fixed_content[:start_pos] + new_match_text + fixed_content[end_pos:]
            
            # Ajustar offset para los siguientes reemplazos
            offset += len(new_match_text) - len(match.group(0))
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    
    print(f"✅ Fixed Recipe constructors in {file_path}")

if __name__ == "__main__":
    fix_recipe_constructor("/Users/rafaelprimo/Backend-Rest-API/test/unit/domain/models/test_recipe_model.py")
