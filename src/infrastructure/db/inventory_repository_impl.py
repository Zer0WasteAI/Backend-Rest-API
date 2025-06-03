from typing import Optional
from sqlalchemy import select, delete, and_
from datetime import datetime
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
        # Convertir added_at string a datetime para comparar
        try:
            added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
        except ValueError:
            # Intentar otros formatos si falla
            added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
        
        # Eliminar el stack específico
        stmt = delete(IngredientStackORM).where(
            and_(
                IngredientStackORM.ingredient_name == ingredient_name,
                IngredientStackORM.inventory_user_uid == user_uid,
                IngredientStackORM.added_at == added_at_datetime
            )
        )
        self.db.session.execute(stmt)
        
        # Verificar si quedan otros stacks del mismo ingrediente
        remaining_stacks = self.db.session.execute(
            select(IngredientStackORM).where(
                and_(
                    IngredientStackORM.ingredient_name == ingredient_name,
                    IngredientStackORM.inventory_user_uid == user_uid
                )
            )
        ).scalars().all()
        
        # Si no quedan stacks, eliminar también el ingrediente
        if not remaining_stacks:
            self.db.session.execute(
                delete(IngredientORM).where(
                    and_(
                        IngredientORM.name == ingredient_name,
                        IngredientORM.inventory_user_uid == user_uid
                    )
                )
            )
        
        self.db.session.commit()

    def delete_food_item(self, user_uid: str, food_name: str, added_at: str) -> None:
        return None

    def update_food_item(self, user_uid: str, food_item: FoodItem) -> None:
        return None

    def update_ingredient_stack(self, user_uid: str, ingredient_name: str, added_at: str, new_stack: IngredientStack, new_meta: Ingredient) -> None:
        # Convertir added_at string a datetime
        try:
            added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
        except ValueError:
            added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
        
        # Actualizar el ingrediente metadata
        stmt = select(IngredientORM).where(
            and_(
                IngredientORM.name == ingredient_name,
                IngredientORM.inventory_user_uid == user_uid
            )
        )
        ingredient_orm = self.db.session.execute(stmt).scalar_one_or_none()
        
        if ingredient_orm:
            ingredient_orm.type_unit = new_meta.type_unit
            ingredient_orm.storage_type = new_meta.storage_type
            ingredient_orm.tips = new_meta.tips
            ingredient_orm.image_path = new_meta.image_path
        
        # Actualizar el stack específico
        stack_stmt = select(IngredientStackORM).where(
            and_(
                IngredientStackORM.ingredient_name == ingredient_name,
                IngredientStackORM.inventory_user_uid == user_uid,
                IngredientStackORM.added_at == added_at_datetime
            )
        )
        stack_orm = self.db.session.execute(stack_stmt).scalar_one_or_none()
        
        if stack_orm:
            stack_orm.quantity = new_stack.quantity
            stack_orm.expiration_date = new_stack.expiration_date
            # Mantenemos el added_at original, pero actualizamos al nuevo si cambió
            if new_stack.added_at != added_at_datetime:
                stack_orm.added_at = new_stack.added_at
        
        self.db.session.commit()

    def get_inventory(self, user_uid: str) -> Optional[Inventory]:
        return self.db.session.get(InventoryORM, user_uid)

    def create_inventory(self, user_uid: str) -> None:
        self.db.session.add(InventoryORM(user_uid=user_uid))
        self.db.session.commit()