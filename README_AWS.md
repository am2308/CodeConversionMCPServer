# 🚀 CodeConversion Server - AWS Serverless Deployment

A cost-optimized, single-click deployment solution for your multi-tenant code conversion service on AWS.

## ✨ Features

- **🎯 Single-click deploy/destroy** - Deploy or destroy entire infrastructure with one command
- **💰 Cost-optimized** - Uses ap-south-1 region and minimal resources for lowest cost
- **🔒 Secure** - Secrets managed via AWS Secrets Manager
- **📈 Scalable** - Serverless architecture with Lambda and API Gateway
- **🗄️ Reliable** - RDS PostgreSQL with automated backups

## 💰 Cost Breakdown (Monthly Estimates for ap-south-1)

| Service | Configuration | Estimated Cost |
|---------|---------------|----------------|
| Lambda | 512MB, ~1M requests | $0.20 |
| API Gateway | ~1M requests | $1.00 |
| RDS PostgreSQL | db.t3.micro | $13.00 |
| Secrets Manager | 2 secrets | $0.80 |
| S3 | <1GB storage | $0.02 |
| **Total** | | **~$15/month** |

> 💡 **Cost Saving Tip**: Use `./deploy-aws.sh destroy` when not in use to save ~$13/month on RDS costs!

## 🚀 Quick Start

### Prerequisites

1. **AWS CLI** configured with credentials
2. **AWS SAM CLI** installed
3. **GitHub App** credentials (private key file)

### Install Dependencies

```bash
# Install AWS CLI (macOS)
brew install awscli

# Install SAM CLI
pip install aws-sam-cli

# Configure AWS credentials
aws configure
```

### Deploy in 3 Commands

```bash
# 1. Clone and enter directory
cd CodeConversionMCPServer

# 2. Make script executable
chmod +x deploy-aws.sh

# 3. Deploy everything
./deploy-aws.sh deploy
```

### Destroy When Not Needed

```bash
# Save costs by destroying all resources
./deploy-aws.sh destroy
```

## 📁 Required Files

Before deployment, ensure you have:

```
CodeConversionMCPServer/
├── deploy-aws.sh                    # ✅ Deployment script
├── template.yaml                    # ✅ Infrastructure definition
├── aws_lambda.py                    # ✅ Lambda handler
├── requirements-aws.txt             # ✅ Python dependencies
├── github-app-private-key.pem       # ❗ Your GitHub App private key
└── .env                            # ❗ Your environment variables
```

### Example .env file:

```bash
# GitHub App Configuration
GITHUB_APP_ID=1759505
GITHUB_APP_SLUG=codeconversion
GITHUB_CLIENT_ID=Iv23ligOQSHy1IBac2Yq
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# OpenAI Configuration
OPENAI_API_KEY=sk-your_openai_api_key

# Encryption Key (generate with: openssl rand -base64 32)
ENCRYPTION_KEY=your_encryption_key_base64
```

## 🎮 Usage Commands

| Command | Description |
|---------|-------------|
| `./deploy-aws.sh deploy` | Deploy entire infrastructure |
| `./deploy-aws.sh destroy` | Destroy all resources to save costs |
| `./deploy-aws.sh status` | Check current deployment status |
| `./deploy-aws.sh help` | Show help and configuration |

## 🔧 Architecture Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   API Gateway   │───▶│  Lambda Function │───▶│  RDS PostgreSQL │
│  (Public HTTPS) │    │   (FastAPI App)  │    │   (Private VPC) │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌──────────────────┐             │
         │              │  Secrets Manager │             │
         │              │ (GitHub/OpenAI)  │             │
         │              └──────────────────┘             │
         │                       │                       │
         ▼                       ▼                       │
┌─────────────────┐    ┌──────────────────┐             │
│   CloudWatch    │    │    S3 Bucket     │             │
│ (Logs/Metrics)  │    │ (Private Keys)   │             │
└─────────────────┘    └──────────────────┘             │
                                                         │
                        ┌──────────────────┐             │
                        │       VPC        │◀────────────┘
                        │ (Private Network)│
                        └──────────────────┘
```

## 🛠️ Configuration Options

Edit the script variables for customization:

```bash
# In deploy-aws.sh
STACK_NAME="codeconversion-server"     # Change stack name
AWS_REGION="ap-south-1"                # Change region
ENVIRONMENT="production"               # Change environment
```

## 📊 Monitoring & Logs

After deployment, monitor your application:

```bash
# View Lambda logs
aws logs tail /aws/lambda/codeconversion-server-api --follow --region ap-south-1

# Check API Gateway metrics
aws cloudwatch get-metric-statistics --namespace AWS/ApiGateway --region ap-south-1

# View RDS metrics
aws cloudwatch get-metric-statistics --namespace AWS/RDS --region ap-south-1
```

## 🔒 Security Features

- **VPC Isolation** - Database in private subnets
- **Secrets Manager** - No hardcoded credentials
- **Encryption** - All data encrypted at rest
- **IAM Roles** - Least privilege access
- **Security Groups** - Restrictive network rules

## 🆘 Troubleshooting

### Common Issues:

1. **Health check fails**
   ```bash
   # Check Lambda logs
   aws logs tail /aws/lambda/codeconversion-server-api --region ap-south-1
   ```

2. **Database connection issues**
   ```bash
   # Verify database is running
   ./deploy-aws.sh status
   ```

3. **GitHub App webhook issues**
   ```bash
   # Update webhook URL in GitHub App settings
   # URL format: https://xxx.execute-api.ap-south-1.amazonaws.com/prod/webhooks/github
   ```

### Support Commands:

```bash
# Check deployment status
./deploy-aws.sh status

# View stack details
aws cloudformation describe-stacks --stack-name codeconversion-server --region ap-south-1

# Test API health
curl https://your-api-url/health
```

## 🔄 CI/CD Integration

For automated deployments, use these commands in your CI/CD pipeline:

```bash
# Deploy
./deploy-aws.sh deploy

# Run tests
curl -f https://your-api-url/health

# Destroy (for staging environments)
./deploy-aws.sh destroy
```

## 💡 Cost Optimization Tips

1. **Use destroy when not needed** - Save ~$13/month on RDS
2. **Monitor usage** - Set up billing alerts
3. **Optimize Lambda memory** - Adjust based on performance needs
4. **Use Reserved Instances** - For production workloads with consistent usage

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test your changes with `./deploy-aws.sh deploy`
4. Clean up with `./deploy-aws.sh destroy`
5. Submit a pull request

---

**Need help?** Check the [troubleshooting section](#-troubleshooting) or run `./deploy-aws.sh help` for more information.
