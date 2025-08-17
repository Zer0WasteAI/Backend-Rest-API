#!/usr/bin/env python3
"""
Test runner for ZeroWasteAI API v1.3 features
"""

import sys
import os
import pytest
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def run_v1_3_tests():
    """Run all v1.3 tests with coverage reporting"""
    
    test_dir = Path(__file__).parent
    
    print("🚀 Running ZeroWasteAI API v1.3 Test Suite")
    print("=" * 50)
    
    # Test modules to run
    test_modules = [
        "test_domain_models.py",
        "test_repositories.py",
        "test_services.py",
        "test_use_cases.py",
        "test_cooking_session.py",
        "test_batch_management.py", 
        "test_environmental_session.py",
        "test_idempotency.py",
        "test_idempotency_endpoints.py",
        "test_all_endpoints.py",
        "test_integration_endpoints.py",
        "test_performance_concurrency.py"
    ]
    
    failed_tests = []
    passed_tests = []
    
    for test_module in test_modules:
        test_path = test_dir / test_module
        
        print(f"\n📋 Running {test_module}...")
        print("-" * 30)
        
        try:
            # Run pytest for this specific module
            result = pytest.main([
                str(test_path),
                "-v",
                "--tb=short",
                "--disable-warnings"
            ])
            
            if result == 0:
                passed_tests.append(test_module)
                print(f"✅ {test_module} - PASSED")
            else:
                failed_tests.append(test_module)
                print(f"❌ {test_module} - FAILED")
                
        except Exception as e:
            failed_tests.append(test_module)
            print(f"🚨 {test_module} - ERROR: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    print(f"✅ Passed: {len(passed_tests)} tests")
    for test in passed_tests:
        print(f"   - {test}")
    
    if failed_tests:
        print(f"\n❌ Failed: {len(failed_tests)} tests")
        for test in failed_tests:
            print(f"   - {test}")
    
    print(f"\n📈 Total: {len(test_modules)} test modules")
    success_rate = (len(passed_tests) / len(test_modules)) * 100
    print(f"📊 Success Rate: {success_rate:.1f}%")
    
    if failed_tests:
        print("\n🔧 To fix failing tests:")
        print("   1. Check test dependencies are installed")
        print("   2. Ensure database is properly configured")
        print("   3. Verify all domain models are imported correctly")
        print("   4. Run individual tests for detailed error messages")
        return False
    else:
        print("\n🎉 All v1.3 tests passed successfully!")
        return True


def run_with_coverage():
    """Run tests with coverage reporting"""
    
    print("📊 Running tests with coverage...")
    
    test_dir = Path(__file__).parent
    project_root = test_dir.parent
    
    # Run pytest with coverage
    cmd = [
        "python", "-m", "pytest",
        str(test_dir),
        "--cov=src",
        "--cov-report=html:htmlcov/v1_3",
        "--cov-report=term-missing",
        "--cov-config=.coveragerc",
        "-v"
    ]
    
    try:
        subprocess.run(cmd, cwd=project_root, check=True)
        print("\n📈 Coverage report generated in htmlcov/v1_3/")
    except subprocess.CalledProcessError as e:
        print(f"❌ Coverage run failed: {e}")
        return False
    
    return True


def check_dependencies():
    """Check if required dependencies are available"""
    
    required_packages = [
        "pytest",
        "flask-testing", 
        "coverage",
        "pytest-cov"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n💡 Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run ZeroWasteAI v1.3 tests")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies only")
    
    args = parser.parse_args()
    
    if args.check_deps:
        if check_dependencies():
            print("✅ All dependencies are available")
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Check dependencies first
    if not check_dependencies():
        sys.exit(1)
    
    # Run tests
    if args.coverage:
        success = run_with_coverage()
    else:
        success = run_v1_3_tests()
    
    sys.exit(0 if success else 1)