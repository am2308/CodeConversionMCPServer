# AWS Serverless Deployment Guide

## 🏗️ Architecture Overview

Your CodeConversion service will be deployed as:
- **API Gateway**: HTTPS endpoints with custom domain
- **Lambda Functions**: FastAPI application using Mangum adapter
- **RDS Postgres**: Managed database with automatic backups
- **Secrets Manager**: Secure storage for credentials
- **CloudFormation**: Infrastructure as Code
- **S3**: Static assets and logs

## 📋 Prerequisites

1. **AWS Account** with programmatic access
2. **AWS CLI** configured
3. **Domain name** (optional, for custom domain)
4. **GitHub App credentials** (already have)

## 🛠️ Deployment Steps

### Step 1: Install AWS Tools
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install AWS SAM CLI
pip install aws-sam-cli

# Configure AWS credentials
aws configure
```

### Step 2: Deploy Infrastructure
```bash
# Deploy the CloudFormation stack
aws cloudformation deploy \
  --template-file aws/infrastructure.yml \
  --stack-name codeconversion-infrastructure \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    Environment=production \
    DomainName=your-domain.com

# Deploy the application
sam build
sam deploy --guided
```

### Step 3: Configure Secrets
```bash
# Store GitHub App credentials in AWS Secrets Manager
aws secretsmanager create-secret \
  --name codeconversion/github-app \
  --description "GitHub App credentials for CodeConversion" \
  --secret-string '{
    "GITHUB_APP_ID": "1759505",
    "GITHUB_CLIENT_ID": "Iv23ligOQSHy1IBac2Yq",
    "GITHUB_CLIENT_SECRET": "your_secret",
    "GITHUB_WEBHOOK_SECRET": "123456"
  }'

# Store other credentials
aws secretsmanager create-secret \
  --name codeconversion/app-secrets \
  --secret-string '{
    "OPENAI_API_KEY": "your_openai_key",
    "ENCRYPTION_KEY": "UTFAlC02TcIlDKRDEf5A6sYiuQSbWSmUiD_Om2eSQyM="
  }'
```

### Step 4: Upload Private Key
```bash
# Upload GitHub App private key to S3
aws s3 cp github-app-private-key.pem \
  s3://codeconversion-secrets-bucket/github-app-private-key.pem \
  --server-side-encryption AES256
```

### Step 5: Update GitHub App Webhook
```bash
# Get your API Gateway URL
aws cloudformation describe-stacks \
  --stack-name codeconversion-app \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiUrl`].OutputValue' \
  --output text

# Update GitHub App webhook URL to:
# https://your-api-id.execute-api.region.amazonaws.com/prod/webhooks/github
```

## 🔧 Configuration

### Environment Variables (managed by AWS)
- **Secrets Manager**: All sensitive credentials
- **Systems Manager**: Configuration parameters
- **Lambda Environment**: Runtime configuration

### Custom Domain (Optional)
```bash
# Create custom domain mapping
aws apigateway create-domain-name \
  --domain-name api.your-domain.com \
  --certificate-arn arn:aws:acm:region:account:certificate/cert-id
```

## 📈 Monitoring & Scaling

### Auto-scaling
- **Lambda**: Automatically scales to handle requests
- **RDS**: Can enable auto-scaling for read replicas
- **API Gateway**: Built-in rate limiting and throttling

### Monitoring
- **CloudWatch**: Logs and metrics
- **X-Ray**: Distributed tracing
- **CloudWatch Alarms**: Error rate and latency alerts

## 💰 Cost Optimization

### Estimated Monthly Costs (for moderate usage)
- **Lambda**: $5-20 (first 1M requests free)
- **API Gateway**: $3-10 (first 1M requests free)
- **RDS**: $15-50 (t3.micro instance)
- **Secrets Manager**: $1-5
- **Total**: ~$25-85/month

### Cost Reduction Tips
- Use **Aurora Serverless v2** for database
- Enable **Lambda Provisioned Concurrency** only if needed
- Use **CloudFront** for caching if high traffic

## 🚀 Benefits of AWS Serverless

### Reliability
- ✅ **99.9%+ uptime** with multi-AZ deployment
- ✅ **Automatic failover** and disaster recovery
- ✅ **Managed services** reduce operational overhead

### Security
- ✅ **VPC isolation** for database
- ✅ **IAM roles** for fine-grained permissions
- ✅ **Secrets Manager** for credential rotation
- ✅ **WAF** for DDoS protection

### Scalability
- ✅ **Auto-scaling** based on demand
- ✅ **Global deployment** with CloudFront
- ✅ **Serverless** - no server management

## 📝 Next Steps

1. Review and customize the CloudFormation templates
2. Deploy infrastructure stack
3. Deploy application stack
4. Test the deployment
5. Update GitHub App webhook URL
6. Monitor and optimize

Would you like me to proceed with creating the specific AWS deployment files?
