import os
import asyncio
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, AzureOpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
import json

# Load environment variables
load_dotenv()

class CandidateAISummaryService:
    """
    Service for generating AI summaries and embeddings for candidate profiles
    using Azure OpenAI through LangChain
    """
    
    def __init__(self):
        """Initialize the AI service with Azure OpenAI configurations"""
        try:
            # Check for required environment variables
            required_env_vars = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY']
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
            print("Initializing Azure OpenAI LLM...")
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_version=os.getenv('AZURE_API_VERSION', '2024-02-15-preview'),
                azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                temperature=0.3,
                max_tokens=300
            )
            print("LLM initialized successfully")
            
            print("Initializing Azure OpenAI Embeddings...")
            self.embeddings = AzureOpenAIEmbeddings(
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_version=os.getenv('AZURE_API_VERSION', '2024-02-15-preview'),
                azure_deployment=os.getenv('AZURE_OPENAI_EMBEDDING_DEPLOYMENT', 'text-embedding-3-small'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                dimensions=1536  # Standard dimension for text-embedding-3-small
            )
            print("Embeddings initialized successfully")
            
        except Exception as init_error:
            print(f"Failed to initialize AI service: {str(init_error)}")
            raise init_error
        
        # Note: Prompt templates are now managed in the database
        # This service will fetch the active template from AiPromptTemplate model
    
    def get_active_prompt_template(self):
        """
        Get the active prompt template from the database
        
        Returns:
            PromptTemplate: LangChain PromptTemplate object
        """
        try:
            # Import here to avoid circular imports
            from models import AiPromptTemplate
            
            active_template = AiPromptTemplate.get_active_template()
            
            if not active_template:
                # Fallback to a detailed template if no active template found
                fallback_template = """
            You are an AI assistant specializing in creating professional candidate profile summaries for recruitment purposes.
            
            Given the candidate profile data below, create a concise professional summary in exactly 200 words or less following this format:
            
            "[X] years of experience in [position] in [domain field].
            Graduated from [university/education].
            Strengths: [key skills and strengths]
            Looking for: [salary expectation and work preferences]
            Open to work status: [availability and notice period]
            Other remarks: [additional relevant information]"
            
            Candidate Profile Data:
            {candidate_profile_data}
            
            Please ensure the summary is:
            - Professional and concise
            - Highlights key qualifications and experience
            - Includes relevant education background
            - Mentions salary expectations if available
            - Notes work availability and preferences
            - Under 200 words total
            
            Summary:"""
                print("Warning: No active prompt template found, using fallback template")
                return PromptTemplate(
                    input_variables=["candidate_profile_data"],
                    template=fallback_template
                )
            
            return PromptTemplate(
                input_variables=["candidate_profile_data"],
                template=active_template.template_content
            )
            
        except Exception as e:
            print(f"Error fetching active prompt template: {str(e)}")
            # Fallback template
            fallback_template = """
            You are an AI assistant specializing in creating professional candidate profile summaries for recruitment purposes.
            
            Given the candidate profile data below, create a concise professional summary in exactly 200 words or less following this format:
            
            "[X] years of experience in [position] in [domain field].
            Graduated from [university/education].
            Strengths: [key skills and strengths]
            Looking for: [salary expectation and work preferences]
            Open to work status: [availability and notice period]
            Other remarks: [additional relevant information]"
            
            Candidate Profile Data:
            {candidate_profile_data}
            
            Please ensure the summary is:
            - Professional and concise
            - Highlights key qualifications and experience
            - Includes relevant education background
            - Mentions salary expectations if available
            - Notes work availability and preferences
            - Under 200 words total
            
            Summary:"""
            return PromptTemplate(
                input_variables=["candidate_profile_data"],
                template=fallback_template
            )
    
    def format_candidate_data(self, candidate_dict: Dict[str, Any]) -> str:
        """
        Format candidate dictionary data into a structured text for AI processing
        
        Args:
            candidate_dict (Dict): Complete candidate profile with relationships
            
        Returns:
            str: Formatted candidate data string
        """
        try:
            # Extract basic information
            basic_info = {
                'Name': f"{candidate_dict.get('first_name', '')} {candidate_dict.get('last_name', '')}".strip(),
                'Email': candidate_dict.get('email', ''),
                'Phone': candidate_dict.get('phone_number', ''),
                'Location': candidate_dict.get('location', ''),
                'Personal Summary': candidate_dict.get('personal_summary', ''),
                'Salary Expectation': candidate_dict.get('salary_expectation', ''),
                'Availability (weeks)': candidate_dict.get('availability_weeks', ''),
                'Preferred Work Types': candidate_dict.get('preferred_work_types', ''),
                'Right to Work': candidate_dict.get('right_to_work', ''),
                'Classification Interest': candidate_dict.get('classification_of_interest', ''),
                'Sub-classification Interest': candidate_dict.get('sub_classification_of_interest', '')
            }
            
            # Format career history
            career_history = []
            for career in candidate_dict.get('career_history', []):
                if career.get('is_active', True):  # Only include active records
                    career_str = f"- {career.get('job_title', '')} at {career.get('company_name', '')}"
                    if career.get('start_date'):
                        career_str += f" ({career.get('start_date')} to {career.get('end_date', 'Present')})"
                    if career.get('description'):
                        career_str += f": {career.get('description')}"
                    career_history.append(career_str)
            
            # Format education
            education = []
            for edu in candidate_dict.get('education', []):
                if edu.get('is_active', True):
                    edu_str = f"- {edu.get('degree', '')} in {edu.get('field_of_study', '')} from {edu.get('school', '')}"
                    if edu.get('start_date') or edu.get('end_date'):
                        edu_str += f" ({edu.get('start_date', '')} - {edu.get('end_date', '')})"
                    if edu.get('grade'):
                        edu_str += f", Grade: {edu.get('grade')}"
                    education.append(edu_str)
            
            # Format skills
            skills = [skill.get('skills', '') for skill in candidate_dict.get('skills', []) 
                     if skill.get('is_active', True) and skill.get('skills')]
            
            # Format languages
            languages = []
            for lang in candidate_dict.get('languages', []):
                if lang.get('is_active', True):
                    lang_str = f"{lang.get('language', '')}"
                    if lang.get('proficiency_level'):
                        lang_str += f" ({lang.get('proficiency_level')})"
                    languages.append(lang_str)
            
            # Format certifications
            certifications = []
            for cert in candidate_dict.get('licenses_certifications', []):
                if cert.get('is_active', True):
                    cert_str = f"- {cert.get('name', '')}"
                    if cert.get('issuing_organization'):
                        cert_str += f" from {cert.get('issuing_organization')}"
                    if cert.get('issue_date'):
                        cert_str += f" ({cert.get('issue_date')})"
                    certifications.append(cert_str)
            
            # Compile formatted data
            formatted_data = "CANDIDATE PROFILE:\n\n"
            
            # Basic Information
            formatted_data += "BASIC INFORMATION:\n"
            for key, value in basic_info.items():
                if value:
                    formatted_data += f"{key}: {value}\n"
            
            # Career History
            if career_history:
                formatted_data += "\nCAREER HISTORY:\n"
                formatted_data += "\n".join(career_history) + "\n"
            
            # Education
            if education:
                formatted_data += "\nEDUCATION:\n"
                formatted_data += "\n".join(education) + "\n"
            
            # Skills
            if skills:
                formatted_data += f"\nSKILLS:\n{', '.join(skills)}\n"
            
            # Languages
            if languages:
                formatted_data += f"\nLANGUAGES:\n{', '.join(languages)}\n"
            
            # Certifications
            if certifications:
                formatted_data += "\nCERTIFICATIONS & LICENSES:\n"
                formatted_data += "\n".join(certifications) + "\n"
            
            return formatted_data
            
        except Exception as e:
            print(f"Error formatting candidate data: {str(e)}")
            return str(candidate_dict)  # Fallback to string representation
    
    async def generate_ai_summary(self, candidate_dict: Dict[str, Any]) -> str:
        """
        Generate AI summary for a candidate profile
        
        Args:
            candidate_dict (Dict): Complete candidate profile with relationships
            
        Returns:
            str: Generated AI summary
        """
        try:
            print("Starting AI summary generation...")
            
            # Format the candidate data
            print("Formatting candidate data...")
            formatted_data = self.format_candidate_data(candidate_dict)
            print(f"Formatted data length: {len(formatted_data)} characters")
            
            # Get the active prompt template from database
            print("Fetching active prompt template...")
            prompt_template = self.get_active_prompt_template()
            
            # Create the prompt
            print("Creating prompt from template...")
            prompt = prompt_template.format(candidate_profile_data=formatted_data)
            print(f"Prompt created, length: {len(prompt)} characters")
            
            # Generate summary using LangChain
            print("Calling Azure OpenAI LLM...")
            response = await self.llm.ainvoke(prompt)
            print(f"LLM response received: {type(response)}")
            
            # Extract content from response
            if hasattr(response, 'content'):
                summary = response.content.strip()
            else:
                summary = str(response).strip()
            
            print(f"Generated summary length: {len(summary)} characters")
            
            # Ensure summary is within word limit (approximately)
            words = summary.split()
            if len(words) > 200:
                summary = ' '.join(words[:200]) + '...'
                print(f"Summary truncated to 200 words")
            
            return summary
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error generating AI summary: {str(e)}")
            print(f"AI summary error traceback: {error_traceback}")
            # Return a basic fallback summary
            name = f"{candidate_dict.get('first_name', '')} {candidate_dict.get('last_name', '')}".strip()
            fallback_summary = f"Professional candidate {name} with experience in {candidate_dict.get('classification_of_interest', 'various fields')}. See full profile for detailed information."
            print(f"Returning fallback summary: {fallback_summary}")
            return fallback_summary
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Azure OpenAI
        
        Args:
            text (str): Text to generate embedding for
            
        Returns:
            List[float]: Embedding vector
        """
        try:
            print(f"Starting embedding generation for text length: {len(text)}")
            
            # Generate embedding using LangChain
            print("Calling Azure OpenAI Embeddings...")
            embedding = await self.embeddings.aembed_query(text)
            print(f"Embedding generated successfully, dimension: {len(embedding)}")
            return embedding
            
        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Error generating embedding: {str(e)}")
            print(f"Embedding error traceback: {error_traceback}")
            # Return zero vector as fallback
            print("Returning zero vector as fallback")
            return [0.0] * 1536
    
    async def process_candidate_profile(self, candidate_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Complete processing: generate AI summary and embedding
        
        Args:
            candidate_dict (Dict): Complete candidate profile with relationships
            
        Returns:
            Dict: Contains 'ai_summary' and 'embedding_vector'
        """
        try:
            # Generate AI summary
            ai_summary = await self.generate_ai_summary(candidate_dict)
            
            # Generate embedding from the AI summary
            embedding_vector = await self.generate_embedding(ai_summary)
            
            return {
                'ai_summary': ai_summary,
                'embedding_vector': embedding_vector,
                'processing_success': True
            }
            
        except Exception as e:
            print(f"Error processing candidate profile: {str(e)}")
            return {
                'ai_summary': None,
                'embedding_vector': None,
                'processing_success': False,
                'error': str(e)
            }

# Create a singleton instance
ai_summary_service = CandidateAISummaryService() 