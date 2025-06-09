from src.infrastructure.db.base import db

class IngredientStackORM(db.Model):
    __tablename__ = "ingredient_stacks"

    ingredient_name = db.Column(db.String(100), primary_key=True)
    inventory_user_uid = db.Column(db.String(100), primary_key=True)
    added_at = db.Column(db.DateTime(timezone=True), primary_key=True)

    quantity = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.DateTime, nullable=False)

    __table_args__ = (
        db.ForeignKeyConstraint(
            ['ingredient_name', 'inventory_user_uid'],
            ['ingredients.name', 'ingredients.inventory_user_uid']
        ),
    )

    ingredient = db.relationship("IngredientORM", back_populates="stacks")
