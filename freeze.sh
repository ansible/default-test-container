#!/usr/bin/env bash

set -eu

versions=$(grep '^RUN /tmp/requirements.sh ' Dockerfile | sed 's|^RUN /tmp/requirements.sh ||;')

echo "Purging existing frozen requirements ..."
rm -f freeze/*

echo "Building a container to freeze the requirements ..."

docker build -t default-test-container-freezer .

for version in ${versions}; do
    echo "Freezing requirements for Python ${version} ..."
    docker run -it default-test-container-freezer "pip${version}" freeze -qqq --disable-pip-version-check | tr -d '\r' > "freeze/${version}.txt"
done

echo "Completed freeze process. You can build the container now."
