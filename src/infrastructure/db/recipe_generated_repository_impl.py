from typing import List, Optional, Dict, Any
import uuid
from src.infrastructure.db.models.recipe_generated_orm import RecipeGeneratedORM
from src.infrastructure.db.base import db


class RecipeGeneratedRepositoryImpl:
    
    def save_generated_recipe(self, user_uid: str, generation_id: str, 
                             recipe_data: Dict[str, Any], generation_type: str) -> str:
        """
        Guarda una receta generada automáticamente
        """
        recipe_uid = str(uuid.uuid4())
        
        recipe_generated = RecipeGeneratedORM(
            uid=recipe_uid,
            user_uid=user_uid,
            generation_id=generation_id,
            title=recipe_data.get('name', recipe_data.get('title', 'Receta sin título')),
            description=recipe_data.get('description', ''),
            duration=str(recipe_data.get('prep_time', recipe_data.get('duration', ''))),
            difficulty=recipe_data.get('difficulty', ''),
            servings=recipe_data.get('servings'),
            category=recipe_data.get('meal_type', recipe_data.get('category', '')),
            recipe_data=recipe_data,  # Almacena toda la receta en JSON
            generation_type=generation_type,
            image_path=recipe_data.get('image_path'),
            image_status=recipe_data.get('image_status', 'generating')
        )
        
        db.session.add(recipe_generated)
        db.session.commit()
        
        return recipe_uid
    
    def find_by_user_and_title(self, user_uid: str, title: str) -> Optional[RecipeGeneratedORM]:
        """
        Busca una receta generada por usuario y título exacto
        """
        return db.session.query(RecipeGeneratedORM).filter(
            RecipeGeneratedORM.user_uid == user_uid,
            RecipeGeneratedORM.title == title
        ).first()
    
    def find_by_user_and_title_fuzzy(self, user_uid: str, title: str) -> Optional[RecipeGeneratedORM]:
        """
        Busca una receta generada por usuario y título (búsqueda difusa)
        """
        return db.session.query(RecipeGeneratedORM).filter(
            RecipeGeneratedORM.user_uid == user_uid,
            RecipeGeneratedORM.title.ilike(f'%{title}%')
        ).first()
    
    def find_by_generation_id(self, generation_id: str) -> List[RecipeGeneratedORM]:
        """
        Obtiene todas las recetas de una generación específica
        """
        return db.session.query(RecipeGeneratedORM).filter(
            RecipeGeneratedORM.generation_id == generation_id
        ).all()
    
    def find_by_user(self, user_uid: str, limit: int = 50) -> List[RecipeGeneratedORM]:
        """
        Obtiene las recetas generadas más recientes de un usuario
        """
        return db.session.query(RecipeGeneratedORM).filter(
            RecipeGeneratedORM.user_uid == user_uid
        ).order_by(RecipeGeneratedORM.generated_at.desc()).limit(limit).all()
    
    def update_image_status(self, recipe_uid: str, image_path: str, image_status: str):
        """
        Actualiza el estado de la imagen de una receta generada
        """
        recipe = db.session.query(RecipeGeneratedORM).filter(
            RecipeGeneratedORM.uid == recipe_uid
        ).first()
        
        if recipe:
            recipe.image_path = image_path
            recipe.image_status = image_status
            db.session.commit() 