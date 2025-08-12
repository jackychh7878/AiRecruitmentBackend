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

Copy `env.example` to `.env` and configure:

```bash
# Database
DATABASE_URL=postgresql://username:password@host:port/database

# OpenAI
OPENAI_API_KEY=your_openai_api_key
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# Flask
FLASK_ENV=production
HOST=0.0.0.0
PORT=5000
WORKERS=4
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 