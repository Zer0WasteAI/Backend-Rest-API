from marshmallow import Schema, fields
class InventoryPublicSchema(Schema):
    user_uid = fields.Str()
    ingredients = fields.List(fields.Str())
    foods = fields.Int()