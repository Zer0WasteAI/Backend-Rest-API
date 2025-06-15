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
        print(f"🔍 [INVENTORY REPO] Fetching inventory for user: {user_uid}")
        
        inventory = Inventory(user_uid)

        stmt = select(IngredientORM).where(IngredientORM.inventory_user_uid == user_uid)
        ingredients = self.db.session.execute(stmt).scalars().all()
        
        print(f"📊 [INVENTORY REPO] Found {len(ingredients)} ingredient types in database")

        for ing in ingredients:
            print(f"🥬 [INVENTORY REPO] Processing ingredient: {ing.name}")
            print(f"   └─ Type unit: {ing.type_unit}")
            print(f"   └─ Storage: {ing.storage_type}")
            print(f"   └─ Stacks count: {len(ing.stacks)}")
            
            domain_ing = Ingredient(
                name=ing.name,
                type_unit=ing.type_unit,
                storage_type=ing.storage_type,
                tips=ing.tips,
                image_path=ing.image_path
            )

            for j, stack in enumerate(ing.stacks):
                print(f"   └─ Stack {j+1}: {stack.quantity} units, expires: {stack.expiration_date}")
                domain_stack = IngredientStack(
                    quantity=stack.quantity,
                    type_unit=ing.type_unit,
                    expiration_date=stack.expiration_date,
                    added_at=stack.added_at
                )
                domain_ing.add_stack(domain_stack)

            inventory.ingredients[ing.name] = domain_ing

        print(f"✅ [INVENTORY REPO] Successfully loaded inventory with {len(inventory.ingredients)} ingredients")
        return inventory

    def save(self, inventory: Inventory) -> None:
        print(f"💾 [INVENTORY REPO] Saving inventory for user: {inventory.user_uid}")
        
        if not self.db.session.get(InventoryORM, inventory.user_uid):
            print(f"📝 [INVENTORY REPO] Creating new inventory record")
            self.db.session.add(InventoryORM(user_uid=inventory.user_uid))
        else:
            print(f"📋 [INVENTORY REPO] Using existing inventory record")
            
        self.db.session.commit()
        print(f"✅ [INVENTORY REPO] Inventory saved successfully")

    def add_ingredient_stack(self, user_uid: str, stack: IngredientStack, ingredient: Ingredient) -> None:
        print(f"📦 [INVENTORY REPO] Adding ingredient stack: {ingredient.name}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Quantity: {stack.quantity}")
        print(f"   └─ Expiration: {stack.expiration_date}")
        
        # Buscar si ya existe el ingrediente en el inventario
        stmt = select(IngredientORM).where(
            and_(
                IngredientORM.name == ingredient.name,
                IngredientORM.inventory_user_uid == user_uid
            )
        )
        existing_ingredient = self.db.session.execute(stmt).scalar_one_or_none()
        
        if not existing_ingredient:
            print(f"   └─ 🆕 Creating new ingredient record for: {ingredient.name}")
            # Crear nuevo ingrediente si no existe
            ingredient_orm = IngredientORM(
                name=ingredient.name,
                type_unit=ingredient.type_unit,
                storage_type=ingredient.storage_type,
                tips=ingredient.tips,
                image_path=ingredient.image_path,
                inventory_user_uid=user_uid
            )
            self.db.session.add(ingredient_orm)
            self.db.session.flush()  # Para obtener el ID
            print(f"   └─ ✅ Created ingredient: {ingredient.name}")
        else:
            print(f"   └─ 🔄 Updating existing ingredient record for: {ingredient.name}")
            # Actualizar datos del ingrediente existente
            existing_ingredient.type_unit = ingredient.type_unit
            existing_ingredient.storage_type = ingredient.storage_type
            existing_ingredient.tips = ingredient.tips
            existing_ingredient.image_path = ingredient.image_path
            print(f"   └─ ✅ Updated ingredient metadata: {ingredient.name}")
        
        # Agregar el nuevo stack
        print(f"   └─ 📦 Adding new stack for: {ingredient.name}")
        stack_orm = IngredientStackORM(
            ingredient_name=ingredient.name,
            inventory_user_uid=user_uid,
            quantity=stack.quantity,
            expiration_date=stack.expiration_date,
            added_at=stack.added_at
        )
        self.db.session.add(stack_orm)
        self.db.session.commit()
        print(f"   └─ ✅ Successfully added stack for: {ingredient.name}")

    def add_food_item(self, user_uid: str, food_item: FoodItem) -> None:
        print(f"🍽️ [INVENTORY REPO] Adding food item: {food_item.name}")
        print(f"   └─ User: {user_uid}")
        print(f"   └─ Serving quantity: {food_item.serving_quantity}")
        print(f"   └─ Expiration: {food_item.expiration_date}")
        
        food_orm = FoodItemORM(
            inventory_user_uid=user_uid,
            name=food_item.name,
            main_ingredients=food_item.main_ingredients,
            category=food_item.category,
            calories=food_item.calories,
            description=food_item.description,
            storage_type=food_item.storage_type,
            expiration_time=food_item.expiration_time,
            time_unit=food_item.time_unit,
            tips=food_item.tips,
            serving_quantity=food_item.serving_quantity,
            image_path=food_item.image_path,
            added_at=food_item.added_at,
            expiration_date=food_item.expiration_date
        )
        
        self.db.session.add(food_orm)
        self.db.session.commit()
        print(f"   └─ ✅ Successfully added food item: {food_item.name}")

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
        try:
            added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
        except ValueError:
            added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
        
        stmt = delete(FoodItemORM).where(
            and_(
                FoodItemORM.name == food_name,
                FoodItemORM.inventory_user_uid == user_uid,
                FoodItemORM.added_at == added_at_datetime
            )
        )
        self.db.session.execute(stmt)
        self.db.session.commit()

    def update_food_item(self, user_uid: str, food_item: FoodItem) -> None:
        try:
            added_at_datetime = datetime.fromisoformat(food_item.added_at.isoformat().replace('Z', '+00:00'))
        except ValueError:
            added_at_datetime = food_item.added_at
        
        stmt = select(FoodItemORM).where(
            and_(
                FoodItemORM.name == food_item.name,
                FoodItemORM.inventory_user_uid == user_uid,
                FoodItemORM.added_at == added_at_datetime
            )
        )
        food_orm = self.db.session.execute(stmt).scalar_one_or_none()
        
        if food_orm:
            food_orm.main_ingredients = food_item.main_ingredients
            food_orm.category = food_item.category
            food_orm.calories = food_item.calories
            food_orm.description = food_item.description
            food_orm.storage_type = food_item.storage_type
            food_orm.expiration_time = food_item.expiration_time
            food_orm.time_unit = food_item.time_unit
            food_orm.tips = food_item.tips
            food_orm.serving_quantity = food_item.serving_quantity
            food_orm.image_path = food_item.image_path
            food_orm.expiration_date = food_item.expiration_date
        
        self.db.session.commit()

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

    def get_ingredient_stack(self, user_uid: str, ingredient_name: str, added_at: str) -> dict:
        """
        Obtiene los datos de un stack específico de ingrediente.
        
        Returns:
            dict: Datos del stack e ingrediente, o None si no se encuentra
        """
        try:
            added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
        except ValueError:
            added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
        
        # Obtener stack específico
        stack_stmt = select(IngredientStackORM).where(
            and_(
                IngredientStackORM.ingredient_name == ingredient_name,
                IngredientStackORM.inventory_user_uid == user_uid,
                IngredientStackORM.added_at == added_at_datetime
            )
        )
        stack_orm = self.db.session.execute(stack_stmt).scalar_one_or_none()
        
        if not stack_orm:
            return None
        
        # Obtener metadata del ingrediente
        ingredient_stmt = select(IngredientORM).where(
            and_(
                IngredientORM.name == ingredient_name,
                IngredientORM.inventory_user_uid == user_uid
            )
        )
        ingredient_orm = self.db.session.execute(ingredient_stmt).scalar_one_or_none()
        
        if not ingredient_orm:
            return None
        
        return {
            'quantity': stack_orm.quantity,
            'type_unit': ingredient_orm.type_unit,
            'expiration_date': stack_orm.expiration_date,
            'added_at': stack_orm.added_at,
            'storage_type': ingredient_orm.storage_type,
            'tips': ingredient_orm.tips,
            'image_path': ingredient_orm.image_path
        }

    def get_food_item(self, user_uid: str, food_name: str, added_at: str) -> dict:
        """
        Obtiene los datos de un food item específico.
        
        Returns:
            dict: Datos del food item, o None si no se encuentra
        """
        try:
            added_at_datetime = datetime.fromisoformat(added_at.replace('Z', '+00:00'))
        except ValueError:
            added_at_datetime = datetime.strptime(added_at, '%Y-%m-%d %H:%M:%S')
        
        stmt = select(FoodItemORM).where(
            and_(
                FoodItemORM.name == food_name,
                FoodItemORM.inventory_user_uid == user_uid,
                FoodItemORM.added_at == added_at_datetime
            )
        )
        food_orm = self.db.session.execute(stmt).scalar_one_or_none()
        
        if not food_orm:
            return None
        
        return {
            'name': food_orm.name,
            'main_ingredients': food_orm.main_ingredients,
            'category': food_orm.category,
            'calories': food_orm.calories,
            'description': food_orm.description,
            'storage_type': food_orm.storage_type,
            'expiration_time': food_orm.expiration_time,
            'time_unit': food_orm.time_unit,
            'tips': food_orm.tips,
            'serving_quantity': food_orm.serving_quantity,
            'image_path': food_orm.image_path,
            'added_at': food_orm.added_at,
            'expiration_date': food_orm.expiration_date
        }
    
    def get_all_food_items(self, user_uid: str) -> list:
        """
        Obtiene todos los food items del inventario de un usuario.
        
        Returns:
            list: Lista de todos los food items del usuario
        """
        stmt = select(FoodItemORM).where(FoodItemORM.inventory_user_uid == user_uid)
        food_items = self.db.session.execute(stmt).scalars().all()
        
        return [
            {
                'name': food_orm.name,
                'main_ingredients': food_orm.main_ingredients,
                'category': food_orm.category,
                'calories': food_orm.calories,
                'description': food_orm.description,
                'storage_type': food_orm.storage_type,
                'expiration_time': food_orm.expiration_time,
                'time_unit': food_orm.time_unit,
                'tips': food_orm.tips,
                'serving_quantity': food_orm.serving_quantity,
                'image_path': food_orm.image_path,
                'added_at': food_orm.added_at,
                'expiration_date': food_orm.expiration_date
            }
            for food_orm in food_items
        ]

    def get_all_ingredient_stacks(self, user_uid: str, ingredient_name: str) -> list:
        """
        Obtiene todos los stacks de un ingrediente específico.
        
        Returns:
            list: Lista de stacks del ingrediente
        """
        stmt = select(IngredientStackORM).where(
            and_(
                IngredientStackORM.ingredient_name == ingredient_name,
                IngredientStackORM.inventory_user_uid == user_uid
            )
        )
        stacks = self.db.session.execute(stmt).scalars().all()
        return [
            {
                'quantity': stack.quantity,
                'added_at': stack.added_at,
                'expiration_date': stack.expiration_date
            }
            for stack in stacks
        ]

    def delete_ingredient_complete(self, user_uid: str, ingredient_name: str) -> None:
        """
        Elimina un ingrediente completo (todos sus stacks) del inventario.
        
        Args:
            user_uid: ID del usuario
            ingredient_name: Nombre del ingrediente a eliminar
        """
        print(f"🗑️ [INVENTORY REPO] Deleting complete ingredient: {ingredient_name}")
        print(f"   └─ User: {user_uid}")
        
        # Primero eliminar todos los stacks del ingrediente
        stmt_stacks = delete(IngredientStackORM).where(
            and_(
                IngredientStackORM.ingredient_name == ingredient_name,
                IngredientStackORM.inventory_user_uid == user_uid
            )
        )
        result_stacks = self.db.session.execute(stmt_stacks)
        deleted_stacks = result_stacks.rowcount
        print(f"   └─ Deleted {deleted_stacks} stacks")
        
        # Luego eliminar el ingrediente principal
        stmt_ingredient = delete(IngredientORM).where(
            and_(
                IngredientORM.name == ingredient_name,
                IngredientORM.inventory_user_uid == user_uid
            )
        )
        result_ingredient = self.db.session.execute(stmt_ingredient)
        deleted_ingredients = result_ingredient.rowcount
        print(f"   └─ Deleted {deleted_ingredients} ingredient record")
        
        self.db.session.commit()
        print(f"✅ [INVENTORY REPO] Successfully deleted complete ingredient: {ingredient_name}")