#!/usr/bin/env python3
"""
Production Validation Test Runner
Runs comprehensive production readiness tests for the entire ZeroWasteAI API
"""
import os
import sys
import subprocess
import time
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print("-" * 60)
    
    start_time = time.time()
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")
        
        if result.stderr:
            print(f"\nSTDERR:\n{result.stderr}")
        
        return result.returncode == 0, execution_time, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 5 minutes")
        return False, 300, "", "Timeout"
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        return False, 0, "", str(e)

def main():
    """Run all production validation tests"""
    print("""
    🌱 ZeroWasteAI API - Production Validation Suite
    ===============================================
    
    This comprehensive test suite validates that the API is ready for production deployment.
    It tests all endpoints, services, security features, and performance characteristics.
    """)
    
    start_time = datetime.now()
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Test configuration
    test_commands = [
        {
            "command": "python -m pytest test/production_validation/test_auth_endpoints_production.py -v --tb=short",
            "description": "Authentication Endpoints Production Validation",
            "critical": True
        },
        {
            "command": "python -m pytest test/production_validation/test_inventory_endpoints_production.py -v --tb=short", 
            "description": "Inventory Management Endpoints Production Validation",
            "critical": True
        },
        {
            "command": "python -m pytest test/production_validation/test_recipe_endpoints_production.py -v --tb=short",
            "description": "Recipe Management Endpoints Production Validation", 
            "critical": True
        },
        {
            "command": "python -m pytest test/production_validation/test_recognition_endpoints_production.py -v --tb=short",
            "description": "AI Recognition Endpoints Production Validation",
            "critical": True
        },
        {
            "command": "python -m pytest test/production_validation/test_environmental_savings_endpoints_production.py -v --tb=short",
            "description": "Environmental Savings Endpoints Production Validation",
            "critical": True
        },
        {
            "command": "python -m pytest test/production_validation/test_planning_endpoints_production.py -v --tb=short",
            "description": "Planning (Meal Plan) Endpoints Production Validation",
            "critical": True
        },
        {
            "command": "python -m pytest test/production_validation/test_admin_user_generation_image_endpoints_production.py -v --tb=short",
            "description": "Admin/User/Generation/Image Management Endpoints Production Validation",
            "critical": True
        },
        {
            "command": "python -m pytest test/production_validation/test_core_services_production.py -v --tb=short",
            "description": "Core Services Production Validation",
            "critical": True
        },
        {
            "command": "python -m pytest test/unit/ -v --tb=short",
            "description": "Existing Unit Tests Validation",
            "critical": False
        },
        {
            "command": "python -m pytest test/functional/ -v --tb=short",
            "description": "Existing Functional Tests Validation", 
            "critical": False
        },
        {
            "command": "python -m pytest test/integration/ -v --tb=short",
            "description": "Existing Integration Tests Validation",
            "critical": False
        }
    ]
    
    # Performance and load tests
    performance_commands = [
        {
            "command": "python -c \"import time; import requests; start=time.time(); requests.get('http://localhost:3000/status'); print(f'Response time: {time.time()-start:.2f}s')\"",
            "description": "API Response Time Check",
            "critical": False
        }
    ]
    
    results = []
    critical_failures = []
    
    print(f"🚀 Starting production validation at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Run test suites
    for test_config in test_commands:
        success, exec_time, stdout, stderr = run_command(
            test_config["command"], 
            test_config["description"]
        )
        
        # Count tests from pytest output
        if "passed" in stdout or "failed" in stdout:
            # Extract test counts from pytest output
            lines = stdout.split('\n')
            for line in lines:
                if "passed" in line and ("failed" in line or "error" in line):
                    # Line like: "5 passed, 2 failed in 10.5s"
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part == "passed" and i > 0:
                            passed_tests += int(parts[i-1])
                            total_tests += int(parts[i-1])
                        if part == "failed" and i > 0:
                            failed_tests += int(parts[i-1])
                            total_tests += int(parts[i-1])
                        if part == "error" and i > 0:
                            failed_tests += int(parts[i-1]) 
                            total_tests += int(parts[i-1])
                    break
        
        result = {
            "description": test_config["description"],
            "success": success,
            "execution_time": exec_time,
            "critical": test_config["critical"],
            "command": test_config["command"]
        }
        results.append(result)
        
        if not success and test_config["critical"]:
            critical_failures.append(result)
        
        if success:
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            if test_config["critical"]:
                print("🚨 CRITICAL FAILURE - This will block production deployment")
    
    # Run performance tests if main tests pass
    if not critical_failures:
        print(f"\n🏃 Running Performance Validation Tests")
        for perf_config in performance_commands:
            success, exec_time, stdout, stderr = run_command(
                perf_config["command"],
                perf_config["description"] 
            )
            
            result = {
                "description": perf_config["description"],
                "success": success,
                "execution_time": exec_time,
                "critical": False,
                "command": perf_config["command"]
            }
            results.append(result)
    
    # Generate final report
    end_time = datetime.now()
    total_execution_time = (end_time - start_time).total_seconds()
    
    print(f"\n\n{'='*80}")
    print(f"🏁 PRODUCTION VALIDATION SUMMARY")
    print(f"{'='*80}")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Execution Time: {total_execution_time:.2f} seconds")
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    
    # Summary by category
    print(f"\n📊 RESULTS BY CATEGORY:")
    print("-" * 40)
    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        critical_marker = "🚨 CRITICAL" if result["critical"] else ""
        print(f"{status:<10} {result['description']:<50} {critical_marker}")
        print(f"           Execution time: {result['execution_time']:.2f}s")
    
    # Critical failures
    if critical_failures:
        print(f"\n🚨 CRITICAL FAILURES (PRODUCTION BLOCKERS):")
        print("-" * 50)
        for failure in critical_failures:
            print(f"❌ {failure['description']}")
            print(f"   Command: {failure['command']}")
            print(f"   Execution time: {failure['execution_time']:.2f}s")
    
    # Production readiness assessment
    print(f"\n🎯 PRODUCTION READINESS ASSESSMENT:")
    print("=" * 50)
    
    if critical_failures:
        print("❌ NOT READY FOR PRODUCTION")
        print(f"   {len(critical_failures)} critical failure(s) must be resolved")
        print("   🚨 DO NOT DEPLOY TO PRODUCTION")
        exit_code = 1
    else:
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 95:
            print("✅ READY FOR PRODUCTION")
            print(f"   All critical tests passed ({success_rate:.1f}% success rate)")
            print("   🚀 APPROVED FOR PRODUCTION DEPLOYMENT")
            exit_code = 0
        elif success_rate >= 85:
            print("⚠️  MOSTLY READY FOR PRODUCTION") 
            print(f"   Some non-critical tests failed ({success_rate:.1f}% success rate)")
            print("   🟡 DEPLOYMENT WITH CAUTION")
            exit_code = 0
        else:
            print("❌ NOT READY FOR PRODUCTION")
            print(f"   Too many test failures ({success_rate:.1f}% success rate)")
            print("   🚨 RESOLVE FAILURES BEFORE DEPLOYMENT")
            exit_code = 1
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    print("-" * 20)
    
    if critical_failures:
        print("1. 🔧 Fix all critical failures before considering deployment")
        print("2. 🧪 Re-run production validation tests after fixes")
        print("3. 📊 Review error logs and improve error handling")
    
    if failed_tests > 0:
        print("4. 🔍 Investigate failed tests and improve test coverage")
        print("5. 📈 Monitor application performance in staging environment")
    
    if total_execution_time > 120:  # 2 minutes
        print("6. ⚡ Consider optimizing test execution time for CI/CD")
    
    print("7. 🔄 Set up continuous integration with these validation tests")
    print("8. 📈 Implement production monitoring and alerting")
    print("9. 🛡️  Review security configurations before deployment")
    print("10. 📚 Update documentation with deployment procedures")
    
    # Save detailed report
    report_file = f"production_validation_report_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
    
    with open(report_file, 'w') as f:
        f.write(f"ZeroWasteAI API - Production Validation Report\n")
        f.write(f"Generated: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*60}\n\n")
        
        f.write(f"SUMMARY:\n")
        f.write(f"Total Tests: {total_tests}\n")
        f.write(f"Passed: {passed_tests}\n") 
        f.write(f"Failed: {failed_tests}\n")
        f.write(f"Success Rate: {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%\n")
        f.write(f"Total Execution Time: {total_execution_time:.2f}s\n\n")
        
        f.write(f"DETAILED RESULTS:\n")
        f.write("-" * 40 + "\n")
        for result in results:
            f.write(f"Test: {result['description']}\n")
            f.write(f"Status: {'PASS' if result['success'] else 'FAIL'}\n")
            f.write(f"Critical: {result['critical']}\n")
            f.write(f"Execution Time: {result['execution_time']:.2f}s\n")
            f.write(f"Command: {result['command']}\n")
            f.write("-" * 40 + "\n")
    
    print(f"\n📋 Detailed report saved to: {report_file}")
    print(f"\n🌱 ZeroWasteAI API Production Validation Complete!")
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()