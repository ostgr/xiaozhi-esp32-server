#!/bin/bash
set -e

echo "=========================================="
echo "Building xiaozhi-server Docker Images"
echo "=========================================="

cd "$(dirname "$0")"

# Build base image
echo -e "\n[1/2] Building base image..."
DOCKER_BUILDKIT=1 docker build \
    -f Dockerfile-server-base \
    -t xiaozhi-server:base \
    .

echo "✓ Base image built: xiaozhi-server:base"

# Build application image
echo -e "\n[2/2] Building application image..."
DOCKER_BUILDKIT=1 docker build \
    -f Dockerfile-server \
    -t xiaozhi-server:latest \
    .

echo "✓ Application image built: xiaozhi-server:latest"

# Display summary
echo -e "\n=========================================="
echo "Build Complete!"
echo "=========================================="
docker images | grep xiaozhi-server | head -2

echo -e "\nTo run the server:"
echo "  cd ../"
echo "  docker compose -f docker-compose.xiaozhi.yml up -d"
