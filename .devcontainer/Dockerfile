FROM mcr.microsoft.com/devcontainers/python:3.10

# Install poetry

ENV POETRY_VERSION=1.3.2
RUN pipx install poetry==${POETRY_VERSION}

# Configure poetry to not use a virtual environment

RUN poetry config virtualenvs.create false

# Workdir

WORKDIR /workspaces/runner-manager

# Install the project dependencies

COPY poetry.lock pyproject.toml /workspaces/runner-manager/

RUN poetry install --no-interaction --no-ansi --no-root
