#!/usr/bin/env python3
"""
Analizador de cobertura de tests de integración
Verifica que todos los controladores tengan tests de integración correspondientes
"""

import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Set, Tuple


class IntegrationTestCoverageAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.controllers_dir = self.project_root / "src" / "interface" / "controllers"
        self.integration_tests_dir = self.project_root / "test" / "integration"
        
    def analyze_integration_test_coverage(self) -> Dict[str, Dict[str, any]]:
        """Analiza la cobertura de tests de integración para todos los controladores"""
        results = {}
        
        # Obtener todos los controladores
        controllers = self._get_all_controllers()
        
        # Obtener todos los archivos de tests de integración
        integration_test_files = self._get_integration_test_files()
        
        # Analizar cada controlador
        for controller_name in controllers:
            # Buscar tests de integración relacionados
            related_tests = self._find_related_integration_tests(controller_name, integration_test_files)
            
            # Extraer endpoints del controlador
            controller_endpoints = self._extract_controller_endpoints(controller_name)
            
            # Verificar cobertura
            covered_endpoints = self._analyze_endpoint_coverage(controller_name, related_tests, controller_endpoints)
            
            results[controller_name] = {
                "controller_file": f"{controller_name}.py",
                "endpoints": controller_endpoints,
                "integration_test_files": related_tests,
                "covered_endpoints": covered_endpoints,
                "missing_coverage": list(set(controller_endpoints) - set(covered_endpoints)),
                "coverage_percentage": self._calculate_coverage_percentage(controller_endpoints, covered_endpoints),
                "has_integration_tests": len(related_tests) > 0
            }
            
        return results
    
    def _get_all_controllers(self) -> List[str]:
        """Obtiene la lista de todos los controladores"""
        controllers = []
        
        for controller_file in self.controllers_dir.glob("*.py"):
            if controller_file.name != "__init__.py":
                controller_name = controller_file.stem
                controllers.append(controller_name)
                
        return sorted(controllers)
    
    def _get_integration_test_files(self) -> List[Path]:
        """Obtiene todos los archivos de tests de integración"""
        test_files = []
        
        for test_file in self.integration_tests_dir.glob("*.py"):
            if test_file.name != "__init__.py":
                test_files.append(test_file)
                
        return test_files
    
    def _find_related_integration_tests(self, controller_name: str, test_files: List[Path]) -> List[str]:
        """Encuentra archivos de tests de integración relacionados con el controlador"""
        related_tests = []
        
        # Patrones para buscar
        controller_base = controller_name.replace("_controller", "")
        search_patterns = [
            controller_name,           # exact match
            controller_base,           # without _controller suffix
            controller_base.replace("_", ""),  # without underscores
        ]
        
        for test_file in test_files:
            test_content = self._read_file_content(test_file)
            if test_content:
                # Buscar referencias al controlador en el contenido
                for pattern in search_patterns:
                    if (pattern in test_file.name.lower() or
                        pattern in test_content.lower() or
                        f"from src.interface.controllers.{controller_name}" in test_content or
                        f"controllers.{controller_name}" in test_content):
                        related_tests.append(test_file.name)
                        break
                        
        return related_tests
    
    def _extract_controller_endpoints(self, controller_name: str) -> List[str]:
        """Extrae los endpoints de un controlador"""
        endpoints = []
        controller_file = self.controllers_dir / f"{controller_name}.py"
        
        content = self._read_file_content(controller_file)
        if not content:
            return endpoints
            
        # Buscar patrones de rutas Flask
        route_patterns = [
            r'@\w+_bp\.route\([\'"]([^\'"]+)[\'"].*?\)\s*(?:@[^\n]*\s*)*def\s+(\w+)',
            r'@app\.route\([\'"]([^\'"]+)[\'"].*?\)\s*(?:@[^\n]*\s*)*def\s+(\w+)',
        ]
        
        for pattern in route_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            for route, method_name in matches:
                endpoint_info = f"{method_name} ({route})"
                endpoints.append(endpoint_info)
                
        return endpoints
    
    def _analyze_endpoint_coverage(self, controller_name: str, test_files: List[str], endpoints: List[str]) -> List[str]:
        """Analiza qué endpoints tienen cobertura en tests de integración"""
        covered_endpoints = []
        
        # Leer contenido de todos los archivos de test relacionados
        test_contents = []
        for test_file_name in test_files:
            test_file_path = self.integration_tests_dir / test_file_name
            content = self._read_file_content(test_file_path)
            if content:
                test_contents.append(content)
        
        # Verificar cobertura de cada endpoint
        for endpoint in endpoints:
            # Extraer información del endpoint
            parts = endpoint.split(" (")
            method_name = parts[0]
            route = parts[1].rstrip(")") if len(parts) > 1 else ""
            
            # Buscar referencias en los tests
            is_covered = False
            for content in test_contents:
                # Buscar por nombre de método
                if (f"test_{method_name}" in content.lower() or
                    f"/{method_name}" in content.lower() or
                    method_name in content):
                    is_covered = True
                    break
                    
                # Buscar por ruta
                if route and route in content:
                    is_covered = True
                    break
                    
                # Buscar patrones comunes
                route_base = route.split('/')[-1] if route else method_name
                if route_base in content.lower():
                    is_covered = True
                    break
            
            if is_covered:
                covered_endpoints.append(endpoint)
                
        return covered_endpoints
    
    def _calculate_coverage_percentage(self, total_endpoints: List[str], covered_endpoints: List[str]) -> float:
        """Calcula el porcentaje de cobertura"""
        if not total_endpoints:
            return 100.0
            
        return (len(covered_endpoints) / len(total_endpoints)) * 100
    
    def _read_file_content(self, file_path: Path) -> str:
        """Lee el contenido de un archivo"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error leyendo {file_path}: {e}")
            return ""
    
    def generate_integration_coverage_report(self) -> str:
        """Genera un reporte completo de cobertura de tests de integración"""
        analysis = self.analyze_integration_test_coverage()
        
        report = []
        report.append("# ANÁLISIS DE COBERTURA DE TESTS DE INTEGRACIÓN")
        report.append("=" * 60)
        report.append("")
        
        # Resumen general
        total_controllers = len(analysis)
        controllers_with_tests = sum(1 for data in analysis.values() if data["has_integration_tests"])
        total_endpoints = sum(len(data["endpoints"]) for data in analysis.values())
        total_covered = sum(len(data["covered_endpoints"]) for data in analysis.values())
        
        overall_coverage = (total_covered / total_endpoints * 100) if total_endpoints > 0 else 100
        
        report.append("## RESUMEN GENERAL")
        report.append(f"- Total de controladores: {total_controllers}")
        report.append(f"- Controladores con tests de integración: {controllers_with_tests}")
        report.append(f"- Controladores sin tests de integración: {total_controllers - controllers_with_tests}")
        report.append(f"- Total de endpoints: {total_endpoints}")
        report.append(f"- Endpoints cubiertos: {total_covered}")
        report.append(f"- Cobertura general: {overall_coverage:.1f}%")
        report.append("")
        
        # Lista de archivos de tests de integración existentes
        test_files = self._get_integration_test_files()
        report.append("## ARCHIVOS DE TESTS DE INTEGRACIÓN EXISTENTES")
        report.append("-" * 40)
        for test_file in test_files:
            report.append(f"- {test_file.name}")
        report.append("")
        
        # Análisis por controlador
        report.append("## ANÁLISIS POR CONTROLADOR")
        report.append("-" * 30)
        
        for controller_name, data in sorted(analysis.items()):
            status_icon = "✅" if data["has_integration_tests"] else "❌"
            report.append(f"\n### {status_icon} {controller_name.upper()}")
            report.append(f"- Archivo: {data['controller_file']}")
            report.append(f"- Cobertura: {data['coverage_percentage']:.1f}%")
            report.append(f"- Total endpoints: {len(data['endpoints'])}")
            report.append(f"- Endpoints cubiertos: {len(data['covered_endpoints'])}")
            
            if data["integration_test_files"]:
                report.append("- Tests de integración relacionados:")
                for test_file in data["integration_test_files"]:
                    report.append(f"  - {test_file}")
            else:
                report.append("- ❌ SIN tests de integración")
            
            if data["endpoints"]:
                report.append("- Endpoints del controlador:")
                for endpoint in data["endpoints"]:
                    covered_icon = "✅" if endpoint in data["covered_endpoints"] else "❌"
                    report.append(f"  {covered_icon} {endpoint}")
            
            if data["missing_coverage"]:
                report.append("- ❌ Endpoints SIN cobertura de integración:")
                for endpoint in data["missing_coverage"]:
                    report.append(f"  - {endpoint}")
        
        # Recomendaciones
        report.append("\n\n## RECOMENDACIONES")
        report.append("-" * 20)
        
        controllers_without_tests = [name for name, data in analysis.items() if not data["has_integration_tests"]]
        if controllers_without_tests:
            report.append("### Controladores que necesitan tests de integración:")
            for controller in controllers_without_tests:
                report.append(f"- {controller}")
            report.append("")
        
        low_coverage_controllers = [
            (name, data["coverage_percentage"]) 
            for name, data in analysis.items() 
            if data["coverage_percentage"] < 50 and data["has_integration_tests"]
        ]
        if low_coverage_controllers:
            report.append("### Controladores con baja cobertura (<50%):")
            for controller, coverage in low_coverage_controllers:
                report.append(f"- {controller}: {coverage:.1f}%")
            report.append("")
        
        # Patrones de tests faltantes
        report.append("### Tipos de tests de integración recomendados:")
        report.append("- Workflow completos entre controladores")
        report.append("- Tests de autenticación y autorización")
        report.append("- Tests de manejo de errores end-to-end")
        report.append("- Tests de validación de datos")
        report.append("- Tests de rendimiento básico")
        
        return "\n".join(report)


if __name__ == "__main__":
    analyzer = IntegrationTestCoverageAnalyzer("/Users/rafaelprimo/Backend-Rest-API")
    report = analyzer.generate_integration_coverage_report()
    
    # Guardar reporte
    output_file = Path("/Users/rafaelprimo/Backend-Rest-API/INTEGRATION_TEST_COVERAGE_ANALYSIS.md")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(report)
    print(f"\n📄 Reporte de integración guardado en: {output_file}")
