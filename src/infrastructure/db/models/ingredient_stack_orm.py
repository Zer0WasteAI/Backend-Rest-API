from datetime import datetime, timezone
from src.infrastructure.db.base import db

class IngredientStackORM(db.Model):
    __tablename__ = "ingredient_stacks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inventory_user_uid = db.Column(db.String(36), db.ForeignKey("inventories.user_uid"))

    ingredient_name = db.Column(db.String(100))  # agrupa stacks por nombre
    quantity = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    type_unit = db.Column(db.String(20), nullable=False)
    storage_type = db.Column(db.String(50))
    tips = db.Column(db.Text)
    image_path = db.Column(db.String(255))
