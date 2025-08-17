# 🎨 Ejemplos de Respuestas con Mensajes Bonitos

## ✅ Respuestas de Éxito

### 🔐 Autenticación Exitosa
```json
{
    "success": true,
    "message": "¡Bienvenido de vuelta! 🎉 Has iniciado sesión exitosamente",
    "service": "authentication",
    "action": "login",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": {
        "user": {
            "uid": "user123",
            "email": "usuario@ejemplo.com",
            "name": "Juan Pérez"
        },
        "tokens": {
            "access_token": "eyJ0eXAiOiJKV1Q...",
            "refresh_token": "eyJ0eXAiOiJKV1Q...",
            "expires_in": 3600
        }
    }
}
```

### 🍳 Receta Generada
```json
{
    "success": true,
    "message": "✨ ¡Receta generada con éxito! Tu nueva creación culinaria está lista",
    "service": "recipes",
    "action": "generated",
    "timestamp": "2024-01-15T10:35:00Z",
    "data": {
        "recipe": {
            "uid": "recipe_789",
            "title": "Pasta con Pollo y Verduras",
            "instructions": ["Paso 1...", "Paso 2..."],
            "ingredients": [{"name": "pollo", "quantity": 200}],
            "prep_time": 30,
            "cook_time": 20
        }
    }
}
```

### 📦 Item Agregado al Inventario
```json
{
    "success": true,
    "message": "✅ ¡Genial! Ingrediente agregado a tu inventario inteligente",
    "service": "inventory",
    "action": "item_added",
    "timestamp": "2024-01-15T10:40:00Z",
    "data": {
        "item": {
            "name": "Tomates",
            "quantity": 5,
            "unit": "pieces",
            "storage_type": "refrigerated",
            "expiration_date": "2024-01-25",
            "ai_generated_tips": ["Conservar en refrigerador", "Usar en 10 días"]
        }
    }
}
```

### 📸 Imagen Subida
```json
{
    "success": true,
    "message": "📸 ¡Imagen subida exitosamente! Ya está disponible en tu galería",
    "service": "image_management",
    "action": "uploaded",
    "timestamp": "2024-01-15T10:45:00Z",
    "data": {
        "image": {
            "uid": "img_456",
            "name": "tomate_fresco",
            "image_path": "https://storage.googleapis.com/...",
            "image_type": "ingredient"
        }
    }
}
```

### 👨‍🍳 Sesión de Cocina Iniciada
```json
{
    "success": true,
    "message": "🔥 ¡Sesión de cocina iniciada! Que disfrutes cocinando",
    "service": "cooking_session",
    "action": "session_started",
    "timestamp": "2024-01-15T11:00:00Z",
    "data": {
        "session_id": "cook_9a1f",
        "status": "running",
        "recipe_title": "Pasta con Pollo",
        "estimated_time": 50
    }
}
```

### 📅 Plan de Comidas Guardado
```json
{
    "success": true,
    "message": "📅 ¡Plan de comidas guardado! Tu semana está organizada",
    "service": "meal_planning",
    "action": "plan_saved",
    "timestamp": "2024-01-15T11:05:00Z",
    "data": {
        "plan": {
            "date": "2024-01-16",
            "meals": {
                "breakfast": "Avena con frutas",
                "lunch": "Pasta con pollo",
                "dinner": "Ensalada césar"
            }
        }
    }
}
```

### 🌱 Impacto Ambiental Calculado
```json
{
    "success": true,
    "message": "🌱 ¡Impacto ambiental calculado! Estás ayudando al planeta",
    "service": "environmental_savings",
    "action": "savings_calculated",
    "timestamp": "2024-01-15T11:10:00Z",
    "data": {
        "savings": {
            "co2_saved": 0.45,
            "water_saved": 15.2,
            "waste_reduced": 0.08
        }
    }
}
```

## ❌ Respuestas de Error

### 🚫 No Autorizado
```json
{
    "success": false,
    "message": "🚫 No tienes autorización para acceder a este recurso",
    "service": "authentication",
    "action": "access",
    "error_type": "unauthorized",
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### 🔍 Recurso No Encontrado
```json
{
    "success": false,
    "message": "🔍 No encontramos esa receta. ¿Estás seguro que existe?",
    "service": "recipes",
    "action": "find",
    "resource": "recipe",
    "error_type": "not_found",
    "timestamp": "2024-01-15T10:35:00Z"
}
```

### 📝 Datos Inválidos
```json
{
    "success": false,
    "message": "📝 Datos inválidos: El nombre del item es requerido",
    "service": "inventory",
    "action": "item_added",
    "error_details": "El nombre del item es requerido",
    "timestamp": "2024-01-15T10:40:00Z"
}
```

### 📷 Error en Imagen
```json
{
    "success": false,
    "message": "📁 Formato de imagen no válido. Usa JPG, PNG o WebP",
    "service": "image_management",
    "action": "upload_failed",
    "error_details": "Unsupported file format: .gif",
    "timestamp": "2024-01-15T10:45:00Z"
}
```

### ⚠️ Cantidad Insuficiente
```json
{
    "success": false,
    "message": "⚠️ Cantidad insuficiente para esta operación",
    "service": "inventory",
    "action": "item_consumed",
    "error_details": "Requested: 10 units, Available: 3 units",
    "timestamp": "2024-01-15T11:00:00Z"
}
```

### 🤖 Error de IA
```json
{
    "success": false,
    "message": "🤔 No detectamos alimentos en esta imagen",
    "service": "recognition",
    "action": "image_processed",
    "error_details": "No food items detected in image analysis",
    "timestamp": "2024-01-15T11:05:00Z"
}
```

### ⏰ Token Expirado
```json
{
    "success": false,
    "message": "⏰ Tu sesión ha expirado. Por favor, inicia sesión nuevamente",
    "service": "authentication",
    "action": "token_refresh",
    "error_type": "token_expired",
    "timestamp": "2024-01-15T11:10:00Z"
}
```

### 😞 Error Interno
```json
{
    "success": false,
    "message": "😞 Algo salió mal. Nuestro equipo ha sido notificado",
    "service": "recipes",
    "action": "generation_failed",
    "error_details": "Error interno del servidor",
    "timestamp": "2024-01-15T11:15:00Z"
}
```

## 🎯 Casos Especiales

### 💡 Advertencia - Ya Existe
```json
{
    "success": false,
    "message": "💡 Esta receta ya está en tus favoritas",
    "service": "recipes",
    "action": "favorite_added",
    "error_details": "Recipe already in favorites",
    "timestamp": "2024-01-15T11:20:00Z"
}
```

### 📊 Información de Estado
```json
{
    "success": true,
    "message": "⏰ Lista de productos próximos a vencer obtenida",
    "service": "inventory",
    "action": "expiring_retrieved",
    "timestamp": "2024-01-15T11:25:00Z",
    "data": {
        "expiring_items": [
            {
                "name": "Leche",
                "expires_in_days": 2,
                "quantity": "1 litro"
            },
            {
                "name": "Pan",
                "expires_in_days": 1,
                "quantity": "1 unidad"
            }
        ]
    }
}
```

## 🔧 Cómo Integrar en Frontend

### React Example
```javascript
// Componente de ejemplo para mostrar respuestas
const ApiResponseHandler = ({ response }) => {
    const getIcon = (success) => success ? "✅" : "❌";
    const getColor = (success) => success ? "green" : "red";
    
    return (
        <div style={{color: getColor(response.success)}}>
            {getIcon(response.success)} {response.message}
            {response.data && (
                <pre>{JSON.stringify(response.data, null, 2)}</pre>
            )}
        </div>
    );
};

// Uso en llamadas a la API
const uploadImage = async (file) => {
    try {
        const response = await api.post('/api/image_management/upload_image', file);
        toast.success(response.data.message); // "📸 ¡Imagen subida exitosamente!"
        return response.data.data;
    } catch (error) {
        toast.error(error.response.data.message); // Error contextual bonito
        throw error;
    }
};
```

### Vue.js Example
```javascript
// Plugin para manejo global de respuestas
Vue.prototype.$handleApiResponse = function(response) {
    if (response.data.success) {
        this.$toast.success(response.data.message);
        return response.data.data;
    } else {
        this.$toast.error(response.data.message);
        throw new Error(response.data.message);
    }
};

// Uso en componente
methods: {
    async addItemToInventory(item) {
        try {
            const response = await this.$api.post('/api/inventory/add_item', item);
            const data = this.$handleApiResponse(response);
            this.refreshInventory();
            return data;
        } catch (error) {
            // Error ya mostrado por $handleApiResponse
            console.error('Error adding item:', error);
        }
    }
}
```

¡Ahora tu API tiene mensajes hermosos y contextuales que harán que la experiencia de usuario sea mucho mejor! 🎉