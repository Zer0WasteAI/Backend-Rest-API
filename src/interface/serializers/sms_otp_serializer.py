from marshmallow import Schema, fields

class SendSMSOtpSchema(Schema):
    phone = fields.Str(required=True)

class VerifySMSOtpSchema(Schema):
    phone = fields.Str(required=True)
    code = fields.Str(required=True)