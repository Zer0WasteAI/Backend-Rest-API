from src.infrastructure.db.base import db
from datetime import datetime, timezone


class EnvironmentalSavingsORM(db.Model):
    __tablename__ = "environmental_savings"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)

    user_uid = db.Column(db.String(128), db.ForeignKey("users.uid"), nullable=False)
    recipe_uid = db.Column(db.String(36), db.ForeignKey("recipes.uid"), nullable=False)

    recipe_title = db.Column(db.String(128), default="No title")
    carbon_footprint = db.Column(db.Float, nullable=False)
    water_footprint = db.Column(db.Float, nullable=False)
    energy_footprint = db.Column(db.Float, nullable=False)
    economic_cost = db.Column(db.Float, nullable=False)

    unit_carbon = db.Column(db.String(20), default="kg CO2e")
    unit_water = db.Column(db.String(20), default="litros")
    unit_energy = db.Column(db.String(20), default="MJ")
    unit_cost = db.Column(db.String(20), default="USD")

    is_cooked = db.Column(db.Boolean, default=False)
    saved_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("environmental_savings", lazy=True))
    recipe = db.relationship("RecipeORM", backref=db.backref("environmental_savings", lazy=True))
