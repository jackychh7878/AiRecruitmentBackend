import os
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from database import db
from models import (
    CandidateMasterProfile, CandidateCareerHistory, CandidateSkills,
    CandidateEducation, CandidateLicensesCertifications, CandidateLanguages,
    CandidateResume
)
from services.resume_parser import get_resume_parser
from services.ai_summary_service import ai_summary_service
from services.candidate_classification_service import candidate_classification_service
import json
import asyncio
from flask import current_app
from werkzeug.datastructures import FileStorage
import tempfile
import logging

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class BatchResumeParserService:
    """
    Service for batch parsing of resumes and creating candidate profiles in parallel
    Handles rate limiting, multi-threading, and progress tracking with metadata
    """
    
    def __init__(self):
        """Initialize the batch resume parser service"""
        # Get rate limiting configuration from environment variables (same as bulk AI)
        self.max_concurrent_workers = int(os.getenv('AI_BULK_MAX_CONCURRENT_WORKERS', 5))
        self.rate_limit_delay = float(os.getenv('AI_BULK_RATE_LIMIT_DELAY_SECONDS', 1.0))
        
        # Job tracking
        self.active_jobs = {}
        self.job_counter = 0
        
        # Store Flask app reference for context management
        self.app = None
        
        logger.info(f"Batch Resume Parser Service initialized:")
        logger.info(f"  Max concurrent workers: {self.max_concurrent_workers}")
        logger.info(f"  Rate limit delay: {self.rate_limit_delay} seconds")
    
    def set_app(self, app):
        """Set the Flask app instance for database operations"""
        self.app = app
        logger.info("Flask app context set for batch resume parser")
    
    def start_batch_parsing(self, validated_files: List[Dict[str, Any]]) -> str:
        """
        Start a new batch parsing job
        
        Args:
            validated_files: List of file dictionaries with 'filename', 'content', 'size' keys
            
        Returns:
            job_id: Unique identifier for tracking the job
        """
        # Generate unique job ID and batch metadata
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        self.job_counter += 1
        job_id = f"batch_parse_{timestamp}_{self.job_counter}"
        batch_number = f"BATCH_{timestamp}_{self.job_counter}"
        batch_upload_datetime = datetime.utcnow().isoformat()
        
        # Initialize job status
        job_status = {
            'job_id': job_id,
            'batch_number': batch_number,
            'status': 'queued',
            'created_at': datetime.utcnow().isoformat(),
            'started_at': None,
            'completed_at': None,
            'total_files': len(validated_files),
            'processed_files': 0,
            'successful_profiles': 0,
            'completed_profiles': 0,  # Complete with all mandatory fields
            'incomplete_profiles': 0,  # Missing some mandatory fields but still created
            'failed_files': 0,
            'ai_summaries_generated': 0,  # Number of candidates with AI summaries
            'ai_summaries_failed': 0,    # Number of candidates where AI processing failed
            'classifications_generated': 0,  # Number of candidates with AI classifications
            'classifications_failed': 0,    # Number of candidates where classification failed
            'progress_percentage': 0.0,
            'processing_time_seconds': 0.0,
            'errors': [],
            'results': []
        }
        
        self.active_jobs[job_id] = job_status
        
        # Start processing in background thread
        thread = threading.Thread(
            target=self._run_batch_parsing,
            args=(job_id, validated_files, batch_number, batch_upload_datetime)
        )
        thread.daemon = True
        thread.start()
        
        logger.info(f"Started batch parsing job {job_id} with {len(validated_files)} files")
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a batch parsing job"""
        try:
            if not job_id:
                logger.warning("get_job_status called with empty job_id")
                return None
            
            if not hasattr(self, 'active_jobs') or self.active_jobs is None:
                logger.error("active_jobs not initialized")
                return None
                
            result = self.active_jobs.get(job_id)
            if result is None:
                logger.info(f"Job {job_id} not found in active_jobs. Available jobs: {list(self.active_jobs.keys())}")
            else:
                logger.debug(f"Found job {job_id} with status: {result.get('status', 'unknown')}")
                
            return result
        except Exception as e:
            logger.error(f"Error in get_job_status for {job_id}: {str(e)}")
            return None
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """Get list of all jobs (active and completed)"""
        return list(self.active_jobs.values())
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job (if possible)"""
        if job_id in self.active_jobs:
            job_status = self.active_jobs[job_id]
            if job_status['status'] in ['queued', 'processing']:
                job_status['status'] = 'cancelled'
                job_status['completed_at'] = datetime.utcnow().isoformat()
                logger.info(f"Cancelled batch parsing job {job_id}")
                return True
        return False
    
    def _run_batch_parsing(self, job_id: str, validated_files: List[Dict[str, Any]], 
                          batch_number: str, batch_upload_datetime: str):
        """
        Run the batch parsing job in a background thread
        """
        # Ensure we have app context for database operations
        if not self.app:
            error_msg = "Flask app not set. Call set_app() before starting jobs."
            job_status = self.active_jobs[job_id]
            job_status['status'] = 'failed'
            job_status['completed_at'] = datetime.utcnow().isoformat()
            job_status['errors'].append(error_msg)
            logger.error(f"ERROR in batch parsing job {job_id}: {error_msg}")
            return
        
        with self.app.app_context():
            job_status = self.active_jobs[job_id]
            
            try:
                logger.info(f"Starting batch resume parsing job: {job_id}")
                job_status['status'] = 'processing'
                job_status['started_at'] = datetime.utcnow().isoformat()
                
                # Process files with rate limiting
                self._process_files_with_rate_limiting(job_id, validated_files, batch_number, batch_upload_datetime)
                
                # Complete job
                job_status['status'] = 'completed'
                job_status['completed_at'] = datetime.utcnow().isoformat()
                job_status['progress_percentage'] = 100.0
                
                logger.info(f"Batch parsing job {job_id} completed:")
                logger.info(f"  Total files: {job_status['total_files']}")
                logger.info(f"  Successful profiles: {job_status['successful_profiles']}")
                logger.info(f"  Completed profiles: {job_status['completed_profiles']}")
                logger.info(f"  Incomplete profiles: {job_status['incomplete_profiles']}")
                logger.info(f"  Failed files: {job_status['failed_files']}")
                logger.info(f"  AI summaries generated: {job_status['ai_summaries_generated']}")
                logger.info(f"  AI summaries failed: {job_status['ai_summaries_failed']}")
                logger.info(f"  Classifications generated: {job_status['classifications_generated']}")
                logger.info(f"  Classifications failed: {job_status['classifications_failed']}")
                
            except Exception as e:
                job_status['status'] = 'failed'
                job_status['completed_at'] = datetime.utcnow().isoformat()
                error_msg = f"Batch parsing job failed: {str(e)}"
                job_status['errors'].append(error_msg)
                logger.error(f"ERROR in batch parsing job {job_id}: {error_msg}")
    
    def _process_files_with_rate_limiting(self, job_id: str, validated_files: List[Dict[str, Any]], 
                                        batch_number: str, batch_upload_datetime: str):
        """
        Process resume files using ThreadPoolExecutor with rate limiting
        """
        job_status = self.active_jobs[job_id]
        start_time = time.time()
        
        # Create temporary files from validated file data
        temp_files = []
        for file_data in validated_files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.write(file_data['content'])
            temp_file.close()
            temp_files.append({
                'temp_path': temp_file.name,
                'original_filename': file_data['filename'],
                'file_size': file_data['size']
            })
        
        # Use ThreadPoolExecutor for controlled concurrency
        with ThreadPoolExecutor(max_workers=self.max_concurrent_workers) as executor:
            # Submit all tasks
            future_to_file = {}
            for file_info in temp_files:
                future = executor.submit(
                    self._process_single_resume, 
                    job_id, file_info, batch_number, batch_upload_datetime
                )
                future_to_file[future] = file_info
            
            # Process completed tasks with rate limiting
            for future in as_completed(future_to_file):
                file_info = future_to_file[future]
                
                try:
                    result = future.result()
                    
                    # Update job status
                    job_status['processed_files'] += 1
                    job_status['results'].append(result)
                    
                    if result['status'] == 'success':
                        job_status['successful_profiles'] += 1
                        if result['profile_status'] == 'completed':
                            job_status['completed_profiles'] += 1
                        else:
                            job_status['incomplete_profiles'] += 1
                        
                        # Track AI summary statistics
                        if result.get('ai_summary_generated', False):
                            job_status['ai_summaries_generated'] += 1
                        else:
                            job_status['ai_summaries_failed'] += 1
                        
                        # Track AI classification statistics
                        if result.get('classification_generated', False):
                            job_status['classifications_generated'] += 1
                        else:
                            job_status['classifications_failed'] += 1
                    else:
                        job_status['failed_files'] += 1
                    
                    # Update progress
                    progress = (job_status['processed_files'] / job_status['total_files']) * 100
                    job_status['progress_percentage'] = round(progress, 1)
                    
                    logger.info(f"Processed file {file_info['original_filename']}: {result['status']}")
                    
                except Exception as e:
                    error_msg = f"Error processing {file_info['original_filename']}: {str(e)}"
                    job_status['errors'].append(error_msg)
                    job_status['failed_files'] += 1
                    job_status['processed_files'] += 1
                    
                    # Update progress
                    progress = (job_status['processed_files'] / job_status['total_files']) * 100
                    job_status['progress_percentage'] = round(progress, 1)
                    
                    logger.error(error_msg)
                
                # Clean up temp file
                try:
                    os.unlink(file_info['temp_path'])
                except:
                    pass
                
                # Apply rate limiting delay
                time.sleep(self.rate_limit_delay)
        
        processing_time = time.time() - start_time
        job_status['processing_time_seconds'] = round(processing_time, 2)
        logger.info(f"Batch processing completed in {processing_time:.2f} seconds")
    
    def _process_single_resume(self, job_id: str, file_info: Dict[str, Any], 
                              batch_number: str, batch_upload_datetime: str) -> Dict[str, Any]:
        """
        Process a single resume file and create candidate profile
        
        Returns:
            Dict containing processing result and metadata
        """
        result = {
            'filename': file_info['original_filename'],
            'file_size': file_info['file_size'],
            'status': 'failed',
            'candidate_id': None,
            'profile_status': None,
            'errors': [],
            'parsing_method': None
        }
        
        # Ensure we have Flask application context for database operations
        # This is critical when running in separate threads
        if not self.app:
            error_msg = "Flask app not set for worker thread"
            result['errors'].append(error_msg)
            logger.error(f"ERROR in worker thread: {error_msg}")
            return result
        
        with self.app.app_context():
            try:
                # Parse the resume
                parser = get_resume_parser()
                result['parsing_method'] = parser.parsing_method
                
                with open(file_info['temp_path'], 'rb') as temp_file:
                    parsed_data = parser.parse_resume(temp_file)
                
                # Check mandatory fields and fill with empty strings if missing
                mandatory_fields = ['first_name', 'last_name', 'email']
                missing_fields = []
                
                for field in mandatory_fields:
                    if not parsed_data.get(field):
                        parsed_data[field] = ""  # Fill with empty string
                        missing_fields.append(field)
                
                # Determine profile status
                profile_status = 'completed' if not missing_fields else 'incomplete'
                result['profile_status'] = profile_status
                
                # Create metadata for tracking
                metadata = {
                    'batch_upload': True,
                    'batch_number': batch_number,
                    'batch_upload_datetime': batch_upload_datetime,
                    'profile_status': profile_status,
                    'missing_mandatory_fields': missing_fields,
                    'parsing_method': parser.parsing_method,
                    'original_filename': file_info['original_filename'],
                    'file_size': file_info['file_size'],
                    'processed_at': datetime.utcnow().isoformat()
                }
                
                # Add metadata to parsed data
                parsed_data['metadata_json'] = metadata
                
                # Perform AI classification for industry and role tags
                try:
                    logger.info(f"Starting AI classification for candidate")
                    
                    # Run AI classification in async context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        classification_result = loop.run_until_complete(
                            candidate_classification_service.classify_candidate(parsed_data)
                        )
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
                    
                    if classification_result.get('classification_success'):
                        # Update parsed data with AI classification
                        if classification_result.get('classification_of_interest'):
                            parsed_data['classification_of_interest'] = classification_result['classification_of_interest']
                        if classification_result.get('sub_classification_of_interest'):
                            parsed_data['sub_classification_of_interest'] = classification_result['sub_classification_of_interest']
                        
                        result['classification_generated'] = True
                        result['classification_reasoning'] = classification_result.get('reasoning', '')
                        logger.info(f"AI classification successful: {classification_result['classification_of_interest']} | {classification_result['sub_classification_of_interest']}")
                    else:
                        result['classification_generated'] = False
                        result['classification_error'] = classification_result.get('error', 'Unknown error')
                        logger.warning(f"AI classification failed: {classification_result.get('error')}")
                        
                except Exception as classification_error:
                    result['classification_generated'] = False
                    result['classification_error'] = str(classification_error)
                    logger.warning(f"AI classification failed: {str(classification_error)}")
                    # Don't fail the whole process if classification fails
                
                # Create candidate profile
                candidate = CandidateMasterProfile(
                    first_name=parsed_data.get('first_name', ''),
                    last_name=parsed_data.get('last_name', ''),
                    chinese_name=parsed_data.get('chinese_name'),
                    email=parsed_data.get('email', ''),
                    location=parsed_data.get('location'),
                    phone_number=parsed_data.get('phone_number'),
                    personal_summary=parsed_data.get('personal_summary'),
                    availability_weeks=parsed_data.get('availability_weeks'),
                    preferred_work_types=parsed_data.get('preferred_work_types'),
                    right_to_work=parsed_data.get('right_to_work', False),
                    salary_expectation=parsed_data.get('salary_expectation'),
                    classification_of_interest=parsed_data.get('classification_of_interest'),
                    sub_classification_of_interest=parsed_data.get('sub_classification_of_interest'),
                    citizenship=parsed_data.get('citizenship'),
                    is_active=True,
                    remarks=f"Created via batch upload - Batch: {batch_number}",
                    metadata_json=metadata
                )
                
                db.session.add(candidate)
                db.session.flush()  # Get the candidate ID
                
                # Create related records following the same pattern as create-from-parsed-data endpoint
                self._create_related_records(candidate.id, parsed_data, metadata)
                
                # Store the original PDF file
                try:
                    with open(file_info['temp_path'], 'rb') as temp_file:
                        pdf_content = temp_file.read()
                    
                    resume_record = CandidateResume(
                        candidate_id=candidate.id,
                        pdf_data=pdf_content,
                        file_name=file_info['original_filename'],
                        file_size=file_info['file_size'],
                        content_type='application/pdf',
                        is_active=True
                    )
                    db.session.add(resume_record)
                except Exception as resume_error:
                    logger.warning(f"Could not store PDF data for candidate {candidate.id}: {resume_error}")
                    # Don't fail the whole process if we can't store the PDF
                
                db.session.commit()
                
                # Generate AI summary and embedding
                try:
                    logger.info(f"Starting AI processing for candidate {candidate.id}")
                    
                    # Get complete candidate data with relationships
                    candidate_with_relationships = candidate.to_dict(include_relationships=True)
                    
                    # Run AI processing in async context
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        ai_processing_result = loop.run_until_complete(
                            ai_summary_service.process_candidate_profile(candidate_with_relationships)
                        )
                    finally:
                        loop.close()
                        asyncio.set_event_loop(None)
                    
                    if ai_processing_result and ai_processing_result.get('processing_success'):
                        # Update candidate with AI summary and embedding
                        candidate.ai_short_summary = ai_processing_result['ai_summary']
                        candidate.embedding_vector = ai_processing_result['embedding_vector']
                        candidate.last_modified_date = datetime.utcnow()
                        db.session.commit()
                        
                        result['ai_summary_generated'] = True
                        logger.info(f"AI summary and embedding generated successfully for candidate {candidate.id}")
                    else:
                        result['ai_summary_generated'] = False
                        result['ai_summary_error'] = ai_processing_result.get('error', 'Unknown error')
                        logger.warning(f"AI processing failed for candidate {candidate.id}: {ai_processing_result.get('error')}")
                        
                except Exception as ai_error:
                    result['ai_summary_generated'] = False
                    result['ai_summary_error'] = str(ai_error)
                    logger.warning(f"AI processing failed for candidate {candidate.id}: {str(ai_error)}")
                    # Don't fail the whole process if AI processing fails
                
                result['status'] = 'success'
                result['candidate_id'] = candidate.id
                
                logger.info(f"Successfully created candidate {candidate.id} from {file_info['original_filename']} (Status: {profile_status})")
                
            except Exception as e:
                db.session.rollback()
                error_msg = f"Failed to process {file_info['original_filename']}: {str(e)}"
                result['errors'].append(error_msg)
                logger.error(error_msg)
        
        return result
    
    def _create_related_records(self, candidate_id: int, parsed_data: Dict[str, Any], metadata: Dict[str, Any]):
        """Create related records for the candidate (career history, skills, education, etc.)"""
        
        # Career History
        career_history = parsed_data.get('career_history', [])
        if career_history:
            for experience in career_history:
                career_record = CandidateCareerHistory(
                     candidate_id=candidate_id,
                     job_title=experience.get('job_title'),
                     company_name=experience.get('company_name'),
                     start_date=self._parse_date(experience.get('start_date')),
                     end_date=self._parse_date(experience.get('end_date')),
                     description=experience.get('job_description', experience.get('description')),
                     is_active=True
                 )
                db.session.add(career_record)
        # Skills
        skills = parsed_data.get('skills', [])
        if skills:
            for skill in skills:
                if isinstance(skill, str):
                    skill_record = CandidateSkills(
                         candidate_id=candidate_id,
                         skills=skill,
                         is_active=True
                    )
                    db.session.add(skill_record)
                elif isinstance(skill, dict):
                    skill_name = skill.get('skill_name', skill.get('name', ''))
                    if skill_name:
                        skill_record = CandidateSkills(
                             candidate_id=candidate_id,
                             skills=skill_name,
                             is_active=True
                        )
                        db.session.add(skill_record)
        # Education
        education = parsed_data.get('education', [])
        if education:
            for edu in education:
                edu_record = CandidateEducation(
                     candidate_id=candidate_id,
                     school=edu.get('institution_name', edu.get('school', '')),
                     degree=edu.get('degree_title', edu.get('degree', '')),
                     field_of_study=edu.get('field_of_study'),
                     start_date=self._parse_date(edu.get('start_date')),
                     end_date=self._parse_date(edu.get('end_date')),
                     grade=edu.get('grade_score', edu.get('grade')),
                     description=edu.get('description'),
                     is_active=True
                )
                db.session.add(edu_record)

        # Licenses & Certifications
        certifications = parsed_data.get('certifications', [])
        if certifications:
            for cert in certifications:
                cert_record = CandidateLicensesCertifications(
                     candidate_id=candidate_id,
                     license_certification_name=cert.get('name', cert.get('license_name', '')),
                     issuing_organisation=cert.get('issuing_organization'),
                     issue_date=self._parse_date(cert.get('issue_date')),
                     expiry_date=self._parse_date(cert.get('expiration_date')),
                     description=cert.get('description'),
                     is_active=True
                )
                db.session.add(cert_record)
         
        # Languages
        languages = parsed_data.get('languages', [])
        if languages:
            for lang in languages:
                if isinstance(lang, str):
                    lang_record = CandidateLanguages(
                         candidate_id=candidate_id,
                         language=lang,
                         is_active=True
                    )
                    db.session.add(lang_record)
                elif isinstance(lang, dict):
                    lang_record = CandidateLanguages(
                         candidate_id=candidate_id,
                         language=lang.get('language', lang.get('name', '')),
                         proficiency_level=lang.get('proficiency_level', lang.get('proficiency', '')),
                         is_active=True
                    )
                    db.session.add(lang_record)

    
    def _parse_date(self, date_string: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_string:
            return None
        
        try:
            # Try common date formats
            date_formats = [
                '%Y-%m-%d',
                '%Y-%m',
                '%Y',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%B %Y',
                '%b %Y'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(str(date_string), fmt)
                except ValueError:
                    continue
            
            return None
        except Exception:
            return None


# Create a global instance for use across the application
batch_resume_parser_service = BatchResumeParserService() 