# Runner Manager

By default, GitHub Actions runners are hosted by GitHub, but it is also
possible to host them on your own infrastructure, with [self-hosted runners].
The Runner Manager is a tool to handle the process of creating,
deleting and managing the state of self-hosted runners.

It is very similar to the [Actions Runner Controller (ARK)] with the
difference being that instead of focusing on Kubernetes (containers) as
backend to host the runners, it focuses on virtual machines.

[Actions Runner Controller (ARK)]: https://github.com/actions/actions-runner-controller/
[self-hosted runners]: https://docs.github.com/en/actions/hosting-your-own-runners/about-self-hosted-runners
