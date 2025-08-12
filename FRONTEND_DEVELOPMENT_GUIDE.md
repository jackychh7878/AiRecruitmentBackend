# Frontend Development Guide: AI-Powered Talent Management System

## Project Context

You are building a **Talent Management System** for a headhunting/recruitment agency. This system manages a talent pool of candidates (resumes) and provides AI-powered features for intelligent candidate matching and profile management.

### Core Purpose
- **Manage candidate profiles** from resume submissions
- **AI-powered candidate summarization** and semantic search
- **Intelligent talent matching** for job requirements
- **Comprehensive profile management** with relationship data

### Key Features
- Resume parsing and profile creation
- AI summary generation and embedding
- Semantic search with hybrid scoring
- Prompt template management
- Bulk AI regeneration capabilities

---

## System Architecture Overview

### Backend Integration
- **Base URL**: `https://ai-recruitment-backend.grayisland-39090923.eastasia.azurecontainerapps.io`
- **Authentication**: Assume already logged in (login system to be added later)
- **AI Services**: Azure OpenAI integration for summaries and embeddings
- **Database**: PostgreSQL with pgvector for semantic search

### Frontend Technology Stack
- **Framework**: React with TypeScript (recommended)
- **State Management**: Redux Toolkit or Zustand
- **UI Library**: Material-UI, Ant Design, or Tailwind CSS
- **HTTP Client**: Axios or React Query
- **File Handling**: FileReader API for PDF uploads

---

## Module 1: Candidate Management

### 1.1 Candidate List Page (Pagination)

**Purpose**: Display all candidates with pagination and search capabilities

**Key Components**:
```typescript
interface CandidateListProps {
  candidates: CandidateProfile[];
  pagination: PaginationInfo;
  loading: boolean;
  onPageChange: (page: number) => void;
  onSearch: (query: string) => void;
  onCreateNew: () => void;
}
```

**API Integration**:
```typescript
// GET /api/candidates?page={page}&per_page={per_page}&include_relationships=true
const fetchCandidates = async (page: number, perPage: number) => {
  const response = await api.get(`/candidates?page=${page}&per_page=${perPage}&include_relationships=true`);
  return response.data;
};
```

**Features**:
- **Pagination controls** with page size selection (10, 20, 50, 100)
- **Search bar** for quick candidate lookup
- **Candidate cards** showing key information (name, role, location, AI summary)
- **Action buttons** (View, Edit, Deactivate, Delete)
- **Status indicators** (Active, Inactive, Pending)

### 1.2 Create New Candidate

**Purpose**: Create candidate profiles with resume import and manual editing

**Workflow**:
1. **Resume Upload**: Drag & drop or file picker for PDF
2. **Resume Parsing**: Call `/api/candidates/parse-resume` API
3. **Form Pre-filling**: Auto-populate form with parsed data
4. **Manual Editing**: Allow user to modify/complete information
5. **Profile Creation**: Call `/api/candidates/create-from-parsed-data` API
6. **Resume Upload**: Upload PDF to candidate profile
7. **AI Finalization**: Trigger AI summary generation

**Key Components**:
```typescript
interface CreateCandidateProps {
  onSuccess: (candidate: CandidateProfile) => void;
  onCancel: () => void;
}

interface ResumeParser {
  onFileUpload: (file: File) => Promise<ParsedResumeData>;
  onParseComplete: (data: ParsedResumeData) => void;
}

interface CandidateForm {
  parsedData: ParsedResumeData;
  onSave: (data: CandidateProfile) => Promise<void>;
  onFinalize: () => Promise<void>;
}
```

**API Integration**:
```typescript
// Step 1: Parse Resume
const parseResume = async (file: File): Promise<ParsedResumeData> => {
  const formData = new FormData();
  formData.append('resume_file', file);
  
  const response = await api.post('/candidates/parse-resume', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  
  return response.data.parsed_data;
};

// Step 2: Create Candidate
const createCandidate = async (parsedData: ParsedResumeData, remarks: string) => {
  const response = await api.post('/candidates/create-from-parsed-data', {
    parsed_data: parsedData,
    remarks
  });
  
  return response.data.candidate;
};

// Step 3: Upload Resume
const uploadResume = async (candidateId: number, file: File) => {
  const formData = new FormData();
  formData.append('resume_file', file);
  formData.append('remarks', 'Initial resume upload');
  
  const response = await api.post(`/candidates/${candidateId}/resumes`, formData);
  return response.data.resume;
};

// Step 4: Finalize with AI
const finalizeCandidate = async (candidateId: number) => {
  const response = await api.patch(`/candidates/${candidateId}?generate_ai_summary=true`, {});
  return response.data.candidate;
};
```

**Form Structure**:
```typescript
interface CandidateFormData {
  // Basic Information
  first_name: string;
  last_name: string;
  email: string;
  phone_number?: string;
  location?: string;
  
  // Professional Details
  personal_summary?: string;
  availability_weeks?: number;
  preferred_work_types?: string;
  right_to_work: boolean;
  salary_expectation?: number;
  classification_of_interest?: string;
  sub_classification_of_interest?: string;
  remarks?: string;
  
  // Related Entities
  career_history: CareerHistory[];
  skills: Skills[];
  education: Education[];
  licenses_certifications: LicenseCertification[];
  languages: Language[];
}
```

### 1.3 Update Existing Candidate

**Purpose**: Edit candidate profiles with module-based CRUD operations

**Module Structure**:
- **Basic Information** (name, contact, location)
- **Career History** (work experience)
- **Skills** (technical and soft skills)
- **Education** (academic background)
- **Licenses & Certifications**
- **Languages**
- **Resumes** (file management)

**CRUD Operations**:
```typescript
// Skills Management
const fetchSkills = async (candidateId: number) => {
  const response = await api.get(`/candidates/${candidateId}/skills`);
  return response.data;
};

const createSkill = async (candidateId: number, skillData: Partial<Skills>) => {
  const response = await api.post(`/candidates/${candidateId}/skills`, skillData);
  return response.data;
};

const updateSkill = async (candidateId: number, skillId: number, skillData: Partial<Skills>) => {
  const response = await api.put(`/candidates/${candidateId}/skills/${skillId}`, skillData);
  return response.data;
};

const deleteSkill = async (candidateId: number, skillId: number) => {
  await api.delete(`/candidates/${candidateId}/skills/${skillId}`);
};
```

**Finalization Workflow**:
1. **Edit Mode**: User can edit any module independently
2. **Save Changes**: Each module saves to its respective API
3. **Finalization Required**: Show warning if user tries to leave without finalizing
4. **AI Processing**: Call finalization API to generate summary and embedding
5. **Confirmation**: Display success message with AI summary preview

**Warning System**:
```typescript
const useFinalizationWarning = (hasUnsavedChanges: boolean) => {
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (hasUnsavedChanges) {
        e.preventDefault();
        e.returnValue = 'You have unsaved changes. Please finalize the profile before leaving.';
        return e.returnValue;
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    return () => window.removeEventListener('beforeunload', handleBeforeUnload);
  }, [hasUnsavedChanges]);
};
```

### 1.4 Candidate Deactivation & Deletion

**Purpose**: Manage candidate lifecycle and data cleanup

**Soft Delete (Deactivate)**:
```typescript
const deactivateCandidate = async (candidateId: number) => {
  await api.delete(`/candidates/${candidateId}`);
  // Update local state to reflect deactivation
};
```

**Hard Delete**:
```typescript
const hardDeleteCandidate = async (candidateId: number) => {
  // Show confirmation dialog
  const confirmed = await showDeleteConfirmation({
    title: 'Permanently Delete Candidate',
    message: 'This action cannot be undone. All data will be permanently removed.',
    confirmText: 'Delete Permanently',
    confirmColor: 'error'
  });
  
  if (confirmed) {
    // Call hard delete API (if available) or update is_active to false
    await api.delete(`/candidates/${candidateId}/permanent`);
  }
};
```

---

## Module 2: Prompt Template Management

**Purpose**: Manage AI prompt templates that control candidate summary generation

### 2.1 Prompt Template List

**Features**:
- **Pagination** for template management
- **Active template indicator** (only one can be active)
- **Template preview** with content truncation
- **Action buttons** (Edit, Activate, Delete)

**API Integration**:
```typescript
const fetchPromptTemplates = async (page: number, activeOnly?: boolean) => {
  const params = new URLSearchParams({ page: page.toString() });
  if (activeOnly !== undefined) {
    params.append('active_only', activeOnly.toString());
  }
  
  const response = await api.get(`/ai-summary/prompt-templates?${params}`);
  return response.data;
};
```

### 2.2 Create/Edit Prompt Template

**Validation Requirements**:
```typescript
const validatePromptTemplate = (content: string): ValidationResult => {
  const errors: string[] = [];
  
  // Check for required placeholder
  if (!content.includes('{candidate_profile_data}')) {
    errors.push('Template must contain {candidate_profile_data} placeholder');
  }
  
  // Check for balanced braces
  const openBraces = (content.match(/\{/g) || []).length;
  const closeBraces = (content.match(/\}/g) || []).length;
  
  if (openBraces !== closeBraces) {
    errors.push('Template has unbalanced braces');
  }
  
  // Check minimum length
  if (content.length < 50) {
    errors.push('Template must be at least 50 characters long');
  }
  
  return {
    isValid: errors.length === 0,
    errors
  };
};
```

**Form Component**:
```typescript
interface PromptTemplateFormProps {
  template?: PromptTemplate;
  onSave: (template: Partial<PromptTemplate>) => Promise<void>;
  onCancel: () => void;
}

const PromptTemplateForm: React.FC<PromptTemplateFormProps> = ({ template, onSave, onCancel }) => {
  const [content, setContent] = useState(template?.template_content || '');
  const [validation, setValidation] = useState<ValidationResult>({ isValid: true, errors: [] });
  
  const handleContentChange = (newContent: string) => {
    setContent(newContent);
    setValidation(validatePromptTemplate(newContent));
  };
  
  const handleSave = async () => {
    if (!validation.isValid) {
      return;
    }
    
    await onSave({
      name: template?.name || '',
      description: template?.description || '',
      template_content: content,
      created_by: 'current_user@company.com'
    });
  };
  
  return (
    <form onSubmit={handleSave}>
      <TextField
        label="Template Name"
        required
        fullWidth
        margin="normal"
      />
      
      <TextField
        label="Description"
        fullWidth
        margin="normal"
        multiline
        rows={2}
      />
      
      <TextField
        label="Template Content"
        required
        fullWidth
        margin="normal"
        multiline
        rows={10}
        value={content}
        onChange={(e) => handleContentChange(e.target.value)}
        error={!validation.isValid}
        helperText={
          validation.isValid 
            ? 'Template is valid' 
            : validation.errors.join(', ')
        }
        placeholder="You are an AI assistant... {candidate_profile_data}..."
      />
      
      <Button type="submit" disabled={!validation.isValid}>
        Save Template
      </Button>
    </form>
  );
};
```

### 2.3 Template Activation

**Purpose**: Activate a template and deactivate others

```typescript
const activateTemplate = async (templateId: number) => {
  try {
    await api.post(`/ai-summary/prompt-templates/${templateId}/activate`);
    
    // Show success message
    showNotification({
      type: 'success',
      message: 'Template activated successfully'
    });
    
    // Refresh template list
    await refreshTemplates();
    
  } catch (error) {
    showNotification({
      type: 'error',
      message: 'Failed to activate template'
    });
  }
};
```

### 2.4 Bulk AI Regeneration

**Purpose**: Regenerate all candidate summaries with new prompt template

**Warning Dialog**:
```typescript
const BulkRegenerationDialog: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  
  const handleStartRegeneration = async () => {
    try {
      setIsProcessing(true);
      
      const response = await api.post('/ai-summary/bulk-regenerate', {
        created_by: 'current_user@company.com'
      });
      
      setJobId(response.data.job_id);
      
      showNotification({
        type: 'warning',
        message: 'Bulk regeneration started. This may take several hours.',
        duration: 10000
      });
      
      // Start monitoring the job
      startJobMonitoring(response.data.job_id);
      
    } catch (error) {
      showNotification({
        type: 'error',
        message: 'Failed to start bulk regeneration'
      });
    } finally {
      setIsProcessing(false);
      setIsOpen(false);
    }
  };
  
  return (
    <Dialog open={isOpen} onClose={() => setIsOpen(false)}>
      <DialogTitle>Bulk AI Regeneration</DialogTitle>
      <DialogContent>
        <Alert severity="warning">
          <strong>Warning:</strong> This operation will regenerate AI summaries and embeddings for ALL candidates.
        </Alert>
        
        <Typography variant="body2" sx={{ mt: 2 }}>
          • Estimated time: 2-6 hours depending on candidate count<br/>
          • Maximum 5 parallel processes for rate limiting<br/>
          • System will be under heavy load during processing<br/>
          • You can monitor progress and cancel if needed
        </Typography>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={() => setIsOpen(false)}>Cancel</Button>
        <Button 
          onClick={handleStartRegeneration}
          disabled={isProcessing}
          color="warning"
          variant="contained"
        >
          {isProcessing ? 'Starting...' : 'Start Regeneration'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

**Job Monitoring**:
```typescript
const useJobMonitoring = (jobId: string | null) => {
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  
  useEffect(() => {
    if (!jobId) return;
    
    const interval = setInterval(async () => {
      try {
        const response = await api.get(`/ai-summary/bulk-regenerate/jobs/${jobId}`);
        setJobStatus(response.data);
        
        if (['completed', 'failed', 'cancelled'].includes(response.data.status)) {
          clearInterval(interval);
          handleJobCompletion(response.data);
        }
      } catch (error) {
        console.error('Job monitoring error:', error);
      }
    }, 5000);
    
    return () => clearInterval(interval);
  }, [jobId]);
  
  return jobStatus;
};
```

---

## Module 3: Semantic Search Feature

**Purpose**: Intelligent candidate search using natural language queries

### 3.1 Search Interface

**Components**:
- **Search Bar**: Google-like search input
- **Search Options**: Confidence threshold toggles
- **Results Display**: Candidate cards with relevance scores
- **Filters**: Additional search criteria

**Search Bar Component**:
```typescript
interface SearchBarProps {
  onSearch: (query: string, options: SearchOptions) => void;
  loading: boolean;
}

const SearchBar: React.FC<SearchBarProps> = ({ onSearch, loading }) => {
  const [query, setQuery] = useState('');
  const [searchMode, setSearchMode] = useState<'broad' | 'balanced' | 'narrow'>('balanced');
  
  const confidenceThresholds = {
    broad: 0.3,
    balanced: 0.7,
    narrow: 0.9
  };
  
  const handleSearch = () => {
    if (query.trim()) {
      onSearch(query.trim(), {
        confidence_threshold: confidenceThresholds[searchMode],
        max_results: 50,
        include_relationships: true
      });
    }
  };
  
  return (
    <div className="search-container">
      <div className="search-bar">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search candidates by skills, experience, or requirements..."
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
        />
        
        <button onClick={handleSearch} disabled={loading}>
          {loading ? <Spinner /> : <SearchIcon />}
        </button>
      </div>
      
      <div className="search-options">
        <ToggleButtonGroup
          value={searchMode}
          exclusive
          onChange={(_, newMode) => newMode && setSearchMode(newMode)}
        >
          <ToggleButton value="broad">Broad Search</ToggleButton>
          <ToggleButton value="balanced">Balanced</ToggleButton>
          <ToggleButton value="narrow">Narrow Search</ToggleButton>
        </ToggleButtonGroup>
        
        <Typography variant="caption" color="textSecondary">
          {searchMode === 'broad' && 'Lower threshold (0.3) - More results, less precise'}
          {searchMode === 'balanced' && 'Medium threshold (0.7) - Balanced results'}
          {searchMode === 'narrow' && 'Higher threshold (0.9) - Fewer results, more precise'}
        </Typography>
      </div>
    </div>
  );
};
```

### 3.2 Search Results

**API Integration**:
```typescript
const searchCandidates = async (query: string, options: SearchOptions) => {
  try {
    setSearchLoading(true);
    
    const response = await api.post('/candidates/semantic-search', {
      query,
      ...options
    });
    
    setSearchResults(response.data.results);
    setSearchStats(response.data);
    
  } catch (error) {
    showNotification({
      type: 'error',
      message: 'Search failed. Please try again.'
    });
  } finally {
    setSearchLoading(false);
  }
};
```

**Results Display**:
```typescript
interface SearchResultCardProps {
  candidate: SemanticSearchResult;
  onClick: (candidate: SemanticSearchResult) => void;
}

const SearchResultCard: React.FC<SearchResultCardProps> = ({ candidate, onClick }) => {
  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'Very High': return 'success';
      case 'High': return 'info';
      case 'Good': return 'warning';
      case 'Moderate': return 'default';
      default: return 'error';
    }
  };
  
  return (
    <Card className="search-result-card" onClick={() => onClick(candidate)}>
      <CardContent>
        <div className="candidate-header">
          <Typography variant="h6">
            {candidate.first_name} {candidate.last_name}
          </Typography>
          
          <Chip
            label={candidate.confidence_level}
            color={getConfidenceColor(candidate.confidence_level)}
            size="small"
          />
        </div>
        
        <Typography variant="body2" color="textSecondary" gutterBottom>
          {candidate.classification_of_interest} • {candidate.location}
        </Typography>
        
        <Typography variant="body2" paragraph>
          {candidate.ai_short_summary}
        </Typography>
        
        <div className="scoring-breakdown">
          <Typography variant="caption" color="textSecondary">
            Relevance: {candidate.relevance_percentage}%
          </Typography>
          
          <div className="score-details">
            <span>Semantic: {Math.round(candidate.semantic_score * 100)}%</span>
            <span>Keyword: {Math.round(candidate.keyword_score * 100)}%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
```

### 3.3 Search Statistics & Examples

**Statistics Display**:
```typescript
const SearchStatistics: React.FC = () => {
  const [stats, setStats] = useState<SearchStatistics | null>(null);
  
  useEffect(() => {
    const fetchStats = async () => {
      const response = await api.get('/candidates/semantic-search/statistics');
      setStats(response.data);
    };
    
    fetchStats();
  }, []);
  
  if (!stats) return <Skeleton />;
  
  return (
    <div className="search-statistics">
      <Typography variant="h6">System Statistics</Typography>
      
      <Grid container spacing={2}>
        <Grid item xs={6}>
          <StatCard
            title="Total Candidates"
            value={stats.total_active_candidates}
            icon={<PeopleIcon />}
          />
        </Grid>
        
        <Grid item xs={6}>
          <StatCard
            title="AI Coverage"
            value={`${stats.embedding_coverage_percentage}%`}
            icon={<AIAnalyticsIcon />}
          />
        </Grid>
      </Grid>
      
      <div className="hybrid-scoring-info">
        <Typography variant="subtitle2">Hybrid Scoring Formula</Typography>
        <Typography variant="body2" color="textSecondary">
          {stats.hybrid_scoring.formula}
        </Typography>
        <Typography variant="caption">
          {stats.hybrid_scoring.description}
        </Typography>
      </div>
    </div>
  );
};
```

---

## Module 4: Chatbot Feature (Future Implementation)

**Purpose**: AI-powered job-candidate matching through conversational interface

### 4.1 Chat Interface Design

**Components**:
- **Chat Window**: Message history and input
- **Candidate Cards**: Search results displayed in chat
- **Job Description Upload**: File input for job requirements
- **Conversation Flow**: Guided matching process

**Chat Component Structure**:
```typescript
interface ChatbotProps {
  onCandidateSelect: (candidate: CandidateProfile) => void;
}

const Chatbot: React.FC<ChatbotProps> = ({ onCandidateSelect }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [jobDescription, setJobDescription] = useState<File | null>(null);
  
  const handleJobUpload = async (file: File) => {
    setJobDescription(file);
    
    // Add system message
    addMessage({
      type: 'system',
      content: `Job description uploaded: ${file.name}`,
      timestamp: new Date()
    });
    
    // Simulate AI processing
    setIsTyping(true);
    
    // TODO: Integrate with backend job analysis API
    setTimeout(() => {
      addMessage({
        type: 'assistant',
        content: 'I\'ve analyzed the job description. Let me search for suitable candidates...',
        timestamp: new Date()
      });
      
      // Trigger semantic search
      triggerCandidateSearch();
      setIsTyping(false);
    }, 2000);
  };
  
  const triggerCandidateSearch = async () => {
    // TODO: Extract key requirements from job description
    const searchQuery = 'Extract requirements from job description';
    
    try {
      const results = await searchCandidates(searchQuery, {
        confidence_threshold: 0.7,
        max_results: 10,
        include_relationships: true
      });
      
      // Display candidate cards in chat
      addMessage({
        type: 'candidates',
        content: 'Here are the most suitable candidates:',
        candidates: results,
        timestamp: new Date()
      });
      
    } catch (error) {
      addMessage({
        type: 'error',
        content: 'Failed to search for candidates. Please try again.',
        timestamp: new Date()
      });
    }
  };
  
  return (
    <div className="chatbot-container">
      <div className="chat-header">
        <Typography variant="h6">AI Recruitment Assistant</Typography>
        <Typography variant="caption">
          Upload a job description and I'll help you find the best candidates
        </Typography>
      </div>
      
      <div className="chat-messages">
        {messages.map((message, index) => (
          <ChatMessage key={index} message={message} onCandidateSelect={onCandidateSelect} />
        ))}
        
        {isTyping && (
          <div className="typing-indicator">
            <span>AI is thinking</span>
            <Dots />
          </div>
        )}
      </div>
      
      <div className="chat-input">
        <FileUpload
          accept=".pdf,.doc,.docx,.txt"
          onFileSelect={handleJobUpload}
          placeholder="Upload job description or type your requirements..."
        />
      </div>
    </div>
  );
};
```

### 4.2 Candidate Card Integration

**Chat Message Types**:
```typescript
interface ChatMessage {
  id: string;
  type: 'user' | 'assistant' | 'system' | 'candidates' | 'error';
  content: string;
  timestamp: Date;
  candidates?: SemanticSearchResult[];
  metadata?: any;
}

const ChatMessage: React.FC<{ message: ChatMessage; onCandidateSelect: (candidate: CandidateProfile) => void }> = ({ message, onCandidateSelect }) => {
  if (message.type === 'candidates') {
    return (
      <div className="message candidates-message">
        <Typography variant="body2">{message.content}</Typography>
        
        <div className="candidate-cards">
          {message.candidates?.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              onClick={() => onCandidateSelect(candidate)}
              compact
            />
          ))}
        </div>
      </div>
    );
  }
  
  // Regular message rendering
  return (
    <div className={`message ${message.type}-message`}>
      <Typography variant="body2">{message.content}</Typography>
      <Typography variant="caption" color="textSecondary">
        {message.timestamp.toLocaleTimeString()}
      </Typography>
    </div>
  );
};
```

---

## Implementation Guidelines

### 1. State Management

**Recommended Structure**:
```typescript
// Store slices
interface AppState {
  candidates: {
    list: CandidateProfile[];
    current: CandidateProfile | null;
    loading: boolean;
    pagination: PaginationInfo;
  };
  
  search: {
    results: SemanticSearchResult[];
    query: string;
    loading: boolean;
    filters: SearchFilters;
  };
  
  promptTemplates: {
    list: PromptTemplate[];
    active: PromptTemplate | null;
    loading: boolean;
  };
  
  bulkRegeneration: {
    activeJobs: JobStatus[];
    currentJob: JobStatus | null;
  };
}
```

### 2. Error Handling

**Global Error Boundary**:
```typescript
class GlobalErrorBoundary extends React.Component {
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to monitoring service
    console.error('Global error:', error, errorInfo);
    
    // Show user-friendly error message
    showNotification({
      type: 'error',
      message: 'Something went wrong. Please refresh the page.',
      duration: 0
    });
  }
}
```

**API Error Handling**:
```typescript
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000
});

apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.message || 'An error occurred';
    
    showNotification({
      type: 'error',
      message
    });
    
    return Promise.reject(error);
  }
);
```

### 3. Performance Optimization

**Lazy Loading**:
```typescript
const CandidateList = lazy(() => import('./CandidateList'));
const PromptTemplates = lazy(() => import('./PromptTemplates'));
const SemanticSearch = lazy(() => import('./SemanticSearch'));
const Chatbot = lazy(() => import('./Chatbot'));
```

**Debounced Search**:
```typescript
import { debounce } from 'lodash';

const debouncedSearch = useMemo(
  () => debounce((query: string) => {
    performSearch(query);
  }, 300),
  []
);
```

**Virtual Scrolling** (for large lists):
```typescript
import { FixedSizeList as List } from 'react-window';

const VirtualizedCandidateList: React.FC<{ candidates: CandidateProfile[] }> = ({ candidates }) => {
  const Row = ({ index, style }: { index: number; style: CSSProperties }) => (
    <div style={style}>
      <CandidateCard candidate={candidates[index]} />
    </div>
  );
  
  return (
    <List
      height={600}
      itemCount={candidates.length}
      itemSize={120}
      width="100%"
    >
      {Row}
    </List>
  );
};
```

### 4. Testing Strategy

**Unit Tests**:
- Component rendering and interactions
- API integration and error handling
- Form validation and submission
- State management and updates

**Integration Tests**:
- End-to-end user workflows
- API response handling
- File upload and processing
- Search functionality

**Performance Tests**:
- Large dataset rendering
- Search response times
- Memory usage optimization

---

## Development Phases

### Phase 1: Core Infrastructure
- [ ] Project setup and routing
- [ ] Basic candidate CRUD operations
- [ ] API integration layer
- [ ] Error handling and notifications

### Phase 2: Candidate Management
- [ ] Candidate list with pagination
- [ ] Resume upload and parsing
- [ ] Profile creation and editing
- [ ] Module-based CRUD operations

### Phase 3: AI Features
- [ ] Prompt template management
- [ ] AI summary generation
- [ ] Bulk regeneration system
- [ ] Semantic search implementation

### Phase 4: Advanced Features
- [ ] Search result optimization
- [ ] Chatbot interface
- [ ] Performance optimization
- [ ] User experience improvements

---

## Success Metrics

### User Experience
- **Profile Creation**: < 5 minutes from resume upload to completion
- **Search Response**: < 2 seconds for semantic search results
- **AI Processing**: < 30 seconds for individual profile finalization
- **Bulk Operations**: Progress tracking and cancellation support

### Technical Performance
- **Page Load**: < 3 seconds for candidate list
- **Search Accuracy**: > 85% relevance score for top results
- **Error Rate**: < 2% for API operations
- **Memory Usage**: < 100MB for large candidate lists

This comprehensive guide provides the foundation for building a professional, AI-powered talent management system that meets all the specified requirements while maintaining excellent user experience and performance standards. 