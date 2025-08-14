#!/bin/bash

# 💰 AWS Cost Estimation for CodeConversion Server
# =================================================
# This script provides cost estimates for your deployment

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}💰 CodeConversion Server - Cost Estimation${NC}"
echo -e "${BLUE}===========================================${NC}"
echo ""

# Monthly estimates for ap-south-1 region
echo -e "${CYAN}📊 Monthly Cost Estimates (ap-south-1 region):${NC}"
echo ""

echo -e "${YELLOW}🔧 Core Infrastructure:${NC}"
echo "  • Lambda (512MB, 1M requests)     : $0.20"
echo "  • API Gateway (1M requests)       : $1.00"
echo "  • RDS PostgreSQL (db.t3.micro)    : $13.00"
echo "  • CloudWatch Logs (1GB)           : $0.50"
echo ""

echo -e "${YELLOW}🔒 Security & Storage:${NC}"
echo "  • Secrets Manager (2 secrets)     : $0.80"
echo "  • S3 Bucket (1GB storage)         : $0.02"
echo "  • VPC (NAT Gateway)                : $3.25"
echo ""

echo -e "${YELLOW}📡 Networking:${NC}"
echo "  • Data Transfer (minimal)          : $0.50"
echo "  • Route 53 (if using custom domain): $0.50"
echo ""

echo -e "${GREEN}💸 Total Monthly Cost: ~$19.77${NC}"
echo ""

echo -e "${CYAN}🎯 Cost Optimization Strategies:${NC}"
echo ""

echo -e "${YELLOW}1. 🛑 Use Destroy Command When Not Active:${NC}"
echo "   • Run: ./deploy-aws.sh destroy"
echo "   • Saves: ~$17/month (keeps only S3 costs)"
echo "   • Perfect for: Development, testing, demo periods"
echo ""

echo -e "${YELLOW}2. 🕐 Schedule On/Off (Advanced):${NC}"
echo "   • Deploy: 9 AM on weekdays"
echo "   • Destroy: 6 PM on weekdays"
echo "   • Saves: ~60% costs (~$8/month)"
echo ""

echo -e "${YELLOW}3. 🔧 Right-sizing:${NC}"
echo "   • Monitor Lambda memory usage"
echo "   • Adjust RDS instance based on load"
echo "   • Use CloudWatch to optimize"
echo ""

echo -e "${YELLOW}4. 🌍 Regional Costs Comparison:${NC}"
echo "   • ap-south-1 (Mumbai):    ~$19.77/month (cheapest)"
echo "   • us-east-1 (Virginia):   ~$22.15/month"
echo "   • eu-west-1 (Ireland):    ~$24.30/month"
echo ""

echo -e "${CYAN}📈 Usage-Based Scaling:${NC}"
echo ""

echo -e "${YELLOW}Light Usage (< 100K requests/month):${NC}"
echo "  • Lambda: $0.02"
echo "  • API Gateway: $0.10"
echo "  • Total: ~$17/month"
echo ""

echo -e "${YELLOW}Heavy Usage (> 10M requests/month):${NC}"
echo "  • Lambda: $2.00"
echo "  • API Gateway: $10.00"
echo "  • Consider upgrading RDS: +$20"
echo "  • Total: ~$49/month"
echo ""

echo -e "${GREEN}💡 Recommendations:${NC}"
echo ""
echo "✅ Start with current configuration"
echo "✅ Use destroy command when not actively developing"
echo "✅ Monitor costs with AWS Cost Explorer"
echo "✅ Set up billing alerts at $25/month"
echo "✅ Consider Reserved Instances after 3 months of consistent usage"
echo ""

echo -e "${BLUE}🎮 Quick Commands:${NC}"
echo "  Deploy:  ./deploy-aws.sh deploy"
echo "  Destroy: ./deploy-aws.sh destroy"
echo "  Status:  ./deploy-aws.sh status"
echo ""

echo -e "${CYAN}📊 To monitor actual costs:${NC}"
echo "  aws ce get-cost-and-usage --time-period Start=2025-01-01,End=2025-01-31 --granularity MONTHLY --metrics BlendedCost"
