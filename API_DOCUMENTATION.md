# ZeroWasteAI REST API - Documentación Completa

## Información General

**Versión**: 1.0.0  
**Arquitectura**: Clean Architecture con Firebase Authentication + JWT  
**URL Base**: `http://localhost:3000` (desarrollo)  
**Documentación Swagger**: `/apidocs`  

### Características del Sistema

- 🔥 **Autenticación**: Firebase + JWT con rotación segura de tokens
- 👤 **Gestión de Usuarios**: Perfiles completos con Firestore
- 🤖 **IA Integrada**: Reconocimiento de alimentos y generación de recetas
- 📦 **Inventario Inteligente**: Gestión automatizada con fechas de vencimiento
- 🍳 **Generación de Recetas**: Basadas en inventario y personalizadas
- 📸 **Procesamiento de Imágenes**: Upload y generación asíncrona
- 🌱 **Impacto Ambiental**: Cálculos de sostenibilidad alimentaria
- 🛡️ **Seguridad Empresarial**: Headers de seguridad y rate limiting

---

## Endpoints del Sistema

### 1. INFORMACIÓN DEL SISTEMA

#### `GET /`
**Descripción**: Página de bienvenida con información del API  
**Autenticación**: No requerida  
**Response**:
```json
{
  "message": "¡Bienvenido a ZeroWasteAI API! 🌱",
  "description": "API para reconocimiento de alimentos y gestión de inventario inteligente",
  "version": "1.0.0",
  "architecture": "Clean Architecture with Firebase Authentication + JWT",
  "endpoints": {
    "authentication": "/api/auth",
    "user_profile": "/api/user", 
    "food_recognition": "/api/recognition",
    "inventory_management": "/api/inventory",
    "recipe_generation": "/api/recipes",
    "image_management": "/api/image_management",
    "admin_panel": "/api/admin",
    "api_status": "/status",
    "documentation": "/apidocs"
  }
}
```

#### `GET /status`
**Descripción**: Estado de salud del sistema y conexión a base de datos  
**Autenticación**: No requerida  
**Response**:
```json
{
  "status": "success",
  "message": "✅ Conexión exitosa a la base de datos",
  "architecture": "Firebase Auth + JWT + Clean Architecture",
  "database_info": {
    "host": "localhost",
    "port": 3306,
    "name": "zerowasteai_db",
    "user": "app_user"
  },
  "security_status": {
    "jwt_security": "Active",
    "token_blacklisting": "Enabled",
    "security_headers": "Configured",
    "firebase_integration": "Active"
  }
}
```

---

## 2. AUTENTICACIÓN (`/api/auth`)

### `POST /api/auth/firebase-signin`
**Descripción**: Autenticación principal con Firebase ID Token  
**Autenticación**: Firebase ID Token requerido  
**Headers**: `Authorization: Bearer <firebase_id_token>`

**Request Body**: No requerido (datos en token Firebase)

**Response 200**:
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "user": {
    "uid": "firebase_user_uid_123",
    "email": "usuario@ejemplo.com",
    "name": "Juan Pérez",
    "photo_url": "https://lh3.googleusercontent.com/...",
    "email_verified": true
  },
  "profile": {
    "displayName": "Juan Pérez",
    "language": "es",
    "cookingLevel": "intermediate",
    "measurementUnit": "metric",
    "allergies": [],
    "preferredFoodTypes": []
  }
}
```

### `POST /api/auth/refresh`
**Descripción**: Renovación de tokens JWT con rotación segura  
**Autenticación**: Refresh Token JWT requerido  
**Headers**: `Authorization: Bearer <refresh_token>`

**Response 200**:
```json
{
  "message": "Tokens refreshed successfully",
  "tokens": {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJI...",
    "token_type": "Bearer",
    "expires_in": 3600
  },
  "rotated": true,
  "previous_token_invalidated": true
}
```

### `POST /api/auth/logout`
**Descripción**: Cerrar sesión invalidando todos los tokens del usuario  
**Autenticación**: Access Token JWT requerido  
**Headers**: `Authorization: Bearer <access_token>`

**Response 200**:
```json
{
  "message": "Logout successful",
  "logged_out_at": "2024-01-15T10:30:00Z",
  "tokens_invalidated": true,
  "all_sessions_closed": true
}
```

### `GET /api/auth/firebase-debug`
**Descripción**: Debug de configuración Firebase (solo desarrollo)  
**Autenticación**: No requerida  
**Nota**: ⚠️ Deshabilitar en producción

---

## 3. PERFIL DE USUARIO (`/api/user`)

### `GET /api/user/profile`
**Descripción**: Obtener perfil completo del usuario desde Firestore  
**Autenticación**: Access Token requerido

**Response 200**:
```json
{
  "uid": "00HkiYIBxoVGnIZQQ76S7dbM52E3",
  "displayName": "Carlos Primo",
  "email": "carlos@gm.co",
  "photoURL": null,
  "emailVerified": true,
  "authProvider": "password",
  "language": "es",
  "cookingLevel": "intermediate",
  "measurementUnit": "metric",
  "allergies": [],
  "allergyItems": [],
  "preferredFoodTypes": [],
  "specialDietItems": [],
  "favoriteRecipes": [],
  "initialPreferencesCompleted": true,
  "createdAt": "2025-05-23T08:16:24Z",
  "lastLoginAt": "2025-05-23T08:16:25Z"
}
```

### `PUT /api/user/profile`
**Descripción**: Actualizar perfil de usuario en Firestore  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "displayName": "Carlos Primo Actualizado",
  "language": "en",
  "cookingLevel": "advanced",
  "measurementUnit": "imperial",
  "allergies": ["nuts", "dairy"],
  "allergyItems": ["almendras", "leche"],
  "preferredFoodTypes": ["mediterranea", "italiana"],
  "specialDietItems": ["vegetarian"],
  "initialPreferencesCompleted": true
}
```

**Response 200**:
```json
{
  "message": "Perfil actualizado exitosamente",
  "profile": {
    "uid": "00HkiYIBxoVGnIZQQ76S7dbM52E3",
    "displayName": "Carlos Primo Actualizado",
    "language": "en",
    "cookingLevel": "advanced"
  }
}
```

---

## 4. RECONOCIMIENTO IA (`/api/recognition`)

### `POST /api/recognition/ingredients`
**Descripción**: Reconocimiento automático de ingredientes en imágenes  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "images_paths": [
    "uploads/recognition/abc123-image1.jpg",
    "uploads/recognition/def456-image2.jpg"
  ]
}
```

**Response 200**:
```json
{
  "ingredients": [
    {
      "name": "Tomates cherry",
      "quantity": 500,
      "type_unit": "gr",
      "storage_type": "refrigerador",
      "expiration_time": 5,
      "time_unit": "days",
      "expiration_date": "2024-01-20T00:00:00Z",
      "added_at": "2024-01-15T10:00:00Z",
      "tips": "Mantener refrigerados para mayor duración",
      "image_path": "https://via.placeholder.com/150x150/f0f0f0/666666?text=Generando...",
      "image_status": "generating",
      "confidence": 0.95,
      "allergen_alert": false
    }
  ],
  "recognition_summary": {
    "total_ingredients_detected": 3,
    "confidence_average": 0.89,
    "processing_time_seconds": 2.3,
    "allergen_warnings": 0
  },
  "images": {
    "status": "generating",
    "task_id": "rec_img_abc123",
    "estimated_time": "10-15 segundos"
  }
}
```

### `POST /api/recognition/foods`
**Descripción**: Reconocimiento de alimentos/comidas preparadas  
**Autenticación**: Access Token requerido  
**Parámetros**: Similares a `/ingredients`

### `POST /api/recognition/batch`
**Descripción**: Procesamiento en lote de múltiples imágenes  
**Autenticación**: Access Token requerido

---

## 5. GESTIÓN DE INVENTARIO (`/api/inventory`)

### `GET /api/inventory`
**Descripción**: Obtener contenido completo del inventario del usuario  
**Autenticación**: Access Token requerido

**Query Parameters**:
- `filter` (opcional): `all`, `expiring`, `fresh`
- `sort` (opcional): `name`, `expiration`, `added_date`
- `limit` (opcional): Número máximo de elementos

**Response 200**:
```json
{
  "inventory_content": {
    "ingredients": [
      {
        "name": "Tomates cherry",
        "quantity": 500,
        "type_unit": "gr",
        "storage_type": "refrigerador",
        "expiration_date": "2024-01-20T00:00:00Z",
        "added_at": "2024-01-15T10:00:00Z",
        "days_until_expiration": 5,
        "status": "fresh",
        "tips": "Mantener refrigerados"
      }
    ],
    "foods": [
      {
        "name": "Ensalada preparada",
        "quantity": 2,
        "type_unit": "porciones",
        "expiration_date": "2024-01-17T00:00:00Z",
        "added_at": "2024-01-16T12:00:00Z",
        "days_until_expiration": 1,
        "status": "expiring_soon"
      }
    ]
  },
  "summary": {
    "total_ingredients": 15,
    "total_foods": 3,
    "expiring_soon": 4,
    "fresh_items": 14
  }
}
```

### `POST /api/inventory/ingredients`
**Descripción**: Agregar ingredientes manualmente al inventario  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "ingredients": [
    {
      "name": "Arroz integral",
      "quantity": 1000,
      "type_unit": "gr",
      "storage_type": "despensa",
      "expiration_time": 30,
      "time_unit": "days"
    }
  ]
}
```

### `GET /api/inventory/expiring`
**Descripción**: Obtener elementos próximos a vencer  
**Autenticación**: Access Token requerido

**Query Parameters**:
- `days` (opcional): Días de anticipación (default: 3)

### `PUT /api/inventory/ingredients/<ingredient_name>/<added_at>`
**Descripción**: Actualizar ingrediente específico  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "quantity": 750,
  "storage_type": "refrigerador",
  "expiration_time": 7,
  "time_unit": "days"
}
```

### `DELETE /api/inventory/ingredients/<ingredient_name>/<added_at>`
**Descripción**: Eliminar ingrediente del inventario  
**Autenticación**: Access Token requerido

### `POST /api/inventory/ingredients/<ingredient_name>/<added_at>/consume`
**Descripción**: Marcar ingrediente como consumido  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "quantity_consumed": 200,
  "consumption_date": "2024-01-16T18:00:00Z",
  "notes": "Usado para ensalada"
}
```

### `POST /api/inventory/ingredients/from-recognition`
**Descripción**: Agregar ingredientes desde reconocimiento IA  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "recognition_results": [
    {
      "name": "Tomates cherry",
      "quantity": 500,
      "type_unit": "gr",
      "confidence": 0.95,
      "auto_detected_storage": "refrigerador",
      "auto_detected_expiration": 5
    }
  ],
  "user_adjustments": {
    "apply_auto_storage": true,
    "apply_auto_expiration": true,
    "custom_notes": "Reconocido automáticamente"
  }
}
```

### `POST /api/inventory/upload_image`
**Descripción**: Subir imagen para reconocimiento automático  
**Autenticación**: Access Token requerido  
**Content-Type**: `multipart/form-data`

**Form Data**:
- `image`: Archivo de imagen (JPG, PNG, WEBP)
- `recognition_type`: `ingredients` | `foods`

### `POST /api/inventory/add_item`
**Descripción**: Agregar elemento único al inventario  
**Autenticación**: Access Token requerido

---

## 6. GENERACIÓN DE RECETAS (`/api/recipes`)

### `POST /api/recipes/generate-from-inventory`
**Descripción**: Generar recetas inteligentes basadas en inventario  
**Autenticación**: Access Token requerido

**Response 200**:
```json
{
  "generated_recipes": [
    {
      "name": "Ensalada de Tomates Cherry con Queso",
      "description": "Ensalada fresca aprovechando los tomates cherry del refrigerador",
      "ingredients": [
        {
          "name": "Tomates cherry",
          "quantity": 300,
          "unit": "gr",
          "available_in_inventory": true,
          "expiring_soon": true
        }
      ],
      "steps": [
        "Lavar y cortar los tomates cherry por la mitad",
        "Cortar el queso en cubos pequeños",
        "Mezclar tomates y queso en un bowl"
      ],
      "cooking_time_minutes": 10,
      "difficulty": "easy",
      "servings": 2,
      "calories_per_serving": 180,
      "image_path": null,
      "image_status": "generating",
      "uses_expiring_ingredients": true,
      "inventory_coverage": 0.85,
      "environmental_impact": {
        "co2_saved_kg": 0.5,
        "water_saved_liters": 12.3,
        "food_waste_reduced": true
      }
    }
  ],
  "generation_summary": {
    "total_recipes": 3,
    "recipes_using_expiring_items": 2,
    "inventory_utilization": 0.78,
    "environmental_benefits": {
      "total_co2_saved": 1.2,
      "total_water_saved": 34.5,
      "ingredients_saved_from_waste": 5
    }
  },
  "images": {
    "status": "generating",
    "task_id": "task_abc123def456",
    "check_images_url": "/api/generation/images/status/task_abc123def456",
    "estimated_time": "15-30 segundos"
  }
}
```

### `POST /api/recipes/generate-custom`
**Descripción**: Generar receta personalizada con ingredientes específicos  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "ingredients": [
    {"name": "Pollo", "quantity": 500, "unit": "gr"},
    {"name": "Pasta", "quantity": 300, "unit": "gr"},
    {"name": "Tomates", "quantity": 400, "unit": "gr"}
  ],
  "cuisine_type": "italiana",
  "difficulty": "intermedio",
  "prep_time": "medio",
  "dietary_restrictions": [],
  "meal_type": "almuerzo",
  "servings": 4
}
```

### `POST /api/recipes/save`
**Descripción**: Guardar receta en favoritos del usuario  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "recipe": {
    "name": "Pasta carbonara casera",
    "description": "Una deliciosa pasta italiana",
    "ingredients": [
      {"name": "Pasta", "quantity": 400, "unit": "gr"},
      {"name": "Huevos", "quantity": 4, "unit": "unidades"}
    ],
    "instructions": [
      {"step": 1, "description": "Cocinar la pasta al dente"}
    ],
    "prep_time": 30,
    "servings": 4,
    "difficulty": "intermedio"
  },
  "user_notes": "Receta favorita para domingos",
  "rating": 5,
  "custom_category": "Comidas familiares"
}
```

### `GET /api/recipes/saved`
**Descripción**: Obtener recetas guardadas del usuario  
**Autenticación**: Access Token requerido

**Query Parameters**:
- `category` (opcional): Filtrar por categoría
- `difficulty` (opcional): `fácil`, `intermedio`, `avanzado`
- `max_prep_time` (opcional): Tiempo máximo en minutos
- `min_rating` (opcional): Valoración mínima (1-5)
- `search` (opcional): Búsqueda de texto
- `sort_by` (opcional): `saved_date`, `rating`, `prep_time`, `name`
- `page` (opcional): Número de página
- `per_page` (opcional): Elementos por página

### `GET /api/recipes/all`
**Descripción**: Obtener todas las recetas del sistema  
**Autenticación**: Access Token requerido

### `DELETE /api/recipes/delete`
**Descripción**: Eliminar receta guardada del usuario  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "title": "Pasta carbonara casera"
}
```

### `GET /api/recipes/default`
**Descripción**: Obtener recetas por defecto del sistema  
**Autenticación**: No requerida

**Query Parameters**:
- `category` (opcional): `destacadas`, `rapidas_faciles`, `vegetarianas`, `postres`, `saludables`

---

## 7. PLANIFICACIÓN DE COMIDAS (`/api/planning`)

### `POST /api/planning/save`
**Descripción**: Guardar plan de comidas para una fecha específica  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "date": "2024-01-20",
  "meals": {
    "breakfast": {
      "name": "Avena con frutas",
      "description": "Desayuno nutritivo con avena y frutas frescas",
      "recipe_id": "recipe_123",
      "ingredients": ["Avena", "Plátano", "Miel", "Leche"],
      "prep_time_minutes": 10
    },
    "lunch": {
      "name": "Ensalada mediterránea",
      "description": "Ensalada fresca con vegetales",
      "ingredients": ["Lechuga", "Tomate", "Pepino"],
      "prep_time_minutes": 15
    },
    "dinner": {
      "name": "Pollo al horno",
      "description": "Pollo con especias y vegetales",
      "ingredients": ["Pollo", "Especias", "Vegetales"],
      "prep_time_minutes": 45
    },
    "snacks": [
      {
        "name": "Frutos secos",
        "description": "Mix de almendras y nueces",
        "prep_time_minutes": 0
      }
    ]
  }
}
```

### `PUT /api/planning/update`
**Descripción**: Actualizar plan de comidas existente  
**Autenticación**: Access Token requerido

### `DELETE /api/planning/delete`
**Descripción**: Eliminar plan de comidas  
**Autenticación**: Access Token requerido

### `GET /api/planning/by-date`
**Descripción**: Obtener plan de comidas por fecha específica  
**Autenticación**: Access Token requerido

**Query Parameters**:
- `date` (requerido): Fecha en formato YYYY-MM-DD

### `GET /api/planning/all`
**Descripción**: Obtener todos los planes de comidas del usuario  
**Autenticación**: Access Token requerido

### `GET /api/planning/dates`
**Descripción**: Obtener fechas con planes de comidas disponibles  
**Autenticación**: Access Token requerido

---

## 8. GENERACIÓN DE IMÁGENES (`/api/generation`)

### `GET /api/generation/images/status/<task_id>`
**Descripción**: Verificar estado de generación de imagen asíncrona  
**Autenticación**: Access Token requerido

**Response 200 (Completado)**:
```json
{
  "task_id": "img_gen_123456789",
  "status": "completed",
  "progress": 100,
  "estimated_remaining_time": 0,
  "started_at": "2024-01-16T10:30:00Z",
  "completed_at": "2024-01-16T10:32:45Z",
  "processing_time": 165,
  "result": {
    "image_url": "https://storage.googleapis.com/bucket/generated_images/img_gen_123456789.jpg",
    "image_path": "generated_images/img_gen_123456789.jpg",
    "generation_method": "ai_enhanced",
    "image_quality": "high",
    "dimensions": {"width": 1024, "height": 1024},
    "file_size": 245760,
    "format": "JPEG"
  }
}
```

**Response 202 (En Proceso)**:
```json
{
  "task_id": "img_gen_123456789",
  "status": "processing",
  "progress": 65,
  "estimated_remaining_time": 45,
  "started_at": "2024-01-16T10:30:00Z",
  "current_step": "ai_generation",
  "steps_completed": 2,
  "total_steps": 3,
  "message": "Generando imagen con IA, por favor espere..."
}
```

---

## 9. IMPACTO AMBIENTAL (`/api/environmental_savings`)

### `POST /api/environmental_savings/calculate/from-title`
**Descripción**: Calcular ahorro ambiental por título de receta  
**Autenticación**: Access Token requerido

**Request Body**:
```json
{
  "title": "Ensalada de Tomates Cherry con Queso Manchego"
}
```

**Response 200**:
```json
{
  "recipe_title": "Ensalada de Tomates Cherry con Queso Manchego",
  "environmental_impact": {
    "co2_reduction_kg": 0.85,
    "water_saved_liters": 23.4,
    "food_waste_reduced_kg": 0.5,
    "carbon_footprint_kg": 0.45,
    "sustainability_score": 8.2
  },
  "breakdown": {
    "ingredients_impact": [
      {
        "ingredient": "Tomates cherry",
        "co2_saved": 0.3,
        "water_saved": 12.1,
        "local_source": true,
        "impact_category": "low"
      }
    ],
    "comparison_vs_processed": {
      "co2_difference": 0.85,
      "water_difference": 23.4,
      "packaging_saved": true,
      "transport_reduced": 0.3
    }
  },
  "recommendations": [
    "Usar ingredientes locales cuando sea posible",
    "Aprovechar ingredientes próximos a vencer",
    "Compostar restos vegetales"
  ]
}
```

### `POST /api/environmental_savings/calculate/from-uid`
**Descripción**: Calcular ahorro ambiental por UID de receta  
**Autenticación**: Access Token requerido

### `GET /api/environmental_savings/user/all`
**Descripción**: Obtener todos los cálculos ambientales del usuario  
**Autenticación**: Access Token requerido

### `GET /api/environmental_savings/user/summary`
**Descripción**: Resumen de impacto ambiental del usuario  
**Autenticación**: Access Token requerido

---

## 10. GESTIÓN DE IMÁGENES (`/api/image_management`)

### `POST /api/image_management/upload`
**Descripción**: Subir imagen al sistema  
**Autenticación**: Access Token requerido

### `GET /api/image_management/search`
**Descripción**: Buscar imágenes similares  
**Autenticación**: Access Token requerido

### `POST /api/image_management/assign`
**Descripción**: Asignar imagen de referencia a elemento  
**Autenticación**: Access Token requerido

---

## 11. ADMINISTRACIÓN (`/api/admin`)

### Endpoints Administrativos
**Nota**: Requieren permisos de administrador

- `GET /api/admin/users` - Listar usuarios del sistema
- `GET /api/admin/stats` - Estadísticas del sistema
- `POST /api/admin/maintenance` - Tareas de mantenimiento
- `GET /api/admin/logs` - Logs del sistema

---

## Códigos de Estado HTTP

### Exitosos (2xx)
- **200 OK**: Operación exitosa
- **201 Created**: Recurso creado exitosamente
- **202 Accepted**: Operación aceptada (procesamiento asíncrono)

### Errores del Cliente (4xx)
- **400 Bad Request**: Datos de entrada inválidos
- **401 Unauthorized**: Token de autenticación inválido/expirado
- **403 Forbidden**: Sin permisos para el recurso
- **404 Not Found**: Recurso no encontrado
- **409 Conflict**: Conflicto con el estado actual del recurso
- **422 Unprocessable Entity**: Datos válidos pero no procesables
- **429 Too Many Requests**: Rate limit excedido

### Errores del Servidor (5xx)
- **500 Internal Server Error**: Error interno del servidor
- **502 Bad Gateway**: Error en servicios externos (Firebase, IA)
- **503 Service Unavailable**: Servicio temporalmente no disponible

---

## Autenticación y Seguridad

### Headers Requeridos
```
Authorization: Bearer <jwt_access_token>
Content-Type: application/json
```

### Flujo de Autenticación
1. **Login con Firebase**: `POST /api/auth/firebase-signin`
2. **Uso de Access Token**: Incluir en requests posteriores
3. **Renovación**: `POST /api/auth/refresh` cuando expire
4. **Logout**: `POST /api/auth/logout` para invalidar tokens

### Rate Limiting
- **Autenticación**: 5 requests/minuto
- **Refresh Token**: 10 requests/minuto  
- **API General**: 100 requests/minuto
- **Upload de Imágenes**: 20 requests/minuto

### Seguridad
- ✅ HTTPS en producción
- ✅ Headers de seguridad (CORS, CSP, HSTS)
- ✅ Validación de entrada
- ✅ Token blacklisting
- ✅ Rate limiting
- ✅ Logs de seguridad

---

## Formatos de Fecha y Hora

**Formato**: ISO 8601 UTC  
**Ejemplo**: `2024-01-15T10:30:00Z`

**Fechas simples**: `YYYY-MM-DD`  
**Ejemplo**: `2024-01-15`

---

## Límites del Sistema

### Uploads
- **Tamaño máximo por imagen**: 10MB
- **Formatos soportados**: JPG, PNG, WEBP, GIF
- **Máximo imágenes por request**: 5

### Datos
- **Máximo ingredientes por inventario**: 1000
- **Máximo recetas guardadas**: 500
- **Máximo planes de comidas**: 365 días

### Performance
- **Timeout de requests**: 30 segundos
- **Generación de imágenes**: 2-5 minutos
- **Reconocimiento IA**: 5-15 segundos

---

## Códigos de Error Personalizados

### Autenticación
- `AUTH_001`: Token expirado
- `AUTH_002`: Token inválido
- `AUTH_003`: Permisos insuficientes
- `AUTH_004`: Usuario no encontrado

### Inventario
- `INV_001`: Elemento no encontrado
- `INV_002`: Cantidad insuficiente
- `INV_003`: Elemento ya existe
- `INV_004`: Límite de inventario excedido

### Recetas
- `REC_001`: Receta no encontrada
- `REC_002`: Ingredientes insuficientes
- `REC_003`: Error en generación IA
- `REC_004`: Receta ya guardada

### Reconocimiento
- `REC_AI_001`: Imagen no válida
- `REC_AI_002`: Sin elementos reconocidos
- `REC_AI_003`: Confianza insuficiente
- `REC_AI_004`: Servicio IA no disponible

---

## Ejemplos de Uso Completo

### 1. Flujo de Usuario Nuevo
```bash
# 1. Obtener Firebase ID Token (en frontend)
# 2. Autenticarse con la API
curl -X POST https://api.zerowasteai.com/api/auth/firebase-signin \
  -H "Authorization: Bearer <firebase_id_token>"

# 3. Actualizar perfil
curl -X PUT https://api.zerowasteai.com/api/user/profile \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"language": "es", "cookingLevel": "intermediate"}'

# 4. Subir imagen para reconocimiento
curl -X POST https://api.zerowasteai.com/api/inventory/upload_image \
  -H "Authorization: Bearer <access_token>" \
  -F "image=@/path/to/image.jpg" \
  -F "recognition_type=ingredients"
```

### 2. Generación de Recetas desde Inventario
```bash
# 1. Verificar inventario
curl -X GET https://api.zerowasteai.com/api/inventory \
  -H "Authorization: Bearer <access_token>"

# 2. Generar recetas basadas en inventario
curl -X POST https://api.zerowasteai.com/api/recipes/generate-from-inventory \
  -H "Authorization: Bearer <access_token>"

# 3. Verificar estado de generación de imágenes
curl -X GET https://api.zerowasteai.com/api/generation/images/status/<task_id> \
  -H "Authorization: Bearer <access_token>"

# 4. Guardar receta favorita
curl -X POST https://api.zerowasteai.com/api/recipes/save \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"recipe": {...}, "rating": 5}'
```

---

## Soporte y Contacto

**Documentación Swagger**: `/apidocs`  
**Repositorio**: GitHub (privado)  
**Equipo**: ZeroWasteAI Development Team  
**Misión**: Reducir el desperdicio alimentario a través de tecnología IA  

---

*Documentación generada automáticamente - Versión 1.0.0*  
*Última actualización: Enero 2024*