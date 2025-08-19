# ANÁLISIS COMPLETO DE COBERTURA DE TESTS
==================================================

## RESUMEN GENERAL
- Total de métodos: 117
- Métodos sin tests: 0
- Cobertura general: 100.0%

## CONTROLADORES
--------------------

### ADMIN_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 2
- Tests existentes: 14
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ cleanup_expired_tokens
  ✅ get_security_stats

### AUTH_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 5
- Tests existentes: 34
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ firebase_debug
  ✅ refresh_token
  ✅ logout
  ✅ firebase_signin
  ✅ guest_login

### COOKING_SESSION_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 4
- Tests existentes: 16
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ get_mise_en_place
  ✅ start_cooking_session
  ✅ complete_cooking_step
  ✅ finish_cooking_session

### ENVIRONMENTAL_SAVINGS_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 6
- Tests existentes: 20
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ calculate_savings_from_title
  ✅ calculate_savings_from_uid
  ✅ get_all_calculations
  ✅ get_calculations_by_status
  ✅ get_environmental_summary
  ✅ calculate_savings_from_session

### GENERATION_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 2
- Tests existentes: 20
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ get_generation_images_status
  ✅ get_generation_images

### IMAGE_MANAGEMENT_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 4
- Tests existentes: 18
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ assign_image
  ✅ search_similar_images
  ✅ sync_images
  ✅ upload_image

### INVENTORY_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 27
- Tests existentes: 33
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ add_ingredients
  ✅ get_inventory_complete
  ✅ update_ingredient
  ✅ delete_ingredient
  ✅ get_expiring_items
  ✅ add_ingredients_from_recognition
  ✅ add_foods_from_recognition
  ✅ get_inventory_simple
  ✅ update_ingredient_quantity
  ✅ update_food_quantity
  ✅ delete_ingredient_complete
  ✅ delete_food_item
  ✅ mark_ingredient_stack_consumed
  ✅ mark_food_item_consumed
  ✅ get_ingredient_detail
  ✅ get_food_detail
  ✅ get_ingredients_list
  ✅ get_foods_list
  ✅ upload_inventory_image
  ✅ add_item_to_inventory
  ✅ get_expiring_soon
  ✅ reserve_batch
  ✅ freeze_batch
  ✅ transform_batch
  ✅ quarantine_batch
  ✅ discard_batch
  ✅ create_leftover

### PLANNING_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 7
- Tests existentes: 18
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ save_meal_plan
  ✅ update_meal_plan
  ✅ delete_meal_plan
  ✅ get_meal_plan_by_date
  ✅ get_all_meal_plans
  ✅ get_meal_plan_dates
  ✅ update_meal_plan_images

### RECIPE_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 11
- Tests existentes: 62
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ generate_recipes
  ✅ generate_custom_recipes
  ✅ get_saved_recipes
  ✅ get_all_recipes
  ✅ delete_user_recipe
  ✅ get_generated_recipes_gallery
  ✅ get_default_recipes
  ✅ add_recipe_to_favorites
  ✅ remove_recipe_from_favorites
  ✅ get_user_favorite_recipes
  ✅ update_recipe_favorite

### RECOGNITION_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 8
- Tests existentes: 29
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ recognize_ingredients
  ✅ recognize_ingredients_complete
  ✅ recognize_foods
  ✅ recognize_batch
  ✅ recognize_ingredients_async
  ✅ get_recognition_status
  ✅ get_images_status
  ✅ get_recognition_images

### USER_CONTROLLER
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 2
- Tests existentes: 15
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ get_user_profile
  ✅ update_user_profile


## SERVICIOS
--------------------

### APPLICATION/FILE_UPLOAD_SERVICE
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 3
- Tests existentes: 13
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ FileUploadService.upload_image
  ✅ upload_image
  ✅ upload_image

### APPLICATION/FOOD_IMAGE_GENERATOR_SERVICE
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 4
- Tests existentes: 16
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ FoodImageGeneratorService.get_or_generate_food_image
  ✅ FoodImageGeneratorService.list_existing_foods_images
  ✅ get_or_generate_food_image
  ✅ list_existing_foods_images

### APPLICATION/IMAGE_UPLOAD_VALIDATOR
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 2
- Tests existentes: 17
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ ImageUploadValidator.validate_upload_request
  ✅ validate_upload_request

### APPLICATION/INGREDIENT_IMAGE_GENERATOR_SERVICE
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 10
- Tests existentes: 18
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ IngredientImageGeneratorService.get_or_generate_ingredient_image
  ✅ IngredientImageGeneratorService.clear_session_cache
  ✅ IngredientImageGeneratorService.get_cache_stats
  ✅ IngredientImageGeneratorService.get_or_generate_ingredient_images_sync_batch
  ✅ IngredientImageGeneratorService.list_existing_ingredients_images
  ✅ get_or_generate_ingredient_image
  ✅ clear_session_cache
  ✅ get_cache_stats
  ✅ get_or_generate_ingredient_images_sync_batch
  ✅ list_existing_ingredients_images

### APPLICATION/INVENTORY_IMAGE_UPLOAD_SERVICE
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 6
- Tests existentes: 19
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ InventoryImageUploadService.upload_inventory_image
  ✅ InventoryImageUploadService.get_user_inventory_images
  ✅ InventoryImageUploadService.delete_inventory_image
  ✅ upload_inventory_image
  ✅ get_user_inventory_images
  ✅ delete_inventory_image

### APPLICATION/INVENTORY_IMAGE_UPLOAD_VALIDATOR
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 3
- Tests existentes: 14
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ InventoryImageUploadValidator.validate_inventory_upload
  ✅ validate_inventory_upload
  ✅ validate_inventory_upload

### APPLICATION/RECIPE_IMAGE_GENERATOR_SERVICE
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 3
- Tests existentes: 18
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ RecipeImageGeneratorService.get_or_generate_recipe_image
  ✅ get_or_generate_recipe_image
  ✅ get_or_generate_recipe_image

### INFRASTRUCTURE/IDEMPOTENCY_SERVICE
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 6
- Tests existentes: 12
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ IdempotencyService.check_idempotency
  ✅ IdempotencyService.store_response
  ✅ IdempotencyService.cleanup_expired_keys
  ✅ check_idempotency
  ✅ store_response
  ✅ cleanup_expired_keys

### INFRASTRUCTURE/MISE_EN_PLACE_SERVICE
- Archivo de test: ✅ Existe
- Cobertura: 100.0%
- Métodos totales: 2
- Tests existentes: 13
- ✅ Todos los métodos tienen tests
- Métodos disponibles:
  ✅ MiseEnPlaceService.generate_mise_en_place
  ✅ generate_mise_en_place