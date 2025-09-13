#!/bin/bash

echo "Building aio-dynamic-push with Cypress support..."

# Build the Docker image
docker build -t aio-dynamic-push-cypress . --progress=plain

if [ $? -eq 0 ]; then
    echo "✅ Docker build successful!"
    echo ""
    echo "To test Cypress functionality, run:"
    echo "docker-compose -f docker-compose.cypress.yml up"
    echo ""
    echo "Or run the test directly:"
    echo "docker run --rm -it aio-dynamic-push-cypress sh -c 'Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & python test_docker_cypress.py'"
else
    echo "❌ Docker build failed!"
    exit 1
fi
