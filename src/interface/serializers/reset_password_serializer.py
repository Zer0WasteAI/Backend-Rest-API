from marshmallow import Schema, fields, validate

class SendPasswordResetCodeSchema(Schema):
    email = fields.Email(required=True)

class VerifyPasswordResetCodeSchema(Schema):
    email = fields.Email(required=True)
    code = fields.Str(required=True, validate=validate.Length(equal=6))

class ChangePasswordSchema(Schema):
    email = fields.Email(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=6))