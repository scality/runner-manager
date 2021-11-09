FROM python:3.9.5-slim

ENV PYTHONUNBUFFERED=0
ENV PYTHONPATH=$PYTHONPATH:/app/srcs

#
# Install packages needed by the buildchain
#
RUN apt-get upgrade
RUN apt-get --assume-yes update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --assume-yes \
    curl \
    git \
    python3 \
    python3-pip


WORKDIR /app

COPY ./requirements.txt .
RUN pip install -r ./requirements.txt

COPY srcs /app/srcs
COPY ./templates /app/templates
CMD ["uvicorn", "srcs.web.app:app", "--host", "0.0.0.0", "--port", "80"]

