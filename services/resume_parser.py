import re
import spacy
import PyPDF2
import nltk
import os
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Any
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import logging
from dotenv import load_dotenv

# Azure Document Intelligence imports
try:
    from azure.ai.documentintelligence import DocumentIntelligenceClient
    from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
    from azure.core.credentials import AzureKeyCredential
    AZURE_DI_AVAILABLE = True
except ImportError:
    AZURE_DI_AVAILABLE = False

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class ResumeParser:
    """
    Resume parsing service using NER and PDF text extraction
    Based on the methodology from: https://medium.com/pythons-gurus/performing-resum%C3%A9-analysis-using-ner-with-cosine-similarity-8eb99879cda4
    """
    
    def __init__(self):
        """Initialize the resume parser with NLP models and entity patterns"""
        # Check which parsing mode to use
        self.use_azure_di = os.getenv('USE_AZURE_DOCUMENT_INTELLIGENCE', 'false').lower() == 'true'
        
        if self.use_azure_di:
            self._initialize_azure_di_client()
            # Still need NLTK for text cleaning and summary extraction
            self._initialize_nltk_data()
        else:
            self._initialize_nltk_data()
            self.nlp = self._load_spacy_model()
            self._setup_entity_ruler()
            
        self.lemmatizer = WordNetLemmatizer()
        
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
                'school': schools[0] if schools else None,
                'degree': education_keywords[0] if education_keywords else None,
                'field_of_study': None,  # Could be enhanced with more sophisticated parsing
                'start_date': None,
                'end_date': years[-1] if years else None,  # Assume most recent year is graduation
                'grade': None,
                'description': None
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
                
        # Create work experience records
        if companies or job_titles:
            for i, company in enumerate(companies[:3]):  # Limit to top 3 companies
                experience_record = {
                    'job_title': job_titles[i] if i < len(job_titles) else None,
                    'company_name': company,
                    'start_date': None,  # Could be enhanced with date parsing
                    'end_date': None,
                    'description': None
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
                'skills': skill.title(),
                'career_history_id': None
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
                    'language': language.title(),
                    'proficiency_level': proficiency
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
                    'name': match.group().title(),
                    'issuing_organization': None,
                    'issue_date': None,
                    'expiration_date': None,
                    'credential_id': None,
                    'credential_url': None
                })
                
        return certifications_list
        
    def _analyze_document_with_azure_di(self, pdf_file) -> Dict[str, Any]:
        """
        Analyze document using Azure Document Intelligence
        
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
            
            # Try different models in order of preference
            # prebuilt-layout provides the most structure but may not be available in all regions
            # prebuilt-read is more widely available but provides less structure
            # prebuilt-document is a general-purpose model
            models_to_try = [
                ("prebuilt-layout", "layout analysis with full structure"),
                ("prebuilt-read", "text extraction with basic structure"), 
                ("prebuilt-document", "general document analysis")
            ]
            
            last_error = None
            for model_name, description in models_to_try:
                try:
                    logger.info(f"Trying Azure DI model: {model_name} ({description})")
                    poller = self.azure_di_client.begin_analyze_document(
                        model_name,
                        analyze_request
                    )
                    
                    result = poller.result()
                    logger.info(f"Azure Document Intelligence analysis completed using {model_name}")
                    
                    # Add metadata about which model was used
                    if hasattr(result, '__dict__'):
                        result._used_model = model_name
                    
                    return result
                    
                except Exception as model_error:
                    last_error = model_error
                    if "404" in str(model_error):
                        logger.warning(f"Model {model_name} not available: {model_error}")
                        continue
                    else:
                        # If it's not a 404, this might be a more serious error
                        logger.error(f"Error with model {model_name}: {model_error}")
                        raise model_error
            
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
                    'school': schools[0] if schools else None,
                    'degree': education_keywords[0] if education_keywords else None,
                    'field_of_study': None,
                    'start_date': None,
                    'end_date': years[-1] if years else None,
                    'grade': None,
                    'description': None
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
                        'job_title': job_titles[i] if i < len(job_titles) else None,
                        'company_name': company,
                        'start_date': None,
                        'end_date': None,
                        'description': None
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
                    'skills': skill.title(),
                    'career_history_id': None
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
                        'language': language.title(),
                        'proficiency_level': proficiency
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
                        'name': match.group().title(),
                        'issuing_organization': None,
                        'issue_date': None,
                        'expiration_date': None,
                        'credential_id': None,
                        'credential_url': None
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
        
    def parse_resume(self, pdf_file) -> Dict[str, Any]:
        """
        Main method to parse resume and extract structured information
        
        Args:
            pdf_file: PDF file object
            
        Returns:
            Dict containing extracted candidate information
        """
        try:
            if self.use_azure_di:
                return self._parse_resume_with_azure_di(pdf_file)
            else:
                return self._parse_resume_with_spacy(pdf_file)
                
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise ValueError(f"Failed to parse resume: {str(e)}")
    
    def _parse_resume_with_azure_di(self, pdf_file) -> Dict[str, Any]:
        """Parse resume using Azure Document Intelligence"""
        try:
            # Analyze document with Azure DI
            azure_result = self._analyze_document_with_azure_di(pdf_file)
            
            # Extract information using Azure DI results
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

# Global instance
resume_parser = ResumeParser() 