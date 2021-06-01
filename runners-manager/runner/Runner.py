from runner.VmType import VmType


class Runner(object):
    name: str
    has_run: bool
    has_child: bool

    parent_name: str or None
    action_id: int or None
    vm_id: str or None
    vm_type: VmType

    def __init__(self, name: str, vm_id: str, vm_type: VmType, parent_name=None):
        self.name = name
        self.vm_id = vm_id
        self.vm_type = vm_type
        self.parent_name = parent_name

        self.has_run = False
        self.action_id = None
        self.has_child = False

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __unicode__(self):
        return f"{self.name}, github id: {self.action_id}, scality.cloud: {self.vm_id}"

    def __str__(self):
        return self.__unicode__()
