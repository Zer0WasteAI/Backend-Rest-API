from datetime import datetime, timezone
from src.infrastructure.db.base import db

class RecipeORM(db.Model):
    __tablename__ = "recipes"

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)

    title = db.Column(db.String(200), nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    ingredients = db.Column(db.JSON, nullable=False)  # Lista de strings
    steps = db.Column(db.JSON, nullable=False)  # Lista de strings
    footer = db.Column(db.Text, nullable=True)
    is_custom = db.Column(db.Boolean, default=False)
    saved_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", backref=db.backref("saved_recipes", lazy=True)) 