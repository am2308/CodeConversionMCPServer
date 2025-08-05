# Multi-Tenant Code Conversion MCP Server API

## Overview

This is a multi-tenant service that allows users to convert code from various programming languages to Python using their own GitHub repositories and credentials.

## Getting Started

### 1. User Registration

First, register as a user with your GitHub credentials:

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "github_username": "your-github-username",
    "github_token": "ghp_your_github_personal_access_token"
  }'
```

**Response:**
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "api_key": "ccmcp_xxxxxxxxxxxxx",
  "message": "User registered successfully"
}
```

**Important:** Save your `api_key` - you'll need it for all subsequent requests.

### 2. Convert Repository

Start a conversion job:

```bash
curl -X POST "http://localhost:8000/convert" \
  -H "Authorization: Bearer ccmcp_xxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "your-github-username",
    "repo_name": "your-repository",
    "branch": "main",
    "target_branch": "convert-to-python",
    "source_languages": ["shell", "typescript"],
    "target_language": "python"
  }'
```

**Response:**
```json
{
  "task_id": "456e7890-e89b-12d3-a456-426614174001",
  "status": "pending",
  "message": "Conversion job started. Use /jobs/{job_id} to check status."
}
```

### 3. Check Job Status

Monitor your conversion job:

```bash
curl -X GET "http://localhost:8000/jobs/456e7890-e89b-12d3-a456-426614174001" \
  -H "Authorization: Bearer ccmcp_xxxxxxxxxxxxx"
```

**Response:**
```json
{
  "job_id": "456e7890-e89b-12d3-a456-426614174001",
  "status": "completed",
  "repo_owner": "your-github-username",
  "repo_name": "your-repository",
  "source_branch": "main",
  "target_branch": "convert-to-python",
  "files_processed": 5,
  "files_converted": 5,
  "pr_url": "https://github.com/your-username/your-repo/pull/1",
  "error_message": null,
  "created_at": "2025-01-01T10:00:00Z",
  "started_at": "2025-01-01T10:01:00Z",
  "completed_at": "2025-01-01T10:05:00Z"
}
```

### 4. List Your Jobs

Get all your conversion jobs:

```bash
curl -X GET "http://localhost:8000/jobs?limit=10&offset=0" \
  -H "Authorization: Bearer ccmcp_xxxxxxxxxxxxx"
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register a new user

### Conversion
- `POST /convert` - Start a conversion job
- `GET /jobs/{job_id}` - Get job status
- `GET /jobs` - List user's jobs

### System
- `GET /health` - Health check
- `GET /supported-languages` - List supported languages
- `GET /` - API information

## Supported Languages

The service supports conversion from these languages to Python:
- Shell/Bash scripts
- PowerShell
- TypeScript/JavaScript
- Go
- Rust
- Java
- C/C++
- And many more...

## GitHub Personal Access Token

You need a GitHub Personal Access Token with these permissions:
- `repo` (full repository access)
- `workflow` (if converting GitHub Actions)

Create one at: https://github.com/settings/tokens

## Security Features

- Encrypted storage of GitHub tokens
- Per-user API keys
- Rate limiting (if configured)
- Input validation
- Secure credential handling

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad request (validation error)
- `401` - Unauthorized (invalid API key)
- `404` - Not found
- `500` - Internal server error

## Rate Limits

- Registration: 5 requests per hour per IP
- Conversion jobs: 10 concurrent jobs per user
- API calls: 1000 requests per hour per user

## Support

For issues or questions:
1. Check the logs in your Docker container
2. Verify your GitHub token permissions
3. Ensure your repository is accessible
4. Check the job status for error messages
