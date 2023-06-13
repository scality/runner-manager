from marshmallow import Schema, fields


class GcloudConfig(Schema):
    project_id = fields.Str(required=True)
    zone = fields.Str(required=True)


class GcloudConfigVmType(Schema):
    machine_type = fields.Str(required=True)
    project = fields.Str(required=True)
    family = fields.Str(required=True)
    disk_size_gb = fields.Str(required=True)
    spot = fields.Boolean(load_default=False)
