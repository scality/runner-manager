FROM python:3.9.5-slim

ENV PYTHONUNBUFFERED=0
ENV PYTHONPATH=$PYTHONPATH:/app/backend

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

COPY ./requirements.txt .
RUN pip install -r ./requirements.txt

COPY backend /app/backend
COPY ./settings.yml /app
COPY ./templates /app/templates
CMD ["uvicorn", "backend.web:app", "--host", "0.0.0.0", "--port", "80", "--reload", "--log-level", "trace"]

