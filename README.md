# AI Recruitment Backend Database Schema

This repository contains the PostgreSQL database schema for an AI-powered recruitment system designed to manage candidate profiles comprehensively.

## Overview

The database is designed to store detailed candidate information including personal details, career history, skills, education, certifications, languages, and resume files. It supports AI/ML capabilities through embedding vectors and includes proper indexing for efficient querying.

## 🐳 Docker Deployment

### Quick Start with Docker

```bash
# Build and run the application
chmod +x build-and-run.sh
./build-and-run.sh
```

### Manual Docker Commands

```bash
# Build the image
docker build -t ai-recruitment-backend .

# Run the container
docker run -d \
  --name ai-recruitment-backend \
  -p 5000:5000 \
  --env-file .env \
  ai-recruitment-backend
```

### Azure Container Apps Deployment

```bash
# Deploy to Azure Container Apps
chmod +x deploy-azure.sh
./deploy-azure.sh
```

For detailed deployment instructions, see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).

## 🧠 Resume Parsing Engine

This system includes an advanced resume parsing engine that supports three different parsing methods:

### Parsing Methods

| Method | Description | Best For | Requirements |
|--------|-------------|----------|--------------|
| **spacy** | Traditional NER using spaCy and NLTK | Lightweight, offline processing | `python -m spacy download en_core_web_sm` |
| **azure_di** | Azure Document Intelligence | Complex PDF layouts, tables | Azure DI resource |
| **langextract** | Google LangExtract + Azure OpenAI Fallback | Highest accuracy, AI understanding | Gemini API key OR Azure OpenAI |

### Configuration

Set the parsing method using environment variables:

```bash
# Choose parsing method: 'spacy', 'azure_di', or 'langextract'
RESUME_PARSING_METHOD=spacy

# For Azure Document Intelligence
AZURE_DI_ENDPOINT=https://your-di-resource.cognitiveservices.azure.com/
AZURE_DI_API_KEY=your_azure_di_api_key

# For LangExtract (Option 1: Gemini API)
LANGEXTRACT_API_KEY=your_google_gemini_api_key

# For LangExtract (Option 2: Azure OpenAI fallback - uses existing credentials)
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

For detailed setup instructions, see [RESUME_PARSING_CONFIGURATION.md](RESUME_PARSING_CONFIGURATION.md).

## Database Schema

### Main Tables

#### 1. `candidate_master_profile`
The central table containing candidate personal information and AI-generated summaries.

**Key Features:**
- Simple auto-incrementing integer primary keys (SERIAL)
- Email uniqueness constraint
- Support for 1536-dimension embedding vectors (OpenAI compatible)
- JSONB metadata field for flexible data storage
- Automatic timestamp management

#### 2. Related Tables (One-to-Many relationships)

- **`candidate_career_history`** - Employment history with support for current roles
- **`candidate_skills`** - Skills linked to candidates and optionally to specific career history
- **`candidate_education`** - Educational background and qualifications
- **`candidate_licenses_certifications`** - Professional licenses and certifications
- **`candidate_languages`** - Language proficiencies with levels
- **`candidate_resume`** - Azure blob storage references for resume files

#### 3. Lookup Table

- **`ai_recruitment_com_code`** - Configurable codes for work types, classifications, etc.

## Features

### 🚀 Performance Optimizations
- Comprehensive indexing strategy
- Vector similarity search support (pgvector)
- Efficient foreign key relationships
- Optimized for common query patterns

### 🔄 Data Integrity
- Foreign key constraints with CASCADE deletes
- Unique constraints where appropriate
- Automatic timestamp updates via triggers
- Boolean flags for soft deletes (`is_active`)

### 🤖 AI/ML Ready
- Embedding vector storage (1536 dimensions)
- JSONB metadata fields
- AI-generated summary fields
- Flexible classification system

### 📊 Analytics Friendly
- Created/modified date tracking
- Soft delete support
- Comprehensive candidate profiling
- Relationship tracking between skills and career history

## Prerequisites

1. **PostgreSQL 12+** with the following extensions:
   - `vector` (pgvector for embedding storage)

2. **pgvector Extension**
   ```bash
   # Install pgvector (varies by system)
   # For Ubuntu/Debian:
   sudo apt install postgresql-15-pgvector
   
   # For macOS with Homebrew:
   brew install pgvector
   ```

## Setup Instructions

### 1. Create Database
```sql
CREATE DATABASE ai_recruitment_db;
\c ai_recruitment_db;
```

### 2. Run Schema Creation
```bash
psql -d ai_recruitment_db -f database_schema.sql
```

### 3. Load Sample Data (Optional)
```bash
psql -d ai_recruitment_db -f sample_data.sql
```

## Usage Examples

### Basic Queries

#### Get candidate with full profile
```sql
SELECT 
    c.*,
    array_agg(DISTINCT ch.job_title) as job_titles,
    array_agg(DISTINCT cs.skills) as skills,
    array_agg(DISTINCT cl.language) as languages
FROM candidate_master_profile c
LEFT JOIN candidate_career_history ch ON c.id = ch.candidate_id
LEFT JOIN candidate_skills cs ON c.id = cs.candidate_id
LEFT JOIN candidate_languages cl ON c.id = cl.candidate_id
WHERE c.email = 'john.smith@email.com'
GROUP BY c.id;
```

#### Search by skills
```sql
SELECT DISTINCT c.first_name, c.last_name, c.email
FROM candidate_master_profile c
JOIN candidate_skills cs ON c.id = cs.candidate_id
WHERE cs.skills ILIKE '%React%' 
AND c.is_active = true;
```

#### Vector similarity search (requires embedding data)
```sql
SELECT 
    c.first_name, 
    c.last_name, 
    c.email,
    c.embedding_vector <=> '[0.1, 0.2, ...]'::vector as distance
FROM candidate_master_profile c
WHERE c.embedding_vector IS NOT NULL
ORDER BY distance
LIMIT 10;
```

## API Endpoints

The application provides a comprehensive REST API with Swagger documentation:

- **Health Check**: `GET /api/health`
- **Swagger UI**: `/swagger/`
- **Candidates**: `/api/candidates`
- **Resumes**: `/api/resumes`
- **Skills**: `/api/skills`
- **Education**: `/api/education`
- **Languages**: `/api/languages`
- **Licenses**: `/api/licenses-certifications`

## Docker Features

- **Pre-loaded AI Models**: spaCy NER and NLTK data included
- **Health Monitoring**: Built-in health checks and monitoring
- **Production Ready**: Gunicorn server with optimized configuration
- **Azure Optimized**: Ready for Azure Container Apps deployment

## Environment Configuration

Create a `.env` file and configure the following variables:

```bash
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# Azure OpenAI (for AI summaries and embeddings)
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

# Resume Parser Configuration
# Set to 'true' to use Azure Document Intelligence, 'false' for open-source spaCy/NLTK
USE_AZURE_DOCUMENT_INTELLIGENCE=false

# Azure Document Intelligence (only needed if USE_AZURE_DOCUMENT_INTELLIGENCE=true)
AZURE_DI_ENDPOINT=https://your-document-intelligence-resource.cognitiveservices.azure.com/
AZURE_DI_API_KEY=your_document_intelligence_api_key

# Flask
FLASK_ENV=production
FLASK_DEBUG=false
HOST=0.0.0.0
PORT=5000
FRONTEND_URL=http://localhost:3000

# AI Processing Configuration
SEMANTIC_SEARCH_SEMANTIC_WEIGHT=0.7
AI_BULK_MAX_CONCURRENT_WORKERS=5
AI_BULK_RATE_LIMIT_DELAY_SECONDS=1.0
```

### Resume Parser Models

The application supports two resume parsing modes:

**1. Open Source Mode (Default)** - `USE_AZURE_DOCUMENT_INTELLIGENCE=false`
- Uses spaCy and NLTK for named entity recognition
- No additional costs or API keys required
- Requires `python -m spacy download en_core_web_sm`

**2. Azure Document Intelligence Mode** - `USE_AZURE_DOCUMENT_INTELLIGENCE=true`
- Uses Azure's AI Document Intelligence service
- Requires Azure subscription and API credentials
- Generally provides better accuracy for structured documents
- Incurs usage-based costs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 