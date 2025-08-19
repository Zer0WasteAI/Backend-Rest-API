#!/usr/bin/env python3
"""
🔧 TEST FIXER - Arreglar tests después de remover @api_response decorators
Actualiza la configuración de tests para trabajar con el nuevo formato de errores
"""

import os
import re
from pathlib import Path

def fix_controller_test_setup():
    """Arregla la configuración base de los tests de controladores"""
    
    # Patrón para encontrar la fixture app básica
    old_app_fixture = '''@pytest.fixture
    def app(self):
        """Create Flask app for testing"""
        app = Flask(__name__)
        app.config['JWT_SECRET_KEY'] = 'test-secret'
        app.config['TESTING'] = True
        app.register_blueprint(inventory_bp, url_prefix='/api/inventory')
        
        # Initialize JWT
        jwt = JWTManager(app)
        
        return app'''
    
    # Nueva fixture que usa la app completa del proyecto
    new_app_fixture = '''@pytest.fixture
    def app(self):
        """Create Flask app for testing using project configuration"""
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        
        # Set testing environment before importing
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TESTING'] = '1'
        
        from src.main import create_app
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False
        })
        return app'''
    
    return old_app_fixture, new_app_fixture

def fix_test_imports():
    """Arregla los imports necesarios para los tests"""
    old_imports = '''from src.interface.controllers.inventory_controller import inventory_bp'''
    
    new_imports = '''# Removed: from src.interface.controllers.inventory_controller import inventory_bp
# Now using complete app configuration'''
    
    return old_imports, new_imports

def update_controller_test_file(filepath):
    """Actualiza un archivo de test de controlador específico"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix imports
        old_import, new_import = fix_test_imports()
        if old_import in content:
            content = content.replace(old_import, new_import)
            print(f"   ✅ Updated imports in {filepath}")
        
        # Fix app fixture
        old_fixture, new_fixture = fix_controller_test_setup()
        if '@pytest.fixture\n    def app(self):' in content:
            # Replace the entire fixture definition
            pattern = r'@pytest\.fixture\s+def app\(self\):.*?return app'
            replacement = new_fixture
            content = re.sub(pattern, replacement, content, flags=re.DOTALL)
            print(f"   ✅ Updated app fixture in {filepath}")
        
        # Only write if content changed
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   💾 Saved changes to {filepath}")
        else:
            print(f"   ⏭️  No changes needed in {filepath}")
            
    except Exception as e:
        print(f"   ❌ Error updating {filepath}: {e}")

def fix_middleware_tests():
    """Arregla los tests de middleware que tienen problemas de contexto Flask"""
    middleware_test_file = "test/unit/interface/middlewares/test_decorators.py"
    
    if not os.path.exists(middleware_test_file):
        print(f"   📁 {middleware_test_file} not found")
        return
    
    try:
        with open(middleware_test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the Flask app configuration in middleware tests
        old_pattern = r'app = Flask\(__name__\)\s+app\.config\[\'INTERNAL_SECRET_KEY\'\] = \'secret\''
        new_pattern = '''app = Flask(__name__)
    app.config['INTERNAL_SECRET_KEY'] = 'secret'
    app.config['TESTING'] = True
    
    # Push application context for tests
    ctx = app.app_context()
    ctx.push()'''
        
        content = re.sub(old_pattern, new_pattern, content)
        
        with open(middleware_test_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"   ✅ Fixed middleware tests")
        
    except Exception as e:
        print(f"   ❌ Error fixing middleware tests: {e}")

def main():
    """Main function to fix all failing tests"""
    print("=" * 80)
    print("🔧 TEST FIXER - Arreglando tests después de @api_response removal")
    print("=" * 80)
    
    # Fix controller tests
    print("\n🎯 Fixing Controller Tests...")
    print("-" * 50)
    
    controller_tests_dir = Path("test/unit/interface/controllers/")
    if controller_tests_dir.exists():
        test_files = list(controller_tests_dir.glob("test_*.py"))
        for test_file in test_files:
            print(f"Procesando: {test_file.name}")
            update_controller_test_file(str(test_file))
    else:
        print("   📁 Controller tests directory not found")
    
    # Fix middleware tests
    print("\n🛡️  Fixing Middleware Tests...")
    print("-" * 50)
    fix_middleware_tests()
    
    print("\n" + "=" * 80)
    print("✅ TEST FIXING COMPLETED")
    print("=" * 80)
    
    print("\n🎯 CHANGES MADE:")
    print("1. ✅ Updated Flask app fixtures to use complete project configuration")
    print("2. ✅ Fixed imports to remove @api_response dependencies")  
    print("3. ✅ Added proper Flask context management")
    print("4. ✅ Set testing environment variables")
    
    print("\n💡 NEXT STEP:")
    print("Run the tests again to see the improvements!")
    print("Command: python test_status_report.py")

if __name__ == "__main__":
    main()
