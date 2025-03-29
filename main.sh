#!/bin/bash
# PC deploy script (no need for Jetson-specific code)

echo "Deploying orchestrator and frontend on PC..."

# Create necessary directories
mkdir -p projects

# Build and start only the orchestrator and frontend
docker-compose build orchestrator frontend
docker-compose up -d orchestrator frontend

echo "Services started:"
echo "- Orchestrator on port 9999"
echo "- Frontend on port 3333"