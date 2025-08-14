#!/bin/bash

# Setup secrets for Kubernetes deployment
set -e

echo "Setting up Kubernetes secrets..."

# Check if required environment variables are set
if [ -z "$GITHUB_TOKEN" ]; then
    read -p "Enter your GitHub Personal Access Token: " GITHUB_TOKEN
fi

if [ -z "$OPENAI_API_KEY" ]; then
    read -p "Enter your OpenAI API Key: " OPENAI_API_KEY
fi

# Create namespace if it doesn't exist
kubectl create namespace mcp-converter --dry-run=client -o yaml | kubectl apply -f -

# Create secrets
kubectl create secret generic mcp-converter-secrets \
    --from-literal=github-token="$GITHUB_TOKEN" \
    --from-literal=openai-api-key="$OPENAI_API_KEY" \
    --namespace=mcp-converter \
    --dry-run=client -o yaml | kubectl apply -f -

echo "Secrets created successfully!"