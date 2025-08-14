#!/bin/bash

# Deployment script for Kubernetes
set -e

echo "Deploying MCP Converter to Kubernetes..."

# Apply Kubernetes manifests in order
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secrets.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/rbac.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/networkpolicy.yaml

# Optional: Apply ingress (uncomment if you have ingress controller)
# kubectl apply -f k8s/ingress.yaml

echo "Deployment completed!"
echo "Checking deployment status..."
kubectl get pods -n mcp-converter
kubectl get svc -n mcp-converter

echo "To check logs, run:"
echo "kubectl logs -f deployment/mcp-converter -n mcp-converter"