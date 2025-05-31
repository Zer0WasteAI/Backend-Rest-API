from typing import Optional
from sqlalchemy import select
from src.domain.models.inventory import Inventory
from src.domain.models.ingredient import Ingredient, IngredientStack
from src.domain.models.food_item import FoodItem
from src.domain.repositories.inventory_repository import InventoryRepository
from src.infrastructure.db.models.ingredient_orm import IngredientORM
from src.infrastructure.db.models.ingredient_stack_orm import IngredientStackORM
from src.infrastructure.db.models.food_item_orm import FoodItemORM
from src.infrastructure.db.models.inventory_orm import InventoryORM

class InventoryRepositoryImpl(InventoryRepository):
    def __init__(self, db):
        self.db = db

    def get_by_user_uid(self, user_uid: str) -> Optional[Inventory]:
        inventory = Inventory(user_uid)

        stmt = select(IngredientORM).where(IngredientORM.inventory_user_uid == user_uid)
        ingredients = self.db.session.execute(stmt).scalars().all()

        for ing in ingredients:
            domain_ing = Ingredient(
                name=ing.name,
                type_unit=ing.type_unit,
                storage_type=ing.storage_type,
                tips=ing.tips,
                image_path=ing.image_path
            )

            for stack in ing.stacks:
                domain_stack = IngredientStack(
                    quantity=stack.quantity,
                    expiration_date=stack.expiration_date,
                    added_at=stack.added_at
                )
                domain_ing.add_stack(domain_stack)

            inventory.ingredients[ing.name] = domain_ing

        return inventory

    def save(self, inventory: Inventory) -> None:
        if not self.db.session.get(InventoryORM, inventory.user_uid):
            self.db.session.add(InventoryORM(user_uid=inventory.user_uid))
        self.db.session.commit()

    def add_ingredient_stack(self, user_uid: str, stack: IngredientStack, ingredient: Ingredient) -> None:

        stmt = select(IngredientORM).where(
            IngredientORM.name == ingredient.name,
            IngredientORM.inventory_user_uid == user_uid
        )
        ingredient_orm = self.db.session.execute(stmt).scalar_one_or_none()

        if not ingredient_orm:
            ingredient_orm = IngredientORM(
                name=ingredient.name,
                type_unit=ingredient.type_unit,
                storage_type=ingredient.storage_type,
                tips=ingredient.tips,
                image_path=ingredient.image_path,
                inventory_user_uid=user_uid
            )
            self.db.session.add(ingredient_orm)
        else:
            ingredient_orm.type_unit = ingredient.type_unit
            ingredient_orm.storage_type = ingredient.storage_type
            ingredient_orm.tips = ingredient.tips
            ingredient_orm.image_path = ingredient.image_path

        stack_orm = IngredientStackORM(
            ingredient_name=ingredient.name,
            added_at=stack.added_at,
            quantity=stack.quantity,
            expiration_date=stack.expiration_date,
            inventory_user_uid=user_uid
        )
        self.db.session.add(stack_orm)
        self.db.session.commit()

    def add_food_item(self, user_uid: str, food_item: FoodItem) -> None:
        return None

    def delete_ingredient_stack(self, user_uid: str, ingredient_name: str, added_at: str) -> None:
        return None

    def delete_food_item(self, user_uid: str, food_name: str, added_at: str) -> None:
        return None

    def update_food_item(self, user_uid: str, food_item: FoodItem) -> None:
        return None

    def update_ingredient_stack(self, user_uid: str, ingredient_name: str, added_at: str, new_stack: IngredientStack, new_meta: Ingredient) -> None:
        return None

    def get_inventory(self, user_uid: str) -> Optional[Inventory]:
        return self.db.session.get(InventoryORM, user_uid)

    def create_inventory(self, user_uid: str) -> None:
        self.db.session.add(InventoryORM(user_uid=user_uid))
        self.db.session.commit()