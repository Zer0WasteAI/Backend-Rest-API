# 🗑️ API de Eliminación del Inventario

Esta documentación describe los endpoints para eliminar ingredientes y comidas del inventario de manera selectiva.

## 🎯 Resumen

Los endpoints de eliminación permiten:
- **Eliminar ingredientes completos** (todos sus stacks)
- **Eliminar stacks específicos** de ingredientes
- **Eliminar food items específicos**

## 🔧 Endpoints

### 1. Eliminar Ingrediente Completo

**DELETE** `/api/inventory/ingredients/{ingredient_name}`

Elimina un ingrediente completo del inventario, incluyendo todos sus stacks.

#### **Parámetros URL:**
- `ingredient_name`: Nombre del ingrediente (string)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
```

#### **Response Exitoso (200):**
```json
{
  "message": "Ingrediente eliminado completamente del inventario",
  "ingredient": "Tomate",
  "deleted": "all_stacks"
}
```

#### **Response Error (404):**
```json
{
  "error": "Ingredient 'Tomate' not found in inventory"
}
```

#### **Ejemplo de uso:**
```bash
curl -X DELETE \
  http://localhost:3000/api/inventory/ingredients/Tomate \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 2. Eliminar Stack Específico de Ingrediente

**DELETE** `/api/inventory/ingredients/{ingredient_name}/{added_at}`

Elimina un stack específico de ingrediente. Si es el último stack, elimina también el ingrediente completo.

#### **Parámetros URL:**
- `ingredient_name`: Nombre del ingrediente (string)
- `added_at`: Timestamp de cuando se agregó el stack (ISO format)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
```

#### **Response Exitoso (200):**
```json
{
  "message": "Stack de ingrediente eliminado exitosamente",
  "ingredient": "Tomate",
  "deleted_stack_added_at": "2025-01-01T10:00:00Z",
  "note": "Si era el último stack, el ingrediente fue eliminado completamente"
}
```

#### **Response Error (404):**
```json
{
  "error": "Error eliminando stack del ingrediente 'Tomate': Ingredient stack 'Tomate' not found (added at: 2025-01-01T10:00:00Z)"
}
```

#### **Ejemplo de uso:**
```bash
curl -X DELETE \
  http://localhost:3000/api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

### 3. Eliminar Food Item

**DELETE** `/api/inventory/foods/{food_name}/{added_at}`

Elimina un food item específico del inventario.

#### **Parámetros URL:**
- `food_name`: Nombre de la comida (string)
- `added_at`: Timestamp de cuando se agregó la comida (ISO format)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
```

#### **Response Exitoso (200):**
```json
{
  "message": "Comida eliminada exitosamente del inventario",
  "food": "Pasta con Tomate",
  "deleted_added_at": "2025-01-01T10:00:00Z"
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
curl -X DELETE \
  http://localhost:3000/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T10:00:00Z \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔄 Casos de Uso

### **Escenario 1: Eliminar Ingrediente Completo**
Cuando quieres eliminar completamente un ingrediente sin importar cuántos stacks tenga:

```javascript
// Eliminar todos los tomates del inventario
const deleteCompleteIngredient = async (ingredientName) => {
  try {
    const response = await fetch(
      `/api/inventory/ingredients/${encodeURIComponent(ingredientName)}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Ingredient deleted completely:', data.message);
      return data;
    } else {
      throw new Error('Failed to delete ingredient');
    }
  } catch (error) {
    console.error('❌ Error deleting ingredient:', error);
    throw error;
  }
};
```

### **Escenario 2: Eliminar Stack Específico**
Cuando quieres eliminar solo un lote específico de un ingrediente:

```javascript
// Eliminar solo el stack de tomates que se agregó en una fecha específica
const deleteSpecificStack = async (ingredientName, addedAt) => {
  try {
    const response = await fetch(
      `/api/inventory/ingredients/${encodeURIComponent(ingredientName)}/${addedAt}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Stack deleted:', data.message);
      return data;
    } else {
      throw new Error('Failed to delete stack');
    }
  } catch (error) {
    console.error('❌ Error deleting stack:', error);
    throw error;
  }
};
```

### **Escenario 3: Eliminar Comida**
Cuando quieres eliminar una comida específica:

```javascript
// Eliminar una comida específica
const deleteFoodItem = async (foodName, addedAt) => {
  try {
    const response = await fetch(
      `/api/inventory/foods/${encodeURIComponent(foodName)}/${addedAt}`,
      {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('✅ Food item deleted:', data.message);
      return data;
    } else {
      throw new Error('Failed to delete food item');
    }
  } catch (error) {
    console.error('❌ Error deleting food item:', error);
    throw error;
  }
};
```

---

## 🔍 Cómo Obtener los Datos Necesarios

Para usar estos endpoints, necesitas:

1. **Nombre del item**: Disponible en cualquier GET del inventario
2. **added_at timestamp**: Disponible en el campo `added_at` de cada stack/food

### Ejemplo - Flujo completo:

```bash
# 1. Obtener inventario para ver qué eliminar
GET /api/inventory

# Response incluye:
{
  "ingredients": [
    {
      "name": "Tomate",
      "stacks": [
        {
          "quantity": 1.0,
          "added_at": "2025-01-01T10:00:00Z",  // ← Usar para eliminar stack específico
          "expiration_date": "2025-01-15T10:00:00Z"
        },
        {
          "quantity": 2.0,
          "added_at": "2025-01-02T15:30:00Z",  // ← Otro stack
          "expiration_date": "2025-01-16T15:30:00Z"
        }
      ]
    }
  ]
}

# 2a. Eliminar stack específico
DELETE /api/inventory/ingredients/Tomate/2025-01-01T10:00:00Z

# 2b. O eliminar ingrediente completo (todos los stacks)
DELETE /api/inventory/ingredients/Tomate
```

---

## ⚠️ Comportamientos Importantes

### **🔄 Auto-limpieza de Ingredientes**
- Al eliminar el **último stack** de un ingrediente, el ingrediente se elimina automáticamente
- No quedan ingredientes "vacíos" en el inventario

### **🛡️ Validaciones**
- Todos los endpoints verifican que el item exista antes de eliminar
- Se retorna error 404 si el item no se encuentra
- Se requiere autenticación JWT válida

### **📊 Logs y Monitoreo**
- Todas las operaciones de eliminación se registran en logs
- Incluye información del usuario, item eliminado y timestamp

---

## 🎯 Resumen de URLs

| Operación | Método | URL | Descripción |
|-----------|--------|-----|-------------|
| Eliminar ingrediente completo | DELETE | `/api/inventory/ingredients/{name}` | Elimina el ingrediente y todos sus stacks |
| Eliminar stack específico | DELETE | `/api/inventory/ingredients/{name}/{added_at}` | Elimina solo un stack del ingrediente |
| Eliminar food item | DELETE | `/api/inventory/foods/{name}/{added_at}` | Elimina un food item específico |

---

## 🔐 Autenticación

- **Todos los endpoints requieren JWT token válido**
- El token debe incluirse en el header `Authorization: Bearer {token}`
- El usuario solo puede eliminar items de su propio inventario

---

## 📝 Notas para el Frontend

### **🎨 UI/UX Recomendaciones**
- **Confirmación de eliminación**: Siempre pedir confirmación antes de eliminar
- **Diferenciación visual**: Distinguir entre eliminar stack vs ingrediente completo
- **Feedback inmediato**: Mostrar mensaje de éxito/error después de la operación
- **Actualización automática**: Refrescar la lista del inventario después de eliminar

### **🔄 Manejo de Estados**
```javascript
// Ejemplo de manejo de estados en React
const [isDeleting, setIsDeleting] = useState(false);

const handleDeleteStack = async (ingredient, addedAt) => {
  if (!confirm(`¿Eliminar stack de ${ingredient} agregado el ${addedAt}?`)) return;
  
  setIsDeleting(true);
  try {
    await deleteSpecificStack(ingredient, addedAt);
    // Refrescar inventario
    await fetchInventory();
    toast.success('Stack eliminado exitosamente');
  } catch (error) {
    toast.error('Error eliminando stack');
  } finally {
    setIsDeleting(false);
  }
};
``` 