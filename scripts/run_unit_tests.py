#!/usr/bin/env python3
"""
Unit Test Runner for ZeroWasteAI API
Comprehensive test execution script with coverage reporting
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Run unit tests for ZeroWasteAI API')
    parser.add_argument('--coverage', '-c', action='store_true', 
                       help='Run with coverage reporting (default: True)')
    parser.add_argument('--no-coverage', action='store_true',
                       help='Run without coverage reporting')
    parser.add_argument('--html', action='store_true',
                       help='Generate HTML coverage report')
    parser.add_argument('--xml', action='store_true', 
                       help='Generate XML coverage report')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--parallel', '-n', type=int, default=1,
                       help='Number of parallel processes (default: 1)')
    parser.add_argument('--test-type', choices=['unit', 'integration', 'functional', 'all'],
                       default='unit', help='Type of tests to run (default: unit)')
    parser.add_argument('--module', '-m', type=str,
                       help='Run tests for specific module (e.g., models, services)')
    parser.add_argument('--file', '-f', type=str,
                       help='Run specific test file')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run performance benchmarks')
    parser.add_argument('--install-deps', action='store_true',
                       help='Install test dependencies before running')
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        print("📦 Installing test dependencies...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", "requirements-test.txt"
        ], check=True)
        print("✅ Dependencies installed successfully\n")
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Test selection
    if args.test_type == 'unit':
        cmd.append("test/unit/")
    elif args.test_type == 'integration':
        cmd.append("test/integration/")
    elif args.test_type == 'functional':
        cmd.append("test/functional/")
    elif args.test_type == 'all':
        cmd.append("test/")
    
    # Specific module or file
    if args.module:
        if args.test_type == 'unit':
            cmd[-1] = f"test/unit/**/*{args.module}*"
        else:
            cmd[-1] = f"test/**/*{args.module}*"
    
    if args.file:
        cmd[-1] = args.file
    
    # Coverage options
    if not args.no_coverage and args.test_type in ['unit', 'all']:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing"
        ])
        
        if args.html:
            cmd.append("--cov-report=html:htmlcov")
        
        if args.xml:
            cmd.append("--cov-report=xml:coverage.xml")
        
        # Coverage thresholds based on test type
        if args.test_type == 'unit':
            cmd.append("--cov-fail-under=85")
        else:
            cmd.append("--cov-fail-under=80")
    
    # Parallel execution
    if args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])
    
    # Verbose output
    if args.verbose:
        cmd.extend(["-v", "-s"])
    
    # Benchmarking
    if args.benchmark:
        cmd.append("--benchmark-only")
    
    # Additional pytest options for better output
    cmd.extend([
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ])
    
    print("🧪 Running ZeroWasteAI API Unit Tests")
    print("=" * 50)
    print(f"📍 Test Type: {args.test_type}")
    print(f"🔧 Coverage: {'Enabled' if not args.no_coverage else 'Disabled'}")
    print(f"⚡ Parallel: {args.parallel} processes")
    print(f"📁 Target: {cmd[-4] if 'test/' in str(cmd) else 'Custom'}")
    print("=" * 50)
    
    # Create necessary directories
    Path("htmlcov").mkdir(exist_ok=True)
    Path("test-reports").mkdir(exist_ok=True)
    
    # Execute tests
    try:
        print(f"🚀 Executing: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, cwd=os.getcwd())
        
        # Report results
        if result.returncode == 0:
            print("\n" + "=" * 50)
            print("✅ ALL TESTS PASSED!")
            print("=" * 50)
            
            if not args.no_coverage and args.html:
                print("📊 HTML Coverage Report: htmlcov/index.html")
            if not args.no_coverage and args.xml:
                print("📄 XML Coverage Report: coverage.xml")
                
        else:
            print("\n" + "=" * 50)
            print("❌ SOME TESTS FAILED!")
            print("=" * 50)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Tests interrupted by user")
        sys.exit(130)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()