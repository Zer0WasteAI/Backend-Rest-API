from src.infrastructure.db.base import db

class InventoryORM(db.Model):
    __tablename__ = "inventories"

    user_uid = db.Column(db.String(36), db.ForeignKey("users.uid"), primary_key=True)
    # Relación 1 a 1 con user
    user = db.relationship("User", backref=db.backref("inventory", uselist=False))
