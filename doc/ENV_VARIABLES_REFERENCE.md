# Environment Variables Reference

This document lists all the environment variables needed for the AI Recruitment Backend system.

## Resume Parsing Configuration

```bash
# Choose parsing method: 'spacy', 'azure_di', or 'langextract'
RESUME_PARSING_METHOD=spacy
```

## Azure OpenAI Configuration (Shared by AI Services and LangExtract)

```bash
# Azure OpenAI credentials (used by both AI summary service and LangExtract)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-02-01
```

## Azure Document Intelligence (Optional - for azure_di parsing method)

```bash
# Azure Document Intelligence credentials
AZURE_DI_ENDPOINT=https://your-di-resource.cognitiveservices.azure.com/
AZURE_DI_API_KEY=your_azure_di_api_key
```

## Database Configuration

```bash
# Database connection
DATABASE_URL=your_database_connection_string
```

## Complete .env File Example

```bash
# Resume Parsing Method
RESUME_PARSING_METHOD=langextract

# Azure OpenAI (shared by AI services and LangExtract)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small
AZURE_OPENAI_API_VERSION=2024-02-01

# Azure Document Intelligence (optional)
AZURE_DI_ENDPOINT=https://your-di-resource.cognitiveservices.azure.com/
AZURE_DI_API_KEY=your_azure_di_api_key

# Bulk Processing Configuration
# Threading and rate limiting for bulk AI operations and batch resume parsing
AI_BULK_MAX_CONCURRENT_WORKERS=5
AI_BULK_RATE_LIMIT_DELAY_SECONDS=1.0

# File Upload Configuration
# Individual file size limit (in bytes) - default: 16MB
MAX_CONTENT_LENGTH=16777216
# Total batch upload size limit (in bytes) - default: 200MB
BATCH_UPLOAD_LIMIT=209715200

# Database
DATABASE_URL=your_database_connection_string
```

## Notes

- **LangExtract has two options:**
  1. **Gemini API** (if you have `LANGEXTRACT_API_KEY`) - Uses Google's Gemini models
  2. **Azure OpenAI Fallback** - Uses your existing Azure OpenAI credentials
- **Automatic fallback** - If Gemini fails or API key is missing, automatically uses Azure OpenAI
- **Cost-effective** - Azure OpenAI fallback uses your existing deployment
- **Consistent billing** - Azure OpenAI usage appears under your existing resource 