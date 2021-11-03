FROM python:3.9.5-slim

ENV PYTHONUNBUFFERED=0

#
# Install packages needed by the buildchain
#
RUN apt-get upgrade
RUN apt-get --assume-yes update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --assume-yes \
    curl \
    git \
    python \
    python3 \
    python3-pip


WORKDIR /app

COPY ./web-requirements.txt .
RUN pip install -r ./web-requirements.txt

COPY . /install-runner
RUN pip3 install /install-runner --use-feature=in-tree-build
RUN rm -rf /install-runner

COPY ./web /app/web
COPY ./settings.yml /app
COPY ./templates /app/templates
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--log-level", "trace"]

