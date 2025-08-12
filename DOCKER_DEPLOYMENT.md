# 🐳 Docker Deployment Guide for AI Recruitment Backend (Standalone)

This guide provides comprehensive instructions for containerizing and deploying your AI Recruitment Backend application as a standalone Docker container to Azure Container Apps.

## 📋 Prerequisites

- Docker Desktop installed and running
- Azure CLI installed and configured
- Python 3.11+ (for local development)
- Git (for version control)
- **External PostgreSQL database** (you handle setup manually)

## 🏗️ Project Structure

```
AiRecruitmentBackend/
├── Dockerfile                 # Standalone Docker build
├── start.sh                   # Container startup script
├── .dockerignore             # Docker build optimization
├── deploy-azure.sh           # Azure Container Apps deployment script
├── env.example               # Environment variables template
├── app.py                    # Main Flask application
├── requirements.txt           # Python dependencies
├── models.py                 # Database models
├── routes/                   # API route definitions
├── services/                 # Business logic services
└── database_schema.sql       # Database schema (for manual setup)
```

## 🚀 Quick Start

### 1. Local Docker Development

```bash
# Clone the repository
git clone <your-repo-url>
cd AiRecruitmentBackend

# Copy environment template
cp .env.prod_example .env

# Edit .env with your configuration
nano .env

# Build Docker image
docker build -t ai-recruitment-backend .

# Run container (connect to your external database)
docker run -d \
  --name ai-recruitment-backend \
  -p 5000:5000 \
  --env-file .env \
  ai-recruitment-backend
```

### 2. Azure Container Apps Deployment

```bash
# Make deployment script executable
chmod +x deploy-azure.sh

# Set environment variables
export DATABASE_URL="your-external-database-connection-string"
export OPENAI_API_KEY="your-openai-api-key"
export AZURE_OPENAI_API_KEY="your-azure-openai-key"
export AZURE_OPENAI_ENDPOINT="your-azure-openai-endpoint"

# Run deployment
./deploy-azure.sh
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_APP=app.py
HOST=0.0.0.0
PORT=5000
WORKERS=4

# Database Configuration (External - you handle this manually)
DATABASE_URL=postgresql://username:password@your-db-host:5432/ai_recruitment_db

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

### Database Setup (Manual)

Since you handle database setup manually:

1. **Create PostgreSQL database** with pgvector extension
2. **Run database_schema.sql** to create tables
3. **Load sample data** if needed
4. **Update DATABASE_URL** in your environment

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database
CREATE DATABASE ai_recruitment_db;

-- Run schema (you'll do this manually)
-- psql -d ai_recruitment_db -f database_schema.sql
```

## 🐳 Docker Features

### Standalone Build

The Dockerfile creates a self-contained application:

1. **Base Image**: Python 3.11 with system dependencies
2. **Dependencies**: Python packages and AI models
3. **AI Models**: Pre-loaded spaCy and NLTK data
4. **Application**: Your Flask app ready to run

### Pre-built AI Models

The container includes:
- **spaCy English NER model** (`en_core_web_sm`)
- **NLTK data** (punkt, stopwords, wordnet)
- **Custom entity patterns** for skill recognition

### Health Checks

Built-in health monitoring:
```bash
# Health endpoint
GET /api/health

# Container health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1
```

## 🌐 Azure Container Apps Deployment

### Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Azure DNS     │───▶│  Container App   │───▶│  Your External  │
│                 │    │                  │    │   PostgreSQL    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │  Application     │
                       │  Insights        │
                       └──────────────────┘
```

### Deployment Steps

1. **Resource Creation**
   - Resource Group
   - Container Registry
   - Container Apps Environment

2. **Image Build & Push**
   - Build Docker image locally
   - Push to Azure Container Registry
   - Deploy to Container Apps

3. **Configuration**
   - Environment variables
   - External database connection
   - Scaling rules

### Scaling Configuration

```bash
# Auto-scaling settings
--min-replicas 1
--max-replicas 5
--cpu 1.0
--memory 2.0Gi
```

## 📊 Monitoring & Logging

### Application Insights

- Performance monitoring
- Error tracking
- Request analytics
- Custom metrics

### Log Management

```bash
# View container logs
az containerapp logs show \
    --name ai-recruitment-backend \
    --resource-group ai-recruitment-rg

# Local logs
docker logs ai-recruitment-backend
```

### Health Monitoring

- **Endpoint**: `/api/health`
- **Interval**: 30 seconds
- **Timeout**: 30 seconds
- **Retries**: 3 attempts

## 🔒 Security Considerations

### Container Security

- Non-root user execution
- Minimal base image
- Security updates
- Vulnerability scanning

### Network Security

- External database connection
- SSL/TLS encryption
- API authentication
- Rate limiting

### Secrets Management

```bash
# Azure Key Vault integration
az containerapp update \
    --name ai-recruitment-backend \
    --resource-group ai-recruitment-rg \
    --set-env-vars \
        SECRET_KEY="@Microsoft.KeyVault(SecretUri=https://your-vault.vault.azure.net/secrets/secret-key/)"
```

## 🚀 Performance Optimization

### Container Optimization

- Single-stage build
- Layer caching
- Minimal dependencies
- Optimized base image

### Application Optimization

- Gunicorn workers
- Connection pooling
- Caching strategies
- Async processing

### Database Optimization

- External connection pooling
- Query optimization
- Indexing strategies
- Vector similarity search

## 🧪 Testing

### Local Testing

```bash
# Build and run container
docker build -t ai-recruitment-backend .
docker run -d --name test-app -p 5000:5000 --env-file .env ai-recruitment-backend

# Health check
curl http://localhost:5000/api/health

# Swagger UI
open http://localhost:5000/swagger/

# Check logs
docker logs test-app

# Cleanup
docker stop test-app && docker rm test-app
```

### Integration Testing

```bash
# Test database connection (ensure your DB is running)
docker run --rm --env-file .env ai-recruitment-backend python -c "
import os
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
print('Database connection successful')
conn.close()
"
```

## 🔄 CI/CD Integration

### GitHub Actions

```yaml
name: Deploy to Azure Container Apps

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build and push image
        run: |
          docker build -t ${{ secrets.REGISTRY_LOGIN_SERVER }}/ai-recruitment-backend:${{ github.sha }} .
          docker push ${{ secrets.REGISTRY_LOGIN_SERVER }}/ai-recruitment-backend:${{ github.sha }}
      - name: Deploy to Azure
        run: |
          az containerapp update \
            --name ai-recruitment-backend \
            --resource-group ai-recruitment-rg \
            --image ${{ secrets.REGISTRY_LOGIN_SERVER }}/ai-recruitment-backend:${{ github.sha }}
```

## 🆘 Troubleshooting

### Common Issues

1. **Container won't start**
   ```bash
   # Check logs
   docker logs ai-recruitment-backend
   
   # Check health endpoint
   curl http://localhost:5000/api/health
   ```

2. **Database connection failed**
   ```bash
   # Verify database URL
   echo $DATABASE_URL
   
   # Test connection
   docker run --rm --env-file .env ai-recruitment-backend python -c "
   import psycopg2
   conn = psycopg2.connect('$DATABASE_URL')
   print('Connection successful')
   "
   ```

3. **NER models not loading**
   ```bash
   # Check model files
   docker exec ai-recruitment-backend ls -la /app/models
   
   # Rebuild container
   docker build --no-cache -t ai-recruitment-backend .
   ```

### Debug Commands

```bash
# Enter container shell
docker exec -it ai-recruitment-backend bash

# Check Python packages
pip list | grep -E "(spacy|nltk|flask)"

# Verify model loading
python -c "import spacy; nlp = spacy.load('en_core_web_sm'); print('Model loaded')"
```

## 📚 Additional Resources

- [Azure Container Apps Documentation](https://docs.microsoft.com/en-us/azure/container-apps/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Flask Production Deployment](https://flask.palletsprojects.com/en/2.3.x/deploying/)
- [spaCy Model Training](https://spacy.io/usage/training)

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review container logs
3. Verify environment configuration
4. Check Azure Container Apps status
5. Ensure your external database is accessible

---

**Happy Deploying! 🚀** 