from src.infrastructure.db.base import db

class ProfileUser(db.Model):
    __tablename__ = "profile_users"
    uid = db.Column(db.String(36), db.ForeignKey("users.uid"), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    photo_url = db.Column(db.String(255), default="")
    prefs = db.Column(db.JSON, default=[])


