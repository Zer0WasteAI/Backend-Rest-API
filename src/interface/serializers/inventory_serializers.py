from marshmallow import Schema, fields, validate

class IngredientInputSchema(Schema):
    name = fields.String(required=True)
    quantity = fields.Float(required=True)
    
    # ⭐ NUEVO: Soportar ambos formatos para compatibilidad
    # Formato viejo: expiration_time + time_unit (para cálculo manual)
    expiration_time = fields.Integer(required=False, allow_none=True)
    time_unit = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["Días", "Semanas", "Meses", "Años"])
    )
    
    # Formato nuevo: expiration_date pre-calculada (desde reconocimiento)
    expiration_date = fields.DateTime(required=False, allow_none=True)
    
    type_unit = fields.String(required=True)
    storage_type = fields.String(required=True)
    tips = fields.String(required=True)
    image_path = fields.String(required=True)

class AddIngredientsBatchSchema(Schema):
    ingredients = fields.List(fields.Nested(IngredientInputSchema), required=True)

class UpdateIngredientSchema(Schema):
    quantity = fields.Float(required=True)
    
    # ⭐ NUEVO: Soportar ambos formatos para compatibilidad
    expiration_time = fields.Integer(required=False, allow_none=True)
    time_unit = fields.String(
        required=False,
        allow_none=True,
        validate=validate.OneOf(["Días", "Semanas", "Meses", "Años"])
    )
    expiration_date = fields.DateTime(required=False, allow_none=True)
    
    type_unit = fields.String(required=True)
    storage_type = fields.String(required=True)
    tips = fields.String(required=True)
    image_path = fields.String(required=True)
    added_at = fields.DateTime(required=True)

class IngredientStackSchema(Schema):
    quantity = fields.Float(required=True)
    type_unit = fields.String(required=True)
    expiration_date = fields.DateTime(required=True)
    added_at = fields.DateTime(required=True)

class IngredientSchema(Schema):
    name = fields.String(required=True)
    type_unit = fields.String(required=True)
    storage_type = fields.String(required=True)
    tips = fields.String(allow_none=True)
    image_path = fields.String(required=True)
    stacks = fields.List(fields.Nested(IngredientStackSchema))

class InventorySchema(Schema):
    ingredients = fields.List(fields.Nested(IngredientSchema))
    food_items = fields.List(fields.Dict())  # Vacío por ahora

# ===== SCHEMAS SIMPLES PARA ACTUALIZACIÓN DE CANTIDADES =====

class UpdateIngredientQuantitySchema(Schema):
    """Schema simple para actualizar solo la cantidad de un ingrediente"""
    quantity = fields.Float(required=True, validate=validate.Range(min=0))

class UpdateFoodQuantitySchema(Schema):
    """Schema simple para actualizar solo la cantidad de porciones de comida"""
    serving_quantity = fields.Integer(required=True, validate=validate.Range(min=1))
