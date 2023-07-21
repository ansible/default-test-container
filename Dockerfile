FROM quay.io/ansible/base-test-container:5.1.0

COPY requirements /usr/share/container-setup/default/requirements/
COPY freeze /usr/share/container-setup/default/freeze/

RUN pwsh /usr/share/container-setup/default/requirements/sanity.pslint.ps1 -IsContainer && \
    rm -rf /tmp/.dotnet /tmp/Microsoft.PackageManagement

RUN cd /tmp && echo 'Cython < 3' > constraints.txt && \
    PIP_CONSTRAINT=/tmp/constraints.txt python2.7 -m pip install pyyaml==5.4.1 && \
    rm -r constraints.txt /root/.cache/pip

COPY files/requirements.py /usr/share/container-setup/
RUN /usr/share/container-setup/python -B /usr/share/container-setup/requirements.py default

COPY files/prime.py files/ansible-test-*.txt /usr/share/container-setup/
RUN /usr/share/container-setup/python -B /usr/share/container-setup/prime.py default
