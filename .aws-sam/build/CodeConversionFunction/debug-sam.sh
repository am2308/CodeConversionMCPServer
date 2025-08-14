#!/bin/bash

# 🔧 SAM Build Debug Script
# =========================
# Debug SAM build issues step by step

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}🔧 SAM Build Debug${NC}"
echo -e "${BLUE}=================${NC}"

# Step 1: Clean up
echo -e "${YELLOW}🧹 Cleaning up...${NC}"
rm -rf .aws-sam/

# Step 2: Check current directory structure
echo -e "${YELLOW}📁 Current directory structure:${NC}"
ls -la

# Step 3: Check if problematic directories exist
echo -e "${YELLOW}🔍 Checking for problematic directories...${NC}"
for dir in code venv .venv env .env __pycache__; do
    if [ -d "$dir" ]; then
        echo -e "${RED}⚠️ Found: $dir/${NC}"
        echo "Contents of $dir:"
        ls -la "$dir" | head -5
    else
        echo -e "${GREEN}✅ No $dir/ directory${NC}"
    fi
done

# Step 4: Validate template
echo -e "${YELLOW}📋 Validating template...${NC}"
if sam validate; then
    echo -e "${GREEN}✅ Template is valid${NC}"
else
    echo -e "${RED}❌ Template validation failed${NC}"
    exit 1
fi

# Step 5: Check required files for Lambda
echo -e "${YELLOW}📄 Checking Lambda files...${NC}"
required_files=("aws_lambda.py" "requirements-aws.txt" "src/main.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✅ $file exists${NC}"
    else
        echo -e "${RED}❌ $file missing${NC}"
    fi
done

# Step 6: Check .samignore
echo -e "${YELLOW}📋 Checking .samignore...${NC}"
if [ -f ".samignore" ]; then
    echo -e "${GREEN}✅ .samignore exists${NC}"
    echo "First 10 lines of .samignore:"
    head -10 .samignore
else
    echo -e "${RED}❌ .samignore missing${NC}"
fi

# Step 7: Try build without container first
echo -e "${YELLOW}🔨 Testing build without container...${NC}"
if sam build --region ap-south-1; then
    echo -e "${GREEN}✅ Build without container succeeded${NC}"
    
    # Step 8: Try build with container
    echo -e "${YELLOW}🐳 Testing build with container...${NC}"
    if sam build --use-container --region ap-south-1; then
        echo -e "${GREEN}✅ Build with container succeeded${NC}"
    else
        echo -e "${RED}❌ Build with container failed${NC}"
        echo -e "${YELLOW}💡 This is the issue we need to fix${NC}"
    fi
else
    echo -e "${RED}❌ Build without container failed${NC}"
    echo -e "${YELLOW}💡 There's a fundamental issue with the template or files${NC}"
fi

echo -e "${BLUE}🎯 Debug completed${NC}"
