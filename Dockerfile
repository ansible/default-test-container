FROM ubuntu:16.04

COPY files/deadsnakes.list /etc/apt/sources.list.d/deadsnakes.list

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys F23C5A6CF475977595C89F51BA6932366A755776

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    gcc \
    git \
    libbz2-dev \
    libffi-dev \
    libreadline-dev \
    libsqlite3-dev \
    libxml2-dev \
    libxslt1-dev \
    locales \
    make \
    openssh-client \
    openssl \
    python2.6-dev \
    python2.7-dev \
    python3.5-dev \
    python3.6-dev \
    python3.7-dev \
    shellcheck \
    && \
    apt-get clean

ADD https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer /tmp/pyenv-installer
RUN bash -c 'PYENV_ROOT=/usr/local/opt/pyenv bash /tmp/pyenv-installer'
COPY files/python* /tmp/
RUN bash -c 'PYENV_ROOT=/usr/local/opt/pyenv /usr/local/opt/pyenv/bin/pyenv install /tmp/python3.8.0*'
RUN ln -s /usr/local/opt/pyenv/versions/python3.8.0*/bin/python3.8 /usr/local/bin/python3.8
RUN ln -s /usr/local/opt/pyenv/versions/python3.8.0*/bin/pip3.8 /usr/local/bin/pip3.8

RUN rm /etc/apt/apt.conf.d/docker-clean
RUN locale-gen en_US.UTF-8
VOLUME /sys/fs/cgroup /run/lock /run /tmp

RUN ln -s python2.7 /usr/bin/python2
RUN ln -s python3.6 /usr/bin/python3
RUN ln -s python3   /usr/bin/python

# Install dotnet core SDK, pwsh, and other PS/.NET sanity test tools.
# For now, we need to manually purge XML docs and other items from a Nuget dir to vastly reduce the image size.
# See https://github.com/dotnet/dotnet-docker/issues/237 for details.
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    apt-transport-https \
    && \
    apt-get clean
ADD https://packages.microsoft.com/config/ubuntu/16.04/prod.list /etc/apt/sources.list.d/microsoft.list
RUN curl --silent https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    dotnet-sdk-2.1.4 \
    powershell \
    && \
    find /usr/share/dotnet/sdk/NuGetFallbackFolder/ -name '*.xml' -type f -delete \
    && \
    apt-get clean
RUN dotnet --version
RUN pwsh --version
COPY requirements/sanity.ps1 /tmp/
RUN /tmp/sanity.ps1

ENV container=docker
CMD ["/sbin/init"]

# Install pip and requirements last to speed up local container rebuilds when updating requirements.

ADD https://bootstrap.pypa.io/get-pip.py /tmp/get-pip.py
ADD https://bootstrap.pypa.io/2.6/get-pip.py /tmp/get-pip2.6.py

COPY files/requirements.sh /tmp/
COPY files/early-requirements.txt /tmp/
COPY requirements/*.txt /tmp/requirements/
COPY freeze/*.txt /tmp/freeze/

RUN /tmp/requirements.sh 2.6
RUN /tmp/requirements.sh 2.7
RUN /tmp/requirements.sh 3.5
RUN /tmp/requirements.sh 3.7
RUN /tmp/requirements.sh 3.8
RUN /tmp/requirements.sh 3.6
