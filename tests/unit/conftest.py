from datetime import timedelta

import httpx
from githubkit import Response
from githubkit.config import Config
from githubkit.rest.models import AuthenticationToken
from hypothesis import HealthCheck
from hypothesis import settings as hypothesis_settings
from pytest import fixture

from runner_manager import Runner, RunnerGroup
from runner_manager.clients.github import GitHub

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
        runner_group_id=1,
        status="online",
        busy=False,
        labels=[{"name": "label"}],
        manager=settings.name,
    )
    assert runner.Meta.global_key_prefix == settings.name
    Runner.delete_many(Runner.find().all())
    return runner


@fixture()
def runner_token(runner_group: RunnerGroup, github: GitHub) -> AuthenticationToken:
    token: Response[
        AuthenticationToken
    ] = github.rest.actions.create_registration_token_for_org(
        org=runner_group.organization
    )
    return token.parsed_data
