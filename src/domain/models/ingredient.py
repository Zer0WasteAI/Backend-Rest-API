class Ingredient:
    def __init__(self, name: str, quantity: float, type_unit: str, storage_type: str, expiration_time: int, time_unit: str, tips: str, image_path: str):
        self.name = name
        self.quantity = quantity
        self.type_unit = type_unit
        self.storage_type = storage_type
        self.expiration_time = expiration_time
        self.time_unit = time_unit
        self.tips = tips
        self.image_path = image_path

    def __repr__(self):
        return f"Ingredient(name={self.name}, quantity={self.quantity}, type_unit={self.type_unit}, storage_type={self.storage_type}, expiration_time={self.expiration_time}, time_unit={self.time_unit}, tips={self.tips}, image_path={self.image_path})"