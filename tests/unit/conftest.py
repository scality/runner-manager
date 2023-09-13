from base64 import b64encode
from datetime import datetime, timedelta, timezone

import httpx
from githubkit.config import Config
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings
from pytest import fixture

from runner_manager import Runner
from runner_manager.clients.github import GitHub
from runner_manager.models.runner import RunnerLabel

hypothesis_settings.register_profile(
    "unit",
    suppress_health_check=[HealthCheck.function_scoped_fixture],
    max_examples=10,
    deadline=timedelta(seconds=1),
)
hypothesis_settings.load_profile("unit")


@fixture()
def github(settings) -> GitHub:
    """
    Return a GitHub client configured with:

    - The mock server as base_url.
    - Accept application/json as response from the server.

    """

    config = Config(
        base_url=httpx.URL(settings.github_base_url),
        accept="*/*",
        user_agent="runner-manager",
        follow_redirects=True,
        timeout=httpx.Timeout(5.0),
    )

    return GitHub(config=config)


@fixture()
def runner(settings) -> Runner:
    runner: Runner = Runner(
        id=1,
        name="test",
        organization="octo-org",
        created_at=datetime.now(timezone.utc),
        runner_group_id=1,
        status="offline",
        busy=False,
        labels=[RunnerLabel(name="label")],
        manager=settings.name,
        encoded_jit_config=b64encode(b'{"test": "test"}'),
    )
    assert runner.Meta.global_key_prefix == settings.name
    Runner.delete_many(Runner.find().all())
    return runner
