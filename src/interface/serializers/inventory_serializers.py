from marshmallow import Schema, fields, validate

class IngredientInputSchema(Schema):
    name = fields.String(required=True)
    quantity = fields.Float(required=True)
    expiration_time = fields.Integer(required=True)
    time_unit = fields.String(
        required=True,
        validate=validate.OneOf(["Días", "Semanas", "Meses"])
    )
    type_unit = fields.String(required=True)
    storage_type = fields.String(required=True)
    tips = fields.String(required=True)
    image_path = fields.String(required=True)

class AddIngredientsBatchSchema(Schema):
    ingredients = fields.List(fields.Nested(IngredientInputSchema), required=True)

class UpdateIngredientSchema(Schema):
    quantity = fields.Float(required=True)
    expiration_time = fields.Integer(required=True)
    time_unit = fields.String(
        required=True,
        validate=validate.OneOf(["Días", "Semanas", "Meses"])
    )
    type_unit = fields.String(required=True)
    storage_type = fields.String(required=True)
    tips = fields.String(required=True)
    image_path = fields.String(required=True)
    added_at = fields.DateTime(required=True)

class IngredientStackSchema(Schema):
    quantity = fields.Float(required=True)
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
