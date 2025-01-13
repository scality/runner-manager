from runner_manager.models.backend import ScalewayConfig, ScalewayInstanceConfig
from runner_manager.backend.scaleway import ScalewayBackend
from runner_manager.models.runner import Runner
from pytest import fixture

@fixture
def config():
    return ScalewayConfig()


def test_scaleway_backend(config):
    runner = Runner(name="test_runner", busy=False)
    backend = ScalewayBackend(config=config)
    import pdb; pdb.set_trace()
