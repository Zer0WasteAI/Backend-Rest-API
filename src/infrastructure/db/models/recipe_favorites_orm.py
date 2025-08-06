from src.infrastructure.db.base import db
from datetime import datetime, timezone

class RecipeFavoritesORM(db.Model):
    __tablename__ = "recipe_favorites"

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)
    recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes_generated.uid"), nullable=False)
    
    # Optional metadata
    rating = db.Column(db.Integer, nullable=True)  # 1-5 stars
    notes = db.Column(db.Text(500), nullable=True)
    favorited_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    
    # Relaciones
    user = db.relationship("User", backref=db.backref("recipe_favorites", lazy=True))
    recipe = db.relationship("RecipeGeneratedORM", backref=db.backref("favorites", lazy=True))
    
    # Índice compuesto para evitar duplicados
    __table_args__ = (
        db.UniqueConstraint('user_uid', 'recipe_uid', name='unique_user_recipe_favorite'),
    )
    
    def __repr__(self):
        return f'<RecipeFavorite {self.uid}: User {self.user_uid} -> Recipe {self.recipe_uid}>'