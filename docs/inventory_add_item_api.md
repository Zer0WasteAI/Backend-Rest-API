# 🎯 API para Agregar Items al Inventario

Esta documentación describe el endpoint unificado para agregar items (ingredientes o comidas) al inventario, con enriquecimiento automático de datos usando IA.

## 🎯 Propósito

El endpoint permite agregar items al inventario proporcionando solo los datos básicos desde el frontend. Los campos faltantes se generan automáticamente usando IA:

- **Para ingredientes**: tips de almacenamiento, tiempo de vencimiento, impacto ambiental, ideas de uso
- **Para comidas**: ingredientes principales, categoría, calorías, descripción, tips, análisis nutricional

## 🔧 Endpoint

### Agregar Item al Inventario

**POST** `/api/inventory/add_item`

Agrega un item (ingrediente o comida) al inventario del usuario con enriquecimiento de IA.

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
Content-Type: application/json
```

#### **Request Body:**
```json
{
  "name": "string",         // Nombre del item (required)
  "quantity": "number",     // Cantidad (required)
  "unit": "string",         // Unidad de cantidad (required)
  "storage_type": "string", // Tipo de almacenamiento (required)
  "category": "string",     // 'ingredient' o 'food' (required)
  "image_url": "string"     // URL de imagen (optional, nullable)
}
```

#### **Campos Requeridos:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | string | Nombre del item (1-100 caracteres) |
| `quantity` | number | Cantidad > 0 |
| `unit` | string | Unidad de cantidad (ver valores válidos) |
| `storage_type` | string | Tipo de almacenamiento (ver valores válidos) |
| `category` | string | `ingredient` o `food` |

#### **Campos Opcionales:**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `image_url` | string \| null | URL de imagen del item |

---

## 📝 Valores Válidos

### **Unidades (`unit`):**
```
gramos, gr, g
kilogramos, kg, kilo, kilos
litros, l, lt
mililitros, ml
unidades, unidad, u, piezas, pieza
tazas, taza
cucharadas, cda
cucharaditas, cdita
porciones, porcion
latas, lata
paquetes, paquete
bolsas, bolsa
```

### **Tipos de Almacenamiento (`storage_type`):**
```
refrigerador, nevera, frigorifico
congelador, freezer
despensa, alacena, gabinete
temperatura ambiente, ambiente
lugar fresco, fresco
lugar seco, seco
```

---

## 📋 Ejemplos de Uso

### **1. Agregar Ingrediente**

```javascript
const addIngredient = async (ingredientData) => {
  try {
    const response = await fetch('/api/inventory/add_item', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: 'Tomate',
        quantity: 500,
        unit: 'gramos',
        storage_type: 'refrigerador',
        category: 'ingredient',
        image_url: 'https://example.com/tomate.jpg'
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Ingredient added:', result);
      return result;
    }
  } catch (error) {
    console.error('❌ Error adding ingredient:', error);
  }
};
```

### **2. Agregar Comida**

```javascript
const addFood = async (foodData) => {
  try {
    const response = await fetch('/api/inventory/add_item', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${userToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: 'Pasta con Pollo',
        quantity: 2,
        unit: 'porciones',
        storage_type: 'refrigerador',
        category: 'food',
        image_url: null  // Sin imagen
      })
    });
    
    if (response.ok) {
      const result = await response.json();
      console.log('✅ Food added:', result);
      return result;
    }
  } catch (error) {
    console.error('❌ Error adding food:', error);
  }
};
```

### **3. Formulario Frontend Completo**

```html
<form id="add-item-form">
  <input type="text" name="name" placeholder="Nombre del item" required>
  
  <input type="number" name="quantity" placeholder="Cantidad" min="0.01" step="0.01" required>
  
  <select name="unit" required>
    <option value="">Seleccionar unidad</option>
    <option value="gramos">Gramos</option>
    <option value="kg">Kilogramos</option>
    <option value="litros">Litros</option>
    <option value="ml">Mililitros</option>
    <option value="unidades">Unidades</option>
    <option value="porciones">Porciones</option>
  </select>
  
  <select name="storage_type" required>
    <option value="">Tipo de almacenamiento</option>
    <option value="refrigerador">Refrigerador</option>
    <option value="congelador">Congelador</option>
    <option value="despensa">Despensa</option>
    <option value="temperatura ambiente">Temperatura ambiente</option>
  </select>
  
  <select name="category" required>
    <option value="">Categoría</option>
    <option value="ingredient">Ingrediente</option>
    <option value="food">Comida</option>
  </select>
  
  <input type="url" name="image_url" placeholder="URL de imagen (opcional)">
  
  <button type="submit">Agregar al Inventario</button>
</form>
```

---

## 📥 Respuestas

### **Response Exitoso (201) - Ingrediente:**

```json
{
  "message": "Ingredient added successfully",
  "item_type": "ingredient",
  "item_data": {
    "name": "Tomate",
    "quantity": 500,
    "unit": "gramos",
    "storage_type": "refrigerador",
    "expiration_date": "2024-01-15T10:30:00+00:00",
    "tips": "Mantener en refrigerador, evitar exposición directa al sol. Ideal para consumir en ensaladas o cocinar.",
    "image_path": "https://example.com/tomate.jpg",
    "enriched_fields": [
      "tips",
      "expiration_time", 
      "time_unit",
      "environmental_impact",
      "utilization_ideas"
    ]
  }
}
```

### **Response Exitoso (201) - Comida:**

```json
{
  "message": "Food added successfully",
  "item_type": "food",
  "item_data": {
    "name": "Pasta con Pollo",
    "serving_quantity": 2,
    "storage_type": "refrigerador",
    "expiration_date": "2024-01-08T10:30:00+00:00",
    "main_ingredients": ["pasta", "pollo", "salsa de tomate"],
    "category": "plato principal",
    "calories": 450,
    "description": "Pasta italiana con pollo marinado en salsa de tomate casera",
    "tips": "Refrigerar inmediatamente después de cocinar. Recalentar a 165°F antes de consumir.",
    "image_path": "",
    "enriched_fields": [
      "main_ingredients",
      "food_category",
      "calories",
      "description",
      "tips",
      "expiration_time",
      "time_unit",
      "nutritional_analysis",
      "consumption_ideas"
    ]
  }
}
```

### **Response de Error (400) - Validación:**

```json
{
  "error": "Validation failed",
  "details": {
    "quantity": ["Quantity must be greater than 0"],
    "unit": ["Invalid unit"],
    "category": ["Category must be 'ingredient' or 'food'"]
  }
}
```

### **Response de Error (400) - Datos Inválidos:**

```json
{
  "error": "Field 'name' is required"
}
```

### **Response de Error (401):**

```json
{
  "error": "JWT token required"
}
```

### **Response de Error (500):**

```json
{
  "error": "Failed to add item to inventory",
  "details": "AI service unavailable"
}
```

### **Response con Campos IA Nulos (201) - Cuando IA falla:**

```json
{
  "message": "Ingredient added successfully",
  "item_type": "ingredient", 
  "item_data": {
    "name": "Apio",
    "quantity": 200,
    "unit": "gramos",
    "storage_type": "refrigerador",
    "expiration_date": "2024-01-15T10:30:00+00:00",
    "tips": "Almacenar en lugar fresco y seco.",
    "image_path": "",
    "environmental_impact": null,
    "utilization_ideas": null,
    "enriched_fields": ["tips", "expiration_time", "time_unit"]
  }
}
```

```json
{
  "message": "Food added successfully",
  "item_type": "food",
  "item_data": {
    "name": "Guiso Casero",
    "serving_quantity": 3,
    "storage_type": "refrigerador", 
    "expiration_date": "2024-01-08T10:30:00+00:00",
    "main_ingredients": null,
    "category": "otros",
    "calories": null,
    "description": null,
    "tips": "Refrigerar y consumir pronto.",
    "nutritional_analysis": null,
    "consumption_ideas": null,
    "image_path": "",
    "enriched_fields": ["tips", "expiration_time", "time_unit"]
  }
}
```

---

## 🤖 Enriquecimiento con IA

### **Para Ingredientes:**
- **`tips`**: Consejos de almacenamiento y uso (nullable)
- **`expiration_time` + `time_unit`**: Tiempo de vida estimado (nullable)
- **`environmental_impact`**: Información sobre impacto ambiental (nullable)
- **`utilization_ideas`**: Ideas para aprovechar el ingrediente (nullable)

### **Para Comidas:**
- **`main_ingredients`**: Lista de ingredientes principales detectados (nullable)
- **`food_category`**: Categoría gastronómica (plato principal, postre, etc.) (nullable)
- **`calories`**: Estimación calórica por porción (nullable)
- **`description`**: Descripción generada del platillo (nullable)
- **`tips`**: Consejos de almacenamiento y recalentamiento (nullable)
- **`nutritional_analysis`**: Análisis nutricional básico (nullable)
- **`consumption_ideas`**: Sugerencias de consumo (nullable)

---

## 🔒 Seguridad y Validaciones

### **Autenticación:**
- JWT token requerido en todas las peticiones
- Datos aislados por usuario (`user_uid`)

### **Validaciones:**
- Nombre: 1-100 caracteres, solo letras, números y algunos símbolos
- Cantidad: Número positivo mayor a 0
- Unidad: Solo valores predefinidos
- Storage type: Solo valores predefinidos
- Categoría: Solo 'ingredient' o 'food'
- Image URL: URL válida o null

### **Manejo de Errores de IA:**
- Si falla el enriquecimiento de IA, se usan valores por defecto
- El item se agrega exitosamente aunque la IA falle
- Los errores de IA no interrumpen el proceso

---

## 🔄 Integración con Otros Endpoints

### **Flujo Completo con Upload de Imagen:**

1. **Subir imagen**: `POST /api/inventory/upload_image`
   ```json
   {
     "upload_type": "ingredient",  // o "food"
     "item_name": "Tomate"
   }
   ```

2. **Agregar al inventario**: `POST /api/inventory/add_item`
   ```json
   {
     "name": "Tomate",
     "quantity": 500,
     "unit": "gramos",
     "storage_type": "refrigerador", 
     "category": "ingredient",
     "image_url": "URL_DESDE_PASO_1"
   }
   ```

### **Consultar después de agregar:**
- **Ver detalles**: `GET /api/inventory/ingredients/{name}/detail`
- **Listar inventario**: `GET /api/inventory/ingredients/list`
- **Inventario completo**: `GET /api/inventory/complete`

---

## 🧪 cURL Examples

### **Agregar Ingrediente:**
```bash
curl -X POST \
  "http://localhost:3000/api/inventory/add_item" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Cebolla",
    "quantity": 3,
    "unit": "unidades",
    "storage_type": "despensa",
    "category": "ingredient",
    "image_url": null
  }'
```

### **Agregar Comida:**
```bash
curl -X POST \
  "http://localhost:3000/api/inventory/add_item" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sopa de Verduras",
    "quantity": 4,
    "unit": "porciones",
    "storage_type": "refrigerador",
    "category": "food",
    "image_url": "https://example.com/sopa.jpg"
  }'
```

---

## ⚠️ Consideraciones

### **Datos Nullable:**
- `image_url` puede ser `null` o estar ausente

**Campos generados por IA (TODOS NULLABLE):**

**Para Ingredientes:**
- `tips` → puede ser `null` o string vacío
- `environmental_impact` → puede ser `null` o string vacío  
- `utilization_ideas` → puede ser `null` o array vacío

**Para Comidas:**
- `main_ingredients` → puede ser `null` o array vacío
- `food_category` → puede ser `null` o "otros" por defecto
- `calories` → puede ser `null` si no se puede estimar
- `description` → puede ser `null` o string vacío
- `tips` → puede ser `null` o string vacío
- `nutritional_analysis` → puede ser `null` o string vacío
- `consumption_ideas` → puede ser `null` o array vacío

### **Performance:**
- El enriquecimiento de IA añade latencia (~2-5 segundos)
- Los datos por defecto se usan si la IA tarda más de 10 segundos

### **Consistencia:**
- Los nombres de items se normalizan (trim, lowercase)
- Las unidades se validan contra lista predefinida
- Las fechas de vencimiento se calculan automáticamente 