# Resume Parsing Setup Guide

## Overview

This feature adds intelligent resume parsing capabilities to the AI Recruitment Backend using Named Entity Recognition (NER). It automatically extracts candidate information from PDF resumes and returns structured data that can be used to prefill candidate creation forms.

**Based on methodology from**: [Performing Resumé Analysis using NER with Cosine Similarity](https://medium.com/pythons-gurus/performing-resum%C3%A9-analysis-using-ner-with-cosine-similarity-8eb99879cda4)

## Features

✅ **PDF Text Extraction** - Extracts readable text from PDF resumes  
✅ **Named Entity Recognition** - Identifies people, organizations, locations, dates  
✅ **Smart Information Extraction**:
- Personal information (name, email, phone, location)
- Professional/Executive summary extraction
- Work experience (job titles, companies, dates)
- Education (schools, degrees, graduation years)
- Skills (technical and professional skills)
- Languages and proficiency levels
- Certifications and licenses

✅ **Intelligent Preprocessing** - Text cleaning and normalization  
✅ **Completeness Scoring** - Quality assessment of extracted data  
✅ **Structured Output** - Returns data in the same format as existing candidate API

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

The following packages will be installed:
- `PyPDF2==3.0.1` - PDF text extraction
- `spacy==3.7.2` - Natural Language Processing and NER
- `nltk==3.8.1` - Text preprocessing utilities
- `scikit-learn==1.3.2` - Text analysis algorithms
- `python-multipart==0.0.6` - File upload handling

### 2. Install spaCy English Model

```bash
python -m spacy download en_core_web_sm
```

This downloads the English language model required for Named Entity Recognition.

### 3. Verify Installation

Run the test script to verify everything is working:

```bash
python test_resume_parser.py
```

Expected output:
```
Resume Parser Dependency Test
========================================
Testing imports...
✓ PyPDF2 imported successfully
✓ spaCy imported successfully
✓ NLTK imported successfully
✓ scikit-learn imported successfully

Testing spaCy English model...
✓ spaCy English model loaded successfully
✓ NER test found entities: [('John Doe', 'PERSON'), ('Microsoft', 'ORG'), ('Seattle', 'GPE')]

Testing NLTK data...
✓ NLTK stopwords available
✓ NLTK WordNet lemmatizer available
✓ NLTK punkt tokenizer available

Testing resume parser service...
✓ ResumeParser initialized successfully
✓ Text cleaning works: 'test resume special character'
✓ Contact extraction works: {'email': 'john.doe@example.com', 'phone_number': '5551234567'}

========================================
🎉 All tests passed! Resume parsing is ready to use.
```

## API Usage

### 1. Parse Resume Endpoint

**POST** `/candidates/parse-resume`

Upload a PDF resume and get structured candidate data.

#### Request
- **Content-Type**: `multipart/form-data`
- **File Parameter**: `resume_file` (PDF file, max 10MB)

#### Example using curl:
```bash
curl -X POST \
  http://localhost:5000/candidates/parse-resume \
  -H "Content-Type: multipart/form-data" \
  -F "resume_file=@john_doe_resume.pdf"
```

#### Response Format:
```json
{
  "success": true,
  "message": "Resume parsed successfully. Extracted 15 entities with 87.5% completeness.",
  "candidate_data": {
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com",
    "phone_number": "5551234567",
    "location": "San Francisco, CA",
    "personal_summary": "Experienced software engineer with 5+ years...",
    "career_history": [
      {
        "job_title": "Senior Software Engineer",
        "company_name": "Tech Corp",
        "start_date": null,
        "end_date": null,
        "description": null
      }
    ],
    "skills": [
      {"skills": "Python", "career_history_id": null},
      {"skills": "React", "career_history_id": null},
      {"skills": "Docker", "career_history_id": null}
    ],
    "education": [
      {
        "school": "University of California",
        "degree": "Bachelor of Science in Computer Science",
        "field_of_study": null,
        "start_date": null,
        "end_date": "2019",
        "grade": null,
        "description": null
      }
    ],
    "languages": [
      {"language": "English", "proficiency_level": "Native"},
      {"language": "Spanish", "proficiency_level": "Intermediate"}
    ],
    "licenses_certifications": [
      {
        "name": "Aws Certified",
        "issuing_organization": null,
        "issue_date": null,
        "expiration_date": null,
        "credential_id": null,
        "credential_url": null
      }
    ],
         "resumes": []
  },
  "parsing_stats": {
    "file_size_bytes": 245760,
    "file_name": "john_doe_resume.pdf",
    "entities_extracted": {
      "career_history_count": 3,
      "skills_count": 8,
      "education_count": 2,
      "languages_count": 2,
      "certifications_count": 1
    },
    "contact_info_found": {
      "email": true,
      "phone": true,
      "location": true
    },
    "name_extracted": {
      "first_name": true,
      "last_name": true
    },
    "completeness_score": 87.5
  }
}
```

### 2. Create Candidate from Parsed Data

**POST** `/candidates/create-from-parsed-data`

Create a complete candidate profile directly from parsed resume data (JSON only).

#### Request
- **Content-Type**: `application/json`
- **Body**: JSON object with candidate data (includes optional base64 PDF data)

#### Example using curl:
```bash
curl -X POST \
  http://localhost:5000/candidates/create-from-parsed-data \
  -H "Content-Type: application/json" \
  -d @example_parsed_resume_data.json
```

### 3. Create Candidate with PDF File

**POST** `/candidates/create-with-pdf`

Create a complete candidate profile from parsed resume data + original PDF file.

#### Request
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `pdf_file`: PDF file (required)
  - `candidate_data`: JSON string with candidate data (required)

#### Example using curl:
```bash
curl -X POST \
  http://localhost:5000/candidates/create-with-pdf \
  -F "pdf_file=@resume.pdf" \
  -F "candidate_data={\"first_name\":\"John\",\"last_name\":\"Doe\",\"email\":\"john@example.com\"}"
```

### 4. Resume Management APIs

#### Create Resume with Base64 Data
**POST** `/resumes/`
- **Content-Type**: `application/json`
- **Body**: JSON with base64 encoded PDF data

```json
{
  "candidate_id": 123,
  "file_name": "resume.pdf",
  "file_size": 1024000,
  "content_type": "application/pdf",
  "pdf_data_base64": "JVBERi0xLjQK..."
}
```

#### Upload Resume File
**POST** `/resumes/upload`
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `pdf_file`: PDF file (required)
  - `candidate_id`: Candidate ID (required)

#### Download Resume PDF
**GET** `/resumes/{resume_id}/download`

Download the stored PDF file for a resume.

#### Response
- **Content-Type**: `application/pdf`
- **Headers**: `Content-Disposition: attachment; filename="resume.pdf"`

#### Get Resume Info
**GET** `/resumes/{resume_id}/info`

Get resume metadata without downloading the file.

#### List All Resumes
**GET** `/resumes/`

List all resume records with pagination and filtering options.

#### Response Format:
```json
{
  "success": true,
  "message": "Candidate profile created successfully with 26 total records. Success rate: 100.0%",
  "candidate": {
    "id": 123,
    "first_name": "John",
    "last_name": "Doe",
    // ... complete candidate data with all relationships
    "career_history": [...],
    "skills": [...],
    "education": [...],
    "languages": [...],
    "licenses_certifications": [...]
  },
  "creation_stats": {
    "candidate_id": 123,
    "records_created": {
      "career_history": 3,
      "skills": 10,
      "education": 2,
      "licenses_certifications": 2,
      "languages": 3,
      "resumes": 0
    },
    "validation_errors": [],
    "success_rate": 100.0
  }
}
```

### 5. Get Parser Information

**GET** `/candidates/parse-resume/supported-formats`

Get information about supported formats and parsing capabilities.

## Frontend Integration

### Example JavaScript/React Usage

```javascript
const parseResume = async (file) => {
  const formData = new FormData();
  formData.append('resume_file', file);
  
  try {
    const response = await fetch('/candidates/parse-resume', {
      method: 'POST',
      body: formData
    });
    
    const result = await response.json();
    
    if (result.success) {
      // Use result.candidate_data to prefill your form
      setFormData(result.candidate_data);
      
      // Show parsing statistics
      console.log(`Parsed with ${result.parsing_stats.completeness_score}% completeness`);
    } else {
      console.error('Parsing failed:', result.message);
    }
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

### Form Pre-filling Example

```javascript
const prefillCandidateForm = (candidateData) => {
  // Basic information
  setFirstName(candidateData.first_name || '');
  setLastName(candidateData.last_name || '');
  setEmail(candidateData.email || '');
  setPhone(candidateData.phone_number || '');
  setLocation(candidateData.location || '');
  setSummary(candidateData.personal_summary || '');
  
  // Related data
  setCareerHistory(candidateData.career_history || []);
  setSkills(candidateData.skills || []);
  setEducation(candidateData.education || []);
  setLanguages(candidateData.languages || []);
  setCertifications(candidateData.licenses_certifications || []);
};
```

### Direct Creation Example

```javascript
const createCandidateFromParsedData = async (parsedData) => {
  try {
    const response = await fetch('/candidates/create-from-parsed-data', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(parsedData.candidate_data)
    });
    
    const result = await response.json();
    
    if (result.success) {
      console.log(`Created candidate ID: ${result.candidate.id}`);
      console.log(`Success rate: ${result.creation_stats.success_rate}%`);
      
      // Redirect to candidate profile or show success message
      window.location.href = `/candidates/${result.candidate.id}`;
    } else {
      console.error('Creation failed:', result.message);
    }
  } catch (error) {
    console.error('Request failed:', error);
  }
};
```

### Complete Workflow Example

```javascript
// Step 1: Parse resume
const handleResumeUpload = async (file) => {
  const formData = new FormData();
  formData.append('resume_file', file);
  
  try {
    // Parse the resume
    const parseResponse = await fetch('/candidates/parse-resume', {
      method: 'POST',
      body: formData
    });
    
    const parseResult = await parseResponse.json();
    
    if (parseResult.success) {
      // Option A: Prefill form for user review
      if (userWantsToReview) {
        prefillCandidateForm(parseResult.candidate_data);
        showReviewForm();
      }
      // Option B: Create candidate directly
      else {
        await createCandidateFromParsedData(parseResult);
      }
    }
  } catch (error) {
    console.error('Resume processing failed:', error);
  }
};
```

## Parsing Accuracy Tips

### For Best Results:
1. **Use standard resume formats** - Traditional chronological or functional layouts work best
2. **Include clear section headers** - "Experience", "Education", "Skills", "Certifications"
3. **Ensure text is selectable** - Avoid scanned images or graphics-heavy PDFs
4. **Use common terminology** - Standard job titles and company names are better recognized
5. **Include complete contact information** - Full name, email, phone number
6. **List skills explicitly** - Technical skills in dedicated sections

### Supported Information Types:
- ✅ **Names**: First and last names from PERSON entities
- ✅ **Contact**: Email addresses and phone numbers (various formats)
- ✅ **Locations**: Cities, states, countries from GPE entities
- ✅ **Companies**: Organization names from ORG entities
- ✅ **Summary**: Professional/Executive summary, career objective, profile sections
- ✅ **Skills**: 50+ predefined technical skills (Python, JavaScript, AWS, etc.)
- ✅ **Education**: Universities, colleges, degrees, graduation years
- ✅ **Languages**: 25+ common languages with proficiency levels
- ✅ **Certifications**: AWS, Azure, Microsoft, Oracle, and other common certs

## Troubleshooting

### Common Issues:

#### 1. "spaCy model not found"
```bash
python -m spacy download en_core_web_sm
```

#### 2. "NLTK data not found"
The system will automatically download required NLTK data on first use.

#### 3. "No text extracted from PDF"
- Ensure PDF contains selectable text (not just images)
- Try converting scanned PDFs to text-searchable PDFs first
- Check if PDF is password protected

#### 4. "Poor parsing results"
- Use standard resume formats
- Ensure clear section headers
- Include explicit skill listings
- Verify contact information is clearly formatted

#### 5. File Upload Issues
- Check file size (max 10MB)
- Ensure file is actually a PDF
- Verify file is not corrupted

### Debug Mode:
To see detailed parsing information, check the application logs when processing resumes.

## Technical Architecture

### Components:
1. **ResumeParser** (`services/resume_parser.py`) - Main parsing engine
2. **PDF Extraction** - PyPDF2 for text extraction
3. **NER Engine** - spaCy with custom entity ruler for skills recognition
4. **Text Preprocessing** - NLTK for cleaning and normalization
5. **API Endpoint** - Flask-RESTX endpoint with file upload validation

### Processing Pipeline:
1. **File Validation** - Size, format, content checks
2. **Text Extraction** - PDF to plain text conversion
3. **Text Cleaning** - Remove noise, normalize formatting
4. **Entity Recognition** - Extract people, organizations, locations
5. **Information Extraction** - Parse contact info, skills, experience
6. **Data Structuring** - Format into candidate API schema
7. **Quality Assessment** - Calculate completeness score

## Performance Considerations

- **File Size Limit**: 10MB maximum
- **Processing Time**: 2-5 seconds for typical resumes
- **Memory Usage**: ~50-100MB per parsing operation
- **Concurrent Requests**: Can handle multiple simultaneous uploads
- **Model Loading**: spaCy model loaded once at startup

## Security Notes

- Files are processed in memory only (not saved to disk)
- No sensitive data is logged
- File type validation prevents malicious uploads
- Size limits prevent resource exhaustion attacks

---

## Need Help?

If you encounter issues:
1. Run `python test_resume_parser.py` to verify setup
2. Check application logs for detailed error messages
3. Ensure all dependencies are correctly installed
4. Verify the spaCy English model is available 