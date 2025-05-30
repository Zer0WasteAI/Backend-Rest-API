from marshmallow import Schema, fields, validate

class FoodItemInputSchema(Schema):
    name = fields.Str(required=True)
    main_ingredients = fields.List(fields.Str(), required=True)
    category = fields.Str(required=True, validate=validate.OneOf(["Entrada", "Plato principal", "Postre", "Bebida"]))
    calories = fields.Float(allow_none=True)
    description = fields.Str(required=True)
    storage_type = fields.Str(required=True)
    expiration_time = fields.Int(required=True)
    time_unit = fields.Str(required=True, validate=validate.OneOf(["Días", "Semanas", "Meses"]))
    tips = fields.Str(required=True)
    serving_quantity = fields.Int(required=True)
    image_path = fields.Str(required=True)
    added_at = fields.DateTime(required=True)