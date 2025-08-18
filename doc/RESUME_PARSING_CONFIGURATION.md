# Resume Parsing Configuration Guide

This document explains how to configure the enhanced resume parsing service that supports three different parsing methods.

## Overview

The resume parser now supports three parsing methods:

1. **spacy** - Traditional NER using spaCy and NLTK (default, lightweight)
2. **azure_di** - Azure Document Intelligence (cloud-based, good for complex layouts)
3. **langextract** - Google LangExtract with Azure OpenAI (AI-powered, most accurate)

## Environment Variables

### Primary Configuration

```bash
# Choose parsing method: 'spacy', 'azure_di', or 'langextract'
RESUME_PARSING_METHOD=spacy
```

### Method-Specific Configuration

#### 1. SpaCy Configuration (Default)
```bash
RESUME_PARSING_METHOD=spacy
```

**Requirements:**
- Install spaCy model: `python -m spacy download en_core_web_sm`
- No additional environment variables required
- Lightest option, works offline

#### 2. Azure Document Intelligence
```bash
RESUME_PARSING_METHOD=azure_di
AZURE_DI_ENDPOINT=https://your-document-intelligence.cognitiveservices.azure.com/
AZURE_DI_API_KEY=your_azure_di_api_key_here
```

**Requirements:**
- Azure Document Intelligence resource
- Good for complex PDF layouts
- Handles tables and structured documents well

#### 3. LangExtract with Azure OpenAI Fallback
```bash
RESUME_PARSING_METHOD=langextract
# Option 1: Use LangExtract with Gemini (if you have Google API key)
LANGEXTRACT_API_KEY=your_google_gemini_api_key_here

# Option 2: Use Azure OpenAI fallback (uses your existing credentials)
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-02-01
```

**Requirements:**
- Either Google Gemini API key OR Azure OpenAI resource
- If both are available, will try Gemini first, then fall back to Azure OpenAI
- If only Azure OpenAI is available, will use direct Azure OpenAI extraction
- Most accurate extraction using AI understanding

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install SpaCy Model (if using spacy method)

```bash
python -m spacy download en_core_web_sm
```

### 3. Set Environment Variables

Create a `.env` file in your project root with the appropriate variables for your chosen method.

### 4. Azure Resource Setup

#### For Azure Document Intelligence:
1. Create an Azure Document Intelligence resource in the Azure portal
2. Copy the endpoint and API key to your environment variables

#### For Azure OpenAI (LangExtract):
1. Create an Azure OpenAI resource in the Azure portal
2. Deploy a GPT-4 or GPT-4 Turbo model
3. Copy the endpoint, API key, and deployment name to your environment variables

## Output Format

All three parsing methods return identical JSON structure:

```json
{
  "first_name": "string",
  "last_name": "string", 
  "email": "string",
  "location": "string",
  "phone_number": "string",
  "personal_summary": "string",
  "availability_weeks": null,
  "preferred_work_types": null,
  "right_to_work": null,
  "salary_expectation": null,
  "classification_of_interest": null,
  "sub_classification_of_interest": null,
  "is_active": true,
  "career_history": [
    {
      "job_title": "string",
      "company_name": "string", 
      "start_date": "string",
      "end_date": "string",
      "description": "string"
    }
  ],
  "skills": [
    {
      "skills": "string",
      "career_history_id": null
    }
  ],
  "education": [
    {
      "school": "string",
      "degree": "string",
      "field_of_study": "string",
      "start_date": "string",
      "end_date": "string", 
      "grade": "string",
      "description": "string"
    }
  ],
  "licenses_certifications": [
    {
      "name": "string",
      "issuing_organization": "string",
      "issue_date": "string",
      "expiration_date": "string",
      "credential_id": "string",
      "credential_url": "string"
    }
  ],
  "languages": [
    {
      "language": "string",
      "proficiency_level": "string"
    }
  ],
  "resumes": []
}
```

## Choosing the Right Method

### Use **spacy** when:
- You need a lightweight, offline solution
- Processing simple text-based resumes
- Cost is a primary concern
- You have high volume, low-complexity parsing needs

### Use **azure_di** when:
- Dealing with complex PDF layouts
- Documents have tables, columns, or complex formatting
- You need good OCR capabilities
- You want a balance between accuracy and cost

### Use **langextract** when:
- You need the highest accuracy
- Dealing with varied resume formats
- You want AI understanding of context and relationships
- You have access to Azure OpenAI
- Cost is less of a concern compared to accuracy

## Fallback Behavior

The system includes automatic fallback:
1. If the primary method fails, it attempts to fall back to spacy
2. If all parsing fails, basic regex extraction is used
3. Logs provide detailed information about which method was used

## Migration from Old System

The old `USE_AZURE_DOCUMENT_INTELLIGENCE` environment variable is no longer used. 

**Old configuration:**
```bash
USE_AZURE_DOCUMENT_INTELLIGENCE=true
```

**New configuration:**
```bash
RESUME_PARSING_METHOD=azure_di
```

## Troubleshooting

### Common Issues:

1. **LangExtract fails**: Ensure Azure OpenAI endpoint and API key are correct
2. **Azure DI fails**: Check that the Document Intelligence resource is active
3. **SpaCy fails**: Ensure the en_core_web_sm model is installed

### Debugging:

Set logging level to DEBUG to see detailed parsing information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

| Method | Speed | Accuracy | Cost | Offline |
|--------|-------|----------|------|---------|
| spacy | Fast | Good | Free | Yes |
| azure_di | Medium | Very Good | Low | No |
| langextract | Slow | Excellent | High | No |

## Cost Estimates

- **spacy**: Free (computational cost only)
- **azure_di**: ~$0.001-0.01 per page
- **langextract**: ~$0.01-0.10 per resume (depending on model and length)

*Costs are approximate and depend on specific Azure pricing and Azure OpenAI pricing.* 