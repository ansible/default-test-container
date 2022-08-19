FROM quay.io/ansible/base-test-container:3.5.0

COPY requirements /usr/share/container-setup/default/requirements/
COPY freeze /usr/share/container-setup/default/freeze/

RUN pwsh /usr/share/container-setup/default/requirements/sanity.pslint.ps1 -IsContainer

COPY files/requirements.py /usr/share/container-setup/
RUN python3.10 -B /usr/share/container-setup/requirements.py default

COPY files/prime.py files/ansible-test-*.txt /usr/share/container-setup/
RUN python3.10 -B /usr/share/container-setup/prime.py default
