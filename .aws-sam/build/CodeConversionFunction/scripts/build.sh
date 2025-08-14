#!/bin/bash

# Build script for MCP Converter
set -e

echo "Building MCP GitHub Shell to Python Converter..."

# Build Docker image
docker build -t mcp-converter:latest .

# Tag for your registry (replace with your registry)
# docker tag mcp-converter:latest your-registry.com/mcp-converter:latest

echo "Build completed successfully!"
echo "To push to registry, run:"
echo "docker push your-registry.com/mcp-converter:latest"