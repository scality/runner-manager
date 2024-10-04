FROM python:3.11

ARG VERSION=dev

LABEL org.opencontainers.image.title=runner-manager
LABEL org.opencontainers.image.source=https://github.com/scality/runner-manager
LABEL org.opencontainers.image.description="Manager for GitHub Actions self-hosted runners" 
LABEL org.opencontainers.image.licenses="Apache-2.0"
LABEL org.opencontainers.image.version=$VERSION

EXPOSE 8000
HEALTHCHECK NONE

# install poetry
ARG POETRY_VERSION=1.7.1
ENV POETRY_VERSION=${POETRY_VERSION} \
    POETRY_NO_INTERACTION=1 \
    POETRY_NO_ANSI=1

RUN pip install --no-cache-dir poetry==$POETRY_VERSION

# Create a runner-manager group and user
RUN groupadd -r runner-manager && \
    useradd --no-log-init -r -g runner-manager runner-manager && \
    mkdir -p /home/runner-manager && \
    chown -R runner-manager:runner-manager /home/runner-manager

# copy project requirement files here to ensure they will be cached.
WORKDIR /app

COPY --chown=runner-manager:runner-manager poetry.lock pyproject.toml /app/

# install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-directory --no-root

# copy project
COPY . /app

RUN poetry install --only-root

USER runner-manager

# run entrypoint.sh
CMD ["uvicorn", "runner_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]
