import re
import spacy
import PyPDF2
import nltk
import os
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import logging
from dotenv import load_dotenv

# Azure Document Intelligence imports
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest, DocumentAnalysisFeature
    from azure.core.credentials import AzureKeyCredential
    AZURE_DI_AVAILABLE = True
except ImportError:
    AZURE_DI_AVAILABLE = False

# LangExtract imports
try:
    import langextract as lx
    LANGEXTRACT_AVAILABLE = True
except ImportError:
    LANGEXTRACT_AVAILABLE = False

# Azure OpenAI imports for LangExtract
try:
    from openai import AzureOpenAI
    AZURE_OPENAI_AVAILABLE = True
except ImportError:
    AZURE_OPENAI_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Load environment variables
load_dotenv()

class ResumeParser:
    """
    Enhanced resume parsing service supporting multiple parsing methods:
    - spacy: Traditional NER with spaCy and NLTK
    - azure_di: Azure Document Intelligence
    - langextract: Google LangExtract with Gemini API
    """
    
    def __init__(self):
        """Initialize the resume parser with the selected parsing method"""
        # Determine parsing method from environment variable
        self.parsing_method = os.getenv('RESUME_PARSING_METHOD', 'spacy').lower()
        
        if self.parsing_method not in ['spacy', 'azure_di', 'langextract']:
            logger.warning(f"Invalid parsing method '{self.parsing_method}', defaulting to 'spacy'")
            self.parsing_method = 'spacy'
        
        logger.info(f"Initializing resume parser with method: {self.parsing_method}")
        
        # Initialize based on selected method
        if self.parsing_method == 'langextract':
            self._initialize_langextract()
        elif self.parsing_method == 'azure_di':
            self._initialize_azure_di_client()
        else:  # spacy
            self._initialize_spacy()
            
        # Always initialize NLTK for text cleaning
        self._initialize_nltk_data()
        self.lemmatizer = WordNetLemmatizer()
        
    def _initialize_langextract(self):
        """Initialize LangExtract with fallback to Azure OpenAI"""
        if not LANGEXTRACT_AVAILABLE:
            raise ImportError("LangExtract not available. Please install: pip install langextract")
            
        if not AZURE_OPENAI_AVAILABLE:
            raise ImportError("Azure OpenAI not available. Please install: pip install openai")
            
        # Check for Azure OpenAI environment variables (for fallback)
        # Use the same environment variables as the existing AI service
        required_vars = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY', 'AZURE_OPENAI_DEPLOYMENT_NAME']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required Azure OpenAI environment variables: {', '.join(missing_vars)}. Please set up Azure OpenAI resource.")
            
        try:
            # Store Azure OpenAI configuration for fallback
            # Use the same environment variables as the existing AI service
            self.azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
            self.azure_openai_api_key = os.getenv('AZURE_OPENAI_API_KEY')
            self.azure_openai_model = os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
            self.azure_openai_api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
            
            # Create Azure OpenAI client for fallback
            self.azure_openai_client = AzureOpenAI(
                azure_endpoint=self.azure_openai_endpoint,
                api_key=self.azure_openai_api_key,
                api_version=self.azure_openai_api_version
            )
            
            # Check if LANGEXTRACT_API_KEY is available for Gemini
            langextract_api_key = os.getenv('LANGEXTRACT_API_KEY')
            if langextract_api_key:
                logger.info("LangExtract initialized with Gemini API key")
                logger.info("Will use Gemini model with Azure OpenAI fallback")
            else:
                logger.info("LangExtract initialized without Gemini API key")
                logger.info("Will use Azure OpenAI fallback for all extractions")
                logger.info(f"Azure OpenAI deployment: {self.azure_openai_model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangExtract: {str(e)}")
            raise
            
    def _initialize_azure_di_client(self):
        """Initialize Azure Document Intelligence client"""
        if not AZURE_DI_AVAILABLE:
            raise ImportError("Azure Document Intelligence SDK not available. Please install: pip install azure-ai-documentintelligence")
            
        # Check for required environment variables
        required_vars = ['AZURE_DI_ENDPOINT', 'AZURE_DI_API_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            raise ValueError(f"Missing required Azure Document Intelligence environment variables: {', '.join(missing_vars)}")
            
        try:
            endpoint = os.getenv('AZURE_DI_ENDPOINT')
            api_key = os.getenv('AZURE_DI_API_KEY')
            
            self.azure_di_client = DocumentIntelligenceClient(
                endpoint=endpoint,
                credential=AzureKeyCredential(api_key)
            )
            logger.info("Azure Document Intelligence client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Azure Document Intelligence client: {str(e)}")
            raise
            
    def _initialize_spacy(self):
        """Initialize spaCy for NER"""
        self._initialize_nltk_data()
        self.nlp = self._load_spacy_model()
        self._setup_entity_ruler()
            
    def _initialize_nltk_data(self):
        """Download required NLTK data"""
        try:
            nltk.data.find('tokenizers/punkt')
        except LookupError:
            nltk.download('punkt')
            
        try:
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('stopwords')
            
        try:
            nltk.data.find('corpora/wordnet')
        except LookupError:
            nltk.download('wordnet')
            
    def _load_spacy_model(self):
        """Load spaCy model for NER"""
        try:
            nlp = spacy.load('en_core_web_sm')
            logger.info("SpaCy model loaded successfully")
            return nlp
        except OSError:
            logger.error("SpaCy model 'en_core_web_sm' not found. Please install it using: python -m spacy download en_core_web_sm")
            raise
            
    def _setup_entity_ruler(self):
        """Setup entity ruler for custom skill recognition"""
        try:
            # Add entity ruler pipeline
            ruler = self.nlp.add_pipe("entity_ruler", before="ner")
            
            # Define patterns for common skills and technologies
            skill_patterns = [
                # Programming Languages
                {"label": "SKILL", "pattern": [{"LOWER": "python"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "javascript"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "java"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "react"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "node.js"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "nodejs"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "sql"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "html"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "css"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "angular"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "vue"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "flutter"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "django"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "flask"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "spring"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "laravel"}]},
                
                # Databases
                {"label": "SKILL", "pattern": [{"LOWER": "mysql"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "postgresql"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "mongodb"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "redis"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "oracle"}]},
                
                # Cloud & DevOps
                {"label": "SKILL", "pattern": [{"LOWER": "aws"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "azure"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "docker"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "kubernetes"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "jenkins"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "terraform"}]},
                
                # Data Science & AI
                {"label": "SKILL", "pattern": [{"LOWER": "machine"}, {"LOWER": "learning"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "tensorflow"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "pytorch"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "pandas"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "numpy"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "scikit-learn"}]},
                
                # Tools & Methodologies
                {"label": "SKILL", "pattern": [{"LOWER": "git"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "agile"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "scrum"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "jira"}]},
                {"label": "SKILL", "pattern": [{"LOWER": "confluence"}]},
            ]
            
            ruler.add_patterns(skill_patterns)
            logger.info("Entity ruler configured with skill patterns")
            
        except Exception as e:
            logger.error(f"Error setting up entity ruler: {str(e)}")

    def extract_text_from_pdf(self, pdf_file) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_file: File object or BytesIO containing PDF data
            
        Returns:
            str: Extracted text from PDF
        """
        try:
            text = ''
            
            # If it's a file upload from Flask
            if hasattr(pdf_file, 'read'):
                pdf_file.seek(0)  # Reset file pointer
                pdf_data = BytesIO(pdf_file.read())
            else:
                pdf_data = pdf_file
                
            reader = PyPDF2.PdfReader(pdf_data)
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + '\n'
                    
            if not text.strip():
                raise ValueError("No text could be extracted from the PDF")
                
            logger.info(f"Successfully extracted {len(text)} characters from PDF")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def clean_text(self, text: str) -> str:
        """
        Clean and preprocess text data
        
        Args:
            text: Raw text to clean
            
        Returns:
            str: Cleaned text
        """
        try:
            # Remove hyperlinks, HTML tags, and special characters
            text = re.sub(r'https?://\S+|www\.\S+', '', text)
            text = re.sub(r'<.*?>', '', text)
            text = re.sub(r'[^\w\s\n.@-]', ' ', text)  # Keep dots, @ for emails, - for dates
            
            # Convert to lowercase and tokenize
            text = text.lower()
            words = word_tokenize(text)
            
            # Lemmatize words
            lemmatized_words = [self.lemmatizer.lemmatize(word) for word in words]
            
            # Remove English stopwords but keep important words for NER
            stop_words = set(stopwords.words('english'))
            # Don't remove these important words for resume parsing
            keep_words = {'university', 'college', 'school', 'degree', 'bachelor', 'master', 'phd', 'diploma',
                         'experience', 'work', 'job', 'company', 'manager', 'developer', 'engineer',
                         'certification', 'license', 'skill', 'language', 'fluent', 'native'}
            
            filtered_words = [word for word in lemmatized_words 
                            if word not in stop_words or word in keep_words]
            
            return ' '.join(filtered_words)
            
        except Exception as e:
            logger.error(f"Error cleaning text: {str(e)}")
            return text  # Return original text if cleaning fails

    def extract_contact_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract contact information from text"""
        contact_info = {
            'email': None,
            'phone_number': None
        }
        
        # Extract email
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            contact_info['email'] = emails[0]
            
        # Extract phone number
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{3}-\d{3}-\d{4}',
            r'\d{10,}'
        ]
        
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                # Clean and format phone number
                phone = re.sub(r'[^\d+]', '', phones[0])
                if len(phone) >= 10:
                    contact_info['phone_number'] = phone
                    break
                    
        return contact_info
        
    def extract_education(self, text: str) -> List[Dict[str, Any]]:
        """Extract education information from text"""
        education_list = []
        
        # Common education keywords and patterns
        education_patterns = [
            r'(bachelor|master|phd|doctorate|diploma|certificate|degree)[\s\w]*in[\s\w]+',
            r'(university|college|institute|school)[\s\w]{1,50}',
            r'(b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?|ph\.?d\.?)[\s\w]*',
        ]
        
        # Extract years (graduation years)
        year_pattern = r'\b(19|20)\d{2}\b'
        years = re.findall(year_pattern, text)
        
        doc = self.nlp(text)
        
        education_keywords = []
        schools = []
        degrees = []
        
        # Extract organizations that might be schools
        for ent in doc.ents:
            if ent.label_ == "ORG":
                # Check if it's likely an educational institution
                if any(keyword in ent.text.lower() for keyword in 
                      ['university', 'college', 'institute', 'school', 'academy']):
                    schools.append(ent.text)
                    
        # Extract degree information using patterns
        for pattern in education_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                education_keywords.append(match.group())
                
        # Try to construct education records
        if schools or education_keywords:
            education_record = {
                'candidate_id': 0,  # Will be set when saving to database
                'school': schools[0] if schools else None,
                'degree': education_keywords[0] if education_keywords else None,
                'field_of_study': None,  # Could be enhanced with more sophisticated parsing
                'start_date': None,
                'end_date': years[-1] if years else None,  # Assume most recent year is graduation
                'grade': None,
                'description': None,
                'is_active': True
            }
            education_list.append(education_record)
            
        return education_list
        
    def extract_work_experience(self, text: str) -> List[Dict[str, Any]]:
        """Extract work experience from text"""
        experience_list = []
        
        doc = self.nlp(text)
        
        # Extract organizations (potential employers)
        companies = []
        for ent in doc.ents:
            if ent.label_ == "ORG":
                companies.append(ent.text)
                
        # Extract dates
        dates = []
        for ent in doc.ents:
            if ent.label_ == "DATE":
                dates.append(ent.text)
                
        # Job title patterns
        job_title_patterns = [
            r'(senior|junior|lead|principal)?\s*(software|web|mobile|data|system)?\s*(engineer|developer|analyst|manager|designer|architect|scientist)',
            r'(project|product|marketing|sales|operations|hr|finance)\s*manager',
            r'(ceo|cto|cfo|vp|director|coordinator|specialist|consultant)',
        ]
        
        job_titles = []
        for pattern in job_title_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                job_titles.append(match.group())
                
        # Create work experience records in the required format
        if companies or job_titles:
            for i, company in enumerate(companies[:3]):  # Limit to top 3 companies
                experience_record = {
                    'candidate_id': 0,  # Will be set when saving to database
                    'job_title': job_titles[i] if i < len(job_titles) else None,
                    'company_name': company,
                    'start_date': None,  # Could be enhanced with date parsing
                    'end_date': None,
                    'description': None,
                    'is_active': True
                }
                experience_list.append(experience_record)
                
        return experience_list
        
    def extract_skills(self, text: str) -> List[Dict[str, Any]]:
        """Extract skills using NER"""
        skills_list = []
        
        doc = self.nlp(text)
        
        # Extract skills identified by entity ruler
        extracted_skills = set()
        for ent in doc.ents:
            if ent.label_ == "SKILL":
                extracted_skills.add(ent.text.lower())
                
        # Convert to list format expected by API
        for skill in extracted_skills:
            skills_list.append({
                'candidate_id': 0,  # Will be set when saving to database
                'career_history_id': 0,  # Will be set when linking to specific job
                'skills': skill.title(),
                'is_active': True
            })
            
        return skills_list
        
    def extract_languages(self, text: str) -> List[Dict[str, Any]]:
        """Extract language information from text"""
        languages_list = []
        
        # Common languages
        language_keywords = [
            'english', 'spanish', 'french', 'german', 'italian', 'portuguese', 'chinese',
            'japanese', 'korean', 'arabic', 'hindi', 'russian', 'dutch', 'swedish',
            'norwegian', 'danish', 'finnish', 'polish', 'czech', 'hungarian',
            'mandarin', 'cantonese', 'tamil', 'bengali', 'urdu', 'thai', 'vietnamese'
        ]
        
        # Proficiency levels
        proficiency_keywords = ['native', 'fluent', 'advanced', 'intermediate', 'basic', 'beginner']
        
        doc = self.nlp(text)
        
        # Look for language mentions
        text_lower = text.lower()
        for language in language_keywords:
            if language in text_lower:
                # Try to find proficiency level near the language mention
                proficiency = 'Intermediate'  # Default
                for prof in proficiency_keywords:
                    if prof in text_lower:
                        proficiency = prof.title()
                        break
                        
                languages_list.append({
                    'candidate_id': 0,  # Will be set when saving to database
                    'language': language.title(),
                    'proficiency_level': proficiency,
                    'is_active': True
                })
                
        return languages_list
        
    def extract_certifications(self, text: str) -> List[Dict[str, Any]]:
        """Extract certifications and licenses from text"""
        certifications_list = []
        
        # Common certification patterns
        cert_patterns = [
            r'(aws|azure|google cloud|gcp)\s+(certified|certification)',
            r'(cissp|cisa|cism|pmp|scrum master|product owner)',
            r'(microsoft|oracle|cisco|comptia|linux)\s+certified',
            r'(cpa|cfa|frm|caia|phr|shrm)',
        ]
        
        # Extract certification mentions
        for pattern in cert_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                certifications_list.append({
                    'candidate_id': 0,  # Will be set when saving to database
                    'name': match.group().title(),
                    'issuing_organization': None,
                    'issue_date': None,
                    'expiration_date': None,
                    'credential_id': None,
                    'credential_url': None,
                    'is_active': True
                })
                
        return certifications_list
        
    def _analyze_document_with_azure_di(self, pdf_file) -> Dict[str, Any]:
        """
        Analyze document using Azure Document Intelligence with query fields for resume parsing
        
        Args:
            pdf_file: PDF file object
            
        Returns:
            Dict containing analyzed document data
        """
        try:
            # Prepare the document for Azure DI
            if hasattr(pdf_file, 'read'):
                pdf_file.seek(0)
                document_content = pdf_file.read()
            else:
                document_content = pdf_file
                
            # Create AnalyzeDocumentRequest with the document content
            analyze_request = AnalyzeDocumentRequest(bytes_source=document_content)
            
            # Define focused query fields for resume parsing (essential fields only)
            resume_query_fields = [
                "Summary",
                "Name", 
                "Phone", 
                "Email", 
                "Education", 
                "ProfessionalExperienceRole", 
                "ProfessionalExperienceDescription",
                "Skills", 
                "LicensesCertifications", 
                "Languages"
            ]
            
            # Try different models with query fields support
            # prebuilt-layout supports query fields and provides the best structure
            models_to_try = [
                ("prebuilt-layout", "layout analysis with query fields"),
                ("prebuilt-document", "general document analysis with query fields")
            ]
            
            last_error = None
            for model_name, description in models_to_try:
                try:
                    logger.info(f"Trying Azure DI model: {model_name} ({description})")
                    logger.info(f"Using {len(resume_query_fields)} query fields for resume parsing")
                    
                    # Use query fields feature for better extraction
                    poller = self.azure_di_client.begin_analyze_document(
                        model_name,
                        analyze_request,
                        features=[DocumentAnalysisFeature.QUERY_FIELDS],
                        query_fields=resume_query_fields
                    )
                    
                    result = poller.result()
                    logger.info(f"Azure Document Intelligence analysis completed using {model_name} with query fields")
                    
                    # Add metadata about which model was used
                    if hasattr(result, '__dict__'):
                        result._used_model = model_name
                        result._used_query_fields = True
                    
                    return result
                    
                except Exception as model_error:
                    last_error = model_error
                    if "404" in str(model_error):
                        logger.warning(f"Model {model_name} not available: {model_error}")
                        continue
                    else:
                        logger.error(f"Error with model {model_name}: {model_error}")
                        # If query fields fail, try without them as fallback
                        try:
                            logger.info(f"Retrying {model_name} without query fields as fallback")
                            poller = self.azure_di_client.begin_analyze_document(
                                model_name,
                                analyze_request
                            )
                            result = poller.result()
                            logger.info(f"Azure Document Intelligence analysis completed using {model_name} (fallback mode)")
                            
                            if hasattr(result, '__dict__'):
                                result._used_model = model_name
                                result._used_query_fields = False
                            
                            return result
                            
                        except Exception as fallback_error:
                            logger.error(f"Fallback also failed for {model_name}: {fallback_error}")
                            continue
            
            # If we get here, all models failed
            raise ValueError(f"All Azure DI models failed. Last error: {last_error}")
            
        except Exception as e:
            logger.error(f"Error analyzing document with Azure DI: {str(e)}")
            raise ValueError(f"Failed to analyze document with Azure DI: {str(e)}")
    
    def _extract_contact_info_from_azure_di(self, result) -> Dict[str, Optional[str]]:
        """Extract contact information from Azure DI result"""
        contact_info = {
            'email': None,
            'phone_number': None
        }
        
        # Try to extract from key-value pairs first if available
        if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
            for kv_pair in result.key_value_pairs:
                key = kv_pair.key.content.lower() if kv_pair.key else ''
                value = kv_pair.value.content if kv_pair.value else ''
                
                if any(keyword in key for keyword in ['email', 'e-mail', 'mail']):
                    contact_info['email'] = value
                elif any(keyword in key for keyword in ['phone', 'mobile', 'tel', 'cell']):
                    contact_info['phone_number'] = value
        
        # Fallback to content extraction if key-value pairs don't work
        if hasattr(result, 'content') and (not contact_info['email'] or not contact_info['phone_number']):
            content = result.content
            
            # Extract email using regex on content
            if not contact_info['email']:
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                emails = re.findall(email_pattern, content)
                if emails:
                    contact_info['email'] = emails[0]
                
            # Extract phone number using regex
            if not contact_info['phone_number']:
                phone_patterns = [
                    r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                    r'\(\d{3}\)\s*\d{3}-\d{4}',
                    r'\d{3}-\d{3}-\d{4}',
                    r'\d{10,}'
                ]
                
                for pattern in phone_patterns:
                    phones = re.findall(pattern, content)
                    if phones:
                        phone = re.sub(r'[^\d+]', '', phones[0])
                        if len(phone) >= 10:
                            contact_info['phone_number'] = phone
                            break
        
        # Also try to extract from structured word data if available
        if hasattr(result, 'pages') and result.pages:
            for page in result.pages:
                if hasattr(page, 'words'):
                    page_content = ' '.join([word.content for word in page.words])
                    
                    # Look for email patterns in page content
                    if not contact_info['email']:
                        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                        emails = re.findall(email_pattern, page_content)
                        if emails:
                            contact_info['email'] = emails[0]
                    
                    # Look for phone patterns
                    if not contact_info['phone_number']:
                        phone_patterns = [
                            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
                            r'\(\d{3}\)\s*\d{3}-\d{4}',
                            r'\d{3}-\d{3}-\d{4}',
                            r'\d{10,}'
                        ]
                        
                        for pattern in phone_patterns:
                            phones = re.findall(pattern, page_content)
                            if phones:
                                phone = re.sub(r'[^\d+]', '', phones[0])
                                if len(phone) >= 10:
                                    contact_info['phone_number'] = phone
                                    break
                        
        return contact_info
    
    def _extract_education_from_azure_di(self, result) -> List[Dict[str, Any]]:
        """Extract education information from Azure DI result"""
        education_list = []
        
        if hasattr(result, 'content'):
            content = result.content
            
            # Use similar patterns as the original method but on Azure DI extracted content
            education_patterns = [
                r'(bachelor|master|phd|doctorate|diploma|certificate|degree)[\s\w]*in[\s\w]+',
                r'(university|college|institute|school)[\s\w]{1,50}',
                r'(b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?|ph\.?d\.?)[\s\w]*',
            ]
            
            year_pattern = r'\b(19|20)\d{2}\b'
            years = re.findall(year_pattern, content)
            
            schools = []
            education_keywords = []
            
            # Extract school names and degrees
            for pattern in education_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    text = match.group()
                    if any(keyword in text.lower() for keyword in 
                          ['university', 'college', 'institute', 'school', 'academy']):
                        schools.append(text)
                    else:
                        education_keywords.append(text)
            
            if schools or education_keywords:
                education_record = {
                    'candidate_id': 0,  # Will be set when saving to database
                    'school': schools[0] if schools else None,
                    'degree': education_keywords[0] if education_keywords else None,
                    'field_of_study': None,
                    'start_date': None,
                    'end_date': years[-1] if years else None,
                    'grade': None,
                    'description': None,
                    'is_active': True
                }
                education_list.append(education_record)
                
        return education_list
    
    def _extract_work_experience_from_azure_di(self, result) -> List[Dict[str, Any]]:
        """Extract work experience from Azure DI result"""
        experience_list = []
        
        if hasattr(result, 'content'):
            content = result.content
            
            # Job title patterns
            job_title_patterns = [
                r'(senior|junior|lead|principal)?\s*(software|web|mobile|data|system)?\s*(engineer|developer|analyst|manager|designer|architect|scientist)',
                r'(project|product|marketing|sales|operations|hr|finance)\s*manager',
                r'(ceo|cto|cfo|vp|director|coordinator|specialist|consultant)',
            ]
            
            # Company patterns (look for common business entity suffixes)
            company_patterns = [
                r'[A-Z][a-zA-Z\s&]+\s+(Inc|LLC|Corp|Corporation|Ltd|Limited|Company|Co\.)',
                r'[A-Z][a-zA-Z\s&]+\s+(Technologies|Tech|Software|Systems|Solutions)'
            ]
            
            job_titles = []
            companies = []
            
            # Extract job titles
            for pattern in job_title_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    job_titles.append(match.group().strip())
            
            # Extract company names
            for pattern in company_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    companies.append(match.group().strip())
            
            # Create work experience records
            if companies or job_titles:
                for i, company in enumerate(companies[:3]):
                    experience_record = {
                        'candidate_id': 0,  # Will be set when saving to database
                        'job_title': job_titles[i] if i < len(job_titles) else None,
                        'company_name': company,
                        'start_date': None,
                        'end_date': None,
                        'description': None,
                        'is_active': True
                    }
                    experience_list.append(experience_record)
                    
        return experience_list
    
    def _extract_skills_from_azure_di(self, result) -> List[Dict[str, Any]]:
        """Extract skills from Azure DI result"""
        skills_list = []
        
        if hasattr(result, 'content'):
            content = result.content.lower()
            
            # Use the same skill patterns from the entity ruler
            skill_keywords = [
                'python', 'javascript', 'java', 'react', 'node.js', 'nodejs', 'sql',
                'html', 'css', 'angular', 'vue', 'flutter', 'django', 'flask', 'spring', 'laravel',
                'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
                'aws', 'azure', 'docker', 'kubernetes', 'jenkins', 'terraform',
                'machine learning', 'tensorflow', 'pytorch', 'pandas', 'numpy', 'scikit-learn',
                'git', 'agile', 'scrum', 'jira', 'confluence'
            ]
            
            extracted_skills = set()
            for skill in skill_keywords:
                if skill in content:
                    extracted_skills.add(skill)
            
            # Convert to expected format
            for skill in extracted_skills:
                skills_list.append({
                    'candidate_id': 0,  # Will be set when saving to database
                    'career_history_id': 0,  # Will be set when linking to specific job
                    'skills': skill.title(),
                    'is_active': True
                })
                
        return skills_list
    
    def _extract_languages_from_azure_di(self, result) -> List[Dict[str, Any]]:
        """Extract language information from Azure DI result"""
        languages_list = []
        
        if hasattr(result, 'content'):
            content = result.content.lower()
            
            language_keywords = [
                'english', 'spanish', 'french', 'german', 'italian', 'portuguese', 'chinese',
                'japanese', 'korean', 'arabic', 'hindi', 'russian', 'dutch', 'swedish',
                'norwegian', 'danish', 'finnish', 'polish', 'czech', 'hungarian',
                'mandarin', 'cantonese', 'tamil', 'bengali', 'urdu', 'thai', 'vietnamese'
            ]
            
            proficiency_keywords = ['native', 'fluent', 'advanced', 'intermediate', 'basic', 'beginner']
            
            for language in language_keywords:
                if language in content:
                    proficiency = 'Intermediate'  # Default
                    for prof in proficiency_keywords:
                        if prof in content:
                            proficiency = prof.title()
                            break
                            
                    languages_list.append({
                        'candidate_id': 0,  # Will be set when saving to database
                        'language': language.title(),
                        'proficiency_level': proficiency,
                        'is_active': True
                    })
                    
        return languages_list
    
    def _extract_certifications_from_azure_di(self, result) -> List[Dict[str, Any]]:
        """Extract certifications and licenses from Azure DI result"""
        certifications_list = []
        
        if hasattr(result, 'content'):
            content = result.content
            
            cert_patterns = [
                r'(aws|azure|google cloud|gcp)\s+(certified|certification)',
                r'(cissp|cisa|cism|pmp|scrum master|product owner)',
                r'(microsoft|oracle|cisco|comptia|linux)\s+certified',
                r'(cpa|cfa|frm|caia|phr|shrm)',
            ]
            
            for pattern in cert_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    certifications_list.append({
                        'candidate_id': 0,  # Will be set when saving to database
                        'name': match.group().title(),
                        'issuing_organization': None,
                        'issue_date': None,
                        'expiration_date': None,
                        'credential_id': None,
                        'credential_url': None,
                        'is_active': True
                    })
                    
        return certifications_list
    
    def _extract_name_and_location_from_azure_di(self, result) -> tuple:
        """Extract name and location from Azure DI result"""
        first_name = None
        last_name = None
        location = None
        
        # Try to extract from key-value pairs first if available
        if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
            for kv_pair in result.key_value_pairs:
                key = kv_pair.key.content.lower() if kv_pair.key else ''
                value = kv_pair.value.content if kv_pair.value else ''
                
                if any(keyword in key for keyword in ['name', 'full name', 'first name']):
                    name_parts = value.split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])
                elif 'location' in key or 'address' in key or 'city' in key:
                    location = value
        
        # Use structured page data if available
        if hasattr(result, 'pages') and result.pages and (not first_name or not location):
            for page in result.pages:
                if hasattr(page, 'words') and page.words:
                    # Get words from the top portion of the first page for name extraction
                    if not first_name:
                        top_words = []
                        for word in page.words[:20]:  # Check first 20 words
                            if hasattr(word, 'polygon') and word.polygon:
                                # Check if word is in upper portion of page (y-coordinate < 2.0)
                                if len(word.polygon) >= 2 and word.polygon[1] < 2.0:
                                    top_words.append(word.content)
                        
                        # Look for name pattern in top words
                        top_text = ' '.join(top_words)
                        name_candidates = []
                        for line in top_text.split('\n'):
                            line = line.strip()
                            if line and not any(char in line for char in ['@', 'http', 'phone', 'mobile', 'tel', '+', '·']):
                                words = line.split()
                                if 2 <= len(words) <= 4 and all(word.replace('-', '').replace("'", '').isalpha() for word in words):
                                    name_candidates.append((words[0], ' '.join(words[1:])))
                        
                        if name_candidates:
                            first_name, last_name = name_candidates[0]
        
        # Fallback to content extraction if structured data doesn't work
        if hasattr(result, 'content') and (not first_name or not location):
            content = result.content
            
            # Try to extract name from the beginning of the document
            if not first_name:
                lines = content.split('\n')
                for line in lines[:5]:  # Check first 5 lines
                    line = line.strip()
                    if line and not any(char in line for char in ['@', 'http', 'phone', 'mobile', 'tel', '+', '·']):
                        # Check if it looks like a name (2-4 words, no special characters)
                        words = line.split()
                        if 2 <= len(words) <= 4 and all(word.replace('-', '').replace("'", '').isalpha() for word in words):
                            first_name = words[0]
                            last_name = ' '.join(words[1:])
                            break
            
            # Extract location using common location patterns
            if not location:
                location_patterns = [
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z]{2})',  # City, State
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*),\s*([A-Z][a-z]+)',  # City, Country
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+)',  # City State without comma
                ]
                
                for pattern in location_patterns:
                    matches = re.search(pattern, content)
                    if matches:
                        location = matches.group()
                        break
        
        return first_name, last_name, location
        
    def _extract_summary_section(self, text: str) -> Optional[str]:
        """
        Extract personal summary or executive summary section from resume text
        
        Args:
            text: Raw resume text
            
        Returns:
            str: Extracted summary or None if not found
        """
        try:
            # Common summary section headers
            summary_patterns = [
                r'(executive\s+summary|professional\s+summary|career\s+summary|summary\s+of\s+qualifications|summary|profile|overview|objective|career\s+objective)',
                r'(about\s+me|professional\s+profile|personal\s+statement)'
            ]
            
            text_lower = text.lower()
            
            for pattern in summary_patterns:
                # Find summary section header
                match = re.search(pattern, text_lower)
                if match:
                    start_pos = match.end()
                    
                    # Extract text after the header until next section or reasonable length
                    remaining_text = text[start_pos:].strip()
                    
                    # Look for next section headers to stop extraction
                    next_section_patterns = [
                        r'\n\s*(experience|work\s+experience|employment|career\s+history|professional\s+experience)',
                        r'\n\s*(education|academic\s+background|qualifications)',
                        r'\n\s*(skills|technical\s+skills|core\s+competencies)',
                        r'\n\s*(certifications|licenses|achievements)',
                        r'\n\s*(contact|contact\s+information)',
                        r'\n\s*\w+\s*\n'  # Generic section break
                    ]
                    
                    summary_text = remaining_text
                    min_end_pos = len(remaining_text)
                    
                    for next_pattern in next_section_patterns:
                        next_match = re.search(next_pattern, remaining_text, re.IGNORECASE)
                        if next_match and next_match.start() < min_end_pos:
                            min_end_pos = next_match.start()
                    
                    if min_end_pos < len(remaining_text):
                        summary_text = remaining_text[:min_end_pos].strip()
                    
                    # Clean up the summary
                    summary_text = re.sub(r'\n+', ' ', summary_text)  # Replace newlines with spaces
                    summary_text = re.sub(r'\s+', ' ', summary_text)   # Normalize whitespace
                    summary_text = summary_text.strip()
                    
                    # Limit length and ensure it's substantial
                    if len(summary_text) > 50:  # Minimum length check
                        if len(summary_text) > 500:
                            summary_text = summary_text[:500] + "..."
                        return summary_text
            
            # Fallback: extract first few meaningful sentences if no summary section found
            sentences = []
            for sentence in text.split('.'):
                sentence = sentence.strip()
                if len(sentence) > 20 and not sentence.lower().startswith(('phone', 'email', 'address', 'mobile')):
                    sentences.append(sentence)
                if len(sentences) >= 3:
                    break
            
            if sentences:
                fallback_summary = '. '.join(sentences) + '.'
                if len(fallback_summary) > 500:
                    fallback_summary = fallback_summary[:500] + "..."
                return fallback_summary
                
            return None
            
        except Exception as e:
            logger.error(f"Error extracting summary section: {str(e)}")
            return None
        
    def _create_langextract_examples(self) -> List[Dict[str, Any]]:
        """Create examples for LangExtract resume parsing"""
        return [
            {
                "full_name": "John Smith",
                "email": "john.smith@email.com",
                "phone": "+1-555-123-4567",
                "location": "San Francisco, CA",
                "summary": "Experienced software engineer with 5+ years in full-stack development",
                "education": {
                    "degree": "Bachelor of Science in Computer Science",
                    "school": "Stanford University",
                    "graduation_year": "2018"
                },
                "work_experience": [
                    {
                        "title": "Senior Software Engineer",
                        "company": "Tech Corp",
                        "duration": "2020-2023",
                        "description": "Led development of microservices architecture"
                    }
                ],
                "skills": ["Python", "JavaScript", "React", "AWS", "Docker"],
                "languages": [
                    {"language": "English", "proficiency": "Native"},
                    {"language": "Spanish", "proficiency": "Intermediate"}
                ],
                "certifications": ["AWS Certified Developer", "Google Cloud Professional"]
            }
        ]

    def _parse_resume_with_langextract(self, pdf_file) -> Dict[str, Any]:
        """Parse resume using LangExtract with Azure OpenAI"""
        try:
            # Extract text from PDF
            text = self.extract_text_from_pdf(pdf_file)
            
            # Define extraction prompt
            prompt_description = """
            Extract comprehensive resume information from the provided text. Focus on:
            1. Personal Information: Full name, email, phone number, location
            2. Professional Summary: Brief career overview or objective
            3. Education: Degrees, schools, graduation years, fields of study
            4. Work Experience: Job titles, companies, dates, descriptions
            5. Skills: Technical and soft skills
            6. Languages: Languages spoken and proficiency levels
            7. Certifications: Professional certifications and licenses
            
            Be thorough and accurate in extraction. If information is not clearly stated, 
            use reasonable inference based on context.
            """
            
            # Create examples for better extraction
            examples = self._create_langextract_examples()
            
            # Use LangExtract with Azure OpenAI
            logger.info("Starting LangExtract extraction with Azure OpenAI")
            
            try:
                # Try to use LangExtract with default Gemini model
                # If LANGEXTRACT_API_KEY is not set, this will fail and we'll use Azure OpenAI fallback
                result = lx.extract(
                    text_or_documents=text,
                    prompt_description=prompt_description,
                    examples=examples,
                    model_id="gemini-2.5-flash",  # Use default Gemini model
                    max_workers=1,
                    extraction_passes=2  # Multiple passes for better accuracy
                )
                
                # Convert LangExtract result to standardized format
                return self._convert_langextract_result(result, text)
                
            except Exception as langextract_error:
                logger.warning(f"LangExtract failed: {langextract_error}")
                
                # Check if it's an API key issue
                if "api" in str(langextract_error).lower() or "key" in str(langextract_error).lower():
                    logger.info("LangExtract failed due to API key issue, using Azure OpenAI fallback")
                else:
                    logger.info("LangExtract failed, falling back to direct Azure OpenAI extraction")
                
                # Fallback: Use direct Azure OpenAI if LangExtract fails
                return self._extract_with_azure_openai_direct(text)
            
        except Exception as e:
            logger.error(f"Error parsing resume with LangExtract: {str(e)}")
            raise
    


    def _convert_langextract_result(self, langextract_result: Any, original_text: str) -> Dict[str, Any]:
        """Convert LangExtract result to standardized format"""
        try:
            # Extract the first result if multiple results
            if hasattr(langextract_result, 'results') and langextract_result.results:
                extracted_data = langextract_result.results[0]
            else:
                extracted_data = langextract_result
            
            # Parse name
            full_name = extracted_data.get('full_name', '')
            name_parts = full_name.split() if full_name else []
            first_name = name_parts[0] if name_parts else None
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
            
            # Parse education
            education_list = []
            education_data = extracted_data.get('education', {})
            if education_data:
                education_record = {
                    'candidate_id': 0,  # Will be set when saving to database
                    'school': education_data.get('school'),
                    'degree': education_data.get('degree'),
                    'field_of_study': education_data.get('field_of_study'),
                    'start_date': None,
                    'end_date': education_data.get('graduation_year'),
                    'grade': None,
                    'description': None,
                    'is_active': True
                }
                education_list.append(education_record)
            
            # Parse work experience
            career_history = []
            work_exp = extracted_data.get('work_experience', [])
            for exp in work_exp:
                career_record = {
                    'candidate_id': 0,  # Will be set when saving to database
                    'job_title': exp.get('title'),
                    'company_name': exp.get('company'),
                    'start_date': None,
                    'end_date': None,
                    'description': exp.get('description'),
                    'is_active': True
                }
                # Parse duration if available
                duration = exp.get('duration', '')
                if duration:
                    # Try to extract start and end dates from duration
                    date_matches = re.findall(r'\b(19|20)\d{2}\b', duration)
                    if len(date_matches) >= 2:
                        career_record['start_date'] = date_matches[0]
                        career_record['end_date'] = date_matches[1]
                    elif len(date_matches) == 1:
                        career_record['start_date'] = date_matches[0]
                        
                career_history.append(career_record)
            
            # Parse skills
            skills_list = []
            skills = extracted_data.get('skills', [])
            for skill in skills:
                skills_list.append({
                    'candidate_id': 0,  # Will be set when saving to database
                    'career_history_id': 0,  # Will be set when linking to specific job
                    'skills': skill,
                    'is_active': True
                })
            
            # Parse languages
            languages_list = []
            languages = extracted_data.get('languages', [])
            for lang in languages:
                if isinstance(lang, dict):
                    languages_list.append({
                        'candidate_id': 0,  # Will be set when saving to database
                        'language': lang.get('language'),
                        'proficiency_level': lang.get('proficiency', 'Intermediate'),
                        'is_active': True
                    })
                else:
                    languages_list.append({
                        'candidate_id': 0,  # Will be set when saving to database
                        'language': lang,
                        'proficiency_level': 'Intermediate',
                        'is_active': True
                    })
            
            # Parse certifications
            certifications_list = []
            certifications = extracted_data.get('certifications', [])
            for cert in certifications:
                certifications_list.append({
                    'candidate_id': 0,  # Will be set when saving to database
                    'name': cert,
                    'issuing_organization': None,
                    'issue_date': None,
                    'expiration_date': None,
                    'credential_id': None,
                    'credential_url': None,
                    'is_active': True
                })
            
            # Structure the response
            parsed_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': extracted_data.get('email'),
                'location': extracted_data.get('location'),
                'phone_number': extracted_data.get('phone'),
                'personal_summary': extracted_data.get('summary'),
                'availability_weeks': 0,
                'preferred_work_types': None,
                'right_to_work': True,
                'salary_expectation': 0,
                'classification_of_interest': None,
                'sub_classification_of_interest': None,
                'citizenship': None,
                'is_active': True,
                # Relationship data
                'career_history': career_history,
                'skills': skills_list,
                'education': education_list,
                'licenses_certifications': certifications_list,
                'languages': languages_list,
                'resumes': [],
                'resume_file': {}
            }
            
            logger.info("Successfully converted LangExtract result to standardized format")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error converting LangExtract result: {str(e)}")
            # Fallback to basic extraction if conversion fails
            return self._fallback_extraction(original_text)

    def _fallback_extraction(self, text: str) -> Dict[str, Any]:
        """Fallback extraction using basic regex patterns"""
        # Basic contact info extraction
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        
        phone_patterns = [
            r'\+?\d{1,3}[-.\s]?\(?\d{1,4}\)?[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
            r'\(\d{3}\)\s*\d{3}-\d{4}',
            r'\d{3}-\d{3}-\d{4}',
            r'\d{10,}'
        ]
        
        phone = None
        for pattern in phone_patterns:
            phones = re.findall(pattern, text)
            if phones:
                phone = re.sub(r'[^\d+]', '', phones[0])
                if len(phone) >= 10:
                    break
        
        return {
            'first_name': None,
            'last_name': None,
            'email': emails[0] if emails else None,
            'location': None,
            'phone_number': phone,
            'personal_summary': None,
            'availability_weeks': 0,
            'preferred_work_types': None,
            'right_to_work': True,
            'salary_expectation': 0,
            'classification_of_interest': None,
            'sub_classification_of_interest': None,
            'citizenship': None,
            'is_active': True,
            'career_history': [],
            'skills': [],
            'education': [],
            'licenses_certifications': [],
            'languages': [],
            'resumes': [],
            'resume_file': {}
        }

    def parse_resume(self, pdf_file) -> Dict[str, Any]:
        """
        Main method to parse resume using the configured parsing method
        
        Args:
            pdf_file: PDF file object
            
        Returns:
            Dict containing extracted candidate information
        """
        try:
            logger.info(f"Parsing resume using method: {self.parsing_method}")
            
            if self.parsing_method == 'langextract':
                return self._parse_resume_with_langextract(pdf_file)
            elif self.parsing_method == 'azure_di':
                return self._parse_resume_with_azure_di(pdf_file)
            else:  # spacy
                return self._parse_resume_with_spacy(pdf_file)
                
        except Exception as e:
            logger.error(f"Error parsing resume with {self.parsing_method}: {str(e)}")
            # Try fallback methods if primary method fails
            if self.parsing_method != 'spacy':
                logger.info("Attempting fallback to spacy method")
                try:
                    self._initialize_spacy()
                    return self._parse_resume_with_spacy(pdf_file)
                except Exception as fallback_error:
                    logger.error(f"Fallback also failed: {str(fallback_error)}")
            
            raise ValueError(f"Failed to parse resume: {str(e)}")
    
    def _parse_resume_with_azure_di(self, pdf_file) -> Dict[str, Any]:
        """Parse resume using Azure Document Intelligence with query fields"""
        try:
            # Analyze document with Azure DI
            azure_result = self._analyze_document_with_azure_di(pdf_file)
            
            # Check if query fields were used and extract accordingly
            used_query_fields = getattr(azure_result, '_used_query_fields', False)
            
            if used_query_fields:
                logger.info("Using query fields extraction for resume parsing")
                # Use the new query fields extraction method
                first_name, last_name, location = self._extract_name_and_location_from_query_fields(azure_result)
                contact_info = self._extract_contact_info_from_query_fields(azure_result)
                education = self._extract_education_from_query_fields(azure_result)
                career_history = self._extract_work_experience_from_query_fields(azure_result)
                skills = self._extract_skills_from_query_fields(azure_result)
                languages = self._extract_languages_from_query_fields(azure_result)
                licenses_certifications = self._extract_certifications_from_query_fields(azure_result)
                personal_summary = self._extract_summary_from_query_fields(azure_result)
            else:
                logger.info("Using traditional extraction methods (fallback)")
                # Fall back to the original extraction methods
                first_name, last_name, location = self._extract_name_and_location_from_azure_di(azure_result)
                contact_info = self._extract_contact_info_from_azure_di(azure_result)
                education = self._extract_education_from_azure_di(azure_result)
                career_history = self._extract_work_experience_from_azure_di(azure_result)
                skills = self._extract_skills_from_azure_di(azure_result)
                languages = self._extract_languages_from_azure_di(azure_result)
                licenses_certifications = self._extract_certifications_from_azure_di(azure_result)
                
                # Extract personal summary from content
                personal_summary = None
                if hasattr(azure_result, 'content'):
                    personal_summary = self._extract_summary_section(azure_result.content)
            
            # Structure the response in the same format as candidate API
            parsed_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': contact_info.get('email'),
                'location': location,
                'phone_number': contact_info.get('phone_number'),
                'personal_summary': personal_summary,
                'availability_weeks': 0,
                'preferred_work_types': None,
                'right_to_work': True,
                'salary_expectation': 0,
                'classification_of_interest': None,
                'sub_classification_of_interest': None,
                'citizenship': None,
                'is_active': True,
                # Relationship data
                'career_history': career_history,
                'skills': skills,
                'education': education,
                'licenses_certifications': licenses_certifications,
                'languages': languages,
                'resumes': [],  # Will be populated when resume is saved
                'resume_file': {}
            }
            
            logger.info("Successfully parsed resume using Azure Document Intelligence")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume with Azure DI: {str(e)}")
            raise
    
    def _parse_resume_with_spacy(self, pdf_file) -> Dict[str, Any]:
        """Parse resume using spaCy and NLTK (original method)"""
        try:
            # Extract text from PDF
            raw_text = self.extract_text_from_pdf(pdf_file)
            
            # Clean text for better NER
            cleaned_text = self.clean_text(raw_text)
            
            # Process with spaCy for NER
            doc = self.nlp(raw_text)  # Use raw text for NER to preserve formatting

            print(doc)
            
            # Extract name (assume first PERSON entity is the candidate's name)
            first_name = None
            last_name = None
            for ent in doc.ents:
                if ent.label_ == "PERSON":
                    name_parts = ent.text.strip().split()
                    if len(name_parts) >= 2:
                        first_name = name_parts[0]
                        last_name = ' '.join(name_parts[1:])
                    elif len(name_parts) == 1:
                        first_name = name_parts[0]
                    break
                    
            # Extract location
            location = None
            for ent in doc.ents:
                if ent.label_ in ["GPE", "LOC"]:  # Geopolitical entity or location
                    location = ent.text
                    break
                    
            # Extract contact information
            contact_info = self.extract_contact_info(raw_text)
            
            # Extract sections
            education = self.extract_education(raw_text)
            career_history = self.extract_work_experience(raw_text)
            skills = self.extract_skills(raw_text)
            languages = self.extract_languages(raw_text)
            licenses_certifications = self.extract_certifications(raw_text)
            
            # Extract personal/executive summary with better logic
            personal_summary = self._extract_summary_section(raw_text)
                
            # Structure the response in the same format as candidate API
            parsed_data = {
                'first_name': first_name,
                'last_name': last_name,
                'email': contact_info.get('email'),
                'location': location,
                'phone_number': contact_info.get('phone_number'),
                'personal_summary': personal_summary,
                'availability_weeks': None,
                'preferred_work_types': None,
                'right_to_work': None,
                'salary_expectation': None,
                'classification_of_interest': None,
                'sub_classification_of_interest': None,
                'is_active': True,
                # Relationship data
                'career_history': career_history,
                'skills': skills,
                'education': education,
                'licenses_certifications': licenses_certifications,
                'languages': languages,
                'resumes': []  # Will be populated when resume is saved
            }
            
            logger.info(f"Successfully parsed resume with {len(doc.ents)} entities using spaCy")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume with spaCy: {str(e)}")
            raise

    def _extract_name_and_location_from_query_fields(self, result) -> tuple:
        """Extract name and location from Azure DI query fields results"""
        first_name = None
        last_name = None
        location = None
        
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract name from the Name field
                    if 'Name' in doc.fields and doc.fields['Name']:
                        full_name = doc.fields['Name'].value_string or doc.fields['Name'].content
                        if full_name:
                            name_parts = full_name.strip().split()
                            if len(name_parts) >= 2:
                                first_name = name_parts[0]
                                last_name = ' '.join(name_parts[1:])
                            elif len(name_parts) == 1:
                                first_name = name_parts[0]
                    
                    # Location is not in our query fields, so we'll extract from content fallback
                    # This will be handled by the fallback extraction methods
        
        return first_name, last_name, location
    
    def _extract_contact_info_from_query_fields(self, result) -> Dict[str, Optional[str]]:
        """Extract contact information from Azure DI query fields results"""
        contact_info = {
            'email': None,
            'phone_number': None
        }
        
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract email
                    if 'Email' in doc.fields and doc.fields['Email']:
                        email_value = doc.fields['Email'].value_string or doc.fields['Email'].content
                        if email_value and '@' in email_value:
                            contact_info['email'] = email_value.strip()
                    
                    # Extract phone
                    if 'Phone' in doc.fields and doc.fields['Phone']:
                        phone_value = doc.fields['Phone'].value_string or doc.fields['Phone'].content
                        if phone_value:
                            # Clean phone number
                            phone_clean = re.sub(r'[^\d+]', '', phone_value)
                            if len(phone_clean) >= 10:
                                contact_info['phone_number'] = phone_clean
        
        return contact_info
    
    def _extract_education_from_query_fields(self, result) -> List[Dict[str, Any]]:
        """Extract education information from Azure DI query fields results"""
        education_list = []
        
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract education from the Education field
                    if 'Education' in doc.fields and doc.fields['Education']:
                        education_value = doc.fields['Education'].value_string or doc.fields['Education'].content
                        if education_value:
                            # Parse education content to extract structured information
                            education_record = {
                                'school': None,
                                'degree': None,
                                'field_of_study': None,
                                'start_date': None,
                                'end_date': None,
                                'grade': None,
                                'description': education_value
                            }
                            
                            # Try to extract school and degree from the education text
                            # Look for common patterns like "Bachelor of Science in Computer Science from MIT"
                            degree_patterns = [
                                r'(bachelor|master|phd|doctorate|diploma|certificate|degree)[\s\w]*',
                                r'(b\.?s\.?|m\.?s\.?|b\.?a\.?|m\.?a\.?|ph\.?d\.?)[\s\w]*'
                            ]
                            school_patterns = [
                                r'(university|college|institute|school)[\s\w]{1,50}',
                                r'from\s+([\w\s]+?)(?:\s|$)',
                                r'at\s+([\w\s]+?)(?:\s|$)'
                            ]
                            
                            for pattern in degree_patterns:
                                match = re.search(pattern, education_value, re.IGNORECASE)
                                if match:
                                    education_record['degree'] = match.group().strip()
                                    break
                            
                            for pattern in school_patterns:
                                match = re.search(pattern, education_value, re.IGNORECASE)
                                if match:
                                    school_name = match.group().replace('from', '').replace('at', '').strip()
                                    if school_name:
                                        education_record['school'] = school_name
                                        break
                            
                            education_list.append(education_record)
        
        return education_list
    
    def _extract_work_experience_from_query_fields(self, result) -> List[Dict[str, Any]]:
        """Extract work experience from Azure DI query fields results with separate role and description"""
        experience_list = []
        
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract role and description separately
                    role_value = None
                    description_value = None
                    
                    if 'ProfessionalExperienceRole' in doc.fields and doc.fields['ProfessionalExperienceRole']:
                        role_value = doc.fields['ProfessionalExperienceRole'].value_string or doc.fields['ProfessionalExperienceRole'].content
                    
                    if 'ProfessionalExperienceDescription' in doc.fields and doc.fields['ProfessionalExperienceDescription']:
                        description_value = doc.fields['ProfessionalExperienceDescription'].value_string or doc.fields['ProfessionalExperienceDescription'].content
                    
                    # Process if we have at least one of the fields
                    if role_value or description_value:
                        experience_record = {
                            'job_title': None,
                            'company_name': None,
                            'start_date': None,
                            'end_date': None,
                            'description': description_value
                        }
                        
                        # Extract job title and company from role field
                        if role_value:
                            # Try to extract job title from role
                            job_title_patterns = [
                                r'(senior|junior|lead|principal)?\s*(software|web|mobile|data|system)?\s*(engineer|developer|analyst|manager|designer|architect|scientist)',
                                r'(project|product|marketing|sales|operations|hr|finance)\s*manager',
                                r'(ceo|cto|cfo|vp|director|coordinator|specialist|consultant)',
                                r'^([^,\n@]+?)(?:\s+at\s|\s+@\s|$)',  # Everything before "at" or "@" as job title
                            ]
                            
                            for pattern in job_title_patterns:
                                match = re.search(pattern, role_value, re.IGNORECASE)
                                if match:
                                    if pattern.startswith('^'):  # For the general pattern
                                        experience_record['job_title'] = match.group(1).strip()
                                    else:
                                        experience_record['job_title'] = match.group().strip()
                                    break
                            
                            # Extract company name from role field
                            company_patterns = [
                                r'(?:at|@)\s+([A-Z][a-zA-Z\s&]+?)(?:\s|$|,)',  # After "at" or "@"
                                r'([A-Z][a-zA-Z\s&]+)\s+(Inc|LLC|Corp|Corporation|Ltd|Limited|Company|Co\.)',
                                r'([A-Z][a-zA-Z\s&]+)\s+(Technologies|Tech|Software|Systems|Solutions)'
                            ]
                            
                            for pattern in company_patterns:
                                match = re.search(pattern, role_value)
                                if match:
                                    if '(?:at|@)' in pattern:
                                        company_name = match.group(1).strip()
                                    else:
                                        company_name = match.group().strip()
                                    experience_record['company_name'] = company_name
                                    break
                            
                            # If no job title was extracted yet, use the whole role as job title
                            if not experience_record['job_title']:
                                # Clean up the role value to use as job title
                                clean_role = re.sub(r'\s+at\s+.*$', '', role_value, flags=re.IGNORECASE).strip()
                                clean_role = re.sub(r'\s+@\s+.*$', '', clean_role, flags=re.IGNORECASE).strip()
                                if clean_role:
                                    experience_record['job_title'] = clean_role
                        
                        # Also try to extract company from description if not found in role
                        if not experience_record['company_name'] and description_value:
                            company_patterns = [
                                r'(?:at|@)\s+([A-Z][a-zA-Z\s&]+?)(?:\s|$|,)',
                                r'([A-Z][a-zA-Z\s&]+)\s+(Inc|LLC|Corp|Corporation|Ltd|Limited|Company|Co\.)',
                                r'([A-Z][a-zA-Z\s&]+)\s+(Technologies|Tech|Software|Systems|Solutions)'
                            ]
                            
                            for pattern in company_patterns:
                                match = re.search(pattern, description_value)
                                if match:
                                    if '(?:at|@)' in pattern:
                                        company_name = match.group(1).strip()
                                    else:
                                        company_name = match.group().strip()
                                    experience_record['company_name'] = company_name
                                    break
                        
                        experience_list.append(experience_record)
        
        return experience_list
    
    def _extract_skills_from_query_fields(self, result) -> List[Dict[str, Any]]:
        """Extract skills from Azure DI query fields results"""
        skills_list = []
        
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract skills from the Skills field
                    if 'Skills' in doc.fields and doc.fields['Skills']:
                        skills_value = doc.fields['Skills'].value_string or doc.fields['Skills'].content
                        if skills_value:
                            # Split skills by common delimiters
                            skills = re.split(r'[,;|\n\r•·\-]', skills_value)
                            for skill in skills:
                                skill = skill.strip()
                                if skill and len(skill) > 1:
                                    skills_list.append({
                                        'skills': skill.title(),
                                        'career_history_id': None
                                    })
        
        return skills_list
    
    def _extract_languages_from_query_fields(self, result) -> List[Dict[str, Any]]:
        """Extract languages from Azure DI query fields results"""
        languages_list = []
        
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract languages from the Languages field
                    if 'Languages' in doc.fields and doc.fields['Languages']:
                        languages_value = doc.fields['Languages'].value_string or doc.fields['Languages'].content
                        if languages_value:
                            # Parse language mentions
                            languages = re.split(r'[,;|\n\r•·\-]', languages_value)
                            for lang in languages:
                                lang = lang.strip()
                                if lang and len(lang) > 1:
                                    # Try to extract proficiency if mentioned
                                    proficiency = 'Intermediate'  # Default
                                    proficiency_keywords = ['native', 'fluent', 'advanced', 'intermediate', 'basic', 'beginner']
                                    for prof in proficiency_keywords:
                                        if prof.lower() in lang.lower():
                                            proficiency = prof.title()
                                            lang = lang.replace(prof, '').strip()
                                            break
                                    
                                    languages_list.append({
                                        'candidate_id': 0,  # Will be set when saving to database
                                        'language': lang.title(),
                                        'proficiency_level': proficiency,
                                        'is_active': True
                                    })
        
        return languages_list
    
    def _extract_certifications_from_query_fields(self, result) -> List[Dict[str, Any]]:
        """Extract certifications from Azure DI query fields results"""
        certifications_list = []
        
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract certifications from the LicensesCertifications field
                    if 'LicensesCertifications' in doc.fields and doc.fields['LicensesCertifications']:
                        certs_value = doc.fields['LicensesCertifications'].value_string or doc.fields['LicensesCertifications'].content
                        if certs_value:
                            # Parse certification mentions
                            certs = re.split(r'[,;|\n\r•·\-]', certs_value)
                            for cert in certs:
                                cert = cert.strip()
                                if cert and len(cert) > 2:
                                    certifications_list.append({
                                        'name': cert.title(),
                                        'issuing_organization': None,
                                        'issue_date': None,
                                        'expiration_date': None,
                                        'credential_id': None,
                                        'credential_url': None
                                    })
        
        return certifications_list
    
    def _extract_summary_from_query_fields(self, result) -> Optional[str]:
        """Extract professional summary from Azure DI query fields results"""
        if hasattr(result, 'documents') and result.documents:
            for doc in result.documents:
                if hasattr(doc, 'fields') and doc.fields:
                    # Extract summary from the Summary field
                    if 'Summary' in doc.fields and doc.fields['Summary']:
                        summary_value = doc.fields['Summary'].value_string or doc.fields['Summary'].content
                        if summary_value and len(summary_value.strip()) > 50:  # Minimum length check
                            summary = summary_value.strip()
                            if len(summary) > 500:
                                summary = summary[:500] + "..."
                            return summary
        
        return None

    def _convert_azure_di_to_structured_text(self, result) -> str:
        """
        Convert Azure DI result to structured text format that can be used with LLM
        for better field extraction if standard methods don't work well
        
        Args:
            result: Azure DI analysis result
            
        Returns:
            str: Structured text representation of the document
        """
        structured_text = ""
        
        if hasattr(result, 'content'):
            # Use the main content as base
            structured_text = result.content
            
        # Add additional structured information if available
        if hasattr(result, 'pages') and result.pages:
            for page_idx, page in enumerate(result.pages):
                structured_text += f"\n\n--- PAGE {page_idx + 1} STRUCTURED DATA ---\n"
                
                # Add word-level information with coordinates for better context
                if hasattr(page, 'words'):
                    words_by_line = {}
                    for word in page.words:
                        if hasattr(word, 'polygon') and len(word.polygon) >= 2:
                            y_coord = round(word.polygon[1], 1)  # Use Y coordinate to group by line
                            if y_coord not in words_by_line:
                                words_by_line[y_coord] = []
                            words_by_line[y_coord].append(word.content)
                    
                    # Sort by Y coordinate and build line-by-line text
                    for y_coord in sorted(words_by_line.keys()):
                        line_text = ' '.join(words_by_line[y_coord])
                        structured_text += f"Line {y_coord}: {line_text}\n"
                
                # Add table information if available
                if hasattr(result, 'tables') and result.tables:
                    for table_idx, table in enumerate(result.tables):
                        structured_text += f"\n--- TABLE {table_idx + 1} ---\n"
                        if hasattr(table, 'cells'):
                            table_data = {}
                            for cell in table.cells:
                                row = cell.row_index
                                col = cell.column_index
                                if row not in table_data:
                                    table_data[row] = {}
                                table_data[row][col] = cell.content
                            
                            # Format table
                            for row_idx in sorted(table_data.keys()):
                                row_cells = []
                                for col_idx in sorted(table_data[row_idx].keys()):
                                    row_cells.append(table_data[row_idx][col_idx])
                                structured_text += " | ".join(row_cells) + "\n"
        
        # Add key-value pairs if available
        if hasattr(result, 'key_value_pairs') and result.key_value_pairs:
            structured_text += "\n--- KEY-VALUE PAIRS ---\n"
            for kv_pair in result.key_value_pairs:
                key = kv_pair.key.content if kv_pair.key else 'Unknown Key'
                value = kv_pair.value.content if kv_pair.value else 'Unknown Value'
                structured_text += f"{key}: {value}\n"
        
        return structured_text
    
    def _extract_with_llm_fallback(self, structured_text: str) -> Dict[str, Any]:
        """
        Placeholder method for LLM-based extraction as fallback
        This could be implemented with OpenAI or Azure OpenAI in the future
        
        Args:
            structured_text: Structured text from Azure DI
            
        Returns:
            Dict: Extracted information using LLM
        """
        # For now, this is a placeholder that returns empty structure
        # In the future, this could call OpenAI/Azure OpenAI with a prompt like:
        # "Extract the following information from this resume: name, email, phone, education, work experience, skills..."
        
        logger.info("LLM fallback not implemented yet, using standard regex extraction")
        return {
            'contact_info': {'email': None, 'phone_number': None},
            'education': [],
            'work_experience': [],
            'skills': [],
            'languages': [],
            'certifications': [],
            'first_name': None,
            'last_name': None,
            'location': None,
            'summary': None
        }

    def _extract_with_azure_openai_direct(self, text: str) -> Dict[str, Any]:
        """Direct extraction using Azure OpenAI when LangExtract fails"""
        try:
            # Create structured prompt for direct extraction
            prompt = f"""
            Extract the following information from this resume text and return it in JSON format:

            Resume Text:
            {text}

            Please extract:
            1. full_name: The person's complete name
            2. email: Email address
            3. phone: Phone number (clean format)
            4. location: Current location/address
            5. summary: Professional summary or objective
            6. education: Array of education records with degree, school, graduation_year
            7. work_experience: Array of work experience with title, company, duration, description
            8. skills: Array of technical and professional skills
            9. languages: Array of languages with proficiency
            10. certifications: Array of certifications and licenses

            Return ONLY valid JSON without any additional text or markdown formatting.
            """

            response = self.azure_openai_client.chat.completions.create(
                model=self.azure_openai_model,
                messages=[
                    {"role": "system", "content": "You are an expert at extracting structured information from resumes. Extract the requested information accurately and completely."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000
            )

            # Parse the JSON response
            result_text = response.choices[0].message.content
            
            # Clean up the response (remove markdown if present)
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0]
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0]
            
            import json
            extracted_data = json.loads(result_text.strip())
            
            # Convert to standardized format
            return self._convert_direct_extraction_result(extracted_data, text)
            
        except Exception as e:
            logger.error(f"Direct Azure OpenAI extraction failed: {str(e)}")
            # Final fallback to basic text extraction
            return self._fallback_extraction(text)
    
    def _convert_direct_extraction_result(self, extracted_data: Dict[str, Any], original_text: str) -> Dict[str, Any]:
        """Convert direct Azure OpenAI extraction result to standardized format"""
        try:
            # Parse name
            full_name = extracted_data.get('full_name', '')
            name_parts = full_name.split() if full_name else []
            first_name = name_parts[0] if name_parts else None
            last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else None
            
            # Parse education
            education_list = []
            education_data = extracted_data.get('education', [])
            if isinstance(education_data, list):
                for edu in education_data:
                    education_record = {
                        'candidate_id': 0,  # Will be set when saving to database
                        'school': edu.get('school'),
                        'degree': edu.get('degree'),
                        'field_of_study': edu.get('field_of_study'),
                        'start_date': None,
                        'end_date': edu.get('graduation_year'),
                        'grade': None,
                        'description': None,
                        'is_active': True
                    }
                    education_list.append(education_record)
            
            # Parse work experience
            career_history = []
            work_exp = extracted_data.get('work_experience', [])
            if isinstance(work_exp, list):
                for exp in work_exp:
                    career_record = {
                        'candidate_id': 0,  # Will be set when saving to database
                        'job_title': exp.get('title'),
                        'company_name': exp.get('company'),
                        'start_date': exp.get('start_date'),
                        'end_date': exp.get('end_date'),
                        'description': exp.get('description'),
                        'is_active': True
                    }
                    career_history.append(career_record)
            
            # Parse skills
            skills_list = []
            skills_data = extracted_data.get('skills', [])
            if isinstance(skills_data, list):
                for skill in skills_data:
                    if isinstance(skill, str):
                        skills_list.append({
                            'candidate_id': 0,  # Will be set when saving to database
                            'career_history_id': 0,  # Will be set when linking to specific job
                            'skills': skill,
                            'is_active': True
                        })
            
            # Parse languages
            languages_list = []
            languages_data = extracted_data.get('languages', [])
            if isinstance(languages_data, list):
                for lang in languages_data:
                    if isinstance(lang, str):
                        languages_list.append({
                            'candidate_id': 0,  # Will be set when saving to database
                            'language': lang,
                            'proficiency_level': None,
                            'is_active': True
                        })
                    elif isinstance(lang, dict):
                        languages_list.append({
                            'candidate_id': 0,  # Will be set when saving to database
                            'language': lang.get('language'),
                            'proficiency_level': lang.get('proficiency'),
                            'is_active': True
                        })
            
            # Parse certifications
            certifications_list = []
            cert_data = extracted_data.get('certifications', [])
            if isinstance(cert_data, list):
                for cert in cert_data:
                    if isinstance(cert, str):
                        certifications_list.append({
                            'candidate_id': 0,  # Will be set when saving to database
                            'name': cert,
                            'issuing_organization': None,
                            'issue_date': None,
                            'expiration_date': None,
                            'credential_id': None,
                            'credential_url': None,
                            'is_active': True
                        })
            
            # Create standardized result
            return {
                'first_name': first_name,
                'last_name': last_name,
                'email': extracted_data.get('email'),
                'location': extracted_data.get('location'),
                'phone_number': extracted_data.get('phone'),
                'personal_summary': extracted_data.get('summary'),
                'availability_weeks': 0,
                'preferred_work_types': None,
                'right_to_work': True,
                'salary_expectation': 0,
                'classification_of_interest': None,
                'sub_classification_of_interest': None,
                'citizenship': None,
                'is_active': True,
                'career_history': career_history,
                'skills': skills_list,
                'education': education_list,
                'licenses_certifications': certifications_list,
                'languages': languages_list,
                'resumes': [],
                'resume_file': {}
            }
            
        except Exception as e:
            logger.error(f"Error converting direct extraction result: {str(e)}")
            # Final fallback
            return self._fallback_extraction(original_text)

# Global instance - created lazily to pick up environment variable changes
_resume_parser_instance = None

def get_resume_parser():
    """Get or create the resume parser instance"""
    global _resume_parser_instance
    if _resume_parser_instance is None:
        _resume_parser_instance = ResumeParser()
    return _resume_parser_instance

def reset_resume_parser():
    """Reset the resume parser instance (useful for testing or config changes)"""
    global _resume_parser_instance
    _resume_parser_instance = None

# For backward compatibility
resume_parser = get_resume_parser() 