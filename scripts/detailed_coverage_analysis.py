#!/usr/bin/env python3
"""
ZeroWasteAI API - Detailed Coverage Analysis
Advanced coverage analysis with module-level reporting and recommendations
"""
import os
import sys
import json
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class CoverageAnalyzer:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.src_path = self.project_root / "src"
        self.reports = {}
        
    def run_pytest_coverage(self, test_path: str, output_name: str) -> Dict[str, Any]:
        """Run pytest with coverage for specific test path"""
        cmd = [
            "python3", "-m", "pytest", test_path,
            "--cov=src",
            f"--cov-report=json:coverage_{output_name}.json",
            f"--cov-report=xml:coverage_{output_name}.xml",
            "--cov-branch",
            "--quiet"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # Load JSON coverage data
            json_file = Path(f"coverage_{output_name}.json")
            coverage_data = {}
            
            if json_file.exists():
                with open(json_file, 'r') as f:
                    coverage_data = json.load(f)
            
            return {
                'success': result.returncode == 0,
                'output': result.stdout,
                'error': result.stderr,
                'coverage_data': coverage_data,
                'json_file': str(json_file),
                'xml_file': f"coverage_{output_name}.xml"
            }
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'Timeout', 'coverage_data': {}}
        except Exception as e:
            return {'success': False, 'error': str(e), 'coverage_data': {}}
    
    def analyze_module_coverage(self, coverage_data: Dict) -> Dict[str, Any]:
        """Analyze coverage at module level"""
        module_analysis = {}
        
        if 'files' in coverage_data:
            for file_path, file_data in coverage_data['files'].items():
                # Extract module information
                if file_path.startswith('src/'):
                    relative_path = file_path[4:]  # Remove 'src/' prefix
                    
                    # Determine module category
                    module_category = self.categorize_module(relative_path)
                    
                    coverage_info = {
                        'file_path': relative_path,
                        'category': module_category,
                        'num_statements': file_data.get('num_statements', 0),
                        'missing_lines': len(file_data.get('missing_lines', [])),
                        'excluded_lines': len(file_data.get('excluded_lines', [])),
                        'coverage_percent': file_data.get('summary', {}).get('percent_covered', 0)
                    }
                    
                    if coverage_info['num_statements'] > 0:
                        coverage_info['covered_lines'] = coverage_info['num_statements'] - coverage_info['missing_lines']
                    else:
                        coverage_info['covered_lines'] = 0
                    
                    module_analysis[relative_path] = coverage_info
        
        return module_analysis
    
    def categorize_module(self, file_path: str) -> str:
        """Categorize modules by their location and purpose"""
        if file_path.startswith('presentation/controllers/'):
            return 'Controllers'
        elif file_path.startswith('application/use_cases/'):
            return 'Use Cases'
        elif file_path.startswith('application/services/'):
            return 'Application Services'
        elif file_path.startswith('domain/'):
            return 'Domain Logic'
        elif file_path.startswith('infrastructure/db/'):
            return 'Database Layer'
        elif file_path.startswith('infrastructure/'):
            return 'Infrastructure'
        elif file_path.startswith('shared/'):
            return 'Shared Utilities'
        elif file_path.startswith('config/'):
            return 'Configuration'
        else:
            return 'Other'
    
    def generate_module_summary(self, module_analysis: Dict) -> Dict[str, Any]:
        """Generate summary by module category"""
        category_summary = {}
        
        for file_path, coverage_info in module_analysis.items():
            category = coverage_info['category']
            
            if category not in category_summary:
                category_summary[category] = {
                    'files': [],
                    'total_statements': 0,
                    'total_covered': 0,
                    'total_missing': 0,
                    'files_count': 0,
                    'avg_coverage': 0
                }
            
            cat_info = category_summary[category]
            cat_info['files'].append({
                'path': file_path,
                'coverage': coverage_info['coverage_percent'],
                'statements': coverage_info['num_statements']
            })
            cat_info['total_statements'] += coverage_info['num_statements']
            cat_info['total_covered'] += coverage_info['covered_lines']
            cat_info['total_missing'] += coverage_info['missing_lines']
            cat_info['files_count'] += 1
        
        # Calculate averages
        for category, info in category_summary.items():
            if info['total_statements'] > 0:
                info['avg_coverage'] = (info['total_covered'] / info['total_statements']) * 100
            else:
                info['avg_coverage'] = 0
            
            # Sort files by coverage (lowest first)
            info['files'].sort(key=lambda x: x['coverage'])
        
        return category_summary
    
    def identify_coverage_gaps(self, module_analysis: Dict) -> List[Dict]:
        """Identify files with low coverage that need attention"""
        gaps = []
        
        for file_path, coverage_info in module_analysis.items():
            coverage_percent = coverage_info['coverage_percent']
            statements = coverage_info['num_statements']
            
            # Identify files needing attention
            priority = 'LOW'
            if coverage_percent < 50 and statements > 20:
                priority = 'HIGH'
            elif coverage_percent < 70 and statements > 10:
                priority = 'MEDIUM'
            elif coverage_percent < 85 and statements > 5:
                priority = 'LOW'
            
            if priority in ['HIGH', 'MEDIUM']:
                gaps.append({
                    'file_path': file_path,
                    'category': coverage_info['category'],
                    'coverage_percent': coverage_percent,
                    'missing_lines': coverage_info['missing_lines'],
                    'total_statements': statements,
                    'priority': priority
                })
        
        # Sort by priority and coverage
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
        gaps.sort(key=lambda x: (priority_order[x['priority']], x['coverage_percent']))
        
        return gaps
    
    def run_comprehensive_analysis(self):
        """Run comprehensive coverage analysis"""
        print("🔍 ZeroWasteAI API - Detailed Coverage Analysis")
        print("=" * 60)
        
        test_suites = [
            ('test/unit/', 'unit'),
            ('test/functional/', 'functional'),
            ('test/integration/', 'integration'),
            ('test/production_validation/', 'production'),
            ('test/performance/', 'performance'),
            ('test/', 'complete')
        ]
        
        analysis_results = {}
        
        for test_path, suite_name in test_suites:
            if Path(test_path).exists():
                print(f"\n📊 Analyzing {suite_name} test coverage...")
                result = self.run_pytest_coverage(test_path, suite_name)
                
                if result['success'] and result['coverage_data']:
                    module_analysis = self.analyze_module_coverage(result['coverage_data'])
                    category_summary = self.generate_module_summary(module_analysis)
                    coverage_gaps = self.identify_coverage_gaps(module_analysis)
                    
                    analysis_results[suite_name] = {
                        'total_coverage': result['coverage_data'].get('totals', {}).get('percent_covered', 0),
                        'module_analysis': module_analysis,
                        'category_summary': category_summary,
                        'coverage_gaps': coverage_gaps,
                        'files_analyzed': len(module_analysis)
                    }
                    
                    total_cov = analysis_results[suite_name]['total_coverage']
                    files_count = analysis_results[suite_name]['files_analyzed']
                    print(f"   ✅ {suite_name.capitalize()}: {total_cov:.1f}% coverage ({files_count} files)")
                else:
                    print(f"   ❌ {suite_name.capitalize()}: Analysis failed")
                    if result['error']:
                        print(f"      Error: {result['error']}")
        
        return analysis_results
    
    def generate_detailed_report(self, analysis_results: Dict):
        """Generate detailed coverage report"""
        print(f"\n\n{'='*80}")
        print("📈 DETAILED COVERAGE ANALYSIS REPORT")
        print(f"{'='*80}")
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Overall coverage summary
        if 'complete' in analysis_results:
            complete_analysis = analysis_results['complete']
            total_coverage = complete_analysis['total_coverage']
            
            print(f"\n🎯 OVERALL COVERAGE: {total_coverage:.2f}%")
            
            # Coverage grade
            if total_coverage >= 90:
                grade, status = "A+", "EXCELLENT"
            elif total_coverage >= 80:
                grade, status = "A", "VERY GOOD"
            elif total_coverage >= 70:
                grade, status = "B", "GOOD"
            elif total_coverage >= 60:
                grade, status = "C", "ACCEPTABLE"
            else:
                grade, status = "D", "NEEDS IMPROVEMENT"
            
            print(f"Coverage Grade: {grade} ({status})")
        
        # Coverage by test suite
        print(f"\n📊 COVERAGE BY TEST SUITE:")
        print("-" * 40)
        for suite_name, results in analysis_results.items():
            coverage = results['total_coverage']
            files = results['files_analyzed']
            print(f"{suite_name.capitalize():<15}: {coverage:6.1f}% ({files:3d} files)")
        
        # Coverage by module category
        if 'complete' in analysis_results:
            print(f"\n🏗️ COVERAGE BY MODULE CATEGORY:")
            print("-" * 50)
            category_summary = analysis_results['complete']['category_summary']
            
            for category, info in sorted(category_summary.items()):
                avg_cov = info['avg_coverage']
                files_count = info['files_count']
                statements = info['total_statements']
                print(f"{category:<20}: {avg_cov:6.1f}% ({files_count:2d} files, {statements:4d} statements)")
        
        # Top coverage gaps
        if 'complete' in analysis_results:
            coverage_gaps = analysis_results['complete']['coverage_gaps']
            if coverage_gaps:
                print(f"\n⚠️ TOP COVERAGE GAPS (Need Attention):")
                print("-" * 60)
                
                high_priority = [gap for gap in coverage_gaps if gap['priority'] == 'HIGH']
                medium_priority = [gap for gap in coverage_gaps if gap['priority'] == 'MEDIUM']
                
                if high_priority:
                    print("🚨 HIGH PRIORITY:")
                    for gap in high_priority[:5]:  # Top 5
                        print(f"   • {gap['file_path']:<40} {gap['coverage_percent']:5.1f}% ({gap['category']})")
                
                if medium_priority:
                    print("\n⚠️ MEDIUM PRIORITY:")
                    for gap in medium_priority[:5]:  # Top 5
                        print(f"   • {gap['file_path']:<40} {gap['coverage_percent']:5.1f}% ({gap['category']})")
            else:
                print(f"\n✅ NO SIGNIFICANT COVERAGE GAPS FOUND!")
        
        # Recommendations
        print(f"\n💡 COVERAGE IMPROVEMENT RECOMMENDATIONS:")
        print("-" * 45)
        
        if 'complete' in analysis_results:
            total_coverage = analysis_results['complete']['total_coverage']
            coverage_gaps = analysis_results['complete']['coverage_gaps']
            
            if total_coverage >= 85:
                print("✅ Excellent coverage! Focus on edge cases and error handling.")
            elif total_coverage >= 75:
                print("✅ Good coverage. Consider testing complex business logic.")
            elif total_coverage >= 65:
                print("⚠️ Acceptable coverage. Focus on critical path testing.")
            else:
                print("❌ Low coverage. Significant testing effort needed.")
            
            high_priority_count = len([g for g in coverage_gaps if g['priority'] == 'HIGH'])
            if high_priority_count > 0:
                print(f"🎯 Priority: Address {high_priority_count} high-priority coverage gaps")
            
            # Category-specific recommendations
            category_summary = analysis_results['complete']['category_summary']
            low_coverage_categories = [
                cat for cat, info in category_summary.items() 
                if info['avg_coverage'] < 70
            ]
            
            if low_coverage_categories:
                print(f"📋 Focus on these module categories: {', '.join(low_coverage_categories)}")
        
        print(f"\n📁 DETAILED REPORTS GENERATED:")
        print("-" * 30)
        for suite_name in analysis_results.keys():
            print(f"• coverage_{suite_name}.json")
            print(f"• coverage_{suite_name}.xml")

def main():
    """Main entry point"""
    analyzer = CoverageAnalyzer()
    
    try:
        # Run comprehensive analysis
        analysis_results = analyzer.run_comprehensive_analysis()
        
        # Generate detailed report
        analyzer.generate_detailed_report(analysis_results)
        
        # Success assessment
        if 'complete' in analysis_results:
            total_coverage = analysis_results['complete']['total_coverage']
            if total_coverage >= 70:
                print(f"\n🎉 COVERAGE ANALYSIS COMPLETED SUCCESSFULLY!")
                print(f"   Overall coverage: {total_coverage:.2f}%")
                sys.exit(0)
            else:
                print(f"\n⚠️ COVERAGE ANALYSIS COMPLETED - IMPROVEMENT NEEDED")
                print(f"   Current coverage: {total_coverage:.2f}%")
                print(f"   Target coverage: 70%+")
                sys.exit(1)
        else:
            print(f"\n❌ COVERAGE ANALYSIS FAILED")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\n\n⚠️ Analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()