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

echo "Fixing bad frozen versions ..."

for version in ${versions}; do
    echo "Fixing frozen versions for Python ${version} ..."
    sed 's/^solidfire-sdk-python==1.5.0.87$/solidfire-sdk-python==1.5.0.87.post1  # .post1 required for successful install/' < "freeze/${version}.txt" > /tmp/freeze.txt
    mv /tmp/freeze.txt "freeze/${version}.txt"
done

echo "Completed freeze process. You can build the container now."
