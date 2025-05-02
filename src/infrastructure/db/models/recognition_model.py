from src.infrastructure.db.base import db
from datetime import datetime, timezone

class RecognitionORM(db.Model):
    __tablename__ = 'recognitions'

    uid = db.Column(db.String(36), primary_key=True)
    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), nullable=False)
    recognized_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    image_path = db.Column(db.Text, nullable=False)
    raw_result = db.Column(db.JSON)
    is_validated = db.Column(db.Boolean, default=False)
    validated_at = db.Column(db.DateTime, nullable=True)

