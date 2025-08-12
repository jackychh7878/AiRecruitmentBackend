import os
import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from database import db
from models import CandidateMasterProfile, AiPromptTemplate
from services.ai_summary_service import ai_summary_service
import json
from flask import current_app

# Load environment variables
load_dotenv()

class BulkAIRegenerationService:
    """
    Service for bulk regeneration of AI summaries and embeddings for all candidate profiles
    Handles rate limiting, multi-threading, and progress tracking
    """
    
    def __init__(self):
        """Initialize the bulk regeneration service"""
        # Get rate limiting configuration from environment variables
        self.max_concurrent_workers = int(os.getenv('AI_BULK_MAX_CONCURRENT_WORKERS', 5))
        self.rate_limit_delay = float(os.getenv('AI_BULK_RATE_LIMIT_DELAY_SECONDS', 1.0))
        
        # Job tracking
        self.active_jobs = {}
        self.job_counter = 0
        
        # Store Flask app reference for context management
        self.app = None
        
        print(f"Bulk AI Regeneration Service initialized:")
        print(f"  Max concurrent workers: {self.max_concurrent_workers}")
        print(f"  Rate limit delay: {self.rate_limit_delay} seconds")
    
    def set_app(self, app):
        """Set Flask app instance for context management"""
        self.app = app
    
    def generate_job_id(self) -> str:
        """Generate a unique job ID"""
        self.job_counter += 1
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"bulk_regen_{timestamp}_{self.job_counter}"
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a specific job"""
        return self.active_jobs.get(job_id)
    
    def get_all_active_jobs(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all active jobs"""
        return self.active_jobs.copy()
    
    def start_bulk_regeneration(self, prompt_template_id: Optional[int] = None, 
                              created_by: str = "system") -> str:
        """
        Start bulk regeneration of AI summaries for all candidate profiles
        
        Args:
            prompt_template_id (int, optional): Specific template ID to activate first
            created_by (str): User who initiated the job
            
        Returns:
            str: Job ID for tracking
        """
        job_id = self.generate_job_id()
        
        # Initialize job status
        job_status = {
            'job_id': job_id,
            'status': 'starting',
            'started_at': datetime.utcnow().isoformat(),
            'created_by': created_by,
            'prompt_template_id': prompt_template_id,
            'total_profiles': 0,
            'processed_profiles': 0,
            'successful_updates': 0,
            'failed_updates': 0,
            'current_profile_id': None,
            'estimated_completion': None,
            'errors': [],
            'completed_at': None
        }
        
        self.active_jobs[job_id] = job_status
        
        # Start background thread
        thread = threading.Thread(
            target=self._run_bulk_regeneration,
            args=(job_id, prompt_template_id),
            daemon=True
        )
        thread.start()
        
        return job_id
    
    def _run_bulk_regeneration(self, job_id: str, prompt_template_id: Optional[int]):
        """
        Main method that runs the bulk regeneration in background
        """
        # Ensure we have app context for database operations
        if not self.app:
            error_msg = "Flask app not set. Call set_app() before starting jobs."
            job_status = self.active_jobs[job_id]
            job_status['status'] = 'failed'
            job_status['completed_at'] = datetime.utcnow().isoformat()
            job_status['errors'].append(error_msg)
            print(f"ERROR in bulk regeneration job {job_id}: {error_msg}")
            return
        
        with self.app.app_context():
            job_status = self.active_jobs[job_id]
            
            try:
                print(f"Starting bulk AI regeneration job: {job_id}")
                
                # Step 1: Activate specific template if provided
                if prompt_template_id:
                    self._activate_template(job_id, prompt_template_id)
                
                # Step 2: Get all candidate profiles
                job_status['status'] = 'fetching_profiles'
                profiles = self._get_all_profiles(job_id)
                
                if not profiles:
                    job_status['status'] = 'completed'
                    job_status['completed_at'] = datetime.utcnow().isoformat()
                    print(f"No profiles found for regeneration. Job {job_id} completed.")
                    return
                
                job_status['total_profiles'] = len(profiles)
                job_status['status'] = 'processing'
                
                print(f"Found {len(profiles)} profiles to process")
                
                # Step 3: Process profiles with rate limiting
                self._process_profiles_with_rate_limiting(job_id, profiles)
                
                # Step 4: Complete job
                job_status['status'] = 'completed'
                job_status['completed_at'] = datetime.utcnow().isoformat()
                
                print(f"Bulk regeneration job {job_id} completed:")
                print(f"  Total profiles: {job_status['total_profiles']}")
                print(f"  Successful updates: {job_status['successful_updates']}")
                print(f"  Failed updates: {job_status['failed_updates']}")
                
            except Exception as e:
                job_status['status'] = 'failed'
                job_status['completed_at'] = datetime.utcnow().isoformat()
                error_msg = f"Job failed with error: {str(e)}"
                job_status['errors'].append(error_msg)
                print(f"ERROR in bulk regeneration job {job_id}: {error_msg}")
    
    def _activate_template(self, job_id: str, template_id: int):
        """Activate a specific prompt template"""
        job_status = self.active_jobs[job_id]
        
        try:
            template = AiPromptTemplate.query.get(template_id)
            if not template:
                raise ValueError(f"Template with ID {template_id} not found")
            
            template.activate()
            print(f"Activated template: {template.name} (ID: {template_id})")
            
        except Exception as e:
            error_msg = f"Failed to activate template {template_id}: {str(e)}"
            job_status['errors'].append(error_msg)
            print(f"WARNING: {error_msg}")
    
    def _get_all_profiles(self, job_id: str) -> List[CandidateMasterProfile]:
        """Get all active candidate profiles"""
        try:
            profiles = CandidateMasterProfile.query.filter_by(is_active=True).all()
            return profiles
        except Exception as e:
            job_status = self.active_jobs[job_id]
            error_msg = f"Failed to fetch profiles: {str(e)}"
            job_status['errors'].append(error_msg)
            raise e
    
    def _process_profiles_with_rate_limiting(self, job_id: str, profiles: List[CandidateMasterProfile]):
        """
        Process profiles using ThreadPoolExecutor with rate limiting
        """
        job_status = self.active_jobs[job_id]
        start_time = time.time()
        
        # Use ThreadPoolExecutor for controlled concurrency
        with ThreadPoolExecutor(max_workers=self.max_concurrent_workers) as executor:
            # Submit all tasks
            future_to_profile = {}
            for profile in profiles:
                future = executor.submit(self._process_single_profile, job_id, profile)
                future_to_profile[future] = profile
            
            # Process completed tasks with rate limiting
            for future in as_completed(future_to_profile):
                profile = future_to_profile[future]
                job_status['current_profile_id'] = profile.id
                
                try:
                    success = future.result()
                    if success:
                        job_status['successful_updates'] += 1
                    else:
                        job_status['failed_updates'] += 1
                        
                except Exception as e:
                    job_status['failed_updates'] += 1
                    error_msg = f"Profile {profile.id}: {str(e)}"
                    job_status['errors'].append(error_msg)
                    print(f"ERROR processing profile {profile.id}: {error_msg}")
                
                job_status['processed_profiles'] += 1
                
                # Calculate estimated completion
                if job_status['processed_profiles'] > 0:
                    elapsed_time = time.time() - start_time
                    avg_time_per_profile = elapsed_time / job_status['processed_profiles']
                    remaining_profiles = job_status['total_profiles'] - job_status['processed_profiles']
                    estimated_seconds = remaining_profiles * avg_time_per_profile
                    estimated_completion = datetime.utcnow().timestamp() + estimated_seconds
                    job_status['estimated_completion'] = datetime.fromtimestamp(estimated_completion).isoformat()
                
                # Progress logging
                if job_status['processed_profiles'] % 10 == 0:
                    print(f"Progress: {job_status['processed_profiles']}/{job_status['total_profiles']} profiles processed")
                
                # Rate limiting delay between processing
                if self.rate_limit_delay > 0:
                    time.sleep(self.rate_limit_delay)
    
    def _process_single_profile(self, job_id: str, profile: CandidateMasterProfile) -> bool:
        """
        Process a single candidate profile - regenerate AI summary and embedding
        
        Args:
            job_id (str): The job ID for tracking
            profile (CandidateMasterProfile): The profile to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Each worker thread needs its own app context
        with self.app.app_context():
            try:
                print(f"Processing profile {profile.id}: {profile.first_name} {profile.last_name}")
                
                # Verify database session is working
                print(f"Database session info: {type(db.session)}")
                print(f"Profile object type: {type(profile)}")
                print(f"Profile ID: {profile.id}")
                
                # Check current values before update
                print(f"Current ai_short_summary: {profile.ai_short_summary[:100] if profile.ai_short_summary else 'None'}...")
                
                # Handle pgvector field properly
                if profile.embedding_vector is not None:
                    try:
                        current_embedding_length = len(profile.embedding_vector)
                        print(f"Current embedding_vector length: {current_embedding_length}")
                    except (TypeError, ValueError):
                        try:
                            current_embedding_length = profile.embedding_vector.size
                            print(f"Current embedding_vector size: {current_embedding_length}")
                        except:
                            print(f"Current embedding_vector present but length unknown")
                else:
                    print(f"Current embedding_vector: None")
                
                # Get complete profile with relationships
                candidate_dict = profile.to_dict(include_relationships=True)
                print(f"Profile dict keys: {list(candidate_dict.keys())}")
                
                # Filter only active relationships
                filtered_dict = self._filter_active_relationships(candidate_dict)
                print(f"Filtered dict keys: {list(filtered_dict.keys())}")
                
                # Create async event loop for AI processing
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
                try:
                    print(f"Starting AI processing for profile {profile.id}")
                    
                    # Generate AI summary and embedding
                    result = loop.run_until_complete(
                        ai_summary_service.process_candidate_profile(filtered_dict)
                    )
                    
                    print(f"AI processing result for profile {profile.id}: success={result.get('processing_success')}")
                    
                    if result.get('processing_success', False):
                        # Update the profile in database
                        ai_summary = result.get('ai_summary')
                        embedding_vector = result.get('embedding_vector')
                        
                        print(f"AI summary length: {len(ai_summary) if ai_summary else 0}")
                        
                        # Handle embedding vector length safely
                        if embedding_vector:
                            print(f"Embedding vector length: {len(embedding_vector)}")
                        else:
                            print(f"Embedding vector: None")
                        
                        # Check if we have valid data to update
                        if not ai_summary and not embedding_vector:
                            print(f"⚠️ No AI summary or embedding generated for profile {profile.id}")
                            return False
                        
                        # Use a fresh database session for this update
                        # Get a fresh reference to the profile
                        fresh_profile = db.session.get(CandidateMasterProfile, profile.id)
                        if not fresh_profile:
                            print(f"❌ Could not get fresh profile {profile.id} from database")
                            return False
                        
                        # Update the fresh profile object
                        update_made = False
                        
                        if ai_summary:
                            old_summary = fresh_profile.ai_short_summary
                            fresh_profile.ai_short_summary = ai_summary
                            print(f"Set ai_short_summary for profile {fresh_profile.id}")
                            print(f"  Old: {old_summary[:100] if old_summary else 'None'}...")
                            print(f"  New: {ai_summary[:100]}...")
                            update_made = True
                        
                        if embedding_vector:
                            old_embedding = fresh_profile.embedding_vector
                            fresh_profile.embedding_vector = embedding_vector
                            print(f"Set embedding_vector for profile {fresh_profile.id}")
                            
                            # Handle old embedding length safely
                            if old_embedding is not None:
                                try:
                                    old_length = len(old_embedding)
                                    print(f"  Old length: {old_length}")
                                except (TypeError, ValueError):
                                    try:
                                        old_length = old_embedding.size
                                        print(f"  Old size: {old_length}")
                                    except:
                                        print(f"  Old embedding present but length unknown")
                            else:
                                print(f"  Old embedding: None")
                            
                            print(f"  New length: {len(embedding_vector)}")
                            update_made = True
                        
                        if update_made:
                            # Update modification time
                            fresh_profile.last_modified_date = datetime.utcnow()
                            print(f"Updated last_modified_date for profile {fresh_profile.id}")
                            
                            # Check if SQLAlchemy detects changes
                            print(f"SQLAlchemy dirty objects: {db.session.dirty}")
                            print(f"SQLAlchemy new objects: {db.session.new}")
                            
                            # Commit changes
                            try:
                                db.session.commit()
                                print(f"✅ Successfully committed changes for profile {fresh_profile.id}")
                                
                                # Verify the update by refreshing the object
                                db.session.refresh(fresh_profile)
                                print(f"✅ Verified update - ai_short_summary: {fresh_profile.ai_short_summary[:100] if fresh_profile.ai_short_summary else 'None'}...")
                                
                                # Handle pgvector field properly (it's a numpy array)
                                if fresh_profile.embedding_vector is not None:
                                    try:
                                        embedding_length = len(fresh_profile.embedding_vector)
                                        print(f"✅ Verified update - embedding_vector length: {embedding_length}")
                                    except (TypeError, ValueError):
                                        # If it's a numpy array, use .size or .shape
                                        try:
                                            embedding_length = fresh_profile.embedding_vector.size
                                            print(f"✅ Verified update - embedding_vector size: {embedding_length}")
                                        except:
                                            print(f"✅ Verified update - embedding_vector present but length unknown")
                                else:
                                    print(f"✅ Verified update - embedding_vector: None")
                                
                                return True
                            except Exception as commit_error:
                                print(f"❌ Commit failed for profile {fresh_profile.id}: {str(commit_error)}")
                                import traceback
                                print(f"Commit error traceback: {traceback.format_exc()}")
                                db.session.rollback()
                                return False
                        else:
                            print(f"⚠️ No updates made for profile {fresh_profile.id}")
                            return False
                    else:
                        error_msg = result.get('error', 'Unknown error')
                        print(f"AI processing failed for profile {profile.id}: {error_msg}")
                        return False
                        
                finally:
                    loop.close()
                    asyncio.set_event_loop(None)
                    
            except Exception as e:
                import traceback
                error_traceback = traceback.format_exc()
                print(f"Error processing profile {profile.id}: {str(e)}")
                print(f"Error traceback: {error_traceback}")
                try:
                    db.session.rollback()
                    print(f"Rolled back database session for profile {profile.id}")
                except:
                    pass
                return False
    
    def _filter_active_relationships(self, candidate_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Filter out inactive relationships from candidate data"""
        filtered_dict = candidate_dict.copy()
        
        # Filter each relationship type to include only active records
        relationship_fields = [
            'career_history', 'skills', 'education', 
            'licenses_certifications', 'languages', 'resumes'
        ]
        
        for field in relationship_fields:
            if field in filtered_dict and isinstance(filtered_dict[field], list):
                filtered_dict[field] = [
                    item for item in filtered_dict[field] 
                    if item.get('is_active', True)
                ]
        
        return filtered_dict
    
    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job (if possible)
        Note: Once threads are running, they can't be forcefully stopped,
        but we can mark the job as cancelled
        """
        if job_id in self.active_jobs:
            job_status = self.active_jobs[job_id]
            if job_status['status'] in ['starting', 'fetching_profiles', 'processing']:
                job_status['status'] = 'cancelled'
                job_status['completed_at'] = datetime.utcnow().isoformat()
                return True
        return False
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Clean up completed jobs older than specified hours"""
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        jobs_to_remove = []
        for job_id, job_status in self.active_jobs.items():
            if job_status['status'] in ['completed', 'failed', 'cancelled']:
                if job_status.get('completed_at'):
                    completed_time = datetime.fromisoformat(job_status['completed_at']).timestamp()
                    if completed_time < cutoff_time:
                        jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
        
        print(f"Cleaned up {len(jobs_to_remove)} old jobs")

# Global instance
bulk_ai_regeneration_service = BulkAIRegenerationService() 