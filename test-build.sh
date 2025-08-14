#!/bin/bash

# Quick SAM build test script
# This script tests the SAM build process without deploying

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}🧪 Testing SAM Build Process${NC}"
echo -e "${YELLOW}==============================${NC}"

# Clean everything
echo -e "${YELLOW}🧹 Cleaning all build artifacts...${NC}"
rm -rf .aws-sam/ code/ code-* venv/ .venv/

# Update .samignore
echo -e "${YELLOW}📝 Creating comprehensive .samignore...${NC}"
cat > .samignore << 'EOF'
# Virtual environments and backup directories
code/
code-*
*code*
venv/
.venv/
env/
.env/

# Python cache
__pycache__/
*.pyc
*.pyo

# IDE and OS files
.vscode/
.idea/
.DS_Store

# Sensitive files
*.pem
*.key
.env

# Build artifacts
build/
dist/
*.egg-info/

# Documentation and scripts
*.md
deploy*.sh
git-push.sh
cost-estimate.sh
setup.sh
validate-template.sh
init-postgres.sh
migrate_db.py
docker-compose.yml
Dockerfile
samconfig.toml.backup
EOF

# Validate template
echo -e "${YELLOW}🔍 Validating SAM template...${NC}"
if ! sam validate --region ap-south-1; then
    echo -e "${RED}❌ Template validation failed${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Template validation passed${NC}"

# Test build
echo -e "${YELLOW}🔨 Testing SAM build...${NC}"
if ! sam build --use-container --region ap-south-1; then
    echo -e "${RED}❌ SAM build failed${NC}"
    exit 1
fi

# Check build results
echo -e "${YELLOW}📦 Checking build results...${NC}"
if [ -d ".aws-sam/build/CodeConversionFunction" ]; then
    echo -e "${GREEN}✅ Build successful - Lambda function created${NC}"
    echo -e "${YELLOW}📊 Build contents:${NC}"
    ls -la .aws-sam/build/CodeConversionFunction/ | head -10
    
    # Check if our source code is included
    if [ -f ".aws-sam/build/CodeConversionFunction/aws_lambda.py" ]; then
        echo -e "${GREEN}✅ Lambda handler found${NC}"
    else
        echo -e "${RED}❌ Lambda handler missing${NC}"
        exit 1
    fi
    
    if [ -d ".aws-sam/build/CodeConversionFunction/src" ]; then
        echo -e "${GREEN}✅ Source code included${NC}"
    else
        echo -e "${RED}❌ Source code missing${NC}"
        exit 1
    fi
    
else
    echo -e "${RED}❌ Build directory not found${NC}"
    exit 1
fi

echo -e "${GREEN}🎉 Build test completed successfully!${NC}"
echo -e "${YELLOW}💡 You can now run: ./deploy-aws.sh deploy${NC}"
