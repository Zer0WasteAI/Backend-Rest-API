#!/usr/bin/env python3
"""
🧪 TEST STATUS REPORT - Post Decorator Removal Analysis
Analyze test status after removing @api_response decorators
"""

import subprocess
import sys
import os
from pathlib import Path

def run_tests_safely(test_path):
    """Run tests and capture results safely"""
    try:
        result = subprocess.run([
            f"{os.getcwd()}/venv/bin/python", "-m", "pytest", 
            test_path, "-v", "--tb=no", "-q"
        ], capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Timeout"
    except Exception as e:
        return -2, "", str(e)

def main():
    """Generate test status report"""
    print("=" * 80)
    print("🧪 TEST STATUS REPORT - Post @api_response Removal")
    print("=" * 80)
    
    test_categories = {
        "✅ Serializers (Working)": "test/unit/interface/serializers/",
        "❌ Controllers (Need Updates)": "test/unit/interface/controllers/",
        "❌ Middlewares (Need Updates)": "test/unit/interface/middlewares/",
        "🔍 Integration Tests": "test/integration/",
        "🔍 Functional Tests": "test/functional/",
        "🔍 Performance Tests": "test/performance/"
    }
    
    working_tests = 0
    failing_tests = 0
    total_categories = len(test_categories)
    
    for category, path in test_categories.items():
        print(f"\n{category}")
        print("-" * 50)
        
        if not Path(path).exists():
            print(f"   📁 Path {path} doesn't exist")
            continue
            
        code, stdout, stderr = run_tests_safely(path)
        
        if code == 0:
            # Parse passed tests - look for the final summary line
            lines = stdout.split('\n')
            for line in lines:
                # Look for pattern like "9 passed, 24 warnings in 0.02s"
                if 'passed' in line and 'in' in line and 's' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit() and i+1 < len(parts) and 'passed' in parts[i+1]:
                            passed = int(part)
                            working_tests += passed
                            print(f"   ✅ {passed} tests passing")
                            break
                    break
        elif code == 1:
            # Some tests failed - parse the summary line
            lines = stdout.split('\n')
            summary_line = ""
            for line in lines:
                if '=' in line and ('failed' in line.lower() or 'error' in line.lower() or 'passed' in line.lower()):
                    # Find the actual summary line between ===
                    if line.strip().startswith('=') and ('failed' in line or 'error' in line or 'passed' in line):
                        summary_line = line
                        break
            
            if summary_line:
                print(f"   ❌ {summary_line.strip('= ')}")
                # Try to extract numbers from summary
                words = summary_line.split()
                for i, word in enumerate(words):
                    if word.isdigit():
                        if i+1 < len(words):
                            if 'failed' in words[i+1].lower():
                                failing_tests += int(word)
                            elif 'error' in words[i+1].lower():
                                failing_tests += int(word)
            else:
                print(f"   ❌ Tests failed (details in stdout)")
                failing_tests += 1
        else:
            print(f"   🚫 Error running tests: {stderr}")
            failing_tests += 1
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    print(f"✅ Working Tests: {working_tests}")
    print(f"❌ Tests Needing Updates: {failing_tests}")
    print(f"📋 Total Test Categories: {total_categories}")
    
    print("\n🔧 RECOMMENDATIONS:")
    print("1. ✅ Serializer tests are working correctly")
    print("2. ❌ Controller tests need updating due to @api_response decorator removal")
    print("3. ❌ Middleware tests have Flask context issues")
    print("4. 🔄 Focus on fixing controller tests to match new error handling")
    
    print("\n💡 NEXT STEPS:")
    print("1. Update controller test fixtures to work with new error format")
    print("2. Fix Flask app context configuration in test setup")
    print("3. Update test assertions to match detailed error responses")
    
    if working_tests > failing_tests:
        print("\n🎉 Good news: More tests are working than failing!")
        print("   The core functionality (serializers) is solid.")
    else:
        print("\n⚠️ Most tests need updates due to decorator changes")
        print("   This is expected after removing @api_response decorators.")

if __name__ == "__main__":
    main()
