# AI Recruitment Backend - Frontend API Documentation

## Table of Contents
1. [Authentication & Base Configuration](#authentication--base-configuration)
2. [Candidate Profile Management](#candidate-profile-management)
3. [Semantic Search API](#semantic-search-api)
4. [Resume Management](#resume-management)
5. [AI Summary & Embedding](#ai-summary--embedding)
6. [Prompt Template Management](#prompt-template-management)
7. [Bulk AI Regeneration](#bulk-ai-regeneration)
8. [Related Entity Management](#related-entity-management)
9. [Error Handling](#error-handling)
10. [Data Models](#data-models)

---

## Authentication & Base Configuration

### Base URL
```
http://localhost:5000/api
```

### Headers
```javascript
{
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
```

---

## Candidate Profile Management

### 1. Get All Candidates

**Endpoint:** `GET /candidates`

**Description:** Retrieve a paginated list of candidate profiles with comprehensive search and filtering capabilities. Active candidates are sorted first, followed by inactive candidates.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10, max: 100)
- `is_active` (optional): Filter by active status (if not specified, shows all with active first)
- `search` (optional): Search across name, email, classification, or sub-classification tags (partial match)
- `classification` (optional): Filter by classification
- `sub_classification` (optional): Filter by sub-classification tags (comma-separated)
- `location` (optional): Filter by location
- `citizenship` (optional): Filter by citizenship/visa status
- `include_relationships` (optional): Include related data (default: false)

**Request Examples:**
```javascript
// Basic pagination
fetch('/api/candidates?page=1&per_page=20&include_relationships=true')

// Search by name or email
fetch('/api/candidates?search=john')

// Search by classification
fetch('/api/candidates?search=software engineer')

// Search by sub-classification tags (new tag feature)
fetch('/api/candidates?search=full stack developer,business analyst')

// Filter by specific sub-classification tags
fetch('/api/candidates?sub_classification=react developer,node.js')

// Combined search and filters
fetch('/api/candidates?search=python&classification=software&is_active=true')
```

**Response (200 OK):**
```json
{
  "candidates": [
    // Note: Results are sorted with active candidates first, then inactive
    // sub_classification_of_interest now supports comma-separated tags
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@email.com",
      "location": "New York, NY",
      "phone_number": "+1-555-0123",
      "personal_summary": "Experienced software engineer...",
      "availability_weeks": 2,
      "preferred_work_types": "Remote, Hybrid",
      "right_to_work": true,
      "salary_expectation": 120000.00,
      "classification_of_interest": "Software Engineering",
      "sub_classification_of_interest": "full stack developer,react developer",
      "is_active": true,
      "remarks": "Open to relocation",
      "ai_short_summary": "5 years of experience in full-stack development...",
      "created_date": "2025-01-15T10:30:00",
      "last_modified_date": "2025-01-20T14:45:00",
      "career_history": [...],
      "skills": [...],
      "education": [...],
      "licenses_certifications": [...],
      "languages": [...],
      "resumes": [...]
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
```

### 2. Get Candidate by ID

**Endpoint:** `GET /candidates/{candidate_id}`

**Description:** Retrieve a specific candidate profile by ID with optional relationship data.

**Path Parameters:**
- `candidate_id` (required): Integer ID of the candidate

**Query Parameters:**
- `include_relationships` (optional): Include related data (default: false)

**Request Example:**
```javascript
fetch('/api/candidates/1?include_relationships=true')
```

**Response (200 OK):**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@email.com",
  // ... same structure as above
}
```

**Error Response (404 Not Found):**
```json
{
  "message": "Candidate not found"
}
```

### 3. Create New Candidate

**Endpoint:** `POST /candidates`

**Description:** Create a new candidate profile with optional related entities.

**Request Body:**
```json
{
  "first_name": "Jane",
  "last_name": "Smith",
  "email": "jane.smith@email.com",
  "location": "San Francisco, CA",
  "phone_number": "+1-555-0456",
  "personal_summary": "Passionate data scientist...",
  "availability_weeks": 4,
  "preferred_work_types": "Remote",
  "right_to_work": true,
  "salary_expectation": 140000.00,
  "classification_of_interest": "Data Science",
  "sub_classification_of_interest": "Machine Learning",
  "remarks": "Specialized in NLP and computer vision",
  "career_history": [
    {
      "job_title": "Senior Data Scientist",
      "company_name": "Tech Corp",
      "start_date": "2022-01-01",
      "end_date": "2024-12-31",
      "description": "Led machine learning projects..."
    }
  ],
  "skills": [
    {
      "skills": "Python, TensorFlow, PyTorch, SQL",
      "career_history_id": null
    }
  ],
  "education": [
    {
      "school": "Stanford University",
      "degree": "Master of Science",
      "field_of_study": "Computer Science",
      "start_date": "2020-09-01",
      "end_date": "2022-06-01",
      "grade": "3.9/4.0"
    }
  ]
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Candidate profile created successfully",
  "candidate": {
    "id": 2,
    "first_name": "Jane",
    // ... complete candidate data
  }
}
```

### 4. Update Candidate Profile

**Endpoint:** `PATCH /candidates/{candidate_id}`

**Description:** Update an existing candidate profile. Can also trigger AI summary generation and embedding creation.

**Path Parameters:**
- `candidate_id` (required): Integer ID of the candidate

**Query Parameters:**
- `generate_ai_summary` (optional): Generate AI summary and embedding (default: false)

**Request Body:**
```json
{
  "first_name": "Jane",
  "location": "Seattle, WA",
  "salary_expectation": 150000.00,
  "remarks": "Updated remarks with new information"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Candidate profile updated successfully",
  "candidate": {
    "id": 2,
    "first_name": "Jane",
    "location": "Seattle, WA",
    // ... updated data
  }
}
```

### 5. Delete Candidate

**Endpoint:** `DELETE /candidates/{candidate_id}`

**Description:** Soft delete a candidate profile (sets is_active to false).

**Path Parameters:**
- `candidate_id` (required): Integer ID of the candidate

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Candidate profile deleted successfully"
}
```

---

## Semantic Search API

### 1. Semantic Search

**Endpoint:** `POST /candidates/semantic-search`

**Description:** Search candidates using hybrid semantic similarity and keyword matching.

**Request Body:**
```json
{
  "query": "Python developer with machine learning experience",
  "confidence_threshold": 0.7,
  "max_results": 20,
  "include_relationships": true
}
```

**Parameters:**
- `query` (required): Natural language search query
- `confidence_threshold` (optional): Minimum similarity score 0.0-1.0 (default: 0.7)
- `max_results` (optional): Maximum results (default: 50, max: 100)
- `include_relationships` (optional): Include related data (default: false)

**Response (200 OK):**
```json
{
  "success": true,
  "results": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@email.com",
      "semantic_score": 0.8542,
      "keyword_score": 0.9234,
      "hybrid_score": 0.8765,
      "confidence_level": "Very High",
      "relevance_percentage": 87.7,
      "scoring_breakdown": {
        "semantic_weight": 0.7,
        "keyword_weight": 0.3,
        "semantic_contribution": 0.5979,
        "keyword_contribution": 0.2770
      },
      "ai_short_summary": "5 years of experience in full-stack development...",
      "career_history": [...],
      "skills": [...]
    }
  ],
  "total_found": 15,
  "query": "Python developer with machine learning experience",
  "confidence_threshold": 0.7,
  "query_embedding_dimension": 1536
}
```

### 2. Search Statistics

**Endpoint:** `GET /candidates/semantic-search/statistics`

**Description:** Get system statistics and hybrid scoring configuration.

**Response (200 OK):**
```json
{
  "total_active_candidates": 150,
  "candidates_with_embeddings": 120,
  "candidates_without_embeddings": 30,
  "embedding_coverage_percentage": 80.0,
  "default_confidence_threshold": 0.7,
  "max_results_limit": 50,
  "hybrid_scoring": {
    "semantic_weight": 0.7,
    "keyword_weight": 0.3,
    "formula": "0.7 × semantic_score + 0.3 × keyword_score",
    "description": "Hybrid scoring combines semantic similarity with exact keyword matching"
  }
}
```

### 3. Search Examples

**Endpoint:** `GET /candidates/semantic-search/example-queries`

**Description:** Get example search queries and usage tips.

**Response (200 OK):**
```json
{
  "examples": [
    {
      "category": "Technical Skills",
      "queries": [
        "Python developer with machine learning experience",
        "Full-stack developer with React and Node.js"
      ]
    }
  ],
  "tips": [
    "Use specific skills and technologies for better results",
    "Include industry or domain knowledge when relevant"
  ],
  "confidence_thresholds": {
    "0.5+": "Very High - Very specific matches",
    "0.4+": "High - Strong matches",
    "0.+": "Good - Relevant matches (default)"
  }
}
```

---

## Resume Management

### 1. Upload Resume

**Endpoint:** `POST /candidates/{candidate_id}/resumes`

**Description:** Upload a PDF resume for a candidate.

**Path Parameters:**
- `candidate_id` (required): Integer ID of the candidate

**Request Body (multipart/form-data):**
```javascript
const formData = new FormData();
formData.append('resume_file', fileInput.files[0]);
formData.append('remarks', 'Updated resume with latest experience');

fetch(`/api/candidates/${candidateId}/resumes`, {
  method: 'POST',
  body: formData
});
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Resume uploaded successfully",
  "resume": {
    "id": 1,
    "candidate_id": 1,
    "file_name": "john_doe_resume.pdf",
    "file_size": 245760,
    "content_type": "application/pdf",
    "upload_date": "2025-01-20T15:30:00",
    "is_active": true
  }
}
```

### 2. Get Resume

**Endpoint:** `GET /candidates/{candidate_id}/resumes/{resume_id}`

**Description:** Get resume details by ID.

**Response (200 OK):**
```json
{
  "id": 1,
  "candidate_id": 1,
  "file_name": "john_doe_resume.pdf",
  "file_size": 245760,
  "content_type": "application/pdf",
  "upload_date": "2025-01-20T15:30:00",
  "is_active": true
}
```

### 3. Download Resume

**Endpoint:** `GET /candidates/resumes/{resume_id}/download`

**Description:** Download the actual PDF file.

**Response:** Binary PDF file with appropriate headers.

### 4. Delete Resume

**Endpoint:** `DELETE /candidates/{candidate_id}/resumes/{resume_id}`

**Description:** Soft delete a resume.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Resume deleted successfully"
}
```

---

## AI Summary & Embedding

### 1. Resume Parsing

**Endpoint:** `POST /candidates/parse-resume`

**Description:** Parse a PDF resume and extract candidate information for profile creation.

**Request Body (multipart/form-data):**
```javascript
const formData = new FormData();
formData.append('resume_file', fileInput.files[0]);

fetch('/api/candidates/parse-resume', {
  method: 'POST',
  body: formData
});
```

**Response (200 OK):**
```json
{
  "success": true,
  "parsed_data": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@email.com",
    "phone_number": "+1-555-0123",
    "personal_summary": "Experienced software engineer...",
    "career_history": [...],
    "skills": [...],
    "education": [...],
    "licenses_certifications": [...],
    "languages": [...]
  },
  "parsing_metadata": {
    "processing_time": 2.5,
    "confidence_score": 0.85
  }
}
```

### 2. Create Candidate from Parsed Data

**Endpoint:** `POST /candidates/create-from-parsed-data`

**Description:** Create a new candidate profile from parsed resume data.

**Request Body:**
```json
{
  "parsed_data": {
    "first_name": "John",
    "last_name": "Doe",
    // ... parsed data from resume
  },
  "remarks": "Created from resume parsing"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Candidate profile created from parsed data",
  "candidate": {
    "id": 3,
    // ... complete candidate data
  }
}
```

---

## Prompt Template Management

### 1. Get All Prompt Templates

**Endpoint:** `GET /candidates/ai-summary/prompt-templates`

**Description:** Retrieve all AI prompt templates with pagination and filtering.

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `per_page` (optional): Items per page (default: 10)
- `active_only` (optional): Filter by active status (true/false)

**Response (200 OK):**
```json
{
  "templates": [
    {
      "id": 1,
      "name": "Default Recruitment Summary",
      "description": "Standard template for candidate summaries",
      "template_content": "You are an AI assistant...",
      "is_active": true,
      "version_number": 1,
      "created_by": "system",
      "created_date": "2025-01-01T00:00:00",
      "last_modified_date": "2025-01-01T00:00:00"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 5,
    "pages": 1
  },
  "filters": {
    "active_only": null
  }
}
```

### 2. Get Active Prompt Template

**Endpoint:** `GET /candidates/ai-summary/prompt-template`

**Description:** Get the currently active prompt template.

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Default Recruitment Summary",
  "template_content": "You are an AI assistant...",
  "is_active": true,
  "version_number": 1
}
```

### 3. Create Prompt Template

**Endpoint:** `POST /candidates/ai-summary/prompt-templates`

**Description:** Create a new prompt template.

**Request Body:**
```json
{
  "name": "Custom Summary Template",
  "description": "Template for specific industry summaries",
  "template_content": "You are an AI assistant specializing in...",
  "created_by": "admin@company.com"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Prompt template created successfully",
  "template": {
    "id": 2,
    "name": "Custom Summary Template",
    // ... complete template data
  }
}
```

### 4. Update Prompt Template

**Endpoint:** `PUT /candidates/ai-summary/prompt-templates/{template_id}`

**Description:** Update an existing prompt template.

**Request Body:**
```json
{
  "name": "Updated Template Name",
  "description": "Updated description",
  "template_content": "Updated template content..."
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Prompt template updated successfully",
  "template": {
    // ... updated template data
  }
}
```

### 5. Activate Prompt Template

**Endpoint:** `POST /candidates/ai-summary/prompt-templates/{template_id}/activate`

**Description:** Activate a specific prompt template (deactivates others).

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Prompt template activated successfully"
}
```

### 6. Delete Prompt Template

**Endpoint:** `DELETE /candidates/ai-summary/prompt-templates/{template_id}`

**Description:** Hard delete a prompt template.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Prompt template deleted successfully"
}
```

---

## Bulk AI Regeneration

### 1. Start Bulk Regeneration

**Endpoint:** `POST /candidates/ai-summary/bulk-regenerate`

**Description:** Start bulk regeneration of AI summaries and embeddings for all candidates.

**Request Body:**
```json
{
  "created_by": "admin@company.com",
  "prompt_template_id": 1
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Bulk regeneration job started successfully",
  "job_id": "bulk_regen_20250120_153000_1",
  "warnings": [
    "This process may take a long time",
    "Maximum 5 parallel processes for rate limiting"
  ]
}
```

### 2. Get Job Status

**Endpoint:** `GET /candidates/ai-summary/bulk-regenerate/jobs/{job_id}`

**Description:** Get detailed status of a bulk regeneration job.

**Response (200 OK):**
```json
{
  "job_id": "bulk_regen_20250120_153000_1",
  "status": "processing",
  "started_at": "2025-01-20T15:30:00",
  "created_by": "admin@company.com",
  "prompt_template_id": 1,
  "total_profiles": 150,
  "processed_profiles": 45,
  "successful_updates": 42,
  "failed_updates": 3,
  "current_profile_id": 46,
  "estimated_completion": "2025-01-20T16:15:00",
  "errors": [
    "Failed to process profile 23: Network timeout"
  ],
  "completed_at": null
}
```

### 3. Get All Active Jobs

**Endpoint:** `GET /candidates/ai-summary/bulk-regenerate/jobs`

**Description:** List all active bulk regeneration jobs.

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "job_id": "bulk_regen_20250120_153000_1",
      "status": "processing",
      "started_at": "2025-01-20T15:30:00",
      "total_profiles": 150,
      "processed_profiles": 45
    }
  ],
  "total_jobs": 1
}
```

### 4. Cancel Job

**Endpoint:** `DELETE /candidates/ai-summary/bulk-regenerate/jobs/{job_id}`

**Description:** Cancel a running bulk regeneration job.

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Job cancelled successfully"
}
```

### 5. Get Bulk Regeneration Statistics

**Endpoint:** `GET /candidates/ai-summary/bulk-regenerate/stats`

**Description:** Get system capacity and statistics for bulk operations.

**Response (200 OK):**
```json
{
  "max_concurrent_workers": 5,
  "rate_limit_delay_seconds": 1.0,
  "active_jobs_count": 1,
  "system_capacity": "Available for new jobs",
  "estimated_processing_time_per_profile": "2-5 seconds"
}
```

---

## Related Entity Management

### Career History

#### Get All Career History
**Endpoint:** `GET /candidates/{candidate_id}/career-history`

#### Create Career History
**Endpoint:** `POST /candidates/{candidate_id}/career-history`

#### Update Career History
**Endpoint:** `PUT /candidates/{candidate_id}/career-history/{history_id}`

#### Delete Career History
**Endpoint:** `DELETE /candidates/{candidate_id}/career-history/{history_id}`

### Skills

#### Get All Skills
**Endpoint:** `GET /candidates/{candidate_id}/skills`

#### Create Skills
**Endpoint:** `POST /candidates/{candidate_id}/skills`

#### Update Skills
**Endpoint:** `PUT /candidates/{candidate_id}/skills/{skill_id}`

#### Delete Skills
**Endpoint:** `DELETE /candidates/{candidate_id}/skills/{skill_id}`

### Education

#### Get All Education
**Endpoint:** `GET /candidates/{candidate_id}/education`

#### Create Education
**Endpoint:** `POST /candidates/{candidate_id}/education`

#### Update Education
**Endpoint:** `PUT /candidates/{candidate_id}/education/{education_id}`

#### Delete Education
**Endpoint:** `DELETE /candidates/{candidate_id}/education/{education_id}`

### Licenses & Certifications

#### Get All Licenses
**Endpoint:** `GET /candidates/{candidate_id}/licenses-certifications`

#### Create License
**Endpoint:** `POST /candidates/{candidate_id}/licenses-certifications`

#### Update License
**Endpoint:** `PUT /candidates/{candidate_id}/licenses-certifications/{license_id}`

#### Delete License
**Endpoint:** `DELETE /candidates/{candidate_id}/licenses-certifications/{license_id}`

### Languages

#### Get All Languages
**Endpoint:** `GET /candidates/{candidate_id}/languages`

#### Create Language
**Endpoint:** `POST /candidates/{candidate_id}/languages`

#### Update Language
**Endpoint:** `PUT /candidates/{candidate_id}/languages/{language_id}`

#### Delete Language
**Endpoint:** `DELETE /candidates/{candidate_id}/languages/{language_id}`

---

## Error Handling

### Standard Error Response Format

```json
{
  "message": "Error description",
  "error_code": "ERROR_CODE",
  "details": {
    "field": "Additional error information"
  }
}
```

### HTTP Status Codes

| Status | Description | Common Causes |
|--------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request body or parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource already exists |
| 415 | Unsupported Media Type | Invalid file format |
| 422 | Unprocessable Entity | Validation errors |
| 500 | Internal Server Error | Server-side error |

### Common Error Scenarios

#### 1. Validation Errors (400)
```json
{
  "message": "Validation failed",
  "errors": [
    {
      "field": "email",
      "message": "Invalid email format"
    },
    {
      "field": "salary_expectation",
      "message": "Must be a positive number"
    }
  ]
}
```

#### 2. Resource Not Found (404)
```json
{
  "message": "Candidate not found",
  "candidate_id": 999
}
```

#### 3. Conflict Errors (409)
```json
{
  "message": "Email already exists",
  "existing_candidate_id": 1
}
```

#### 4. File Upload Errors (415)
```json
{
  "message": "Unsupported file type. Only PDF files are allowed.",
  "uploaded_type": "image/jpeg"
}
```

#### 5. AI Service Errors (500)
```json
{
  "message": "AI summary generation failed",
  "error": "Azure OpenAI service unavailable",
  "retry_after": 300
}
```

---

## Data Models

### Candidate Profile
```typescript
interface CandidateProfile {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  location?: string;
  phone_number?: string;
  personal_summary?: string;
  availability_weeks?: number;
  preferred_work_types?: string;
  right_to_work: boolean;
  salary_expectation?: number;
  classification_of_interest?: string;
  sub_classification_of_interest?: string;
  is_active: boolean;
  remarks?: string;
  ai_short_summary?: string;
  created_date: string;
  last_modified_date: string;
}
```

### Career History
```typescript
interface CareerHistory {
  id: number;
  candidate_id: number;
  job_title: string;
  company_name: string;
  start_date: string;
  end_date?: string;
  description?: string;
  is_active: boolean;
  created_date: string;
  last_modified_date: string;
}
```

### Skills
```typescript
interface Skills {
  id: number;
  candidate_id: number;
  career_history_id?: number;
  skills: string;
  is_active: boolean;
  created_date: string;
  last_modified_date: string;
}
```

### Education
```typescript
interface Education {
  id: number;
  candidate_id: number;
  school: string;
  degree: string;
  field_of_study: string;
  start_date: string;
  end_date?: string;
  grade?: string;
  description?: string;
  is_active: boolean;
  created_date: string;
  last_modified_date: string;
}
```

### Semantic Search Result
```typescript
interface SemanticSearchResult extends CandidateProfile {
  semantic_score: number;
  keyword_score: number;
  hybrid_score: number;
  confidence_level: string;
  relevance_percentage: number;
  scoring_breakdown: {
    semantic_weight: number;
    keyword_weight: number;
    semantic_contribution: number;
    keyword_contribution: number;
  };
}
```

---

## Frontend Implementation Tips

### 1. File Upload Handling
```javascript
// Resume upload with progress
const uploadResume = async (candidateId, file) => {
  const formData = new FormData();
  formData.append('resume_file', file);
  
  try {
    const response = await fetch(`/api/candidates/${candidateId}/resumes`, {
      method: 'POST',
      body: formData
    });
    
    if (!response.ok) {
      throw new Error(`Upload failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Resume upload error:', error);
    throw error;
  }
};
```

### 2. Semantic Search with Debouncing
```javascript
import { debounce } from 'lodash';

const searchCandidates = debounce(async (query, options = {}) => {
  try {
    const response = await fetch('/api/candidates/semantic-search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        confidence_threshold: 0.7,
        max_results: 20,
        include_relationships: true,
        ...options
      })
    });
    
    if (!response.ok) {
      throw new Error(`Search failed: ${response.statusText}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Search error:', error);
    throw error;
  }
}, 300);
```

### 3. Real-time Job Monitoring
```javascript
const monitorJob = async (jobId) => {
  const interval = setInterval(async () => {
    try {
      const response = await fetch(`/api/candidates/ai-summary/bulk-regenerate/jobs/${jobId}`);
      const jobStatus = await response.json();
      
      updateJobProgress(jobStatus);
      
      if (['completed', 'failed', 'cancelled'].includes(jobStatus.status)) {
        clearInterval(interval);
        handleJobCompletion(jobStatus);
      }
    } catch (error) {
      console.error('Job monitoring error:', error);
    }
  }, 5000); // Check every 5 seconds
  
  return () => clearInterval(interval);
};
```

### 4. Error Boundary Implementation
```javascript
class APIErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('API Error:', error, errorInfo);
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <h2>Something went wrong</h2>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Try again
          </button>
        </div>
      );
    }
    
    return this.props.children;
  }
}
```

---

## Rate Limiting & Performance

### 1. Request Throttling
- **Semantic Search**: 10 requests per minute per user
- **AI Summary Generation**: 5 requests per minute per user
- **Bulk Operations**: 1 request per 5 minutes per user

### 2. Response Caching
- **Search Results**: Cache for 5 minutes
- **Candidate Profiles**: Cache for 10 minutes
- **Statistics**: Cache for 1 hour

### 3. Pagination Guidelines
- **Default page size**: 10 items
- **Maximum page size**: 100 items
- **Recommended page size**: 20-50 items

---

## Testing & Development

### 1. Local Development
```bash
# Start the backend
python app.py

# Test endpoints
python test_semantic_search.py
```

### 2. Environment Variables
```bash
# Required for AI features
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Optional configuration
SEMANTIC_SEARCH_SEMANTIC_WEIGHT=0.7
AI_BULK_MAX_CONCURRENT_WORKERS=5
```

### 3. Health Check
```javascript
// Check if backend is running
const healthCheck = async () => {
  try {
    const response = await fetch('/api/candidates/semantic-search/statistics');
    return response.ok;
  } catch {
    return false;
  }
};
```

This comprehensive API documentation provides frontend developers with everything they need to integrate with the AI Recruitment Backend system. Each endpoint includes detailed request/response examples, error handling, and implementation tips for a smooth development experience. 