from src.infrastructure.db.base import db
from datetime import datetime, timezone

class RecipeGeneratedORM(db.Model):
    __tablename__ = "recipes_generated"

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)
    generation_id = db.Column(db.String(36), db.ForeignKey("generations.uid"), nullable=False)
    
    # Campos de la receta
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text(500), nullable=True)
    duration = db.Column(db.String(50), nullable=True)
    difficulty = db.Column(db.String(50), nullable=True)
    servings = db.Column(db.Integer, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    
    # Datos JSON de la receta completa
    recipe_data = db.Column(db.JSON, nullable=False)  # Almacena ingredients, steps, etc.
    
    # Metadata
    generation_type = db.Column(db.String(20), nullable=False)  # 'inventory' o 'custom'
    generated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    image_path = db.Column(db.String(1000), nullable=True)
    image_status = db.Column(db.String(50), default="generating", nullable=True)
    
    # Relaciones
    user = db.relationship("User", backref=db.backref("generated_recipes", lazy=True))
    generation = db.relationship("GenerationORM", backref=db.backref("recipes_generated", lazy=True))
    
    def __repr__(self):
        return f'<RecipeGenerated {self.uid}: {self.title}>' 