FROM python:3.9.5-slim

ENV PYTHONUNBUFFERED=0

#
# Install packages needed by the buildchain
#
RUN apt-get upgrade
RUN apt-get --assume-yes update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --assume-yes \
    python \
    python3 \
    python3-pip


WORKDIR /app

COPY ./web-requirements.txt .
RUN pip install -r ./web-requirements.txt

COPY ./web /app/web
CMD ["uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "80"]

