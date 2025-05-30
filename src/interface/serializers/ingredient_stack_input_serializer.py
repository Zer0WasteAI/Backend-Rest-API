from marshmallow import Schema, fields

class IngredientStackInputSchema(Schema):
    quantity = fields.Float(required=True)
    expiration_date = fields.DateTime(required=True)
    added_at = fields.DateTime(required=True)

class IngredientInputSchema(Schema):
    name = fields.Str(required=True)
    type_unit = fields.Str(required=True)
    storage_type = fields.Str(required=True)
    tips = fields.Str(required=True)
    image_path = fields.Str(required=True)
    stacks = fields.List(fields.Nested(IngredientStackInputSchema), required=True)