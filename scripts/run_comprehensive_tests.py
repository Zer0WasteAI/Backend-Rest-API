#!/usr/bin/env python3
"""
🧪 COMPREHENSIVE TEST RUNNER - ZeroWasteAI API
Advanced test execution script with detailed failure analysis, coverage reporting, and performance metrics
"""

import sys
import os
import subprocess
import argparse
import json
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
import xml.etree.ElementTree as ET

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class TestResult:
    """Container for test execution results"""
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.skipped_tests = 0
        self.errors = 0
        self.warnings = 0
        self.execution_time = 0.0
        self.coverage_percentage = 0.0
        self.failed_test_details = []
        self.slow_tests = []
        self.coverage_missing = []

class ComprehensiveTestRunner:
    """Advanced test runner with detailed reporting and analysis"""
    
    def __init__(self, args):
        self.args = args
        # scripts/ directory; repo root is parent
        self.project_root = Path(__file__).parent
        self.repo_root = self.project_root.parent
        self.results = TestResult()
        self.start_time = time.time()
        
    def print_header(self):
        """Print colorful header"""
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}🧪 COMPREHENSIVE TEST RUNNER - ZeroWasteAI API{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}📅 Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}📁 Project Root: {self.project_root}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}🎯 Test Type: {self.args.test_type}{Colors.ENDC}")
        print(f"{Colors.OKCYAN}🔢 Parallel Jobs: {self.args.parallel}{Colors.ENDC}\n")

    def build_pytest_command(self) -> List[str]:
        """Build pytest command with all options"""
        # Auto-detect Python environment
        venv_python = self.project_root / 'venv' / 'bin' / 'python'
        
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
        
        # Test paths based on type
        if self.args.test_type == 'unit':
            cmd.append(str(self.repo_root / 'test' / 'unit'))
        elif self.args.test_type == 'integration':
            cmd.append(str(self.repo_root / 'test' / 'integration'))
        elif self.args.test_type == 'functional':
            cmd.append(str(self.repo_root / 'test' / 'functional'))
        elif self.args.test_type == 'performance':
            cmd.append(str(self.repo_root / 'test' / 'performance'))
        elif self.args.test_type == 'production':
            cmd.append(str(self.repo_root / 'test' / 'production_validation'))
        else:  # all
            cmd.append(str(self.repo_root / 'test'))
        
        # Coverage options
        if not self.args.no_coverage:
            cmd.extend([
                '--cov=src',
                '--cov-report=term-missing',
                '--cov-report=html:htmlcov',
                '--cov-report=xml:coverage.xml',
                '--cov-report=json:coverage.json',
                '--cov-branch'
            ])
            
            if self.args.coverage_fail_under:
                cmd.extend([f'--cov-fail-under={self.args.coverage_fail_under}'])
        
        # Output options
        cmd.extend([
            '--verbose',
            '--tb=long' if self.args.detailed_failures else '--tb=short',
            '--junit-xml=test-results.xml',
            '--html=test-report.html',
            '--self-contained-html'
        ])
        
        # Performance options
        if self.args.parallel > 1:
            cmd.extend(['-n', str(self.args.parallel)])
        
        # Filter options
        if self.args.keyword:
            cmd.extend(['-k', self.args.keyword])
        
        if self.args.marker:
            cmd.extend(['-m', self.args.marker])
        
        # Failure handling
        if self.args.maxfail:
            cmd.extend(['--maxfail', str(self.args.maxfail)])
        
        if self.args.stop_on_first_failure:
            cmd.append('-x')
        
        # Additional options
        if self.args.capture == 'no':
            cmd.append('-s')
        elif self.args.capture == 'sys':
            cmd.append('--capture=sys')
        
        if self.args.show_locals:
            cmd.append('--showlocals')
        
        if self.args.durations:
            cmd.extend(['--durations', str(self.args.durations)])
        
        return cmd

    def execute_tests(self) -> Tuple[int, str, str]:
        """Execute pytest with comprehensive logging"""
        cmd = self.build_pytest_command()
        
        print(f"{Colors.OKBLUE}🚀 Executing: {' '.join(cmd)}{Colors.ENDC}\n")
        
        try:
            env = os.environ.copy()
            # Avoid incompatible third-party plugins (e.g., pytest-flask with Flask 3)
            env.setdefault('PYTEST_DISABLE_PLUGIN_AUTOLOAD', '1')
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                cwd=self.repo_root,
                env=env
            )
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)

    def parse_junit_xml(self) -> Dict:
        """Parse JUnit XML results for detailed analysis"""
        xml_path = self.project_root / 'test-results.xml'
        if not xml_path.exists():
            return {}
        
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
            
            results = {
                'testsuites': [],
                'summary': {
                    'total': 0,
                    'passed': 0,
                    'failed': 0,
                    'skipped': 0,
                    'errors': 0,
                    'time': 0.0
                }
            }
            
            for testsuite in root.findall('testsuite'):
                suite_data = {
                    'name': testsuite.get('name', ''),
                    'tests': int(testsuite.get('tests', 0)),
                    'failures': int(testsuite.get('failures', 0)),
                    'errors': int(testsuite.get('errors', 0)),
                    'skipped': int(testsuite.get('skipped', 0)),
                    'time': float(testsuite.get('time', 0)),
                    'testcases': []
                }
                
                for testcase in testsuite.findall('testcase'):
                    case_data = {
                        'name': testcase.get('name', ''),
                        'classname': testcase.get('classname', ''),
                        'time': float(testcase.get('time', 0)),
                        'status': 'passed'
                    }
                    
                    if testcase.find('failure') is not None:
                        failure = testcase.find('failure')
                        case_data['status'] = 'failed'
                        case_data['failure_message'] = failure.get('message', '')
                        case_data['failure_text'] = failure.text or ''
                    
                    elif testcase.find('error') is not None:
                        error = testcase.find('error')
                        case_data['status'] = 'error'
                        case_data['error_message'] = error.get('message', '')
                        case_data['error_text'] = error.text or ''
                    
                    elif testcase.find('skipped') is not None:
                        case_data['status'] = 'skipped'
                        skipped = testcase.find('skipped')
                        case_data['skip_reason'] = skipped.get('message', '')
                    
                    suite_data['testcases'].append(case_data)
                
                results['testsuites'].append(suite_data)
                
                # Update summary
                results['summary']['total'] += suite_data['tests']
                results['summary']['failed'] += suite_data['failures']
                results['summary']['errors'] += suite_data['errors']
                results['summary']['skipped'] += suite_data['skipped']
                results['summary']['time'] += suite_data['time']
            
            results['summary']['passed'] = (
                results['summary']['total'] - 
                results['summary']['failed'] - 
                results['summary']['errors'] - 
                results['summary']['skipped']
            )
            
            return results
            
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  Warning: Could not parse JUnit XML: {e}{Colors.ENDC}")
            return {}

    def parse_coverage_json(self) -> Dict:
        """Parse coverage JSON for detailed coverage analysis"""
        coverage_path = self.project_root / 'coverage.json'
        if not coverage_path.exists():
            return {}
        
        try:
            with open(coverage_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"{Colors.WARNING}⚠️  Warning: Could not parse coverage JSON: {e}{Colors.ENDC}")
            return {}

    def analyze_failures(self, junit_data: Dict) -> List[Dict]:
        """Analyze failed tests for common patterns"""
        failures = []
        
        for testsuite in junit_data.get('testsuites', []):
            for testcase in testsuite.get('testcases', []):
                if testcase['status'] in ['failed', 'error']:
                    failure_info = {
                        'suite': testsuite['name'],
                        'test': testcase['name'],
                        'class': testcase['classname'],
                        'time': testcase['time'],
                        'status': testcase['status'],
                        'message': testcase.get('failure_message', testcase.get('error_message', '')),
                        'details': testcase.get('failure_text', testcase.get('error_text', '')),
                        'category': self.categorize_failure(testcase.get('failure_message', ''))
                    }
                    failures.append(failure_info)
        
        return failures

    def categorize_failure(self, message: str) -> str:
        """Categorize failure based on error message"""
        message_lower = message.lower()
        
        if 'connection' in message_lower or 'timeout' in message_lower:
            return 'Network/Connection'
        elif 'database' in message_lower or 'sql' in message_lower:
            return 'Database'
        elif 'import' in message_lower or 'module' in message_lower:
            return 'Import/Module'
        elif 'assertion' in message_lower or 'assert' in message_lower:
            return 'Assertion'
        elif 'attribute' in message_lower:
            return 'Attribute'
        elif 'key' in message_lower and 'error' in message_lower:
            return 'Key/Index'
        elif 'type' in message_lower and 'error' in message_lower:
            return 'Type'
        elif 'value' in message_lower and 'error' in message_lower:
            return 'Value'
        elif 'permission' in message_lower or 'forbidden' in message_lower:
            return 'Permission'
        elif 'not found' in message_lower or '404' in message_lower:
            return 'Resource Not Found'
        else:
            return 'Other'

    def print_summary(self, junit_data: Dict, coverage_data: Dict):
        """Print comprehensive test summary"""
        summary = junit_data.get('summary', {})
        
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}📊 TEST EXECUTION SUMMARY{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        # Test Results
        total = summary.get('total', 0)
        passed = summary.get('passed', 0)
        failed = summary.get('failed', 0)
        errors = summary.get('errors', 0)
        skipped = summary.get('skipped', 0)
        execution_time = summary.get('time', 0)
        
        print(f"\n{Colors.BOLD}🎯 Test Results:{Colors.ENDC}")
        print(f"  {Colors.OKGREEN}✅ Passed: {passed}{Colors.ENDC}")
        print(f"  {Colors.FAIL}❌ Failed: {failed}{Colors.ENDC}")
        print(f"  {Colors.FAIL}💥 Errors: {errors}{Colors.ENDC}")
        print(f"  {Colors.WARNING}⏭️  Skipped: {skipped}{Colors.ENDC}")
        print(f"  {Colors.OKBLUE}📊 Total: {total}{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}⏱️  Execution Time: {execution_time:.2f}s{Colors.ENDC}")
        
        # Success Rate
        if total > 0:
            success_rate = (passed / total) * 100
            color = Colors.OKGREEN if success_rate >= 90 else Colors.WARNING if success_rate >= 70 else Colors.FAIL
            print(f"  {color}📈 Success Rate: {success_rate:.1f}%{Colors.ENDC}")
        
        # Coverage Information
        if coverage_data and not self.args.no_coverage:
            totals = coverage_data.get('totals', {})
            coverage_percent = totals.get('percent_covered', 0)
            
            print(f"\n{Colors.BOLD}📋 Coverage Report:{Colors.ENDC}")
            print(f"  {Colors.OKGREEN}📊 Coverage: {coverage_percent:.1f}%{Colors.ENDC}")
            print(f"  {Colors.OKBLUE}📄 Covered Lines: {totals.get('covered_lines', 0)}{Colors.ENDC}")
            print(f"  {Colors.WARNING}📄 Missing Lines: {totals.get('missing_lines', 0)}{Colors.ENDC}")
            print(f"  {Colors.OKCYAN}🌿 Branch Coverage: {totals.get('percent_covered_display', 'N/A')}{Colors.ENDC}")

    def print_failure_analysis(self, failures: List[Dict]):
        """Print detailed failure analysis"""
        if not failures:
            print(f"\n{Colors.OKGREEN}🎉 No test failures detected!{Colors.ENDC}")
            return
        
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}🔍 FAILURE ANALYSIS{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        # Failure categories
        categories = {}
        for failure in failures:
            category = failure['category']
            if category not in categories:
                categories[category] = []
            categories[category].append(failure)
        
        print(f"\n{Colors.BOLD}📊 Failure Categories:{Colors.ENDC}")
        for category, fails in categories.items():
            print(f"  {Colors.FAIL}❌ {category}: {len(fails)} failures{Colors.ENDC}")
        
        # Detailed failure information
        print(f"\n{Colors.BOLD}🔍 Detailed Failure Information:{Colors.ENDC}")
        for i, failure in enumerate(failures[:10], 1):  # Show first 10 failures
            print(f"\n{Colors.FAIL}❌ Failure #{i}:{Colors.ENDC}")
            print(f"  {Colors.BOLD}Test:{Colors.ENDC} {failure['test']}")
            print(f"  {Colors.BOLD}Suite:{Colors.ENDC} {failure['suite']}")
            print(f"  {Colors.BOLD}Class:{Colors.ENDC} {failure['class']}")
            print(f"  {Colors.BOLD}Category:{Colors.ENDC} {failure['category']}")
            print(f"  {Colors.BOLD}Time:{Colors.ENDC} {failure['time']:.3f}s")
            print(f"  {Colors.BOLD}Message:{Colors.ENDC} {failure['message'][:200]}...")
        
        if len(failures) > 10:
            print(f"\n{Colors.WARNING}... and {len(failures) - 10} more failures{Colors.ENDC}")

    def print_slow_tests(self, junit_data: Dict):
        """Print slowest tests"""
        all_tests = []
        for testsuite in junit_data.get('testsuites', []):
            for testcase in testsuite.get('testcases', []):
                all_tests.append({
                    'name': testcase['name'],
                    'suite': testsuite['name'],
                    'time': testcase['time']
                })
        
        # Sort by time and get top 10
        slow_tests = sorted(all_tests, key=lambda x: x['time'], reverse=True)[:10]
        
        if slow_tests:
            print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
            print(f"{Colors.HEADER}{Colors.BOLD}⏱️  SLOWEST TESTS{Colors.ENDC}")
            print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
            
            for i, test in enumerate(slow_tests, 1):
                color = Colors.FAIL if test['time'] > 10 else Colors.WARNING if test['time'] > 5 else Colors.OKCYAN
                print(f"{color}{i:2d}. {test['name']} - {test['time']:.3f}s{Colors.ENDC}")

    def generate_report_files(self, junit_data: Dict, coverage_data: Dict, failures: List[Dict]):
        """Generate comprehensive report files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON Summary Report
        report = {
            'timestamp': timestamp,
            'execution_time': time.time() - self.start_time,
            'summary': junit_data.get('summary', {}),
            'coverage': coverage_data.get('totals', {}) if coverage_data else {},
            'failures': failures,
            'configuration': {
                'test_type': self.args.test_type,
                'parallel_jobs': self.args.parallel,
                'coverage_enabled': not self.args.no_coverage
            }
        }
        
        report_file = self.project_root / f'test_report_{timestamp}.json'
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.OKGREEN}📄 Detailed JSON report saved: {report_file}{Colors.ENDC}")

    def run(self) -> int:
        """Main execution method"""
        self.print_header()
        
        # Execute tests
        return_code, stdout, stderr = self.execute_tests()
        
        # Print test output
        if stdout:
            print(stdout)
        
        if stderr and self.args.show_stderr:
            print(f"{Colors.WARNING}STDERR:{Colors.ENDC}")
            print(stderr)
        
        # Parse results
        junit_data = self.parse_junit_xml()
        coverage_data = self.parse_coverage_json()
        failures = self.analyze_failures(junit_data)
        
        # Generate reports
        self.print_summary(junit_data, coverage_data)
        self.print_failure_analysis(failures)
        
        if self.args.show_slow_tests:
            self.print_slow_tests(junit_data)
        
        if self.args.generate_report:
            self.generate_report_files(junit_data, coverage_data, failures)
        
        # Final status
        total_execution_time = time.time() - self.start_time
        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")
        print(f"{Colors.BOLD}⏱️  Total Execution Time: {total_execution_time:.2f}s{Colors.ENDC}")
        
        if return_code == 0:
            print(f"{Colors.OKGREEN}{Colors.BOLD}🎉 ALL TESTS PASSED!{Colors.ENDC}")
        else:
            print(f"{Colors.FAIL}{Colors.BOLD}💥 TESTS FAILED - Return Code: {return_code}{Colors.ENDC}")
        
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")
        
        return return_code

def main():
    parser = argparse.ArgumentParser(
        description='🧪 Comprehensive Test Runner for ZeroWasteAI API',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Test selection
    parser.add_argument(
        '--test-type', 
        choices=['unit', 'integration', 'functional', 'performance', 'production', 'all'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    
    parser.add_argument(
        '-k', '--keyword',
        help='Run tests matching given substring expression'
    )
    
    parser.add_argument(
        '-m', '--marker',
        help='Run tests matching given marker expression'
    )
    
    # Coverage options
    parser.add_argument(
        '--no-coverage',
        action='store_true',
        help='Disable coverage reporting'
    )
    
    parser.add_argument(
        '--coverage-fail-under',
        type=int,
        default=80,
        help='Fail if coverage is below this percentage (default: 80)'
    )
    
    # Output options
    parser.add_argument(
        '--detailed-failures',
        action='store_true',
        help='Show detailed failure tracebacks'
    )
    
    parser.add_argument(
        '--show-slow-tests',
        action='store_true',
        help='Show slowest tests'
    )
    
    parser.add_argument(
        '--show-stderr',
        action='store_true',
        help='Show stderr output'
    )
    
    parser.add_argument(
        '--show-locals',
        action='store_true',
        help='Show local variables in tracebacks'
    )
    
    parser.add_argument(
        '--durations',
        type=int,
        default=10,
        help='Show N slowest tests (0 to disable)'
    )
    
    # Execution options
    parser.add_argument(
        '-n', '--parallel',
        type=int,
        default=1,
        help='Number of parallel processes (default: 1)'
    )
    
    parser.add_argument(
        '--maxfail',
        type=int,
        help='Stop after N failures'
    )
    
    parser.add_argument(
        '-x', '--stop-on-first-failure',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '--capture',
        choices=['no', 'sys', 'fd'],
        default='sys',
        help='Per-test capturing method (default: sys)'
    )
    
    # Report options
    parser.add_argument(
        '--generate-report',
        action='store_true',
        help='Generate detailed JSON report file'
    )
    
    args = parser.parse_args()
    
    # Run tests
    runner = ComprehensiveTestRunner(args)
    return runner.run()

if __name__ == '__main__':
    sys.exit(main())
