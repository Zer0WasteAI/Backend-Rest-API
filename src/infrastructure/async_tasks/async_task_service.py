import uuid
import threading
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

from src.infrastructure.db.base import db
from src.infrastructure.db.models.async_task_orm import AsyncTaskORM


class AsyncTaskService:
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=3, thread_name_prefix="AsyncTask")
    
    def create_task(self, user_uid: str, task_type: str, input_data: Dict[str, Any]) -> str:
        """Crea una nueva tarea asíncrona y retorna el task_id"""
        task_id = str(uuid.uuid4())
        
        print(f"🆕 [ASYNC TASK] ===== CREATING NEW TASK =====")
        print(f"🆕 [ASYNC TASK] Task ID: {task_id}")
        print(f"🆕 [ASYNC TASK] User UID: {user_uid}")
        print(f"🆕 [ASYNC TASK] Task Type: {task_type}")
        print(f"🆕 [ASYNC TASK] Input Data: {input_data}")
        
        try:
            task = AsyncTaskORM(
                task_id=task_id,
                user_uid=user_uid,
                task_type=task_type,
                status='pending',
                input_data=input_data,
                progress_percentage=0,
                current_step='Iniciando procesamiento...'
            )
            
            db.session.add(task)
            db.session.commit()
            
            print(f"✅ [ASYNC TASK] Task {task_id} created successfully for user {user_uid}")
            print(f"🆕 [ASYNC TASK] ===== TASK CREATION COMPLETED =====")
            return task_id
            
        except Exception as e:
            import traceback
            print(f"🚨 [ASYNC TASK] Error creating task {task_id}:")
            print(f"🚨 [ASYNC TASK] Exception type: {type(e).__name__}")
            print(f"🚨 [ASYNC TASK] Exception message: {str(e)}")
            print(f"🚨 [ASYNC TASK] FULL TRACEBACK:")
            print(traceback.format_exc())
            
            # Rollback en caso de error
            db.session.rollback()
            raise e
    
    def update_task_progress(self, task_id: str, progress: int, step: str, status: str = None):
        """Actualiza el progreso de una tarea"""
        try:
            from flask import current_app
            with current_app.app_context():
                task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
                if task:
                    task.progress_percentage = progress
                    task.current_step = step
                    if status:
                        task.status = status
                    if status == 'processing' and not task.started_at:
                        task.started_at = datetime.now(timezone.utc)
                        
                    db.session.commit()
                    print(f"📊 [ASYNC TASK] {task_id}: {progress}% - {step}")
        except Exception as e:
            print(f"🚨 [ASYNC TASK] Error updating progress for {task_id}: {str(e)}")
    
    def complete_task(self, task_id: str, result_data: Dict[str, Any]):
        """Marca una tarea como completada con el resultado"""
        print(f"💾 [ASYNC TASK] ===== COMPLETING TASK =====")
        print(f"💾 [ASYNC TASK] Task ID: {task_id}")
        print(f"💾 [ASYNC TASK] Result data type: {type(result_data)}")
        print(f"💾 [ASYNC TASK] Result data keys: {result_data.keys() if isinstance(result_data, dict) else 'Not a dict'}")
        
        if isinstance(result_data, dict) and 'ingredients' in result_data:
            print(f"💾 [ASYNC TASK] Ingredients count: {len(result_data['ingredients'])}")
            if len(result_data['ingredients']) > 0:
                first_ingredient = result_data['ingredients'][0]
                print(f"💾 [ASYNC TASK] First ingredient example:")
                print(f"💾 [ASYNC TASK]   Name: {first_ingredient.get('name', 'No name')}")
                print(f"💾 [ASYNC TASK]   Image: {first_ingredient.get('image_path', 'No image')}")
                print(f"💾 [ASYNC TASK]   Expiration: {first_ingredient.get('expiration_date', 'No expiration')}")
        
        try:
            from flask import current_app
            with current_app.app_context():
                task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
                if task:
                    task.status = 'completed'
                    task.progress_percentage = 100
                    task.current_step = 'Procesamiento completado'
                    task.result_data = result_data
                    task.completed_at = datetime.now(timezone.utc)
                    
                    db.session.commit()
                    print(f"✅ [ASYNC TASK] Completed task {task_id}")
                    print(f"💾 [ASYNC TASK] Data saved to database successfully")
                else:
                    print(f"🚨 [ASYNC TASK] Task {task_id} not found for completion!")
                    
        except Exception as e:
            print(f"🚨 [ASYNC TASK] Error completing task {task_id}: {str(e)}")
            import traceback
            print(f"🚨 [ASYNC TASK] Error traceback: {traceback.format_exc()}")
        finally:
            print(f"💾 [ASYNC TASK] ===== TASK COMPLETION FINISHED =====")
    
    def fail_task(self, task_id: str, error_message: str):
        """Marca una tarea como fallida"""
        print(f"❌ [ASYNC TASK] ===== FAILING TASK =====")
        print(f"❌ [ASYNC TASK] Task ID: {task_id}")
        print(f"❌ [ASYNC TASK] Error Message: {error_message}")
        
        try:
            from flask import current_app
            with current_app.app_context():
                task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
                if task:
                    print(f"❌ [ASYNC TASK] Task found - Current status: {task.status}")
                    print(f"❌ [ASYNC TASK] Task type: {task.task_type}")
                    print(f"❌ [ASYNC TASK] User UID: {task.user_uid}")
                    print(f"❌ [ASYNC TASK] Input data: {task.input_data}")
                    print(f"❌ [ASYNC TASK] Progress before failure: {task.progress_percentage}%")
                    print(f"❌ [ASYNC TASK] Last step: {task.current_step}")
                    
                    task.status = 'failed'
                    task.current_step = 'Error en procesamiento'
                    task.error_message = error_message
                    task.completed_at = datetime.now(timezone.utc)
                    
                    db.session.commit()
                    print(f"✅ [ASYNC TASK] Task {task_id} marked as failed successfully")
                else:
                    print(f"🚨 [ASYNC TASK] Task {task_id} not found in database!")
                    
        except Exception as e:
            import traceback
            print(f"🚨 [ASYNC TASK] Error failing task {task_id}:")
            print(f"🚨 [ASYNC TASK] Exception type: {type(e).__name__}")
            print(f"🚨 [ASYNC TASK] Exception message: {str(e)}")
            print(f"🚨 [ASYNC TASK] Original error was: {error_message}")
            print(f"🚨 [ASYNC TASK] FULL TRACEBACK:")
            print(traceback.format_exc())
            
        finally:
            print(f"❌ [ASYNC TASK] ===== TASK FAILURE PROCESS COMPLETED =====")
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene el estado actual de una tarea"""
        task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
        if not task:
            return None
        
        return {
            "task_id": task.task_id,
            "status": task.status,
            "progress_percentage": task.progress_percentage,
            "current_step": task.current_step,
            "created_at": task.created_at.isoformat(),
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result_data": task.result_data,
            "error_message": task.error_message
        }
    
    def run_async_recognition(self, task_id: str, ai_service, recognition_repository, 
                            storage_adapter, ingredient_image_generator_service, 
                            calculator_service, user_uid: str, images_paths: List[str]):
        """Ejecuta reconocimiento de ingredientes en background"""
        
        # Capturar el app context actual
        from flask import current_app
        app = current_app._get_current_object()
        
        def background_recognition():
            with app.app_context():
                print(f"🚀 [ASYNC RECOGNITION] ===== STARTING BACKGROUND PROCESSING =====")
                print(f"🚀 [ASYNC RECOGNITION] Task ID: {task_id}")
                print(f"🚀 [ASYNC RECOGNITION] User UID: {user_uid}")
                print(f"🚀 [ASYNC RECOGNITION] Images count: {len(images_paths)}")
                print(f"🚀 [ASYNC RECOGNITION] Images paths: {images_paths}")
                
                try:
                    # Paso 1: Actualizar estado - iniciando
                    print(f"🚀 [ASYNC RECOGNITION] Step 1: Initializing task...")
                    self.update_task_progress(task_id, 5, "Preparando imágenes...", "processing")
                    
                    # Paso 2: Cargar imágenes
                    print(f"🚀 [ASYNC RECOGNITION] Step 2: Loading images from storage...")
                    images_files = []
                    for i, path in enumerate(images_paths):
                        try:
                            print(f"🚀 [ASYNC RECOGNITION] Loading image {i+1}/{len(images_paths)}: {path}")
                            file = storage_adapter.get_image(path)
                            images_files.append(file)
                            progress = 5 + (i + 1) * 10 // len(images_paths)
                            self.update_task_progress(task_id, progress, f"Cargando imagen {i+1}/{len(images_paths)}")
                            print(f"✅ [ASYNC RECOGNITION] Image {i+1} loaded successfully")
                        except Exception as img_error:
                            print(f"🚨 [ASYNC RECOGNITION] Error loading image {i+1} ({path}): {str(img_error)}")
                            raise Exception(f"Error loading image {i+1}: {str(img_error)}")
                    
                    print(f"✅ [ASYNC RECOGNITION] All {len(images_files)} images loaded successfully")
                    
                    # Paso 3: Reconocimiento AI básico
                    print(f"🚀 [ASYNC RECOGNITION] Step 3: Starting AI recognition...")
                    self.update_task_progress(task_id, 20, "Detectando ingredientes con IA...")
                    
                    try:
                        result = ai_service.recognize_ingredients(images_files)
                        print(f"✅ [ASYNC RECOGNITION] AI recognition completed")
                        print(f"🚀 [ASYNC RECOGNITION] Recognized {len(result.get('ingredients', []))} ingredients")
                        for i, ingredient in enumerate(result.get('ingredients', [])):
                            print(f"🚀 [ASYNC RECOGNITION]   Ingredient {i+1}: {ingredient.get('name', 'Unknown')}")
                    except Exception as ai_error:
                        print(f"🚨 [ASYNC RECOGNITION] AI recognition failed: {str(ai_error)}")
                        raise Exception(f"AI recognition failed: {str(ai_error)}")
                    
                    # Paso 4: Guardar reconocimiento básico
                    print(f"🚀 [ASYNC RECOGNITION] Step 4: Saving recognition data...")
                    self.update_task_progress(task_id, 40, "Guardando datos de reconocimiento...")
                    
                    try:
                        from src.domain.models.recognition import Recognition
                        recognition = Recognition(
                            uid=str(uuid.uuid4()),
                            user_uid=user_uid,
                            images_paths=images_paths,
                            recognized_at=datetime.now(timezone.utc),
                            raw_result=result,
                            is_validated=False,
                            validated_at=None
                        )
                        recognition_repository.save(recognition)
                        print(f"✅ [ASYNC RECOGNITION] Recognition data saved with UID: {recognition.uid}")
                    except Exception as save_error:
                        print(f"🚨 [ASYNC RECOGNITION] Error saving recognition: {str(save_error)}")
                        raise Exception(f"Error saving recognition data: {str(save_error)}")
                    
                    # Paso 5: Generar imágenes en paralelo
                    print(f"🚀 [ASYNC RECOGNITION] Step 5: Starting parallel image generation...")
                    current_time = datetime.now(timezone.utc)
                    self.update_task_progress(task_id, 50, "Generando imágenes de ingredientes...")
                    
                    def generate_ingredient_image(ingredient_data):
                        ingredient, user_uid = ingredient_data
                        ingredient_name = ingredient["name"]
                        descripcion = ingredient.get("description", "")
                        
                        print(f"🎨 [ASYNC RECOGNITION] Generating image for: {ingredient_name}")
                        
                        try:
                            image_path = ingredient_image_generator_service.get_or_generate_ingredient_image(
                                ingredient_name=ingredient_name,
                                user_uid=user_uid,
                                descripcion=descripcion
                            )
                            print(f"✅ [ASYNC RECOGNITION] Image generated for {ingredient_name}: {image_path}")
                            return ingredient_name, image_path, None
                        except Exception as e:
                            error_msg = f"Error generating image for {ingredient_name}: {str(e)}"
                            print(f"🚨 [ASYNC RECOGNITION] {error_msg}")
                            return ingredient_name, "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image", str(e)
                    
                    # Generación paralela de imágenes
                    ingredient_images = {}
                    total_ingredients = len(result['ingredients'])
                    
                    print(f"🚀 [ASYNC RECOGNITION] Starting parallel generation for {total_ingredients} ingredients...")
                    
                    try:
                        with ThreadPoolExecutor(max_workers=2) as image_executor:
                            thread_data = [(ingredient, user_uid) for ingredient in result["ingredients"]]
                            
                            future_to_ingredient = {
                                image_executor.submit(generate_ingredient_image, data): data[0]["name"] 
                                for data in thread_data
                            }
                            
                            completed_images = 0
                            for future in future_to_ingredient:
                                ingredient_name, image_path, error = future.result()
                                ingredient_images[ingredient_name] = image_path
                                completed_images += 1
                                
                                if error:
                                    print(f"⚠️ [ASYNC RECOGNITION] Image generation error for {ingredient_name}: {error}")
                                
                                # Actualizar progreso dinámicamente
                                progress = 50 + (completed_images * 30 // total_ingredients)
                                self.update_task_progress(task_id, progress, f"Imagen generada para {ingredient_name}")
                                
                        print(f"✅ [ASYNC RECOGNITION] All image generation tasks completed")
                        
                    except Exception as parallel_error:
                        print(f"🚨 [ASYNC RECOGNITION] Error in parallel image generation: {str(parallel_error)}")
                        raise Exception(f"Error in parallel image generation: {str(parallel_error)}")
                    
                    # Paso 6: Finalizar datos de cada ingrediente
                    print(f"🚀 [ASYNC RECOGNITION] Step 6: Finalizing ingredient data...")
                    self.update_task_progress(task_id, 85, "Finalizando datos de ingredientes...")
                    
                    for i, ingredient in enumerate(result["ingredients"]):
                        ingredient_name = ingredient["name"]
                        print(f"🚀 [ASYNC RECOGNITION] Processing ingredient {i+1}: {ingredient_name}")
                        
                        # Asignar imagen
                        ingredient["image_path"] = ingredient_images.get(ingredient_name, "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image")
                        
                        # Calcular fecha de vencimiento
                        try:
                            expiration_date = calculator_service.calculate_expiration_date(
                                added_at=current_time,
                                time_value=ingredient["expiration_time"],
                                time_unit=ingredient["time_unit"]
                            )
                            ingredient["expiration_date"] = expiration_date.isoformat()
                            print(f"✅ [ASYNC RECOGNITION] Expiration calculated for {ingredient_name}: {expiration_date}")
                        except Exception as e:
                            print(f"⚠️ [ASYNC RECOGNITION] Error calculating expiration for {ingredient_name}: {str(e)}")
                            from datetime import timedelta
                            fallback_date = current_time + timedelta(days=ingredient.get("expiration_time", 7))
                            ingredient["expiration_date"] = fallback_date.isoformat()
                            print(f"⚠️ [ASYNC RECOGNITION] Using fallback expiration for {ingredient_name}: {fallback_date}")
                        
                        ingredient["added_at"] = current_time.isoformat()
                    
                    # Paso 7: Completar tarea
                    print(f"🚀 [ASYNC RECOGNITION] Step 7: Completing task...")
                    self.update_task_progress(task_id, 95, "Guardando resultado final...")
                    self.complete_task(task_id, result)
                    
                    print(f"🎉 [ASYNC RECOGNITION] ===== TASK COMPLETED SUCCESSFULLY =====")
                    print(f"🎉 [ASYNC RECOGNITION] Task {task_id} completed with {len(result['ingredients'])} ingredients")
                    print(f"🎉 [ASYNC RECOGNITION] Generated {len([img for img in ingredient_images.values() if 'placeholder' not in img])} images")
                    
                except Exception as e:
                    import traceback
                    print(f"🚨 [ASYNC RECOGNITION] ===== TASK FAILED =====")
                    print(f"🚨 [ASYNC RECOGNITION] Task ID: {task_id}")
                    print(f"🚨 [ASYNC RECOGNITION] Error: {str(e)}")
                    print(f"🚨 [ASYNC RECOGNITION] Error type: {type(e).__name__}")
                    print(f"🚨 [ASYNC RECOGNITION] Context:")
                    print(f"🚨 [ASYNC RECOGNITION]   User UID: {user_uid}")
                    print(f"🚨 [ASYNC RECOGNITION]   Images paths: {images_paths}")
                    print(f"🚨 [ASYNC RECOGNITION]   Images loaded: {len(locals().get('images_files', []))}")
                    print(f"🚨 [ASYNC RECOGNITION] FULL TRACEBACK:")
                    print(traceback.format_exc())
                    
                    self.fail_task(task_id, str(e))
                    print(f"🚨 [ASYNC RECOGNITION] ===== TASK FAILURE PROCESS COMPLETED =====")
        
        # Lanzar en background
        self.executor.submit(background_recognition)
        print(f"🎯 [ASYNC RECOGNITION] Task {task_id} queued for background processing")

    def run_simple_image_generation(self, recognition_id: str, user_uid: str, ingredients: List[dict], 
                                  ingredient_image_generator_service, recognition_repository):
        """
        Ejecuta generación simple de imágenes para reconocimiento sin task tracking complejo.
        Actualiza directamente el reconocimiento en la base de datos.
        """
        
        # Capturar el app context actual
        from flask import current_app
        app = current_app._get_current_object()
        
        def background_simple_generation():
            with app.app_context():
                print(f"🎨 [SIMPLE IMAGES] ===== STARTING BACKGROUND IMAGE GENERATION =====")
                print(f"🎨 [SIMPLE IMAGES] Recognition ID: {recognition_id}")
                print(f"🎨 [SIMPLE IMAGES] User UID: {user_uid}")
                print(f"🎨 [SIMPLE IMAGES] Ingredients count: {len(ingredients)}")
                
                try:
                    def generate_ingredient_image(ingredient_data):
                        ingredient, user_uid, recognition_id = ingredient_data
                        ingredient_name = ingredient["name"]
                        descripcion = ingredient.get("description", "")
                        
                        print(f"🎨 [SIMPLE IMAGES] Generating image for: {ingredient_name}")
                        
                        try:
                            image_path = ingredient_image_generator_service.get_or_generate_ingredient_image(
                                ingredient_name=ingredient_name,
                                user_uid=user_uid,
                                descripcion=descripcion
                            )
                            print(f"✅ [SIMPLE IMAGES] Image generated for {ingredient_name}: {image_path}")
                            return ingredient_name, image_path, None
                        except Exception as e:
                            error_msg = f"Error generating image for {ingredient_name}: {str(e)}"
                            print(f"🚨 [SIMPLE IMAGES] {error_msg}")
                            return ingredient_name, "https://via.placeholder.com/150x150/cccccc/666666?text=Error", str(e)
                    
                    # Generación paralela de imágenes
                    ingredient_images = {}
                    total_ingredients = len(ingredients)
                    
                    print(f"🎨 [SIMPLE IMAGES] Starting parallel generation for {total_ingredients} ingredients...")
                    
                    with ThreadPoolExecutor(max_workers=3) as image_executor:
                        thread_data = [(ingredient, user_uid, recognition_id) for ingredient in ingredients]
                        
                        future_to_ingredient = {
                            image_executor.submit(generate_ingredient_image, data): data[0]["name"] 
                            for data in thread_data
                        }
                        
                        completed_images = 0
                        for future in future_to_ingredient:
                            ingredient_name, image_path, error = future.result()
                            ingredient_images[ingredient_name] = image_path
                            completed_images += 1
                            
                            if error:
                                print(f"⚠️ [SIMPLE IMAGES] Image generation error for {ingredient_name}: {error}")
                            
                            print(f"✅ [SIMPLE IMAGES] Progress: {completed_images}/{total_ingredients} images completed")
                    
                    print(f"✅ [SIMPLE IMAGES] All image generation completed")
                    
                    # Actualizar el reconocimiento con las imágenes generadas
                    print(f"💾 [SIMPLE IMAGES] Updating recognition with generated images...")
                    recognition = recognition_repository.find_by_uid(recognition_id)
                    
                    if recognition:
                        # Actualizar cada ingrediente con su imagen
                        for ingredient in recognition.raw_result["ingredients"]:
                            ingredient_name = ingredient["name"]
                            if ingredient_name in ingredient_images:
                                ingredient["image_path"] = ingredient_images[ingredient_name]
                                ingredient["image_status"] = "ready"
                                print(f"✅ [SIMPLE IMAGES] Updated {ingredient_name} with image")
                        
                        # Guardar cambios en la base de datos
                        recognition_repository.save(recognition)
                        print(f"💾 [SIMPLE IMAGES] Recognition {recognition_id} updated successfully")
                        
                        # Log de finalización con notificación para el frontend
                        print(f"🎉 [SIMPLE IMAGES] ===== IMAGE GENERATION COMPLETED =====")
                        print(f"🎉 [SIMPLE IMAGES] Recognition ID: {recognition_id}")
                        print(f"🎉 [SIMPLE IMAGES] Generated {len(ingredient_images)} images")
                        print(f"🎉 [SIMPLE IMAGES] ✨ FRONTEND NOTIFICATION: Images ready for recognition {recognition_id}")
                        print(f"🎉 [SIMPLE IMAGES] ===== GENERATION SUCCESS =====")
                    
                except Exception as e:
                    import traceback
                    print(f"🚨 [SIMPLE IMAGES] ===== IMAGE GENERATION FAILED =====")
                    print(f"🚨 [SIMPLE IMAGES] Recognition ID: {recognition_id}")
                    print(f"🚨 [SIMPLE IMAGES] Error: {str(e)}")
                    print(f"🚨 [SIMPLE IMAGES] Error type: {type(e).__name__}")
                    print(f"🚨 [SIMPLE IMAGES] FULL TRACEBACK:")
                    print(traceback.format_exc())
                    print(f"🚨 [SIMPLE IMAGES] ===== GENERATION FAILURE =====")
        
        # Lanzar en background
        self.executor.submit(background_simple_generation)
        print(f"🎯 [SIMPLE IMAGES] Image generation queued for recognition {recognition_id}")

    def run_simple_food_image_generation(self, recognition_id: str, user_uid: str, foods: List[dict], 
                                       food_image_generator_service, recognition_repository):
        """
        Ejecuta generación simple de imágenes para reconocimiento de comidas sin task tracking complejo.
        Actualiza directamente el reconocimiento en la base de datos.
        """
        
        # Capturar el app context actual
        from flask import current_app
        app = current_app._get_current_object()
        
        def background_food_image_generation():
            with app.app_context():
                print(f"🎨 [SIMPLE FOOD IMAGES] ===== STARTING FOOD IMAGE GENERATION =====")
                print(f"🎨 [SIMPLE FOOD IMAGES] Recognition ID: {recognition_id}")
                print(f"🎨 [SIMPLE FOOD IMAGES] User: {user_uid}")
                print(f"🎨 [SIMPLE FOOD IMAGES] Foods to process: {len(foods)}")
                
                try:
                    generated_count = 0
                    updated_foods = []
                    
                    # Generar imagen para cada comida en paralelo
                    for i, food in enumerate(foods):
                        try:
                            food_name = food.get("name", f"food_{i}")
                            description = food.get("description", "")
                            main_ingredients = food.get("main_ingredients", [])
                            
                            print(f"🎨 [SIMPLE FOOD IMAGES] Processing {i+1}/{len(foods)}: {food_name}")
                            
                            # Generar imagen para la comida
                            image_url = food_image_generator_service.get_or_generate_food_image(
                                food_name=food_name,
                                user_uid=user_uid,
                                description=description,
                                main_ingredients=main_ingredients
                            )
                            
                            if image_url:
                                food["image_path"] = image_url
                                generated_count += 1
                                print(f"✅ [SIMPLE FOOD IMAGES] Generated image for: {food_name}")
                            else:
                                print(f"❌ [SIMPLE FOOD IMAGES] Failed to generate image for: {food_name}")
                            
                            updated_foods.append(food)
                            
                        except Exception as e:
                            print(f"🚨 [SIMPLE FOOD IMAGES] Error generating image for food {i}: {str(e)}")
                            updated_foods.append(food)  # Añadir sin imagen
                            continue
                    
                    # Actualizar el reconocimiento en la base de datos
                    print(f"💾 [SIMPLE FOOD IMAGES] Updating recognition with {generated_count} images...")
                    
                    recognition = recognition_repository.find_by_uid(recognition_id)
                    if recognition:
                        # Actualizar los datos del reconocimiento con las imágenes
                        updated_result = recognition.raw_result.copy()
                        updated_result["foods"] = updated_foods
                        
                        recognition.raw_result = updated_result
                        recognition_repository.update(recognition)
                        
                        print(f"✅ [SIMPLE FOOD IMAGES] Updated existing recognition: {recognition_id}")
                        print(f"💾 [SIMPLE FOOD IMAGES] Recognition {recognition_id} updated successfully")
                    else:
                        print(f"❌ [SIMPLE FOOD IMAGES] Recognition {recognition_id} not found for update")
                    
                    print(f"🎉 [SIMPLE FOOD IMAGES] ===== FOOD IMAGE GENERATION COMPLETED =====")
                    print(f"🎉 [SIMPLE FOOD IMAGES] Recognition ID: {recognition_id}")
                    print(f"🎉 [SIMPLE FOOD IMAGES] Generated {generated_count} images")
                    print(f"🎉 [SIMPLE FOOD IMAGES] ✨ FRONTEND NOTIFICATION: Food images ready for recognition {recognition_id}")
                    print(f"🎉 [SIMPLE FOOD IMAGES] ===== GENERATION SUCCESS =====")
                    
                except Exception as e:
                    print(f"🚨 [SIMPLE FOOD IMAGES] Critical error: {str(e)}")
                    import traceback
                    print(f"🚨 [SIMPLE FOOD IMAGES] Traceback: {traceback.format_exc()}")
        
        # Lanzar en background
        self.executor.submit(background_food_image_generation)
        print(f"🎯 [SIMPLE FOOD IMAGES] Task queued for background processing")

    def run_async_image_generation(self, task_id: str, user_uid: str, ingredients: List[dict], 
                                 ingredient_image_generator_service, calculator_service, 
                                 recognition_repository, recognition_id: str):
        """
        Ejecuta la generación asíncrona de imágenes para ingredientes.
        """
        """Ejecuta generación de imágenes de ingredientes en background"""
        
        # Capturar el app context actual
        from flask import current_app
        app = current_app._get_current_object()
        
        def background_image_generation():
            with app.app_context():
                print(f"🎨 [ASYNC IMAGES] Starting background image generation for task {task_id}")
                
                try:
                    # Paso 1: Actualizar estado - iniciando
                    self.update_task_progress(task_id, 5, "Iniciando generación de imágenes...", "processing")
                    
                    # Paso 2: Generar imágenes en paralelo
                    current_time = datetime.now(timezone.utc)
                    self.update_task_progress(task_id, 10, "Generando imágenes de ingredientes...")
                    
                    def generate_ingredient_image(ingredient_data):
                        ingredient, user_uid = ingredient_data
                        ingredient_name = ingredient["name"]
                        descripcion = ingredient.get("description", "")
                        
                        try:
                            image_path = ingredient_image_generator_service.get_or_generate_ingredient_image(
                                ingredient_name=ingredient_name,
                                user_uid=user_uid,
                                descripcion=descripcion
                            )
                            return ingredient_name, image_path, None
                        except Exception as e:
                            return ingredient_name, "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image", str(e)
                    
                    # Generación paralela de imágenes
                    ingredient_images = {}
                    total_ingredients = len(ingredients)
                    
                    with ThreadPoolExecutor(max_workers=3) as image_executor:
                        thread_data = [(ingredient, user_uid) for ingredient in ingredients]
                        
                        future_to_ingredient = {
                            image_executor.submit(generate_ingredient_image, data): data[0]["name"] 
                            for data in thread_data
                        }
                        
                        completed_images = 0
                        for future in future_to_ingredient:
                            ingredient_name, image_path, error = future.result()
                            ingredient_images[ingredient_name] = image_path
                            completed_images += 1
                            
                            # Actualizar progreso dinámicamente
                            progress = 10 + (completed_images * 70 // total_ingredients)
                            self.update_task_progress(task_id, progress, f"✅ Imagen generada para {ingredient_name}")
                            if error:
                                print(f"⚠️ [ASYNC IMAGES] Warning generating image for {ingredient_name}: {error}")
                    
                    # Paso 3: Actualizar ingredientes con imágenes
                    self.update_task_progress(task_id, 85, "Actualizando datos con imágenes...")
                    
                    # Preparar datos actualizados
                    updated_ingredients = []
                    for ingredient in ingredients:
                        ingredient_name = ingredient["name"]
                        
                        # Asignar imagen generada
                        ingredient["image_path"] = ingredient_images.get(ingredient_name, "https://via.placeholder.com/150x150/cccccc/666666?text=No+Image")
                        ingredient["image_status"] = "ready"
                        
                        updated_ingredients.append(ingredient)
                    
                    # Paso 4: Actualizar reconocimiento en base de datos
                    self.update_task_progress(task_id, 90, "Guardando imágenes en base de datos...")
                    
                    try:
                        # Obtener el reconocimiento original
                        from src.domain.models.recognition import Recognition
                        print(f"🔍 [ASYNC IMAGES] Looking for recognition: {recognition_id}")
                        recognition = recognition_repository.find_by_uid(recognition_id)
                        
                        if recognition:
                            print(f"✅ [ASYNC IMAGES] Found recognition, updating with {len(updated_ingredients)} ingredients")
                            # Actualizar el raw_result con las imágenes
                            updated_result = recognition.raw_result.copy()
                            updated_result['ingredients'] = updated_ingredients
                            
                            # Guardar actualización
                            recognition.raw_result = updated_result
                            recognition_repository.save(recognition)
                            print(f"✅ [ASYNC IMAGES] Successfully updated recognition {recognition_id} with images")
                        else:
                            print(f"⚠️ [ASYNC IMAGES] Recognition {recognition_id} not found for update")
                            
                    except Exception as e:
                        print(f"⚠️ [ASYNC IMAGES] Error updating recognition: {str(e)}")
                        print(f"🔍 [ASYNC IMAGES] Recognition ID: {recognition_id}")
                        print(f"🔍 [ASYNC IMAGES] Task ID: {task_id}")
                        # No fallar por esto, las imágenes están en el resultado de la tarea
                    
                    # Paso 5: Completar tarea con imágenes
                    self.update_task_progress(task_id, 95, "Finalizando generación de imágenes...")
                    
                    result_data = {
                        "recognition_id": recognition_id,
                        "ingredients": updated_ingredients,
                        "images_generated": len(ingredient_images),
                        "total_ingredients": total_ingredients,
                        "completed_at": current_time.isoformat()
                    }
                    
                    self.complete_task(task_id, result_data)
                    
                    print(f"🎉 [ASYNC IMAGES] Task {task_id} completed successfully - {len(ingredient_images)} images generated")
                    
                except Exception as e:
                    print(f"🚨 [ASYNC IMAGES] Task {task_id} failed: {str(e)}")
                    self.fail_task(task_id, str(e))
        
        # Lanzar en background
        self.executor.submit(background_image_generation)
        print(f"🎯 [ASYNC IMAGES] Task {task_id} queued for background image processing")


    def run_async_food_image_generation(self, task_id: str, user_uid: str, foods: List[dict], 
                                      food_image_generator_service, calculator_service, 
                                      recognition_repository, recognition_id: str):
        """
        Ejecuta la generación asíncrona de imágenes para platos de comida.
        """
        from flask import current_app
        app = current_app._get_current_object()
        
        def background_food_image_generation():
            with app.app_context():
                print(f"🍽️ [ASYNC FOOD IMAGES] Starting background food image generation for task {task_id}")
                
                try:
                    # Paso 1: Actualizar estado - iniciando
                    self.update_task_progress(task_id, 5, "Iniciando generación de imágenes de platos...", "processing")
                    
                    # Paso 2: Generar imágenes en paralelo
                    current_time = datetime.now(timezone.utc)
                    self.update_task_progress(task_id, 10, "Generando imágenes de platos de comida...")
                    
                    def generate_food_image(food_data):
                        food, user_uid = food_data
                        food_name = food["name"]
                        description = food.get("description", "")
                        main_ingredients = food.get("main_ingredients", [])
                        
                        try:
                            image_path = food_image_generator_service.get_or_generate_food_image(
                                food_name=food_name,
                                user_uid=user_uid,
                                description=description,
                                main_ingredients=main_ingredients
                            )
                            return food_name, image_path, None
                        except Exception as e:
                            return food_name, "https://via.placeholder.com/300x300/e8f5e8/666666?text=No+Image", str(e)
                    
                    # Generación paralela de imágenes
                    food_images = {}
                    total_foods = len(foods)
                    
                    with ThreadPoolExecutor(max_workers=3) as image_executor:
                        thread_data = [(food, user_uid) for food in foods]
                        
                        future_to_food = {
                            image_executor.submit(generate_food_image, data): data[0]["name"] 
                            for data in thread_data
                        }
                        
                        completed_images = 0
                        for future in future_to_food:
                            food_name, image_path, error = future.result()
                            food_images[food_name] = image_path
                            completed_images += 1
                            
                            # Actualizar progreso dinámicamente
                            progress = 10 + (completed_images * 70 // total_foods)
                            self.update_task_progress(task_id, progress, f"✅ Imagen generada para {food_name}")
                            if error:
                                print(f"⚠️ [ASYNC FOOD IMAGES] Warning generating image for {food_name}: {error}")
                    
                    # Paso 3: Actualizar foods con imágenes
                    self.update_task_progress(task_id, 85, "Actualizando platos con imágenes...")
                    
                    # Preparar datos actualizados
                    updated_foods = []
                    for food in foods:
                        food_name = food["name"]
                        
                        # Asignar imagen generada
                        food["image_path"] = food_images.get(food_name, "https://via.placeholder.com/300x300/e8f5e8/666666?text=No+Image")
                        food["image_status"] = "ready"
                        
                        updated_foods.append(food)
                    
                    # Paso 4: Actualizar reconocimiento en base de datos
                    self.update_task_progress(task_id, 90, "Guardando imágenes en base de datos...")
                    
                    try:
                        # Obtener el reconocimiento original
                        from src.domain.models.recognition import Recognition
                        print(f"🔍 [ASYNC FOOD IMAGES] Looking for recognition: {recognition_id}")
                        recognition = recognition_repository.find_by_uid(recognition_id)
                        
                        if recognition:
                            print(f"✅ [ASYNC FOOD IMAGES] Found recognition, updating with {len(updated_foods)} foods")
                            # Actualizar el raw_result con las imágenes
                            updated_result = recognition.raw_result.copy()
                            updated_result['foods'] = updated_foods
                            
                            # Guardar actualización
                            recognition.raw_result = updated_result
                            recognition_repository.save(recognition)
                            print(f"✅ [ASYNC FOOD IMAGES] Successfully updated recognition {recognition_id} with food images")
                        else:
                            print(f"⚠️ [ASYNC FOOD IMAGES] Recognition {recognition_id} not found for update")
                            
                    except Exception as e:
                        print(f"⚠️ [ASYNC FOOD IMAGES] Error updating recognition: {str(e)}")
                        print(f"🔍 [ASYNC FOOD IMAGES] Recognition ID: {recognition_id}")
                        print(f"🔍 [ASYNC FOOD IMAGES] Task ID: {task_id}")
                        # No fallar por esto, las imágenes están en el resultado de la tarea
                    
                    # Paso 5: Completar tarea con imágenes
                    self.update_task_progress(task_id, 95, "Finalizando generación de imágenes de platos...")
                    
                    result_data = {
                        "recognition_id": recognition_id,
                        "foods": updated_foods,
                        "images_generated": len(food_images),
                        "total_foods": total_foods,
                        "completed_at": current_time.isoformat()
                    }
                    
                    self.complete_task(task_id, result_data)
                    
                    print(f"🎉 [ASYNC FOOD IMAGES] Task {task_id} completed successfully - {len(food_images)} images generated")
                    
                except Exception as e:
                    print(f"🚨 [ASYNC FOOD IMAGES] Task {task_id} failed: {str(e)}")
                    self.fail_task(task_id, str(e))
        
        # Lanzar en background
        self.executor.submit(background_food_image_generation)
        print(f"🎯 [ASYNC FOOD IMAGES] Task {task_id} queued for background food image processing")

    def run_async_recipe_image_generation(self, task_id: str, user_uid: str, recipes: List[dict],
                                          recipe_image_generator_service,
                                          generation_repository, generation_id: str):
        """
        Ejecuta la generación asíncrona de imágenes para recetas generadas y actualiza la tabla Generation.
        """
        from flask import current_app
        app = current_app._get_current_object()

        def background_recipe_image_generation():
            with app.app_context():
                print(f"👩‍🍳 [ASYNC RECIPE IMAGES] Starting background recipe image generation for task {task_id}")

                try:
                    self.update_task_progress(task_id, 5, "Iniciando generación de imágenes de recetas...",
                                              "processing")
                    current_time = datetime.now(timezone.utc)

                    def generate_recipe_image(recipe_data):
                        recipe, user_uid = recipe_data
                        recipe_title = recipe["title"]
                        description = recipe.get("description", "")
                        ingredients = recipe.get("ingredients", [])

                        try:
                            image_path = recipe_image_generator_service.get_or_generate_recipe_image(
                                recipe_title=recipe_title,
                                user_uid=user_uid,
                                description=description,
                                ingredients=ingredients
                            )
                            return recipe_title, image_path, None
                        except Exception as e:
                            return recipe_title, "https://via.placeholder.com/300x300/fde3e3/666666?text=No+Image", str(
                                e)

                    recipe_images = {}
                    total_recipes = len(recipes)

                    with ThreadPoolExecutor(max_workers=3) as image_executor:
                        thread_data = [(recipe, user_uid) for recipe in recipes]

                        future_to_recipe = {
                            image_executor.submit(generate_recipe_image, data): data[0]["title"]
                            for data in thread_data
                        }

                        completed_images = 0
                        for future in future_to_recipe:
                            recipe_title, image_path, error = future.result()
                            recipe_images[recipe_title] = image_path
                            completed_images += 1

                            progress = 10 + (completed_images * 70 // total_recipes)
                            self.update_task_progress(task_id, progress, f"✅ Imagen generada para {recipe_title}")
                            if error:
                                print(f"⚠️ [ASYNC RECIPE IMAGES] Warning generating image for {recipe_title}: {error}")

                    self.update_task_progress(task_id, 85, "Actualizando recetas con imágenes...")

                    # Modificar recetas in-place
                    for recipe in recipes:
                        recipe_title = recipe["title"]
                        recipe["image_path"] = recipe_images.get(recipe_title)
                        recipe["image_status"] = "ready"

                    # 🔄 Actualizar generación en base de datos
                    try:
                        print(f"🔄 [GENERATION UPDATE] Buscando generación {generation_id}")
                        generation = generation_repository.find_by_uid(generation_id)
                        if generation:
                            print(f"✅ [GENERATION UPDATE] Actualizando generación con imágenes")
                            updated_result = generation.raw_result.copy()
                            updated_result["generated_recipes"] = recipes
                            generation.raw_result = updated_result
                            generation_repository.save(generation)
                        else:
                            print(f"⚠️ [GENERATION UPDATE] No se encontró la generación {generation_id}")
                    except Exception as e:
                        print(f"⚠️ [GENERATION UPDATE] Error actualizando generación: {str(e)}")

                    self.update_task_progress(task_id, 95, "Finalizando generación de imágenes de recetas...")

                    result_data = {
                        "generation_id": generation_id,
                        "recipes": recipes,
                        "images_generated": len(recipe_images),
                        "total_recipes": total_recipes,
                        "completed_at": current_time.isoformat()
                    }

                    self.complete_task(task_id, result_data)
                    print(
                        f"🎉 [ASYNC RECIPE IMAGES] Task {task_id} completed successfully - {len(recipe_images)} images generated")

                except Exception as e:
                    print(f"🚨 [ASYNC RECIPE IMAGES] Task {task_id} failed: {str(e)}")
                    self.fail_task(task_id, str(e))

        self.executor.submit(background_recipe_image_generation)
        print(f"🎯 [ASYNC RECIPE IMAGES] Task {task_id} queued for background recipe image processing")


# Instancia global
async_task_service = AsyncTaskService() 