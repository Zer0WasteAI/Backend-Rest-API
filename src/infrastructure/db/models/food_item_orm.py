from datetime import datetime, timezone
from src.infrastructure.db.base import db

class FoodItemORM(db.Model):
    __tablename__ = "food_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inventory_user_uid = db.Column(db.String(36), db.ForeignKey("inventories.user_uid"))

    name = db.Column(db.String(100), nullable=False)
    main_ingredients = db.Column(db.JSON)  # lista de strings
    category = db.Column(db.String(50))
    calories = db.Column(db.Float)
    description = db.Column(db.Text)
    storage_type = db.Column(db.String(50))
    expiration_time = db.Column(db.Integer)
    time_unit = db.Column(db.String(20))
    tips = db.Column(db.Text)
    serving_quantity = db.Column(db.Integer)
    image_path = db.Column(db.String(1000))
    added_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    expiration_date = db.Column(db.DateTime, nullable=False)
