from datetime import datetime
from src.domain.models.ingredient import Ingredient, IngredientStack

class AddIngredientsToInventoryUseCase:
    def __init__(self, repository, calculator):
        self.repository = repository
        self.calculator = calculator

    def execute(self, user_uid: str, ingredients_data: list[dict]):
        print(f"🏗️ [ADD INGREDIENTS USE CASE] Starting execution for user: {user_uid}")
        
        inventory = self.repository.get_inventory(user_uid)
        if inventory is None:
            print(f"📝 [ADD INGREDIENTS USE CASE] Creating new inventory for user: {user_uid}")
            self.repository.create_inventory(user_uid)
        else:
            print(f"📋 [ADD INGREDIENTS USE CASE] Using existing inventory for user: {user_uid}")

        now = datetime.now()
        print(f"⏰ [ADD INGREDIENTS USE CASE] Processing timestamp: {now}")
        
        for i, item in enumerate(ingredients_data):
            name = item["name"]
            type_unit = item["type_unit"]
            storage_type = item["storage_type"]
            tips = item["tips"]
            image_path = item["image_path"]
            quantity = item["quantity"]
            expiration_time = item["expiration_time"]
            time_unit = item["time_unit"]

            print(f"📦 [ADD INGREDIENTS {i+1}] Processing: {name}")
            print(f"   └─ Quantity: {quantity} {type_unit}")
            print(f"   └─ Storage: {storage_type}")
            print(f"   └─ Expiration: {expiration_time} {time_unit}")
            print(f"   └─ Image: {image_path[:50]}..." if len(image_path) > 50 else f"   └─ Image: {image_path}")

            try:
                if "expiration_date" in item and item["expiration_date"]:
                    expiration_date = datetime.fromisoformat(item["expiration_date"].replace('Z', '+00:00'))
                    print(f"   └─ ✅ Using pre-calculated expiration: {expiration_date}")
                else:
                    expiration_date = self.calculator.calculate_expiration_date(
                        added_at=now,
                        time_value=expiration_time,
                        time_unit=time_unit
                    )
                    print(f"   └─ ⏳ Calculated new expiration: {expiration_date}")

                ingredient = Ingredient(
                    name=name,
                    type_unit=type_unit,
                    storage_type=storage_type,
                    tips=tips,
                    image_path=image_path
                )

                stack = IngredientStack(
                    quantity=quantity,
                    type_unit=type_unit,
                    expiration_date=expiration_date,
                    added_at=now
                )

                print(f"   └─ 💾 Saving to repository...")
                self.repository.add_ingredient_stack(user_uid, stack, ingredient)
                print(f"   └─ ✅ Successfully saved: {name}")
                
            except Exception as e:
                print(f"   └─ 🚨 Error processing {name}: {str(e)}")
                raise e
        
        print(f"🎉 [ADD INGREDIENTS USE CASE] Successfully processed all {len(ingredients_data)} ingredients")
