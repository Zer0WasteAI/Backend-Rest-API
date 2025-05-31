from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from src.infrastructure.db.base import db

class IngredientStackORM(db.Model):
    __tablename__ = "ingredient_stacks"

    ingredient_name = db.Column(db.String(100), primary_key=True)
    inventory_user_uid = db.Column(db.String(100), primary_key=True)
    added_at = db.Column(DateTime(timezone=True), primary_key=True)

    quantity = db.Column(Float, nullable=False)
    expiration_date = db.Column(DateTime, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['ingredient_name', 'inventory_user_uid'],
            ['ingredients.name', 'ingredients.inventory_user_uid']
        ),
    )

    ingredient = relationship("IngredientORM", back_populates="stacks")
