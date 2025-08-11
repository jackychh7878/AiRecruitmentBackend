# AI Recruitment Backend Database Schema

This repository contains the PostgreSQL database schema for an AI-powered recruitment system designed to manage candidate profiles comprehensively.

## Overview

The database is designed to store detailed candidate information including personal details, career history, skills, education, certifications, languages, and resume files. It supports AI/ML capabilities through embedding vectors and includes proper indexing for efficient querying.

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
SELECT c.first_name, c.last_name, c.ai_short_summary,
       c.embedding_vector <-> '[0.1,0.2,...]'::vector as similarity
FROM candidate_master_profile c
WHERE c.embedding_vector IS NOT NULL
ORDER BY similarity
LIMIT 10;
```

### Data Insertion Examples

#### Add new candidate
```sql
INSERT INTO candidate_master_profile (
    first_name, last_name, email, location, personal_summary,
    preferred_work_types, right_to_work, salary_expectation
) VALUES (
    'Jane', 'Doe', 'jane.doe@email.com', 'Perth, WA', 
    'Experienced project manager with agile methodology expertise',
    'FULL_TIME,HYBRID', true, 110000.00
);
```

## Database Maintenance

### Regular Maintenance Tasks

1. **Update Statistics**
   ```sql
   ANALYZE;
   ```

2. **Reindex Vector Indexes** (if using many embeddings)
   ```sql
   REINDEX INDEX idx_candidate_master_profile_embedding;
   ```

3. **Clean Up Inactive Records** (optional)
   ```sql
   DELETE FROM candidate_skills WHERE is_active = false 
   AND last_modified_date < NOW() - INTERVAL '1 year';
   ```

## Schema Considerations

### Scalability
- Simple integer primary keys for easy management and better performance
- Proper indexing for common query patterns
- Vector indexes for AI similarity searches

### Flexibility
- JSONB metadata fields for evolving requirements
- Soft delete pattern preserves data integrity
- Configurable lookup codes

### Data Quality
- Email uniqueness prevents duplicates
- Foreign key constraints maintain referential integrity
- Automatic timestamp management

## Future Enhancements

- [ ] Add audit trail tables
- [ ] Implement data retention policies
- [ ] Add more sophisticated search capabilities
- [ ] Include job matching tables
- [ ] Add candidate scoring/ranking tables

## Support

For questions or issues with the database schema, please refer to the PostgreSQL documentation or create an issue in this repository. 