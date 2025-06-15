from src.infrastructure.db.base import db
from datetime import datetime, timezone

class GenerationORM(db.Model):
    __tablename__ = 'generations'

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.now(timezone.utc), nullable=False)
    generation_type = db.Column(db.String(20), nullable=False)  # 'inventory' o 'custom'
    raw_result = db.Column(db.JSON, nullable=False)
    recipes_ids = db.Column(db.JSON, nullable=True)  # lista de uids de recetas generadas
    is_validated = db.Column(db.Boolean, default=False)
    validated_at = db.Column(db.DateTime, nullable=True)
