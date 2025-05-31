from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.db.base import db

class IngredientORM(db.Model):
    __tablename__ = "ingredients"

    name = db.Column(db.String(100), primary_key=True)
    inventory_user_uid = db.Column(db.String(100), ForeignKey("inventories.user_uid"), primary_key=True)

    type_unit = db.Column(db.String(50), nullable=False)
    storage_type = db.Column(db.String(50), nullable=False)
    tips = db.Column(db.String(255), nullable=True)
    image_path = db.Column(db.String(255), nullable=False)

    inventory = relationship("InventoryORM", back_populates="ingredients")
    stacks = relationship("IngredientStackORM", back_populates="ingredient", cascade="all, delete-orphan")