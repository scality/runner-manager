FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# Install kustomize
ARG KUSTOMIZE_VERSION=5.1.0

RUN curl -sSL -o /tmp/kustomize.tar.gz \
    "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize/v${KUSTOMIZE_VERSION}/kustomize_v${KUSTOMIZE_VERSION}_linux_amd64.tar.gz" && \
    tar -xf /tmp/kustomize.tar.gz && \
    mv kustomize /usr/local/bin/

# Install poetry

ARG POETRY_VERSION=1.3.2
RUN pipx install poetry==${POETRY_VERSION}
