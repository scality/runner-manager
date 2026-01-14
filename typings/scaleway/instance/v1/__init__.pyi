from enum import Enum
from typing import Optional, List
from dataclasses import dataclass

class ServerState(str, Enum):
    RUNNING: str
    STOPPED: str
    STARTING: str
    STOPPING: str

class ServerAction(str, Enum):
    POWERON: str
    POWEROFF: str
    REBOOT: str
    TERMINATE: str

@dataclass
class Image:
    id: str
    name: str

@dataclass
class Server:
    id: str
    name: str
    state: ServerState
    tags: List[str]

class InstanceV1API:
    def __init__(self, client, bypass_validation: bool = False) -> None: ...
    def _create_server(
        self,
        zone: Optional[str] = None,
        commercial_type: str = ...,
        name: Optional[str] = None,
        dynamic_ip_required: Optional[bool] = None,
        routed_ip_enabled: Optional[bool] = None,
        image: Optional[str] = None,
        volumes: Optional[dict] = None,
        enable_ipv6: Optional[bool] = None,
        protected: bool = False,
        public_ip: Optional[str] = None,
        public_ips: Optional[List[str]] = None,
        boot_type: Optional[str] = None,
        organization: Optional[str] = None,
        project: Optional[str] = None,
        tags: Optional[List[str]] = None,
        security_group: Optional[str] = None,
        placement_group: Optional[str] = None,
        admin_password_encryption_ssh_key_id: Optional[str] = None,
    ): ...
    def get_server(self, zone: str, server_id: str): ...
    def delete_server(self, zone: str, server_id: str) -> None: ...
    def server_action(
        self, zone: str, server_id: str, action: ServerAction
    ) -> None: ...
    def get_image(self, zone: str, image_id: str): ...
    def list_images(self, zone: str, name: Optional[str] = None): ...
    def list_servers(
        self, zone: str, project: Optional[str] = None, tags: Optional[List[str]] = None
    ): ...
    def update_server(
        self, zone: str, server_id: str, tags: Optional[List[str]] = None
    ): ...
    def set_server_user_data(
        self, zone: str, server_id: str, key: str, content: bytes
    ) -> None: ...
