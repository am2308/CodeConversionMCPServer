# Production Deployment Guide

## GitHub App Architecture Overview

### How It Works in Production

The GitHub App model is designed for **multi-tenant SaaS applications** where:

1. **Service Owner (You)** creates ONE GitHub App with credentials
2. **End Users** install YOUR app on their repositories  
3. **No User Credentials Required** - users just install and use

### Architecture Flow

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Service Owner │    │   GitHub App    │    │   End Users     │
│   (You/Admin)   │    │   (Your App)    │    │   (Customers)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. Create App         │                       │
         │ & Configure           │                       │
         │ Credentials           │                       │
         ├──────────────────────►│                       │
         │                       │                       │
         │                       │ 2. Install App        │
         │                       │ (One-click)           │
         │                       │◄──────────────────────┤
         │                       │                       │
         │                       │ 3. Use Service        │
         │                       │ (API calls)           │
         │                       │◄──────────────────────┤
```

## Production Deployment Steps

### 1. Service Owner Setup (One-time)

#### A. Create GitHub App
1. Go to GitHub Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Configure:
   - **App name**: "YourService Code Converter"
   - **Homepage URL**: `https://your-domain.com`
   - **Webhook URL**: `https://your-domain.com/webhooks/github`
   - **Permissions**:
     - Repository permissions:
       - Contents: Read & Write
       - Pull requests: Write
       - Metadata: Read
   - **Events**: Installation, Installation repositories

#### B. Configure Environment Variables
```bash
# Set these in your production environment (Railway, Render, etc.)
GITHUB_APP_ID=123456
GITHUB_CLIENT_ID=Iv1.a1b2c3d4e5f6g7h8
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_WEBHOOK_SECRET=your_webhook_secret
GITHUB_APP_PRIVATE_KEY_PATH=/app/private-key.pem
```

#### C. Deploy Private Key Securely
```bash
# In your deployment platform, mount the private key as a file
# Railway: Add as a volume
# Render: Add as a secret file
# Docker: Mount as volume
```

### 2. User Experience (Self-Service)

#### A. User Registration
```bash
curl -X POST "https://your-domain.com/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "github_username": "username"
  }'
```

Response includes GitHub App installation URL:
```json
{
  "user_id": "uuid",
  "api_key": "user_api_key",
  "github_auth_url": "https://github.com/apps/your-app/installations/new",
  "message": "Install the GitHub App to enable repository access"
}
```

#### B. One-Click GitHub App Installation
User clicks the provided URL and installs your app on their repositories.

#### C. Immediate Usage
```bash
curl -X POST "https://your-domain.com/convert" \
  -H "Authorization: Bearer user_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "username",
    "repo_name": "my-repo",
    "target_language": "python"
  }'
```

## Deployment Platforms

### Railway (Recommended)
```bash
# Deploy to Railway
railway login
railway new
railway add
railway deploy

# Set environment variables in Railway dashboard
```

### Render
```yaml
# render.yaml
services:
  - type: web
    name: code-converter
    env: docker
    dockerfilePath: ./Dockerfile
    envVars:
      - key: GITHUB_APP_ID
        value: 123456
      - key: GITHUB_CLIENT_ID
        sync: false  # Set in dashboard
```

### Heroku
```bash
heroku create your-app-name
heroku config:set GITHUB_APP_ID=123456
heroku config:set GITHUB_CLIENT_ID=your_client_id
# ... set other vars
git push heroku main
```

## Security Best Practices

### 1. Environment Variables
- **NEVER** commit credentials to git
- Use platform-specific secret management
- Rotate webhook secrets regularly

### 2. Private Key Security
- Store as file, not environment variable
- Use platform secret file mounting
- Restrict file permissions (600)

### 3. Network Security
- Use HTTPS only
- Validate webhook signatures
- Rate limit API endpoints

## Local Development Setup

For development/testing only:

```bash
# 1. Create test GitHub App
# 2. Download private key to project root
# 3. Set environment variables in .env
cp .env.example .env
# Edit .env with your test app credentials

# 4. Use ngrok for webhook testing
ngrok http 8000
# Use ngrok URL in GitHub App webhook settings
```

## Common Issues & Solutions

### "No GitHub token configured"
- Ensure GitHub App credentials are set
- Verify user has installed the app
- Check webhook is receiving installation events

### "Installation token generation failed"
- Verify private key file exists and is readable
- Check GitHub App permissions
- Ensure app ID matches the app

### "Repository not accessible"
- User must install app on specific repository
- Check repository permissions in GitHub App
- Verify installation events are processed

## Monitoring & Logs

```bash
# Check service health
curl https://your-domain.com/health

# Monitor logs for GitHub App issues
# Look for: "GitHub App installation linked"
# Look for: "Generated installation access token"
```

This architecture ensures:
- ✅ Users never need to provide GitHub credentials
- ✅ Service owner controls GitHub App security
- ✅ Scalable for thousands of users
- ✅ Secure token management
- ✅ Simple user onboarding
