from src.infrastructure.db.base import db
from datetime import date, datetime, timezone

class DailyMealPlanORM(db.Model):
    __tablename__ = "daily_meal_plans"

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)
    date = db.Column(db.Date, nullable=False, index=True, unique=False)

    breakfast_recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes.uid"), nullable=True)
    lunch_recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes.uid"), nullable=True)
    dinner_recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes.uid"), nullable=True)
    dessert_recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes.uid"), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc), nullable=False)

    # Relaciones
    user = db.relationship("User", backref=db.backref("meal_plans", lazy=True))

    breakfast_recipe = db.relationship("RecipeORM", foreign_keys=[breakfast_recipe_uid])
    lunch_recipe = db.relationship("RecipeORM", foreign_keys=[lunch_recipe_uid])
    dinner_recipe = db.relationship("RecipeORM", foreign_keys=[dinner_recipe_uid])
    dessert_recipe = db.relationship("RecipeORM", foreign_keys=[dessert_recipe_uid])

    __table_args__ = (
        db.UniqueConstraint("user_uid", "date", name="uq_user_date_mealplan"),
    )
