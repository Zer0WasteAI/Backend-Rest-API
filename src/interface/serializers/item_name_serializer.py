from marshmallow import Schema, fields

class ItemNameSchema(Schema):
    item_name = fields.Str(required=True)