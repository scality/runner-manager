FROM mcr.microsoft.com/devcontainers/python:3.10-bullseye

# Install poetry

ENV POETRY_VERSION=1.3.2
RUN pipx install poetry==${POETRY_VERSION}

# Configure poetry to not use a virtual environment

RUN poetry config virtualenvs.create false

# Workdir

WORKDIR /workspaces/runner-manager

# Create a non-root user

RUN useradd -r -u 1000 -g root appuserRunnerManager \
    && chown -R appuserRunnerManager /workspaces/runner-manager
USER appuserRunnerManager

# Install the project dependencies

COPY poetry.lock pyproject.toml /workspaces/runner-manager/

RUN poetry install --no-interaction --no-ansi --no-root
