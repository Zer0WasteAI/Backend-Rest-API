# Estructura Completa del JSON de Ingredientes

Este documento describe la estructura completa del JSON que devuelve la API cuando se reconocen ingredientes o se obtienen del inventario con toda la información enriquecida.

## Reconocimiento Completo de Ingredientes

### Endpoint: `POST /recognition/ingredients/complete`

#### Request
```json
{
  "images_paths": ["path/to/image1.jpg", "path/to/image2.jpg"]
}
```

#### Response
```json
{
  "ingredients": [
    {
      // ============ INFORMACIÓN BÁSICA ============
      "name": "Maíz",
      "description": "Mazorca de maíz amarillo con granos grandes y dulces, textura firme y color dorado intenso",
      "quantity": 0.1,
      "type_unit": "g",
      "storage_type": "Bodega",
      "expiration_time": 14,
      "time_unit": "Días",
      "tips": "Consejos sobre cómo conservar mejor el ingrediente, recomendación de uso, etc.",
      
      // ============ FECHAS Y METADATOS ============
      "expiration_date": "2025-05-14T12:00:00Z",
      "added_at": "2025-01-01T12:00:00Z",
      "image_path": "https://storage.googleapis.com/...",
      
      // ============ IMPACTO AMBIENTAL ============
      "environmental_impact": {
        "carbon_footprint": {
          "value": 0.0,
          "unit": "kg",
          "description": "CO2"
        },
        "water_footprint": {
          "value": 0,
          "unit": "l",
          "description": "agua"
        },
        "sustainability_message": "Al consumir este ingrediente antes de que se eche a perder evitas..."
      },
      
      // ============ IDEAS DE APROVECHAMIENTO ============
      "utilization_ideas": [
        {
          "title": "Congelar en porciones pequeñas",
          "description": "Divide el maíz en porciones individuales y congélalas para mayor duración",
          "type": "conservación"
        },
        {
          "title": "Incluir en guisos o sopas",
          "description": "Mezcla varios ingredientes donde se puedan aprovechar todos los sabores",
          "type": "preparación"
        },
        {
          "title": "Buscar recetas de aprovechamiento",
          "description": "Busca recetas de aprovechamiento específicas en la sección de recetas",
          "type": "aprovechamiento"
        }
      ]
    }
  ]
}
```

## Inventario Completo

### Endpoint: `GET /inventory/complete`

#### Response
```json
{
  "ingredients": [
    {
      // ============ INFORMACIÓN BÁSICA ============
      "name": "Maíz",
      "type_unit": "g",
      "storage_type": "Bodega",
      "tips": "Consejos sobre cómo conservar mejor el ingrediente",
      "image_path": "https://storage.googleapis.com/...",
      
      // ============ LOTES DISPONIBLES ============
      "stacks": [
        {
          "quantity": 0.1,
          "type_unit": "g",
          "expiration_date": "2025-05-14T12:00:00Z",
          "added_at": "2025-01-01T12:00:00Z"
        }
      ],
      
      // ============ IMPACTO AMBIENTAL ============
      "environmental_impact": {
        "carbon_footprint": {
          "value": 0.0,
          "unit": "kg",
          "description": "CO2"
        },
        "water_footprint": {
          "value": 0,
          "unit": "l",
          "description": "agua"
        },
        "sustainability_message": "Al consumir este ingrediente antes de que se eche a perder evitas..."
      },
      
      // ============ IDEAS DE APROVECHAMIENTO ============
      "utilization_ideas": [
        {
          "title": "Congelar en porciones pequeñas",
          "description": "Divide el maíz en porciones individuales y congélalas para mayor duración",
          "type": "conservación"
        },
        {
          "title": "Incluir en guisos o sopas",
          "description": "Mezcla varios ingredientes donde se puedan aprovechar todos los sabores",
          "type": "preparación"
        },
        {
          "title": "Buscar recetas de aprovechamiento",
          "description": "Busca recetas de aprovechamiento específicas en la sección de recetas",
          "type": "aprovechamiento"
        }
      ]
    }
  ],
  "food_items": [],
  "total_ingredients": 1,
  "enriched_with": ["environmental_impact", "utilization_ideas"]
}
```

## Prompts Separados Utilizados

### 1. Prompt de Impacto Ambiental
```
Actúa como un experto en sostenibilidad alimentaria y análisis de ciclo de vida.

Para el ingrediente: {ingredient_name}

Analiza su impacto ambiental considerando:
- Huella de carbono promedio desde la producción hasta el consumo
- Huella hídrica necesaria para su producción
- Considera el contexto peruano y regional

Devuelve únicamente un JSON con la estructura mostrada arriba.
```

### 2. Prompt de Ideas de Aprovechamiento
```
Actúa como un chef peruano experto en aprovechamiento de alimentos y reducción del desperdicio.

Para el ingrediente: {ingredient_name}
Descripción: {description}

Genera ideas prácticas de aprovechamiento considerando:
- Formas de usar el ingrediente cuando está fresco
- Técnicas de conservación caseras
- Maneras de aprovechar partes que normalmente se descartan
- Recetas o preparaciones específicas de la cocina peruana

Devuelve únicamente un JSON con la estructura mostrada arriba.
```

## Flujo de Datos

1. **Reconocimiento Básico**: Se obtienen los datos fundamentales del ingrediente
2. **Enriquecimiento con IA**: Se agregan impacto ambiental e ideas de aprovechamiento
3. **Procesamiento de Imágenes**: Se asignan o generan imágenes
4. **Cálculo de Fechas**: Se calculan fechas de vencimiento
5. **Almacenamiento**: Se guarda en el inventario
6. **Recuperación Completa**: Al consultar el inventario, se enriquece nuevamente con IA

## Compatibilidad

La API mantiene compatibilidad con:
- Endpoints básicos existentes (`/recognition/ingredients`, `/inventory`)
- Nuevos endpoints completos (`/recognition/ingredients/complete`, `/inventory/complete`)
- Estructura de datos anterior (solo se agregan campos, no se modifican existentes) 