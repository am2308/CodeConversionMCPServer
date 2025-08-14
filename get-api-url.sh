#!/bin/bash

# Script to get the API URL from CloudFormation stack
# Usage: ./get-api-url.sh [stack-name]

STACK_NAME=${1:-codeconversion-server}

echo "🔍 Getting API URL from CloudFormation stack: $STACK_NAME"
echo "=================================================="

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI is not installed. Please install it first."
    exit 1
fi

# Get the API URL
API_URL=$(aws cloudformation describe-stacks \
    --stack-name "$STACK_NAME" \
    --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
    --output text 2>/dev/null)

if [ $? -eq 0 ] && [ -n "$API_URL" ]; then
    echo "✅ API URL found:"
    echo ""
    echo "    $API_URL"
    echo ""
    echo "📋 Copy this URL and paste it into the frontend configuration."
    echo "🌐 You can also open frontend-example.html in your browser now."
    echo ""
    
    # Test the health endpoint
    echo "🔍 Testing API health endpoint..."
    if command -v curl &> /dev/null; then
        HEALTH_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health")
        if [ "$HEALTH_RESPONSE" -eq 200 ]; then
            echo "✅ API is healthy and responding!"
        else
            echo "⚠️  API returned status code: $HEALTH_RESPONSE"
        fi
    else
        echo "ℹ️  Install curl to test API health automatically"
    fi
    
else
    echo "❌ Failed to get API URL. Possible reasons:"
    echo "   - Stack '$STACK_NAME' doesn't exist"
    echo "   - AWS credentials not configured"
    echo "   - Wrong region selected"
    echo ""
    echo "💡 Try:"
    echo "   aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE"
fi

echo ""
echo "🛠️  Stack management commands:"
echo "   Deploy:  ./deploy-aws.sh deploy"
echo "   Status:  ./deploy-aws.sh status"  
echo "   Destroy: ./deploy-aws.sh destroy"
