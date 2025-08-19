#!/usr/bin/env python3
"""
🏃‍♂️ QUICK TEST RUNNER - ZeroWasteAI API
Simple and fast test execution with immediate failure reporting
"""

import subprocess
import sys
import os
import time
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
    print(f"{Colors.CYAN}{Colors.BOLD}🏃‍♂️ QUICK TEST RUNNER - ZeroWasteAI API{Colors.END}")
    print(f"{Colors.CYAN}{'='*60}{Colors.END}\n")

def run_tests(test_type="all", verbose=False, stop_on_fail=False):
    """Run tests with immediate output"""
    
    start_time = time.time()
    
    # Build pytest command - auto-detect Python environment
    project_root = Path(__file__).parent
    venv_python = project_root / 'venv' / 'bin' / 'python'
    
    if venv_python.exists():
        python_cmd = str(venv_python)
    else:
        # Try common Python commands
        for cmd_name in ['python3', 'python']:
            try:
                subprocess.run([cmd_name, '--version'], capture_output=True, check=True)
                python_cmd = cmd_name
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            python_cmd = 'python3'  # fallback
    
    cmd = [python_cmd, '-m', 'pytest']
    
    # Add test directory based on type
    if test_type == "unit":
        cmd.append('test/unit')
        print(f"{Colors.BLUE}🎯 Running UNIT tests only{Colors.END}")
    elif test_type == "integration": 
        cmd.append('test/integration')
        print(f"{Colors.BLUE}🎯 Running INTEGRATION tests only{Colors.END}")
    elif test_type == "functional":
        cmd.append('test/functional')
        print(f"{Colors.BLUE}🎯 Running FUNCTIONAL tests only{Colors.END}")
    elif test_type == "performance":
        cmd.append('test/performance') 
        print(f"{Colors.BLUE}🎯 Running PERFORMANCE tests only{Colors.END}")
    else:
        cmd.append('test')
        print(f"{Colors.BLUE}🎯 Running ALL tests{Colors.END}")
    
    # Add options
    if verbose:
        cmd.extend(['-v', '--tb=long'])
    else:
        cmd.extend(['--tb=short'])
    
    if stop_on_fail:
        cmd.append('-x')  # Stop on first failure
    
    cmd.extend([
        '--disable-warnings',  # Less noise
        '--maxfail=10',        # Stop after 10 failures max
        '--durations=5'        # Show 5 slowest tests
    ])
    
    print(f"{Colors.YELLOW}🚀 Command: {' '.join(cmd)}{Colors.END}\n")
    
    # Run tests with real-time output
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            cwd=Path(__file__).parent
        )
        
        # Print output in real time
        failed_tests = []
        current_failure = []
        in_failure = False
        
        for line in process.stdout:
            # Print line immediately
            print(line, end='')
            
            # Track failures
            if 'FAILED' in line and '::' in line:
                failed_test = line.split('FAILED')[0].strip()
                failed_tests.append(failed_test)
            
            # Track failure details
            if line.startswith('=') and 'FAILURES' in line:
                in_failure = True
                current_failure = []
            elif line.startswith('=') and ('short test summary' in line.lower() or 'failed' in line.lower()):
                in_failure = False
            elif in_failure and line.strip():
                current_failure.append(line.strip())
        
        # Wait for process to complete
        return_code = process.wait()
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Print summary
        print(f"\n{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"{Colors.BOLD}📊 QUICK SUMMARY{Colors.END}")
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        print(f"⏱️  Execution time: {execution_time:.2f} seconds")
        
        if return_code == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✅ ALL TESTS PASSED!{Colors.END}")
        else:
            print(f"{Colors.RED}{Colors.BOLD}❌ SOME TESTS FAILED (Return code: {return_code}){Colors.END}")
            
            if failed_tests:
                print(f"\n{Colors.RED}💥 Failed tests ({len(failed_tests)} total):{Colors.END}")
                for i, test in enumerate(failed_tests[:10], 1):  # Show first 10
                    print(f"  {i}. {test}")
                
                if len(failed_tests) > 10:
                    print(f"  ... and {len(failed_tests) - 10} more")
        
        print(f"{Colors.CYAN}{'='*60}{Colors.END}")
        
        return return_code
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Tests interrupted by user{Colors.END}")
        return 130
    except Exception as e:
        print(f"\n{Colors.RED}❌ Error running tests: {e}{Colors.END}")
        return 1

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='🏃‍♂️ Quick Test Runner')
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'functional', 'performance'],
        help='Type of tests to run (default: all)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output with detailed tracebacks'
    )
    parser.add_argument(
        '-x', '--stop-on-fail',
        action='store_true',
        help='Stop on first failure'
    )
    
    args = parser.parse_args()
    
    print_header()
    return run_tests(args.test_type, args.verbose, args.stop_on_fail)

if __name__ == '__main__':
    sys.exit(main())
