from marshmallow import Schema, fields, validate

class ChangePasswordSchema(Schema):
    email = fields.Email(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6))
