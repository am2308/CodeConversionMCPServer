#!/bin/bash

# Script to update AWS Secrets Manager with values from .env file
# Usage: ./update-secrets.sh

STACK_NAME="codeconversion-server"

echo "🔑 Updating AWS Secrets Manager with environment values"
echo "====================================================="

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found. Please create it first."
    exit 1
fi

# Source the .env file
set -a
source .env
set +a

echo "📋 Found environment variables:"
echo "  - GITHUB_APP_ID: $GITHUB_APP_ID"
echo "  - GITHUB_CLIENT_ID: $GITHUB_CLIENT_ID"
echo "  - OPENAI_API_KEY: ${OPENAI_API_KEY:0:20}..."
echo "  - ENCRYPTION_KEY: ${ENCRYPTION_KEY:0:20}..."

# Get secret names from CloudFormation
echo ""
echo "🔍 Getting secret names from CloudFormation..."

GITHUB_SECRET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`GitHubAppSecretName`].OutputValue' \
    --output text 2>/dev/null)

APP_SECRET_NAME=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`AppSecretName`].OutputValue' \
    --output text 2>/dev/null)

if [ -z "$GITHUB_SECRET_NAME" ] || [ -z "$APP_SECRET_NAME" ]; then
    echo "❌ Could not get secret names from CloudFormation stack"
    exit 1
fi

echo "✅ Found secrets:"
echo "  - GitHub App Secret: $GITHUB_SECRET_NAME"
echo "  - App Secret: $APP_SECRET_NAME"

# Update GitHub App secrets
echo ""
echo "🔄 Updating GitHub App secrets..."

GITHUB_SECRET_JSON=$(cat <<EOF
{
  "GITHUB_APP_ID": "$GITHUB_APP_ID",
  "GITHUB_APP_SLUG": "$GITHUB_APP_SLUG",
  "GITHUB_CLIENT_ID": "$GITHUB_CLIENT_ID",
  "GITHUB_CLIENT_SECRET": "$GITHUB_CLIENT_SECRET",
  "GITHUB_WEBHOOK_SECRET": "$GITHUB_WEBHOOK_SECRET"
}
EOF
)

aws secretsmanager update-secret \
    --secret-id "$GITHUB_SECRET_NAME" \
    --secret-string "$GITHUB_SECRET_JSON" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ GitHub App secrets updated successfully"
else
    echo "❌ Failed to update GitHub App secrets"
fi

# Update Application secrets
echo ""
echo "🔄 Updating Application secrets..."

APP_SECRET_JSON=$(cat <<EOF
{
  "OPENAI_API_KEY": "$OPENAI_API_KEY",
  "ENCRYPTION_KEY": "$ENCRYPTION_KEY"
}
EOF
)

aws secretsmanager update-secret \
    --secret-id "$APP_SECRET_NAME" \
    --secret-string "$APP_SECRET_JSON" > /dev/null

if [ $? -eq 0 ]; then
    echo "✅ Application secrets updated successfully"
else
    echo "❌ Failed to update Application secrets"
fi

# Upload GitHub App private key to S3
echo ""
echo "🔄 Uploading GitHub App private key to S3..."

SECRETS_BUCKET=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`SecretsBucket`].OutputValue' \
    --output text 2>/dev/null)

if [ -n "$SECRETS_BUCKET" ] && [ -f "github-app-private-key.pem" ]; then
    aws s3 cp github-app-private-key.pem s3://$SECRETS_BUCKET/github-app-private-key.pem > /dev/null
    
    if [ $? -eq 0 ]; then
        echo "✅ GitHub App private key uploaded to S3"
    else
        echo "❌ Failed to upload GitHub App private key"
    fi
else
    echo "⚠️  Skipped: No S3 bucket found or github-app-private-key.pem missing"
fi

echo ""
echo "🎉 Secrets update completed!"
echo "📱 Next steps:"
echo "   1. Test the frontend: open frontend-example.html"
echo "   2. Register a user"
echo "   3. Install GitHub App (link will be provided in the UI)"
echo "   4. Test repository conversion"
