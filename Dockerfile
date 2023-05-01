FROM python:3.11.3-bullseye

ENV PYTHONUNBUFFERED=0
ENV POETRY_VERSION=1.3.2
ENV PYTHONPATH=/app/srcs
ENV DEBIAN_FRONTEND=noninteractive
#
# Install packages needed by the buildchain
#
RUN apt-get update && \
    apt-get install --no-install-recommends --assume-yes \
    ca-certificates \
    curl \
    git

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-dev --no-root

COPY . /app/

RUN useradd -r -u 1000 runner-manager \
    && chown -R runner-manager /app
USER runner-manager

CMD ["uvicorn", "srcs.web.app:app", "--host", "0.0.0.0", "--port", "80"]
