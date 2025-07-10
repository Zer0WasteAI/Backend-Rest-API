from src.infrastructure.db.base import db

class ImageReferenceORM(db.Model):
    __tablename__ = 'image_references'

    uid = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    image_path = db.Column(db.String(1000), nullable=False)
    image_type = db.Column(db.String(50), nullable=False)