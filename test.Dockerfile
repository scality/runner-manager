FROM python:3.9.7-slim
#
# Install packages needed by the buildchain
#

RUN apt-get upgrade
RUN apt-get --assume-yes update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --assume-yes \
    build-essential \
    curl \
    git \
    sudo \
    wget


WORKDIR /app
RUN python3 -m ensurepip --default-pip
RUN pip3 install tox==3.4.0

# Set the desired version of Helm
ENV DESIRED_VERSION v2.17.0
# Install helm
RUN curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get > /tmp/get_helm.sh && bash /tmp/get_helm.sh