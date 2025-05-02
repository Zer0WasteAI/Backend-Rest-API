class Food:
    def __init__(self, uid: str, name: str, main_ingredients: list, category: str, description: str, storage_type: str, expiration_time: int, time_unit: str, serving_quantity: int, tips: str):
        self.uid = uid
        self.name = name
        self.main_ingredients = main_ingredients
        self.category = category
        self.description = description
        self.storage_type = storage_type
        self.expiration_time = expiration_time
        self.time_unit = time_unit
        self.serving_quantity = serving_quantity
        self.tips = tips

    def __repr__(self):
        return f"Food(uid={self.uid}, name={self.name}, main_ingredients={self.main_ingredients}, category={self.category}, description={self.description}, storage_type={self.storage_type}, expiration_time={self.expiration_time}, time_unit={self.time_unit}, serving_quantity={self.serving_quantity}, tips={self.tips})"