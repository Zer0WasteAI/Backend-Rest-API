#!/usr/bin/env python3
"""
Analizador de cobertura de tests para controladores y servicios
Verifica que cada método tenga sus tests correspondientes
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple

class TestCoverageAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.controllers_dir = self.project_root / "src" / "interface" / "controllers"
        self.services_dir = self.project_root / "src" / "application" / "services"
        self.infrastructure_services_dir = self.project_root / "src" / "infrastructure" / "services"
        self.tests_dir = self.project_root / "test" / "unit"
        
    def analyze_controller_coverage(self) -> Dict[str, Dict[str, List[str]]]:
        """Analiza la cobertura de tests para todos los controladores"""
        results = {}
        
        for controller_file in self.controllers_dir.glob("*.py"):
            if controller_file.name == "__init__.py":
                continue
                
            controller_name = controller_file.stem
            methods = self._extract_controller_methods(controller_file)
            test_file = self.tests_dir / "interface" / "controllers" / f"test_{controller_name}.py"
            
            if test_file.exists():
                test_methods = self._extract_test_methods(test_file)
                missing_tests = self._find_missing_tests(methods, test_methods, controller_name)
            else:
                test_methods = []
                missing_tests = methods
                
            results[controller_name] = {
                "methods": methods,
                "tests": test_methods,
                "missing_tests": missing_tests,
                "test_file_exists": test_file.exists(),
                "coverage_percentage": self._calculate_coverage(methods, missing_tests)
            }
            
        return results
    
    def analyze_service_coverage(self) -> Dict[str, Dict[str, List[str]]]:
        """Analiza la cobertura de tests para todos los servicios"""
        results = {}
        
        # Servicios de aplicación
        for service_file in self.services_dir.glob("*.py"):
            if service_file.name == "__init__.py":
                continue
                
            service_name = service_file.stem
            methods = self._extract_service_methods(service_file)
            test_file = self.tests_dir / "application" / "services" / f"test_{service_name}.py"
            
            if test_file.exists():
                test_methods = self._extract_test_methods(test_file)
                missing_tests = self._find_missing_tests(methods, test_methods, service_name)
            else:
                test_methods = []
                missing_tests = methods
                
            results[f"application/{service_name}"] = {
                "methods": methods,
                "tests": test_methods,
                "missing_tests": missing_tests,
                "test_file_exists": test_file.exists(),
                "coverage_percentage": self._calculate_coverage(methods, missing_tests)
            }
        
        # Servicios de infraestructura
        for service_file in self.infrastructure_services_dir.glob("*.py"):
            if service_file.name == "__init__.py":
                continue
                
            service_name = service_file.stem
            methods = self._extract_service_methods(service_file)
            test_file = self.tests_dir / "infrastructure" / "services" / f"test_{service_name}.py"
            
            if test_file.exists():
                test_methods = self._extract_test_methods(test_file)
                missing_tests = self._find_missing_tests(methods, test_methods, service_name)
            else:
                test_methods = []
                missing_tests = methods
                
            results[f"infrastructure/{service_name}"] = {
                "methods": methods,
                "tests": test_methods,
                "missing_tests": missing_tests,
                "test_file_exists": test_file.exists(),
                "coverage_percentage": self._calculate_coverage(methods, missing_tests)
            }
            
        return results
    
    def _extract_controller_methods(self, file_path: Path) -> List[str]:
        """Extrae los métodos de endpoint de un controlador"""
        methods = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar patrones de rutas Flask
            route_pattern = r'@\w+_bp\.route\([\'"]([^\'"]+)[\'"].*?\)\s*(?:@[^\n]*\s*)*def\s+(\w+)'
            matches = re.findall(route_pattern, content, re.MULTILINE | re.DOTALL)
            
            for route, method_name in matches:
                methods.append(method_name)
                
        except Exception as e:
            print(f"Error analizando {file_path}: {e}")
            
        return methods
    
    def _extract_service_methods(self, file_path: Path) -> List[str]:
        """Extrae los métodos públicos de un servicio"""
        methods = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            if not item.name.startswith('_'):  # Solo métodos públicos
                                methods.append(f"{node.name}.{item.name}")
                elif isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                    # Funciones del módulo (no dentro de clase)
                    methods.append(node.name)
                    
        except Exception as e:
            print(f"Error analizando {file_path}: {e}")
            
        return methods
    
    def _extract_test_methods(self, file_path: Path) -> List[str]:
        """Extrae los métodos de test de un archivo de test"""
        test_methods = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Buscar métodos que empiecen con test_
            test_pattern = r'def\s+(test_\w+)'
            matches = re.findall(test_pattern, content)
            test_methods.extend(matches)
            
        except Exception as e:
            print(f"Error analizando tests {file_path}: {e}")
            
        return test_methods
    
    def _find_missing_tests(self, methods: List[str], test_methods: List[str], component_name: str) -> List[str]:
        """Encuentra métodos que no tienen tests correspondientes"""
        missing = []
        
        for method in methods:
            method_base = method.split('.')[-1]  # Para servicios con ClassName.method
            
            # Patrones esperados de tests
            expected_patterns = [
                f"test_{method_base}",
                f"test_{method_base}_success",
                f"test_{method_base}_error",
                f"test_{component_name}_{method_base}",
                f"test_{method_base.replace('_', '')}"  # Sin underscores
            ]
            
            has_test = False
            for pattern in expected_patterns:
                if any(pattern in test_method for test_method in test_methods):
                    has_test = True
                    break
            
            if not has_test:
                missing.append(method)
                
        return missing
    
    def _calculate_coverage(self, methods: List[str], missing_tests: List[str]) -> float:
        """Calcula el porcentaje de cobertura de tests"""
        if not methods:
            return 100.0
            
        covered = len(methods) - len(missing_tests)
        return (covered / len(methods)) * 100
    
    def generate_report(self) -> str:
        """Genera un reporte completo de cobertura"""
        controller_analysis = self.analyze_controller_coverage()
        service_analysis = self.analyze_service_coverage()
        
        report = []
        report.append("# ANÁLISIS COMPLETO DE COBERTURA DE TESTS")
        report.append("=" * 50)
        report.append("")
        
        # Resumen general
        total_methods = 0
        total_missing = 0
        
        for analysis in [controller_analysis, service_analysis]:
            for component_data in analysis.values():
                total_methods += len(component_data["methods"])
                total_missing += len(component_data["missing_tests"])
        
        overall_coverage = ((total_methods - total_missing) / total_methods * 100) if total_methods > 0 else 100
        report.append(f"## RESUMEN GENERAL")
        report.append(f"- Total de métodos: {total_methods}")
        report.append(f"- Métodos sin tests: {total_missing}")
        report.append(f"- Cobertura general: {overall_coverage:.1f}%")
        report.append("")
        
        # Controladores
        report.append("## CONTROLADORES")
        report.append("-" * 20)
        
        for controller_name, data in sorted(controller_analysis.items()):
            report.append(f"\n### {controller_name.upper()}")
            report.append(f"- Archivo de test: {'✅ Existe' if data['test_file_exists'] else '❌ NO EXISTE'}")
            report.append(f"- Cobertura: {data['coverage_percentage']:.1f}%")
            report.append(f"- Métodos totales: {len(data['methods'])}")
            report.append(f"- Tests existentes: {len(data['tests'])}")
            
            if data["missing_tests"]:
                report.append("- ❌ Métodos SIN tests:")
                for method in data["missing_tests"]:
                    report.append(f"  - {method}")
            else:
                report.append("- ✅ Todos los métodos tienen tests")
                
            if data["methods"]:
                report.append("- Métodos disponibles:")
                for method in data["methods"]:
                    status = "✅" if method not in data["missing_tests"] else "❌"
                    report.append(f"  {status} {method}")
        
        # Servicios
        report.append("\n\n## SERVICIOS")
        report.append("-" * 20)
        
        for service_name, data in sorted(service_analysis.items()):
            if not data["methods"]:  # Skip servicios sin métodos públicos
                continue
                
            report.append(f"\n### {service_name.upper()}")
            report.append(f"- Archivo de test: {'✅ Existe' if data['test_file_exists'] else '❌ NO EXISTE'}")
            report.append(f"- Cobertura: {data['coverage_percentage']:.1f}%")
            report.append(f"- Métodos totales: {len(data['methods'])}")
            report.append(f"- Tests existentes: {len(data['tests'])}")
            
            if data["missing_tests"]:
                report.append("- ❌ Métodos SIN tests:")
                for method in data["missing_tests"]:
                    report.append(f"  - {method}")
            else:
                report.append("- ✅ Todos los métodos tienen tests")
                
            if data["methods"]:
                report.append("- Métodos disponibles:")
                for method in data["methods"]:
                    status = "✅" if method not in data["missing_tests"] else "❌"
                    report.append(f"  {status} {method}")
        
        return "\n".join(report)


if __name__ == "__main__":
    analyzer = TestCoverageAnalyzer("/Users/rafaelprimo/Backend-Rest-API")
    report = analyzer.generate_report()
    
    # Guardar reporte
    output_file = Path("/Users/rafaelprimo/Backend-Rest-API/TEST_COVERAGE_ANALYSIS.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Reporte guardado en: {output_file}")
