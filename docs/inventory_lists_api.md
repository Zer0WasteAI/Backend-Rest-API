# 📋 API de Listas Específicas del Inventario

Esta documentación describe los endpoints para obtener listas específicas **solo de ingredientes** o **solo de food items** del inventario del usuario.

## 🎯 Resumen

Los nuevos endpoints proporcionan acceso directo a tipos específicos de items:
- **Lista solo de ingredientes** - Sin food items, con información detallada de todos los stacks
- **Lista solo de food items** - Sin ingredientes, con información nutricional y estadísticas

## 🔧 Endpoints

### 1. Obtener Lista de Ingredientes

**GET** `/api/inventory/ingredients/list`

Obtiene **únicamente** los ingredientes del inventario del usuario, sin food items.

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
```

#### **Response Exitoso (200):**
```json
{
  "ingredients": [
    {
      "name": "Tomate",
      "type_unit": "g",
      "storage_type": "Refrigerador",
      "tips": "Mantener en refrigerador para mayor duración",
      "image_path": "https://storage.googleapis.com/bucket/tomate.jpg",
      "stacks": [
        {
          "quantity": 500.0,
          "type_unit": "g",
          "expiration_date": "2025-01-15T12:00:00Z",
          "added_at": "2025-01-01T10:00:00Z",
          "days_to_expire": 14,
          "is_expired": false
        },
        {
          "quantity": 300.0,
          "type_unit": "g",
          "expiration_date": "2025-01-20T12:00:00Z",
          "added_at": "2025-01-05T14:00:00Z",
          "days_to_expire": 19,
          "is_expired": false
        }
      ],
      "total_quantity": 800.0,
      "stack_count": 2,
      "nearest_expiration": "2025-01-15T12:00:00Z",
      "average_quantity_per_stack": 400.0
    },
    {
      "name": "Cebolla",
      "type_unit": "unidad",
      "storage_type": "Bodega",
      "tips": "Almacenar en lugar seco y ventilado",
      "image_path": "https://storage.googleapis.com/bucket/cebolla.jpg",
      "stacks": [
        {
          "quantity": 3.0,
          "type_unit": "unidad",
          "expiration_date": "2025-02-01T12:00:00Z",
          "added_at": "2025-01-02T08:00:00Z",
          "days_to_expire": 31,
          "is_expired": false
        }
      ],
      "total_quantity": 3.0,
      "stack_count": 1,
      "nearest_expiration": "2025-02-01T12:00:00Z",
      "average_quantity_per_stack": 3.0
    }
  ],
  "total_ingredients": 2,
  "total_stacks": 3,
  "summary": {
    "ingredient_types": 2,
    "total_stacks": 3,
    "average_stacks_per_ingredient": 1.5
  }
}
```

#### **Response Sin Datos (200):**
```json
{
  "ingredients": [],
  "total_ingredients": 0,
  "total_stacks": 0,
  "message": "No inventory found"
}
```

---

### 2. Obtener Lista de Food Items

**GET** `/api/inventory/foods/list`

Obtiene **únicamente** los food items del inventario del usuario, sin ingredientes.

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
```

#### **Response Exitoso (200):**
```json
{
  "foods": [
    {
      "name": "Pasta con Tomate",
      "category": "Plato Principal",
      "serving_quantity": 2,
      "calories": 450,
      "description": "Pasta italiana con salsa de tomate fresco y albahaca",
      "storage_type": "Refrigerador",
      "tips": "Recalentar en microondas por 2 minutos antes de servir",
      "image_path": "https://storage.googleapis.com/bucket/pasta.jpg",
      
      "added_at": "2025-01-01T12:00:00Z",
      "expiration_date": "2025-01-03T12:00:00Z",
      "expiration_time": 2,
      "time_unit": "Días",
      "days_to_expire": 2,
      "is_expired": false,
      
      "main_ingredients": ["Pasta", "Tomate", "Albahaca", "Aceite de oliva"],
      
      "calories_per_serving": 225,
      "total_calories": 450,
      "status": "fresh"
    },
    {
      "name": "Ensalada Caesar",
      "category": "Ensalada",
      "serving_quantity": 1,
      "calories": 320,
      "description": "Ensalada caesar con pollo y aderezo casero",
      "storage_type": "Refrigerador",
      "tips": "Consumir el mismo día para mejor frescura",
      "image_path": "https://storage.googleapis.com/bucket/caesar.jpg",
      
      "added_at": "2025-01-01T18:00:00Z",
      "expiration_date": "2025-01-02T18:00:00Z",
      "expiration_time": 1,
      "time_unit": "Días",
      "days_to_expire": 1,
      "is_expired": false,
      
      "main_ingredients": ["Lechuga", "Pollo", "Queso parmesano", "Aderezo caesar"],
      
      "calories_per_serving": 320,
      "total_calories": 320,
      "status": "expiring_soon"
    }
  ],
  "total_foods": 2,
  "total_servings": 3,
  "total_calories": 770,
  "summary": {
    "food_items": 2,
    "total_servings": 3,
    "total_calories": 770,
    "average_calories_per_food": 385,
    "average_servings_per_food": 1.5,
    "categories": {
      "Plato Principal": {
        "count": 1,
        "total_servings": 2,
        "total_calories": 450
      },
      "Ensalada": {
        "count": 1,
        "total_servings": 1,
        "total_calories": 320
      }
    }
  }
}
```

#### **Response Sin Datos (200):**
```json
{
  "foods": [],
  "total_foods": 0,
  "total_servings": 0,
  "total_calories": 0,
  "message": "No food items found"
}
```

---

## 🌟 **Características de las Listas**

### **🥬 Lista de Ingredientes:**
- **Ordenada alfabéticamente** por nombre
- **Todos los stacks** de cada ingrediente con fechas de vencimiento
- **Estadísticas calculadas**: cantidad total, promedio por stack, próximo vencimiento
- **Información básica**: almacenamiento, consejos, imagen

### **🍽️ Lista de Food Items:**
- **Ordenada por vencimiento** (más próximos primero)
- **Estadísticas nutricionales**: calorías totales, por porción
- **Categorización automática** con resumen por categorías
- **Estado del item**: fresh, expiring_soon, expired

---

## 📊 **Datos Incluidos**

### **Para cada Ingrediente:**
```json
{
  "name": "string",
  "type_unit": "string",
  "storage_type": "string", 
  "tips": "string",
  "image_path": "string",
  "stacks": [{ /* detalles de cada stack */ }],
  "total_quantity": "number",
  "stack_count": "number",
  "nearest_expiration": "ISO date",
  "average_quantity_per_stack": "number"
}
```

### **Para cada Food Item:**
```json
{
  "name": "string",
  "category": "string",
  "serving_quantity": "number",
  "calories": "number",
  "description": "string",
  "storage_type": "string",
  "tips": "string",
  "image_path": "string",
  "main_ingredients": ["array"],
  "calories_per_serving": "number", 
  "total_calories": "number",
  "status": "fresh|expiring_soon|expired",
  "days_to_expire": "number",
  "is_expired": "boolean"
}
```

---

## 📝 **Ejemplos de Uso**

### **JavaScript/React:**

```javascript
// Obtener solo ingredientes
const getIngredientsList = async () => {
  try {
    const response = await fetch('/api/inventory/ingredients/list', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${userToken}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log(`📋 Found ${data.total_ingredients} ingredients`);
      console.log(`📊 Total stacks: ${data.total_stacks}`);
      
      // Procesar ingredientes
      data.ingredients.forEach(ingredient => {
        console.log(`🥬 ${ingredient.name}: ${ingredient.total_quantity} ${ingredient.type_unit}`);
        console.log(`   Stacks: ${ingredient.stack_count}`);
        console.log(`   Next expiration: ${ingredient.nearest_expiration}`);
      });
      
      return data;
    }
  } catch (error) {
    console.error('❌ Error fetching ingredients:', error);
  }
};

// Obtener solo food items
const getFoodsList = async () => {
  try {
    const response = await fetch('/api/inventory/foods/list', {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${userToken}`
      }
    });
    
    if (response.ok) {
      const data = await response.json();
      console.log(`🍽️ Found ${data.total_foods} food items`);
      console.log(`🍴 Total servings: ${data.total_servings}`);
      console.log(`🔥 Total calories: ${data.total_calories}`);
      
      // Procesar food items
      data.foods.forEach(food => {
        console.log(`🍽️ ${food.name} (${food.category})`);
        console.log(`   Servings: ${food.serving_quantity}`);
        console.log(`   Status: ${food.status}`);
        console.log(`   Days to expire: ${food.days_to_expire}`);
      });
      
      // Procesar categorías
      Object.entries(data.summary.categories).forEach(([category, stats]) => {
        console.log(`📂 ${category}: ${stats.count} items, ${stats.total_calories} calories`);
      });
      
      return data;
    }
  } catch (error) {
    console.error('❌ Error fetching foods:', error);
  }
};
```

### **cURL Examples:**

```bash
# Obtener lista de ingredientes
curl -X GET \
  "http://localhost:3000/api/inventory/ingredients/list" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Obtener lista de food items
curl -X GET \
  "http://localhost:3000/api/inventory/foods/list" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔐 **Autenticación y Seguridad**

- **JWT requerido**: Todos los endpoints requieren token válido
- **Aislamiento por usuario**: Solo acceso a items del inventario del usuario autenticado
- **Filtrado automático**: Cada endpoint devuelve solo el tipo solicitado

## 💡 **Casos de Uso en Frontend**

### **Páginas Especializadas:**
- **Página solo de ingredientes** - Gestión de ingredientes sin distracciones
- **Página solo de comidas** - Planificación de comidas preparadas
- **Dashboards separados** - Métricas específicas por tipo

### **Componentes UI:**
- **Lista de ingredientes disponibles** para cocinar
- **Menú de comidas preparadas** para consumir
- **Filtros y búsquedas** específicas por tipo

### **Optimización:**
- **Carga selectiva** - Solo cargar el tipo que necesitas
- **Menor transferencia de datos** - No mezclar tipos innecesariamente
- **Renderizado optimizado** - Componentes específicos para cada tipo 