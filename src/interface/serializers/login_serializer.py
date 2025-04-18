from marshmallow import Schema, fields

class LoginUserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)
