from src.infrastructure.db.base import db
class RecipeIngredientORM(db.Model):
    __tablename__ = "recipe_ingredients"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes.uid"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    type_unit = db.Column(db.String(50), nullable=False)

    recipe = db.relationship("RecipeORM", back_populates="ingredients")
