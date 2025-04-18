from marshmallow import Schema, fields, validate

class RegisterUserSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=6))
    name = fields.Str(required=True)
    phone = fields.Str(required=True)
