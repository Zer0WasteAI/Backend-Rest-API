# Mapa de Cobertura de Tests (Progreso por partes)

Este documento enumera, por capas, qué endpoints/servicios/métodos tienen tests y cuáles faltan. Se irá completando por partes para mantener claridad y foco.

Fecha: 2025-08-17

## Estado de avance
- Fase 1: Endpoints (Controllers)
  - [x] Inventory Controller
  - [ ] Resto de controllers (Auth, User, Recognition, Recipes, Image Management, Planning, Generation, Environmental Savings, Cooking Session)
- Fase 2: Domain Services
- Fase 3: Application Use Cases
- Fase 4: Infrastructure Services/Adapters

---

## Endpoints: Inventory Controller (`/api/inventory`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- POST `/ingredients`: probado (unit, functional/production, performance)
- GET `/` (inventario básico): probado (unit, functional/production, performance)
- GET `/complete`: probado (unit, functional/production, performance)
- PUT `/ingredients/<ingredient_name>/<added_at>`: probado (unit, functional/production)
- DELETE `/ingredients/<ingredient_name>/<added_at>`: probado (unit, functional/production)
- GET `/expiring`: probado (unit, functional/production, performance)
- POST `/ingredients/from-recognition`: probado (unit, functional/production)
- POST `/foods/from-recognition`: probado (functional/production) — falta unit
- GET `/simple`: probado (performance)
- PATCH `/ingredients/<ingredient_name>/<added_at>/quantity`: probado (unit, functional/production)
- PATCH `/foods/<food_name>/<added_at>/quantity`: probado (functional/production) — falta unit
- DELETE `/ingredients/<ingredient_name>`: probado (functional/production) — falta unit
- DELETE `/foods/<food_name>/<added_at>`: probado (functional/production) — falta unit
- POST `/ingredients/<ingredient_name>/<added_at>/consume`: probado (unit, functional/production)
- POST `/foods/<food_name>/<added_at>/consume`: probado (functional/production) — falta unit
- GET `/ingredients/<ingredient_name>/detail`: probado (unit, functional/production)
- GET `/foods/<food_name>/<added_at>/detail`: probado (functional/production) — falta unit
- GET `/ingredients/list`: probado (unit, functional/production)
- GET `/foods/list`: probado (functional/production) — falta unit
- POST `/upload_image`: probado (unit, functional/production)
- POST `/add_item`: probado (unit, functional/production)
- GET `/expiring_soon`: probado (unit, integration)
- POST `/batch/<batch_id>/reserve`: probado (unit, integration)
- POST `/batch/<batch_id>/freeze`: probado (unit, integration)
- POST `/batch/<batch_id>/transform`: probado (integration) — falta unit
- POST `/batch/<batch_id>/quarantine`: FALTA (no se encontró test)
- POST `/batch/<batch_id>/discard`: probado (integration) — falta unit
- POST `/leftovers`: probado (unit, integration)

Fuentes de verificación:
- Unit: `test/unit/interface/controllers/test_inventory_controller.py`
- Functional/Production: `test/production_validation/test_inventory_endpoints_production.py`
- Integration: `test/integration/test_all_endpoints.py`
- Performance: `test/performance/*`

---

## Endpoints: Auth Controller (`/api/auth`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- GET `/firebase-debug`: probado (unit, functional/production)
- POST `/refresh`: probado (functional/production) — falta unit
- POST `/logout`: probado (functional/production) — falta unit
- POST `/firebase-signin`: probado (functional/production, performance) — falta unit

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_auth_controller.py`
- Functional/Production: `test/production_validation/test_auth_endpoints_production.py`
- Performance: `test/performance/test_comprehensive_performance.py`

Notas:
- Los tests unitarios actuales del controller de Auth verifican estructuras/integraciones, pero no ejercen directamente los endpoints `/refresh`, `/logout` ni `/firebase-signin` con peticiones; se recomienda añadir unit tests específicos para estos handlers.

---

## Endpoints: Recipes Controller (`/api/recipes`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- POST `/generate-from-inventory`: probado (unit, functional/production, performance)
- POST `/generate-custom`: probado (functional/production) — falta unit
- GET `/saved`: probado (functional/production, performance) — falta unit
- GET `/all`: probado (functional/production, performance) — falta unit
- DELETE `/delete` (query `recipe_uid`): probado (functional/production) — falta unit
- GET `/generated/gallery`: probado (functional/production) — falta unit
- GET `/default`: probado (functional/production) — falta unit
- POST `/generate-save-from-inventory`: probado (functional, performance) — falta unit
- POST `/generated/<recipe_uid>/favorite`: probado (functional/production) — falta unit
- DELETE `/generated/<recipe_uid>/favorite`: probado (functional/production) — falta unit
- PUT `/generated/<recipe_uid>/favorite`: probado (functional/production) — falta unit
- GET `/generated/favorites`: probado (functional/production) — falta unit

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_recipe_controller.py`
- Functional/Production: `test/production_validation/test_recipe_endpoints_production.py`, `test/functional/test_recipe_generate_save.py`
- Performance: `test/performance/test_comprehensive_performance.py`, `test/performance/test_load_testing_suite.py`, `test/performance/test_database_performance.py`

Notas:
- La suite unitaria de `Recipe Controller` valida integración/estructuras y solo ejerce directamente el endpoint de generación desde inventario; se recomienda añadir unit tests específicos para el resto de handlers.

---

## Endpoints: User Controller (`/api/user`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- GET `/profile`: probado (unit, functional/production)
- PUT `/profile`: probado (unit, functional/production)

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_user_controller.py`
- Functional/Production: `test/production_validation/test_admin_user_generation_image_endpoints_production.py`

Notas:
- Ambos endpoints cuentan con pruebas unitarias que mockean Firestore service y validaciones de error. Cobertura funcional/production confirma flujos y edge cases adicionales.

---

## Endpoints: Recognition Controller (`/api/recognition`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- POST `/ingredients`: probado (unit, functional/production)
- POST `/ingredients/complete`: probado (unit, functional/production)
- POST `/foods`: probado (unit, functional/production)
- POST `/batch`: probado (unit, functional/production, performance)
- POST `/ingredients/async`: probado (unit, functional/production)
- GET `/status/<task_id>`: probado (unit, functional/production)
- GET `/images/status/<task_id>`: probado (unit, functional/production)
- GET `/recognition/<recognition_id>/images`: probado (unit, functional/production)

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_recognition_controller.py`
- Functional/Production: `test/production_validation/test_recognition_endpoints_production.py`
- Performance: `test/performance/test_comprehensive_performance.py`

Notas:
- La suite unitaria cubre los handlers principales, incluyendo asincronía y estados de tarea.

---

## Endpoints: Planning Controller (`/api/planning`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- POST `/save`: probado (unit, functional/production)
- PUT `/update`: probado (unit, functional/production)
- DELETE `/delete`: probado (unit, functional/production)
- GET `/get`: probado (unit, functional/production)
- GET `/all`: probado (unit, functional/production, performance)
- GET `/dates`: probado (unit, functional/production)
- POST `/images/update`: probado (unit, functional/production)

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_planning_controller.py`
- Functional/Production: `test/production_validation/test_planning_endpoints_production.py`
- Performance: `test/performance/test_comprehensive_performance.py`, `test/performance/test_database_performance.py`, `test/performance/test_load_testing_suite.py`

Notas:
- Cobertura sólida en unit y functional; performance cubre endpoints de lectura masiva.

---

## Endpoints: Environmental Savings Controller (`/api/environmental_savings`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- POST `/calculate/from-title`: probado (unit, functional/production)
- POST `/calculate/from-uid/<recipe_uid>`: probado (unit, functional/production)
- GET `/calculations`: probado (unit, functional/production, performance)
- GET `/calculations/status`: probado (unit, functional/production)
- GET `/summary`: probado (unit, functional/production, performance)
- POST `/calculate/from-session`: probado (integration)

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_environmental_savings_controller.py`
- Functional/Production: `test/production_validation/test_environmental_savings_endpoints_production.py`, `test/functional/test_environmental_endpoints.py`
- Integration: `test/integration/test_all_endpoints.py`
- Performance: `test/performance/test_comprehensive_performance.py`, `test/performance/test_database_performance.py`, `test/performance/test_load_testing_suite.py`

Notas:
- `from-session` aparece cubierto en integración; recomendable añadir unit test específico si se desea paridad con el resto.

---

## Endpoints: Image Management Controller (`/api/image_management`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- POST `/assign_image`: probado (unit, functional/production)
- POST `/search_similar_images`: probado (unit, functional/production)
- POST `/sync_images`: probado (unit, functional/production)
- POST `/upload_image`: probado (functional/production) — falta unit

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_image_management_controller.py` (registrado con prefijo `/api/images` para pruebas)
- Functional/Production: `test/production_validation/test_admin_user_generation_image_endpoints_production.py`

Notas:
- Se recomienda añadir unit test para `/upload_image` para paridad con los demás endpoints del módulo.

---

## Endpoints: Generation Controller (`/api/generation`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- GET `/images/status/<task_id>`: probado (unit, functional/production)
- GET `/<generation_id>/images`: probado (unit, functional/production)

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_generation_controller.py`
- Functional/Production: `test/production_validation/test_admin_user_generation_image_endpoints_production.py`

Notas:
- La suite unitaria incluye validaciones de métodos no permitidos y parámetros.

---

## Endpoints: Admin Controller (`/api/admin`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- POST `/cleanup-tokens`: probado (unit, functional/production)
- GET `/security-stats`: probado (unit, functional/production)

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_admin_controller.py`
- Functional/Production: `test/functional/test_admin_endpoints.py`, `test/production_validation/test_admin_user_generation_image_endpoints_production.py`

Notas:
- Endpoints marcados como internos con `internal_only`; tests cubren headers/secret.

---

## Endpoints: Cooking Session Controller (registrado bajo `/api/recipes`)

Resumen por endpoint. Se indica si existe al menos un test y el tipo de test encontrado.

- GET `/<recipe_uid>/mise_en_place`: probado (unit, integration)
- POST `/cooking_session/start`: probado (unit, integration, idempotency integration)
- POST `/cooking_session/complete_step`: probado (unit, integration)
- POST `/cooking_session/finish`: probado (unit, integration)

Fuentes de verificación:
- Unit (controllers): `test/unit/interface/controllers/test_cooking_session_controller.py` (registrado para pruebas bajo `/api/cooking_session`)
- Integration: `test/integration/test_all_endpoints.py`, `test/integration/test_idempotency_endpoints.py`

Notas:
- En producción, el blueprint se monta en `/api/recipes`; los unit tests usan un prefijo de pruebas `/api/cooking_session` para aislar.

---

## Domain Services (`src/domain/services`)

Resumen por servicio. Todos cuentan con pruebas unitarias específicas.

- `auth_service.py`: probado (unit)
- `email_service.py`: probado (unit)
- `ia_food_analyzer_service.py`: probado (unit)
- `ia_recipe_generator_service.py`: probado (unit)
- `inventory_calculator.py`: probado (unit)
- `oauth_service.py`: probado (unit)
- `sms_service.py`: probado (unit)

Fuentes: `test/unit/domain/services/*`

---

## Application Use Cases (`src/application/use_cases`)

Resumen por módulo con estado de cobertura unitaria. La mayoría de casos de uso están cubiertos indirectamente por tests de controllers e integración, pero aquí se señala cobertura de unit tests específicos de use cases.

### Auth
- `login_oauth_usecase.py`: probado (unit)
- `login_user_usecase.py`: probado (unit)
- `refresh_token_usecase.py`: probado (unit)
- `logout_usecase.py`: probado (unit)

Fuentes: `test/unit/application/use_cases/auth/*`

### Cooking Session
- `start_cooking_session_use_case.py`: probado (unit)
- `complete_step_use_case.py`: probado (unit)
- `finish_cooking_session_use_case.py`: probado (unit)

Fuentes: `test/unit/application/use_cases/cooking_session/*`

### Inventory
- Probados (unit):
  - `add_ingredients_to_inventory_use_case.py`
  - `get_expiring_soon_use_case.py`
  - `get_inventory_content_use_case.py`
- Faltan unit tests:
  - `upload_inventory_image_use_case.py`
  - `batch_management_use_cases.py` (reserve/freeze/transform/quarantine/discard)
  - `mark_ingredient_stack_consumed_use_case.py`
  - `get_food_detail_use_case.py`
  - `mark_food_item_consumed_use_case.py`
  - `update_ingredient_quantity_use_case.py`
  - `delete_food_item_use_case.py`
  - `add_item_to_inventory_use_case.py`
  - `add_ingredients_and_foods_to_inventory_use_case.py`
  - `get_expiring_soon_batches_use_case.py`
  - `create_leftover_use_case.py`
  - `get_ingredient_detail_use_case.py`
  - `update_food_quantity_use_case.py`
  - `delete_ingredient_status_use_case.py`
  - `update_ingredient_stack_use_case.py`
  - `update_food_item_use_case.py`
  - `delete_ingredient_complete_use_case.py`
  - `get_ingredients_list_use_case.py`
  - `get_foods_list_use_case.py`
  - `base_inventory_use_case.py` (abstract/base)

Fuentes: `test/unit/application/use_cases/inventory/*`

### Recipes
- Probado (unit):
  - `save_recipe_use_case.py`
  - `generate_recipes_use_case.py`
  - `prepare_recipe_generation_data_use_case.py`
  - `generate_custom_recipe_use_case.py`
  - `get_saved_recipes_use_case.py`
  - `get_all_recipes_use_case.py`
  - `delete_user_recipe_use_case.py`
  - `add_recipe_to_favorites_use_case.py`
  - `remove_recipe_from_favorites_use_case.py`
  - `get_favorite_recipes_use_case.py`
  - `get_mise_en_place_use_case.py`
  - `calculate_enviromental_savings_from_recipe_name.py`
  - `calculate_enviromental_savings_from_recipe_uid.py`
  - `get_all_environmental_calculations_by_user.py`
  - `get_environmental_calculations_by_user_and_status.py`
  - `sum_environmental_calculations_by_user.py`
- Faltan unit tests:
  - `calculate_environmental_savings_from_session.py` (pendiente en Recipes Controller; use case ya probado)

Fuentes: `test/unit/application/use_cases/recipes/*`

### Recognition
- Faltan unit tests:
  - `recognize_ingredients_use_case.py`
  - `recognize_ingredients_complete_use_case.py`
  - `recognize_foods_use_case.py`
  - `recognize_batch_use_case.py`

Notas: cobertura presente en unit tests de controllers e integración, pero no en unit tests de use cases.

### Image Management
- Faltan unit tests:
  - `assign_image_reference_use_case.py`
  - `search_similar_images_use_case.py`
  - `sync_image_loader_use_case.py`
  - `upload_image_use_case.py`
  - `unified_upload_use_case.py`
  - `find_image_by_name_use_case.py`

### Planning
- Faltan unit tests:
  - `save_meal_plan_use_case.py`
  - `update_meal_plan_use_case.py`
  - `delete_meal_plan_use_case.py`
  - `get_meal_plan_by_user_and_date_use_case.py`
  - `get_all_meal_plans_by_user_use_case.py`
  - `get_meal_plan_dates_usecase.py`

Fuentes generales para Use Cases: `test/unit/application/use_cases/**/*`

---

## Infrastructure Adapters/Services (`src/infrastructure/*`)

Resumen por área, con cobertura unitaria y faltantes relevantes.

### AI
- Probados (unit): `gemini_adapter_service.py`
- Faltan unit tests: `gemini_recipe_generator_service.py`, `cache_service.py`, `performance_monitor.py`, `token_optimizer.py`

### Async Tasks
- Faltan unit tests: `async_task_service.py`

### Auth
- Probados (unit): `jwt_service.py`
- Faltan unit tests: `jwt_callbacks.py`

### DB Repositories
- Probados (unit) adicionales: InventoryRepositoryImpl (get/save/add/update/delete básicos), RecipeRepositoryImpl (save/find/find_best_match/count/exists), GenerationRepositoryImpl (save/find/update), RecognitionRepositoryImpl (save/update/find), EnvironmentalSavingsRepositoryImpl (save/find/update/delete), MealPlanRepositoryImpl (save/find/delete/get_all/update), ImageRepositoryImpl (save/find/find_by_name/find_best_match), WasteLogRepository (find_by_user y agregaciones básicas en suite consolidada).
- Pendientes potenciales: revisar rutas menos críticas o edge cases en repos restantes.

### Firebase
- Probados (unit): `firestore_profile_service.py`
- Faltan unit tests: `firebase_storage_adapter.py`, `image_loader_service.py`

### Inventory
- Faltan unit tests: `inventory_calcularor_impl.py`

### Optimization
- Faltan unit tests: `cache_service.py`, `rate_limiter.py`

### Security
- Faltan unit tests: `security_headers.py`, `security_logger.py`, `rate_limiter.py`

### Services
- Probados (unit): `idempotency_service.py`

Fuentes: `test/unit/infrastructure/**/*`, `test/unit/infrastructure/test_config.py`

---

## Serializers y Middlewares

### Serializers (`src/interface/serializers/*`)
- Referenciados en tests de controllers (import/check), pero faltan unit tests específicos de validación para:
  - `inventory_serializers.py`
  - `add_item_serializer.py`
  - `mark_consumed_serializer.py`
  - `upload_image_serializer.py`
  - `item_name_serializer.py`
  - `image_reference_serializer.py`
  - `planning_serializers.py`
  - `reset_password_serializer.py`
  - `recipe_serializers.py` (parcialmente referenciado; falta suite dedicada de validación)

### Middlewares/Decorators
- `interface/middlewares/firebase_auth_decorator.py` (verify_firebase_token): cobertura indirecta en producción y unit (imports), pero falta suite unitaria específica de paths de error y éxito con mocks de Firebase.
- `shared/decorators/internal_only.py`: cobertura indirecta en tests de Admin; recomendable añadir unit tests directos (secret correcto/incorrecto, ausencia de header).
- `infrastructure/security/security_headers.py`: verificado en producción; faltan unit tests.
- `infrastructure/optimization/rate_limiter.py`: usado ampliamente; faltan unit tests dedicados.
- `infrastructure/optimization/cache_service.py`: usado ampliamente; faltan unit tests dedicados.

---

## Próximos pasos
- Completar el mapeo de endpoints para otro controller (sugerido: Auth o Recipes) y actualizar esta lista.
- Tras controllers, mapear Services y Use Cases con el mismo criterio.

---

## Checklist de Pendientes de Tests

Use esta lista para asignar y rastrear rápidamente los tests faltantes. Solo se listan los faltantes (todo está sin marcar por defecto).

### Controllers (Endpoints)
- [x] Inventory: POST `/foods/from-recognition` (unit)
- [x] Inventory: PATCH `/foods/<food_name>/<added_at>/quantity` (unit)
- [x] Inventory: DELETE `/ingredients/<ingredient_name>` (unit)
- [x] Inventory: DELETE `/foods/<food_name>/<added_at>` (unit)
- [x] Inventory: POST `/foods/<food_name>/<added_at>/consume` (unit)
- [x] Inventory: GET `/foods/<food_name>/<added_at>/detail` (unit)
- [x] Inventory: GET `/foods/list` (unit)
- [x] Inventory: POST `/batch/<batch_id>/transform` (unit)
- [x] Inventory: POST `/batch/<batch_id>/discard` (unit)
- [x] Inventory: POST `/batch/<batch_id>/quarantine` (unit/integration)
- [ ] Recipes: POST `/generate-custom` (unit)
- [x] Recipes: GET `/saved` (unit)
- [x] Recipes: GET `/all` (unit)
- [x] Recipes: DELETE `/delete` (unit)
- [x] Recipes: GET `/generated/gallery` (unit)
- [x] Recipes: GET `/default` (unit)
- [x] Recipes: POST `/generate-save-from-inventory` (unit)
- [x] Recipes: POST `/generated/<recipe_uid>/favorite` (unit)
- [x] Recipes: DELETE `/generated/<recipe_uid>/favorite` (unit)
- [x] Recipes: PUT `/generated/<recipe_uid>/favorite` (unit)
- [x] Recipes: GET `/generated/favorites` (unit)
- [x] Auth: POST `/refresh` (unit)
- [x] Auth: POST `/logout` (unit)
- [x] Auth: POST `/firebase-signin` (unit)
- [x] Environmental Savings: POST `/calculate/from-session` (unit)
- [x] Image Management: POST `/upload_image` (unit)

### Application Use Cases
- [ ] Inventory: `upload_inventory_image_use_case.py`
- [x] Inventory: `upload_inventory_image_use_case.py`
- [x] Inventory: `batch_management_use_cases.py` (reserve/freeze/transform/quarantine/discard)
- [x] Inventory: `mark_ingredient_stack_consumed_use_case.py`
- [x] Inventory: `get_food_detail_use_case.py`
- [x] Inventory: `mark_food_item_consumed_use_case.py`
- [x] Inventory: `update_ingredient_quantity_use_case.py`
- [x] Inventory: `delete_food_item_use_case.py`
- [x] Inventory: `add_item_to_inventory_use_case.py`
- [ ] Inventory: `add_ingredients_and_foods_to_inventory_use_case.py`
- [x] Inventory: `add_ingredients_and_foods_to_inventory_use_case.py`
- [ ] Inventory: `get_expiring_soon_batches_use_case.py`
- [x] Inventory: `get_expiring_soon_batches_use_case.py`
- [ ] Inventory: `create_leftover_use_case.py`
- [ ] Inventory: `get_ingredient_detail_use_case.py`
- [x] Inventory: `get_ingredient_detail_use_case.py`
- [ ] Inventory: `get_ingredient_detail_use_case.py` (pendiente)
- [ ] Inventory: `update_food_quantity_use_case.py`
- [ ] Inventory: `delete_ingredient_status_use_case.py`
- [x] Inventory: `delete_ingredient_status_use_case.py`
- [ ] Inventory: `update_ingredient_stack_use_case.py`
- [x] Inventory: `update_ingredient_stack_use_case.py`
- [x] Inventory: `update_food_item_use_case.py`
- [ ] Inventory: `delete_ingredient_complete_use_case.py`
- [x] Inventory: `get_ingredients_list_use_case.py`
- [x] Inventory: `get_foods_list_use_case.py`
- [ ] Inventory: `base_inventory_use_case.py` (base)
- [ ] Recipes: `generate_recipes_use_case.py`
- [ ] Recipes: `prepare_recipe_generation_data_use_case.py`
- [ ] Recipes: `generate_custom_recipe_use_case.py`
- [ ] Recipes: `get_saved_recipes_use_case.py`
- [ ] Recipes: `get_all_recipes_use_case.py`
- [ ] Recipes: `delete_user_recipe_use_case.py`
- [ ] Recipes: `add_recipe_to_favorites_use_case.py`
- [ ] Recipes: `remove_recipe_from_favorites_use_case.py`
- [ ] Recipes: `get_favorite_recipes_use_case.py`
- [ ] Recipes: `get_mise_en_place_use_case.py`
- [ ] Recipes: `calculate_enviromental_savings_from_recipe_name.py`
- [ ] Recipes: `calculate_enviromental_savings_from_recipe_uid.py`
- [ ] Recipes: `calculate_environmental_savings_from_session.py`
- [ ] Recipes: `get_all_environmental_calculations_by_user.py`
- [ ] Recipes: `get_environmental_calculations_by_user_and_status.py`
- [ ] Recipes: `sum_environmental_calculations_by_user.py`
- [ ] Recognition: `recognize_ingredients_use_case.py`
- [ ] Recognition: `recognize_ingredients_complete_use_case.py`
- [ ] Recognition: `recognize_foods_use_case.py`
- [ ] Recognition: `recognize_batch_use_case.py`
- [ ] Image Management: `assign_image_reference_use_case.py`
- [ ] Image Management: `search_similar_images_use_case.py`
- [ ] Image Management: `sync_image_loader_use_case.py`
- [ ] Image Management: `upload_image_use_case.py`
- [ ] Image Management: `unified_upload_use_case.py`
- [ ] Image Management: `find_image_by_name_use_case.py`
- [ ] Planning: `save_meal_plan_use_case.py`
- [ ] Planning: `update_meal_plan_use_case.py`
- [ ] Planning: `delete_meal_plan_use_case.py`
- [ ] Planning: `get_meal_plan_by_user_and_date_use_case.py`
- [ ] Planning: `get_all_meal_plans_by_user_use_case.py`
- [ ] Planning: `get_meal_plan_dates_usecase.py`

### Infrastructure (Servicios/Adapters)
- [ ] AI: `gemini_recipe_generator_service.py` (unit)
- [ ] AI: `cache_service.py` (unit)
- [ ] AI: `performance_monitor.py` (unit)
- [ ] AI: `token_optimizer.py` (unit)
- [ ] Async Tasks: `async_task_service.py` (unit)
- [ ] Auth: `jwt_callbacks.py` (unit)
- [x] Auth: `jwt_callbacks.py` (unit)
- [ ] Firebase: `firebase_storage_adapter.py` (unit)
- [ ] Firebase: `image_loader_service.py` (unit)
- [x] Firebase: `image_loader_service.py` (unit)
- [x] Firebase: `firebase_storage_adapter.py` (unit - helper parsing)
- [ ] Inventory: `inventory_calcularor_impl.py` (unit)
- [ ] Optimization: `cache_service.py` (unit)
- [ ] Optimization: `rate_limiter.py` (unit)
  
Marcados:
- [x] Optimization: `cache_service.py` (unit)
- [x] Optimization: `rate_limiter.py` (unit)
- [ ] Security: `security_headers.py` (unit)
- [ ] Security: `security_logger.py` (unit)
- [ ] Security: `rate_limiter.py` (unit)

### DB Repositories (métodos)
- [ ] IngredientBatchRepository: `find_by_id`, `find_by_user`, `_map_to_domain`
- [ ] CookingSessionRepository: `find_by_id`, `find_by_user`, `_map_to_domain`
- [ ] LeftoverRepository: `find_by_id`, `find_by_user`, `_map_to_domain`
- [ ] WasteLogRepository: `find_by_user`, `_map_to_domain`
- [ ] InventoryRepositoryImpl: todos los métodos clave (get/save/add*/delete*/update*/get_* listados en este documento)
- [ ] RecipeRepositoryImpl: todos los métodos clave (save/find*/delete*/exists/list/get_all/map/count)
- [ ] RecipeGeneratedRepositoryImpl: `save_generated_recipe`, `find_by_*`, `update_image_status`
- [ ] GenerationRepositoryImpl: `save`, `find_by_*`, `update_validation_status`, `_to_domain`
- [ ] RecognitionRepositoryImpl: `save`, `find_by_*`, `update*`, `_to_domain`
- [ ] EnvironmentalSavingsRepositoryImpl: `save`, `find_by_*`, `update*`, `create`, `delete`, `_to_domain`
- [ ] MealPlanRepositoryImpl: `save`, `find_by_*`, `delete_by_user_and_date`, `get_all*`, `update_by_user_and_date`, `_to_domain`
- [ ] ImageRepositoryImpl: `save`, `find_by_*`, `_to_domain`
- [ ] AuthRepository: `create/find/update*`
- [ ] UserRepository: `create/find/update*`
- [ ] ProfileRepository: `create/find/update*`
- [ ] TokenSecurityRepository: `add_to_blacklist/is_token_blacklisted/blacklist_all_user_tokens/track_refresh_token/mark_refresh_token_used/is_refresh_token_compromised/get_refresh_token_info/cleanup_expired_tokens`

### Serializers / Middlewares
- [ ] Serializers: tests de validación para `inventory_serializers.py`
- [ ] Serializers: tests de validación para `add_item_serializer.py`
- [ ] Serializers: tests de validación para `mark_consumed_serializer.py`
- [ ] Serializers: tests de validación para `upload_image_serializer.py`
- [ ] Serializers: tests de validación para `item_name_serializer.py`
- [ ] Serializers: tests de validación para `image_reference_serializer.py`
- [ ] Serializers: tests de validación para `planning_serializers.py`
- [ ] Serializers: tests de validación para `reset_password_serializer.py`
- [ ] Serializers: tests de validación para `recipe_serializers.py`
- [ ] Middleware: `verify_firebase_token` (paths de éxito/error mockeando Firebase Admin)
- [ ] Decorator: `internal_only` (secret correcto/incorrecto, ausencia de header)
## DB Repositories: Métodos sin unit tests específicos (detalle)

Resumen granular por repositorio comparando métodos implementados vs. cubiertos en `test/unit/infrastructure/db/test_repositories.py`.

- IngredientBatchRepository (`src/infrastructure/db/ingredient_batch_repository_impl.py`)
  - Cubiertos: `save`, `find_by_ingredient_fefo`, `find_expiring_soon`, `update_expired_batches`, `lock_batch_for_update`.
  - Faltan: `find_by_id`, `find_by_user`, `_map_to_domain`.

- CookingSessionRepository (`src/infrastructure/db/cooking_session_repository_impl.py`)
  - Cubiertos: `save`, `_serialize_steps`, `_deserialize_steps`, `log_consumption`, `get_session_consumptions`, `find_active_sessions`.
  - Faltan: `find_by_id`, `find_by_user`, `_map_to_domain`.

- LeftoverRepository (`src/infrastructure/db/leftover_repository_impl.py`)
  - Cubiertos: `save`, `find_expiring_soon`, `mark_consumed`.
  - Faltan: `find_by_id`, `find_by_user`, `_map_to_domain`.

- WasteLogRepository (`src/infrastructure/db/waste_log_repository_impl.py`)
  - Cubiertos: `save`, `find_by_date_range`, `get_waste_summary`.
  - Faltan: `find_by_user`, `_map_to_domain`.

- InventoryRepositoryImpl (`src/infrastructure/db/inventory_repository_impl.py`)
  - Faltan (no se hallaron unit tests directos):
    - `get_by_user_uid`, `save`, `add_ingredient_stack`, `add_food_item`, `delete_ingredient_stack`, `delete_food_item`, `update_food_item`,
      `get_inventory`, `create_inventory`, `get_ingredient_stack`, `get_food_item`, `get_all_food_items`, `get_all_ingredient_stacks`, `delete_ingredient_complete`.

- RecipeRepositoryImpl (`src/infrastructure/db/recipe_repository_impl.py`)
  - Faltan: `save`, `find_by_uid`, `find_by_name`, `find_best_match_name`, `find_orm_by_id`, `map_to_domain`, `delete`, `delete_by_user_and_title`,
    `exists_by_user_and_title`, `find_by_user_and_title`, `get_all`, `get_all_by_user`, `_to_domain`, `count_by_user_and_title_prefix`.

- RecipeGeneratedRepositoryImpl (`src/infrastructure/db/recipe_generated_repository_impl.py`)
  - Faltan: `save_generated_recipe`, `find_by_user_and_title`, `find_by_user_and_title_fuzzy`, `find_by_generation_id`, `find_by_user`, `update_image_status`.

- GenerationRepositoryImpl (`src/infrastructure/db/generation_repository_impl.py`)
  - Faltan: `save`, `find_by_user`, `find_by_uid`, `update_validation_status`, `_to_domain`.

- RecognitionRepositoryImpl (`src/infrastructure/db/recognition_repository_impl.py`)
  - Faltan: `save`, `find_by_user`, `find_by_uid`, `get_by_id`, `update_validation_status`, `update`, `_to_domain`.

- EnvironmentalSavingsRepositoryImpl (`src/infrastructure/db/environmental_savings_repository_impl.py`)
  - Faltan: `save`, `find_by_user`, `find_by_uid`, `find_by_user_and_by_is_cooked`, `update_type_status`, `find_by_user_and_recipe`, `_to_domain`,
    `create`, `update`, `delete`, `find_by_user_and_status`, `update_validation_status`.

- MealPlanRepositoryImpl (`src/infrastructure/db/meal_plan_repository_impl.py`)
  - Faltan: `save`, `find_by_user_and_date`, `delete_by_user_and_date`, `get_all_by_user`, `_to_domain`, `get_all_dates_by_user`, `update_by_user_and_date`.

- ImageRepositoryImpl (`src/infrastructure/db/image_repository_impl.py`)
  - Faltan: `save`, `find_by_uid`, `find_by_name`, `find_best_match_name`, `_to_domain`.

- AuthRepository (`src/infrastructure/db/auth_repository.py`)
  - Faltan: `create`, `find_by_uid`, `find_by_uid_and_provider`, `find_by_email`, `update`, `update_jwt_token`.

- UserRepository (`src/infrastructure/db/user_repository.py`)
  - Faltan: `create`, `find_by_email`, `exists_by_email`, `find_by_uid`, `update`, `update_email`, `update_uid`, `find_user_with_auth_by_email`.

- ProfileRepository (`src/infrastructure/db/profile_repository.py`)
  - Faltan: `create`, `find_by_uid`, `update`, `find_by_email`.

- TokenSecurityRepository (`src/infrastructure/db/token_security_repository.py`)
  - Faltan: `add_to_blacklist`, `is_token_blacklisted`, `blacklist_all_user_tokens`, `track_refresh_token`, `mark_refresh_token_used`,
    `is_refresh_token_compromised`, `get_refresh_token_info`, `cleanup_expired_tokens`.
