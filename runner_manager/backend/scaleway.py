# pyright: reportOptionalMemberAccess=false, reportArgumentType=false, reportReturnType=false, reportMissingTypeStubs=false
import logging
import os
import re
import time
from typing import List, Literal

from pydantic import Field
from redis_om import NotFoundError
from scaleway import Client  # type: ignore[import-untyped]
from scaleway.instance.v1 import (  # type: ignore[import-untyped]
    Image,
    Server,
    ServerAction,
    ServerState,
)
from scaleway.instance.v1.custom_api import (
    InstanceUtilsV1API,  # type: ignore[import-untyped]
)
from scaleway.marketplace.v2 import MarketplaceV2API  # type: ignore[import-untyped]

from runner_manager.backend.base import BaseBackend
from runner_manager.models.backend import (
    Backends,
    ScalewayConfig,
    ScalewayInstanceConfig,
)
from runner_manager.models.runner import Runner

log = logging.getLogger(__name__)


class ScalewayBackend(BaseBackend):
    """Backend for Scaleway cloud provider."""

    name: Literal[Backends.scaleway] = Field(default=Backends.scaleway)
    config: ScalewayConfig
    instance_config: ScalewayInstanceConfig

    @property
    def client(self) -> InstanceUtilsV1API:
        """Returns a Scaleway Instance API client."""
        access_key = self.config.access_key or os.getenv("SCW_ACCESS_KEY")
        secret_key = self.config.secret_key or os.getenv("SCW_SECRET_KEY")

        if not access_key or not secret_key:
            raise ValueError(
                "Scaleway credentials not found. Set SCW_ACCESS_KEY and SCW_SECRET_KEY."
            )

        scw_client = Client(
            access_key=access_key,
            secret_key=secret_key,
            default_project_id=self.config.project_id,
            default_zone=self.config.zone,
            default_region=self.config.region,
        )
        return InstanceUtilsV1API(scw_client)

    def sanitize_tags(self, tags: List[str]) -> List[str]:
        """Sanitize tags to comply with Scaleway requirements.

        Scaleway tags must:
        - Be lowercase
        - Contain only alphanumeric characters, hyphens, and underscores
        - Not exceed 255 characters
        """
        sanitized = []
        for tag in tags:
            # Convert to lowercase and replace invalid characters
            sanitized_tag = re.sub(r"[^a-z0-9\-_]", "-", tag.lower())
            # Limit length
            sanitized_tag = sanitized_tag[:255]
            sanitized.append(sanitized_tag)
        return sanitized

    def get_image(self, image_name: str) -> Image:
        """Get image by name or ID.

        Supports three lookup methods in order:
        1. Direct UUID lookup (for explicit image IDs)
        2. User's custom images by name (e.g., Packer-built images)
        3. Scaleway Marketplace images by label

        Args:
            image_name: Image UUID, custom image name, or marketplace label

        Returns:
            Image object from Scaleway Instance API

        Raises:
            ValueError: If image is not found
        """
        import re

        # Check if it's a UUID format
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
            re.IGNORECASE,
        )
        is_uuid = bool(uuid_pattern.match(image_name))

        # 1. Try direct UUID lookup
        if is_uuid:
            try:
                return self.client.get_image(
                    zone=self.config.zone,
                    image_id=image_name,
                ).image
            except Exception as e:
                log.debug(f"Image ID lookup failed: {e}")
                raise ValueError(
                    f"Image with ID '{image_name}' not found in zone {self.config.zone}"
                )

        # 2. Try to find in user's custom images by name (e.g., Packer images)
        try:
            images = self.client.list_images(
                zone=self.config.zone,
                name=image_name,
            ).images
            if images:
                log.info(f"Found user image '{image_name}': {images[0].id}")
                return images[0]
        except Exception as e:
            log.debug(f"User images lookup failed: {e}")

        # 3. Try Scaleway Marketplace
        try:
            # Create marketplace client
            scw_client = Client(
                access_key=self.config.access_key or os.getenv("SCW_ACCESS_KEY"),
                secret_key=self.config.secret_key or os.getenv("SCW_SECRET_KEY"),
                default_project_id=self.config.project_id,
                default_zone=self.config.zone,
                default_region=self.config.region,
            )
            marketplace_client = MarketplaceV2API(scw_client)

            # List all marketplace images with pagination
            all_images = []
            page = 1
            page_size = 100

            while True:
                images_result = marketplace_client.list_images(
                    include_eol=True,
                    page=page,
                    page_size=page_size,
                )
                all_images.extend(images_result.images)

                if len(images_result.images) < page_size:
                    break
                page += 1

            # Find image by label
            marketplace_image = None
            for img in all_images:
                if img.label == image_name:
                    marketplace_image = img
                    break

            if not marketplace_image:
                raise ValueError(f"Image label '{image_name}' not found in marketplace")

            log.info(f"Found marketplace image '{image_name}': {marketplace_image.id}")

            # Get the local version for the current zone
            local_images = marketplace_client.list_local_images(
                image_id=marketplace_image.id,
                zone=self.config.zone,
            )

            if local_images.local_images:
                for local_img in local_images.local_images:
                    if local_img.zone == self.config.zone:
                        log.info(f"Resolved to local image ID: {local_img.id}")
                        return self.client.get_image(
                            zone=self.config.zone,
                            image_id=local_img.id,
                        ).image

        except Exception as marketplace_error:
            log.debug(
                f"Marketplace lookup failed for '{image_name}': {marketplace_error}"
            )

        raise ValueError(
            f"Image '{image_name}' not found in zone {self.config.zone}. "
            f"Tried: UUID lookup, user images, and marketplace."
        )

    def wait_for_server_state(
        self,
        server_id: str,
        target_state: ServerState,
        timeout: int = 300,
    ) -> Server:
        """Wait for server to reach target state."""
        start_time = time.time()
        while time.time() - start_time < timeout:
            server = self.client.get_server(
                zone=self.config.zone,
                server_id=server_id,
            ).server

            if server.state == target_state:
                return server

            time.sleep(2)

        raise TimeoutError(
            f"Server {server_id} did not reach state {target_state} within {timeout} seconds"
        )

    def create(self, runner: Runner) -> Runner:
        """Create a runner instance on Scaleway.

        Args:
            runner (Runner): Runner instance to be created.

        Returns:
            Runner: Updated runner with instance_id.
        """
        log.info(f"Creating Scaleway instance for runner {runner.name}")

        # Get image
        image = self.get_image(self.instance_config.image)

        # Prepare tags
        tags = [
            f"manager={self.manager or runner.manager}",
            f"runner-group={self.runner_group or runner.runner_group_name}",
            f"name={runner.name}",
            f"status={runner.status}",
            f"busy={str(runner.busy)}",
        ] + self.instance_config.tags

        tags = self.sanitize_tags(tags)

        # Add SSH public key as AUTHORIZED_KEY tag for debugging access
        if self.instance_config.ssh_public_key:
            parts = self.instance_config.ssh_public_key.split()
            if len(parts) >= 2:
                ssh_key_for_tag = f"{parts[0]}_{parts[1]}"
                tags.append(f"AUTHORIZED_KEY={ssh_key_for_tag}")
                log.info(
                    "Adding SSH public key via AUTHORIZED_KEY tag for debugging access"
                )
            else:
                log.warning(
                    "Invalid SSH public key format, skipping AUTHORIZED_KEY tag"
                )

        # Prepare security group ID if provided
        security_group = None
        if self.instance_config.security_group_ids:
            security_group = self.instance_config.security_group_ids[0]

        # Determine IP strategy: Public Gateway vs Direct Public IP
        # If public_gateway_id is provided, use private network with gateway
        # Otherwise, use direct public IP if enabled
        use_gateway = bool(self.instance_config.public_gateway_id)
        dynamic_ip_required = self.instance_config.enable_public_ip and not use_gateway

        # Create server using _create_server
        # Note: In SDK 2.10.3, 'protected' is a required parameter
        response = self.client._create_server(
            commercial_type=self.instance_config.commercial_type,
            image=image.id,
            enable_ipv6=self.instance_config.enable_ipv6,
            name=runner.name,
            protected=False,
            dynamic_ip_required=dynamic_ip_required,
            tags=tags,
            boot_type=self.instance_config.boot_type,
            project=self.config.project_id,
            organization=self.config.organization_id,
            security_group=security_group,
        )

        server = response.server
        log.info(f"Server created with ID: {server.id}")

        # If using public gateway, attach to private network
        if use_gateway and self.instance_config.private_network_id:
            try:
                # Attach server to private network using Instance API
                self.client.create_private_nic(
                    server_id=server.id,
                    private_network_id=self.instance_config.private_network_id,
                )
                log.info(
                    f"Server {server.id} attached to private network {self.instance_config.private_network_id}"
                )
            except Exception as e:
                log.warning(
                    f"Failed to attach server to private network: {e}. Server will use public IP."
                )

        # Set cloud-init user data using SDK's InstanceUtilsV1API.set_server_user_data
        # This is similar to GCP's startup-script metadata
        if runner.encoded_jit_config:
            startup_script = self.instance_config.template_startup(runner)
            try:
                self.client.set_server_user_data(
                    server_id=server.id,
                    key="cloud-init",
                    content=startup_script.encode("utf-8"),
                    zone=self.config.zone,
                )
                log.info(f"Cloud-init user data set for server {server.id}")
            except Exception as e:
                log.warning(f"Failed to set cloud-init user data: {e}")
                # Continue anyway, the instance is created
        else:
            log.warning(
                f"No JIT config provided for runner {runner.name}, skipping startup script"
            )

        # Start the server
        self.client.server_action(
            zone=self.config.zone,
            server_id=server.id,
            action=ServerAction.POWERON,
        )

        log.info(f"Starting server {server.id}")

        # Wait for server to be running
        try:
            self.wait_for_server_state(server.id, ServerState.RUNNING)
            log.info(f"Server {server.id} is now running")
        except TimeoutError as e:
            log.error(f"Error waiting for server to start: {e}")

        # Save instance ID
        runner.instance_id = server.id

        return super().create(runner)

    def delete(self, runner: Runner) -> int:
        """Delete a runner instance from Scaleway.

        Args:
            runner (Runner): Runner instance to be deleted.

        Returns:
            int: Number of deleted runners.
        """
        if not runner.instance_id:
            log.warning(f"Runner {runner.name} has no instance_id, skipping deletion")
            return super().delete(runner)

        log.info(f"Deleting Scaleway instance {runner.instance_id}")

        try:
            # Get server to check if it exists
            server = self.client.get_server(
                zone=self.config.zone,
                server_id=runner.instance_id,
            ).server

            # Collect volume IDs before deletion
            volume_ids = []
            if server.volumes:
                # server.volumes is a dict with keys like "0", "1", etc.
                # and values are Volume objects with .id attribute
                volume_ids = [vol.id for vol in server.volumes.values()]
                log.info(f"Server has {len(volume_ids)} volume(s) that will be deleted")

            # Power off the server if it's running
            if server.state in [ServerState.RUNNING, ServerState.STARTING]:
                log.info(f"Powering off server {runner.instance_id}")
                self.client.server_action(
                    zone=self.config.zone,
                    server_id=runner.instance_id,
                    action=ServerAction.POWEROFF,
                )
                # Wait for server to be stopped
                self.wait_for_server_state(
                    runner.instance_id, ServerState.STOPPED, timeout=120
                )

            # Delete the server
            self.client.delete_server(
                zone=self.config.zone,
                server_id=runner.instance_id,
            )
            log.info(f"Server {runner.instance_id} deleted successfully")

            # Delete associated volumes
            for volume_id in volume_ids:
                try:
                    self.client.delete_volume(
                        zone=self.config.zone,
                        volume_id=volume_id,
                    )
                    log.info(f"Volume {volume_id} deleted successfully")
                except Exception as vol_error:
                    log.warning(f"Failed to delete volume {volume_id}: {vol_error}")

        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                log.warning(
                    f"Server {runner.instance_id} not found, may have been already deleted"
                )
            else:
                log.error(f"Error deleting server {runner.instance_id}: {e}")
                raise

        return super().delete(runner)

    def update(self, runner: Runner, webhook) -> Runner:
        """Update a runner instance on Scaleway.

        Args:
            runner (Runner): Runner instance to be updated.
            webhook: Webhook event data.

        Returns:
            Runner: Updated runner.
        """
        if not runner.instance_id:
            log.warning(f"Runner {runner.name} has no instance_id, skipping update")
            return super().update(runner, webhook)

        try:
            # Update tags
            tags = self.sanitize_tags(
                [
                    f"manager={self.manager or runner.manager}",
                    f"runner-group={self.runner_group or runner.runner_group_name}",
                    f"name={runner.name}",
                    f"status={runner.status}",
                    f"busy={str(runner.busy)}",
                ]
                + self.instance_config.tags
            )

            self.client._update_server(
                zone=self.config.zone,
                server_id=runner.instance_id,
                tags=tags,
            )
            log.info(f"Updated tags for server {runner.instance_id}")

        except Exception as e:
            log.error(f"Error updating server {runner.instance_id}: {e}")
            raise

        return super().update(runner, webhook)

    def get(self, instance_id: str) -> Runner:
        """Get a runner instance by instance ID.

        Args:
            instance_id (str): Instance ID to retrieve.

        Returns:
            Runner: Runner instance.

        Raises:
            NotFoundError: If instance is not found.
        """
        runner = Runner.find(Runner.instance_id == instance_id).first()
        if not runner:
            raise NotFoundError(
                f"Runner with instance_id {instance_id} not found in database"
            )
        return runner

    def list(self) -> List[Runner]:
        """List all runner instances from Scaleway.

        Returns:
            List[Runner]: List of runner instances.
        """
        runners = []

        try:
            # List all servers in the project/zone
            servers = self.client.list_servers(
                zone=self.config.zone,
                project=self.config.project_id,
            ).servers

            # Filter servers by tags (sanitized format)
            for server in servers:
                # Check if this server is managed by this runner manager
                # Tags are sanitized, so "=" becomes "-"
                manager_tag = self.sanitize_tags([f"manager={self.manager}"])[0]
                group_tag = self.sanitize_tags([f"runner-group={self.runner_group}"])[0]

                if manager_tag in server.tags and group_tag in server.tags:
                    # Find corresponding runner in database
                    try:
                        runner = Runner.find(Runner.instance_id == server.id).first()
                    except NotFoundError:
                        # Create runner if not found (sync from cloud)
                        # Extract name from tags
                        name = server.name
                        for tag in server.tags:
                            if tag.startswith("name-"):
                                name = tag[5:]  # Remove "name-" prefix
                                break

                        runner = Runner(
                            name=name,
                            instance_id=server.id,
                            runner_group_name=self.runner_group,
                            busy=any("busy-true" in tag for tag in server.tags),
                            status="online",
                            created_at=server.creation_date,
                            started_at=server.creation_date,
                        )
                    runners.append(runner)

        except Exception as e:
            log.error(f"Error listing Scaleway servers: {e}")

        return runners
