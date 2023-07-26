# Concepts

Described below are the concepts that are used in the runner manager.
They should help to understand the rest of the documentation.

## Runners

A runner is a machine that is used to run jobs in [GitHub Actions].
By default, GitHub provides runners that are hosted by them, they
are called [GitHub-hosted runners].

[GitHub Actions] also supports [self-hosted runners], the difference
being that they are managed and hosted by the user.
They will be the focus of the runner manager, and will be referred
to as runners.

## Runner groups

The [runner groups] are a way to organize runners in [GitHub Actions].
In the runner manager, runner groups are used to configure
the specification of the runners that will be created.

Each group will be matched with its appropriate runner group
in the GitHub organization or repository.

!!! note

    We use the term [runner groups] for consistency with [GitHub Actions] API.

More information about the [runner groups] configuration can be found in the
[configuration documentation](./configuration.md#runner-groups).

## Backends

The runner manager supports multiple backends, which are responsible
for hosting the runners. The following backends will be supported:

- GCP.
- AWS.
- Docker (For local functional testing).
- Emulator (For local unit testing).

## Database

The runner manager is stateful and needs to gather information that comes from both
GitHub and the backend that has been configured.

This data needs ideally to be persistent, so that the runner manager can
recover from a reboot or crash and not lose track of the runners
that are currently running.

Redis will be used as a database to store the state of the runners.

## Jobs

The runner manager will be responsible for jobs that are triggered
by events coming from GitHub as well as health checks that are
triggered periodically.

A proper queue needs to be used to ensure that tasks are:

- Not lost if the runner manager crashes.
- Properly distributed between multiple runner manager instances.

Redis is used as a task queue backend, so that only one database server
is required.

[Runner groups]: https://docs.github.com/en/enterprise-cloud@latest/actions/hosting-your-own-runners/managing-self-hosted-runners/managing-access-to-self-hosted-runners-using-groups#about-runner-groups
[GitHub-hosted runners]: https://docs.github.com/en/enterprise-cloud@latest/actions/using-github-hosted-runners/about-github-hosted-runners
[self-hosted runners]: https://docs.github.com/en/enterprise-cloud@latest/actions/hosting-your-own-runners/managing-self-hosted-runners/about-self-hosted-runners
[GitHub Actions]: https://docs.github.com/en/actions
