from marshmallow import Schema, fields


class OpenstackConfig(Schema):
    endpoint = fields.Str(required=True)
    region = fields.Str(required=True)
    project_name = fields.Str(required=True)
    network_name = fields.Str(required=True)

    username = fields.Str(required=False)
    password = fields.Str(required=False)
    token = fields.Str(required=False)
