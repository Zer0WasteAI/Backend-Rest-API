#!/usr/bin/env python3
"""
Script principal para ejecutar tests de integración del Backend Rest API
"""
import unittest
import sys
import argparse
import os
from pathlib import Path

# Agregar el directorio padre al path para imports
test_dir = Path(__file__).parent
sys.path.insert(0, str(test_dir))

from test_config import TestConfig


def run_tests(test_type="both", generate_report=False, skip_env_check=False, verbose=False):
    """
    Ejecuta los tests especificados
    
    Args:
        test_type (str): Tipo de tests a ejecutar ('simple', 'firebase', 'both')
        generate_report (bool): Si generar reporte HTML
        skip_env_check (bool): Si saltar validación del entorno
        verbose (bool): Si mostrar información detallada de respuestas
    """
    
    # Configurar verbosidad en las clases de test
    if verbose:
        os.environ['TEST_VERBOSE'] = 'true'
        print("🔊 Modo verbose activado - se mostrarán respuestas detalladas")
    else:
        os.environ.pop('TEST_VERBOSE', None)
    
    print(f"\n🚀 EJECUTANDO TESTS DE INTEGRACIÓN")
    print(f"📂 Directorio de trabajo: {Path.cwd()}")
    print(f"🎯 Tipo de tests: {test_type}")
    print(f"📊 Generar reporte: {'Sí' if generate_report else 'No'}")
    print(f"🔊 Modo verbose: {'Sí' if verbose else 'No'}")
    
    # Validar entorno si no se salta
    if not skip_env_check:
        print(f"\n🔧 VALIDANDO ENTORNO...")
        TestConfig.print_environment_info()
        
        issues = TestConfig.validate_environment()
        if issues:
            print(f"\n⚠️ PROBLEMAS DETECTADOS:")
            for issue in issues:
                print(f"   - {issue}")
            
            print(f"\n💡 SUGERENCIAS:")
            print(f"   - Asegúrate de que el backend esté ejecutándose en {TestConfig.BASE_URL}")
            print(f"   - Verifica que las credenciales Firebase estén en {TestConfig.FIREBASE_CREDENTIALS_PATH}")
            print(f"   - Agrega imágenes de prueba en {TestConfig.TEST_IMAGES_DIR}")
            print(f"   - O usa --skip-env-check para ejecutar tests sin validación")
            
            # Preguntar si continuar
            try:
                response = input(f"\n¿Continuar con los tests? (y/N): ").strip().lower()
                if response not in ['y', 'yes', 'sí']:
                    print(f"❌ Tests cancelados por el usuario")
                    return False
            except KeyboardInterrupt:
                print(f"\n❌ Tests cancelados por el usuario")
                return False
    else:
        print(f"⏭️ Saltando validación del entorno...")
    
    # Configurar el test runner
    if generate_report:
        try:
            import xmlrunner
            runner = xmlrunner.XMLTestRunner(output='test-reports')
            print(f"📊 Reportes XML se guardarán en ./test-reports/")
        except ImportError:
            print(f"⚠️ xmlrunner no disponible, usando runner estándar")
            runner = unittest.TextTestRunner(verbosity=2)
    else:
        runner = unittest.TextTestRunner(verbosity=2)
    
    # Cargar y ejecutar tests según el tipo
    test_modules = []
    
    if test_type in ['simple', 'both']:
        try:
            from integration.test_simple_auth_flow import TestSimpleAuthFlow
            test_modules.append(TestSimpleAuthFlow)
            print(f"✅ Tests simples cargados")
        except ImportError as e:
            print(f"❌ Error cargando tests simples: {e}")
    
    if test_type in ['firebase', 'both']:
        try:
            from integration.test_firebase_auth_flow import TestFirebaseAuthFlow
            test_modules.append(TestFirebaseAuthFlow)
            print(f"✅ Tests Firebase cargados")
        except ImportError as e:
            print(f"❌ Error cargando tests Firebase: {e}")
            if test_type == 'firebase':
                print(f"💡 Asegúrate de que firebase-admin esté instalado: pip install firebase-admin")
    
    if not test_modules:
        print(f"❌ No se pudieron cargar módulos de test")
        return False
    
    # Crear suite de tests
    suite = unittest.TestSuite()
    
    for test_module in test_modules:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_module)
        suite.addTests(tests)
    
    print(f"\n🧪 INICIANDO EJECUCIÓN DE TESTS...")
    print(f"📊 Total de test cases: {suite.countTestCases()}")
    
    # Ejecutar tests
    result = runner.run(suite)
    
    # Mostrar resumen
    print(f"\n📋 RESUMEN DE EJECUCIÓN:")
    print(f"   🧪 Tests ejecutados: {result.testsRun}")
    print(f"   ✅ Exitosos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"   ❌ Fallidos: {len(result.failures)}")
    print(f"   🚫 Errores: {len(result.errors)}")
    print(f"   ⏭️ Saltados: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    
    # Mostrar detalles de fallos si los hay
    if result.failures:
        print(f"\n💥 DETALLES DE FALLOS:")
        for i, (test, traceback) in enumerate(result.failures, 1):
            print(f"   {i}. {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n🚫 DETALLES DE ERRORES:")
        for i, (test, traceback) in enumerate(result.errors, 1):
            print(f"   {i}. {test}: {traceback.split()[-1] if traceback.split() else 'Error desconocido'}")
    
    # Consejos finales
    print(f"\n💡 CONSEJOS:")
    if result.failures or result.errors:
        print(f"   - Si hay errores de conexión, verifica que el backend esté ejecutándose")
        print(f"   - Si hay errores de Firebase, verifica las credenciales")
        print(f"   - Si hay errores de imágenes, agrega archivos en {TestConfig.TEST_IMAGES_DIR}")
    else:
        print(f"   - ¡Todos los tests pasaron! El sistema está funcionando correctamente")
    
    if verbose:
        print(f"   - Para menor verbosidad, ejecuta sin --verbose")
    else:
        print(f"   - Para más detalles, ejecuta con --verbose")
    
    # Retornar si todos los tests pasaron
    return len(result.failures) == 0 and len(result.errors) == 0


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Ejecuta tests de integración del Backend Rest API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python test/run_tests.py                    # Ejecutar todos los tests
  python test/run_tests.py --type simple     # Solo tests simples
  python test/run_tests.py --type firebase   # Solo tests Firebase
  python test/run_tests.py --verbose         # Con respuestas detalladas
  python test/run_tests.py --report          # Generar reporte XML
  python test/run_tests.py --skip-env-check  # Saltar validación del entorno
        """
    )
    
    parser.add_argument(
        '--type', 
        choices=['simple', 'firebase', 'both'], 
        default='both',
        help='Tipo de tests a ejecutar (default: both)'
    )
    
    parser.add_argument(
        '--report', 
        action='store_true',
        help='Generar reporte XML de tests'
    )
    
    parser.add_argument(
        '--skip-env-check', 
        action='store_true',
        help='Saltar validación del entorno'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar respuestas detalladas de API (útil para debugging)'
    )
    
    parser.add_argument(
        '--list-config',
        action='store_true',
        help='Mostrar configuración del entorno y salir'
    )
    
    args = parser.parse_args()
    
    # Si solo quiere ver la configuración
    if args.list_config:
        TestConfig.print_environment_info()
        issues = TestConfig.validate_environment()
        if issues:
            print(f"\n⚠️ PROBLEMAS DETECTADOS:")
            for issue in issues:
                print(f"   - {issue}")
        return 0
    
    # Ejecutar tests
    success = run_tests(
        test_type=args.type,
        generate_report=args.report,
        skip_env_check=args.skip_env_check,
        verbose=args.verbose
    )
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 