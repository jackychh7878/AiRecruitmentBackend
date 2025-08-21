import os
import asyncio
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
import json
import logging
from database import db
from models import AiRecruitmentComCode

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class CandidateClassificationService:
    """
    Service for automatically classifying candidates based on their resume content
    using AI analysis and predefined lookup data
    """
    
    def __init__(self):
        """Initialize the classification service with Azure OpenAI"""
        try:
            # Check for required environment variables
            required_env_vars = ['AZURE_OPENAI_ENDPOINT', 'AZURE_OPENAI_API_KEY']
            missing_vars = [var for var in required_env_vars if not os.getenv(var)]
            
            if missing_vars:
                raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
            logger.info("Initializing Azure OpenAI for classification...")
            self.llm = AzureChatOpenAI(
                azure_endpoint=os.getenv('AZURE_OPENAI_ENDPOINT'),
                api_version=os.getenv('AZURE_API_VERSION', '2024-02-15-preview'),
                azure_deployment=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini'),
                api_key=os.getenv('AZURE_OPENAI_API_KEY'),
                temperature=0.1,  # Low temperature for consistent classification
                max_tokens=500
            )
            logger.info("Classification service initialized successfully")
            
            # Cache for lookup data to avoid repeated DB queries
            self._classifications_cache = None
            self._sub_classifications_cache = None
            
        except Exception as e:
            logger.error(f"Failed to initialize classification service: {str(e)}")
            raise
    
    def _get_available_classifications(self) -> List[Dict[str, str]]:
        """Get all available classifications from lookup data"""
        if self._classifications_cache is None:
            try:
                records = AiRecruitmentComCode.query.filter_by(
                    category='Classification of interest',
                    is_active=True
                ).order_by(AiRecruitmentComCode.com_code).all()
                
                self._classifications_cache = [
                    {
                        'code': record.com_code,
                        'description': record.description or record.com_code
                    }
                    for record in records
                ]
                logger.info(f"Loaded {len(self._classifications_cache)} classification options")
            except Exception as e:
                logger.error(f"Error loading classifications: {str(e)}")
                self._classifications_cache = []
        
        return self._classifications_cache
    
    def _get_available_sub_classifications(self) -> List[Dict[str, str]]:
        """Get all available sub-classifications from lookup data"""
        if self._sub_classifications_cache is None:
            try:
                records = AiRecruitmentComCode.query.filter_by(
                    category='Sub classification of interest',
                    is_active=True
                ).order_by(AiRecruitmentComCode.com_code).all()
                
                self._sub_classifications_cache = [
                    {
                        'code': record.com_code,
                        'description': record.description or record.com_code
                    }
                    for record in records
                ]
                logger.info(f"Loaded {len(self._sub_classifications_cache)} sub-classification options")
            except Exception as e:
                logger.error(f"Error loading sub-classifications: {str(e)}")
                self._sub_classifications_cache = []
        
        return self._sub_classifications_cache
    
    def _create_classification_prompt(self, candidate_data: Dict[str, Any]) -> str:
        """Create a prompt for AI classification"""
        
        # Extract relevant information from candidate data
        work_experience = candidate_data.get('career_history', [])
        skills = candidate_data.get('skills', [])
        education = candidate_data.get('education', [])
        personal_summary = candidate_data.get('personal_summary', '')
        
        # Format work experience
        experience_text = ""
        for exp in work_experience:
            title = exp.get('job_title', exp.get('title', ''))
            company = exp.get('company_name', exp.get('company', ''))
            description = exp.get('job_description', exp.get('description', ''))
            if title or company:
                experience_text += f"- {title} at {company}: {description}\n"
        
        # Format skills
        skills_text = ""
        if isinstance(skills, list):
            skills_text = ", ".join([
                skill if isinstance(skill, str) else skill.get('skill_name', skill.get('name', ''))
                for skill in skills if skill
            ])
        
        # Format education
        education_text = ""
        for edu in education:
            degree = edu.get('degree_title', edu.get('degree', ''))
            school = edu.get('institution_name', edu.get('school', ''))
            field = edu.get('field_of_study', '')
            if degree or school:
                education_text += f"- {degree} in {field} from {school}\n"
        
        # Get available options
        classifications = self._get_available_classifications()
        sub_classifications = self._get_available_sub_classifications()
        
        # Create the prompt
        prompt = f"""
You are an HR expert specializing in candidate classification. Analyze the following candidate profile and classify them into the most appropriate industry classification and role tags.

CANDIDATE PROFILE:
Personal Summary: {personal_summary}

Work Experience:
{experience_text}

Skills: {skills_text}

Education:
{education_text}

AVAILABLE INDUSTRY CLASSIFICATIONS (code: definition):
{chr(10).join([f"- {item['code']}: {item['description']}" for item in classifications[:20]])}  

AVAILABLE ROLE TAGS (code: definition):
{chr(10).join([f"- {item['code']}: {item['description']}" for item in sub_classifications])}

CLASSIFICATION GUIDELINES:
1. INDUSTRY CLASSIFICATION: Choose the SINGLE most appropriate industry from the list above based on the candidate's work experience and career focus
2. ROLE TAGS: Choose 1-3 specific role tags that best match the candidate's actual job functions and skills
   - Focus on what they DO, not just their job title
   - Consider their technical skills, responsibilities, and experience level
   - Prioritize based on most recent/relevant experience
   - For example: A "Senior Software Engineer" who builds web applications and manages databases might be tagged as "Developer/Programmer, Database Development & Administration"
3. ACCURACY: Only use exact codes from the provided lists above - do not create new codes
4. RELEVANCE: Match role tags to actual work performed, not just job titles

Return your response in this exact JSON format:
{{
    "classification_of_interest": "EXACT_CODE_FROM_LIST",
    "sub_classification_of_interest": ["ROLE_TAG_1", "ROLE_TAG_2"],
    "reasoning": "Brief explanation of why these classifications were chosen based on candidate's actual work and skills"
}}

Do not include any text outside the JSON response.
"""
        return prompt
    
    async def classify_candidate(self, candidate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Classify a candidate based on their profile data
        
        Args:
            candidate_data: Dictionary containing candidate profile information
            
        Returns:
            Dictionary with classification results
        """
        try:
            logger.info("Starting AI classification for candidate")
            
            # Create the classification prompt
            prompt = self._create_classification_prompt(candidate_data)
            
            # Get AI classification
            logger.info("Calling Azure OpenAI for classification...")
            response = await self.llm.ainvoke(prompt)
            
            # Extract content from response
            if hasattr(response, 'content'):
                content = response.content.strip()
            else:
                content = str(response).strip()
            
            logger.info(f"AI response: {content}")
            
            # Parse JSON response - handle markdown code blocks
            try:
                # Remove markdown code block formatting if present
                if content.startswith('```json'):
                    # Extract content between ```json and ```
                    start_marker = '```json'
                    end_marker = '```'
                    start_index = content.find(start_marker) + len(start_marker)
                    end_index = content.rfind(end_marker)
                    if end_index > start_index:
                        content = content[start_index:end_index].strip()
                elif content.startswith('```'):
                    # Extract content between ``` and ```
                    lines = content.split('\n')
                    if len(lines) > 2 and lines[0].startswith('```') and lines[-1].startswith('```'):
                        content = '\n'.join(lines[1:-1]).strip()
                
                classification_result = json.loads(content)
                
                # Validate the classification exists
                classifications = self._get_available_classifications()
                classification_codes = [c['code'] for c in classifications]
                
                selected_classification = classification_result.get('classification_of_interest')
                if selected_classification not in classification_codes:
                    logger.warning(f"AI selected invalid classification: {selected_classification}")
                    selected_classification = None
                
                # Validate sub-classifications
                sub_classifications = self._get_available_sub_classifications()
                sub_classification_codes = [c['code'] for c in sub_classifications]
                
                selected_sub_classifications = classification_result.get('sub_classification_of_interest', [])
                if isinstance(selected_sub_classifications, str):
                    selected_sub_classifications = [selected_sub_classifications]
                
                valid_sub_classifications = [
                    sc for sc in selected_sub_classifications 
                    if sc in sub_classification_codes
                ]
                
                if len(valid_sub_classifications) != len(selected_sub_classifications):
                    logger.warning(f"Some AI selected sub-classifications were invalid")
                
                # Format sub-classifications as comma-separated string
                sub_classification_string = ", ".join(valid_sub_classifications) if valid_sub_classifications else None
                
                return {
                    'classification_of_interest': selected_classification,
                    'sub_classification_of_interest': sub_classification_string,
                    'reasoning': classification_result.get('reasoning', ''),
                    'classification_success': True,
                    'ai_confidence': 'high' if selected_classification and valid_sub_classifications else 'low'
                }
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse AI response as JSON: {str(e)}")
                logger.error(f"AI response was: {content}")
                return {
                    'classification_of_interest': None,
                    'sub_classification_of_interest': None,
                    'reasoning': 'Failed to parse AI response',
                    'classification_success': False,
                    'error': f'JSON parsing error: {str(e)}'
                }
            
        except Exception as e:
            logger.error(f"Error in AI classification: {str(e)}")
            return {
                'classification_of_interest': None,
                'sub_classification_of_interest': None,
                'reasoning': 'Classification failed due to error',
                'classification_success': False,
                'error': str(e)
            }
    
    def get_classification_statistics(self) -> Dict[str, Any]:
        """Get statistics about available classifications"""
        classifications = self._get_available_classifications()
        sub_classifications = self._get_available_sub_classifications()
        
        return {
            'total_classifications': len(classifications),
            'total_sub_classifications': len(sub_classifications),
            'classification_options': [c['code'] for c in classifications[:10]],  # First 10 for preview
            'sub_classification_options': [c['code'] for c in sub_classifications[:10]]  # First 10 for preview
        }

# Create a singleton instance
candidate_classification_service = CandidateClassificationService() 