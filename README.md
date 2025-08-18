# AI Recruitment Backend

An intelligent recruitment management system that leverages AI-powered resume parsing, semantic search, and candidate profiling to streamline the hiring process.

## 🚀 Features

### Core Functionality
- **Candidate Profile Management** - Complete CRUD operations for candidate profiles
- **AI-Powered Resume Parsing** - Extract structured data from PDF resumes using multiple parsing methods
- **Semantic Search** - Find candidates using natural language queries with vector embeddings
- **AI Summary Generation** - Generate intelligent candidate summaries using Azure OpenAI
- **Skills & Experience Tracking** - Manage career history, skills, education, certifications, and languages

### AI & Machine Learning
- **Vector Embeddings** - Generate semantic embeddings for candidate profiles using Azure OpenAI
- **Hybrid Search** - Combine semantic similarity with keyword matching for optimal results
- **Multiple Parsing Methods** - Support for spaCy NLP, Azure Document Intelligence, and LangExtract
- **Bulk AI Processing** - Regenerate AI summaries and embeddings for all candidates with job monitoring

### Technical Features
- **RESTful API** - Comprehensive REST API with Swagger documentation
- **PostgreSQL Database** - Robust data storage with pgvector extension for embeddings
- **Docker Support** - Containerized deployment with multi-stage builds
- **CORS Configuration** - Proper CORS handling for frontend integration
- **Health Monitoring** - Health check endpoints and error handling

## 🛠️ Technology Stack

- **Backend Framework**: Flask with Flask-RESTX
- **Database**: PostgreSQL with pgvector extension
- **AI/ML**: Azure OpenAI (GPT-4o-mini, text-embedding-3-small)
- **NLP Processing**: spaCy, NLTK, LangChain
- **Resume Parsing**: PyPDF2, Azure Document Intelligence, LangExtract
- **Deployment**: Docker, Gunicorn
- **Development**: Python 3.11+

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL with pgvector extension
- Azure OpenAI Service account
- Docker (optional, for containerized deployment)

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd AiRecruitmentBackend
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Download NLP Models
```bash
# Download spaCy model
python -m spacy download en_core_web_sm

# Download NLTK data
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
```

### 5. Database Setup
```bash
# Create PostgreSQL database and enable pgvector
createdb ai_recruitment_db
psql ai_recruitment_db -c "CREATE EXTENSION vector;"

# Run database schema
psql ai_recruitment_db < database_schema.sql

# (Optional) Load sample data
psql ai_recruitment_db < sample_data.sql
```

### 6. Environment Configuration
Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ai_recruitment_db

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-02-01

# Resume Parsing Method (spacy, azure_di, or langextract)
RESUME_PARSING_METHOD=spacy

# Optional: Azure Document Intelligence (for azure_di method)
AZURE_DI_ENDPOINT=https://your-di-resource.cognitiveservices.azure.com/
AZURE_DI_API_KEY=your_azure_di_api_key

# Application Configuration
FLASK_ENV=development
FLASK_DEBUG=true
FRONTEND_URL=http://localhost:3000
```

## 🚀 Running the Application

### Development Mode
```bash
# Start the Flask development server
python app.py
```

### Production Mode
```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# Or use the startup script
chmod +x start.sh
./start.sh
```

### Docker Deployment
```bash
# Build the Docker image
docker build -t ai-recruitment-backend .

# Run the container
docker run -p 5000:5000 --env-file .env ai-recruitment-backend
```

The application will be available at `http://localhost:5000`

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:5000/swagger/`
- **Health Check**: `http://localhost:5000/api/health`

### Key Endpoints

#### Candidate Management
- `GET /api/candidates` - List all candidates with pagination
- `POST /api/candidates` - Create new candidate
- `GET /api/candidates/{id}` - Get candidate by ID
- `PATCH /api/candidates/{id}` - Update candidate
- `DELETE /api/candidates/{id}` - Delete candidate

#### Semantic Search
- `POST /api/candidates/semantic-search` - Search candidates using natural language
- `GET /api/candidates/semantic-search/statistics` - Get search statistics

#### Resume Management
- `POST /api/candidates/{id}/resumes` - Upload resume
- `GET /api/candidates/resumes/{id}/download` - Download resume
- `POST /api/candidates/parse-resume` - Parse resume and extract data

#### AI Services
- `POST /api/candidates/ai-summary/bulk-regenerate` - Start bulk AI regeneration
- `GET /api/candidates/ai-summary/bulk-regenerate/jobs/{job_id}` - Monitor job status

For complete API documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## 🔍 Usage Examples

### Semantic Search
```bash
curl -X POST http://localhost:5000/api/candidates/semantic-search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Python developer with machine learning experience",
    "confidence_threshold": 0.7,
    "max_results": 20,
    "include_relationships": true
  }'
```

### Upload and Parse Resume
```bash
curl -X POST http://localhost:5000/api/candidates/parse-resume \
  -F "resume_file=@resume.pdf"
```

### Create Candidate Profile
```bash
curl -X POST http://localhost:5000/api/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@email.com",
    "location": "New York, NY",
    "skills": [{"skills": "Python, Machine Learning, SQL"}]
  }'
```

## 🔧 Configuration

### Resume Parsing Methods
1. **spaCy (Default)** - Fast, local NLP processing
2. **Azure Document Intelligence** - Cloud-based document analysis
3. **LangExtract** - LLM-powered extraction using Azure OpenAI

Configure via `RESUME_PARSING_METHOD` environment variable.

### Semantic Search Configuration
- `SEMANTIC_SEARCH_SEMANTIC_WEIGHT` - Weight for semantic similarity (default: 0.7)
- Keyword weight is automatically calculated as (1.0 - semantic_weight)

### AI Service Configuration
- `AI_BULK_MAX_CONCURRENT_WORKERS` - Maximum parallel workers for bulk operations (default: 5)

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker build -t ai-recruitment-backend .

# Run with environment file
docker run -p 5000:5000 --env-file .env ai-recruitment-backend

# Run with inline environment variables
docker run -p 5000:5000 \
  -e DATABASE_URL="your_db_url" \
  -e AZURE_OPENAI_ENDPOINT="your_endpoint" \
  -e AZURE_OPENAI_API_KEY="your_key" \
  ai-recruitment-backend
```

### Docker Compose (with PostgreSQL)
```yaml
version: '3.8'
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_DB: ai_recruitment_db
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database_schema.sql:/docker-entrypoint-initdb.d/schema.sql
    ports:
      - "5432:5432"

  backend:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/ai_recruitment_db
      - AZURE_OPENAI_ENDPOINT=your_endpoint
      - AZURE_OPENAI_API_KEY=your_key
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs

volumes:
  postgres_data:
```

## 🧪 Testing

### Run Test Suite
```bash
# Individual tests
python test_case/test_resume_parser.py
python test_case/test_semantic_search.py
python test_case/test_ai_summary.py

# Database tests
python test_case/test_db_connection.py
```

### Health Check
```bash
curl http://localhost:5000/api/health
```

## 📁 Project Structure

```
AiRecruitmentBackend/
├── app.py                    # Main Flask application
├── database.py              # Database configuration
├── models.py                # SQLAlchemy models
├── requirements.txt         # Python dependencies
├── Dockerfile               # Docker configuration
├── start.sh                 # Startup script
├── database_schema.sql      # Database schema
├── routes/                  # API route definitions
│   ├── candidate_profile_routes.py
│   ├── resume_routes.py
│   └── ...
├── services/                # Business logic services
│   ├── resume_parser.py
│   ├── ai_summary_service.py
│   ├── semantic_search_service.py
│   └── bulk_ai_regeneration_service.py
├── test_case/              # Test files
├── doc/                    # Documentation
└── docker_build_script/    # Deployment scripts
```

## 🔐 Security Considerations

- **Environment Variables**: Store sensitive data in `.env` files, not in code
- **CORS Configuration**: Properly configured for frontend domains
- **Input Validation**: API endpoints validate all input data
- **File Upload Security**: PDF validation and size limits for resume uploads
- **Rate Limiting**: Built-in rate limiting for AI service calls

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Error**
   ```bash
   # Check PostgreSQL is running and pgvector is installed
   psql -c "SELECT * FROM pg_extension WHERE extname = 'vector';"
   ```

2. **Azure OpenAI API Error**
   ```bash
   # Verify environment variables
   echo $AZURE_OPENAI_ENDPOINT
   echo $AZURE_OPENAI_API_KEY
   ```

3. **spaCy Model Not Found**
   ```bash
   # Download the English model
   python -m spacy download en_core_web_sm
   ```

4. **NLTK Data Missing**
   ```bash
   # Download required NLTK data
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"
   ```

### Debug Mode
Set `FLASK_DEBUG=true` in your `.env` file for detailed error messages.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Commit your changes: `git commit -am 'Add new feature'`
5. Push to the branch: `git push origin feature-name`
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the [API Documentation](API_DOCUMENTATION.md)
- Review the [Environment Variables Reference](doc/ENV_VARIABLES_REFERENCE.md)
- Check the test cases in the `test_case/` directory for usage examples

## 🎯 Roadmap

- [ ] Additional resume parsing methods
- [ ] Enhanced semantic search with filters
- [ ] Real-time candidate matching
- [ ] Integration with external job boards
- [ ] Advanced analytics and reporting
- [ ] Multi-language support
