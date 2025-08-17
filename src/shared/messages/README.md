# 🎨 Sistema de Mensajes Bonitos y Contextuales

Este sistema proporciona mensajes bonitos, contextuales y consistentes para toda la API de ZeroWasteAI. Los mensajes están diseñados para mejorar la experiencia del usuario y facilitar la integración con el frontend.

## 📋 Características

- ✨ **Mensajes bonitos con emojis** para mejor UX
- 🎯 **Contextuales por servicio** (autenticación, recetas, inventario, etc.)
- 📊 **Respuestas estandarizadas** con formato consistente
- 🚫 **Manejo automático de errores** con decorators
- 🌐 **Multiidioma ready** (actualmente en español)
- ⏰ **Timestamps automáticos** en todas las respuestas

## 🛠️ Uso Básico

### 1. Con Decorators (Recomendado)

```python
from src.shared.decorators.response_handler import api_response
from src.shared.messages.response_messages import ServiceType

@api_response(service=ServiceType.RECIPES, action="generated")
def generate_recipe():
    # Tu lógica aquí
    result = recipe_service.generate()
    return result, 201  # El decorator se encarga del mensaje bonito
```

**Respuesta automática:**
```json
{
    "success": true,
    "message": "✨ ¡Receta generada con éxito! Tu nueva creación culinaria está lista",
    "service": "recipes",
    "action": "generated",
    "timestamp": "2024-01-15T10:30:00Z",
    "data": { /* datos de la receta */ }
}
```

### 2. Con ResponseHelper (Manual)

```python
from src.shared.decorators.response_handler import ResponseHelper
from src.shared.messages.response_messages import ServiceType

def upload_image():
    try:
        # Tu lógica aquí
        result = upload_service.upload(file)
        return ResponseHelper.success_response(
            service=ServiceType.IMAGES,
            action="uploaded",
            data=result
        )
    except Exception as e:
        return ResponseHelper.error_response(
            service=ServiceType.IMAGES,
            action="upload_failed",
            error=str(e)
        )
```

## 🎭 Tipos de Servicios Disponibles

```python
class ServiceType(Enum):
    AUTH = "authentication"          # 🔐 Autenticación
    RECIPES = "recipes"              # 🍳 Gestión de recetas
    INVENTORY = "inventory"          # 📦 Gestión de inventario
    COOKING = "cooking_session"      # 👨‍🍳 Sesiones de cocina
    RECOGNITION = "recognition"      # 🤖 Reconocimiento IA
    IMAGES = "image_management"      # 📸 Gestión de imágenes
    PLANNING = "meal_planning"       # 📅 Planificación de comidas
    ENVIRONMENTAL = "environmental_savings"  # 🌱 Impacto ambiental
    USER = "user_profile"            # 👤 Perfil de usuario
    ADMIN = "admin"                  # 🛡️ Administración
```

## 💬 Ejemplos de Mensajes por Servicio

### 🔐 Autenticación
```json
{
    "success": true,
    "message": "¡Bienvenido de vuelta! 🎉 Has iniciado sesión exitosamente",
    "service": "authentication",
    "action": "login"
}
```

### 🍳 Recetas
```json
{
    "success": true,
    "message": "❤️ Receta añadida a tus favoritas. ¡Excelente elección!",
    "service": "recipes",
    "action": "favorite_added"
}
```

### 📦 Inventario
```json
{
    "success": true,
    "message": "✅ ¡Genial! Ingrediente agregado a tu inventario inteligente",
    "service": "inventory",
    "action": "item_added"
}
```

### ❌ Errores
```json
{
    "success": false,
    "message": "🔍 No encontramos esa receta. ¿Estás seguro que existe?",
    "service": "recipes",
    "action": "find",
    "error_type": "not_found"
}
```

## 🔧 Configuración en Controladores

### Paso 1: Importar dependencias
```python
from src.shared.decorators.response_handler import api_response, ResponseHelper
from src.shared.messages.response_messages import ServiceType
```

### Paso 2: Aplicar decorator
```python
@your_route_decorator
@api_response(service=ServiceType.INVENTORY, action="item_updated")
def update_item():
    # Tu lógica
    return data, 200  # Automáticamente se convierte en mensaje bonito
```

### Paso 3: Manejo de errores automático
```python
# Los siguientes errores se manejan automáticamente:
# - InvalidRequestDataException → Mensaje de datos inválidos
# - RecipeNotFoundException → Mensaje de recurso no encontrado  
# - InvalidTokenException → Mensaje de token inválido
# - PermissionError → Mensaje de permisos
# - ValueError → Mensaje de valor inválido
# - Exception → Mensaje genérico de error interno
```

## 📱 Integración con Frontend

### Estructura de Respuesta Estándar
```javascript
{
    success: boolean,           // true/false para el estado
    message: string,            // Mensaje bonito para mostrar al usuario
    service: string,            // Servicio que generó la respuesta
    action: string,             // Acción específica realizada
    timestamp: string,          // ISO timestamp
    data?: any,                 // Datos de respuesta (solo en éxito)
    error_details?: string,     // Detalles del error (solo en errores)
    error_type?: string         // Tipo específico de error
}
```

### Ejemplo de uso en React
```javascript
// Mostrar el mensaje automáticamente
const response = await api.post('/api/recipes/generate', data);
if (response.data.success) {
    toast.success(response.data.message); // "✨ ¡Receta generada con éxito!"
    setRecipe(response.data.data);
} else {
    toast.error(response.data.message);   // Error contextual bonito
}
```

### Ejemplo de uso en Vue.js
```javascript
// El mensaje viene listo para mostrar
try {
    const { data } = await this.$api.inventory.addItem(item);
    this.$toast.success(data.message); // "✅ ¡Genial! Ingrediente agregado..."
    this.refreshInventory();
} catch (error) {
    // Incluso los errores tienen mensajes bonitos
    this.$toast.error(error.response.data.message);
}
```

## 🎨 Personalización de Mensajes

### Mensaje personalizado con decorator
```python
@api_response(service=ServiceType.RECIPES, action="custom")
def special_endpoint():
    result = do_something()
    # Para usar mensaje personalizado, usa ResponseHelper dentro de la función
    return ResponseHelper.success_response(
        service=ServiceType.RECIPES,
        action="custom",
        data=result,
        message="🎉 ¡Operación especial completada con éxito!"
    )
```

### Agregar nuevos mensajes
```python
# En response_messages.py, agregar al diccionario correspondiente:
RECIPES_MESSAGES = {
    "success": {
        "new_action": "🆕 ¡Nueva acción completada exitosamente!",
        # ... otros mensajes
    }
}
```

## 🧪 Testing

```python
def test_endpoint_with_beautiful_messages():
    response = client.post('/api/inventory/add_item', json=data)
    
    assert response.status_code == 200
    assert response.json['success'] is True
    assert "✅" in response.json['message']  # Verifica que tiene emoji
    assert response.json['service'] == 'inventory'
    assert response.json['action'] == 'item_added'
    assert 'timestamp' in response.json
```

## 🔄 Migración de Endpoints Existentes

### Antes (sin sistema de mensajes)
```python
@app.route('/api/recipes', methods=['POST'])
def create_recipe():
    try:
        recipe = service.create(request.json)
        return jsonify({"message": "Recipe created", "recipe": recipe}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400
```

### Después (con mensajes bonitos)
```python
@app.route('/api/recipes', methods=['POST'])
@api_response(service=ServiceType.RECIPES, action="generated")
def create_recipe():
    recipe = service.create(request.json)  # Errores manejados automáticamente
    return recipe, 201  # Mensaje bonito automático
```

¡El resultado es mucho más limpio y consistente! 🎉