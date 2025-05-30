from marshmallow import Schema, fields
class ExpiringSoonOutputSchema(Schema):
    ingredients = fields.List(fields.Str())
    foods = fields.List(fields.Str())