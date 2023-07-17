FROM python:3.11-slim

EXPOSE 8000

# install poetry
ARG POETRY_VERSION=1.5.1
ENV POETRY_VERSION=${POETRY_VERSION} \
    POETRY_NO_INTERACTION=1 \
    POETRY_NO_ANSI=1

RUN pip install poetry==$POETRY_VERSION

# copy project requirement files here to ensure they will be cached.
WORKDIR /app
COPY poetry.lock pyproject.toml /app/

# install project dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-directory --no-root

# copy project
COPY . /app

# run entrypoint.sh
CMD ["uvicorn", "runner_manager.main:app", "--host", "0.0.0.0", "--port", "8000"]