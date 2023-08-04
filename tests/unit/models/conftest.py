from pytest import fixture


@fixture()
def runner_group() -> RunnerGroup:
    runner_group = RunnerGroup(
        id=1,
        name="test",
        organization="test",
        backend="base",
        backend_config={},
        labels=[
            "label",
        ],
    )
    return runner_group


@fixture(scope="session", autouse=True)
def redis(settings):
    """Flush redis before tests."""

    redis_connection = get_redis_connection(
        url=settings.redis_om_url, decode_responses=True
    )
    redis_connection.flushall()

    Migrator().run()
    yield redis_connection
