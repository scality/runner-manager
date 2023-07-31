import httpx
import pytest
from githubkit.config import Config

from runner_manager.clients.github import GitHub, RunnerGroup


@pytest.fixture()
def github(settings):
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


@pytest.fixture()
def runner_group():
    return RunnerGroup(id=2, name="octo-runner-group")


@pytest.fixture()
def org():
    return "octo-org"
