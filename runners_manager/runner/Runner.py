from runners_manager.runner.VmType import VmType


class Runner(object):
    name: str
    status: str
    status_history: list[str]
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

        self.status = 'offline'
        self.status_history = []
        self.action_id = None
        self.has_child = False

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __unicode__(self):
        return f"{self.name}, github id: {self.action_id}, scality.cloud: {self.vm_id}"

    def __str__(self):
        return self.__unicode__()

    def update_status(self, elem):
        if elem['status'] == 'online' and elem['busy'] is True:
            status = 'running'
        else:
            status = elem['status']

        if self.status == status:
            return

        self.status_history.append(self.status)
        self.status = status

    @property
    def has_run(self) -> bool:
        return self.status == 'offline' and \
            ('online' in self.status_history or 'running' in self.status_history)
