#!/bin/bash

# 🔍 Template Validation Script
# =============================
# Validates AWS CloudFormation template before deployment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}🔍 Validating CloudFormation Template${NC}"
echo -e "${BLUE}====================================${NC}"

# Check if template exists
if [ ! -f "template.yaml" ]; then
    echo -e "${RED}❌ template.yaml not found${NC}"
    exit 1
fi

# Validate template syntax
echo -e "${YELLOW}📋 Validating template syntax...${NC}"
if aws cloudformation validate-template --template-body file://template.yaml --region ap-south-1 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Template syntax is valid${NC}"
else
    echo -e "${RED}❌ Template syntax validation failed${NC}"
    echo -e "${YELLOW}💡 Running detailed validation...${NC}"
    aws cloudformation validate-template --template-body file://template.yaml --region ap-south-1
    exit 1
fi

# Check SAM build
echo -e "${YELLOW}🔨 Testing SAM build...${NC}"
if sam build --use-container --region ap-south-1 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ SAM build successful${NC}"
else
    echo -e "${RED}❌ SAM build failed${NC}"
    echo -e "${YELLOW}💡 Running detailed build...${NC}"
    sam build --use-container --region ap-south-1
    exit 1
fi

# Check for required files
echo -e "${YELLOW}📁 Checking required files...${NC}"

files_to_check=(
    "aws_lambda.py"
    "requirements-aws.txt"
    "src/main.py"
    "src/config.py"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file found${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
    fi
done

# Check optional files
echo -e "${YELLOW}📄 Checking optional files...${NC}"

if [ -f "github-app-private-key.pem" ]; then
    echo -e "${GREEN}✅ GitHub App private key found${NC}"
else
    echo -e "${YELLOW}⚠️ GitHub App private key not found (you can add it later)${NC}"
fi

if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Environment file found${NC}"
else
    echo -e "${YELLOW}⚠️ .env file not found (you can add it later)${NC}"
fi

# Summary
echo -e "${GREEN}🎉 Template validation completed!${NC}"
echo -e "${BLUE}💡 You can now run: ./deploy-aws.sh deploy${NC}"
