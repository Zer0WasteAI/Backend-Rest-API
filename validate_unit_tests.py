#!/usr/bin/env python3
"""
Unit Test Validation Script
Quick validation that our unit test infrastructure is working
"""

import sys
import subprocess
import os
from pathlib import Path

def validate_test_structure():
    """Validate test directory structure"""
    print("🔍 Validating test structure...")
    
    required_dirs = [
        "test/unit",
        "test/unit/domain/models",
        "test/unit/application/use_cases/recipes", 
        "test/unit/infrastructure/auth"
    ]
    
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            print(f"❌ Missing directory: {dir_path}")
            return False
        print(f"✅ Directory exists: {dir_path}")
    
    return True

def validate_test_files():
    """Validate test files exist"""
    print("\n🔍 Validating test files...")
    
    test_files = [
        "test/unit/domain/models/test_user_model.py",
        "test/unit/domain/models/test_recipe_model.py", 
        "test/unit/domain/models/test_inventory_model.py",
        "test/unit/application/use_cases/recipes/test_save_recipe_use_case.py",
        "test/unit/infrastructure/auth/test_jwt_service.py"
    ]
    
    for file_path in test_files:
        if not Path(file_path).exists():
            print(f"❌ Missing test file: {file_path}")
            return False
        print(f"✅ Test file exists: {file_path}")
    
    return True

def validate_dependencies():
    """Check if test dependencies are available"""
    print("\n🔍 Validating dependencies...")
    
    try:
        import pytest
        print(f"✅ pytest: {pytest.__version__}")
    except ImportError:
        print("❌ pytest not installed")
        return False
    
    try:
        import pytest_cov
        print("✅ pytest-cov: available")
    except ImportError:
        print("⚠️  pytest-cov not installed (coverage may not work)")
    
    try:
        import pytest_mock
        print("✅ pytest-mock: available")
    except ImportError:
        print("⚠️  pytest-mock not installed (mocking may not work)")
        
    return True

def run_sample_test():
    """Run a sample test to validate setup"""
    print("\n🧪 Running sample test...")
    
    # Run just one simple test
    cmd = [
        sys.executable, "-m", "pytest", 
        "test/unit/domain/models/test_user_model.py::TestUserModel::test_user_creation_with_required_fields",
        "-v", "--tb=short", "--no-cov"
    ]
    
    try:
        result = subprocess.run(cmd, cwd=os.getcwd(), capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Sample test passed!")
            return True
        else:
            print("❌ Sample test failed!")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Failed to run sample test: {e}")
        return False

def main():
    print("🚀 ZeroWasteAI API - Unit Test Validation")
    print("=" * 50)
    
    # Run validations
    validations = [
        validate_test_structure,
        validate_test_files, 
        validate_dependencies,
        run_sample_test
    ]
    
    all_passed = True
    for validation in validations:
        if not validation():
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✅ ALL VALIDATIONS PASSED!")
        print("\n📋 Next steps:")
        print("1. Install test dependencies: pip install -r requirements-test.txt")
        print("2. Run unit tests: python run_unit_tests.py")
        print("3. View coverage: python run_unit_tests.py --html")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("Please fix the issues above before running tests.")
        sys.exit(1)

if __name__ == "__main__":
    main()