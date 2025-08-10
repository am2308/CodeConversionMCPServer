# GitHub App Setup Guide

## 🚨 IMPORTANT: Two Different Use Cases

### Use Case 1: You Want to Provide This as a SaaS Service
- **You** deploy the service once with your GitHub App credentials
- **End users** just register and install your app (no setup needed)
- Users never see `.env` files or credentials

### Use Case 2: Someone Else Wants to Run Their Own Instance  
- **They** need to create their own GitHub App
- **They** need to configure their own `.env` file
- **They** become the service provider for their users

---

## For Use Case 1 (SaaS Service Provider)

If you want to provide this as a service to other users:

### 1. Deploy Your Service (One Time Setup)

1. **Create GitHub App** (as you did)
2. **Deploy to Cloud Platform** (Railway, Render, etc.)
3. **Configure Environment Variables** in your deployment platform
4. **Share Your Service URL** with users

### 2. User Experience (No Setup Required)

Users just need to:
1. Go to your service URL (e.g., `https://yourservice.com`)
2. Register with email/GitHub username
3. Install your GitHub App when prompted
4. Start converting code immediately

**Users never touch `.env` files or credentials!**

---

## For Use Case 2 (Self-Hosted Instance)

If someone wants to run their own instance, here's the **complete step-by-step process**:

From **their** GitHub App settings:

1. **App ID**: Copy from their app settings page
2. **Client ID**: Copy from their app settings  
3. **Client Secret**: Generate new client secret
4. **Private Key**: Generate and download private key
5. **Webhook Secret**: Create a secure random string

### Step 4: Configure Environment Variables

Create `.env` file with **their** credentials:

```bash
# Copy example and edit
cp .env.example .env

# Edit .env with their values:
# GITHUB_APP_ID=their_app_id
# GITHUB_CLIENT_ID=their_client_id  
# GITHUB_CLIENT_SECRET=their_client_secret
# GITHUB_WEBHOOK_SECRET=their_webhook_secret
# OPENAI_API_KEY=their_openai_key
```

### Step 5: Setup Private Key

```bash
# Copy their downloaded private key to project root
cp ~/Downloads/their-app.private-key.pem ./github-app-private-key.pem
```

### Step 6: Deploy Their Instance

Choose deployment method:

#### Option A: Docker (Local/Server)
```bash
# Build and run
docker-compose up -d

# Check health
curl http://localhost:8000/health
```

#### Option B: Cloud Platform (Recommended)
```bash
# Deploy to Railway/Render/Heroku
# Set environment variables in platform dashboard
# Upload private key as secret file
```

### Step 7: Configure Webhook URL

Update their GitHub App webhook URL to point to their deployment:
- Local: Use ngrok: `https://abc123.ngrok.io/webhooks/github`  
- Production: `https://their-domain.com/webhooks/github`

### Step 8: Test Their Instance

```bash
# Register first user (themselves)
curl -X POST "https://their-domain.com/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@their-company.com",
    "github_username": "their-github-username"
  }'

# Install their app when prompted
# Test conversion
```

---

## Summary

**For SaaS (Recommended):**
- You setup once, users just use your service
- No technical setup required for end users
- You maintain one GitHub App for all users

**For Self-Hosted:**
- Each organization runs their own instance  
- They create their own GitHub App
- They configure their own environment
- More complex but gives them full control

## Which Should You Choose?

### Choose SaaS if:
- You want to provide a service to multiple users/companies
- Users don't want to deal with technical setup
- You want recurring revenue/business model

### Choose Self-Hosted if:
- Organizations want full control over their data
- Enterprise customers with strict security requirements  
- Open source community contributions

---

## Current Status

Based on your screenshots, you're set up for **SaaS model**. You just need to:

1. **Complete your GitHub App configuration** (add the missing credentials to .env)
2. **Deploy to a cloud platform** (Railway, Render, etc.)
3. **Share the service URL** with users

Then users can:
1. Visit your service URL
2. Register with email/GitHub username  
3. Install your app via the provided link
4. Start converting code immediately

**No `.env` files or technical setup required for your users!**

Create/update your `.env` file with these values:

```bash
# Database Configuration
DATABASE_URL=postgresql://codeconv_user:akhil123@postgres:5432/codeconv
POSTGRES_PASSWORD=akhil123

# OpenAI Configuration  
OPENAI_API_KEY="your_openai_key_here"

# GitHub App Configuration (REPLACE WITH YOUR VALUES)
GITHUB_APP_ID=YOUR_APP_ID_HERE
GITHUB_CLIENT_ID=YOUR_CLIENT_ID_HERE
GITHUB_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GITHUB_WEBHOOK_SECRET=any_random_secret_string_here
GITHUB_APP_PRIVATE_KEY_PATH=/app/github-app-private-key.pem

# Security
ENCRYPTION_KEY="UTFAlC02TcIlDKRDEf5A6sYiuQSbWSmUiD_Om2eSQyM="

# Server Configuration
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=["*"]
LOG_LEVEL=INFO
```

### 3. Copy Private Key to Project

```bash
# Copy your downloaded private key to the project root
cp ~/Downloads/codeconversion.*.private-key.pem ./github-app-private-key.pem
```

### 4. Update Docker Compose to Mount the Private Key

The private key needs to be accessible inside the Docker container.

### 5. Restart Containers

```bash
docker-compose down
docker-compose up -d
```

## Quick Test Commands

Once configured, test with:

```bash
# Register a user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "github_username": "am2308"
  }'

# Test conversion (use the API key from registration)
curl -X POST "http://localhost:8000/convert" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "am2308",
    "repo_name": "your-repo-name",
    "target_language": "python"
  }'
```

The error should be resolved once you have all these credentials properly configured!

---

## For Someone Else Wanting to Run Their Own Instance

Here's a step-by-step process for someone who wants to run their own instance of the CodeConversion service:

### Step 1: Clone and Setup Repository

```bash
# Clone the repository
git clone https://github.com/your-username/CodeConversionMCPServer.git
cd CodeConversionMCPServer

# Install dependencies (if running locally)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Create Their Own GitHub App

They need to create their own GitHub App (not use yours):

1. Go to GitHub Settings → Developer settings → GitHub Apps
2. Click "New GitHub App"
3. Fill in **their** details:
   - **App name**: "MyCompany Code Converter" (their choice)
   - **Homepage URL**: "https://their-domain.com" (their URL)
   - **Webhook URL**: "https://their-domain.com/webhooks/github" (their webhook)
   - **Permissions**: Same as your app
   - **Events**: Installation, Installation repositories

### Step 3: Get GitHub App Credentials

From **their** GitHub App settings:

1. **App ID**: Look for "App ID" at the top of your app settings page
2. **Client ID**: Look for "Client ID" in the app settings
3. **Client Secret**: 
   - If you don't have one, click "Generate a new client secret"
   - Copy the generated secret (you won't be able to see it again)
4. **Private Key**:
   - Scroll to "Private keys" section
   - Click "Generate a private key"
   - Download the `.pem` file

### Step 4: Update Your .env File

Create/update your `.env` file with these values:

```bash
# Database Configuration
DATABASE_URL=postgresql://codeconv_user:akhil123@postgres:5432/codeconv
POSTGRES_PASSWORD=akhil123

# OpenAI Configuration  
OPENAI_API_KEY="your_openai_key_here"

# GitHub App Configuration (REPLACE WITH YOUR VALUES)
GITHUB_APP_ID=YOUR_APP_ID_HERE
GITHUB_CLIENT_ID=YOUR_CLIENT_ID_HERE
GITHUB_CLIENT_SECRET=YOUR_CLIENT_SECRET_HERE
GITHUB_WEBHOOK_SECRET=any_random_secret_string_here
GITHUB_APP_PRIVATE_KEY_PATH=/app/github-app-private-key.pem

# Security
ENCRYPTION_KEY="UTFAlC02TcIlDKRDEf5A6sYiuQSbWSmUiD_Om2eSQyM="

# Server Configuration
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=["*"]
LOG_LEVEL=INFO
```

### Step 5: Copy Private Key to Project

```bash
# Copy your downloaded private key to the project root
cp ~/Downloads/codeconversion.*.private-key.pem ./github-app-private-key.pem
```

### Step 6: Update Docker Compose to Mount the Private Key

The private key needs to be accessible inside the Docker container.

### Step 7: Restart Containers

```bash
docker-compose down
docker-compose up -d
```

## Quick Test Commands

Once configured, test with:

```bash
# Register a user
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com", 
    "github_username": "am2308"
  }'

# Test conversion (use the API key from registration)
curl -X POST "http://localhost:8000/convert" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "am2308",
    "repo_name": "your-repo-name",
    "target_language": "python"
  }'
```

The error should be resolved once you have all these credentials properly configured!
