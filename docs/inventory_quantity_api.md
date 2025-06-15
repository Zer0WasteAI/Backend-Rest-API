# 📦 API de Actualización de Cantidades del Inventario

Esta documentación describe los nuevos endpoints para actualizar cantidades específicas de ingredientes y comidas en el inventario de manera simple y eficiente.

## 🎯 Resumen

Los nuevos endpoints permiten actualizar **únicamente las cantidades** sin necesidad de enviar todos los datos del item. Esto es ideal para interfaces de usuario donde el usuario solo quiere cambiar la cantidad disponible.

## 🔧 Endpoints

### 1. Actualizar Cantidad de Ingrediente

**PATCH** `/api/inventory/ingredients/{ingredient_name}/{added_at}/quantity`

Actualiza únicamente la cantidad de un stack específico de ingrediente.

#### **Parámetros URL:**
- `ingredient_name`: Nombre del ingrediente (string)
- `added_at`: Timestamp de cuando se agregó el stack (ISO format)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

#### **Body:**
```json
{
  "quantity": 2.5
}
```

#### **Response Exitoso (200):**
```json
{
  "message": "Cantidad de ingrediente actualizada exitosamente",
  "ingredient": "Tomate",
  "new_quantity": 2.5
}
```

#### **Response Error (404):**
```json
{
  "error": "Stack not found for ingredient 'Tomate' added at '2025-01-01T10:00:00Z'"
}
```

#### **Ejemplo de uso:**
```bash
curl -X PATCH \
  http://localhost:3000/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/quantity \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quantity": 1.5}'
```

---

### 2. Actualizar Cantidad de Comida

**PATCH** `/api/inventory/foods/{food_name}/{added_at}/quantity`

Actualiza únicamente la cantidad de porciones de un food item específico.

#### **Parámetros URL:**
- `food_name`: Nombre de la comida (string)
- `added_at`: Timestamp de cuando se agregó la comida (ISO format)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

#### **Body:**
```json
{
  "serving_quantity": 3
}
```

#### **Response Exitoso (200):**
```json
{
  "message": "Cantidad de comida actualizada exitosamente",
  "food": "Pasta con Tomate",
  "new_serving_quantity": 3
}
```

#### **Response Error (404):**
```json
{
  "error": "Food item not found for 'Pasta con Tomate' added at '2025-01-01T10:00:00Z'"
}
```

#### **Ejemplo de uso:**
```bash
curl -X PATCH \
  http://localhost:3000/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T10:00:00Z/quantity \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"serving_quantity": 2}'
```

---

## 🚀 Ventajas de estos Endpoints

### **✅ Simplicidad**
- Solo requieren enviar la nueva cantidad
- Mantienen todos los demás datos intactos (tipo, vencimiento, tips, etc.)

### **✅ Eficiencia**
- Requests más pequeños y rápidos
- Ideal para interfaces móviles

### **✅ Seguridad**
- Validación de tipos (float para ingredientes, int para comidas)
- Validación de rangos (cantidades no negativas)

### **✅ Usabilidad**
- Ideal para botones de +/- en la UI
- Perfecto para sliders de cantidad

---

## 🔍 Cómo Obtener los Datos Necesarios

Para usar estos endpoints, necesitas:

1. **Nombre del item**: Disponible en cualquier GET del inventario
2. **added_at timestamp**: Disponible en el campo `added_at` de cada stack/food

### Ejemplo - Obtener datos para actualizar:

```bash
# 1. Obtener inventario completo
GET /api/inventory

# Response incluye:
{
  "ingredients": [
    {
      "name": "Tomate",
      "stacks": [
        {
          "quantity": 1.0,
          "added_at": "2025-01-01T10:00:00Z",  // ← Usar este valor
          "expiration_date": "2025-01-15T10:00:00Z"
        }
      ]
    }
  ]
}

# 2. Actualizar cantidad usando los datos obtenidos
PATCH /api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z/quantity
Body: {"quantity": 2.5}
```

---

## 🛠️ Integración Frontend

### **React/JavaScript Ejemplo:**

```javascript
// Actualizar cantidad de ingrediente
const updateIngredientQuantity = async (ingredientName, addedAt, newQuantity) => {
  try {
    const response = await fetch(
      `/api/inventory/ingredients/${encodeURIComponent(ingredientName)}/${addedAt}/quantity`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ quantity: newQuantity })
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Quantity updated:', data.message);
      return data;
    } else {
      throw new Error('Failed to update quantity');
    }
  } catch (error) {
    console.error('❌ Error updating quantity:', error);
    throw error;
  }
};

// Actualizar cantidad de comida
const updateFoodQuantity = async (foodName, addedAt, newServingQuantity) => {
  try {
    const response = await fetch(
      `/api/inventory/foods/${encodeURIComponent(foodName)}/${addedAt}/quantity`,
      {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${userToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ serving_quantity: newServingQuantity })
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Food quantity updated:', data.message);
      return data;
    } else {
      throw new Error('Failed to update food quantity');
    }
  } catch (error) {
    console.error('❌ Error updating food quantity:', error);
    throw error;
  }
};
```

---

## 📝 Notas Importantes

### **🔐 Autenticación**
- Todos los endpoints requieren JWT token válido
- El token debe incluirse en el header `Authorization: Bearer {token}`

### **📊 Validaciones**
- **Ingredientes**: `quantity` debe ser un número float ≥ 0
- **Comidas**: `serving_quantity` debe ser un entero ≥ 1

### **🎯 Identificación de Items**
- Los items se identifican por `nombre` + `added_at`
- El `added_at` debe ser exactamente igual al almacenado en la BD

### **🔄 Datos Preservados**
- Estos endpoints **solo** cambian la cantidad
- Todos los demás datos permanecen intactos:
  - Fechas de vencimiento
  - Tipos de almacenamiento
  - Tips y consejos
  - Imágenes
  - Metadatos de calidad

---

## 🚦 Estados de Response

| Código | Descripción | Cuándo ocurre |
|--------|-------------|---------------|
| 200 | ✅ Actualizado exitosamente | Cantidad actualizada correctamente |
| 400 | ❌ Datos inválidos | Validation error (cantidad negativa, tipo incorrecto) |
| 401 | 🔐 No autorizado | Token JWT inválido o expirado |
| 404 | 🔍 No encontrado | Stack/comida no existe para el usuario |
| 500 | 🚨 Error del servidor | Error interno inesperado | 