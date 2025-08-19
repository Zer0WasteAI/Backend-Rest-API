#!/usr/bin/env python3
"""
🔧 ADVANCED TEST FIXER - Arregla el problema específico con JWT Context
"""

import os
import re
from pathlib import Path

def fix_inventory_controller_test():
    """Arregla específicamente el test del inventory controller con problemas JWT"""
    
    test_file = "test/unit/interface/controllers/test_inventory_controller.py"
    
    try:
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Fix the app fixture to properly handle JWT configuration
        old_app_fixture = '''@pytest.fixture
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
        
        new_app_fixture = '''@pytest.fixture
    def app(self):
        """Create Flask app for testing with full configuration"""
        import sys
        import os
        
        # Set testing environment first
        os.environ['FLASK_ENV'] = 'testing'
        os.environ['TESTING'] = '1'
        
        # Import after setting environment
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))
        from src.main import create_app
        
        # Create app with proper configuration
        app = create_app()
        app.config.update({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "WTF_CSRF_ENABLED": False,
            # JWT Configuration for testing
            "JWT_SECRET_KEY": "test-secret-key",
            "JWT_TOKEN_LOCATION": ["headers"],
            "JWT_HEADER_NAME": "Authorization",
            "JWT_HEADER_TYPE": "Bearer",
            "JWT_ACCESS_TOKEN_EXPIRES": False
        })
        
        # Push application context for proper initialization
        with app.app_context():
            pass  # This ensures all extensions are properly initialized
            
        return app'''
        
        if old_app_fixture in content:
            content = content.replace(old_app_fixture, new_app_fixture)
            print(f"   ✅ Fixed JWT configuration in {test_file}")
        
        # Write the changes
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"   💾 Updated {test_file}")
        
    except Exception as e:
        print(f"   ❌ Error fixing {test_file}: {e}")

def fix_global_conftest():
    """Arregla el archivo conftest.py global para que tenga mejor configuración"""
    
    conftest_file = "test/conftest.py"
    
    try:
        with open(conftest_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add better JWT configuration to the global conftest
        old_config = '''app.config.update({
        "TESTING": True,
        # Use in-memory SQLite for unit tests that may touch the DB layer
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })'''
    
        new_config = '''app.config.update({
        "TESTING": True,
        # Use in-memory SQLite for unit tests that may touch the DB layer
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        # JWT Configuration for testing
        "JWT_SECRET_KEY": "test-secret-key-global",
        "JWT_TOKEN_LOCATION": ["headers"],
        "JWT_HEADER_NAME": "Authorization", 
        "JWT_HEADER_TYPE": "Bearer",
        "JWT_ACCESS_TOKEN_EXPIRES": False,
        "WTF_CSRF_ENABLED": False
    })'''
    
        if old_config in content:
            content = content.replace(old_config, new_config)
            print(f"   ✅ Enhanced global conftest.py")
            
            with open(conftest_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"   💾 Updated {conftest_file}")
        
    except Exception as e:
        print(f"   ❌ Error fixing {conftest_file}: {e}")

def fix_middleware_tests_advanced():
    """Arregla los tests de middleware con una solución más robusta"""
    
    middleware_test_file = "test/unit/interface/middlewares/test_decorators.py"
    
    try:
        with open(middleware_test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace problematic test functions with better versions
        old_test1 = '''def test_internal_only_decorator_allows_with_secret():
    app = Flask(__name__)
    app.config['INTERNAL_SECRET_KEY'] = 'secret'
    app.config['TESTING'] = True
    
    # Push application context for tests
    ctx = app.app_context()
    ctx.push()
    from src.shared.decorators.internal_only import internal_only

    @app.route('/internal')
    @internal_only
    def internal():
        return jsonify({"ok": True}), 200

    client = app.test_client()
    resp_forbidden = client.get('/internal')
    assert resp_forbidden.status_code == 403'''
    
        new_test1 = '''def test_internal_only_decorator_allows_with_secret():
    app = Flask(__name__)
    app.config['INTERNAL_SECRET_KEY'] = 'secret'
    app.config['TESTING'] = True
    
    with app.app_context():
        from src.shared.decorators.internal_only import internal_only

        @app.route('/internal')
        @internal_only
        def internal():
            return jsonify({"ok": True}), 200

        client = app.test_client()
        resp_forbidden = client.get('/internal')
        assert resp_forbidden.status_code == 403'''
    
        if old_test1 in content:
            content = content.replace(old_test1, new_test1)
            print(f"   ✅ Fixed internal_only test")
        
        # Write changes
        with open(middleware_test_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        print(f"   💾 Updated middleware tests")
        
    except Exception as e:
        print(f"   ❌ Error fixing middleware tests: {e}")

def main():
    """Main function to apply advanced fixes"""
    print("=" * 80)
    print("🔧 ADVANCED TEST FIXER - JWT Context Issues")
    print("=" * 80)
    
    print("\n🎯 Fixing JWT Configuration Issues...")
    print("-" * 50)
    
    # Fix specific inventory controller test
    fix_inventory_controller_test()
    
    # Fix global conftest
    fix_global_conftest()
    
    # Fix middleware tests with better context management
    fix_middleware_tests_advanced()
    
    print("\n" + "=" * 80)
    print("✅ ADVANCED FIXES COMPLETED")
    print("=" * 80)
    
    print("\n🎯 FIXES APPLIED:")
    print("1. ✅ Enhanced JWT configuration in controller tests")
    print("2. ✅ Fixed Flask app context initialization") 
    print("3. ✅ Updated global conftest.py with JWT settings")
    print("4. ✅ Improved middleware test context management")
    
    print("\n💡 NEXT STEP:")
    print("Test the improvements with: python test_status_report.py")

if __name__ == "__main__":
    main()
