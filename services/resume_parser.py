import re
import spacy
import PyPDF2
import nltk
from io import BytesIO
from datetime import datetime
from typing import Dict, List, Optional, Any
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ResumeParser:
    """
    Resume parsing service using NER and PDF text extraction
    Based on the methodology from: https://medium.com/pythons-gurus/performing-resum%C3%A9-analysis-using-ner-with-cosine-similarity-8eb99879cda4
    """
    
    def __init__(self):
        """Initialize the resume parser with NLP models and entity patterns"""
        self._initialize_nltk_data()
        self.nlp = self._load_spacy_model()
        self._setup_entity_ruler()
        self.lemmatizer = WordNetLemmatizer()
        
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
            
            logger.info(f"Successfully parsed resume with {len(doc.ents)} entities")
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing resume: {str(e)}")
            raise ValueError(f"Failed to parse resume: {str(e)}")

# Global instance
resume_parser = ResumeParser() 