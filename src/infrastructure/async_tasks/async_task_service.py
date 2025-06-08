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
        
        print(f"🆕 [ASYNC TASK] Created task {task_id} for user {user_uid}")
        return task_id
    
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
        except Exception as e:
            print(f"🚨 [ASYNC TASK] Error completing task {task_id}: {str(e)}")
    
    def fail_task(self, task_id: str, error_message: str):
        """Marca una tarea como fallida"""
        try:
            from flask import current_app
            with current_app.app_context():
                task = AsyncTaskORM.query.filter_by(task_id=task_id).first()
                if task:
                    task.status = 'failed'
                    task.current_step = 'Error en procesamiento'
                    task.error_message = error_message
                    task.completed_at = datetime.now(timezone.utc)
                    
                    db.session.commit()
                    print(f"❌ [ASYNC TASK] Failed task {task_id}: {error_message}")
        except Exception as e:
            print(f"🚨 [ASYNC TASK] Error failing task {task_id}: {str(e)}")
    
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
                print(f"🚀 [ASYNC RECOGNITION] Starting background processing for task {task_id}")
                
                try:
                    # Paso 1: Actualizar estado - iniciando
                    self.update_task_progress(task_id, 5, "Preparando imágenes...", "processing")
                    
                    # Paso 2: Cargar imágenes
                    images_files = []
                    for i, path in enumerate(images_paths):
                        file = storage_adapter.get_image(path)
                        images_files.append(file)
                        progress = 5 + (i + 1) * 10 // len(images_paths)
                        self.update_task_progress(task_id, progress, f"Cargando imagen {i+1}/{len(images_paths)}")
                    
                    # Paso 3: Reconocimiento AI básico
                    self.update_task_progress(task_id, 20, "Detectando ingredientes con IA...")
                    result = ai_service.recognize_ingredients(images_files)
                    
                    # Paso 4: Guardar reconocimiento básico
                    self.update_task_progress(task_id, 40, "Guardando datos de reconocimiento...")
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
                    
                    # Paso 5: Generar imágenes en paralelo
                    current_time = datetime.now(timezone.utc)
                    self.update_task_progress(task_id, 50, "Generando imágenes de ingredientes...")
                    
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
                    total_ingredients = len(result['ingredients'])
                    
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
                            
                            # Actualizar progreso dinámicamente
                            progress = 50 + (completed_images * 30 // total_ingredients)
                            self.update_task_progress(task_id, progress, f"Imagen generada para {ingredient_name}")
                    
                    # Paso 6: Finalizar datos de cada ingrediente
                    self.update_task_progress(task_id, 85, "Finalizando datos de ingredientes...")
                    
                    for ingredient in result["ingredients"]:
                        ingredient_name = ingredient["name"]
                        
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
                        except Exception as e:
                            from datetime import timedelta
                            fallback_date = current_time + timedelta(days=ingredient.get("expiration_time", 7))
                            ingredient["expiration_date"] = fallback_date.isoformat()
                        
                        ingredient["added_at"] = current_time.isoformat()
                    
                    # Paso 7: Completar tarea
                    self.update_task_progress(task_id, 95, "Guardando resultado final...")
                    self.complete_task(task_id, result)
                    
                    print(f"🎉 [ASYNC RECOGNITION] Task {task_id} completed successfully with {len(result['ingredients'])} ingredients")
                    
                except Exception as e:
                    print(f"🚨 [ASYNC RECOGNITION] Task {task_id} failed: {str(e)}")
                    self.fail_task(task_id, str(e))
        
        # Lanzar en background
        self.executor.submit(background_recognition)
        print(f"🎯 [ASYNC RECOGNITION] Task {task_id} queued for background processing")

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
                        recognition = recognition_repository.find_by_uid(recognition_id)
                        
                        if recognition:
                            # Actualizar el raw_result con las imágenes
                            updated_result = recognition.raw_result.copy()
                            updated_result['ingredients'] = updated_ingredients
                            
                            # Guardar actualización
                            recognition.raw_result = updated_result
                            recognition_repository.save(recognition)
                            print(f"✅ [ASYNC IMAGES] Updated recognition {recognition_id} with images")
                        else:
                            print(f"⚠️ [ASYNC IMAGES] Recognition {recognition_id} not found for update")
                            
                    except Exception as e:
                        print(f"⚠️ [ASYNC IMAGES] Error updating recognition: {str(e)}")
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
                        recognition = recognition_repository.find_by_uid(recognition_id)
                        
                        if recognition:
                            # Actualizar el raw_result con las imágenes
                            updated_result = recognition.raw_result.copy()
                            updated_result['foods'] = updated_foods
                            
                            # Guardar actualización
                            recognition.raw_result = updated_result
                            recognition_repository.save(recognition)
                            print(f"✅ [ASYNC FOOD IMAGES] Updated recognition {recognition_id} with food images")
                        else:
                            print(f"⚠️ [ASYNC FOOD IMAGES] Recognition {recognition_id} not found for update")
                            
                    except Exception as e:
                        print(f"⚠️ [ASYNC FOOD IMAGES] Error updating recognition: {str(e)}")
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


# Instancia global
async_task_service = AsyncTaskService() 