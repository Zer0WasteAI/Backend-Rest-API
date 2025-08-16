#!/usr/bin/env python3
"""
ZeroWasteAI API - Comprehensive Coverage Runner
Executes different types of coverage analysis and generates detailed reports
"""
import os
import sys
import subprocess
import time
from datetime import datetime

def run_command(command, description):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"📊 {description}")
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
            timeout=600  # 10 minutes timeout
        )
        end_time = time.time()
        execution_time = end_time - start_time
        
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Return code: {result.returncode}")
        
        if result.stdout:
            print(f"\nSTDOUT:\n{result.stdout}")
        
        if result.stderr and result.returncode != 0:
            print(f"\nSTDERR:\n{result.stderr}")
        
        return result.returncode == 0, execution_time, result.stdout, result.stderr
        
    except subprocess.TimeoutExpired:
        print("❌ Command timed out after 10 minutes")
        return False, 600, "", "Timeout"
    except Exception as e:
        print(f"❌ Error executing command: {e}")
        return False, 0, "", str(e)

def main():
    """Run comprehensive coverage analysis"""
    print("""
    📊 ZeroWasteAI API - Comprehensive Coverage Analysis
    ===================================================
    
    This script runs comprehensive test coverage analysis across all test suites.
    """)
    
    start_time = datetime.now()
    coverage_results = []
    
    # Coverage commands to run
    coverage_commands = [
        {
            "command": "python3 -m pytest test/unit/ --cov=src --cov-report=html:htmlcov/unit --cov-report=term --cov-branch",
            "description": "Unit Tests Coverage Analysis",
            "type": "unit"
        },
        {
            "command": "python3 -m pytest test/functional/ --cov=src --cov-report=html:htmlcov/functional --cov-report=term --cov-branch",
            "description": "Functional Tests Coverage Analysis", 
            "type": "functional"
        },
        {
            "command": "python3 -m pytest test/integration/ --cov=src --cov-report=html:htmlcov/integration --cov-report=term --cov-branch",
            "description": "Integration Tests Coverage Analysis",
            "type": "integration"
        },
        {
            "command": "python3 -m pytest test/production_validation/ --cov=src --cov-report=html:htmlcov/production --cov-report=term --cov-branch",
            "description": "Production Validation Coverage Analysis",
            "type": "production"
        },
        {
            "command": "python3 -m pytest test/performance/ --cov=src --cov-report=html:htmlcov/performance --cov-report=term --cov-branch",
            "description": "Performance Tests Coverage Analysis",
            "type": "performance"
        },
        {
            "command": "python3 -m pytest test/ --cov=src --cov-report=html:htmlcov/complete --cov-report=xml:coverage.xml --cov-report=json:coverage.json --cov-report=term-missing --cov-branch --cov-fail-under=80",
            "description": "Complete Test Suite Coverage Analysis",
            "type": "complete"
        }
    ]
    
    print(f"🚀 Starting coverage analysis at {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    for command_config in coverage_commands:
        success, exec_time, stdout, stderr = run_command(
            command_config["command"],
            command_config["description"]
        )
        
        # Extract coverage percentage from output
        coverage_percentage = None
        if stdout:
            lines = stdout.split('\n')
            for line in lines:
                if 'TOTAL' in line and '%' in line:
                    try:
                        # Extract percentage (usually at the end of TOTAL line)
                        parts = line.split()
                        for part in parts:
                            if '%' in part:
                                coverage_percentage = float(part.replace('%', ''))
                                break
                    except:
                        pass
        
        result = {
            "type": command_config["type"],
            "description": command_config["description"],
            "success": success,
            "execution_time": exec_time,
            "coverage_percentage": coverage_percentage
        }
        coverage_results.append(result)
        
        if success:
            if coverage_percentage:
                print(f"✅ PASSED - Coverage: {coverage_percentage}%")
            else:
                print("✅ PASSED")
        else:
            print("❌ FAILED")
    
    # Generate comprehensive coverage report
    end_time = datetime.now()
    total_execution_time = (end_time - start_time).total_seconds()
    
    print(f"\n\n{'='*80}")
    print(f"📊 COMPREHENSIVE COVERAGE ANALYSIS SUMMARY")
    print(f"{'='*80}")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Completed: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Execution Time: {total_execution_time:.2f} seconds")
    
    # Coverage results by category
    print(f"\n📈 COVERAGE RESULTS BY CATEGORY:")
    print("-" * 50)
    
    total_coverage = 0
    coverage_count = 0
    
    for result in coverage_results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        coverage_text = f"{result['coverage_percentage']:.1f}%" if result['coverage_percentage'] else "N/A"
        print(f"{status:<10} {result['description']:<40} {coverage_text:<10}")
        print(f"           Execution time: {result['execution_time']:.2f}s")
        
        if result['coverage_percentage']:
            total_coverage += result['coverage_percentage']
            coverage_count += 1
    
    # Overall coverage assessment
    if coverage_count > 0:
        average_coverage = total_coverage / coverage_count
        print(f"\n🎯 OVERALL COVERAGE ASSESSMENT:")
        print("=" * 40)
        print(f"Average Coverage: {average_coverage:.2f}%")
        
        if average_coverage >= 90:
            grade = "A+"
            status = "EXCELLENT"
        elif average_coverage >= 80:
            grade = "A"
            status = "VERY GOOD"
        elif average_coverage >= 70:
            grade = "B"
            status = "GOOD"
        elif average_coverage >= 60:
            grade = "C"
            status = "ACCEPTABLE"
        else:
            grade = "D"
            status = "NEEDS IMPROVEMENT"
        
        print(f"Coverage Grade: {grade}")
        print(f"Coverage Status: {status}")
        
        # Coverage recommendations
        print(f"\n💡 COVERAGE RECOMMENDATIONS:")
        print("-" * 30)
        
        if average_coverage >= 85:
            print("✅ Excellent coverage - ready for production deployment")
        elif average_coverage >= 75:
            print("✅ Good coverage - consider minor improvements")
        elif average_coverage >= 65:
            print("⚠️ Acceptable coverage - focus on critical paths")
        else:
            print("❌ Low coverage - significant testing needed")
        
        # Identify areas for improvement
        low_coverage = [r for r in coverage_results if r['coverage_percentage'] and r['coverage_percentage'] < 80]
        if low_coverage:
            print("\n📋 Areas needing coverage improvement:")
            for result in low_coverage:
                print(f"   • {result['type']}: {result['coverage_percentage']:.1f}%")
    
    # Generate file locations
    print(f"\n📁 GENERATED COVERAGE REPORTS:")
    print("-" * 30)
    print("📄 HTML Reports:")
    print("   • Complete Coverage: htmlcov/complete/index.html")
    print("   • Unit Tests: htmlcov/unit/index.html")
    print("   • Functional Tests: htmlcov/functional/index.html")
    print("   • Integration Tests: htmlcov/integration/index.html")
    print("   • Production Tests: htmlcov/production/index.html")
    print("   • Performance Tests: htmlcov/performance/index.html")
    print("\n📄 Machine-readable Reports:")
    print("   • XML Report: coverage.xml")
    print("   • JSON Report: coverage.json")
    
    # Final success assessment
    successful_runs = len([r for r in coverage_results if r['success']])
    total_runs = len(coverage_results)
    
    if successful_runs == total_runs and average_coverage >= 70:
        print(f"\n🎉 COVERAGE ANALYSIS COMPLETED SUCCESSFULLY!")
        print(f"   {successful_runs}/{total_runs} test suites analyzed")
        print(f"   Average coverage: {average_coverage:.2f}%")
        exit_code = 0
    else:
        print(f"\n❌ COVERAGE ANALYSIS COMPLETED WITH ISSUES")
        print(f"   {successful_runs}/{total_runs} test suites successful")
        if coverage_count > 0:
            print(f"   Average coverage: {average_coverage:.2f}%")
        exit_code = 1
    
    print(f"\n📊 ZeroWasteAI Coverage Analysis Complete!")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()