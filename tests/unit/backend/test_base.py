from redis_om import Migrator

from runner_manager import RunnerGroup
from runner_manager.models.backend import InstanceConfig


def test_backend_create_runner(backend, runner):
    runner = backend.create(runner)
    assert runner.backend == backend.name
    assert runner.instance_id == runner.pk


def test_backend_delete_runner(backend, runner):
    runner = backend.create(runner)
    assert backend.delete(runner) == 1


def test_backend_list_runners(backend, runner):
    runner = backend.create(runner)
    Migrator().run()
    assert runner in backend.list()


def test_backend_update_runner(backend, runner):
    runner = backend.create(runner)
    runner.busy = True
    runner.status = "online"
    runner = backend.update(runner)
    assert runner.busy is True
    assert runner.status == "online"

def test_instance_config_template(backend, runner):
    runner = backend.create(runner)
    template = backend.instance_config.template_startup(runner)
    assert runner.name in template
    assert runner.labels[0].name in template
    assert runner.encoded_jit_config in template

def test_setup_redhat_credentials(runner, monkeypatch):
    monkeypatch.setenv("REDHAT_USERNAME", "username")
    monkeypatch.setenv("REDHAT_PASSWORD", "password")
    # Test loading from an InstanceConfig object
    instance = InstanceConfig()
    assert instance.redhat_username == "username"
    assert instance.redhat_password is not None
    assert instance.redhat_password == "password"
    # Test loading from a runnerGroup object
    runner_group: RunnerGroup = RunnerGroup(
        name="test",
        backend={"name": "base", "instance_config": {}},
        organization="octo-org",
        labels=["label"],
    )
    runner_group.save()

    # Test the remaining config when the group is retrieved from the database
    runner_group = RunnerGroup.get(runner_group.pk)
    assert runner_group.backend.instance_config
    assert runner_group.backend.instance_config.redhat_username == "username"
    assert runner_group.backend.instance_config.redhat_password is not None
    assert runner_group.backend.instance_config.redhat_password == "password"
    # Ensure that the template is rendered correctly
    template = runner_group.backend.instance_config.template_startup(runner)
    assert 'REDHAT_USERNAME="username"' in template
    assert 'REDHAT_PASSWORD="password"' in template

def test_job_scripts(runner_group, runner):
    runner.job_started_script = "echo \"job started\""
    runner.job_completed_script = "echo \"job completed\""
    # Ensure that the template is rendered correctly
    template = runner_group.backend.instance_config.template_startup(runner)
    assert "echo \"Hello\"" in template
    assert "echo \"job completed\"" in template