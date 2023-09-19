from base64 import b64encode
from datetime import datetime, timedelta, timezone
from typing import List, TypeVar, cast

import httpx
from githubkit.config import Config
from githubkit.paginator import Paginator
from githubkit.response import Response
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


RT = TypeVar("RT")


def get_next_monkeypatch(self: Paginator):
    """monkeypatch Paginator._get_next_page to limit the number of pages to 2"""
    if self._current_page == 2:
        return []

    response = self.request(
        *self.args,
        **self.kwargs,
        page=self._current_page,  # type: ignore
        per_page=self._per_page,  # type: ignore
    )
    self._cached_data = (
        cast(Response[List[RT]], response).parsed_data
        if self.map_func is None
        else self.map_func(response)
    )
    self._index = 0
    self._current_page += 1
    return self._cached_data


@fixture()
def github(settings, monkeypatch) -> GitHub:
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

    monkeypatch.setattr(Paginator, "_get_next_page", get_next_monkeypatch)
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
