# MCP Multi-Language to Python Converter

A comprehensive MCP (Model Context Protocol) server that automatically discovers code files in multiple programming languages within GitHub repositories, converts them to Python code using LLM models, and creates pull requests with the converted code.

## Features

- **Secure GitHub Integration**: Uses GitHub Personal Access Tokens for secure repository access
- **Multi-Language Code Discovery**: Automatically finds code files in 20+ programming languages
- **LLM-Powered Conversion**: Uses OpenAI GPT models for high-quality code conversion to Python
- **Automated Pull Requests**: Creates detailed pull requests with converted code
- **Kubernetes Ready**: Complete Kubernetes deployment configuration with security best practices
- **Production Ready**: Includes health checks, logging, monitoring, and error handling

## Supported Languages

The converter supports the following programming languages:

- **Shell Scripts**: `.sh`, `.bash`, `.zsh`, `.fish`
- **PowerShell**: `.ps1`, `.psm1`, `.psd1`
- **Web Languages**: `.js`, `.jsx`, `.ts`, `.tsx`
- **System Languages**: `.go`, `.rs`, `.c`, `.cpp`, `.cc`, `.cxx`
- **JVM Languages**: `.java`, `.scala`, `.kt`, `.groovy`
- **Other Languages**: `.rb`, `.php`, `.cs`, `.swift`, `.pl`, `.r`, `.R`, `.lua`, `.dart`

All these languages can be converted to Python while maintaining their original functionality and adapting language-specific patterns to Pythonic equivalents.

## Quick Start

### Prerequisites

- Docker
- Kubernetes cluster
- GitHub Personal Access Token with repository access
- OpenAI API key

### Local Development

1. **Clone and setup**:
```bash
git clone <repository-url>
cd mcp-multi-language-converter
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Setup environment**:
```bash
cp .env.example .env
# Edit .env with your tokens
```

4. **Run locally**:
```bash
python -m uvicorn src.main:app --reload
```

### Kubernetes Deployment

1. **Build Docker image**:
```bash
chmod +x scripts/build.sh
./scripts/build.sh
```

2. **Setup secrets**:
```bash
chmod +x scripts/setup-secrets.sh
./scripts/setup-secrets.sh
```

3. **Deploy to Kubernetes**:
```bash
chmod +x scripts/deploy.sh
./scripts/deploy.sh
```

## Usage

### API Endpoints

- `GET /`: Service information
- `GET /supported-languages`: List of supported programming languages
- `GET /health`: Health check
- `POST /convert`: Start conversion process
- `GET /status/{task_id}`: Check conversion status

### Convert Repository

**Convert all supported languages:**
```bash
curl -X POST "http://your-service/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "username",
    "repo_name": "repository-name",
    "branch": "main"
  }'
```

**Convert specific languages:**
```bash
curl -X POST "http://your-service/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_owner": "username",
    "repo_name": "repository-name",
    "branch": "main",
    "source_languages": ["shell", "javascript", "go"],
    "target_language": "python"
  }'
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | Required |
| `OPENAI_API_KEY` | OpenAI API Key | Required |
| `LLM_MODEL` | LLM Model to use | `gpt-4` |
| `PORT` | Server port | `8000` |
| `DEBUG` | Debug mode | `false` |
| `MAX_FILE_SIZE` | Max file size in bytes | `10000` |
| `MAX_FILES_PER_REPO` | Max files per repository | `50` |

### GitHub Token Permissions

Your GitHub Personal Access Token needs the following permissions:
- `repo` (Full control of private repositories)
- `workflow` (Update GitHub Action workflows)

## Language-Specific Conversion Features

### Shell Scripts
- Converts shell commands to `subprocess.run()` calls
- Maintains file operations using `pathlib`
- Preserves environment variable handling
- Converts pipes and redirections appropriately

### PowerShell
- Adapts PowerShell cmdlets to Python equivalents
- Converts object pipelines to Python data processing
- Maintains Windows-specific functionality where possible

### Web Languages (JS/TS)
- Converts async/await patterns to Python asyncio
- Adapts DOM manipulation to appropriate Python libraries
- Maintains API call patterns using `requests` or `httpx`

### System Languages (Go/Rust/C++)
- Converts concurrent patterns to Python threading/asyncio
- Adapts memory management concepts
- Maintains performance-critical sections with appropriate libraries

### Data Languages (R)
- Converts to pandas/numpy for data manipulation
- Maintains statistical analysis patterns
- Adapts visualization to matplotlib/seaborn

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │    │   GitHub         │    │   OpenAI        │
│   Web Server    │◄──►│   Service        │    │   LLM Service   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Conversion    │    │   Repository     │    │   Multi-Language│
│   Service       │◄──►│   Operations     │    │   Conversion    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Security Features

- **Non-root container execution**
- **Resource limits and requests**
- **Network policies for pod isolation**
- **RBAC with minimal permissions**
- **Secret management through Kubernetes secrets**
- **TLS termination at ingress**

## Monitoring and Logging

- **Structured JSON logging** with contextual information
- **Health check endpoints** for Kubernetes probes
- **Horizontal Pod Autoscaling** based on CPU/memory usage
- **Resource monitoring** and alerting ready

## Development

### Project Structure

```
src/
├── main.py                 # FastAPI application
├── config.py              # Configuration settings
├── models/
│   └── schemas.py         # Pydantic models
├── services/
│   ├── github_service.py  # GitHub API operations
│   ├── llm_service.py     # LLM interactions
│   └── conversion_service.py # Main conversion logic
└── utils/
    └── logging.py         # Logging configuration

k8s/                       # Kubernetes manifests
├── namespace.yaml
├── secrets.yaml
├── configmap.yaml
├── deployment.yaml
├── service.yaml
├── ingress.yaml
├── rbac.yaml
├── hpa.yaml
└── networkpolicy.yaml

scripts/                   # Deployment scripts
├── build.sh
├── deploy.sh
└── setup-secrets.sh
```

### Adding New Languages

To add support for a new programming language:

1. **Update `src/config.py`**:
   - Add file extensions to `supported_extensions`
   - Map extensions to language names

2. **Update `src/services/llm_service.py`**:
   - Add language-specific conversion instructions
   - Include appropriate Python library mappings

3. **Test the conversion**:
   - Create test files in the new language
   - Verify conversion quality and functionality

### Adding New Features

1. **Create feature branch**
2. **Add tests** in appropriate test files
3. **Update documentation**
4. **Submit pull request**

## Troubleshooting

### Common Issues

1. **GitHub API Rate Limiting**:
   - Use GitHub Apps for higher rate limits
   - Implement exponential backoff

2. **LLM API Failures**:
   - Check API key validity
   - Monitor usage quotas

3. **Kubernetes Deployment Issues**:
   - Check pod logs: `kubectl logs -f deployment/mcp-converter -n mcp-converter`
   - Verify secrets: `kubectl get secrets -n mcp-converter`

4. **Language-Specific Conversion Issues**:
   - Check if the source language is in the supported list
   - Verify file extensions are correctly mapped
   - Review conversion logs for specific error messages

### Support

For issues and questions:
1. Check the logs for detailed error messages
2. Verify your GitHub token permissions
3. Ensure OpenAI API key is valid and has sufficient credits
4. Check the `/supported-languages` endpoint for current language support

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

We welcome contributions that improve security, performance, add new programming languages, or enhance conversion quality!