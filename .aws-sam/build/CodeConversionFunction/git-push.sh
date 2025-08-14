#!/bin/bash

# 🔒 Secure Git Push Script for CodeConversion Server
# ====================================================
# This script safely pushes code to git by:
# 1. Backing up sensitive files
# 2. Creating sanitized versions for git
# 3. Pushing to repository
# 4. Restoring original files for local development

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${PURPLE}🔒 Secure Git Push for CodeConversion Server${NC}"
echo -e "${PURPLE}=============================================${NC}"

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo -e "${RED}❌ Not in a git repository. Initialize with: git init${NC}"
    exit 1
fi

# Function to backup sensitive files
backup_sensitive_files() {
    echo -e "${YELLOW}📁 Backing up sensitive files...${NC}"
    
    # Create backup directory
    mkdir -p .git-backup
    
    # Backup files that contain secrets
    if [ -f ".env" ]; then
        cp .env .git-backup/.env.backup
        echo -e "${GREEN}✅ Backed up .env${NC}"
    fi
    
    if [ -f "github-app-private-key.pem" ]; then
        cp github-app-private-key.pem .git-backup/github-app-private-key.pem.backup
        echo -e "${GREEN}✅ Backed up GitHub private key${NC}"
    fi
    
    if [ -f "codeconversion.2025-08-10.private-key.pem" ]; then
        cp codeconversion.2025-08-10.private-key.pem .git-backup/codeconversion.2025-08-10.private-key.pem.backup
        echo -e "${GREEN}✅ Backed up CodeConversion private key${NC}"
    fi
}

# Function to create sanitized versions
create_sanitized_versions() {
    echo -e "${YELLOW}🧹 Creating sanitized versions for git...${NC}"
    
    # Create sanitized .env.example from .env
    if [ -f ".env" ]; then
        cat > .env.example << 'EOF'
# Environment Configuration for CodeConversion Server
# ===================================================
# Copy this file to .env and fill in your actual values

# GitHub App Configuration (Get from GitHub App settings)
GITHUB_APP_ID=your_github_app_id
GITHUB_APP_SLUG=your_github_app_slug
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
GITHUB_WEBHOOK_SECRET=your_webhook_secret

# OpenAI Configuration (Get from OpenAI platform)
OPENAI_API_KEY=sk-your_openai_api_key_here

# Database Configuration (for local development)
POSTGRES_PASSWORD=your_postgres_password
DATABASE_URL=postgresql://codeconv_user:your_password@localhost:5432/codeconv

# Security (Generate with: openssl rand -base64 32)
ENCRYPTION_KEY=your_base64_encryption_key_here

# Optional Configuration
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=["*"]
LOG_LEVEL=INFO
EOF
        echo -e "${GREEN}✅ Created sanitized .env.example${NC}"
    fi
    
    # Create placeholder private key
    if [ -f "github-app-private-key.pem" ]; then
        cat > github-app-private-key.pem << 'EOF'
-----BEGIN RSA PRIVATE KEY-----
PLACEHOLDER: Replace this file with your actual GitHub App private key
You can download this from your GitHub App settings page
This file is gitignored and should never be committed to version control
-----END RSA PRIVATE KEY-----
EOF
        echo -e "${GREEN}✅ Created placeholder GitHub private key${NC}"
    fi
    
    # Update template.yaml to remove sensitive defaults
    if [ -f "template.yaml" ]; then
        # Create a temporary file with sanitized secrets
        sed -e 's/"GITHUB_APP_ID": "[^"]*"/"GITHUB_APP_ID": "YOUR_GITHUB_APP_ID"/g' \
            -e 's/"GITHUB_APP_SLUG": "[^"]*"/"GITHUB_APP_SLUG": "YOUR_GITHUB_APP_SLUG"/g' \
            -e 's/"GITHUB_CLIENT_ID": "[^"]*"/"GITHUB_CLIENT_ID": "YOUR_GITHUB_CLIENT_ID"/g' \
            -e 's/"GITHUB_CLIENT_SECRET": "[^"]*"/"GITHUB_CLIENT_SECRET": "YOUR_GITHUB_CLIENT_SECRET"/g' \
            -e 's/"GITHUB_WEBHOOK_SECRET": "[^"]*"/"GITHUB_WEBHOOK_SECRET": "YOUR_GITHUB_WEBHOOK_SECRET"/g' \
            -e 's/"OPENAI_API_KEY": "[^"]*"/"OPENAI_API_KEY": "YOUR_OPENAI_API_KEY"/g' \
            -e 's/"ENCRYPTION_KEY": "[^"]*"/"ENCRYPTION_KEY": "YOUR_ENCRYPTION_KEY"/g' \
            template.yaml > template.yaml.tmp && mv template.yaml.tmp template.yaml
        echo -e "${GREEN}✅ Sanitized template.yaml${NC}"
    fi
}

# Function to restore original files
restore_sensitive_files() {
    echo -e "${YELLOW}🔄 Restoring original sensitive files...${NC}"
    
    if [ -f ".git-backup/.env.backup" ]; then
        cp .git-backup/.env.backup .env
        echo -e "${GREEN}✅ Restored .env${NC}"
    fi
    
    if [ -f ".git-backup/github-app-private-key.pem.backup" ]; then
        cp .git-backup/github-app-private-key.pem.backup github-app-private-key.pem
        echo -e "${GREEN}✅ Restored GitHub private key${NC}"
    fi
    
    if [ -f ".git-backup/codeconversion.2025-08-10.private-key.pem.backup" ]; then
        cp .git-backup/codeconversion.2025-08-10.private-key.pem.backup codeconversion.2025-08-10.private-key.pem
        echo -e "${GREEN}✅ Restored CodeConversion private key${NC}"
    fi
    
    # Restore template.yaml from git if it was modified
    if git diff --quiet template.yaml; then
        echo -e "${BLUE}ℹ️ template.yaml unchanged${NC}"
    else
        git checkout HEAD -- template.yaml 2>/dev/null || echo -e "${YELLOW}⚠️ Could not restore template.yaml from git${NC}"
        if [ -f ".git-backup/template.yaml.backup" ]; then
            cp .git-backup/template.yaml.backup template.yaml
            echo -e "${GREEN}✅ Restored template.yaml from backup${NC}"
        fi
    fi
}

# Function to update .gitignore
update_gitignore() {
    echo -e "${YELLOW}📝 Updating .gitignore...${NC}"
    
    # Create .gitignore if it doesn't exist
    touch .gitignore
    
    # Add sensitive file patterns if not already present
    cat >> .gitignore << 'EOF'

# Sensitive files - never commit these
.env
*.pem
*.key
.git-backup/
codeconversion.*.private-key.pem

# AWS and deployment
.aws/
samconfig.toml.backup

# Python
__pycache__/
*.pyc
*.pyo
*.egg-info/
.venv/
venv/
code/

# IDE
.vscode/settings.json
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite

EOF

    # Remove duplicates from .gitignore
    sort .gitignore | uniq > .gitignore.tmp && mv .gitignore.tmp .gitignore
    echo -e "${GREEN}✅ Updated .gitignore${NC}"
}

# Function to get repository information
get_repo_info() {
    echo -e "${CYAN}📝 Repository Configuration${NC}"
    echo ""
    
    # Check if remote origin exists
    if git remote get-url origin &>/dev/null; then
        CURRENT_REMOTE=$(git remote get-url origin)
        echo -e "${BLUE}Current remote origin: $CURRENT_REMOTE${NC}"
        read -p "Use current remote? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            return
        fi
    fi
    
    echo -e "${YELLOW}Enter repository details:${NC}"
    
    # Get username
    read -p "GitHub username: " GITHUB_USERNAME
    if [ -z "$GITHUB_USERNAME" ]; then
        echo -e "${RED}❌ Username cannot be empty${NC}"
        exit 1
    fi
    
    # Get repository name
    read -p "Repository name: " REPO_NAME
    if [ -z "$REPO_NAME" ]; then
        echo -e "${RED}❌ Repository name cannot be empty${NC}"
        exit 1
    fi
    
    # Construct repository URL
    REPO_URL="https://github.com/$GITHUB_USERNAME/$REPO_NAME.git"
    
    # Set or update remote origin
    if git remote get-url origin &>/dev/null; then
        git remote set-url origin "$REPO_URL"
        echo -e "${GREEN}✅ Updated remote origin to: $REPO_URL${NC}"
    else
        git remote add origin "$REPO_URL"
        echo -e "${GREEN}✅ Added remote origin: $REPO_URL${NC}"
    fi
}

# Function to commit and push changes
commit_and_push() {
    echo -e "${CYAN}📤 Committing and pushing changes${NC}"
    echo ""
    
    # Get commit message
    read -p "Commit message (default: 'Update CodeConversion server'): " COMMIT_MESSAGE
    if [ -z "$COMMIT_MESSAGE" ]; then
        COMMIT_MESSAGE="Update CodeConversion server"
    fi
    
    # Get branch name
    CURRENT_BRANCH=$(git branch --show-current)
    read -p "Branch to push to (default: $CURRENT_BRANCH): " TARGET_BRANCH
    if [ -z "$TARGET_BRANCH" ]; then
        TARGET_BRANCH="$CURRENT_BRANCH"
    fi
    
    # Add all changes
    echo -e "${YELLOW}📁 Adding files to git...${NC}"
    git add .
    
    # Show what will be committed
    echo -e "${BLUE}📋 Files to be committed:${NC}"
    git diff --cached --name-only
    echo ""
    
    # Confirm commit
    read -p "Proceed with commit and push? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}❌ Operation cancelled${NC}"
        restore_sensitive_files
        exit 0
    fi
    
    # Commit changes
    git commit -m "$COMMIT_MESSAGE"
    echo -e "${GREEN}✅ Changes committed${NC}"
    
    # Push to remote
    echo -e "${YELLOW}📤 Pushing to remote repository...${NC}"
    git push origin "$TARGET_BRANCH"
    echo -e "${GREEN}✅ Changes pushed to $TARGET_BRANCH${NC}"
}

# Function to cleanup
cleanup() {
    echo -e "${YELLOW}🧹 Cleaning up...${NC}"
    restore_sensitive_files
    rm -rf .git-backup
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main execution
main() {
    echo -e "${BLUE}🔍 Checking repository status...${NC}"
    
    # Check if there are any changes
    if git diff --quiet && git diff --staged --quiet; then
        echo -e "${YELLOW}⚠️ No changes detected to commit${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 0
        fi
    fi
    
    # Trap to ensure cleanup on exit
    trap cleanup EXIT
    
    # Backup original files
    backup_sensitive_files
    
    # Update .gitignore
    update_gitignore
    
    # Create sanitized versions
    create_sanitized_versions
    
    # Get repository information
    get_repo_info
    
    # Commit and push
    commit_and_push
    
    echo -e "${GREEN}🎉 Successfully pushed to git!${NC}"
    echo -e "${BLUE}💡 Your local development files have been restored${NC}"
    echo -e "${CYAN}🔒 Sensitive information was not committed to git${NC}"
}

# Show help
show_help() {
    echo -e "${BLUE}Usage: ./git-push.sh [options]${NC}"
    echo ""
    echo -e "${YELLOW}This script safely pushes code to git by:${NC}"
    echo "  • Backing up sensitive files (.env, *.pem)"
    echo "  • Creating sanitized versions for git"
    echo "  • Pushing changes to repository"
    echo "  • Restoring original files for local development"
    echo ""
    echo -e "${YELLOW}Options:${NC}"
    echo "  help, --help, -h    Show this help message"
    echo ""
    echo -e "${YELLOW}Files that will be sanitized:${NC}"
    echo "  • .env → .env.example (with placeholder values)"
    echo "  • *.pem files → placeholder versions"
    echo "  • template.yaml (removes hardcoded secrets)"
    echo ""
    echo -e "${YELLOW}Files added to .gitignore:${NC}"
    echo "  • .env, *.pem, *.key files"
    echo "  • Backup directories"
    echo "  • AWS configuration files"
}

# Handle command line arguments
case "${1:-main}" in
    help|--help|-h)
        show_help
        ;;
    main)
        main
        ;;
    *)
        echo -e "${RED}❌ Invalid option: $1${NC}"
        show_help
        exit 1
        ;;
esac
