import os
from unittest.mock import MagicMock

import pytest
from redis_om import NotFoundError
from scaleway.instance.v1 import ServerState

from runner_manager.backend.scaleway import ScalewayBackend
from runner_manager.models.backend import (
    Backends,
    ScalewayConfig,
    ScalewayInstanceConfig,
)
from runner_manager.models.runner import Runner
from runner_manager.models.runner_group import RunnerGroup


@pytest.fixture()
def scaleway_group(settings) -> RunnerGroup:
    """Create a runner group with Scaleway backend configuration."""
    config = ScalewayConfig(
        project_id=os.environ.get("SCW_DEFAULT_PROJECT_ID", "test-project-id"),
        zone=os.environ.get("SCW_DEFAULT_ZONE", "fr-par-1"),
        region=os.environ.get("SCW_DEFAULT_REGION", "fr-par"),
    )
    runner_group = RunnerGroup(
        id=2,
        name="test-scaleway",
        organization="octo-org",
        manager=settings.name,
        backend=ScalewayBackend(
            name=Backends.scaleway,
            config=config,
            instance_config=ScalewayInstanceConfig(
                commercial_type="DEV1-S",
                # Use the actual UUID for Ubuntu 22.04 Jammy in fr-par-1
                image=os.environ.get(
                    "SCW_IMAGE_ID", "ec31d73d-ca36-4536-adf4-0feb76d30379"
                ),
                tags=["test", "runner-manager"],
            ),
        ),
        labels=["scaleway", "test"],
    )
    return runner_group


@pytest.fixture()
def fake_scaleway_group(scaleway_group, monkeypatch):
    """Mock the Scaleway client for tests without API."""

    # Mock Image
    mock_image = MagicMock()
    mock_image.id = "test-image-id"
    mock_image.name = "ubuntu_jammy"

    # Mock Server
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.name = "test-runner"
    mock_server.state = ServerState.RUNNING
    mock_server.tags = ["manager=test", "runner-group=test-scaleway"]

    # Mock API responses
    mock_client = MagicMock()
    mock_client.get_image.return_value = MagicMock(image=mock_image)
    mock_client.list_images.return_value = MagicMock(images=[mock_image])
    mock_client._create_server.return_value = MagicMock(server=mock_server)
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    mock_client.list_servers.return_value = MagicMock(servers=[mock_server])
    mock_client.set_server_user_data.return_value = None
    mock_client.server_action.return_value = None
    mock_client.update_server.return_value = None
    mock_client.delete_server.return_value = None
    mock_client.delete_volume.return_value = None  # For fallback from Block API

    # Mock Block Storage API client
    # By default, simulate that volumes are not found in Block API (like l_ssd volumes)
    # This will trigger fallback to Instance API, maintaining compatibility with existing tests
    mock_block_client = MagicMock()
    mock_block_client.delete_volume.side_effect = Exception(
        "404 not_found: Volume not in Block API"
    )

    # Patch the client property
    monkeypatch.setattr(ScalewayBackend, "client", property(lambda self: mock_client))
    monkeypatch.setattr(
        ScalewayBackend, "block_client", property(lambda self: mock_block_client)
    )

    # Mock wait_for_server_state to return immediately
    def mock_wait(self, server_id, target_state, timeout=300):
        return mock_server

    monkeypatch.setattr(ScalewayBackend, "wait_for_server_state", mock_wait)

    return scaleway_group


@pytest.fixture()
def scaleway_runner(runner: Runner, scaleway_group: RunnerGroup) -> Runner:
    """Use the standard test runner."""
    # Cleanup and return a runner for testing
    scaleway_group.backend.delete(runner)
    return runner


def test_sanitize_tags(fake_scaleway_group):
    """Test tag sanitization for Scaleway compliance."""
    backend = fake_scaleway_group.backend

    # Test with invalid characters
    tags = ["Test-Tag", "with spaces", "UPPERCASE", "special@chars!", "underscore_ok"]
    sanitized = backend.sanitize_tags(tags)

    assert "test-tag" in sanitized
    assert "with-spaces" in sanitized
    assert "uppercase" in sanitized
    assert "special-chars-" in sanitized
    assert "underscore_ok" in sanitized

    # All tags should be lowercase
    for tag in sanitized:
        assert tag == tag.lower()

    # Test length limitation
    long_tag = "a" * 300
    sanitized_long = backend.sanitize_tags([long_tag])
    assert len(sanitized_long[0]) == 255


def test_backend_name(fake_scaleway_group):
    """Test backend name is correctly set."""
    assert fake_scaleway_group.backend.name == Backends.scaleway
    assert fake_scaleway_group.backend.name == "scaleway"


def test_get_image(fake_scaleway_group):
    """Test getting image by name from user images."""
    backend = fake_scaleway_group.backend
    image = backend.get_image("ubuntu_jammy")

    assert image.id == "test-image-id"
    assert image.name == "ubuntu_jammy"


def test_get_image_by_uuid(fake_scaleway_group):
    """Test getting image by UUID."""
    backend = fake_scaleway_group.backend

    # UUID format should trigger direct get_image call
    uuid = "ec31d73d-ca36-4536-adf4-0feb76d30379"
    image = backend.get_image(uuid)

    assert image.id == "test-image-id"


def test_get_image_marketplace(fake_scaleway_group, monkeypatch):
    """Test getting image from Scaleway Marketplace."""
    # Mock marketplace image
    mock_marketplace_img = MagicMock()
    mock_marketplace_img.id = "marketplace-img-id"
    mock_marketplace_img.label = "ubuntu_noble"

    # Mock local image
    mock_local_img = MagicMock()
    mock_local_img.id = "local-img-uuid"
    mock_local_img.zone = "fr-par-1"

    # Mock marketplace API
    mock_marketplace_api = MagicMock()
    mock_marketplace_api.list_images.return_value = MagicMock(
        images=[mock_marketplace_img]
    )
    mock_marketplace_api.list_local_images.return_value = MagicMock(
        local_images=[mock_local_img]
    )

    # Mock MarketplaceV2API where it's imported in the backend module
    monkeypatch.setattr(
        "runner_manager.backend.scaleway.MarketplaceV2API",
        lambda client: mock_marketplace_api,
    )

    # Mock list_images to return empty (force marketplace lookup)
    backend = fake_scaleway_group.backend
    mock_client = backend.client
    mock_client.list_images.return_value = MagicMock(images=[])

    # Get image from marketplace
    image = backend.get_image("ubuntu_noble")

    # Verify it called marketplace API
    assert mock_marketplace_api.list_images.called
    assert mock_marketplace_api.list_local_images.called
    assert image.id == "test-image-id"


def test_get_image_not_found(fake_scaleway_group, monkeypatch):
    """Test error when image is not found anywhere."""
    backend = fake_scaleway_group.backend

    # Mock all lookups to fail
    mock_client = backend.client
    mock_client.list_images.return_value = MagicMock(images=[])

    # Mock marketplace to also fail
    mock_marketplace_api = MagicMock()
    mock_marketplace_api.list_images.return_value = MagicMock(images=[])

    monkeypatch.setattr(
        "runner_manager.backend.scaleway.MarketplaceV2API",
        lambda client: mock_marketplace_api,
    )

    with pytest.raises(ValueError, match="not found in zone"):
        backend.get_image("non-existent-image")


def test_get_image_user_priority(fake_scaleway_group, monkeypatch):
    """Test that user images take priority over marketplace images."""
    backend = fake_scaleway_group.backend

    # Mock user image found
    mock_user_image = MagicMock()
    mock_user_image.id = "user-custom-image-id"
    mock_user_image.name = "my-custom-ubuntu"

    mock_client = backend.client
    mock_client.list_images.return_value = MagicMock(images=[mock_user_image])

    # Mock marketplace (should not be called)
    mock_marketplace_api = MagicMock()
    monkeypatch.setattr(
        "runner_manager.backend.scaleway.MarketplaceV2API",
        lambda client: mock_marketplace_api,
    )

    image = backend.get_image("my-custom-ubuntu")

    # Verify user image was returned
    assert image.id == "user-custom-image-id"

    # Verify marketplace was NOT called (user image found first)
    assert not mock_marketplace_api.list_images.called


def test_create_instance_mock(scaleway_runner, fake_scaleway_group):
    """Test instance creation with mocked client."""
    backend = fake_scaleway_group.backend
    runner = backend.create(scaleway_runner)

    assert runner.instance_id == "test-server-id"
    assert runner.backend == "scaleway"


def test_delete_instance_mock(scaleway_runner, fake_scaleway_group):
    """Test instance deletion with mocked client."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    result = backend.delete(scaleway_runner)
    assert result == 1


def test_update_instance_mock(scaleway_runner, fake_scaleway_group):
    """Test instance update with mocked client."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    runner = backend.update(scaleway_runner, None)
    assert runner.instance_id == "test-server-id"


def test_list_instances_mock(scaleway_runner, fake_scaleway_group):
    """Test listing instances with mocked client."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    runners = backend.list()
    assert isinstance(runners, list)


def test_wait_for_server_state_timeout(fake_scaleway_group, monkeypatch):
    """Test wait_for_server_state timeout."""

    # Mock get_server to return a server in STARTING state
    mock_server = MagicMock()
    mock_server.state = ServerState.STARTING
    mock_client = MagicMock()
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    monkeypatch.setattr(ScalewayBackend, "client", property(lambda self: mock_client))

    # Restore the real wait_for_server_state method
    monkeypatch.undo()
    monkeypatch.setattr(ScalewayBackend, "client", property(lambda self: mock_client))

    backend_instance = ScalewayBackend(
        name=Backends.scaleway,
        config=fake_scaleway_group.backend.config,
        instance_config=fake_scaleway_group.backend.instance_config,
    )

    with pytest.raises(TimeoutError):
        backend_instance.wait_for_server_state(
            "test-server-id", ServerState.RUNNING, timeout=1
        )


def test_create_with_ssh_key(scaleway_runner, fake_scaleway_group, monkeypatch):
    """Test instance creation with SSH public key."""
    # Add SSH public key to config
    fake_scaleway_group.backend.instance_config.ssh_public_key = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAbCdEfGhIjKlMnOpQrStUvWxYz user@example.com"

    backend = fake_scaleway_group.backend
    runner = backend.create(scaleway_runner)

    assert runner.instance_id == "test-server-id"
    # Verify AUTHORIZED_KEY tag was added
    mock_client = backend.client
    create_call = mock_client._create_server.call_args
    tags = create_call.kwargs.get("tags", [])
    assert any(tag.startswith("AUTHORIZED_KEY=") for tag in tags)


def test_create_with_invalid_ssh_key(scaleway_runner, fake_scaleway_group, caplog):
    """Test instance creation with invalid SSH public key format."""
    # Add invalid SSH public key to config
    fake_scaleway_group.backend.instance_config.ssh_public_key = "invalid-key"

    backend = fake_scaleway_group.backend
    runner = backend.create(scaleway_runner)

    assert runner.instance_id == "test-server-id"
    # Verify warning was logged
    assert "Invalid SSH public key format" in caplog.text


def test_create_with_public_gateway(scaleway_runner, fake_scaleway_group):
    """Test instance creation with public gateway."""
    # Add public gateway configuration
    fake_scaleway_group.backend.instance_config.public_gateway_id = "test-gateway-id"
    fake_scaleway_group.backend.instance_config.private_network_id = "test-network-id"

    backend = fake_scaleway_group.backend
    mock_client = backend.client
    mock_client.create_private_nic.return_value = None

    runner = backend.create(scaleway_runner)

    assert runner.instance_id == "test-server-id"
    # Verify private NIC was created
    mock_client.create_private_nic.assert_called_once()


def test_create_with_public_gateway_failure(
    scaleway_runner, fake_scaleway_group, caplog, monkeypatch
):
    """Test instance creation with public gateway attachment failure."""
    # Add public gateway configuration
    fake_scaleway_group.backend.instance_config.public_gateway_id = "test-gateway-id"
    fake_scaleway_group.backend.instance_config.private_network_id = "test-network-id"

    backend = fake_scaleway_group.backend
    mock_client = backend.client
    mock_client.create_private_nic.side_effect = Exception("Network error")

    runner = backend.create(scaleway_runner)

    assert runner.instance_id == "test-server-id"
    # Verify warning was logged
    assert "Failed to attach server to private network" in caplog.text


def test_create_without_jit_config(scaleway_runner, fake_scaleway_group, caplog):
    """Test instance creation without JIT config."""
    # Remove JIT config
    scaleway_runner.encoded_jit_config = None

    backend = fake_scaleway_group.backend
    created_runner = backend.create(scaleway_runner)

    assert created_runner.instance_id == "test-server-id"
    # Verify warning was logged
    assert "No JIT config provided" in caplog.text


def test_delete_with_volume_error(
    scaleway_runner, fake_scaleway_group, caplog, monkeypatch
):
    """Test instance deletion with volume deletion error."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    # Mock server with volumes
    mock_volume = MagicMock()
    mock_volume.id = "test-volume-id"
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.state = ServerState.RUNNING
    mock_server.volumes = {"0": mock_volume}

    mock_client = backend.client
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    mock_client.delete_volume.side_effect = Exception("Volume deletion failed")

    # Restore wait_for_server_state mock
    def mock_wait(self, server_id, target_state, timeout=300):
        return mock_server

    monkeypatch.setattr(ScalewayBackend, "wait_for_server_state", mock_wait)

    result = backend.delete(scaleway_runner)

    # Verify warning was logged
    assert "Failed to delete volume" in caplog.text
    assert result == 1


def test_delete_with_volume_not_found_404(
    scaleway_runner, fake_scaleway_group, caplog, monkeypatch
):
    """Test instance deletion when volume returns 404 error."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    # Mock server with volumes
    mock_volume = MagicMock()
    mock_volume.id = "test-volume-id"
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.state = ServerState.RUNNING
    mock_server.volumes = {"0": mock_volume}

    mock_client = backend.client
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    mock_client.delete_volume.side_effect = Exception("Error 404: Volume not found")

    # Restore wait_for_server_state mock
    def mock_wait(self, server_id, target_state, timeout=300):
        return mock_server

    monkeypatch.setattr(ScalewayBackend, "wait_for_server_state", mock_wait)

    result = backend.delete(scaleway_runner)

    # Verify info log for not_found volume (not warning)
    assert "not found - may have been auto-deleted" in caplog.text
    assert "Failed to delete volume" not in caplog.text
    assert result == 1


def test_delete_stopped_server(scaleway_runner, fake_scaleway_group):
    """Test deletion of already stopped server."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    # Mock server in STOPPED state
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.state = ServerState.STOPPED
    mock_server.volumes = {}

    mock_client = backend.client
    mock_client.get_server.return_value = MagicMock(server=mock_server)

    result = backend.delete(scaleway_runner)

    # Verify server_action POWEROFF was NOT called
    assert mock_client.server_action.call_count == 0
    assert result == 1


def test_delete_not_found(scaleway_runner, fake_scaleway_group, caplog):
    """Test deletion of non-existent server."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "non-existent-id"
    scaleway_runner.save()

    mock_client = backend.client
    mock_client.get_server.side_effect = Exception("404 not found")

    result = backend.delete(scaleway_runner)

    # Verify warning was logged
    assert "not found" in caplog.text
    assert result == 1


def test_delete_with_block_storage_volume(
    scaleway_runner, fake_scaleway_group, caplog, monkeypatch
):
    """Test instance deletion with block storage (sbs_volume) using Block API."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    # Mock server with block storage volume
    mock_volume = MagicMock()
    mock_volume.id = "test-block-volume-id"
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.state = ServerState.RUNNING
    mock_server.volumes = {"0": mock_volume}

    # Mock Instance API client
    mock_client = MagicMock()
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    mock_client.delete_server.return_value = None
    mock_client.delete_volume.return_value = None
    mock_client.server_action.return_value = None

    # Mock Block Storage API client
    mock_block_client = MagicMock()
    mock_block_client.delete_volume.return_value = None

    # Patch both clients
    monkeypatch.setattr(ScalewayBackend, "client", property(lambda self: mock_client))
    monkeypatch.setattr(
        ScalewayBackend, "block_client", property(lambda self: mock_block_client)
    )

    # Mock wait_for_server_state
    def mock_wait(self, server_id, target_state, timeout=300):
        return mock_server

    monkeypatch.setattr(ScalewayBackend, "wait_for_server_state", mock_wait)

    result = backend.delete(scaleway_runner)

    # Verify Block Storage API was called first
    mock_block_client.delete_volume.assert_called_once_with(
        zone=backend.config.zone,
        volume_id="test-block-volume-id",
    )
    # Verify Instance API delete_volume was NOT called
    mock_client.delete_volume.assert_not_called()
    # Verify successful deletion was logged
    assert (
        "Block storage volume test-block-volume-id deleted successfully" in caplog.text
    )
    assert result == 1


def test_delete_with_volume_fallback_to_instance_api(
    scaleway_runner, fake_scaleway_group, caplog, monkeypatch
):
    """Test volume deletion fallback from Block API to Instance API for l_ssd volumes."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    # Mock server with l_ssd volume
    mock_volume = MagicMock()
    mock_volume.id = "test-lssd-volume-id"
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.state = ServerState.RUNNING
    mock_server.volumes = {"0": mock_volume}

    # Mock Instance API client
    mock_client = MagicMock()
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    mock_client.delete_server.return_value = None
    mock_client.delete_volume.return_value = None
    mock_client.server_action.return_value = None

    # Mock Block Storage API client to return 404 (volume not found in Block API)
    mock_block_client = MagicMock()
    mock_block_client.delete_volume.side_effect = Exception(
        "404 not_found: Volume not found in Block API"
    )

    # Patch both clients
    monkeypatch.setattr(ScalewayBackend, "client", property(lambda self: mock_client))
    monkeypatch.setattr(
        ScalewayBackend, "block_client", property(lambda self: mock_block_client)
    )

    # Mock wait_for_server_state
    def mock_wait(self, server_id, target_state, timeout=300):
        return mock_server

    monkeypatch.setattr(ScalewayBackend, "wait_for_server_state", mock_wait)

    result = backend.delete(scaleway_runner)

    # Verify Block Storage API was called first
    mock_block_client.delete_volume.assert_called_once_with(
        zone=backend.config.zone,
        volume_id="test-lssd-volume-id",
    )
    # Verify Instance API was called as fallback
    mock_client.delete_volume.assert_called_once_with(
        zone=backend.config.zone,
        volume_id="test-lssd-volume-id",
    )
    # Verify successful deletion through Instance API was logged
    assert "Instance volume test-lssd-volume-id deleted successfully" in caplog.text
    assert result == 1


def test_list_with_auto_create(fake_scaleway_group, monkeypatch):
    """Test list() creates runners for servers not in database."""
    backend = fake_scaleway_group.backend

    # Mock server not in database
    mock_server = MagicMock()
    mock_server.id = "new-server-id"
    mock_server.name = "new-runner"
    mock_server.tags = [
        backend.sanitize_tags([f"manager={backend.manager}"])[0],
        backend.sanitize_tags([f"runner-group={backend.runner_group}"])[0],
        "name-new-runner",
        "busy-true",
    ]
    mock_server.creation_date = "2026-01-13T10:00:00Z"

    mock_client = backend.client
    mock_client.list_servers.return_value = MagicMock(servers=[mock_server])

    runners = backend.list()

    # Verify a runner was created
    assert len(runners) == 1
    assert runners[0].instance_id == "new-server-id"
    assert runners[0].name == "new-runner"
    assert runners[0].busy is True


def test_update_without_instance_id(scaleway_runner, fake_scaleway_group, caplog):
    """Test update when runner has no instance_id."""
    backend = fake_scaleway_group.backend
    # Don't set instance_id
    scaleway_runner.instance_id = None
    scaleway_runner.save()

    runner = backend.update(scaleway_runner, None)

    # Verify warning was logged and no update was attempted
    assert "no instance_id" in caplog.text
    assert runner.instance_id is None


def test_get_not_found(fake_scaleway_group):
    """Test get() with non-existent instance_id."""
    backend = fake_scaleway_group.backend

    with pytest.raises(NotFoundError):
        backend.get("non-existent-id")


def test_get_image_by_id(fake_scaleway_group):
    """Test get_image with valid image ID."""
    backend = fake_scaleway_group.backend
    image = backend.get_image("test-image-id")

    assert image.id == "test-image-id"


# Real API tests (skipped if credentials not available)


@pytest.mark.skipif(
    not os.getenv("SCW_ACCESS_KEY"), reason="Scaleway credentials not found"
)
def test_create_delete(scaleway_runner, scaleway_group):
    """Test instance creation and deletion.

    This test requires valid Scaleway credentials:
    - SCW_ACCESS_KEY
    - SCW_SECRET_KEY
    - SCW_DEFAULT_PROJECT_ID
    """
    # Create instance
    runner = scaleway_group.backend.create(scaleway_runner)

    assert runner.instance_id is not None
    assert runner.backend == "scaleway"
    assert Runner.find(Runner.instance_id == runner.instance_id).first() == runner

    # Delete instance
    scaleway_group.backend.delete(runner)

    # Verify deletion from database
    with pytest.raises(NotFoundError):
        Runner.find(Runner.instance_id == runner.instance_id).first()


@pytest.mark.skipif(
    not os.getenv("SCW_ACCESS_KEY"), reason="Scaleway credentials not found"
)
def test_update(scaleway_runner, scaleway_group):
    """Test instance update."""
    runner = scaleway_group.backend.create(scaleway_runner)
    scaleway_group.backend.update(runner, None)
    runner = Runner.find(Runner.instance_id == runner.instance_id).first()
    scaleway_group.backend.delete(runner)
    with pytest.raises(NotFoundError):
        scaleway_group.backend.get(runner.instance_id)


@pytest.mark.skipif(
    not os.getenv("SCW_ACCESS_KEY"), reason="Scaleway credentials not found"
)
def test_get(scaleway_runner, scaleway_group):
    """Test instance retrieval."""
    runner = scaleway_group.backend.create(scaleway_runner)
    retrieved_runner = scaleway_group.backend.get(runner.instance_id)
    assert retrieved_runner.instance_id == runner.instance_id
    assert retrieved_runner.name == runner.name
    scaleway_group.backend.delete(runner)
    with pytest.raises(NotFoundError):
        scaleway_group.backend.get(runner.instance_id)


@pytest.mark.skipif(
    not os.getenv("SCW_ACCESS_KEY"), reason="Scaleway credentials not found"
)
def test_list(scaleway_runner, scaleway_group):
    """Test instance listing."""
    runner = scaleway_group.backend.create(scaleway_runner)
    runners = scaleway_group.backend.list()
    assert runner in runners
    scaleway_group.backend.delete(runner)
    with pytest.raises(NotFoundError):
        scaleway_group.backend.get(runner.instance_id)


def test_create_with_default_sbs_volume(
    scaleway_runner, fake_scaleway_group, monkeypatch, caplog
):
    """Test instance creation with default sbs_volume configuration."""
    # Mock image with root_volume
    mock_image = MagicMock()
    mock_image.id = "test-image-id"
    mock_root_volume = MagicMock()
    mock_root_volume.id = "snapshot-id"
    mock_image.root_volume = mock_root_volume

    # Patch get_image at class level
    def mock_get_image(self, image_name):
        return mock_image

    monkeypatch.setattr(ScalewayBackend, "get_image", mock_get_image)

    backend = fake_scaleway_group.backend
    backend.create(scaleway_runner)

    # Verify volumes parameter was passed to _create_server
    mock_client = backend.client
    create_call = mock_client._create_server.call_args
    volumes = create_call.kwargs.get("volumes")

    assert volumes is not None
    assert "0" in volumes
    assert volumes["0"].volume_type == "sbs_volume"
    assert volumes["0"].size == 20_000_000_000  # 20GB default
    assert volumes["0"].base_snapshot == "snapshot-id"

    # Verify log message
    assert "Creating sbs_volume boot volume: 20GB" in caplog.text
    assert "from snapshot snapshot-id" in caplog.text


def test_create_with_l_ssd_volume(
    scaleway_runner, fake_scaleway_group, monkeypatch, caplog
):
    """Test instance creation with l_ssd volume type."""
    # Mock image
    mock_image = MagicMock()
    mock_image.id = "test-image-id"

    # Patch get_image at class level
    def mock_get_image(self, image_name):
        return mock_image

    monkeypatch.setattr(ScalewayBackend, "get_image", mock_get_image)

    # Configure l_ssd
    fake_scaleway_group.backend.instance_config.volume_type = "l_ssd"
    fake_scaleway_group.backend.instance_config.volume_size_gb = 80

    backend = fake_scaleway_group.backend
    backend.create(scaleway_runner)

    # Verify volumes parameter
    mock_client = backend.client
    create_call = mock_client._create_server.call_args
    volumes = create_call.kwargs.get("volumes")

    assert volumes is not None
    assert "0" in volumes
    assert volumes["0"].volume_type == "l_ssd"
    assert volumes["0"].size == 80_000_000_000  # 80GB
    # For l_ssd, no base_snapshot should be set
    assert (
        not hasattr(volumes["0"], "base_snapshot") or volumes["0"].base_snapshot is None
    )

    # Verify log message
    assert "Creating l_ssd boot volume: 80GB" in caplog.text


def test_create_with_custom_volume_size(
    scaleway_runner, fake_scaleway_group, monkeypatch
):
    """Test instance creation with custom volume size."""
    mock_image = MagicMock()
    mock_image.id = "test-image-id"
    mock_root_volume = MagicMock()
    mock_root_volume.id = "snapshot-id"
    mock_image.root_volume = mock_root_volume

    # Patch get_image at class level
    def mock_get_image(self, image_name):
        return mock_image

    monkeypatch.setattr(ScalewayBackend, "get_image", mock_get_image)

    # Set custom size
    fake_scaleway_group.backend.instance_config.volume_size_gb = 100
    backend = fake_scaleway_group.backend

    backend.create(scaleway_runner)

    mock_client = backend.client
    create_call = mock_client._create_server.call_args
    volumes = create_call.kwargs.get("volumes")

    assert volumes["0"].size == 100_000_000_000  # 100GB


def test_create_with_no_root_volume_fallback(
    scaleway_runner, fake_scaleway_group, monkeypatch, caplog
):
    """Test fallback when image has no root_volume."""
    mock_image = MagicMock()
    mock_image.id = "test-image-id"
    mock_image.root_volume = None  # No root volume

    # Patch get_image at class level
    def mock_get_image(self, image_name):
        return mock_image

    monkeypatch.setattr(ScalewayBackend, "get_image", mock_get_image)

    backend = fake_scaleway_group.backend
    backend.create(scaleway_runner)

    # Verify warning was logged
    assert "has no root_volume, using default volume from image" in caplog.text

    # Verify volumes=None was passed
    mock_client = backend.client
    create_call = mock_client._create_server.call_args
    volumes = create_call.kwargs.get("volumes")
    assert volumes is None


def test_create_with_user_provided_volumes(
    scaleway_runner, fake_scaleway_group, monkeypatch
):
    """Test instance creation with user-provided volumes configuration."""
    from scaleway.instance.v1 import VolumeServerTemplate

    # Mock image
    mock_image = MagicMock()
    mock_image.id = "test-image-id"

    # Patch get_image at class level
    def mock_get_image(self, image_name):
        return mock_image

    monkeypatch.setattr(ScalewayBackend, "get_image", mock_get_image)

    # Set user-provided volumes
    custom_volumes = {
        "0": VolumeServerTemplate(
            volume_type="sbs_volume",
            size=50_000_000_000,
            base_snapshot="custom-snapshot-id",
        )
    }
    fake_scaleway_group.backend.instance_config.volumes = custom_volumes

    backend = fake_scaleway_group.backend
    backend.create(scaleway_runner)

    # Verify user-provided volumes were used
    mock_client = backend.client
    create_call = mock_client._create_server.call_args
    volumes = create_call.kwargs.get("volumes")

    assert volumes == custom_volumes


def test_block_client_with_credentials(scaleway_group, monkeypatch):
    """Test block_client property with valid credentials format."""
    backend = scaleway_group.backend
    # Set fake credentials with valid format (SCW prefix for access key)
    monkeypatch.setenv("SCW_ACCESS_KEY", "SCWXXXXXXXXXXXXXXXXX")
    monkeypatch.setenv("SCW_SECRET_KEY", "11111111-1111-1111-1111-111111111111")

    # Mock the Client validation to avoid actual API calls
    from scaleway import Client

    original_validate = Client.validate

    def mock_validate(self):
        return True

    monkeypatch.setattr(Client, "validate", mock_validate)

    # This should not raise an error about credentials
    client = backend.block_client
    assert client is not None

    # Restore
    monkeypatch.setattr(Client, "validate", original_validate)


def test_block_client_without_credentials(scaleway_group, monkeypatch):
    """Test block_client raises ValueError without credentials."""
    backend = scaleway_group.backend
    # Clear environment variables and config
    monkeypatch.delenv("SCW_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SCW_SECRET_KEY", raising=False)
    backend.config.access_key = None
    backend.config.secret_key = None

    with pytest.raises(ValueError, match="Scaleway credentials not found"):
        _ = backend.block_client


def test_client_without_credentials(scaleway_group, monkeypatch):
    """Test client property raises ValueError without credentials."""
    backend = scaleway_group.backend
    # Clear environment variables and config
    monkeypatch.delenv("SCW_ACCESS_KEY", raising=False)
    monkeypatch.delenv("SCW_SECRET_KEY", raising=False)
    backend.config.access_key = None
    backend.config.secret_key = None

    with pytest.raises(ValueError, match="Scaleway credentials not found"):
        _ = backend.client


def test_delete_with_block_api_non_404_error(
    scaleway_runner, fake_scaleway_group, caplog, monkeypatch
):
    """Test volume deletion when Block API fails with non-404 error and Instance API also fails."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    # Mock server with volume
    mock_volume = MagicMock()
    mock_volume.id = "test-volume-id"
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.state = ServerState.RUNNING
    mock_server.volumes = {"0": mock_volume}

    # Mock Instance API client
    mock_client = MagicMock()
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    mock_client.delete_server.return_value = None
    mock_client.server_action.return_value = None
    # Instance API also fails with permission error
    mock_client.delete_volume.side_effect = Exception("Permission denied")

    # Mock Block Storage API client - fails with permission error (not 404)
    mock_block_client = MagicMock()
    mock_block_client.delete_volume.side_effect = Exception(
        "Permission denied: insufficient permissions"
    )

    # Patch both clients
    monkeypatch.setattr(ScalewayBackend, "client", property(lambda self: mock_client))
    monkeypatch.setattr(
        ScalewayBackend, "block_client", property(lambda self: mock_block_client)
    )

    # Mock wait_for_server_state
    def mock_wait(self, server_id, target_state, timeout=300):
        return mock_server

    monkeypatch.setattr(ScalewayBackend, "wait_for_server_state", mock_wait)

    result = backend.delete(scaleway_runner)

    # Verify warning was logged for the failed volume deletion
    assert "Failed to delete volume test-volume-id" in caplog.text
    assert "Permission denied" in caplog.text
    assert result == 1


def test_delete_with_block_api_no_fallback_on_permission_error(
    scaleway_runner, fake_scaleway_group, caplog, monkeypatch
):
    """Test volume deletion when Block API fails with non-404 error (no fallback to Instance API)."""
    backend = fake_scaleway_group.backend
    scaleway_runner.instance_id = "test-server-id"
    scaleway_runner.save()

    # Mock server with volume
    mock_volume = MagicMock()
    mock_volume.id = "test-volume-id"
    mock_server = MagicMock()
    mock_server.id = "test-server-id"
    mock_server.state = ServerState.RUNNING
    mock_server.volumes = {"0": mock_volume}

    # Mock Instance API client - succeeds on fallback (shouldn't be called)
    mock_client = MagicMock()
    mock_client.get_server.return_value = MagicMock(server=mock_server)
    mock_client.delete_server.return_value = None
    mock_client.server_action.return_value = None
    mock_client.delete_volume.return_value = None

    # Mock Block Storage API client - fails with permission error (not 404)
    mock_block_client = MagicMock()
    mock_block_client.delete_volume.side_effect = Exception(
        "403 Permission denied: insufficient permissions"
    )

    # Patch both clients
    monkeypatch.setattr(ScalewayBackend, "client", property(lambda self: mock_client))
    monkeypatch.setattr(
        ScalewayBackend, "block_client", property(lambda self: mock_block_client)
    )

    # Mock wait_for_server_state
    def mock_wait(self, server_id, target_state, timeout=300):
        return mock_server

    monkeypatch.setattr(ScalewayBackend, "wait_for_server_state", mock_wait)

    result = backend.delete(scaleway_runner)

    # Verify Block API was called
    mock_block_client.delete_volume.assert_called_once()
    # Verify Instance API was NOT called (error was not 404)
    mock_client.delete_volume.assert_not_called()
    # Verify warning was logged
    assert "Failed to delete volume test-volume-id" in caplog.text
    assert "Permission denied" in caplog.text
    assert result == 1
