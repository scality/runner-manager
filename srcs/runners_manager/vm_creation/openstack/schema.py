from marshmallow import fields
from marshmallow import Schema


class OpenstackConfig(Schema):
    auth_url = fields.Str(required=True)
    region_name = fields.Str(required=True)
    project_name = fields.Str(required=True)
    network_name = fields.Str(required=True)
    rnic_network_name = fields.Str(required=True)

    username = fields.Str(required=False)
    password = fields.Str(required=False)
    token = fields.Str(required=False)
    id = fields.Str(required=False)
    secret = fields.Str(required=False)


class OpenstackConfigVmType(Schema):
    flavor = fields.Str(required=True)
    image = fields.Str(required=True)
    availability_zone = fields.Str(required=False)
