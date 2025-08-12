# API Quick Reference Guide

## Most Used Endpoints

### 🔍 **Semantic Search**
```javascript
// Search candidates
POST /api/candidates/semantic-search
{
  "query": "Python developer with ML experience",
  "confidence_threshold": 0.7,
  "max_results": 20
}
```

### 👤 **Candidate Management**
```javascript
// Get all candidates
GET /api/candidates?page=1&per_page=20&include_relationships=true

// Get specific candidate
GET /api/candidates/{id}?include_relationships=true

// Create candidate
POST /api/candidates

// Update candidate
PATCH /api/candidates/{id}

// Delete candidate
DELETE /api/candidates/{id}
```

### 📄 **Resume Operations**
```javascript
// Upload resume
POST /api/candidates/{id}/resumes
// Use FormData with 'resume_file'

// Parse resume
POST /api/candidates/parse-resume
// Use FormData with 'resume_file'

// Download resume
GET /api/candidates/resumes/{id}/download
```

### 🤖 **AI Features**
```javascript
// Generate AI summary (via PATCH)
PATCH /api/candidates/{id}?generate_ai_summary=true

// Bulk AI regeneration
POST /api/candidates/ai-summary/bulk-regenerate
{
  "created_by": "user@company.com"
}

// Monitor bulk job
GET /api/candidates/ai-summary/bulk-regenerate/jobs/{job_id}
```

### ⚙️ **System Configuration**
```javascript
// Get search statistics
GET /api/candidates/semantic-search/statistics

// Get search examples
GET /api/candidates/semantic-search/example-queries

// Get active prompt template
GET /api/candidates/ai-summary/prompt-template
```

## Common Response Patterns

### ✅ **Success Response**
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### ❌ **Error Response**
```json
{
  "message": "Error description",
  "error_code": "ERROR_CODE"
}
```

### 📊 **Paginated Response**
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

## Key Headers
```javascript
{
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
```

## Environment Variables
```bash
# Required
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint

# Optional
SEMANTIC_SEARCH_SEMANTIC_WEIGHT=0.7
AI_BULK_MAX_CONCURRENT_WORKERS=5
``` 