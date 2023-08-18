FROM ghcr.io/actions/actions-runner:2.308.0

ENV RUNNER_NAME name
ENV RUNNER_ORG octo-org
ENV RUNNER_REPO repo
ENV RUNNER_LABELS label
ENV RUNNER_TOKEN token

COPY ./entrypoint.sh /home/runner/


ENTRYPOINT [ "./entrypoint.sh" ]
