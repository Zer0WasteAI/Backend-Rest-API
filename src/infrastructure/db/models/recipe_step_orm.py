from src.infrastructure.db.base import db
class RecipeStepORM(db.Model):
    __tablename__ = "recipe_steps"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes.uid"), nullable=False)
    step_order = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(255), nullable=False)

    recipe = db.relationship("RecipeORM", back_populates="steps")
