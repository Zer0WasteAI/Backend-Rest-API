from src.infrastructure.db.base import db
from datetime import datetime, timezone
from src.infrastructure.db.models.user_favorite_recipes import user_favorite_recipes

class RecipeORM(db.Model):
    __tablename__ = "recipes"

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    footer = db.Column(db.String(255), nullable=True)
    generated_by_ai = db.Column(db.Boolean, default=True)
    saved_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=True)
    image_status = db.Column(db.String(50), default="generating", nullable=True)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text(300), nullable=False)
    image_path = db.Column(db.String(1000), nullable=True)

    ingredients = db.relationship("RecipeIngredientORM", back_populates="recipe", cascade="all, delete-orphan")
    steps = db.relationship("RecipeStepORM", back_populates="recipe", cascade="all, delete-orphan")
    user = db.relationship("User", backref=db.backref("saved_recipes", lazy=True))
    favorited_by = db.relationship(
        'User',
        secondary=user_favorite_recipes,
        back_populates='favorite_recipes',
        lazy='dynamic'
    )
