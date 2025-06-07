from src.infrastructure.db.base import db

class RecipeORM(db.Model):
    __tablename__ = "recipes"

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)

    title = db.Column(db.String(255), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    footer = db.Column(db.String(255), nullable=True)
    generated_by_ai = db.Column(db.Boolean, default=True)

    ingredients = db.relationship("RecipeIngredientORM", back_populates="recipe", cascade="all, delete-orphan")
    steps = db.relationship("RecipeStepORM", back_populates="recipe", cascade="all, delete-orphan")

    user = db.relationship("User", backref=db.backref("recipes", lazy=True))
