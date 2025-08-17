# ZeroWasteAI API - Flujos Detallados 🔄

## Tabla de Contenidos
1. [Flujo de Autenticación](#flujo-de-autenticación)
2. [Flujo de Reconocimiento de Alimentos](#flujo-de-reconocimiento-de-alimentos)
3. [Flujo de Gestión de Inventario](#flujo-de-gestión-de-inventario)
4. [Flujo de Generación de Recetas](#flujo-de-generación-de-recetas)
5. [Flujo de Planificación de Comidas](#flujo-de-planificación-de-comidas)
6. [Flujo de Cálculo Ambiental](#flujo-de-cálculo-ambiental)
7. [Flujo de Gestión de Imágenes](#flujo-de-gestión-de-imágenes)

---

## 🔐 Flujo de Autenticación

### Archivos Involucrados:
```
📁 Controllers: 
  └── src/interface/controllers/auth_controller.py

📁 Use Cases:
  ├── src/application/use_cases/auth/login_oauth_usecase.py
  ├── src/application/use_cases/auth/refresh_token_usecase.py
  └── src/application/use_cases/auth/logout_usecase.py

📁 Services:
  ├── src/infrastructure/auth/oauth_service.py
  └── src/infrastructure/auth/jwt_service.py

📁 Models:
  ├── src/domain/models/auth_user.py
  ├── src/domain/models/user.py
  └── src/domain/models/profile_user.py

📁 Infrastructure:
  ├── src/infrastructure/security/token_security_repository.py
  ├── src/infrastructure/db/schemas/token_blacklist_schema.py
  └── src/infrastructure/auth/jwt_callbacks.py
```

### Proceso Detallado:

#### 1. Login OAuth (POST /api/auth/login)
```python
# Flujo paso a paso:
1. Usuario → auth_controller.py::login()
2. Controller → oauth_service.py::verify_firebase_token()
3. OAuth Service → Firebase Auth API
4. Firebase Auth → Validación del token
5. OAuth Service → jwt_service.py::generate_tokens()
6. JWT Service → Genera access + refresh tokens
7. Controller → token_security_repository.py::save_refresh_token()
8. Repository → Guarda en token_blacklist_schema
9. Controller → Response con tokens + perfil
```

#### 2. Refresh Token (POST /api/auth/refresh)
```python
# Flujo paso a paso:
1. Usuario → auth_controller.py::refresh_token()
2. Controller → refresh_token_usecase.py::execute()
3. Use Case → token_security_repository.py::validate_refresh_token()
4. Repository → Verifica token en BD
5. Use Case → jwt_service.py::generate_new_access_token()
6. JWT Service → Genera nuevo access token
7. Use Case → token_security_repository.py::mark_refresh_token_used()
8. Repository → Marca token como usado
9. Controller → Response con nuevo access token
```

#### 3. Logout (POST /api/auth/logout)
```python
# Flujo paso a paso:
1. Usuario → auth_controller.py::logout()
2. Controller → logout_usecase.py::execute()
3. Use Case → token_security_repository.py::blacklist_token()
4. Repository → Agrega token a blacklist
5. Use Case → token_security_repository.py::invalidate_refresh_tokens()
6. Repository → Invalida todos los refresh tokens del usuario
7. Controller → Response de logout exitoso
```

---

## 🔍 Flujo de Reconocimiento de Alimentos

### Archivos Involucrados:
```
📁 Controllers:
  └── src/interface/controllers/recognition_controller.py

📁 Use Cases:
  ├── src/application/use_cases/recognition/recognize_foods_use_case.py
  ├── src/application/use_cases/recognition/recognize_ingredients_complete_use_case.py
  └── src/application/use_cases/recognition/recognize_batch_use_case.py

📁 Services:
  ├── src/infrastructure/ai/ia_food_analyzer_service.py
  ├── src/infrastructure/ai/gemini_adapter_service.py
  └── src/infrastructure/storage/firebase_storage_adapter.py

📁 Models:
  └── src/domain/models/recognition.py

📁 Repositories:
  └── src/infrastructure/db/recognition_repository_impl.py
```

### Proceso Detallado:

#### 1. Reconocimiento de Alimentos (POST /api/recognition/foods)
```python
# Flujo paso a paso:
1. Usuario → recognition_controller.py::recognize_foods()
2. Controller → Validación de imágenes
3. Controller → firebase_storage_adapter.py::upload_images()
4. Storage → Firebase Storage (guarda imágenes)
5. Controller → recognize_foods_use_case.py::execute()
6. Use Case → gemini_adapter_service.py::analyze_food_images()
7. AI Service → Google Gemini API (análisis de IA)
8. AI Service → ia_food_analyzer_service.py::process_results()
9. Analyzer → Estructura datos de reconocimiento
10. Use Case → recognition_repository_impl.py::save()
11. Repository → Guarda en recognition_orm
12. Controller → Response con alimentos detectados
```

#### 2. Reconocimiento Completo de Ingredientes (POST /api/recognition/ingredients/complete)
```python
# Flujo paso a paso:
1. Usuario → recognition_controller.py::recognize_ingredients_complete()
2. Controller → recognize_ingredients_complete_use_case.py::execute()
3. Use Case → gemini_adapter_service.py::analyze_ingredients()
4. AI Service → Análisis detallado con IA
5. Use Case → ia_food_analyzer_service.py::extract_ingredient_details()
6. Analyzer → Extrae cantidad, unidades, calidad
7. Use Case → recognition_repository_impl.py::save_complete()
8. Repository → Guarda datos completos
9. Controller → Response con ingredientes estructurados
```

#### 3. Procesamiento en Lote (POST /api/recognition/batch)
```python
# Flujo paso a paso:
1. Usuario → recognition_controller.py::recognize_batch()
2. Controller → recognize_batch_use_case.py::execute()
3. Use Case → firebase_storage_adapter.py::upload_batch()
4. Storage → Subida masiva a Firebase
5. Use Case → gemini_adapter_service.py::batch_analyze()
6. AI Service → Procesamiento paralelo
7. Use Case → ia_food_analyzer_service.py::process_batch_results()
8. Analyzer → Estructura resultados en lote
9. Use Case → recognition_repository_impl.py::save_batch()
10. Repository → Guardado masivo en BD
11. Controller → Response con todos los resultados
```

---

## 📦 Flujo de Gestión de Inventario

### Archivos Involucrados:
```
📁 Controllers:
  └── src/interface/controllers/inventory_controller.py

📁 Use Cases:
  ├── src/application/use_cases/inventory/add_item_to_inventory_use_case.py
  ├── src/application/use_cases/inventory/get_inventory_content_use_case.py
  ├── src/application/use_cases/inventory/update_ingredient_quantity_use_case.py
  ├── src/application/use_cases/inventory/get_expiring_soon_use_case.py
  └── src/application/use_cases/inventory/mark_ingredient_stack_consumed_use_case.py

📁 Services:
  └── src/application/services/inventory_calculator.py

📁 Models:
  ├── src/domain/models/inventory.py
  ├── src/domain/models/ingredient.py
  └── src/domain/models/food_item.py

📁 Repositories:
  └── src/infrastructure/db/inventory_repository_impl.py
```

### Proceso Detallado:

#### 1. Agregar Elemento al Inventario (POST /api/inventory/add_item)
```python
# Flujo paso a paso:
1. Usuario → inventory_controller.py::add_item()
2. Controller → Validación de datos de entrada
3. Controller → add_item_to_inventory_use_case.py::execute()
4. Use Case → inventory_calculator.py::calculate_expiration()
5. Calculator → Calcula fecha de vencimiento
6. Use Case → inventory_repository_impl.py::add_ingredient()
7. Repository → inventory_orm.py (guarda en BD)
8. Repository → ingredient_stack_orm.py (stack específico)
9. Use Case → inventory_calculator.py::update_totals()
10. Calculator → Recalcula totales del inventario
11. Controller → Response con elemento agregado
```

#### 2. Obtener Contenido del Inventario (GET /api/inventory/content)
```python
# Flujo paso a paso:
1. Usuario → inventory_controller.py::get_content()
2. Controller → get_inventory_content_use_case.py::execute()
3. Use Case → inventory_repository_impl.py::get_user_inventory()
4. Repository → Query a inventory_orm + joins
5. Repository → Mapea ORMs a domain models
6. Use Case → inventory_calculator.py::calculate_freshness()
7. Calculator → Calcula estado de frescura
8. Use Case → inventory_calculator.py::group_by_category()
9. Calculator → Agrupa por categorías
10. Controller → Serializa y retorna inventario
```

#### 3. Elementos Próximos a Vencer (GET /api/inventory/expiring_soon)
```python
# Flujo paso a paso:
1. Usuario → inventory_controller.py::get_expiring_soon()
2. Controller → get_expiring_soon_use_case.py::execute()
3. Use Case → inventory_repository_impl.py::get_expiring_items()
4. Repository → Query filtrada por fechas
5. Use Case → inventory_calculator.py::calculate_urgency()
6. Calculator → Calcula nivel de urgencia
7. Use Case → inventory_calculator.py::sort_by_priority()
8. Calculator → Ordena por prioridad
9. Controller → Response con elementos urgentes
```

---

## 🍳 Flujo de Generación de Recetas

### Archivos Involucrados:
```
📁 Controllers:
  └── src/interface/controllers/recipe_controller.py

📁 Use Cases:
  ├── src/application/use_cases/recipes/generate_recipes_use_case.py
  ├── src/application/use_cases/recipes/generate_custom_recipe_use_case.py
  ├── src/application/use_cases/recipes/save_recipe_use_case.py
  └── src/application/use_cases/recipes/prepare_recipe_generation_data_use_case.py

📁 Services:
  ├── src/infrastructure/ai/gemini_recipe_generator_service.py
  ├── src/infrastructure/ai/recipe_image_generator_service.py
  └── src/infrastructure/async_tasks/async_task_service.py

📁 Models:
  └── src/domain/models/recipe.py

📁 Repositories:
  ├── src/infrastructure/db/recipe_repository_impl.py
  └── src/infrastructure/db/inventory_repository_impl.py
```

### Proceso Detallado:

#### 1. Generación de Recetas Basada en Inventario (POST /api/recipes/generate)
```python
# Flujo paso a paso:
1. Usuario → recipe_controller.py::generate_recipes()
2. Controller → generate_recipes_use_case.py::execute()
3. Use Case → prepare_recipe_generation_data_use_case.py::execute()
4. Data Preparer → inventory_repository_impl.py::get_available_ingredients()
5. Repository → Obtiene ingredientes disponibles
6. Data Preparer → Estructura datos para IA
7. Use Case → gemini_recipe_generator_service.py::generate_recipes()
8. AI Service → Google Gemini API (generación)
9. AI Service → Procesa respuesta de IA
10. Use Case → recipe_repository_impl.py::save_generated_recipes()
11. Repository → Guarda recetas en recipe_orm
12. Use Case → async_task_service.py::queue_image_generation()
13. Async Service → Cola generación de imágenes
14. Controller → Response con recetas (imágenes pendientes)

# Proceso Asíncrono de Imágenes:
15. async_task_service.py → recipe_image_generator_service.py::generate_images()
16. Image Generator → Google Gemini API (imágenes)
17. Image Generator → firebase_storage_adapter.py::upload_images()
18. Storage → Guarda imágenes en Firebase
19. Async Service → recipe_repository_impl.py::update_image_paths()
20. Repository → Actualiza rutas de imágenes
```

#### 2. Generación de Receta Personalizada (POST /api/recipes/generate_custom)
```python
# Flujo paso a paso:
1. Usuario → recipe_controller.py::generate_custom_recipe()
2. Controller → generate_custom_recipe_use_case.py::execute()
3. Use Case → user_profile_service.py::get_preferences()
4. Profile Service → Obtiene preferencias del usuario
5. Use Case → gemini_recipe_generator_service.py::generate_custom()
6. AI Service → Generación personalizada con IA
7. Use Case → recipe_repository_impl.py::save_custom_recipe()
8. Repository → Guarda receta personalizada
9. Use Case → async_task_service.py::queue_custom_image()
10. Async Service → Cola imagen personalizada
11. Controller → Response con receta personalizada
```

#### 3. Guardar Receta del Usuario (POST /api/recipes/save)
```python
# Flujo paso a paso:
1. Usuario → recipe_controller.py::save_recipe()
2. Controller → save_recipe_use_case.py::execute()
3. Use Case → Valida datos de receta
4. Use Case → recipe_repository_impl.py::save_user_recipe()
5. Repository → Guarda en recipe_orm
6. Repository → recipe_ingredient_orm.py (ingredientes)
7. Repository → recipe_step_orm.py (pasos)
8. Use Case → inventory_repository_impl.py::mark_ingredients_planned()
9. Repository → Marca ingredientes como planificados
10. Controller → Response con receta guardada
```

---

## 📅 Flujo de Planificación de Comidas

### Archivos Involucrados:
```
📁 Controllers:
  └── src/interface/controllers/planning_controller.py

📁 Use Cases:
  ├── src/application/use_cases/planning/save_meal_plan_use_case.py
  ├── src/application/use_cases/planning/get_meal_plan_by_user_and_date_use_case.py
  ├── src/application/use_cases/planning/update_meal_plan_use_case.py
  └── src/application/use_cases/planning/delete_meal_plan_use_case.py

📁 Models:
  └── src/domain/models/daily_meal_plan.py

📁 Repositories:
  └── src/infrastructure/db/meal_plan_repository_impl.py
```

### Proceso Detallado:

#### 1. Guardar Plan de Comida (POST /api/planning/meal_plan)
```python
# Flujo paso a paso:
1. Usuario → planning_controller.py::save_meal_plan()
2. Controller → save_meal_plan_use_case.py::execute()
3. Use Case → Valida fechas y recetas
4. Use Case → meal_plan_repository_impl.py::check_existing_plan()
5. Repository → Verifica planes existentes
6. Use Case → meal_plan_repository_impl.py::save_plan()
7. Repository → Guarda en daily_meal_plan_orm
8. Use Case → inventory_repository_impl.py::reserve_ingredients()
9. Repository → Reserva ingredientes necesarios
10. Controller → Response con plan guardado
```

#### 2. Obtener Plan por Fecha (GET /api/planning/meal_plan/{date})
```python
# Flujo paso a paso:
1. Usuario → planning_controller.py::get_meal_plan_by_date()
2. Controller → get_meal_plan_by_user_and_date_use_case.py::execute()
3. Use Case → meal_plan_repository_impl.py::find_by_date()
4. Repository → Query por usuario y fecha
5. Repository → Join con recipe_orm para detalles
6. Use Case → Mapea a domain model
7. Use Case → recipe_repository_impl.py::enrich_with_details()
8. Repository → Enriquece con detalles de recetas
9. Controller → Response con plan completo
```

---

## 🌱 Flujo de Cálculo Ambiental

### Archivos Involucrados:
```
📁 Controllers:
  └── src/interface/controllers/environmental_savings_controller.py

📁 Use Cases:
  ├── src/application/use_cases/recipes/calculate_enviromental_savings_from_recipe_name.py
  ├── src/application/use_cases/recipes/calculate_enviromental_savings_from_recipe_uid.py
  └── src/application/use_cases/recipes/sum_environmental_calculations_by_user.py

📁 Models:
  └── src/domain/models/environmental_savings.py

📁 Repositories:
  └── src/infrastructure/db/environmental_savings_repository_impl.py
```

### Proceso Detallado:

#### 1. Calcular Ahorro por Título (POST /api/environmental_savings/calculate/from-title)
```python
# Flujo paso a paso:
1. Usuario → environmental_savings_controller.py::calculate_savings_from_title()
2. Controller → estimate_savings_by_title_use_case.py::execute()
3. Use Case → recipe_repository_impl.py::find_by_title()
4. Repository → Busca receta por título
5. Use Case → environmental_calculator.py::calculate_co2_savings()
6. Calculator → Calcula reducción de CO2
7. Use Case → environmental_calculator.py::calculate_water_savings()
8. Calculator → Calcula ahorro de agua
9. Use Case → environmental_calculator.py::calculate_waste_reduction()
10. Calculator → Calcula reducción de desperdicio
11. Use Case → environmental_savings_repository_impl.py::save_calculation()
12. Repository → Guarda cálculo en environmental_savings_orm
13. Controller → Response con métricas ambientales
```

#### 2. Resumen Consolidado (GET /api/environmental_savings/summary)
```python
# Flujo paso a paso:
1. Usuario → environmental_savings_controller.py::get_environmental_summary()
2. Controller → sum_environmental_calculations_by_user.py::execute()
3. Use Case → environmental_savings_repository_impl.py::get_user_calculations()
4. Repository → Query todos los cálculos del usuario
5. Use Case → environmental_calculator.py::aggregate_totals()
6. Calculator → Suma totales por período
7. Use Case → environmental_calculator.py::calculate_trends()
8. Calculator → Calcula tendencias temporales
9. Use Case → environmental_calculator.py::generate_insights()
10. Calculator → Genera insights personalizados
11. Controller → Response con resumen completo
```

---

## 🖼️ Flujo de Gestión de Imágenes

### Archivos Involucrados:
```
📁 Controllers:
  └── src/interface/controllers/image_management_controller.py

📁 Use Cases:
  ├── src/application/use_cases/image_management/assign_image_reference_use_case.py
  ├── src/application/use_cases/image_management/search_similar_images_use_case.py
  └── src/application/use_cases/image_management/upload_image_use_case.py

📁 Services:
  └── src/infrastructure/ai/image_loader_service.py

📁 Models:
  └── src/domain/models/image_reference.py

📁 Repositories:
  └── src/infrastructure/db/image_repository_impl.py
```

### Proceso Detallado:

#### 1. Asignar Imagen a Ingrediente (POST /api/image_management/assign_image)
```python
# Flujo paso a paso:
1. Usuario → image_management_controller.py::assign_image()
2. Controller → assign_image_reference_use_case.py::execute()
3. Use Case → image_repository_impl.py::search_by_name()
4. Repository → Busca imágenes por nombre
5. Use Case → image_loader_service.py::calculate_similarity()
6. Service → Calcula similitud semántica
7. Use Case → image_loader_service.py::select_best_match()
8. Service → Selecciona mejor coincidencia
9. Use Case → image_repository_impl.py::create_reference()
10. Repository → Crea referencia en image_reference_orm
11. Controller → Response con imagen asignada
```

#### 2. Subir Nueva Imagen (POST /api/image_management/upload_image)
```python
# Flujo paso a paso:
1. Usuario → image_management_controller.py::upload_image()
2. Controller → upload_image_use_case.py::execute()
3. Use Case → Valida formato y tamaño
4. Use Case → firebase_storage_adapter.py::upload_file()
5. Storage → Sube a Firebase Storage
6. Use Case → image_loader_service.py::extract_metadata()
7. Service → Extrae metadatos de imagen
8. Use Case → image_repository_impl.py::save_image_reference()
9. Repository → Guarda referencia en BD
10. Use Case → image_loader_service.py::update_search_index()
11. Service → Actualiza índice de búsqueda
12. Controller → Response con imagen subida
```

---

## Consideraciones de Performance

### 🚀 Optimizaciones Implementadas:
1. **Rate Limiting** - Previene abuso de endpoints costosos
2. **Caching** - Cache de operaciones de IA frecuentes
3. **Async Processing** - Generación de imágenes en background
4. **Connection Pooling** - Pool optimizado de conexiones DB
5. **Lazy Loading** - Carga bajo demanda de relaciones

### 📊 Métricas de Monitoreo:
1. **Response Times** - Tiempo de respuesta por endpoint
2. **AI Usage** - Consumo de APIs de IA
3. **Cache Hit Rate** - Eficiencia del cache
4. **Database Load** - Carga de la base de datos
5. **Error Rates** - Tasas de error por flujo

---

*Documentación de Flujos Detallados - ZeroWasteAI API v1.0.0*
*Cada flujo incluye todos los archivos involucrados y el proceso paso a paso*