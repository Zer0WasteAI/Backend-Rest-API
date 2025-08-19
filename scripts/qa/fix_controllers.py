#!/usr/bin/env python3
"""
Script para remover decoradores @api_response y mejorar manejo de errores
"""
import os
import re
import glob

def fix_controller_file(file_path):
    """Remueve @api_response decorators y mejora manejo de errores"""
    print(f"🔧 Processing: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remover líneas @api_response completas
    content = re.sub(r'@api_response\(service=ServiceType\.[^)]+\)\n', '', content)
    
    # Mejorar bloques except Exception existentes con detalles
    def enhance_exception_handler(match):
        indent = match.group(1)
        rest_of_except = match.group(2)
        
        # Si ya tiene error_details, no modificar
        if 'error_details' in rest_of_except:
            return match.group(0)
        
        enhanced = f"""{indent}except Exception as e:
{indent}    error_details = {{
{indent}        "error_type": type(e).__name__,
{indent}        "error_message": str(e),
{indent}        "traceback": str(e.__traceback__.tb_frame.f_code.co_filename) + ":" + str(e.__traceback__.tb_lineno) if e.__traceback__ else "No traceback"
{indent}    }}
{indent}    
{indent}    # Log the detailed error
{indent}    print(f"ERROR: {{error_details}}")
{indent}    
{rest_of_except}"""
        
        # Si el return usa jsonify, agregar details
        if 'jsonify(' in rest_of_except and '"error"' in rest_of_except:
            enhanced = enhanced.replace(
                'return jsonify({"error"',
                'return jsonify({"error"'
            )
            # Buscar el jsonify y agregar details
            enhanced = re.sub(
                r'return jsonify\(\{"error": ([^}]+)\}\)',
                r'return jsonify({"error": \1, "details": error_details})',
                enhanced
            )
        
        return enhanced
    
    # Patrón para encontrar except Exception blocks
    content = re.sub(
        r'(\s+)except Exception as e:(.*?)(?=\n\s*(?:def |class |@|$))',
        enhance_exception_handler,
        content,
        flags=re.DOTALL
    )
    
    # Escribir archivo modificado
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Fixed: {file_path}")

def main():
    """Procesar todos los controladores"""
    controllers_path = "/Users/rafaelprimo/Backend-Rest-API/src/interface/controllers"
    
    # Encontrar todos los archivos .py en controllers
    controller_files = glob.glob(os.path.join(controllers_path, "*.py"))
    
    # Filtrar __init__.py
    controller_files = [f for f in controller_files if not f.endswith('__init__.py')]
    
    print(f"🎯 Found {len(controller_files)} controller files")
    
    for file_path in controller_files:
        try:
            fix_controller_file(file_path)
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
    
    print("\n🎉 All controllers processed!")
    print("📋 Changes made:")
    print("   - Removed all @api_response decorators")
    print("   - Enhanced exception handling with detailed error info")
    print("   - Added error_details to JSON responses")

if __name__ == "__main__":
    main()
