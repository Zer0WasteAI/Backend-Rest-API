# 🍽️ API para Marcar Items como Consumidos

Esta documentación describe los endpoints para marcar ingredientes y comidas como consumidos en el inventario. Permite un tracking preciso del consumo con opciones de consumo parcial o total.

## 🎯 Funcionalidades

- **Marcar ingredientes como consumidos por stack** (consumo parcial o total)
- **Marcar comidas como consumidas** (consumo parcial o total)
- **Tracking automático** de fechas y cantidades consumidas
- **Validación inteligente** de cantidades disponibles
- **Respuestas detalladas** con información nutricional y de consumo

## 🔧 Endpoints

### 1. Marcar Stack de Ingrediente como Consumido

**POST** `/api/inventory/ingredients/{ingredient_name}/{added_at}/consume`

Marca un stack específico de ingrediente como consumido. Permite consumo parcial o total.

#### **Parámetros URL:**
- `ingredient_name`: Nombre del ingrediente (string)
- `added_at`: Timestamp del stack (ISO format, ej: `2025-01-01T10:00:00Z`)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

#### **Body (Opcional):**
```json
{
  "consumed_quantity": 2.5
}
```

**Campos del Body:**
- `consumed_quantity` (float, opcional): Cantidad a consumir. Si se omite, consume todo el stack.

#### **Response Exitoso - Consumo Total (200):**
```json
{
  "message": "Ingredient stack marked as consumed",
  "action": "full_consumption",
  "ingredient": "Tomate",
  "consumed_quantity": 3.0,
  "unit": "kg",
  "stack_removed": true,
  "consumed_at": "2025-01-15T14:30:00Z",
  "original_added_at": "2025-01-01T10:00:00Z"
}
```

#### **Response Exitoso - Consumo Parcial (200):**
```json
{
  "message": "Ingredient partially consumed",
  "action": "partial_consumption",
  "ingredient": "Tomate",
  "consumed_quantity": 1.5,
  "remaining_quantity": 1.5,
  "unit": "kg",
  "stack_removed": false,
  "consumed_at": "2025-01-15T14:30:00Z",
  "original_added_at": "2025-01-01T10:00:00Z"
}
```

#### **Response Error (404):**
```json
{
  "error": "Ingredient stack 'Tomate' not found (added at: 2025-01-01T10:00:00Z)"
}
```

#### **Response Error (400):**
```json
{
  "error": "Cannot consume 5.0 kg - only 3.0 kg available"
}
```

---

### 2. Marcar Food Item como Consumido

**POST** `/api/inventory/foods/{food_name}/{added_at}/consume`

Marca un food item como consumido. Permite consumo parcial o total.

#### **Parámetros URL:**
- `food_name`: Nombre de la comida (string)
- `added_at`: Timestamp del food item (ISO format)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

#### **Body (Opcional):**
```json
{
  "consumed_portions": 1.5
}
```

**Campos del Body:**
- `consumed_portions` (float, opcional): Porciones a consumir. Si se omite, consume todo el food item.

#### **Response Exitoso - Consumo Total (200):**
```json
{
  "message": "Food item marked as consumed",
  "action": "full_consumption",
  "food": "Pasta con Tomate",
  "consumed_portions": 2.0,
  "food_removed": true,
  "consumed_at": "2025-01-15T14:30:00Z",
  "original_added_at": "2025-01-01T12:00:00Z",
  "food_details": {
    "category": "principal",
    "main_ingredients": ["pasta", "tomate", "ajo"],
    "calories": 350,
    "description": "Deliciosa pasta con salsa de tomate casera"
  }
}
```

#### **Response Exitoso - Consumo Parcial (200):**
```json
{
  "message": "Food item partially consumed",
  "action": "partial_consumption",
  "food": "Pasta con Tomate",
  "consumed_portions": 1.0,
  "remaining_portions": 1.0,
  "food_removed": false,
  "consumed_at": "2025-01-15T14:30:00Z",
  "original_added_at": "2025-01-01T12:00:00Z",
  "food_details": {
    "category": "principal",
    "main_ingredients": ["pasta", "tomate", "ajo"],
    "calories": 350,
    "description": "Deliciosa pasta con salsa de tomate casera"
  }
}
```

#### **Response Error (404):**
```json
{
  "error": "Food item 'Pasta con Tomate' not found (added at: 2025-01-01T12:00:00Z)"
}
```

## 🔍 Casos de Uso

### **Escenario 1: Consumir Stack Completo de Ingrediente**
```bash
# Consumir todo un stack de tomates
curl -X POST \
  http://localhost:3000/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
  # Sin body = consume todo
```

### **Escenario 2: Consumir Parcialmente un Stack**
```bash
# Consumir solo 1.5 kg de un stack de 3 kg de tomates
curl -X POST \
  http://localhost:3000/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/consume \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consumed_quantity": 1.5
  }'
```

### **Escenario 3: Consumir Comida Completa**
```bash
# Consumir toda una comida
curl -X POST \
  http://localhost:3000/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T12:00:00Z/consume \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json"
  # Sin body = consume todo
```

### **Escenario 4: Consumir Parcialmente una Comida**
```bash
# Consumir 1.5 porciones de 2 porciones disponibles
curl -X POST \
  http://localhost:3000/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T12:00:00Z/consume \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "consumed_portions": 1.5
  }'
```

## 🧑‍💻 Integración Frontend

### **Marcar Ingrediente como Consumido**
```javascript
const markIngredientConsumed = async (ingredientName, addedAt, consumedQuantity = null) => {
  try {
    const body = consumedQuantity ? { consumed_quantity: consumedQuantity } : {};
    
    const response = await fetch(
      `/api/inventory/ingredients/${encodeURIComponent(ingredientName)}/${addedAt}/consume`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      
      if (data.action === 'full_consumption') {
        console.log(`✅ ${data.ingredient} stack completely consumed`);
        // Remover del UI
      } else {
        console.log(`✅ ${data.ingredient}: ${data.consumed_quantity} consumed, ${data.remaining_quantity} remaining`);
        // Actualizar cantidad en UI
      }
      
      return data;
    } else {
      throw new Error('Failed to mark ingredient as consumed');
    }
  } catch (error) {
    console.error('❌ Error marking ingredient as consumed:', error);
    throw error;
  }
};

// Uso
markIngredientConsumed('Tomate', '2025-01-01T10:00:00Z', 1.5);
```

### **Marcar Comida como Consumida**
```javascript
const markFoodConsumed = async (foodName, addedAt, consumedPortions = null) => {
  try {
    const body = consumedPortions ? { consumed_portions: consumedPortions } : {};
    
    const response = await fetch(
      `/api/inventory/foods/${encodeURIComponent(foodName)}/${addedAt}/consume`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      
      if (data.action === 'full_consumption') {
        console.log(`✅ ${data.food} completely consumed`);
        // Remover del UI
        
        // Mostrar información nutricional
        if (data.food_details) {
          console.log(`Calories consumed: ${data.food_details.calories * data.consumed_portions}`);
        }
      } else {
        console.log(`✅ ${data.food}: ${data.consumed_portions} portions consumed, ${data.remaining_portions} remaining`);
        // Actualizar cantidad en UI
      }
      
      return data;
    } else {
      throw new Error('Failed to mark food as consumed');
    }
  } catch (error) {
    console.error('❌ Error marking food as consumed:', error);
    throw error;
  }
};

// Uso
markFoodConsumed('Pasta con Tomate', '2025-01-01T12:00:00Z', 1.0);
```

## 📊 Beneficios del Sistema

### **Para Ingredientes:**
- ✅ **Tracking preciso por lotes**: Cada stack se identifica por fecha de adición
- ✅ **Consumo parcial**: No es necesario consumir todo el stack
- ✅ **Gestión automática**: Si es el último stack, elimina el ingrediente completo
- ✅ **Validación inteligente**: Previene consumir más de lo disponible

### **Para Comidas:**
- ✅ **Control de porciones**: Maneja porciones fraccionales
- ✅ **Información nutricional**: Retorna detalles de la comida consumida
- ✅ **Flexibilidad**: Permite consumo parcial de comidas preparadas
- ✅ **Tracking completo**: Registra qué, cuándo y cuánto se consumió

## 🔒 Seguridad

- 🔐 **Autenticación JWT obligatoria**
- 👤 **Aislamiento por usuario**: Solo puede consumir items de su propio inventario
- ✅ **Validación de datos**: Cantidades y porciones validadas automáticamente
- 🚫 **Prevención de errores**: No permite consumir más de lo disponible

## 🎯 Notas de Implementación

1. **Timestamps**: Usar formato ISO 8601 (ej: `2025-01-01T10:00:00Z`)
2. **URL Encoding**: Los nombres con espacios deben estar encoded (ej: `Pasta%20con%20Tomate`)
3. **Cantidades decimales**: Se permiten cantidades fraccionales (ej: `1.5`)
4. **Consumo total**: Si se omite la cantidad/porción, se consume todo el item 