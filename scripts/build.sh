#!/bin/sh
set -eu

echo "INFO: Building docker-reforger-test image..."

docker build -t docker-reforger-test .

echo "INFO: docker-reforger-test is built. Please update your docker compose."
