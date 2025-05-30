from typing import Optional
from sqlalchemy import select
from src.domain.models.inventory import Inventory
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem
from src.domain.repositories.inventory_repository import InventoryRepository
from src.infrastructure.db.models.ingredient_stack_orm import IngredientStackORM
from src.infrastructure.db.models.food_item_orm import FoodItemORM
from src.infrastructure.db.models.inventory_orm import InventoryORM

class InventoryRepositoryImpl(InventoryRepository):
    def __init__(self, db):
        self.db = db

    def get_by_user_uid(self, user_uid: str) -> Optional[Inventory]:
        inventory = Inventory(user_uid)

        # Ingredientes
        stmt = select(IngredientStackORM).where(IngredientStackORM.inventory_user_uid == user_uid)
        ingredient_stacks = self.db.session.execute(stmt).scalars().all()
        for stack in ingredient_stacks:
            inventory.add_ingredient_stack(
                name=stack.ingredient_name,
                stack=IngredientStack(stack.quantity, stack.expiration_date, stack.added_at),
                type_unit=stack.type_unit,
                storage_type=stack.storage_type,
                tips=stack.tips,
                image_path=stack.image_path
            )

        # Platos
        stmt = select(FoodItemORM).where(FoodItemORM.inventory_user_uid == user_uid)
        food_items = self.db.session.execute(stmt).scalars().all()
        for item in food_items:
            food = FoodItem(
                name=item.name,
                main_ingredients=item.main_ingredients,
                category=item.category,
                calories=item.calories,
                description=item.description,
                storage_type=item.storage_type,
                expiration_time=item.expiration_time,
                time_unit=item.time_unit,
                tips=item.tips,
                serving_quantity=item.serving_quantity,
                image_path=item.image_path,
                added_at=item.added_at,
                expiration_date=item.expiration_date
            )
            inventory.add_food_item(food)

        return inventory

    def save(self, inventory: Inventory) -> None:
        if not self.db.session.get(InventoryORM, inventory.user_uid):
            self.db.session.add(InventoryORM(user_uid=inventory.user_uid))
        self.db.session.commit()

    def update(self, inventory: Inventory) -> None:
        self._clear_existing(inventory.user_uid)
        self._insert_new_data(inventory)
        self.db.session.commit()

    def _clear_existing(self, user_uid: str):
        self.db.session.query(IngredientStackORM).filter_by(inventory_user_uid=user_uid).delete()
        self.db.session.query(FoodItemORM).filter_by(inventory_user_uid=user_uid).delete()

    def _insert_new_data(self, inventory: Inventory):
        for ing in inventory.ingredients.values():
            for stack in ing.stacks:
                self.db.session.add(IngredientStackORM(
                    inventory_user_uid=inventory.user_uid,
                    ingredient_name=ing.name,
                    quantity=stack.quantity,
                    expiration_date=stack.expiration_date,
                    added_at=stack.added_at,
                    type_unit=ing.type_unit,
                    storage_type=ing.storage_type,
                    tips=ing.tips,
                    image_path=ing.image_path
                ))

        for food in inventory.foods:
            self.db.session.add(FoodItemORM(
                inventory_user_uid=inventory.user_uid,
                name=food.name,
                main_ingredients=food.main_ingredients,
                category=food.category,
                calories=food.calories,
                description=food.description,
                storage_type=food.storage_type,
                expiration_time=food.expiration_time,
                time_unit=food.time_unit,
                tips=food.tips,
                serving_quantity=food.serving_quantity,
                image_path=food.image_path,
                added_at=food.added_at,
                expiration_date=food.expiration_date
            ))
