# 🧪 Sistema de Tests de Integración

Este sistema de tests permite validar el funcionamiento completo del Backend Rest API, incluyendo autenticación Firebase, reconocimiento de ingredientes, y manejo de inventarios.

## 🌟 Características Principales

- **🔥 Autenticación Firebase**: Tests completos con usuarios anónimos reales
- **🧪 Tests Simplificados**: Validación sin requerir credenciales Firebase
- **📊 Logging Detallado**: Visualización completa de requests y responses
- **📷 Gestión de Imágenes**: Soporte para categorías de ingredientes y comidas
- **🛡️ Validación de Seguridad**: Verificación de endpoints protegidos
- **📋 Reportes**: Generación de reportes XML opcionales

## 📁 Estructura del Proyecto

```
test/
├── README.md                 # Esta documentación
├── run_tests.py             # Script principal para ejecutar tests
├── test_config.py           # Configuración centralizada
├── integration/
│   ├── test_firebase_auth_flow.py    # Tests completos con Firebase
│   └── test_simple_auth_flow.py      # Tests simplificados
└── images/
    ├── ingredients/         # Imágenes de ingredientes individuales 🥕🍎
    └── foods/              # Imágenes de comidas completas 🍕🥗
```

## 🚀 Uso Rápido

### Ejecutar Todos los Tests
```bash
python test/run_tests.py
```

### Ejecutar con Respuestas Detalladas (NUEVO)
```bash
python test/run_tests.py --verbose
```

### Ejecutar Solo Tests Específicos
```bash
# Solo tests simples (sin Firebase)
python test/run_tests.py --type simple

# Solo tests Firebase
python test/run_tests.py --type firebase

# Ambos tipos
python test/run_tests.py --type both
```

### Ver Configuración del Entorno
```bash
python test/run_tests.py --list-config
```

## 🔊 Modo Verbose (NUEVA CARACTERÍSTICA)

El modo `--verbose` muestra información **completa** de todas las requests y responses:

### ✨ Qué Muestra:
- **📤 Request Details**: URL, headers, body (con tokens truncados por seguridad)
- **📋 Response Details**: Status code, headers completos, JSON formateado
- **⏱️ Timing**: Tiempo de respuesta de cada request
- **🔥 Firebase Details**: Información completa del usuario y tokens
- **📊 Data Analysis**: Estructura detallada de respuestas complejas

### 🛡️ Seguridad:
- Los tokens de autenticación se muestran truncados por seguridad
- Se omiten headers sensibles como cookies
- Los tokens en el body también se truncan

### 📄 Ejemplo de Output Verbose:

```
📤 REQUEST POST
🔗 URL: http://localhost:3000/api/auth/firebase-signin
📨 Request Headers:
   Authorization: Bearer eyJhbGciOiAiUlMyNTYi...0YfG-ofYGw
   Content-Type: application/json
📤 Request Body:
{
  "firebase_token": "eyJhbGciOiAiUlMyNTYi...0YfG-ofYGw"
}

📋 FIREBASE SIGNIN RESPONSE
🔗 URL: http://localhost:3000/api/auth/firebase-signin
📊 Status Code: 200
⏱️ Tiempo: 0.15s
📨 Response Headers:
   Server: Werkzeug/3.1.3 Python/3.11.13
   Content-Type: application/json
   Content-Length: 245
📄 Response JSON:
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "uid": "D1vPwLSM65TLzFtmNqWrlv6gfut1",
    "email": null,
    "isAnonymous": true
  },
  "expires_in": 3600
}
```

## 🔥 Tests de Firebase

### Configuración Requerida:
1. **Credenciales Firebase**: `src/config/firebase_credentials.json`
2. **Firebase Admin SDK**: `pip install firebase-admin`

### Flujo del Test:
1. **Crear Usuario Anónimo**: Usando Firebase Admin SDK
2. **Generar Token**: Token personalizado Firebase
3. **Signin Backend**: Intercambiar token por access token
4. **Test Endpoints**: Probar reconocimiento e inventario
5. **Cleanup**: Eliminar usuario de prueba

### Información Detallada Mostrada:
```
📋 FIREBASE USER RECORD:
   UID: D1vPwLSM65TLzFtmNqWrlv6gfut1
   Provider Data: []
   Custom Claims: None
   Creation Time: 1749263924321

📋 CUSTOM TOKEN INFO:
   Tipo: <class 'bytes'>
   Tamaño: 984 bytes
   Preview: b'eyJhbGciOiAiUlMyNTYi...0YfG-ofYGw'
```

## 🧪 Tests Simplificados

### Casos de Uso:
- **Desarrollo Local**: Sin requerir configuración Firebase
- **CI/CD**: Tests rápidos de endpoints
- **Debugging**: Verificar respuestas sin autenticación

### Validaciones:
- ✅ Backend funcionando
- ✅ Firebase configurado
- ✅ Endpoints protegidos (401 esperado)
- ✅ Estructura de errores

## 📷 Gestión de Imágenes

### Categorías Soportadas:
- **🥕 Ingredientes** (`test/images/ingredients/`): Tomate, manzana, lechuga...
- **🍽️ Comidas** (`test/images/foods/`): Pizza, ensalada, pasta...

### Formatos Soportados:
- `.jpg`, `.jpeg`, `.png`, `.bmp`, `.webp`

### Agregar Imágenes:
```bash
# Ingredientes individuales
cp tomate.jpg test/images/ingredients/

# Comidas completas  
cp pizza.jpg test/images/foods/
```

## 📊 Interpretando Resultados

### Códigos de Estado Esperados:
- **200**: Operación exitosa
- **401**: "Authorization token is required" (esperado sin auth)
- **403**: Token inválido o expirado

### Responses Típicas:

#### ✅ Backend Status (200):
```json
{
  "status": "success",
  "architecture": "Firebase Auth + JWT + Clean Architecture",
  "database_name": "zwaidb",
  "security_status": {
    "firebase_integration": "Active",
    "jwt_security": "Active"
  }
}
```

#### 🔒 Endpoint Protegido (401):
```json
{
  "error": "Authorization token is required"
}
```

#### 🥕 Reconocimiento Exitoso (200):
```json
{
  "ingredients": [
    {
      "name": "Tomate",
      "description": "Fruto rojo rico en licopeno",
      "environmental_impact": {
        "carbon_footprint": {"value": 1.1, "unit": "kg"},
        "water_footprint": {"value": 214, "unit": "l"}
      }
    }
  ]
}
```

## 🛠️ Opciones Avanzadas

### Generar Reportes XML:
```bash
python test/run_tests.py --report
# Crea archivos en ./test-reports/
```

### Saltar Validación de Entorno:
```bash
python test/run_tests.py --skip-env-check
```

### Combinando Opciones:
```bash
# Tests Firebase verbosos con reporte
python test/run_tests.py --type firebase --verbose --report

# Tests completos saltando validación
python test/run_tests.py --skip-env-check --verbose
```

## 🐛 Debugging y Troubleshooting

### Errores Comunes:

#### "ModuleNotFoundError: No module named 'firebase_admin'"
```bash
pip install firebase-admin
```

#### "No se encontraron credenciales Firebase"
- Verificar que existe `src/config/firebase_credentials.json`
- Usar `--list-config` para ver la ruta completa

#### "No hay imágenes de prueba"
- Agregar archivos `.jpg` o `.png` en `test/images/ingredients/`
- Usar `--list-config` para ver imágenes detectadas

#### Backend no responde (Connection Error)
- Verificar que el backend esté corriendo en `localhost:3000`
- Comprobar con `curl http://localhost:3000/status`

### Debug Detallado:
```bash
# Ver respuestas completas
python test/run_tests.py --verbose

# Solo configuración
python test/run_tests.py --list-config

# Tests específicos con máximo detalle
python test/run_tests.py --type firebase --verbose --skip-env-check
```

## 📈 Casos de Uso Recomendados

### 🚀 Desarrollo Local:
```bash
# Quick check sin Firebase
python test/run_tests.py --type simple

# Con respuestas detalladas para debugging
python test/run_tests.py --type simple --verbose
```

### 🔥 Validación Completa:
```bash
# Con Firebase y logging completo
python test/run_tests.py --type firebase --verbose

# Todo el sistema
python test/run_tests.py --verbose
```

### 🤖 CI/CD:
```bash
# Tests rápidos con reporte
python test/run_tests.py --type simple --report --skip-env-check
```

### 🐛 Debugging de Problemas:
```bash
# Máxima información
python test/run_tests.py --verbose --skip-env-check

# Ver solo configuración
python test/run_tests.py --list-config
```

## 🔧 Configuración Personalizada

El archivo `test_config.py` contiene toda la configuración:

```python
class TestConfig:
    BASE_URL = "http://localhost:3000"
    TEST_TIMEOUT = 30
    MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_IMAGE_FORMATS = ['.jpg', '.jpeg', '.png', '.bmp', '.webp']
```

## 🎯 Próximos Pasos

1. **Agregar Imágenes**: Colocar archivos de prueba en las carpetas correspondientes
2. **Configurar Firebase**: Si quieres tests completos de autenticación
3. **Ejecutar Tests**: Empezar con `--verbose` para ver todo funcionando
4. **Interpretar Resultados**: Usar la información detallada para debugging

---

**💡 Tip**: Siempre usa `--verbose` cuando estés debuggeando o quieras entender qué está pasando con las respuestas del API. ¡Es la nueva característica más útil para ver exactamente qué datos está devolviendo Firebase y todos los endpoints! 