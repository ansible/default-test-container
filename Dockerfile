FROM quay.io/bedrock/ubuntu:bionic-20201119

# increment the number in this file to force a full container rebuild
COPY files/update.txt /tmp/update.txt

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    g++ \
    gcc \
    git \
    gnupg2 \
    libbz2-dev \
    libffi-dev \
    libreadline-dev \
    libsqlite3-dev \
    libxml2-dev \
    libxslt1-dev \
    libyaml-dev \
    locales \
    make \
    openssh-client \
    openssh-server \
    openssl \
    python2.7-dev \
    python3.6-dev \
    python3.6-distutils \
    python3.6-venv \
    python3.7-dev \
    python3.7-distutils \
    python3.7-venv \
    python3.8-dev \
    python3.8-distutils \
    python3.8-venv \
    shellcheck \
    systemd-sysv \
    && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# podman build fails with 'apt-key adv ...' but this works for both
RUN curl -sL "http://keyserver.ubuntu.com/pks/lookup?op=get&search=0xF23C5A6CF475977595C89F51BA6932366A755776" | apt-key add

COPY files/deadsnakes.list /etc/apt/sources.list.d/deadsnakes.list

# Install Python versions available from the deadsnakes PPA.
# This is done separately to avoid conflicts with official Ubuntu packages.
RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    python2.6-dev \
    python3.5-dev \
    python3.5-venv \
    python3.9-dev \
    python3.9-distutils \
    python3.9-venv \
    python3.10-dev \
    python3.10-distutils \
    python3.10-venv \
    && \
    apt-get clean

RUN rm /etc/apt/apt.conf.d/docker-clean
RUN locale-gen en_US.UTF-8
VOLUME /sys/fs/cgroup /run/lock /run /tmp

RUN ln -s python2.7 /usr/bin/python2
RUN ln -s python3   /usr/bin/python

# Install pwsh, and other PS/.NET sanity test tools.
RUN apt-get update -y && \
    curl --silent --location https://github.com/PowerShell/PowerShell/releases/download/v7.0.1/powershell_7.0.1-1.ubuntu.18.04_amd64.deb -o /tmp/pwsh.deb \
    && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends /tmp/pwsh.deb \
    && \
    rm /tmp/pwsh.deb \
    && \
    apt-get clean
RUN pwsh --version
COPY requirements/sanity.ps1 /tmp/
RUN /tmp/sanity.ps1 -IsContainer && rm /tmp/sanity.ps1

ENV container=docker
CMD ["/sbin/init"]

# Install pip and requirements last to speed up local container rebuilds when updating requirements.

ADD https://ansible-ci-files.s3.amazonaws.com/ansible-test/get-pip-9.0.3.py /tmp/get-pip-9.0.3.py
ADD https://ansible-ci-files.s3.amazonaws.com/ansible-test/get-pip-20.3.4.py /tmp/get-pip-20.3.4.py
ADD https://ansible-ci-files.s3.amazonaws.com/ansible-test/get-pip-21.0.1.py /tmp/get-pip-21.0.1.py

COPY files/pydistutils.cfg /tmp/
COPY files/requirements.sh /tmp/
COPY files/early-requirements.txt /tmp/
COPY requirements/*.txt /tmp/requirements/
COPY freeze/*.txt /tmp/freeze/

RUN /tmp/requirements.sh 2.6
RUN /tmp/requirements.sh 2.7
RUN /tmp/requirements.sh 3.5
RUN /tmp/requirements.sh 3.7
RUN /tmp/requirements.sh 3.8
RUN /tmp/requirements.sh 3.9
RUN /tmp/requirements.sh 3.10
RUN /tmp/requirements.sh 3.6
