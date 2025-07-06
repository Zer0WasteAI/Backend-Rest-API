import os

base_path = ""

swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": 'zero_waste_api',
            "route": '/api/docs/v1.json',
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "ZeroWasteAI API",
        "description": """
# ZeroWasteAI - API de Gestión de Inventario y Reducción de Desperdicio Alimentario

## Descripción General
ZeroWasteAI es una plataforma integral que combina inteligencia artificial con gestión de inventario para ayudar a los usuarios a reducir el desperdicio de alimentos. La API proporciona funcionalidades completas para:

- **Gestión de Inventario**: Agregar, actualizar y gestionar alimentos e ingredientes
- **Reconocimiento de Imágenes**: Identificar alimentos automáticamente usando IA
- **Generación de Recetas**: Crear recetas personalizadas basadas en ingredientes disponibles
- **Planificación de Comidas**: Organizar y planificar comidas
- **Ahorro Ambiental**: Calcular el impacto ambiental de las recetas
- **Gestión de Usuarios**: Perfiles y preferencias personalizadas
- **Autenticación**: Sistema seguro con Firebase y JWT

## Características Principales

### 🤖 Inteligencia Artificial
- Reconocimiento automático de ingredientes y alimentos en imágenes
- Generación de recetas personalizadas usando IA
- Cálculo automático de fechas de vencimiento
- Generación de imágenes para recetas

### 📱 Gestión de Inventario
- Agregar elementos manualmente o por reconocimiento
- Seguimiento de fechas de vencimiento
- Gestión de cantidades y unidades
- Categorización por tipo de almacenamiento

### 🍳 Recetas Inteligentes  
- Generación basada en inventario disponible
- Recetas personalizadas según preferencias
- Cálculo de impacto ambiental
- Imágenes generadas automáticamente

### 🌱 Sostenibilidad
- Cálculo de huella de carbono
- Seguimiento de ahorro de agua
- Impacto ambiental de las decisiones alimentarias

## Autenticación
La API utiliza un sistema híbrido de autenticación:
- **Firebase Auth**: Para autenticación de usuarios
- **JWT Tokens**: Para autorización de requests

### Flujo de Autenticación
1. Usuario se autentica con Firebase (email/password, Google, etc.)
2. Cliente envía Firebase ID token a `/api/auth/firebase-signin`
3. API valida el token con Firebase y genera JWT tokens internos
4. Cliente usa JWT tokens para requests subsecuentes

## Rate Limiting
- Endpoints de autenticación: 5 requests/minuto
- Endpoints de refresh: 10 requests/minuto  
- Endpoints generales: 100 requests/minuto

## Códigos de Estado HTTP
- **200**: Éxito
- **201**: Recurso creado exitosamente
- **400**: Datos de entrada inválidos
- **401**: No autorizado (token inválido/expirado)
- **403**: Prohibido (sin permisos)
- **404**: Recurso no encontrado
- **409**: Conflicto (recurso ya existe)
- **429**: Rate limit excedido
- **500**: Error interno del servidor

## Formatos de Respuesta
Todas las respuestas están en formato JSON y siguen patrones consistentes:

### Respuesta Exitosa
```json
{
  "message": "Descripción del éxito",
  "data": { ... }
}
```

### Respuesta de Error
```json
{
  "error": "Descripción del error",
  "details": { ... }  // Opcional: detalles adicionales
}
```

## Versionado
Versión actual: **v1.0**
Base URL: `https://api.zerowasteai.com/api`

Para más información, contacta: zerowasteai4@gmail.com
        """,
        "version": "1.0.0",
        "termsOfService": "https://zer0wasteai.com/terms/",
        "contact": {
            "name": "ZeroWasteAI Support",
            "email": "zerowasteai4@gmail.com",
            "url": "https://zer0wasteai.com/support"
        },
        "license": {
            "name": "MIT",
            "url": "https://opensource.org/licenses/MIT"
        }
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": """
**Autenticación JWT Bearer Token**

Para usar los endpoints protegidos, incluye el token JWT en el header Authorization:

```
Authorization: Bearer <tu_jwt_token>
```

### Cómo obtener el token:
1. Autentícate con Firebase en tu aplicación cliente
2. Envía el Firebase ID token al endpoint `/api/auth/firebase-signin`
3. Usa el `access_token` retornado en requests subsecuentes

### Ejemplo de header:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Nota**: Los tokens expiran en 1 hora. Usa el endpoint `/api/auth/refresh` para renovarlos.
            """
        },
        "Internal-Secret": {
            "type": "apiKey", 
            "name": "X-Internal-Secret",
            "in": "header",
            "description": "Secret interno para endpoints administrativos (solo uso interno del sistema)"
        }
    },
    "security": [
        {"Bearer": []}
    ],
    "host": "api.zerowasteai.com",
    "basePath": "/api",
    "schemes": [
        "https",
        "http"
    ],
    "tags": [
        {
            "name": "Auth",
            "description": "Endpoints de autenticación y autorización"
        },
        {
            "name": "User", 
            "description": "Gestión de perfiles y datos de usuario"
        },
        {
            "name": "Inventory",
            "description": "Gestión completa del inventario de alimentos"
        },
        {
            "name": "Recognition",
            "description": "Reconocimiento de alimentos por IA usando imágenes"
        },
        {
            "name": "Recipe",
            "description": "Generación y gestión de recetas inteligentes"
        },
        {
            "name": "Planning",
            "description": "Planificación de comidas y organización"
        },
        {
            "name": "Environmental",
            "description": "Cálculo de impacto ambiental y sostenibilidad"
        },
        {
            "name": "Generation",
            "description": "Estado y gestión de tareas de generación de contenido"
        },
        {
            "name": "Image Management",
            "description": "Gestión y procesamiento de imágenes"
        },
        {
            "name": "Admin",
            "description": "Endpoints administrativos (uso interno)"
        }
    ],
    "externalDocs": {
        "description": "Documentación completa y guías de integración",
        "url": "https://docs.zerowasteai.com"
    }
}