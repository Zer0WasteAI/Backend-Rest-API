#!/usr/bin/env python3
"""
🔍 TEST FAILURE ANALYZER - ZeroWasteAI API
Analyze test failures and provide actionable insights
"""

import subprocess
import sys
import os
import re
import json
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class FailureAnalyzer:
    """Analyzes test failures and provides insights"""
    
    def __init__(self):
        self.failure_patterns = {
            'import_error': r'ModuleNotFoundError|ImportError',
            'connection_error': r'ConnectionError|TimeoutError|connection.*refused',
            'assertion_error': r'AssertionError|assert.*failed',
            'attribute_error': r'AttributeError|has no attribute',
            'key_error': r'KeyError',
            'type_error': r'TypeError',
            'value_error': r'ValueError',
            'database_error': r'DatabaseError|IntegrityError|OperationalError',
            'http_error': r'HTTPError|status.*[45]\d\d',
            'permission_error': r'PermissionError|permission.*denied',
            'file_error': r'FileNotFoundError|No such file'
        }
        
        self.common_solutions = {
            'import_error': [
                "Install missing dependencies with: pip install -r requirements.txt",
                "Check PYTHONPATH includes src directory",
                "Verify module exists and is properly structured"
            ],
            'connection_error': [
                "Check if database/services are running",
                "Verify connection strings in config",
                "Check network connectivity and ports"
            ],
            'assertion_error': [
                "Review test expectations vs actual behavior",
                "Check if data setup is correct",
                "Verify mock configurations"
            ],
            'database_error': [
                "Run database migrations",
                "Check database permissions",
                "Verify test database setup"
            ],
            'http_error': [
                "Check API endpoint URLs",
                "Verify authentication/authorization",
                "Review request payload format"
            ]
        }

    def run_tests_and_collect_failures(self, test_type: str = "all") -> Tuple[int, str]:
        """Run tests and capture failure output"""
        # Auto-detect Python environment
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
        
        if test_type != "all":
            cmd.append(f'test/{test_type}')
        else:
            cmd.append('test')
        
        cmd.extend([
            '--tb=short',
            '--no-cov',  # Disable coverage for faster execution
            '--disable-warnings',
            '-q',  # Quiet mode
            '--maxfail=20'  # Capture multiple failures
        ])
        
        print(f"{Colors.BLUE}🔍 Analyzing test failures for: {test_type}{Colors.END}")
        print(f"{Colors.YELLOW}Command: {' '.join(cmd)}{Colors.END}\n")
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            return result.returncode, result.stdout + result.stderr
        except Exception as e:
            return 1, str(e)

    def parse_failures(self, output: str) -> List[Dict]:
        """Parse pytest output to extract failure information"""
        failures = []
        
        # Split by test failure sections
        sections = re.split(r'_+ (.*?) _+', output)
        
        current_failure = {}
        for section in sections:
            if '::' in section and 'FAILED' in section:
                # This is a test name
                current_failure = {
                    'test_name': section.strip(),
                    'error_type': 'unknown',
                    'error_message': '',
                    'traceback': '',
                    'file_path': '',
                    'line_number': 0
                }
                
            elif current_failure and ('Traceback' in section or 'Error:' in section):
                # This is the failure content
                current_failure['traceback'] = section.strip()
                
                # Extract error type and message
                for error_type, pattern in self.failure_patterns.items():
                    if re.search(pattern, section, re.IGNORECASE):
                        current_failure['error_type'] = error_type
                        break
                
                # Extract error message
                error_lines = section.split('\n')
                for line in error_lines:
                    if any(err in line for err in ['Error:', 'Exception:', 'AssertionError:']):
                        current_failure['error_message'] = line.strip()
                        break
                
                # Extract file and line info
                file_match = re.search(r'File "([^"]+)", line (\d+)', section)
                if file_match:
                    current_failure['file_path'] = file_match.group(1)
                    current_failure['line_number'] = int(file_match.group(2))
                
                failures.append(current_failure)
                current_failure = {}
        
        # Also parse short summary failures
        if '= FAILURES =' in output or '= ERRORS =' in output:
            lines = output.split('\n')
            in_summary = False
            
            for line in lines:
                if 'FAILED' in line and '::' in line:
                    # Extract test name
                    test_name = line.split(' ')[0] if ' ' in line else line
                    
                    # Check if we already have this failure
                    existing = next((f for f in failures if f['test_name'] == test_name), None)
                    if not existing:
                        failures.append({
                            'test_name': test_name,
                            'error_type': 'unknown',
                            'error_message': line,
                            'traceback': '',
                            'file_path': '',
                            'line_number': 0
                        })
        
        return failures

    def categorize_failures(self, failures: List[Dict]) -> Dict[str, List[Dict]]:
        """Group failures by category"""
        categories = defaultdict(list)
        
        for failure in failures:
            category = failure['error_type']
            categories[category].append(failure)
        
        return dict(categories)

    def analyze_patterns(self, failures: List[Dict]) -> Dict:
        """Analyze failure patterns for insights"""
        analysis = {
            'total_failures': len(failures),
            'error_types': Counter(f['error_type'] for f in failures),
            'affected_files': Counter(f['file_path'] for f in failures if f['file_path']),
            'common_messages': Counter(f['error_message'][:100] for f in failures if f['error_message']),
            'failure_locations': defaultdict(list)
        }
        
        # Group by file location
        for failure in failures:
            if failure['file_path']:
                key = f"{failure['file_path']}:{failure['line_number']}"
                analysis['failure_locations'][key].append(failure)
        
        return analysis

    def print_analysis_report(self, failures: List[Dict], analysis: Dict):
        """Print comprehensive failure analysis"""
        print(f"\n{Colors.RED}{'='*80}{Colors.END}")
        print(f"{Colors.RED}{Colors.BOLD}🔍 TEST FAILURE ANALYSIS REPORT{Colors.END}")
        print(f"{Colors.RED}{'='*80}{Colors.END}")
        
        if not failures:
            print(f"{Colors.GREEN}🎉 No failures detected! All tests are passing.{Colors.END}")
            return
        
        # Summary statistics
        print(f"\n{Colors.BOLD}📊 Failure Summary:{Colors.END}")
        print(f"  Total failures: {Colors.RED}{analysis['total_failures']}{Colors.END}")
        
        # Error type distribution
        print(f"\n{Colors.BOLD}🏷️  Error Type Distribution:{Colors.END}")
        for error_type, count in analysis['error_types'].most_common():
            percentage = (count / analysis['total_failures']) * 100
            print(f"  {Colors.RED}{error_type:20} {count:3d} ({percentage:5.1f}%){Colors.END}")
        
        # Most affected files
        if analysis['affected_files']:
            print(f"\n{Colors.BOLD}📁 Most Affected Files:{Colors.END}")
            for file_path, count in analysis['affected_files'].most_common(5):
                print(f"  {Colors.YELLOW}{count:2d}x {file_path}{Colors.END}")
        
        # Categorized failures with solutions
        categories = self.categorize_failures(failures)
        
        print(f"\n{Colors.BOLD}🔧 Failure Categories & Suggested Solutions:{Colors.END}")
        for category, category_failures in categories.items():
            print(f"\n{Colors.RED}❌ {category.upper()} ({len(category_failures)} failures):{Colors.END}")
            
            # Show first few examples
            for i, failure in enumerate(category_failures[:3], 1):
                test_name = failure['test_name'].split('::')[-1] if '::' in failure['test_name'] else failure['test_name']
                print(f"  {i}. {test_name}")
                if failure['error_message']:
                    print(f"     📝 {failure['error_message'][:80]}...")
            
            if len(category_failures) > 3:
                print(f"     ... and {len(category_failures) - 3} more")
            
            # Suggest solutions
            if category in self.common_solutions:
                print(f"  {Colors.GREEN}💡 Suggested solutions:{Colors.END}")
                for solution in self.common_solutions[category]:
                    print(f"     • {solution}")

    def print_detailed_failures(self, failures: List[Dict], max_details: int = 5):
        """Print detailed information for specific failures"""
        if not failures:
            return
            
        print(f"\n{Colors.BLUE}{'='*80}{Colors.END}")
        print(f"{Colors.BLUE}{Colors.BOLD}🔍 DETAILED FAILURE INFORMATION{Colors.END}")
        print(f"{Colors.BLUE}{'='*80}{Colors.END}")
        
        for i, failure in enumerate(failures[:max_details], 1):
            print(f"\n{Colors.RED}❌ Failure #{i}:{Colors.END}")
            print(f"  {Colors.BOLD}Test:{Colors.END} {failure['test_name']}")
            print(f"  {Colors.BOLD}Type:{Colors.END} {failure['error_type']}")
            
            if failure['file_path']:
                print(f"  {Colors.BOLD}Location:{Colors.END} {failure['file_path']}:{failure['line_number']}")
            
            if failure['error_message']:
                print(f"  {Colors.BOLD}Message:{Colors.END} {failure['error_message']}")
            
            if failure['traceback']:
                print(f"  {Colors.BOLD}Traceback (last 3 lines):{Colors.END}")
                lines = failure['traceback'].split('\n')[-3:]
                for line in lines:
                    if line.strip():
                        print(f"    {line}")
        
        if len(failures) > max_details:
            print(f"\n{Colors.YELLOW}... {len(failures) - max_details} more failures not shown{Colors.END}")
            print(f"{Colors.YELLOW}Use --detailed flag to see all failures{Colors.END}")

    def generate_failure_report(self, failures: List[Dict], analysis: Dict, output_file: str = None):
        """Generate JSON report file"""
        if not output_file:
            output_file = "test_failure_report.json"
        
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_failures': analysis['total_failures'],
                'error_types': dict(analysis['error_types']),
                'affected_files': dict(analysis['affected_files']),
            },
            'failures': failures,
            'solutions': self.common_solutions
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n{Colors.GREEN}📄 Detailed failure report saved: {output_file}{Colors.END}")

    def run_analysis(self, test_type: str = "all", detailed: bool = False, save_report: bool = False):
        """Run complete failure analysis"""
        # Run tests and collect output
        return_code, output = self.run_tests_and_collect_failures(test_type)
        
        if return_code == 0:
            print(f"{Colors.GREEN}🎉 All tests passed! No failures to analyze.{Colors.END}")
            return 0
        
        # Parse failures
        failures = self.parse_failures(output)
        
        if not failures:
            print(f"{Colors.YELLOW}⚠️  Tests failed but no specific failures could be parsed.{Colors.END}")
            print(f"{Colors.YELLOW}Raw output:{Colors.END}")
            print(output[-1000:])  # Show last 1000 chars
            return return_code
        
        # Analyze patterns
        analysis = self.analyze_patterns(failures)
        
        # Print reports
        self.print_analysis_report(failures, analysis)
        
        if detailed:
            self.print_detailed_failures(failures, max_details=10)
        
        if save_report:
            self.generate_failure_report(failures, analysis)
        
        return return_code

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='🔍 Test Failure Analyzer')
    parser.add_argument(
        'test_type',
        nargs='?',
        default='all',
        choices=['all', 'unit', 'integration', 'functional', 'performance'],
        help='Type of tests to analyze (default: all)'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Show detailed failure information'
    )
    parser.add_argument(
        '--save-report',
        action='store_true',
        help='Save JSON report to file'
    )
    
    args = parser.parse_args()
    
    analyzer = FailureAnalyzer()
    return analyzer.run_analysis(args.test_type, args.detailed, args.save_report)

if __name__ == '__main__':
    import time
    sys.exit(main())
