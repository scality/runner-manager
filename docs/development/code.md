# Code

The Runner Manager is written in Python, typing will be used and enforced
by [pyright](https://github.com/microsoft/pyright).

All libraries must be compatible with [Pydantic](https://docs.pydantic.dev/).
This requirement will allow to have a nice developer experience
especially when combined with [Fastapi](#fastapi).

## Dependencies

The main dependencies are described below along with the reason why they were chosen.

### Fastapi

[Fastapi](https://fastapi.tiangolo.com/) will be used as a web framework to
expose the API of the runner manager.

### GitHubkit

[GitHubkit](https://github.com/yanyongyu/githubkit) is a GitHub API client for
Python that works exactly like the official GitHub API client for JavaScript, Octokit.

Its code is generated from the OpenAPI specification of the GitHub API.

### Redis-om

[Redis-om](https://github.com/redis/redis-om-python) is a Redis Object Mapper
that allows to store and retrieve Python Pydantic objects in Redis.

This enable fastapi objects to be stored in Redis and retrieved
without having to write boilerplate code.

### RQ

[RQ](https://python-rq.org/) is a simple Python library for queueing jobs and
processing them in the background with workers.

It will be used to process the jobs that will be created by the runner manager.