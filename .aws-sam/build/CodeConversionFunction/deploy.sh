#!/bin/bash

# 🚀 CodeConversion Server - Single Click AWS Deployment
# ======================================================
# Deploy or destroy your serverless application with one command
#
# Usage:
#   ./deploy.sh deploy   - Deploy the application
#   ./deploy.sh destroy  - Destroy the application
#   ./deploy.sh status   - Check deployment status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Configuration
STACK_NAME="codeconversion-server"
AWS_REGION="ap-south-1"
ENVIRONMENT="production"

# Ensure we're in the correct directory
cd "$(dirname "$0")"

echo -e "${PURPLE}🎯 CodeConversion Server - AWS Deployment Tool${NC}"
echo -e "${PURPLE}================================================${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found${NC}"
        echo -e "${YELLOW}💡 Install with: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html${NC}"
        exit 1
    fi
    
    # Check SAM CLI
    if ! command -v sam &> /dev/null; then
        echo -e "${RED}❌ AWS SAM CLI not found${NC}"
        echo -e "${YELLOW}💡 Install with: pip install aws-sam-cli${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity --region "$AWS_REGION" &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured or invalid${NC}"
        echo -e "${YELLOW}💡 Configure with: aws configure${NC}"
        exit 1
    fi
    
    # Check if GitHub App private key exists
    if [ ! -f "github-app-private-key.pem" ]; then
        echo -e "${YELLOW}⚠️  GitHub App private key not found${NC}"
        echo -e "${YELLOW}💡 Place your GitHub App private key as 'github-app-private-key.pem'${NC}"
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to deploy the application
deploy_application() {
    echo -e "${BLUE}🚀 Starting deployment...${NC}"
    
    # Build the application
    echo -e "${YELLOW}🔨 Building SAM application...${NC}"
    sam build --use-container --region "$AWS_REGION"
    
    # Deploy the application
    echo -e "${YELLOW}☁️ Deploying to AWS...${NC}"
    sam deploy \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --parameter-overrides Environment="$ENVIRONMENT" \
        --capabilities CAPABILITY_IAM \
        --resolve-s3 \
        --no-confirm-changeset \
        --no-fail-on-empty-changeset
    
    # Get deployment outputs
    echo -e "${YELLOW}📤 Retrieving deployment information...${NC}"
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
        --output text 2>/dev/null || echo "Not available")
    
    WEBHOOK_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='WebhookUrl'].OutputValue" \
        --output text 2>/dev/null || echo "Not available")
    
    SECRETS_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='SecretsBucket'].OutputValue" \
        --output text 2>/dev/null || echo "Not available")
    
    # Upload GitHub App private key if available
    if [ -f "github-app-private-key.pem" ] && [ "$SECRETS_BUCKET" != "Not available" ]; then
        echo -e "${YELLOW}🔐 Uploading GitHub App private key...${NC}"
        aws s3 cp github-app-private-key.pem "s3://$SECRETS_BUCKET/github-app-private-key.pem" \
            --region "$AWS_REGION" || echo -e "${YELLOW}⚠️ Failed to upload private key${NC}"
    fi
    
    # Update secrets if .env file exists
    if [ -f ".env" ]; then
        echo -e "${YELLOW}🔑 Updating secrets from .env file...${NC}"
        source .env
        
        # Update GitHub App secrets
        GITHUB_SECRET_NAME="${STACK_NAME}/github-app"
        GITHUB_SECRETS=$(cat <<EOF
{
  "GITHUB_APP_ID": "${GITHUB_APP_ID:-1759505}",
  "GITHUB_APP_SLUG": "${GITHUB_APP_SLUG:-codeconversion}",
  "GITHUB_CLIENT_ID": "${GITHUB_CLIENT_ID:-Iv23ligOQSHy1IBac2Yq}",
  "GITHUB_CLIENT_SECRET": "${GITHUB_CLIENT_SECRET:-REPLACE_WITH_YOUR_SECRET}",
  "GITHUB_WEBHOOK_SECRET": "${GITHUB_WEBHOOK_SECRET:-123456}"
}
EOF
        )
        
        aws secretsmanager update-secret \
            --secret-id "$GITHUB_SECRET_NAME" \
            --secret-string "$GITHUB_SECRETS" \
            --region "$AWS_REGION" 2>/dev/null || \
            echo -e "${YELLOW}⚠️ Could not update GitHub secrets (may not exist yet)${NC}"
        
        # Update application secrets
        APP_SECRET_NAME="${STACK_NAME}/app-secrets"
        APP_SECRETS=$(cat <<EOF
{
  "OPENAI_API_KEY": "${OPENAI_API_KEY:-REPLACE_WITH_YOUR_OPENAI_KEY}",
  "ENCRYPTION_KEY": "${ENCRYPTION_KEY:-UTFAlC02TcIlDKRDEf5A6sYiuQSbWSmUiD_Om2eSQyM=}"
}
EOF
        )
        
        aws secretsmanager update-secret \
            --secret-id "$APP_SECRET_NAME" \
            --secret-string "$APP_SECRETS" \
            --region "$AWS_REGION" 2>/dev/null || \
            echo -e "${YELLOW}⚠️ Could not update app secrets (may not exist yet)${NC}"
    fi
    
    # Test deployment
    echo -e "${YELLOW}🧪 Testing deployment...${NC}"
    if [ "$API_URL" != "Not available" ]; then
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" --max-time 30 || echo "000")
        if [ "$HTTP_CODE" = "200" ]; then
            echo -e "${GREEN}✅ Health check passed${NC}"
        else
            echo -e "${YELLOW}⚠️ Health check returned: $HTTP_CODE (Lambda may be cold starting)${NC}"
        fi
    fi
    
    # Display results
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${CYAN}📊 Deployment Information:${NC}"
    echo -e "  🌐 API URL: $API_URL"
    echo -e "  🪝 Webhook URL: $WEBHOOK_URL"
    echo -e "  🪣 Secrets Bucket: $SECRETS_BUCKET"
    echo -e "  🌍 Region: $AWS_REGION"
    echo -e "  📦 Stack: $STACK_NAME"
    
    echo -e "${BLUE}📋 Next Steps:${NC}"
    echo -e "  1. Update GitHub App webhook URL: $WEBHOOK_URL"
    echo -e "  2. Update secrets in AWS Secrets Manager if needed"
    echo -e "  3. Test your endpoints at: $API_URL"
    
    echo -e "${CYAN}💡 Useful Commands:${NC}"
    echo -e "  📜 View logs: aws logs tail /aws/lambda/$STACK_NAME-api --follow --region $AWS_REGION"
    echo -e "  🔍 Check status: ./deploy.sh status"
    echo -e "  💥 Destroy: ./deploy.sh destroy"
}

# Function to destroy the application
destroy_application() {
    echo -e "${RED}💥 Destroying deployment...${NC}"
    
    # Get bucket name before destroying
    SECRETS_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='SecretsBucket'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    # Empty S3 bucket if it exists
    if [ ! -z "$SECRETS_BUCKET" ] && [ "$SECRETS_BUCKET" != "None" ]; then
        echo -e "${YELLOW}🗑️ Emptying S3 bucket...${NC}"
        aws s3 rm "s3://$SECRETS_BUCKET" --recursive --region "$AWS_REGION" 2>/dev/null || true
    fi
    
    # Delete the CloudFormation stack
    echo -e "${YELLOW}🗑️ Deleting CloudFormation stack...${NC}"
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
    
    # Wait for deletion to complete
    echo -e "${YELLOW}⏳ Waiting for stack deletion to complete...${NC}"
    aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" || true
    
    echo -e "${GREEN}✅ Application destroyed successfully${NC}"
    echo -e "${BLUE}💡 All AWS resources have been cleaned up${NC}"
}

# Function to check deployment status
check_status() {
    echo -e "${BLUE}📊 Checking deployment status...${NC}"
    
    # Check if stack exists
    STACK_STATUS=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].StackStatus" \
        --output text 2>/dev/null || echo "DOES_NOT_EXIST")
    
    if [ "$STACK_STATUS" = "DOES_NOT_EXIST" ]; then
        echo -e "${YELLOW}⚠️ Stack does not exist${NC}"
        echo -e "${BLUE}💡 Run './deploy.sh deploy' to create it${NC}"
        return
    fi
    
    echo -e "${CYAN}📦 Stack Status: $STACK_STATUS${NC}"
    
    if [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
        # Get outputs
        API_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" \
            --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
            --output text 2>/dev/null || echo "Not available")
        
        WEBHOOK_URL=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" \
            --query "Stacks[0].Outputs[?OutputKey=='WebhookUrl'].OutputValue" \
            --output text 2>/dev/null || echo "Not available")
        
        echo -e "${GREEN}✅ Application is running${NC}"
        echo -e "  🌐 API URL: $API_URL"
        echo -e "  🪝 Webhook URL: $WEBHOOK_URL"
        
        # Test health endpoint
        if [ "$API_URL" != "Not available" ]; then
            HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" --max-time 10 || echo "000")
            if [ "$HTTP_CODE" = "200" ]; then
                echo -e "${GREEN}✅ Health check: OK${NC}"
            else
                echo -e "${YELLOW}⚠️ Health check: $HTTP_CODE${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️ Stack is in transition state: $STACK_STATUS${NC}"
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}Usage: ./deploy.sh [command]${NC}"
    echo -e ""
    echo -e "${YELLOW}Commands:${NC}"
    echo -e "  deploy   - Deploy the application to AWS"
    echo -e "  destroy  - Destroy the application and clean up resources"
    echo -e "  status   - Check the current deployment status"
    echo -e "  help     - Show this help message"
    echo -e ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo -e "  Stack Name: $STACK_NAME"
    echo -e "  Region: $AWS_REGION"
    echo -e "  Environment: $ENVIRONMENT"
    echo -e ""
    echo -e "${YELLOW}Cost Optimization:${NC}"
    echo -e "  • Uses db.t3.micro RDS instance"
    echo -e "  • Lambda memory: 512MB"
    echo -e "  • Concurrency limit: 5"
    echo -e "  • ap-south-1 region for lower costs"
}

# Main script logic
case "${1:-help}" in
    deploy)
        check_prerequisites
        deploy_application
        ;;
    destroy)
        echo -e "${RED}⚠️ This will permanently delete all resources!${NC}"
        read -p "Are you sure you want to continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            destroy_application
        else
            echo -e "${BLUE}❌ Operation cancelled${NC}"
        fi
        ;;
    status)
        check_status
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        echo -e "${RED}❌ Invalid command: $1${NC}"
        show_help
        exit 1
        ;;
esac
