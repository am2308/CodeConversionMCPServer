# Code Conversion MCP Server

Multi-tenant SaaS service for converting code between programming languages using GitHub repositories and OpenAI LLM.

## 🚀 Two Deployment Options

### Option 1: SaaS Service (Recommended)
**You provide the service, users just use it**

- ✅ **For Users**: No technical setup required
- ✅ **For You**: Deploy once, serve many users  
- ✅ **Business**: Charge users for conversions
- ✅ **Maintenance**: You control updates and security

### Option 2: Self-Hosted Instance
**Each organization runs their own copy**

- ✅ Full control over data and infrastructure
- ✅ Enterprise security compliance
- ✅ Customizable for specific needs
- ❌ Requires technical setup for each deployment

---

## 🎯 Quick Start Guide

### For SaaS Service Providers (You):

1. **Setup GitHub App** (one time)
   ```bash
   # Follow the guide to get your GitHub App credentials
   # See: GITHUB_APP_SETUP.md
   ```

2. **Deploy to Production**
   ```bash
   # Deploy to Railway/Render/Heroku with your credentials
   # See: PRODUCTION_DEPLOYMENT.md
   ```

3. **Share Service URL**
   ```
   Your users will use: https://your-service.com
   ```

### For End Users (Your Customers):

**No technical setup required!**

1. **Register** at your service URL
   ```bash
   POST /auth/register
   {
     "email": "user@company.com",
     "github_username": "username"  
   }
   ```

2. **Install GitHub App** (one-click from registration response)

3. **Convert Code** immediately
   ```bash
   POST /convert
   Authorization: Bearer <api_key_from_registration>
   {
     "repo_owner": "username",
     "repo_name": "my-repo", 
     "target_language": "python"
   }
   ```

---

## 🛠️ Self-Hosted Installation

If someone wants to run their own instance:

### Step-by-Step Process:

1. **Clone Repository**
   ```bash
   git clone https://github.com/your-username/CodeConversionMCPServer.git
   cd CodeConversionMCPServer
   ```

2. **Create Their Own GitHub App**
   - They create a new GitHub App (not use yours)
   - Get their own App ID, Client ID, Client Secret, Private Key
   - Set their own webhook URL

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with THEIR credentials (not yours)
   ```

4. **Deploy Their Instance**
   ```bash
   docker-compose up -d
   # OR deploy to their preferred cloud platform
   ```

5. **Their Users Register**
   - Their users register on THEIR service URL
   - Install THEIR GitHub App
   - Use THEIR API

**See detailed guide: [GITHUB_APP_SETUP.md](./GITHUB_APP_SETUP.md#for-use-case-2-self-hosted-instance)**

---

## 📖 API Documentation

### Authentication
All requests require API key from registration:
```bash
Authorization: Bearer <api_key>
```

### Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | Register new user |
| `/convert` | POST | Start code conversion |
| `/jobs/{id}` | GET | Check conversion status |
| `/jobs` | GET | List user's jobs |
| `/health` | GET | Service health check |

### Example: Full Conversion Flow

```bash
# 1. Register user
curl -X POST "https://your-service.com/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "github_username": "username"}'

# Response includes api_key and github_auth_url
# User installs GitHub App via the provided URL

# 2. Convert repository  
curl -X POST "https://your-service.com/convert" \
  -H "Authorization: Bearer <api_key>" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "username",
    "repo_name": "my-repo",
    "target_language": "python",
    "branch": "main"
  }'

# 3. Check status
curl "https://your-service.com/jobs/<job_id>" \
  -H "Authorization: Bearer <api_key>"
```

---

## 🔧 Supported Languages

**Source Languages** (convert FROM):
- JavaScript/TypeScript (`.js`, `.jsx`, `.ts`, `.tsx`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`, `.hpp`)
- Shell Scripts (`.sh`, `.bash`, `.zsh`)
- PowerShell (`.ps1`)
- Go (`.go`)
- Rust (`.rs`)
- Ruby (`.rb`)
- PHP (`.php`)
- And more...

**Target Language**: Python (more targets coming soon)

---

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Service Owner │    │   GitHub App    │    │   End Users     │
│   (You/Admin)   │    │   (Your App)    │    │   (Customers)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │ 1. Create App         │                       │
         │ & Deploy Service      │                       │
         ├──────────────────────►│                       │
         │                       │                       │
         │                       │ 2. Register & Install │
         │                       │◄──────────────────────┤
         │                       │                       │
         │                       │ 3. Convert Code       │
         │                       │◄──────────────────────┤
```

**Key Benefits:**
- ✅ **Users**: Zero technical setup
- ✅ **Security**: No credential sharing
- ✅ **Scalability**: One app serves thousands of users
- ✅ **Maintenance**: Centralized updates and monitoring

---

## 🚀 Deployment Options

### Cloud Platforms (Recommended)

#### Railway
```bash
railway login
railway new
railway add
railway deploy
```

#### Render
```yaml
# render.yaml
services:
  - type: web
    name: code-converter
    env: docker
```

#### Heroku
```bash
heroku create your-app
heroku config:set GITHUB_APP_ID=123456
git push heroku main
```

### Self-Hosted
```bash
# Docker Compose
docker-compose up -d

# Kubernetes
kubectl apply -f k8s/
```

---

## 📝 Configuration

### Required Environment Variables

**For Service Providers:**
```bash
# GitHub App (your credentials)
GITHUB_APP_ID=your_app_id
GITHUB_CLIENT_ID=your_client_id  
GITHUB_CLIENT_SECRET=your_client_secret
GITHUB_APP_PRIVATE_KEY_PATH=/app/private-key.pem

# OpenAI
OPENAI_API_KEY=your_openai_key

# Database
DATABASE_URL=postgresql://user:pass@host/db
```

**For Self-Hosted Users:**
Same variables but with THEIR GitHub App credentials.

---

## 🔐 Security

- 🔒 **GitHub App Authentication**: Secure, token-based access
- 🔐 **Encrypted Token Storage**: User tokens encrypted at rest
- 🛡️ **API Key Authentication**: Secure user authentication
- 🔍 **Webhook Validation**: Signed webhook verification
- 🚫 **No Credential Sharing**: Users never share GitHub passwords

---

## 📞 Support

### For Service Providers
- [GitHub App Setup Guide](./GITHUB_APP_SETUP.md)
- [Production Deployment Guide](./PRODUCTION_DEPLOYMENT.md)
- [API Documentation](./API_GUIDE.md)

### For Self-Hosted Users
- [Self-Hosted Setup](./GITHUB_APP_SETUP.md#for-use-case-2-self-hosted-instance)
- [Configuration Guide](./.env.example)

### Issues & Contributions
- 🐛 [Report Issues](https://github.com/your-username/repo/issues)
- 🤝 [Contributing Guidelines](./CONTRIBUTING.md)
- 📚 [Documentation](./docs/)

---

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.
