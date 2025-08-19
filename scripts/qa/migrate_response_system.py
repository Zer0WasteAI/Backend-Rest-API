#!/usr/bin/env python3
"""
Script para migrar todos los controllers al nuevo sistema de mensajes bonitos.
Actualiza automáticamente todos los endpoints para usar @api_response decorator.
"""

import re
import os
from pathlib import Path

# Mapeo de controladores a sus tipos de servicio
CONTROLLER_SERVICE_MAPPING = {
    'auth_controller.py': 'ServiceType.AUTH',
    'recipe_controller.py': 'ServiceType.RECIPES', 
    'inventory_controller.py': 'ServiceType.INVENTORY',
    'cooking_session_controller.py': 'ServiceType.COOKING',
    'recognition_controller.py': 'ServiceType.RECOGNITION',
    'image_management_controller.py': 'ServiceType.IMAGES',
    'planning_controller.py': 'ServiceType.PLANNING',
    'environmental_savings_controller.py': 'ServiceType.ENVIRONMENTAL',
    'user_controller.py': 'ServiceType.USER',
    'admin_controller.py': 'ServiceType.ADMIN',
    'generation_controller.py': 'ServiceType.IMAGES'
}

# Mapeo de rutas a acciones
ROUTE_ACTION_MAPPING = {
    # Auth actions
    'login': 'login',
    'logout': 'logout',
    'refresh': 'token_refresh',
    'signin': 'login',
    
    # Recipe actions
    'generate': 'generated',
    'save': 'saved',
    'delete': 'deleted',
    'favorite': 'favorite_added',
    'unfavorite': 'favorite_removed',
    'all': 'list_retrieved',
    
    # Inventory actions
    'add': 'item_added',
    'update': 'item_updated',
    'delete': 'item_deleted',
    'upload': 'uploaded',
    'expiring': 'expiring_retrieved',
    
    # Cooking actions
    'start': 'session_started',
    'complete': 'step_completed',
    'finish': 'session_finished',
    'mise_en_place': 'mise_en_place',
    
    # Recognition actions
    'recognize': 'image_processed',
    'ingredients': 'ingredients_recognized',
    'foods': 'foods_identified',
    'batch': 'batch_processed',
    
    # Image actions
    'upload': 'uploaded',
    'assign': 'assigned',
    'search': 'similar_found',
    'sync': 'synced',
    
    # Planning actions
    'save': 'plan_saved',
    'update': 'plan_updated',
    'delete': 'plan_deleted',
    'get': 'plans_retrieved',
    
    # Environmental actions
    'calculate': 'savings_calculated',
    'summary': 'summary_generated',
    
    # User actions  
    'profile': 'profile_updated',
    'preferences': 'preferences_saved',
    
    # Admin actions
    'cleanup': 'tokens_cleaned',
    'stats': 'stats_retrieved'
}

def get_action_from_route(route_path, method='POST'):
    """Extrae la acción más apropiada de una ruta"""
    
    # Limpiar la ruta
    route_path = route_path.lower().strip('/"')
    
    # Acciones basadas en el método HTTP
    if method == 'GET':
        if 'all' in route_path or 'list' in route_path:
            return 'list_retrieved'
        elif 'expiring' in route_path:
            return 'expiring_retrieved'
        elif 'profile' in route_path:
            return 'profile_retrieved'
        elif 'stats' in route_path:
            return 'stats_retrieved'
        else:
            return 'retrieved'
    elif method == 'POST':
        for keyword, action in ROUTE_ACTION_MAPPING.items():
            if keyword in route_path:
                return action
        return 'created'
    elif method == 'PUT':
        return 'updated'
    elif method == 'DELETE':
        return 'deleted'
    
    return 'processed'

def add_imports_to_controller(file_path):
    """Agrega los imports necesarios al controller"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Verificar si ya tiene los imports
    if 'from src.shared.decorators.response_handler import' in content:
        return content
    
    # Buscar donde insertar los imports
    import_pattern = r'(from src\.shared\.exceptions\.custom import.*\n)'
    if re.search(import_pattern, content):
        # Insertar después de otros imports de shared
        new_imports = (
            r'\1from src.shared.decorators.response_handler import api_response, ResponseHelper\n'
            r'from src.shared.messages.response_messages import ServiceType\n'
        )
        content = re.sub(import_pattern, new_imports, content)
    else:
        # Buscar el último import y agregar después
        last_import_pattern = r'(^from src\..*\n)(?!from src\.)'
        if re.search(last_import_pattern, content, re.MULTILINE):
            insertion_point = content.rfind('from src.')
            end_of_line = content.find('\n', insertion_point) + 1
            new_imports = (
                'from src.shared.decorators.response_handler import api_response, ResponseHelper\n'
                'from src.shared.messages.response_messages import ServiceType\n'
            )
            content = content[:end_of_line] + new_imports + content[end_of_line:]
    
    return content

def add_decorator_to_endpoint(content, service_type):
    """Agrega el decorator @api_response a los endpoints que no lo tienen"""
    
    # Pattern para encontrar definiciones de rutas
    route_pattern = r'(@\w+_bp\.route\([^)]+\)[\s\S]*?)(@\w+|\ndef\s+\w+)'
    
    def replace_route(match):
        route_definition = match.group(1)
        next_decorator_or_function = match.group(2)
        
        # Verificar si ya tiene @api_response
        if '@api_response' in route_definition:
            return match.group(0)
        
        # Extraer información de la ruta
        route_match = re.search(r'route\(["\']([^"\']+)["\'].*methods\s*=\s*\[["\']([^"\']+)["\']', route_definition)
        if not route_match:
            return match.group(0)
        
        route_path = route_match.group(1)
        method = route_match.group(2).upper()
        
        # Determinar la acción
        action = get_action_from_route(route_path, method)
        
        # Agregar el decorator antes del último decorator/función
        api_decorator = f'@api_response(service={service_type}, action="{action}")\n'
        
        return route_definition + api_decorator + next_decorator_or_function
    
    return re.sub(route_pattern, replace_route, content, flags=re.MULTILINE)

def migrate_controller(file_path):
    """Migra un controller individual al nuevo sistema"""
    
    filename = os.path.basename(file_path)
    service_type = CONTROLLER_SERVICE_MAPPING.get(filename)
    
    if not service_type:
        print(f"⚠️  Skipping {filename} - no service type mapping found")
        return False
    
    print(f"🔄 Migrating {filename} with {service_type}...")
    
    try:
        # Agregar imports
        content = add_imports_to_controller(file_path)
        
        # Agregar decorators a endpoints
        content = add_decorator_to_endpoint(content, service_type)
        
        # Escribir el archivo actualizado
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully migrated {filename}")
        return True
        
    except Exception as e:
        print(f"❌ Error migrating {filename}: {str(e)}")
        return False

def main():
    """Función principal para migrar todos los controllers"""
    
    controllers_dir = Path("/Users/rafaelprimo/Backend-Rest-API/src/interface/controllers")
    
    if not controllers_dir.exists():
        print("❌ Controllers directory not found!")
        return
    
    print("🚀 Starting migration of response system to all controllers...")
    print("=" * 60)
    
    success_count = 0
    total_count = 0
    
    for controller_file in controllers_dir.glob("*.py"):
        if controller_file.name == "__init__.py":
            continue
            
        total_count += 1
        
        if migrate_controller(controller_file):
            success_count += 1
    
    print("=" * 60)
    print(f"🎉 Migration completed!")
    print(f"✅ Successfully migrated: {success_count}/{total_count} controllers")
    
    if success_count == total_count:
        print("🌟 All controllers now have beautiful response messages!")
    else:
        print(f"⚠️  {total_count - success_count} controllers need manual review")

if __name__ == "__main__":
    main()