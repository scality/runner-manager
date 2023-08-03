# Code

The Runner Manager is written in Python.

All libraries must be compatible with [Pydantic](https://docs.pydantic.dev/).
This requirement will allow to have a nice developer experience
especially when combined with [Fastapi](#fastapi).

## Dependencies

The main dependencies are described below along with the reason why they were chosen.

### Fastapi

[Fastapi](https://fastapi.tiangolo.com/) will be used as a web framework to
expose the API of the runner manager.

### GitHubKit

[GitHubKit](https://github.com/yanyongyu/githubkit) is a GitHub API client for
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

## Typing

Static typing is enforced by [`pyright`](https://microsft.github.io/pyright/).

It's configuration is located in the
[`pyrightconfig.json`](../../pyrightconfig.json) file.

It is run automatically when `trunk check` is run.

To know more about `pyright` and how to use it, check out
[pyright's documentation](https://microsoft.github.io/pyright/).

### Stub files

Stub files are located in the [`typings`](../../typings) directory.

`pyright` will raise errors if it cannot find the stub files for the libraries
that are used.

To generate the stub files, run the following command:

```bash
poetry run pyright --createstub <library>
```

!!! note "Generated stub requires cleanup"

    Additional modifications might be required to the stub files as
    there are some limitations to the stub files generation.

    For more information checkout [pyright's documentation]

    [pyright's documentation]: https://microsoft.github.io/pyright/#/type-stubs?id=cleaning-up-generated-type-stubs
