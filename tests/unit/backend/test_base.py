from redis_om import Migrator


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
