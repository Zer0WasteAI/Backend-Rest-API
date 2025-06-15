# 🔍 API de Detalles Individuales del Inventario

Esta documentación describe los endpoints para obtener información **completa y detallada** de ingredientes específicos y food items del inventario, incluyendo datos enriquecidos con IA.

## 🎯 Resumen

Los nuevos endpoints proporcionan acceso a información completa de items individuales:
- **Detalles completos de un ingrediente específico** (todos los stacks, impacto ambiental, ideas de aprovechamiento)
- **Detalles completos de un food item específico** (análisis nutricional, consejos de consumo, almacenamiento)

## 🔧 Endpoints

### 1. Obtener Detalles de Ingrediente Específico

**GET** `/api/inventory/ingredients/{ingredient_name}/detail`

Obtiene **TODA** la información disponible de un ingrediente específico del inventario.

#### **Parámetros URL:**
- `ingredient_name`: Nombre del ingrediente (string)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
```

#### **Response Exitoso (200):**
```json
{
  "name": "Tomate",
  "type_unit": "g",
  "storage_type": "Refrigerador",
  "tips": "Mantener en refrigerador para mayor duración. Ideal para ensaladas y salsas.",
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
  
  "environmental_impact": {
    "carbon_footprint": {
      "value": 0.6,
      "unit": "kg",
      "description": "CO2 por kg de tomate"
    },
    "water_footprint": {
      "value": 180,
      "unit": "l",
      "description": "agua por kg de tomate"
    },
    "sustainability_message": "Los tomates locales tienen menor impacto ambiental. Evita el desperdicio consumiéndolos antes del vencimiento."
  },
  
  "utilization_ideas": [
    {
      "title": "Salsa de tomate casera",
      "description": "Aprovecha tomates maduros para hacer una salsa que puedes congelar",
      "type": "preparación"
    },
    {
      "title": "Conserva en aceite",
      "description": "Corta en rodajas y conserva en aceite de oliva para uso posterior",
      "type": "conservación"
    },
    {
      "title": "Secado al sol",
      "description": "Seca rodajas finas para crear tomates deshidratados",
      "type": "aprovechamiento"
    }
  ],
  
  "consumption_advice": {
    "optimal_consumption": "Consume los tomates más maduros primero para evitar desperdicio",
    "preparation_tips": "Lava con agua fría y seca antes de cortar. Evita refrigerar si planeas usar pronto.",
    "nutritional_benefits": "Rico en licopeno, vitamina C y potasio. Excelente antioxidante."
  },
  
  "before_consumption_advice": {
    "quality_check": "Verifica que la piel esté firme y sin manchas oscuras",
    "safety_tips": "Lava bien bajo agua corriente antes de consumir"
  },
  
  "enriched_with": [
    "environmental_impact",
    "utilization_ideas",
    "consumption_advice",
    "before_consumption_advice",
    "statistics"
  ],
  "fetched_at": "2025-01-01T10:00:00Z"
}
```

#### **Response Error (404):**
```json
{
  "error": "Ingredient 'Apio' not found in inventory"
}
```

---

### 2. Obtener Detalles de Food Item Específico

**GET** `/api/inventory/foods/{food_name}/{added_at}/detail`

Obtiene **TODA** la información disponible de un food item específico del inventario.

#### **Parámetros URL:**
- `food_name`: Nombre de la comida (string)
- `added_at`: Timestamp de cuando se agregó (ISO format)

#### **Headers:**
```http
Authorization: Bearer {jwt_token}
```

#### **Response Exitoso (200):**
```json
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
  
  "nutritional_analysis": {
    "macronutrients": {
      "carbohydrates": "Rico en carbohidratos complejos de la pasta",
      "proteins": "Moderado contenido proteico, principalmente de la pasta",
      "fats": "Bajo en grasas, principalmente del aceite de oliva"
    },
    "vitamins_minerals": [
      "Vitamina C (tomate)",
      "Licopeno (tomate)",
      "Vitamina K (albahaca)",
      "Hierro (pasta enriquecida)"
    ],
    "health_benefits": "Proporciona energía sostenida, antioxidantes del tomate y grasas saludables del aceite de oliva",
    "dietary_considerations": "Apto para vegetarianos. Contiene gluten (pasta de trigo)."
  },
  
  "consumption_ideas": [
    {
      "title": "Agregar queso parmesano",
      "description": "Espolvorea queso parmesano rallado para mayor sabor y proteínas",
      "type": "mejora"
    },
    {
      "title": "Acompañar con ensalada",
      "description": "Sirve con ensalada verde para un plato más balanceado",
      "type": "acompañamiento"
    },
    {
      "title": "Transformar en lasaña",
      "description": "Usa como base para preparar una lasaña casera",
      "type": "transformación"
    }
  ],
  
  "storage_advice": {
    "optimal_temperature": "Refrigerado entre 2-4°C para mantener frescura",
    "reheating_tips": "Recalentar en microondas 1-2 minutos o en sartén con un poco de agua",
    "shelf_life_extension": "Consumir dentro de 2-3 días. Congelar porciones si sobra",
    "quality_indicators": "Verificar que no tenga mal olor ni cambios en textura antes de consumir"
  },
  
  "enriched_with": [
    "nutritional_analysis",
    "consumption_ideas",
    "storage_advice",
    "statistics"
  ],
  "fetched_at": "2025-01-01T15:30:00Z"
}
```

#### **Response Error (404):**
```json
{
  "error": "Food item 'Pizza' added at '2025-01-01T10:00:00Z' not found in inventory"
}
```

---

## 🌟 **Características de los Detalles**

### **🥬 Para Ingredientes:**
- **Información básica**: nombre, tipo, almacenamiento, consejos
- **Todos los stacks**: cantidades individuales, fechas de vencimiento
- **Estadísticas**: cantidad total, stack más próximo a vencer
- **Impacto ambiental**: huella de carbono, huella hídrica
- **Ideas de aprovechamiento**: conservación, preparación, aprovechamiento
- **Consejos de consumo**: preparación óptima, beneficios nutricionales
- **Verificaciones de calidad**: cómo verificar frescura antes de consumir

### **🍽️ Para Food Items:**
- **Información básica**: nombre, categoría, porciones, calorías
- **Análisis nutricional**: macronutrientes, vitaminas, beneficios
- **Ideas de consumo**: mejoras, acompañamientos, transformaciones
- **Consejos de almacenamiento**: temperatura, recalentamiento, extensión de vida útil
- **Consideraciones dietéticas**: restricciones, alergenos
- **Estadísticas**: calorías por porción, calorías totales

---

## 📝 **Ejemplos de Uso**

### **JavaScript/React:**

```javascript
// Obtener detalles completos de un ingrediente
const getIngredientDetails = async (ingredientName) => {
  try {
    const response = await fetch(
      `/api/inventory/ingredients/${encodeURIComponent(ingredientName)}/detail`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('🔍 Ingredient details:', data);
      
      // Mostrar estadísticas
      console.log(`Total quantity: ${data.total_quantity} ${data.type_unit}`);
      console.log(`Stacks: ${data.stack_count}`);
      console.log(`Environmental impact: ${data.environmental_impact.sustainability_message}`);
      
      return data;
    } else {
      throw new Error('Ingredient not found');
    }
  } catch (error) {
    console.error('❌ Error fetching ingredient details:', error);
    throw error;
  }
};

// Obtener detalles completos de un food item
const getFoodDetails = async (foodName, addedAt) => {
  try {
    const response = await fetch(
      `/api/inventory/foods/${encodeURIComponent(foodName)}/${addedAt}/detail`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${userToken}`
        }
      }
    );
    
    if (response.ok) {
      const data = await response.json();
      console.log('🍽️ Food details:', data);
      
      // Mostrar información nutricional
      console.log(`Calories per serving: ${data.calories_per_serving}`);
      console.log(`Nutritional benefits: ${data.nutritional_analysis.health_benefits}`);
      
      return data;
    } else {
      throw new Error('Food item not found');
    }
  } catch (error) {
    console.error('❌ Error fetching food details:', error);
    throw error;
  }
};
```

### **cURL Examples:**

```bash
# Obtener detalles de ingrediente específico
curl -X GET \
  "http://localhost:3000/api/inventory/ingredients/Tomate/detail" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# Obtener detalles de food item específico
curl -X GET \
  "http://localhost:3000/api/inventory/foods/Pasta%20con%20Tomate/2025-01-01T10:00:00Z/detail" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🔐 **Autenticación y Seguridad**

- **JWT requerido**: Todos los endpoints requieren token válido
- **Aislamiento por usuario**: Solo acceso a items del inventario del usuario autenticado
- **URL encoding**: Los nombres con espacios deben ser codificados en URLs

## 💡 **Casos de Uso en Frontend**

### **Páginas de Detalles:**
- Pantalla individual para mostrar todo sobre un ingrediente
- Vista detallada de food items con consejos de consumo
- Dashboards con impacto ambiental

### **Widgets Informativos:**
- Tooltips con consejos de aprovechamiento
- Indicadores de frescura y calidad
- Sugerencias de consumo basadas en IA

### **Planificación de Comidas:**
- Información nutricional para planificar menús
- Ideas de transformación de sobras
- Optimización de uso basada en fechas de vencimiento 