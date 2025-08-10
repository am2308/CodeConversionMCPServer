#!/bin/bash

# 🚀 CodeConversion Server - Single Click AWS Deployment & Destroy
# =================================================================
# Deploy or destroy your serverless application with one command
#
# Usage:
#   ./deploy-aws.sh deploy   - Deploy the application
#   ./deploy-aws.sh destroy  - Destroy the application
#   ./deploy-aws.sh status   - Check deployment status

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME=${STACK_NAME:-"codeconversion-server"}
ENVIRONMENT=${ENVIRONMENT:-"production"}
AWS_REGION=${AWS_REGION:-"ap-south-1"}  # Cost-optimized region

echo -e "${PURPLE}🎯 CodeConversion Server - AWS Management Tool${NC}"
echo -e "${PURPLE}===============================================${NC}"

# Function to check prerequisites
check_prerequisites() {
    echo -e "${YELLOW}📋 Checking prerequisites...${NC}"
    
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
        echo -e "${YELLOW}💡 Install with: https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html${NC}"
        exit 1
    fi
    
    if ! command -v sam &> /dev/null; then
        echo -e "${RED}❌ AWS SAM CLI not found. Please install it first.${NC}"
        echo -e "${YELLOW}💡 Install with: pip install aws-sam-cli${NC}"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity --region "$AWS_REGION" &> /dev/null; then
        echo -e "${RED}❌ AWS credentials not configured. Run 'aws configure' first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Prerequisites check passed${NC}"
}

# Function to deploy the application
deploy_application() {
    echo -e "${BLUE}🚀 Starting deployment...${NC}"
    
    # Check for GitHub App private key
    GITHUB_APP_PRIVATE_KEY_PATH="github-app-private-key.pem"
    if [ ! -f "$GITHUB_APP_PRIVATE_KEY_PATH" ]; then
        echo -e "${YELLOW}⚠️ GitHub App private key not found at: $GITHUB_APP_PRIVATE_KEY_PATH${NC}"
        echo -e "${YELLOW}💡 Place your GitHub App private key as 'github-app-private-key.pem'${NC}"
    fi

    # Step 1: Build the SAM application
    echo -e "${YELLOW}🔨 Building SAM application...${NC}"
    sam build --use-container --region "$AWS_REGION"
    
    # Step 2: Deploy infrastructure
    echo -e "${YELLOW}☁️ Deploying infrastructure...${NC}"
    sam deploy \
        --stack-name "$STACK_NAME" \
        --parameter-overrides \
            Environment="$ENVIRONMENT" \
        --capabilities CAPABILITY_IAM \
        --resolve-s3 \
        --region "$AWS_REGION" \
        --no-confirm-changeset \
        --no-fail-on-empty-changeset
    
    # Step 3: Get stack outputs
    echo -e "${YELLOW}📤 Getting stack outputs...${NC}"
    SECRETS_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='SecretsBucket'].OutputValue" \
        --output text \
        --region "$AWS_REGION")
    
    API_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='ApiUrl'].OutputValue" \
        --output text \
        --region "$AWS_REGION")
    
    WEBHOOK_URL=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='WebhookUrl'].OutputValue" \
        --output text \
        --region "$AWS_REGION")
    
    GITHUB_SECRET_ARN=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query "Stacks[0].Outputs[?OutputKey=='GitHubAppSecretArn'].OutputValue" \
        --output text \
        --region "$AWS_REGION")
    
    echo -e "${GREEN}✅ Infrastructure deployed successfully${NC}"
    
    # Step 4: Upload GitHub App private key to S3 (if available)
    if [ -f "$GITHUB_APP_PRIVATE_KEY_PATH" ]; then
        echo -e "${YELLOW}🔐 Uploading GitHub App private key to S3...${NC}"
        aws s3 cp "$GITHUB_APP_PRIVATE_KEY_PATH" "s3://$SECRETS_BUCKET/github-app-private-key.pem" \
            --region "$AWS_REGION"
        echo -e "${GREEN}✅ Private key uploaded to S3${NC}"
    fi
    
    # Step 5: Update secrets in AWS Secrets Manager (if .env exists)
    if [ -f ".env" ]; then
        echo -e "${YELLOW}🔑 Updating secrets in AWS Secrets Manager...${NC}"
        source .env
        
        # Update GitHub App secrets
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
            --secret-id "$GITHUB_SECRET_ARN" \
            --secret-string "$GITHUB_SECRETS" \
            --region "$AWS_REGION"
        
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
            --region "$AWS_REGION"
        
        echo -e "${GREEN}✅ Secrets updated in AWS Secrets Manager${NC}"
    fi
    
    # Step 6: Test the deployment
    echo -e "${YELLOW}🧪 Testing deployment...${NC}"
    HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/health" --max-time 30 || echo "000")
    
    if [ "$HEALTH_CHECK" = "200" ]; then
        echo -e "${GREEN}✅ Health check passed${NC}"
    else
        echo -e "${YELLOW}⚠️ Health check returned: $HEALTH_CHECK (Lambda may be cold starting)${NC}"
    fi
    
    # Display results
    echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"
    echo -e "${CYAN}📊 Deployment Information:${NC}"
    echo -e "  🌐 API URL: $API_URL"
    echo -e "  🪝 Webhook URL: $WEBHOOK_URL"
    echo -e "  🪣 Secrets Bucket: $SECRETS_BUCKET"
    echo -e "  🌍 Region: $AWS_REGION"
    echo -e "  📦 Stack: $STACK_NAME"
    
    echo -e "${BLUE}� Next Steps:${NC}"
    echo -e "  1. Update GitHub App webhook URL: $WEBHOOK_URL"
    echo -e "  2. Update secrets in AWS Secrets Manager if needed"
    echo -e "  3. Test your endpoints at: $API_URL"
    
    echo -e "${CYAN}💡 Useful Commands:${NC}"
    echo -e "  📜 View logs: aws logs tail /aws/lambda/$STACK_NAME-api --follow --region $AWS_REGION"
    echo -e "  🔍 Check status: ./deploy-aws.sh status"
    echo -e "  💥 Destroy: ./deploy-aws.sh destroy"
}

# Function to destroy the application
destroy_application() {
    echo -e "${RED}💥 Destroying deployment...${NC}"
    echo -e "${RED}⚠️ This will permanently delete all resources including the database!${NC}"
    
    # Get bucket name and other resources before destroying
    echo -e "${YELLOW}📤 Getting resource information...${NC}"
    
    SECRETS_BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" \
        --query "Stacks[0].Outputs[?OutputKey=='SecretsBucket'].OutputValue" \
        --output text 2>/dev/null || echo "")
    
    # Empty S3 bucket if it exists
    if [ ! -z "$SECRETS_BUCKET" ] && [ "$SECRETS_BUCKET" != "None" ] && [ "$SECRETS_BUCKET" != "null" ]; then
        echo -e "${YELLOW}🗑️ Emptying S3 bucket: $SECRETS_BUCKET${NC}"
        aws s3 rm "s3://$SECRETS_BUCKET" --recursive --region "$AWS_REGION" 2>/dev/null || true
        echo -e "${GREEN}✅ S3 bucket emptied${NC}"
    fi
    
    # Delete the CloudFormation stack
    echo -e "${YELLOW}🗑️ Deleting CloudFormation stack: $STACK_NAME${NC}"
    aws cloudformation delete-stack \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION"
    
    # Wait for deletion to complete
    echo -e "${YELLOW}⏳ Waiting for stack deletion to complete (this may take 10-15 minutes)...${NC}"
    echo -e "${BLUE}💡 You can safely cancel this wait and check status later with: ./deploy-aws.sh status${NC}"
    
    # Use timeout to avoid waiting too long
    timeout 900 aws cloudformation wait stack-delete-complete \
        --stack-name "$STACK_NAME" \
        --region "$AWS_REGION" 2>/dev/null || {
        echo -e "${YELLOW}⏰ Timeout reached. Checking current status...${NC}"
        
        STACK_STATUS=$(aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --region "$AWS_REGION" \
            --query "Stacks[0].StackStatus" \
            --output text 2>/dev/null || echo "DELETE_COMPLETE")
        
        if [ "$STACK_STATUS" = "DELETE_COMPLETE" ] || [ "$STACK_STATUS" = "DOES_NOT_EXIST" ]; then
            echo -e "${GREEN}✅ Stack deletion completed${NC}"
        else
            echo -e "${YELLOW}⚠️ Stack deletion in progress. Current status: $STACK_STATUS${NC}"
            echo -e "${BLUE}💡 Check status later with: ./deploy-aws.sh status${NC}"
        fi
    }
    
    echo -e "${GREEN}✅ Application destruction initiated${NC}"
    echo -e "${BLUE}💰 All AWS resources are being cleaned up to save costs${NC}"
    echo -e "${CYAN}📊 Cost Savings:${NC}"
    echo -e "  • RDS database stopped/deleted"
    echo -e "  • Lambda functions removed"
    echo -e "  • API Gateway deleted"
    echo -e "  • VPC and networking resources removed"
    echo -e "  • S3 bucket and secrets cleaned up"
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
        echo -e "${BLUE}💡 Run './deploy-aws.sh deploy' to create it${NC}"
        return
    fi
    
    echo -e "${CYAN}📦 Stack Status: $STACK_STATUS${NC}"
    
    if [[ "$STACK_STATUS" == *"IN_PROGRESS"* ]]; then
        echo -e "${YELLOW}⚠️ Stack operation in progress...${NC}"
        echo -e "${BLUE}💡 Wait for the operation to complete${NC}"
    elif [ "$STACK_STATUS" = "CREATE_COMPLETE" ] || [ "$STACK_STATUS" = "UPDATE_COMPLETE" ]; then
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
        echo -e "${RED}❌ Stack is in failed state: $STACK_STATUS${NC}"
        echo -e "${BLUE}💡 You may need to delete and redeploy${NC}"
    fi
}

# Function to show help
show_help() {
    echo -e "${BLUE}Usage: ./deploy-aws.sh [command]${NC}"
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
    echo -e "${YELLOW}Cost Optimization Features:${NC}"
    echo -e "  • Uses ap-south-1 region for lower costs"
    echo -e "  • db.t3.micro RDS instance"
    echo -e "  • Lambda memory: 512MB"
    echo -e "  • Concurrency limit: 5"
    echo -e "  • Single-click destroy to save costs"
    echo -e ""
    echo -e "${YELLOW}Prerequisites:${NC}"
    echo -e "  • AWS CLI configured"
    echo -e "  • AWS SAM CLI installed"
    echo -e "  • github-app-private-key.pem file"
    echo -e "  • .env file with secrets (optional)"
}

# Main script logic
case "${1:-help}" in
    deploy)
        check_prerequisites
        deploy_application
        ;;
    destroy)
        echo -e "${RED}⚠️ DANGER: This will permanently delete ALL resources!${NC}"
        echo -e "${RED}This includes:${NC}"
        echo -e "${RED}  • Database and all data${NC}"
        echo -e "${RED}  • Lambda functions${NC}"
        echo -e "${RED}  • API Gateway${NC}"
        echo -e "${RED}  • S3 bucket and files${NC}"
        echo -e "${RED}  • Secrets and configurations${NC}"
        echo ""
        read -p "Are you absolutely sure you want to continue? (y/N): " -n 1 -r
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
