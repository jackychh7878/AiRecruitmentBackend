import os
from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import (
    CandidateMasterProfile, CandidateCareerHistory, CandidateSkills,
    CandidateEducation, CandidateLicensesCertifications, CandidateLanguages,
    CandidateResume, AiPromptTemplate, BatchJobStatus, BatchJobFailedFile
)
from datetime import datetime
import json
from werkzeug.datastructures import FileStorage
from services.resume_parser import resume_parser, reset_resume_parser
from services.ai_summary_service import ai_summary_service
from services.bulk_ai_regeneration_service import bulk_ai_regeneration_service
from services.semantic_search_service import semantic_search_service
from services.batch_resume_parser import batch_resume_parser_service
from flask import current_app
import logging

# Create namespace
candidate_profile_ns = Namespace('candidates', description='Candidate profile operations')

# Set up logging
logger = logging.getLogger(__name__)

# Define relationship models first
career_history_model = candidate_profile_ns.model('CareerHistory', {
    'id': fields.Integer(readonly=True, description='Career history ID'),
    'candidate_id': fields.Integer(description='Candidate ID'),
    'job_title': fields.String(description='Job title'),
    'company_name': fields.String(description='Company name'),
    'start_date': fields.String(description='Start date'),
    'end_date': fields.String(description='End date'),
    'description': fields.String(description='Job description'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

skills_model = candidate_profile_ns.model('Skills', {
    'id': fields.Integer(readonly=True, description='Skill ID'),
    'candidate_id': fields.Integer(description='Candidate ID'),
    'career_history_id': fields.Integer(description='Career history ID'),
    'skills': fields.String(description='Skills'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

education_model = candidate_profile_ns.model('Education', {
    'id': fields.Integer(readonly=True, description='Education ID'),
    'candidate_id': fields.Integer(description='Candidate ID'),
    'school': fields.String(description='School name'),
    'degree': fields.String(description='Degree'),
    'field_of_study': fields.String(description='Field of study'),
    'start_date': fields.String(description='Start date'),
    'end_date': fields.String(description='End date'),
    'grade': fields.String(description='Grade'),
    'description': fields.String(description='Description'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

licenses_certifications_model = candidate_profile_ns.model('LicensesCertifications', {
    'id': fields.Integer(readonly=True, description='License/Certification ID'),
    'candidate_id': fields.Integer(description='Candidate ID'),
    'name': fields.String(description='License/Certification name'),
    'issuing_organization': fields.String(description='Issuing organization'),
    'issue_date': fields.String(description='Issue date'),
    'expiration_date': fields.String(description='Expiration date'),
    'credential_id': fields.String(description='Credential ID'),
    'credential_url': fields.String(description='Credential URL'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

languages_model = candidate_profile_ns.model('Languages', {
    'id': fields.Integer(readonly=True, description='Language ID'),
    'candidate_id': fields.Integer(description='Candidate ID'),
    'language': fields.String(description='Language'),
    'proficiency_level': fields.String(description='Proficiency level'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

resumes_model = candidate_profile_ns.model('Resumes', {
    'id': fields.Integer(readonly=True, description='Resume ID'),
    'candidate_id': fields.Integer(description='Candidate ID'),
    'file_name': fields.String(description='File name'),
    'file_size': fields.Integer(description='File size'),
    'content_type': fields.String(description='MIME type of the file'),
    'upload_date': fields.DateTime(description='Upload date'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

# Define semantic search models
semantic_search_request_model = candidate_profile_ns.model('SemanticSearchRequest', {
    'query': fields.String(required=True, description='Natural language search query'),
    'confidence_threshold': fields.Float(description='Minimum similarity score (0.0 to 1.0, default: 0.7)'),
    'max_results': fields.Integer(description='Maximum number of results (default: 50)'),
    'include_relationships': fields.Boolean(description='Whether to include relationship data (default: false)')
})

semantic_search_result_model = candidate_profile_ns.model('SemanticSearchResult', {
    'id': fields.Integer(readonly=True, description='Candidate ID'),
    'first_name': fields.String(description='First name'),
    'last_name': fields.String(description='Last name'),
    'chinese_name': fields.String(description='Chinese name'),
    'email': fields.String(description='Email address'),
    'location': fields.String(description='Location'),
    'phone_number': fields.String(description='Phone number'),
    'personal_summary': fields.String(description='Personal summary'),
    'availability_weeks': fields.Integer(description='Availability in weeks'),
    'preferred_work_types': fields.String(description='Preferred work types'),
    'right_to_work': fields.Boolean(description='Right to work status'),
    'salary_expectation': fields.Float(description='Salary expectation'),
    'classification_of_interest': fields.String(description='Classification of interest'),
    'sub_classification_of_interest': fields.String(description='Sub-classification of interest'),
    'citizenship': fields.String(description='Citizenship/visa status'),
    'is_active': fields.Boolean(description='Is active'),
    'remarks': fields.String(description='Remarks'),
    'ai_short_summary': fields.String(description='AI-generated summary'),
    'created_date': fields.DateTime(description='Creation date'),
    'last_modified_date': fields.DateTime(description='Last modification date'),
    'semantic_score': fields.Float(description='Semantic similarity score (0.0 to 1.0)'),
    'keyword_score': fields.Float(description='Keyword matching score (0.0 to 1.0)'),
    'hybrid_score': fields.Float(description='Final hybrid relevance score (0.0 to 1.0)'),
    'confidence_level': fields.String(description='Confidence level description'),
    'relevance_percentage': fields.Float(description='Relevance percentage'),
    'scoring_breakdown': fields.Raw(description='Detailed scoring breakdown with weights and contributions'),
    'career_history': fields.List(fields.Nested(career_history_model), description='Career history'),
    'skills': fields.List(fields.Nested(skills_model), description='Skills'),
    'education': fields.List(fields.Nested(education_model), description='Education'),
    'licenses_certifications': fields.List(fields.Nested(licenses_certifications_model), description='Licenses and certifications'),
    'languages': fields.List(fields.Nested(languages_model), description='Languages'),
    'resumes': fields.List(fields.Nested(resumes_model), description='Resumes')
})

semantic_search_response_model = candidate_profile_ns.model('SemanticSearchResponse', {
    'success': fields.Boolean(description='Whether the search was successful'),
    'results': fields.List(fields.Nested(semantic_search_result_model), description='Search results'),
    'total_found': fields.Integer(description='Total number of candidates found'),
    'query': fields.String(description='Original search query'),
    'confidence_threshold': fields.Float(description='Confidence threshold used'),
    'query_embedding_dimension': fields.Integer(description='Dimension of query embedding vector'),
    'error': fields.String(description='Error message if search failed')
})

search_statistics_model = candidate_profile_ns.model('SearchStatistics', {
    'total_active_candidates': fields.Integer(description='Total number of active candidates'),
    'candidates_with_embeddings': fields.Integer(description='Number of candidates with embeddings'),
    'candidates_without_embeddings': fields.Integer(description='Number of candidates without embeddings'),
    'embedding_coverage_percentage': fields.Float(description='Percentage of candidates with embeddings'),
    'default_confidence_threshold': fields.Float(description='Default confidence threshold'),
    'max_results_limit': fields.Integer(description='Maximum results limit'),
    'hybrid_scoring': fields.Raw(description='Hybrid scoring configuration and formula'),
    'error': fields.String(description='Error message if failed to get statistics')
})

# Define data models for Swagger documentation
candidate_model = candidate_profile_ns.model('Candidate', {
    'id': fields.Integer(readonly=True, description='Candidate ID'),
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
    'chinese_name': fields.String(description='Chinese name'),
    'email': fields.String(required=True, description='Email address'),
    'location': fields.String(description='Location'),
    'phone_number': fields.String(description='Phone number'),
    'personal_summary': fields.String(description='Personal summary'),
    'availability_weeks': fields.Integer(description='Availability in weeks'),
    'preferred_work_types': fields.String(description='Preferred work types'),
    'right_to_work': fields.Boolean(description='Right to work'),
    'salary_expectation': fields.Float(description='Salary expectation'),
    'classification_of_interest': fields.String(description='Classification of interest'),
    'sub_classification_of_interest': fields.String(description='Sub-classification of interest'),
    'citizenship': fields.String(description='Citizenship/visa status'),
    'is_active': fields.Boolean(description='Is active'),
    'remarks': fields.String(description='Remarks'),
    'ai_short_summary': fields.String(description='AI generated short summary'),
    'metadata_json': fields.Raw(description='Additional metadata'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date'),
    # Relationship fields
    'career_history': fields.List(fields.Nested(career_history_model), description='Career history'),
    'skills': fields.List(fields.Nested(skills_model), description='Skills'),
    'education': fields.List(fields.Nested(education_model), description='Education'),
    'licenses_certifications': fields.List(fields.Nested(licenses_certifications_model), description='Licenses and certifications'),
    'languages': fields.List(fields.Nested(languages_model), description='Languages'),
    'resumes': fields.List(fields.Nested(resumes_model), description='Resumes')
})

# Resume upload model for Swagger documentation
resume_upload_parser = candidate_profile_ns.parser()
resume_upload_parser.add_argument('resume_file', 
                                 location='files',
                                 type=FileStorage,
                                 required=True,
                                 help='PDF resume file to parse')
resume_upload_parser.add_argument('enable_ai_classification',
                                 location='form',
                                 type=bool,
                                 default=True,
                                 help='Enable AI-powered industry and role classification (default: true)')

resume_parse_response_model = candidate_profile_ns.model('ResumeParseResponse', {
    'success': fields.Boolean(description='Whether parsing was successful'),
    'message': fields.String(description='Status message'),
    'candidate_data': fields.Nested(candidate_model, description='Parsed candidate information'),
    'parsing_stats': fields.Raw(description='Statistics about the parsing process')
})

# Bulk candidate creation model (matches the output from resume parser)
candidate_bulk_create_model = candidate_profile_ns.model('CandidateBulkCreate', {
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
    'chinese_name': fields.String(description='Chinese name'),
    'email': fields.String(required=True, description='Email address'),
    'location': fields.String(description='Location'),
    'phone_number': fields.String(description='Phone number'),
    'personal_summary': fields.String(description='Personal summary'),
    'availability_weeks': fields.Integer(description='Availability in weeks'),
    'preferred_work_types': fields.String(description='Preferred work types'),
    'right_to_work': fields.Boolean(description='Right to work'),
    'salary_expectation': fields.Float(description='Salary expectation'),
    'classification_of_interest': fields.String(description='Classification of interest'),
    'sub_classification_of_interest': fields.String(description='Sub-classification of interest'),
    'citizenship': fields.String(description='Citizenship/visa status'),
    'is_active': fields.Boolean(description='Is active', default=True),
    # Relationship data
    'career_history': fields.List(fields.Nested(career_history_model), description='Career history records'),
    'skills': fields.List(fields.Nested(skills_model), description='Skills records'),
    'education': fields.List(fields.Nested(education_model), description='Education records'),
    'licenses_certifications': fields.List(fields.Nested(licenses_certifications_model), description='Licenses and certifications'),
    'languages': fields.List(fields.Nested(languages_model), description='Languages'),
    'resumes': fields.List(fields.Nested(resumes_model), description='Resume files'),
    'resume_file': fields.Raw(description='PDF file data (base64 encoded) for direct upload')
})

candidate_bulk_create_response_model = candidate_profile_ns.model('CandidateBulkCreateResponse', {
    'success': fields.Boolean(description='Whether creation was successful'),
    'message': fields.String(description='Status message'),
    'candidate': fields.Nested(candidate_model, description='Created candidate with all relationships'),
    'creation_stats': fields.Raw(description='Statistics about the creation process')
})

candidate_input_model = candidate_profile_ns.model('CandidateInput', {
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
    'chinese_name': fields.String(description='Chinese name'),
    'email': fields.String(required=True, description='Email address'),
    'location': fields.String(description='Location'),
    'phone_number': fields.String(description='Phone number'),
    'personal_summary': fields.String(description='Personal summary'),
    'availability_weeks': fields.Integer(description='Availability in weeks'),
    'preferred_work_types': fields.String(description='Preferred work types'),
    'right_to_work': fields.Boolean(description='Right to work'),
    'salary_expectation': fields.Float(description='Salary expectation'),
    'classification_of_interest': fields.String(description='Classification of interest'),
    'sub_classification_of_interest': fields.String(description='Sub-classification of interest'),
    'citizenship': fields.String(description='Citizenship/visa status'),
    'remarks': fields.String(description='Remarks'),
    'ai_short_summary': fields.String(description='AI generated short summary'),
    'metadata_json': fields.Raw(description='Additional metadata')
})

candidate_list_model = candidate_profile_ns.model('CandidateList', {
    'candidates': fields.List(fields.Nested(candidate_model)),
    'total': fields.Integer(description='Total number of candidates'),
    'pages': fields.Integer(description='Total number of pages'),
    'current_page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page')
})

# Batch resume parsing models
batch_parse_response_model = candidate_profile_ns.model('BatchParseResponse', {
    'success': fields.Boolean(description='Whether batch parsing was started successfully'),
    'message': fields.String(description='Status message'),
    'job_id': fields.String(description='Unique identifier for the batch job'),
    'batch_number': fields.String(description='Unique batch number for tracking'),
    'total_files': fields.Integer(description='Total number of files submitted for parsing')
})

batch_job_status_model = candidate_profile_ns.model('BatchJobStatus', {
    'job_id': fields.String(description='Job identifier'),
    'batch_number': fields.String(description='Batch number'),
    'batch_upload_datetime': fields.String(description='When the batch was uploaded'),
    'status': fields.String(description='Job status (starting, processing, completed, failed, cancelled)'),
    'created_at': fields.String(description='When the job was created'),
    'started_at': fields.String(description='When processing started'),
    'completed_at': fields.String(description='When processing completed'),
    'total_files': fields.Integer(description='Total number of files'),
    'processed_files': fields.Integer(description='Number of files processed'),
    'successful_profiles': fields.Integer(description='Number of successfully created profiles'),
    'completed_profiles': fields.Integer(description='Number of profiles with all mandatory fields'),
    'incomplete_profiles': fields.Integer(description='Number of profiles missing mandatory fields'),
    'failed_files': fields.Integer(description='Number of files that failed to process'),
    'ai_summaries_generated': fields.Integer(description='Number of candidates with AI summaries generated'),
    'ai_summaries_failed': fields.Integer(description='Number of candidates where AI processing failed'),
    'classifications_generated': fields.Integer(description='Number of candidates with AI classifications generated'),
    'classifications_failed': fields.Integer(description='Number of candidates where AI classification failed'),
    'progress_percentage': fields.Float(description='Progress percentage (0-100)'),
    'processing_time_seconds': fields.Float(description='Total processing time in seconds'),
    'errors': fields.List(fields.String, description='List of error messages'),
    'results': fields.List(fields.Raw, description='Detailed results for each file')
})

# Batch upload parser for multiple files
# Note: Swagger UI has limitations with multiple file uploads using action='append'
# We'll define individual file arguments for better Swagger UI support
batch_upload_parser = candidate_profile_ns.parser()
batch_upload_parser.add_argument('resume_files', 
                                location='files',
                                type=FileStorage,
                                required=True,
                                action='append',
                                help='Multiple PDF resume files to parse (select multiple files)')

# Alternative parser for better Swagger UI compatibility
# Supporting up to 20 files for more practical batch testing
swagger_batch_upload_parser = candidate_profile_ns.parser()

# Generate file fields dynamically for better maintainability
def create_swagger_file_fields():
    """Create file fields for Swagger UI dynamically"""
    max_swagger_files = 20  # Reasonable limit for Swagger UI testing
    
    for i in range(1, max_swagger_files + 1):
        field_name = f'file{i}'
        is_required = (i == 1)  # Only first file is required
        help_text = f'PDF resume file #{i}' + (' (required)' if is_required else ' (optional)')
        
        swagger_batch_upload_parser.add_argument(
            field_name,
            location='files',
            type=FileStorage,
            required=is_required,
            help=help_text
        )

# Create the file fields
create_swagger_file_fields()

@candidate_profile_ns.route('/')
class CandidateList(Resource):
    @candidate_profile_ns.doc('get_all_candidates')
    @candidate_profile_ns.param('page', 'Page number', type=int, default=1)
    @candidate_profile_ns.param('per_page', 'Items per page', type=int, default=10)
    @candidate_profile_ns.param('is_active', 'Filter by active status (if not specified, shows all with active first)', type=bool)
    @candidate_profile_ns.param('search', 'Search by name, chinese name, email, classification, or sub-classification tags (partial match)')
    @candidate_profile_ns.param('classification', 'Filter by classification')
    @candidate_profile_ns.param('sub_classification', 'Filter by sub-classification tags (comma-separated)')
    @candidate_profile_ns.param('location', 'Filter by location')
    @candidate_profile_ns.param('citizenship', 'Filter by citizenship/visa status')
    @candidate_profile_ns.param('include_relationships', 'Include related data', type=bool, default=False)
    def get(self):
        """Get all candidates with optional filtering and search including Chinese names (active candidates sorted first)"""
        try:
            # Query parameters for filtering
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            is_active = request.args.get('is_active', type=bool)
            search = request.args.get('search', '').strip()
            classification = request.args.get('classification')
            sub_classification = request.args.get('sub_classification')
            location = request.args.get('location')
            citizenship = request.args.get('citizenship')
            include_relationships = request.args.get('include_relationships', 'false').lower() == 'true'
            
            # Build query - show all candidates but sort active first
            query = CandidateMasterProfile.query
            
            # Filter by active status if specified
            if is_active is not None:
                query = query.filter(CandidateMasterProfile.is_active == is_active)
            
            # Comprehensive search across multiple fields
            if search:
                search_term = f'%{search}%'
                search_conditions = [
                    CandidateMasterProfile.first_name.ilike(search_term),
                    CandidateMasterProfile.last_name.ilike(search_term),
                    CandidateMasterProfile.chinese_name.ilike(search_term),
                    CandidateMasterProfile.email.ilike(search_term),
                    CandidateMasterProfile.classification_of_interest.ilike(search_term),
                    CandidateMasterProfile.sub_classification_of_interest.ilike(search_term)
                ]
                
                # Also search for individual tags in sub_classification_of_interest
                # Split search term by comma and search each tag
                if ',' in search:
                    for tag in search.split(','):
                        tag = tag.strip()
                        if tag:
                            search_conditions.append(
                                CandidateMasterProfile.sub_classification_of_interest.ilike(f'%{tag}%')
                            )
                
                query = query.filter(db.or_(*search_conditions))
            
            # Additional filters
            if classification:
                query = query.filter(CandidateMasterProfile.classification_of_interest.ilike(f'%{classification}%'))
            if sub_classification:
                # Handle comma-separated tags for sub_classification filter
                sub_class_conditions = []
                for tag in sub_classification.split(','):
                    tag = tag.strip()
                    if tag:
                        sub_class_conditions.append(
                            CandidateMasterProfile.sub_classification_of_interest.ilike(f'%{tag}%')
                        )
                if sub_class_conditions:
                    query = query.filter(db.or_(*sub_class_conditions))
            if location:
                query = query.filter(CandidateMasterProfile.location.ilike(f'%{location}%'))
            if citizenship:
                query = query.filter(CandidateMasterProfile.citizenship.ilike(f'%{citizenship}%'))
            
            # Sort by active status first (active = True first), then by creation date
            query = query.order_by(CandidateMasterProfile.is_active.desc(), CandidateMasterProfile.created_date.desc())
            
            # Pagination
            candidates = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'candidates': [candidate.to_dict(include_relationships=include_relationships) for candidate in candidates.items],
                'total': candidates.total,
                'pages': candidates.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

    @candidate_profile_ns.doc('create_candidate')
    @candidate_profile_ns.expect(candidate_input_model)
    def post(self):
        """Create a new candidate"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if field not in data or not data[field]:
                    candidate_profile_ns.abort(400, f'{field} is required')
            
            # Check if email already exists
            existing_candidate = CandidateMasterProfile.query.filter_by(email=data['email']).first()
            if existing_candidate:
                candidate_profile_ns.abort(400, 'Email already exists')
            
            # Create new candidate
            candidate = CandidateMasterProfile(
                first_name=data['first_name'],
                last_name=data['last_name'],
                chinese_name=data.get('chinese_name'),
                email=data['email'],
                location=data.get('location'),
                phone_number=data.get('phone_number'),
                personal_summary=data.get('personal_summary'),
                availability_weeks=data.get('availability_weeks'),
                preferred_work_types=data.get('preferred_work_types'),
                right_to_work=data.get('right_to_work', False),
                salary_expectation=data.get('salary_expectation'),
                classification_of_interest=data.get('classification_of_interest'),
                sub_classification_of_interest=data.get('sub_classification_of_interest'),
                citizenship=data.get('citizenship'),
                remarks=data.get('remarks'),
                ai_short_summary=data.get('ai_short_summary'),
                metadata_json=data.get('metadata_json')
            )
            
            db.session.add(candidate)
            db.session.commit()
            
            return candidate.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/<int:candidate_id>')
@candidate_profile_ns.param('candidate_id', 'Candidate ID')
class Candidate(Resource):
    @candidate_profile_ns.doc('get_candidate')
    @candidate_profile_ns.param('include_relationships', 'Include related data', type=bool, default=True)
    def get(self, candidate_id):
        """Get a specific candidate by ID"""
        try:
            include_relationships = request.args.get('include_relationships', 'true').lower() == 'true'
            
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            result = candidate.to_dict(include_relationships=include_relationships)
            
            return result, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

    @candidate_profile_ns.doc('update_candidate')
    @candidate_profile_ns.expect(candidate_input_model)
    def put(self, candidate_id):
        """Update an existing candidate"""
        try:
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            data = request.get_json()
            
            # Check if email is being changed and if new email already exists
            if 'email' in data and data['email'] != candidate.email:
                existing_candidate = CandidateMasterProfile.query.filter_by(email=data['email']).first()
                if existing_candidate:
                    candidate_profile_ns.abort(400, 'Email already exists')
            
            # Update fields
            updatable_fields = [
                'first_name', 'last_name', 'chinese_name', 'email', 'location', 'phone_number',
                'personal_summary', 'availability_weeks', 'preferred_work_types',
                'right_to_work', 'salary_expectation', 'classification_of_interest',
                'sub_classification_of_interest', 'citizenship', 'is_active', 'remarks',
                'ai_short_summary', 'metadata_json'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(candidate, field, data[field])
            
            candidate.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return candidate.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))

    @candidate_profile_ns.doc('delete_candidate')
    def delete(self, candidate_id):
        """Delete a candidate (soft delete)"""
        try:
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            # Soft delete by setting is_active to False
            candidate.is_active = False
            candidate.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'Candidate deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))

    @candidate_profile_ns.doc('finalize_candidate_profile')
    @candidate_profile_ns.param('generate_ai_summary', 'Generate AI summary and embedding', type=bool, default=True)
    def patch(self, candidate_id):
        """
        Finalize candidate profile update with AI summary generation and embedding
        
        This endpoint should be called after all profile components have been updated.
        It will:
        1. Save the master profile updates to database
        2. Fetch the latest candidate profile with all active relationships
        3. Generate an AI summary using LangChain
        4. Create an embedding vector from the AI summary
        5. Update the profile with AI summary and embedding
        """
        try:
            import asyncio
            
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            # Handle different content types more gracefully
            data = {}
            if request.is_json:
                data = request.get_json() or {}
            elif request.form:
                # Handle form data if needed
                data = request.form.to_dict()
            
            print(f"Request Content-Type: {request.content_type}")
            print(f"Request data: {data}")
            print(f"Request is_json: {request.is_json}")
            
            generate_ai_summary = request.args.get('generate_ai_summary', 'true').lower() == 'true'
            
            # First, update the master profile if data is provided
            if data:
                # Check if email is being changed and if new email already exists
                if 'email' in data and data['email'] != candidate.email:
                    existing_candidate = CandidateMasterProfile.query.filter_by(email=data['email']).first()
                    if existing_candidate:
                        candidate_profile_ns.abort(400, 'Email already exists')
                
                # Update fields (excluding AI fields which will be generated)
                updatable_fields = [
                    'first_name', 'last_name', 'chinese_name', 'email', 'location', 'phone_number',
                    'personal_summary', 'availability_weeks', 'preferred_work_types',
                    'right_to_work', 'salary_expectation', 'classification_of_interest',
                    'sub_classification_of_interest', 'citizenship', 'is_active', 'remarks', 'metadata_json'
                ]
                
                for field in updatable_fields:
                    if field in data:
                        setattr(candidate, field, data[field])
                
                candidate.last_modified_date = datetime.utcnow()
                db.session.commit()
            
            # Fetch the complete candidate profile with all active relationships
            candidate_with_relationships = candidate.to_dict(include_relationships=True)
            
            # Filter out inactive relationships
            for relationship_key in ['career_history', 'skills', 'education', 'licenses_certifications', 'languages', 'resumes']:
                if relationship_key in candidate_with_relationships:
                    candidate_with_relationships[relationship_key] = [
                        item for item in candidate_with_relationships[relationship_key] 
                        if item.get('is_active', True)
                    ]
            
            # Generate AI summary and embedding if requested
            ai_processing_result = None
            if generate_ai_summary:
                try:
                    print(f"Starting AI processing for candidate {candidate_id}")
                    
                    # Check if AI service is available
                    if not ai_summary_service:
                        raise Exception("AI summary service not initialized")
                    
                    # Run the async AI processing in a new event loop
                    try:
                        # Always create a new event loop for consistency
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            ai_processing_result = loop.run_until_complete(
                                ai_summary_service.process_candidate_profile(candidate_with_relationships)
                            )
                        finally:
                            loop.close()
                            asyncio.set_event_loop(None)  # Clean up
                    except Exception as async_error:
                        print(f"Async processing error: {str(async_error)}")
                        raise async_error
                    
                    print(f"AI processing result: {ai_processing_result}")
                    
                    if ai_processing_result and ai_processing_result.get('processing_success'):
                        # Update the candidate with AI summary and embedding
                        print(f"Updating candidate with AI summary...")
                        candidate.ai_short_summary = ai_processing_result['ai_summary']
                        candidate.embedding_vector = ai_processing_result['embedding_vector']
                        candidate.last_modified_date = datetime.utcnow()
                        db.session.commit()
                        print(f"AI summary and embedding saved successfully")
                        
                except Exception as ai_error:
                    import traceback
                    ai_traceback = traceback.format_exc()
                    print(f"AI processing error: {str(ai_error)}")
                    print(f"AI error traceback: {ai_traceback}")
                    ai_processing_result = {
                        'processing_success': False,
                        'error': str(ai_error),
                        'traceback': ai_traceback
                    }
            
            # Get the final updated candidate profile
            final_candidate = candidate.to_dict(include_relationships=True)
            
            # Prepare response
            response_data = {
                'success': True,
                'message': 'Candidate profile finalized successfully',
                'candidate': final_candidate,
                'ai_processing': {
                    'enabled': generate_ai_summary,
                    'success': ai_processing_result.get('processing_success', False) if ai_processing_result else False
                }
            }
            
            if ai_processing_result:
                if ai_processing_result.get('processing_success'):
                    response_data['ai_processing']['summary_generated'] = True
                    response_data['ai_processing']['embedding_created'] = True
                    response_data['ai_processing']['ai_summary'] = ai_processing_result.get('ai_summary')
                else:
                    response_data['ai_processing']['error'] = ai_processing_result.get('error')
            
            return response_data, 200
            
        except Exception as e:
            db.session.rollback()
            # Import traceback for better error reporting
            import traceback
            error_traceback = traceback.format_exc()
            print(f"Profile finalization error: {str(e)}")
            print(f"Full traceback: {error_traceback}")
            candidate_profile_ns.abort(500, f'Profile finalization failed: {str(e)}. Check logs for details.')

@candidate_profile_ns.route('/<int:candidate_id>/hard-delete')
@candidate_profile_ns.param('candidate_id', 'Candidate ID')
class CandidateHardDelete(Resource):
    @candidate_profile_ns.doc('hard_delete_candidate')
    def delete(self, candidate_id):
        """Permanently delete a candidate and all related records"""
        try:
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            # This will cascade delete all related records due to relationship configuration
            db.session.delete(candidate)
            db.session.commit()
            
            return {'message': 'Candidate permanently deleted'}, 200
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/search')
class CandidateSearch(Resource):
    @candidate_profile_ns.doc('search_candidates')
    @candidate_profile_ns.param('q', 'Search query', required=True)
    @candidate_profile_ns.param('page', 'Page number', type=int, default=1)
    @candidate_profile_ns.param('per_page', 'Items per page', type=int, default=10)
    def get(self):
        """Advanced search for candidates"""
        try:
            # Search parameters
            query_text = request.args.get('q', '')
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            
            if not query_text:
                candidate_profile_ns.abort(400, 'Search query is required')
            
            # Search across multiple fields
            query = CandidateMasterProfile.query.filter(
                db.or_(
                    CandidateMasterProfile.first_name.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.last_name.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.email.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.location.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.personal_summary.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.ai_short_summary.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.classification_of_interest.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.sub_classification_of_interest.ilike(f'%{query_text}%'),
                    CandidateMasterProfile.citizenship.ilike(f'%{query_text}%')
                )
            ).filter(CandidateMasterProfile.is_active == True)
            
            # Pagination
            candidates = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'candidates': [candidate.to_dict() for candidate in candidates.items],
                'total': candidates.total,
                'pages': candidates.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/stats')
class CandidateStats(Resource):
    @candidate_profile_ns.doc('get_candidate_stats')
    def get(self):
        """Get candidate statistics"""
        try:
            total_candidates = CandidateMasterProfile.query.count()
            active_candidates = CandidateMasterProfile.query.filter_by(is_active=True).count()
            inactive_candidates = total_candidates - active_candidates
            
            # Classification breakdown
            classification_stats = db.session.query(
                CandidateMasterProfile.classification_of_interest,
                db.func.count(CandidateMasterProfile.id)
            ).filter(CandidateMasterProfile.is_active == True).group_by(
                CandidateMasterProfile.classification_of_interest
            ).all()
            
            return {
                'total_candidates': total_candidates,
                'active_candidates': active_candidates,
                'inactive_candidates': inactive_candidates,
                'classification_breakdown': [
                    {'classification': stat[0], 'count': stat[1]} 
                    for stat in classification_stats if stat[0]
                ]
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

# Prompt template management models
prompt_template_model = candidate_profile_ns.model('PromptTemplate', {
    'id': fields.Integer(readonly=True, description='Template ID'),
    'name': fields.String(required=True, description='Template name'),
    'description': fields.String(description='Template description'),
    'template_content': fields.String(required=True, description='Prompt template with {candidate_profile_data} placeholder'),
    'is_active': fields.Boolean(description='Is this template active'),
    'version_number': fields.Integer(readonly=True, description='Version number'),
    'created_by': fields.String(description='Created by user'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

prompt_template_create_model = candidate_profile_ns.model('PromptTemplateCreate', {
    'name': fields.String(required=True, description='Template name'),
    'description': fields.String(description='Template description'),
    'template_content': fields.String(required=True, description='Prompt template content'),
    'created_by': fields.String(description='Created by user'),
    'base_template_id': fields.Integer(description='Base template ID for versioning')
})

prompt_template_update_model = candidate_profile_ns.model('PromptTemplateUpdate', {
    'name': fields.String(description='Template name'),
    'description': fields.String(description='Template description'),
    'template_content': fields.String(description='Prompt template content'),
    'created_by': fields.String(description='Modified by user')
})

# Bulk regeneration models
bulk_regeneration_request_model = candidate_profile_ns.model('BulkRegenerationRequest', {
    'prompt_template_id': fields.Integer(description='Template ID to activate (optional)', required=False),
    'created_by': fields.String(description='User initiating the job', default='user')
})

bulk_regeneration_response_model = candidate_profile_ns.model('BulkRegenerationResponse', {
    'success': fields.Boolean(description='Whether job was started successfully'),
    'job_id': fields.String(description='Unique job identifier for tracking'),
    'message': fields.String(description='Status message'),
    'warning': fields.String(description='Important warnings about the process')
})

job_status_model = candidate_profile_ns.model('JobStatus', {
    'job_id': fields.String(description='Job identifier'),
    'status': fields.String(description='Current job status'),
    'started_at': fields.String(description='Job start time'),
    'completed_at': fields.String(description='Job completion time'),
    'created_by': fields.String(description='User who initiated the job'),
    'prompt_template_id': fields.Integer(description='Template ID used'),
    'total_profiles': fields.Integer(description='Total profiles to process'),
    'processed_profiles': fields.Integer(description='Profiles processed so far'),
    'successful_updates': fields.Integer(description='Successful updates'),
    'failed_updates': fields.Integer(description='Failed updates'),
    'current_profile_id': fields.Integer(description='Currently processing profile ID'),
    'estimated_completion': fields.String(description='Estimated completion time'),
    'errors': fields.List(fields.String, description='List of errors encountered')
})

@candidate_profile_ns.route('/ai-summary/prompt-templates')
class PromptTemplateList(Resource):
    @candidate_profile_ns.doc('list_prompt_templates')
    @candidate_profile_ns.param('active_only', 'Filter active templates only (true/false)', type='string', required=False)
    @candidate_profile_ns.param('page', 'Page number for pagination', type='int', default=1)
    @candidate_profile_ns.param('per_page', 'Items per page', type='int', default=20)
    def get(self):
        """Get all AI prompt templates with pagination"""
        try:
            # Handle active_only parameter - only filter if explicitly provided
            active_only_param = request.args.get('active_only')
            page = int(request.args.get('page', 1))
            per_page = min(int(request.args.get('per_page', 20)), 100)
            
            query = AiPromptTemplate.query
            
            # Only apply filter if active_only parameter is explicitly provided
            if active_only_param is not None:
                if active_only_param.lower() in ['true', '1', 'yes']:
                    query = query.filter_by(is_active=True)
                elif active_only_param.lower() in ['false', '0', 'no']:
                    query = query.filter_by(is_active=False)
                # If parameter provided but not recognized, ignore filter (show all)
            
            query = query.order_by(AiPromptTemplate.version_number.desc(), AiPromptTemplate.created_date.desc())
            
            paginated = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'templates': [template.to_dict() for template in paginated.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': paginated.total,
                    'pages': paginated.pages,
                    'has_next': paginated.has_next,
                    'has_prev': paginated.has_prev
                },
                'filters': {
                    'active_only': active_only_param
                }
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))
    
    @candidate_profile_ns.doc('create_prompt_template')
    @candidate_profile_ns.expect(prompt_template_create_model)
    def post(self):
        """Create a new AI prompt template"""
        try:
            data = request.get_json()
            
            # Validate required fields
            name = data.get('name', '').strip()
            template_content = data.get('template_content', '').strip()
            
            if not name:
                candidate_profile_ns.abort(400, 'Template name is required')
            
            if not template_content:
                candidate_profile_ns.abort(400, 'Template content is required')
            
            if '{candidate_profile_data}' not in template_content:
                candidate_profile_ns.abort(400, 'Template must contain {candidate_profile_data} placeholder')
            
            # Create version number
            base_template_id = data.get('base_template_id')
            version_number = AiPromptTemplate.create_new_version(base_template_id)
            
            # Create new template
            new_template = AiPromptTemplate(
                name=name,
                description=data.get('description', ''),
                template_content=template_content,
                version_number=version_number,
                created_by=data.get('created_by', 'user'),
                is_active=False  # New templates are not active by default
            )
            
            db.session.add(new_template)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Prompt template created successfully',
                'template': new_template.to_dict()
            }, 201
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/ai-summary/prompt-templates/<int:template_id>')
class PromptTemplate(Resource):
    @candidate_profile_ns.doc('get_prompt_template')
    @candidate_profile_ns.marshal_with(prompt_template_model)
    def get(self, template_id):
        """Get a specific prompt template by ID"""
        try:
            template = AiPromptTemplate.query.get_or_404(template_id)
            return template.to_dict(), 200
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))
    
    @candidate_profile_ns.doc('update_prompt_template')
    @candidate_profile_ns.expect(prompt_template_update_model)
    def put(self, template_id):
        """Update a specific prompt template"""
        try:
            template = AiPromptTemplate.query.get_or_404(template_id)
            data = request.get_json()
            
            # Update fields if provided
            if 'name' in data:
                template.name = data['name'].strip()
            
            if 'description' in data:
                template.description = data['description']
            
            if 'template_content' in data:
                template_content = data['template_content'].strip()
                if not template_content:
                    candidate_profile_ns.abort(400, 'Template content cannot be empty')
                
                if '{candidate_profile_data}' not in template_content:
                    candidate_profile_ns.abort(400, 'Template must contain {candidate_profile_data} placeholder')
                
                template.template_content = template_content
            
            if 'created_by' in data:
                template.created_by = data['created_by']
            
            template.last_modified_date = datetime.utcnow()
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Prompt template updated successfully',
                'template': template.to_dict()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))
    
    @candidate_profile_ns.doc('delete_prompt_template')
    def delete(self, template_id):
        """Hard delete a prompt template"""
        try:
            template = AiPromptTemplate.query.get_or_404(template_id)
            
            if template.is_active:
                candidate_profile_ns.abort(400, 'Cannot delete the active template. Please activate another template first.')
            
            db.session.delete(template)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Prompt template deleted successfully'
            }, 200
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/ai-summary/prompt-templates/<int:template_id>/activate')
class PromptTemplateActivate(Resource):
    @candidate_profile_ns.doc('activate_prompt_template')
    def post(self, template_id):
        """Activate a specific prompt template (deactivates all others)"""
        try:
            template = AiPromptTemplate.query.get_or_404(template_id)
            
            # Activate this template (method handles deactivating others)
            template.activate()
            
            return {
                'success': True,
                'message': f'Template "{template.name}" activated successfully',
                'template': template.to_dict()
            }, 200
            
        except Exception as e:
            db.session.rollback()
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/ai-summary/prompt-template')
class PromptTemplateManager(Resource):
    @candidate_profile_ns.doc('get_active_prompt_template')
    def get(self):
        """Get the currently active AI summary prompt template"""
        try:
            active_template = AiPromptTemplate.get_active_template()
            
            if not active_template:
                candidate_profile_ns.abort(404, 'No active prompt template found')
            
            return {
                'template': active_template.to_dict(),
                'variables': ['candidate_profile_data'],
                'instructions': 'Use {candidate_profile_data} as placeholder for candidate profile data'
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/ai-summary/bulk-regenerate')
class BulkRegenerateAISummaries(Resource):
    @candidate_profile_ns.doc('start_bulk_regeneration')
    @candidate_profile_ns.expect(bulk_regeneration_request_model)
    @candidate_profile_ns.marshal_with(bulk_regeneration_response_model)
    def post(self):
        """
        ⚠️ CAUTION: Regenerate AI summaries for ALL candidate profiles
        
        This endpoint triggers a background job that will:
        1. Optionally activate a specific prompt template
        2. Loop through ALL active candidate profiles
        3. Regenerate AI summary and embedding for each profile
        4. Update the database with new AI-generated content
        
        ⚠️ WARNINGS:
        - This is a heavy operation that may take hours to complete
        - It will consume significant Azure OpenAI credits/tokens
        - Rate limited to max 5 concurrent processes (configurable)
        - Cannot be easily stopped once started
        - All existing AI summaries will be overwritten
        
        💡 Use this when:
        - You've updated the prompt template significantly
        - You want all profiles to use the new template format
        - You're migrating or improving AI summary quality
        
        📊 The job runs in background with progress tracking
        """
        try:
            data = request.get_json() or {}
            
            prompt_template_id = data.get('prompt_template_id')
            created_by = data.get('created_by', 'user')
            
            # Validate template ID if provided
            if prompt_template_id:
                template = AiPromptTemplate.query.get(prompt_template_id)
                if not template:
                    candidate_profile_ns.abort(404, f'Template with ID {prompt_template_id} not found')
            
            # Get count of profiles that will be processed
            profile_count = CandidateMasterProfile.query.filter_by(is_active=True).count()
            
            if profile_count == 0:
                return {
                    'success': False,
                    'job_id': None,
                    'message': 'No active candidate profiles found to process',
                    'warning': None
                }, 200
            
            # Set Flask app context for the service
            bulk_ai_regeneration_service.set_app(current_app._get_current_object())
            
            # Start the bulk regeneration job
            job_id = bulk_ai_regeneration_service.start_bulk_regeneration(
                prompt_template_id=prompt_template_id,
                created_by=created_by
            )
            
            warning_message = (
                f"⚠️ This job will process {profile_count} candidate profiles. "
                f"It may take several hours and consume significant AI credits. "
                f"Monitor progress using job ID: {job_id}"
            )
            
            return {
                'success': True,
                'job_id': job_id,
                'message': f'Bulk regeneration job started successfully. Processing {profile_count} profiles.',
                'warning': warning_message
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/ai-summary/bulk-regenerate/jobs')
class BulkRegenerationJobs(Resource):
    @candidate_profile_ns.doc('list_bulk_regeneration_jobs')
    def get(self):
        """Get status of all bulk regeneration jobs"""
        try:
            jobs = bulk_ai_regeneration_service.get_all_active_jobs()
            
            return {
                'jobs': list(jobs.values()),
                'total_jobs': len(jobs)
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/ai-summary/bulk-regenerate/jobs/<string:job_id>')
class BulkRegenerationJobStatus(Resource):
    @candidate_profile_ns.doc('get_bulk_regeneration_job_status')
    @candidate_profile_ns.marshal_with(job_status_model)
    def get(self, job_id):
        """Get detailed status of a specific bulk regeneration job"""
        try:
            job_status = bulk_ai_regeneration_service.get_job_status(job_id)
            
            if not job_status:
                candidate_profile_ns.abort(404, f'Job with ID {job_id} not found')
            
            return job_status, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))
    
    @candidate_profile_ns.doc('cancel_bulk_regeneration_job')
    def delete(self, job_id):
        """Cancel a running bulk regeneration job (if possible)"""
        try:
            success = bulk_ai_regeneration_service.cancel_job(job_id)
            
            if success:
                return {
                    'success': True,
                    'message': f'Job {job_id} has been marked for cancellation'
                }, 200
            else:
                return {
                    'success': False,
                    'message': f'Job {job_id} could not be cancelled (may not exist or already completed)'
                }, 400
                
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/ai-summary/bulk-regenerate/stats')
class BulkRegenerationStats(Resource):
    @candidate_profile_ns.doc('get_bulk_regeneration_stats')
    def get(self):
        """Get statistics about candidate profiles and bulk regeneration capacity"""
        try:
            # Get profile counts
            total_profiles = CandidateMasterProfile.query.count()
            active_profiles = CandidateMasterProfile.query.filter_by(is_active=True).count()
            profiles_with_ai_summary = CandidateMasterProfile.query.filter(
                CandidateMasterProfile.ai_short_summary.isnot(None)
            ).count()
            
            # Get current rate limiting settings
            max_workers = bulk_ai_regeneration_service.max_concurrent_workers
            rate_limit_delay = bulk_ai_regeneration_service.rate_limit_delay
            
            # Calculate estimated processing time
            estimated_time_per_profile = 10 + rate_limit_delay  # Rough estimate in seconds
            estimated_total_time_hours = (active_profiles * estimated_time_per_profile) / 3600
            
            return {
                'profile_statistics': {
                    'total_profiles': total_profiles,
                    'active_profiles': active_profiles,
                    'profiles_with_ai_summary': profiles_with_ai_summary,
                    'profiles_without_ai_summary': active_profiles - profiles_with_ai_summary
                },
                'processing_capacity': {
                    'max_concurrent_workers': max_workers,
                    'rate_limit_delay_seconds': rate_limit_delay,
                    'estimated_time_per_profile_seconds': estimated_time_per_profile,
                    'estimated_total_processing_hours': round(estimated_total_time_hours, 2)
                },
                'recommendations': [
                    f"Bulk regeneration will process {active_profiles} active profiles",
                    f"Estimated completion time: {round(estimated_total_time_hours, 1)} hours",
                    "Consider running during off-peak hours to minimize impact",
                    "Monitor Azure OpenAI usage and costs during processing"
                ]
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/parse-resume')
class CandidateResumeParser(Resource):
    @candidate_profile_ns.doc('parse_resume_pdf')
    @candidate_profile_ns.expect(resume_upload_parser)
    def post(self):
        """
        Parse PDF resume and extract candidate information with AI-powered classification
        
        **FEATURES**:
        - PDF parsing and data extraction using configurable parsing methods
        - AI-powered industry classification (using lookup data)
        - AI-powered role tag assignment (supports multiple roles)
        - Comprehensive completeness scoring
        - Detailed parsing statistics
        
        **PARSING METHODS**:
        This endpoint supports multiple parsing methods based on the RESUME_PARSING_METHOD environment variable:
        - 'spacy': Traditional NER with spaCy and NLTK (default)
        - 'azure_di': Azure Document Intelligence with query fields
        - 'langextract': LangExtract with Gemini API or Azure OpenAI fallback
        
        **ENVIRONMENT VARIABLES**:
        - RESUME_PARSING_METHOD: Set to 'spacy', 'azure_di', or 'langextract'
        - For azure_di: Requires AZURE_DI_ENDPOINT and AZURE_DI_API_KEY
        - For langextract: Requires AZURE_OPENAI_* variables, optionally LANGEXTRACT_API_KEY
        
        **PROCESSING PIPELINE**:
        1. Parse resume content using configured method (spacy/azure_di/langextract)
        2. Extract entities (name, contact, experience, skills, education, etc.)
        3. AI classification - determine industry and role tags from lookup data
        4. Calculate completeness score including classification data
        5. Return structured candidate data with classification tags
        
        **AI CLASSIFICATION** (Optional):
        - Can be enabled/disabled via 'enable_ai_classification' parameter (default: true)
        - Automatically determines industry classification (e.g., "Information & Communication Technology")
        - Assigns relevant role tags (e.g., ["Data Analyst", "Software Developer"])
        - Uses Azure OpenAI to analyze resume content against predefined lookup codes
        - Provides reasoning for classification decisions
        - Gracefully handles failures without affecting the main parsing process
        
        **PARAMETERS**:
        - resume_file: PDF file to parse (required)
        - enable_ai_classification: Enable/disable AI classification (optional, default: true)
        
        Returns structured candidate data that can be used to prefill 
        candidate creation forms in the frontend, optionally including AI-determined 
        classification and role tags.
        """
        try:
            # Validate file upload
            if 'resume_file' not in request.files:
                candidate_profile_ns.abort(400, 'No resume file provided')
                
            file = request.files['resume_file']
            
            if file.filename == '':
                candidate_profile_ns.abort(400, 'No file selected')
                
            # Validate file type
            if not file.filename.lower().endswith('.pdf'):
                candidate_profile_ns.abort(400, 'Only PDF files are supported')
                
            # Validate file size (max 10MB)
            file.seek(0, 2)  # Seek to end
            file_size = file.tell()
            file.seek(0)  # Reset to beginning
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit
                candidate_profile_ns.abort(400, 'File size must be less than 10MB')
                
            if file_size == 0:
                candidate_profile_ns.abort(400, 'File is empty')
            
            # Get parameters
            enable_ai_classification = request.form.get('enable_ai_classification', 'true').lower() == 'true'
            
            # Parse the resume using the configured parsing service
            try:
                # Get fresh resume parser instance to pick up any environment changes
                from services.resume_parser import get_resume_parser
                current_parser = get_resume_parser()
                parsed_data = current_parser.parse_resume(file)
                
                # Calculate parsing statistics
                parsing_stats = {
                    'file_size_bytes': file_size,
                    'file_name': file.filename,
                    'entities_extracted': {
                        'career_history_count': len(parsed_data.get('career_history', [])),
                        'skills_count': len(parsed_data.get('skills', [])),
                        'education_count': len(parsed_data.get('education', [])),
                        'languages_count': len(parsed_data.get('languages', [])),
                        'certifications_count': len(parsed_data.get('licenses_certifications', []))
                    },
                    'contact_info_found': {
                        'email': bool(parsed_data.get('email')),
                        'phone': bool(parsed_data.get('phone_number')),
                        'location': bool(parsed_data.get('location'))
                    },
                    'name_extracted': {
                        'first_name': bool(parsed_data.get('first_name')),
                        'last_name': bool(parsed_data.get('last_name')),
                        'chinese_name': bool(parsed_data.get('chinese_name'))
                    }
                }
                
                # Calculate completeness score
                completeness_factors = [
                    bool(parsed_data.get('first_name')),
                    bool(parsed_data.get('last_name')),
                    bool(parsed_data.get('email')),
                    bool(parsed_data.get('phone_number')),
                    bool(parsed_data.get('location')),
                    len(parsed_data.get('career_history', [])) > 0,
                    len(parsed_data.get('skills', [])) > 0,
                    len(parsed_data.get('education', [])) > 0
                ]
                
                completeness_score = sum(completeness_factors) / len(completeness_factors) * 100
                parsing_stats['completeness_score'] = round(completeness_score, 1)
                
                # Add parsing method information
                parsing_stats['parsing_method'] = current_parser.parsing_method
                parsing_stats['parsing_method_details'] = {
                    'method': current_parser.parsing_method,
                    'available_methods': ['spacy', 'azure_di', 'langextract'],
                    'environment_variable': 'RESUME_PARSING_METHOD'
                }
                
                # Perform AI classification for industry and role tags (if enabled)
                classification_result = None
                if enable_ai_classification:
                    try:
                        logger.info(f"Starting AI classification for parsed resume: {file.filename}")
                        
                        from services.candidate_classification_service import candidate_classification_service
                        
                        # Run AI classification in async context
                        import asyncio
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
                            
                            parsing_stats['ai_classification'] = {
                                'success': True,
                                'classification_of_interest': classification_result.get('classification_of_interest'),
                                'sub_classification_of_interest': classification_result.get('sub_classification_of_interest'),
                                'reasoning': classification_result.get('reasoning', ''),
                                'message': 'AI classification completed successfully'
                            }
                            
                            logger.info(f"AI classification successful: {classification_result['classification_of_interest']} | {classification_result['sub_classification_of_interest']}")
                        else:
                            parsing_stats['ai_classification'] = {
                                'success': False,
                                'error': classification_result.get('error', 'Unknown error'),
                                'message': 'AI classification failed'
                            }
                            logger.warning(f"AI classification failed: {classification_result.get('error')}")
                            
                    except Exception as classification_error:
                        parsing_stats['ai_classification'] = {
                            'success': False,
                            'error': str(classification_error),
                            'message': 'AI classification failed due to service error'
                        }
                        logger.warning(f"AI classification failed: {str(classification_error)}")
                        # Don't fail the whole process if classification fails
                else:
                    parsing_stats['ai_classification'] = {
                        'enabled': False,
                        'message': 'AI classification disabled by user request'
                    }
                
                # Update parsing statistics with classification info
                if classification_result and classification_result.get('classification_success'):
                    completeness_factors.extend([
                        bool(parsed_data.get('classification_of_interest')),
                        bool(parsed_data.get('sub_classification_of_interest'))
                    ])
                    completeness_score = sum(completeness_factors) / len(completeness_factors) * 100
                    parsing_stats['completeness_score'] = round(completeness_score, 1)
                
                # Update message to include classification status
                classification_status = ""
                if parsing_stats.get('ai_classification', {}).get('success'):
                    classification_status = " with AI industry and role classification"
                elif parsing_stats.get('ai_classification', {}).get('enabled') == False:
                    classification_status = " (AI classification disabled)"
                elif 'ai_classification' in parsing_stats:
                    classification_status = " (AI classification attempted but failed)"
                
                # Prepare response
                response_data = {
                    'success': True,
                    'message': f'Resume parsed successfully using {current_parser.parsing_method} method. Extracted {sum(parsing_stats["entities_extracted"].values())} entities with {parsing_stats["completeness_score"]}% completeness{classification_status}.',
                    'candidate_data': parsed_data,
                    'parsing_stats': parsing_stats
                }
                
                return response_data, 200
                
            except ValueError as ve:
                candidate_profile_ns.abort(422, f'Resume parsing failed: {str(ve)}')
                
        except Exception as e:
            candidate_profile_ns.abort(500, f'An unexpected error occurred: {str(e)}')

# Add multipart parser for PDF upload with JSON data
create_with_pdf_parser = candidate_profile_ns.parser()
create_with_pdf_parser.add_argument('pdf_file', 
                                   location='files',
                                   type=FileStorage,
                                   required=True,
                                   help='PDF resume file')
create_with_pdf_parser.add_argument('candidate_data',
                                   location='form',
                                   type=str,
                                   required=True,
                                   help='JSON string containing candidate data')

@candidate_profile_ns.route('/create-with-pdf')
class CandidateCreateWithPDF(Resource):
    @candidate_profile_ns.doc('create_candidate_with_pdf')
    @candidate_profile_ns.expect(create_with_pdf_parser)
    def post(self):
        """
        Create a complete candidate profile from parsed resume data + PDF file
        
        This endpoint accepts both:
        1. A PDF file (multipart/form-data)
        2. JSON candidate data (form field)
        
        Perfect for creating candidates when you have both the parsed data and the original PDF file.
        """
        try:
            args = create_with_pdf_parser.parse_args()
            pdf_file = args['pdf_file']
            candidate_data_json = args['candidate_data']
            
            # Validate PDF file
            if not pdf_file or pdf_file.filename == '':
                candidate_profile_ns.abort(400, 'No PDF file provided')
            
            if not pdf_file.filename.lower().endswith('.pdf'):
                candidate_profile_ns.abort(400, 'Only PDF files are allowed')
            
            # Parse candidate data JSON
            try:
                import json
                data = json.loads(candidate_data_json)
            except json.JSONDecodeError as e:
                candidate_profile_ns.abort(400, f'Invalid JSON in candidate_data: {str(e)}')
            
            if not data:
                candidate_profile_ns.abort(400, 'No candidate data provided')
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if field not in data or not data[field]:
                    candidate_profile_ns.abort(400, f'{field} is required')
            
            # Check if email already exists
            existing_candidate = CandidateMasterProfile.query.filter_by(email=data['email']).first()
            if existing_candidate:
                candidate_profile_ns.abort(400, f'Email {data["email"]} already exists')
            
            # Read PDF file data
            pdf_data = pdf_file.read()
            if not pdf_data:
                candidate_profile_ns.abort(400, 'PDF file is empty')
            
            # Start database transaction
            try:
                # Create the main candidate profile
                candidate = CandidateMasterProfile(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    chinese_name=data.get('chinese_name'),
                    email=data['email'],
                    location=data.get('location'),
                    phone_number=data.get('phone_number'),
                    personal_summary=data.get('personal_summary'),
                    availability_weeks=data.get('availability_weeks'),
                    preferred_work_types=data.get('preferred_work_types'),
                    right_to_work=data.get('right_to_work', False),
                    salary_expectation=data.get('salary_expectation'),
                    classification_of_interest=data.get('classification_of_interest'),
                    sub_classification_of_interest=data.get('sub_classification_of_interest'),
                    citizenship=data.get('citizenship'),
                    is_active=data.get('is_active', True)
                )
                
                db.session.add(candidate)
                db.session.flush()  # Get the candidate ID without committing
                
                # Track creation statistics
                creation_stats = {
                    'candidate_id': candidate.id,
                    'records_created': {
                        'career_history': 0,
                        'skills': 0,
                        'education': 0,
                        'licenses_certifications': 0,
                        'languages': 0,
                        'resumes': 0
                    },
                    'validation_errors': [],
                    'pdf_file_info': {
                        'original_filename': pdf_file.filename,
                        'file_size': len(pdf_data),
                        'content_type': pdf_file.content_type or 'application/pdf'
                    }
                }
                
                # Create related records (same logic as before)
                # Career history
                if data.get('career_history'):
                    for ch_data in data['career_history']:
                        try:
                            start_date = None
                            end_date = None
                            
                            if ch_data.get('start_date'):
                                if isinstance(ch_data['start_date'], str):
                                    try:
                                        start_date = datetime.strptime(ch_data['start_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid start_date format: {ch_data['start_date']}")
                                else:
                                    start_date = ch_data['start_date']
                            
                            if ch_data.get('end_date'):
                                if isinstance(ch_data['end_date'], str):
                                    try:
                                        end_date = datetime.strptime(ch_data['end_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid end_date format: {ch_data['end_date']}")
                                else:
                                    end_date = ch_data['end_date']
                            
                            if ch_data.get('job_title') and ch_data.get('company_name'):
                                career_history = CandidateCareerHistory(
                                    candidate_id=candidate.id,
                                    job_title=ch_data['job_title'],
                                    company_name=ch_data['company_name'],
                                    start_date=start_date,
                                    end_date=end_date,
                                    description=ch_data.get('description')
                                )
                                db.session.add(career_history)
                                creation_stats['records_created']['career_history'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Career history error: {str(e)}")
                
                # Skills
                if data.get('skills'):
                    for skill_data in data['skills']:
                        try:
                            if skill_data.get('skills'):
                                skill = CandidateSkills(
                                    candidate_id=candidate.id,
                                    career_history_id=skill_data.get('career_history_id'),
                                    skills=skill_data['skills']
                                )
                                db.session.add(skill)
                                creation_stats['records_created']['skills'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Skill error: {str(e)}")
                
                # Education
                if data.get('education'):
                    for edu_data in data['education']:
                        try:
                            start_date = None
                            end_date = None
                            
                            if edu_data.get('start_date'):
                                if isinstance(edu_data['start_date'], str):
                                    try:
                                        start_date = datetime.strptime(edu_data['start_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        try:
                                            start_date = datetime.strptime(edu_data['start_date'], '%Y').date()
                                        except ValueError:
                                            creation_stats['validation_errors'].append(f"Invalid education start_date: {edu_data['start_date']}")
                            
                            if edu_data.get('end_date'):
                                if isinstance(edu_data['end_date'], str):
                                    try:
                                        end_date = datetime.strptime(edu_data['end_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        try:
                                            end_date = datetime.strptime(edu_data['end_date'], '%Y').date()
                                        except ValueError:
                                            creation_stats['validation_errors'].append(f"Invalid education end_date: {edu_data['end_date']}")
                            
                            if edu_data.get('school'):
                                education = CandidateEducation(
                                    candidate_id=candidate.id,
                                    school=edu_data['school'],
                                    degree=edu_data.get('degree'),
                                    field_of_study=edu_data.get('field_of_study'),
                                    start_date=start_date,
                                    end_date=end_date,
                                    grade=edu_data.get('grade'),
                                    description=edu_data.get('description')
                                )
                                db.session.add(education)
                                creation_stats['records_created']['education'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Education error: {str(e)}")
                
                # Licenses & Certifications
                if data.get('licenses_certifications'):
                    for cert_data in data['licenses_certifications']:
                        try:
                            issue_date = None
                            expiration_date = None
                            
                            if cert_data.get('issue_date'):
                                if isinstance(cert_data['issue_date'], str):
                                    try:
                                        issue_date = datetime.strptime(cert_data['issue_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid cert issue_date: {cert_data['issue_date']}")
                            
                            if cert_data.get('expiration_date'):
                                if isinstance(cert_data['expiration_date'], str):
                                    try:
                                        expiration_date = datetime.strptime(cert_data['expiration_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid cert expiration_date: {cert_data['expiration_date']}")
                            
                            if cert_data.get('name'):
                                certification = CandidateLicensesCertifications(
                                    candidate_id=candidate.id,
                                    name=cert_data['name'],
                                    issuing_organization=cert_data.get('issuing_organization'),
                                    issue_date=issue_date,
                                    expiration_date=expiration_date,
                                    credential_id=cert_data.get('credential_id'),
                                    credential_url=cert_data.get('credential_url')
                                )
                                db.session.add(certification)
                                creation_stats['records_created']['licenses_certifications'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Certification error: {str(e)}")
                
                # Languages
                if data.get('languages'):
                    for lang_data in data['languages']:
                        try:
                            if lang_data.get('language'):
                                language = CandidateLanguages(
                                    candidate_id=candidate.id,
                                    language=lang_data['language'],
                                    proficiency_level=lang_data.get('proficiency_level')
                                )
                                db.session.add(language)
                                creation_stats['records_created']['languages'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Language error: {str(e)}")
                
                # Create the resume record with PDF data
                try:
                    resume = CandidateResume(
                        candidate_id=candidate.id,
                        pdf_data=pdf_data,
                        file_name=pdf_file.filename,
                        file_size=len(pdf_data),
                        content_type=pdf_file.content_type or 'application/pdf'
                    )
                    db.session.add(resume)
                    creation_stats['records_created']['resumes'] += 1
                except Exception as e:
                    creation_stats['validation_errors'].append(f"PDF storage error: {str(e)}")
                
                # Commit all changes
                db.session.commit()
                
                # Calculate success metrics
                total_records_created = sum(creation_stats['records_created'].values()) + 1  # +1 for candidate
                
                creation_stats['success_rate'] = round(
                    (total_records_created - len(creation_stats['validation_errors'])) / max(total_records_created, 1) * 100, 2
                ) if total_records_created > 0 else 100
                
                # Get the complete candidate data with relationships
                candidate_with_relationships = candidate.to_dict(include_relationships=True)
                
                return {
                    'success': True,
                    'message': f'Candidate profile created successfully with {total_records_created} total records and PDF file. Success rate: {creation_stats["success_rate"]}%',
                    'candidate': candidate_with_relationships,
                    'creation_stats': creation_stats
                }, 201
                
            except Exception as e:
                db.session.rollback()
                candidate_profile_ns.abort(500, f'Failed to create candidate profile: {str(e)}')
                
        except Exception as e:
            candidate_profile_ns.abort(500, f'An unexpected error occurred: {str(e)}')

@candidate_profile_ns.route('/parse-resume/supported-formats')
class CandidateResumeParserInfo(Resource):
    @candidate_profile_ns.doc('get_resume_parser_info')
    def get(self):
        """Get information about supported resume formats and parsing capabilities"""
        try:
            return {
                'supported_formats': ['PDF'],
                'max_file_size_mb': 10,
                'extractable_information': {
                    'personal_info': [
                        'First name', 'Last name', 'Chinese name', 'Email', 'Phone number', 'Location'
                    ],
                    'professional_info': [
                        'Work experience', 'Job titles', 'Company names', 'Skills'
                    ],
                    'education_info': [
                        'Schools/Universities', 'Degrees', 'Graduation years'
                    ],
                    'additional_info': [
                        'Languages', 'Certifications', 'Licenses'
                    ]
                },
                'parsing_technology': {
                    'method': 'Named Entity Recognition (NER)',
                    'library': 'spaCy with custom entity ruler',
                    'reference': 'https://medium.com/pythons-gurus/performing-resum%C3%A9-analysis-using-ner-with-cosine-similarity-8eb99879cda4'
                },
                'usage_tips': [
                    'Ensure PDF contains selectable text (not scanned images)',
                    'Use standard resume formats for better parsing accuracy',
                    'Include clear section headers (Education, Experience, Skills, etc.)',
                    'Avoid complex layouts or graphics that may interfere with text extraction'
                ]
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/parse-resume/debug-config')
class ResumeParserDebugConfig(Resource):
    @candidate_profile_ns.doc('get_parser_debug_config')
    def get(self):
        """Get current resume parser configuration for debugging"""
        try:
            import os
            from dotenv import load_dotenv
            
            # Reload environment variables to get current state
            load_dotenv()
            
            # Get current environment variables
            parsing_method_env = os.getenv('RESUME_PARSING_METHOD', 'spacy')
            azure_di_endpoint = os.getenv('AZURE_DI_ENDPOINT', '')
            azure_openai_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT', '')
            langextract_api_key = os.getenv('LANGEXTRACT_API_KEY', '')
            
            # Get fresh parser instance
            from services.resume_parser import get_resume_parser
            current_parser = get_resume_parser()
            
            config_info = {
                'environment_variables': {
                    'RESUME_PARSING_METHOD': parsing_method_env,
                    'AZURE_DI_ENDPOINT': 'SET' if azure_di_endpoint else 'NOT SET',
                    'AZURE_DI_API_KEY': 'SET' if os.getenv('AZURE_DI_API_KEY') else 'NOT SET',
                    'AZURE_OPENAI_ENDPOINT': 'SET' if azure_openai_endpoint else 'NOT SET',
                    'AZURE_OPENAI_API_KEY': 'SET' if os.getenv('AZURE_OPENAI_API_KEY') else 'NOT SET',
                    'LANGEXTRACT_API_KEY': 'SET' if langextract_api_key else 'NOT SET'
                },
                'parser_current_config': {
                    'parsing_method': current_parser.parsing_method,
                    'available_methods': ['spacy', 'azure_di', 'langextract'],
                    'has_azure_di_client': hasattr(current_parser, 'azure_di_client'),
                    'has_azure_openai_client': hasattr(current_parser, 'azure_openai_client'),
                    'has_spacy_nlp': hasattr(current_parser, 'nlp')
                },
                'method_specific_features': {
                    'spacy': {
                        'available': True,
                        'uses_entity_ruler': True,
                        'supported_entities': ['PERSON', 'ORG', 'GPE', 'SKILL']
                    },
                    'azure_di': {
                        'available': hasattr(current_parser, 'azure_di_client'),
                        'query_fields_enabled': current_parser.parsing_method == 'azure_di',
                        'query_fields': ['Summary', 'Name', 'Phone', 'Email', 'Education', 'ProfessionalExperienceRole', 'ProfessionalExperienceDescription', 'Skills', 'LicensesCertifications', 'Languages'],
                        'supported_models': ['prebuilt-layout', 'prebuilt-document']
                    },
                    'langextract': {
                        'available': current_parser.parsing_method == 'langextract',
                        'has_gemini_api': bool(langextract_api_key),
                        'has_azure_openai_fallback': hasattr(current_parser, 'azure_openai_client'),
                        'uses_structured_prompts': True
                    }
                },
                'recommendation': f'Parser is configured to use {current_parser.parsing_method} method. Restart Flask app if RESUME_PARSING_METHOD was changed after startup.'
            }
            
            return config_info, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

    @candidate_profile_ns.doc('reset_parser_config')
    def post(self):
        """Reset and reinitialize the resume parser with current environment variables"""
        try:
            # Reset the parser instance
            reset_resume_parser()
            
            # Force reimport to get new instance
            global resume_parser
            from services.resume_parser import get_resume_parser
            resume_parser = get_resume_parser()
            
            # Get new configuration
            import os
            parsing_method_env = os.getenv('RESUME_PARSING_METHOD', 'spacy')
            
            return {
                'message': 'Resume parser reset and reinitialized',
                'new_config': {
                    'environment_variable': 'RESUME_PARSING_METHOD',
                    'current_value': parsing_method_env,
                    'parsing_method': resume_parser.parsing_method,
                    'available_methods': ['spacy', 'azure_di', 'langextract'],
                    'has_azure_di_client': hasattr(resume_parser, 'azure_di_client'),
                    'has_azure_openai_client': hasattr(resume_parser, 'azure_openai_client'),
                    'has_spacy_nlp': hasattr(resume_parser, 'nlp'),
                    'langextract_available': hasattr(resume_parser, 'parsing_method') and resume_parser.parsing_method == 'langextract'
                }
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/parse-resume/config-test')
class ResumeParserConfigTest(Resource):
    @candidate_profile_ns.doc('test_parser_config')
    def get(self):
        """Test current resume parser configuration and show which method will be used"""
        try:
            import os
            from dotenv import load_dotenv
            
            # Reload environment variables
            load_dotenv()
            
            # Get fresh parser instance
            from services.resume_parser import get_resume_parser
            current_parser = get_resume_parser()
            
            parsing_method_env = os.getenv('RESUME_PARSING_METHOD', 'spacy')
            
            # Check configuration status
            config_status = {
                'environment_variable': {
                    'RESUME_PARSING_METHOD': parsing_method_env,
                    'matches_parser': parsing_method_env.lower() == current_parser.parsing_method
                },
                'active_method': current_parser.parsing_method,
                'method_status': {}
            }
            
            # Check each method's availability
            methods = {
                'spacy': {
                    'available': True,
                    'requirements': 'Always available',
                    'ready': True
                },
                'azure_di': {
                    'available': bool(os.getenv('AZURE_DI_ENDPOINT') and os.getenv('AZURE_DI_API_KEY')),
                    'requirements': 'AZURE_DI_ENDPOINT and AZURE_DI_API_KEY',
                    'ready': hasattr(current_parser, 'azure_di_client')
                },
                'langextract': {
                    'available': bool(os.getenv('AZURE_OPENAI_ENDPOINT') and os.getenv('AZURE_OPENAI_API_KEY')),
                    'requirements': 'AZURE_OPENAI_* variables (LANGEXTRACT_API_KEY is optional)',
                    'ready': hasattr(current_parser, 'azure_openai_client'),
                    'has_gemini_fallback': bool(os.getenv('LANGEXTRACT_API_KEY'))
                }
            }
            
            config_status['method_status'] = methods
            
            # Provide recommendations
            if parsing_method_env.lower() != current_parser.parsing_method:
                config_status['warning'] = f"Environment variable is set to '{parsing_method_env}' but parser is using '{current_parser.parsing_method}'. The parser may have fallen back due to missing dependencies."
            
            if not methods[current_parser.parsing_method]['ready']:
                config_status['error'] = f"Current method '{current_parser.parsing_method}' is not properly configured"
            
            return config_status, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, str(e))

@candidate_profile_ns.route('/create-from-parsed-data')
class CandidateBulkCreate(Resource):
    @candidate_profile_ns.doc('create_candidate_from_parsed_data')
    @candidate_profile_ns.expect(candidate_bulk_create_model)
    def post(self):
        """
        Create a complete candidate profile from parsed resume data
        
        This endpoint accepts the JSON output from the resume parser and creates
        a complete candidate profile including all related records (career history,
        skills, education, languages, certifications).
        
        Perfect for creating candidates directly from parsed resume data.
        """
        try:
            data = request.get_json()
            
            if not data:
                candidate_profile_ns.abort(400, 'No data provided')
            
            # Validate required fields
            required_fields = ['first_name', 'last_name', 'email']
            for field in required_fields:
                if field not in data or not data[field]:
                    candidate_profile_ns.abort(400, f'{field} is required')
            
            # Check if email already exists
            existing_candidate = CandidateMasterProfile.query.filter_by(email=data['email']).first()
            if existing_candidate:
                candidate_profile_ns.abort(400, f'Email {data["email"]} already exists')
            
            # Start database transaction
            try:
                # Create the main candidate profile
                candidate = CandidateMasterProfile(
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    chinese_name=data.get('chinese_name'),
                    email=data['email'],
                    location=data.get('location'),
                    phone_number=data.get('phone_number'),
                    personal_summary=data.get('personal_summary'),
                    availability_weeks=data.get('availability_weeks'),
                    preferred_work_types=data.get('preferred_work_types'),
                    right_to_work=data.get('right_to_work', False),
                    salary_expectation=data.get('salary_expectation'),
                    classification_of_interest=data.get('classification_of_interest'),
                    sub_classification_of_interest=data.get('sub_classification_of_interest'),
                    citizenship=data.get('citizenship'),
                    is_active=data.get('is_active', True)
                )
                
                db.session.add(candidate)
                db.session.flush()  # Get the candidate ID without committing
                
                # Track creation statistics
                creation_stats = {
                    'candidate_id': candidate.id,
                    'records_created': {
                        'career_history': 0,
                        'skills': 0,
                        'education': 0,
                        'licenses_certifications': 0,
                        'languages': 0,
                        'resumes': 0
                    },
                    'validation_errors': []
                }
                
                # Create career history records
                if data.get('career_history'):
                    for ch_data in data['career_history']:
                        try:
                            # Parse dates if provided
                            start_date = None
                            end_date = None
                            
                            if ch_data.get('start_date'):
                                if isinstance(ch_data['start_date'], str):
                                    try:
                                        start_date = datetime.strptime(ch_data['start_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid start_date format: {ch_data['start_date']}")
                                else:
                                    start_date = ch_data['start_date']
                            
                            if ch_data.get('end_date'):
                                if isinstance(ch_data['end_date'], str):
                                    try:
                                        end_date = datetime.strptime(ch_data['end_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid end_date format: {ch_data['end_date']}")
                                else:
                                    end_date = ch_data['end_date']
                            
                            if ch_data.get('job_title') and ch_data.get('company_name'):
                                career_history = CandidateCareerHistory(
                                    candidate_id=candidate.id,
                                    job_title=ch_data['job_title'],
                                    company_name=ch_data['company_name'],
                                    start_date=start_date,
                                    end_date=end_date,
                                    description=ch_data.get('description')
                                )
                                db.session.add(career_history)
                                creation_stats['records_created']['career_history'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Career history error: {str(e)}")
                
                # Create skills records
                if data.get('skills'):
                    for skill_data in data['skills']:
                        try:
                            if skill_data.get('skills'):
                                skill = CandidateSkills(
                                    candidate_id=candidate.id,
                                    career_history_id=skill_data.get('career_history_id'),
                                    skills=skill_data['skills']
                                )
                                db.session.add(skill)
                                creation_stats['records_created']['skills'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Skill error: {str(e)}")
                
                # Create education records
                if data.get('education'):
                    for edu_data in data['education']:
                        try:
                            # Parse dates if provided
                            start_date = None
                            end_date = None
                            
                            if edu_data.get('start_date'):
                                if isinstance(edu_data['start_date'], str):
                                    try:
                                        start_date = datetime.strptime(edu_data['start_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        # Try year-only format
                                        try:
                                            start_date = datetime.strptime(edu_data['start_date'], '%Y').date()
                                        except ValueError:
                                            creation_stats['validation_errors'].append(f"Invalid education start_date: {edu_data['start_date']}")
                            
                            if edu_data.get('end_date'):
                                if isinstance(edu_data['end_date'], str):
                                    try:
                                        end_date = datetime.strptime(edu_data['end_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        # Try year-only format
                                        try:
                                            end_date = datetime.strptime(edu_data['end_date'], '%Y').date()
                                        except ValueError:
                                            creation_stats['validation_errors'].append(f"Invalid education end_date: {edu_data['end_date']}")
                            
                            if edu_data.get('school'):
                                education = CandidateEducation(
                                    candidate_id=candidate.id,
                                    school=edu_data['school'],
                                    degree=edu_data.get('degree'),
                                    field_of_study=edu_data.get('field_of_study'),
                                    start_date=start_date,
                                    end_date=end_date,
                                    grade=edu_data.get('grade'),
                                    description=edu_data.get('description')
                                )
                                db.session.add(education)
                                creation_stats['records_created']['education'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Education error: {str(e)}")
                
                # Create licenses & certifications records
                if data.get('licenses_certifications'):
                    for cert_data in data['licenses_certifications']:
                        try:
                            # Parse dates if provided
                            issue_date = None
                            expiration_date = None
                            
                            if cert_data.get('issue_date'):
                                if isinstance(cert_data['issue_date'], str):
                                    try:
                                        issue_date = datetime.strptime(cert_data['issue_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid cert issue_date: {cert_data['issue_date']}")
                            
                            if cert_data.get('expiration_date'):
                                if isinstance(cert_data['expiration_date'], str):
                                    try:
                                        expiration_date = datetime.strptime(cert_data['expiration_date'], '%Y-%m-%d').date()
                                    except ValueError:
                                        creation_stats['validation_errors'].append(f"Invalid cert expiration_date: {cert_data['expiration_date']}")
                            
                            if cert_data.get('name'):
                                certification = CandidateLicensesCertifications(
                                    candidate_id=candidate.id,
                                    name=cert_data['name'],
                                    issuing_organization=cert_data.get('issuing_organization'),
                                    issue_date=issue_date,
                                    expiration_date=expiration_date,
                                    credential_id=cert_data.get('credential_id'),
                                    credential_url=cert_data.get('credential_url')
                                )
                                db.session.add(certification)
                                creation_stats['records_created']['licenses_certifications'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Certification error: {str(e)}")
                
                # Create languages records
                if data.get('languages'):
                    for lang_data in data['languages']:
                        try:
                            if lang_data.get('language'):
                                language = CandidateLanguages(
                                    candidate_id=candidate.id,
                                    language=lang_data['language'],
                                    proficiency_level=lang_data.get('proficiency_level')
                                )
                                db.session.add(language)
                                creation_stats['records_created']['languages'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Language error: {str(e)}")
                
                # Create resume records (if any)
                if data.get('resumes'):
                    for resume_data in data['resumes']:
                        try:
                            if resume_data.get('file_name'):
                                # Handle base64 encoded PDF data if provided
                                pdf_data = None
                                if resume_data.get('pdf_data_base64'):
                                    import base64
                                    pdf_data = base64.b64decode(resume_data['pdf_data_base64'])
                                
                                if pdf_data:
                                    resume = CandidateResume(
                                        candidate_id=candidate.id,
                                        pdf_data=pdf_data,
                                        file_name=resume_data['file_name'],
                                        file_size=resume_data.get('file_size', len(pdf_data)),
                                        content_type=resume_data.get('content_type', 'application/pdf')
                                    )
                                    db.session.add(resume)
                                    creation_stats['records_created']['resumes'] += 1
                        except Exception as e:
                            creation_stats['validation_errors'].append(f"Resume error: {str(e)}")
                
                # Handle direct PDF file upload (base64 encoded)
                if data.get('resume_file'):
                    try:
                        import base64
                        
                        # Decode the base64 PDF data
                        if isinstance(data['resume_file'], str):
                            # If it's a base64 string
                            pdf_data = base64.b64decode(data['resume_file'])
                        elif isinstance(data['resume_file'], dict):
                            # If it's an object with base64 data
                            pdf_data = base64.b64decode(data['resume_file'].get('data', ''))
                        else:
                            raise ValueError("Invalid resume_file format")
                        
                        # Generate a filename if not provided
                        file_name = data.get('file_name', f"{data['first_name']}_{data['last_name']}_resume.pdf")
                        
                        resume = CandidateResume(
                            candidate_id=candidate.id,
                            pdf_data=pdf_data,
                            file_name=file_name,
                            file_size=len(pdf_data),
                            content_type='application/pdf'
                        )
                        db.session.add(resume)
                        creation_stats['records_created']['resumes'] += 1
                        
                    except Exception as e:
                        creation_stats['validation_errors'].append(f"Direct PDF upload error: {str(e)}")
                
                # Commit all changes
                db.session.commit()
                
                # Calculate success metrics
                total_records_created = sum(creation_stats['records_created'].values()) + 1  # +1 for candidate
                total_input_records = (
                    len(data.get('career_history', [])) +
                    len(data.get('skills', [])) +
                    len(data.get('education', [])) +
                    len(data.get('licenses_certifications', [])) +
                    len(data.get('languages', [])) +
                    len(data.get('resumes', []))
                )
                
                creation_stats['success_rate'] = round(
                    (total_records_created - len(creation_stats['validation_errors'])) / max(total_records_created, 1) * 100, 2
                ) if total_records_created > 0 else 100
                
                # Get the complete candidate data with relationships
                candidate_with_relationships = candidate.to_dict(include_relationships=True)
                
                return {
                    'success': True,
                    'message': f'Candidate profile created successfully with {total_records_created} total records. Success rate: {creation_stats["success_rate"]}%',
                    'candidate': candidate_with_relationships,
                    'creation_stats': creation_stats
                }, 201
                
            except Exception as e:
                db.session.rollback()
                candidate_profile_ns.abort(500, f'Failed to create candidate profile: {str(e)}')
                
        except Exception as e:
            candidate_profile_ns.abort(500, f'An unexpected error occurred: {str(e)}') 

@candidate_profile_ns.route('/resumes/<int:resume_id>/download')
class CandidateResumeDownload(Resource):
    @candidate_profile_ns.doc('download_resume_pdf')
    @candidate_profile_ns.param('resume_id', 'Resume ID')
    def get(self, resume_id):
        """
        Download PDF resume file
        
        Returns the PDF file as binary data with appropriate headers.
        """
        try:
            from flask import Response
            
            resume = CandidateResume.query.filter_by(id=resume_id, is_active=True).first()
            if not resume:
                candidate_profile_ns.abort(404, 'Resume not found')
            
            if not resume.pdf_data:
                candidate_profile_ns.abort(404, 'PDF data not found')
            
            # Return PDF as binary response
            response = Response(
                resume.pdf_data,
                mimetype=resume.content_type or 'application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{resume.file_name}"',
                    'Content-Length': str(resume.file_size)
                }
            )
            
            return response
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Download failed: {str(e)}')

# Semantic Search Endpoints
@candidate_profile_ns.route('/semantic-search')
class CandidateSemanticSearch(Resource):
    @candidate_profile_ns.doc('semantic_search_candidates')
    @candidate_profile_ns.expect(semantic_search_request_model)
    @candidate_profile_ns.marshal_with(semantic_search_response_model)
    def post(self):
        """
        Search candidates using hybrid semantic similarity and keyword matching
        
        Performs intelligent search by:
        1. Converting the query to an embedding vector for semantic similarity
        2. Analyzing exact keyword matches in candidate profiles
        3. Combining both scores using configurable weights
        4. Returning results sorted by final hybrid relevance score
        
        Formula: hybrid_score = (semantic_weight × semantic_score) + (keyword_weight × keyword_score)
        
        Example queries:
        - "data scientist with Python experience"
        - "software engineer in fintech"
        - "project manager with agile experience"
        """
        try:
            data = request.get_json()
            
            if not data:
                candidate_profile_ns.abort(400, 'Request body is required')
            
            query = data.get('query')
            if not query or not query.strip():
                candidate_profile_ns.abort(400, 'Search query is required')
            
            # Get optional parameters
            confidence_threshold = data.get('confidence_threshold')
            max_results = data.get('max_results')
            include_relationships = data.get('include_relationships', False)
            
            # Validate confidence threshold
            if confidence_threshold is not None:
                if not isinstance(confidence_threshold, (int, float)) or not 0.0 <= confidence_threshold <= 1.0:
                    candidate_profile_ns.abort(400, 'Confidence threshold must be a number between 0.0 and 1.0')
            
            # Validate max results
            if max_results is not None:
                if not isinstance(max_results, int) or max_results <= 0:
                    candidate_profile_ns.abort(400, 'Max results must be a positive integer')
                if max_results > 100:  # Set reasonable upper limit
                    candidate_profile_ns.abort(400, 'Max results cannot exceed 100')
            
            # Perform semantic search
            import asyncio
            
            # Create new event loop for async operation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                search_results = loop.run_until_complete(
                    semantic_search_service.search_candidates(
                        query=query.strip(),
                        confidence_threshold=confidence_threshold,
                        max_results=max_results,
                        include_relationships=include_relationships
                    )
                )
            finally:
                loop.close()
                asyncio.set_event_loop(None)
            
            if not search_results.get('success'):
                candidate_profile_ns.abort(500, f"Search failed: {search_results.get('error', 'Unknown error')}")
            
            return search_results
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Semantic search failed: {str(e)}')

@candidate_profile_ns.route('/semantic-search/statistics')
class CandidateSearchStatistics(Resource):
    @candidate_profile_ns.doc('get_search_statistics')
    @candidate_profile_ns.marshal_with(search_statistics_model)
    def get(self):
        """
        Get statistics about the semantic search system
        
        Returns information about:
        - Total candidates and embedding coverage
        - Default settings and limits
        - System health metrics
        """
        try:
            stats = semantic_search_service.get_search_statistics()
            
            if 'error' in stats:
                candidate_profile_ns.abort(500, f"Failed to get statistics: {stats['error']}")
            
            return stats
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get search statistics: {str(e)}')

@candidate_profile_ns.route('/semantic-search/example-queries')
class CandidateSearchExamples(Resource):
    @candidate_profile_ns.doc('get_search_examples')
    def get(self):
        """
        Get example search queries to help users understand the system
        
        Returns a list of example queries that demonstrate different search capabilities
        """
        try:
            examples = {
                'examples': [
                    {
                        'category': 'Technical Skills',
                        'queries': [
                            'Python developer with machine learning experience',
                            'Full-stack developer with React and Node.js',
                            'Data scientist with SQL and Python skills',
                            'DevOps engineer with AWS and Docker experience'
                        ]
                    },
                    {
                        'category': 'Industry/Domain',
                        'queries': [
                            'Software engineer in fintech industry',
                            'Project manager with healthcare experience',
                            'Data analyst in e-commerce',
                            'UX designer for mobile applications'
                        ]
                    },
                    {
                        'category': 'Experience Level',
                        'queries': [
                            'Senior software engineer with 5+ years experience',
                            'Junior developer with internship experience',
                            'Team lead with agile methodology experience',
                            'Architect with microservices experience'
                        ]
                    },
                    {
                        'category': 'Location/Remote',
                        'queries': [
                            'Remote software developer',
                            'Data scientist in New York',
                            'Frontend developer in London',
                            'Product manager in San Francisco'
                        ]
                    },
                    {
                        'category': 'Education/Certifications',
                        'queries': [
                            'Computer science graduate with AWS certification',
                            'MBA with project management certification',
                            'Data scientist with PhD in statistics',
                            'Developer with Microsoft certifications'
                        ]
                    }
                ],
                'tips': [
                    'Use specific skills and technologies for better results',
                    'Include industry or domain knowledge when relevant',
                    'Mention experience level or years of experience',
                    'Specify location preferences if important',
                    'Use natural language - the system understands conversational queries'
                ],
                'confidence_thresholds': {
                    '0.5+': 'Very High - Very specific matches',
                    '0.4+': 'High - Strong matches',
                    '0.3+': 'Good - Relevant matches (default)',
                    '0.2+': 'Moderate - Somewhat relevant',
                    '0.1+': 'Low - Basic relevance'
                }
            }
            
            return examples
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get search examples: {str(e)}')

# Batch Resume Parsing Endpoints

@candidate_profile_ns.route('/batch-parse-resumes')
class BatchResumeParser(Resource):
    @candidate_profile_ns.doc('batch_parse_resumes')
    @candidate_profile_ns.expect(swagger_batch_upload_parser)
    @candidate_profile_ns.marshal_with(batch_parse_response_model)
    def post(self):
        """
        Batch parse multiple PDF resumes and create complete candidate profiles in parallel
        
        **FEATURES**:
        - PDF parsing and data extraction
        - Complete candidate profile creation (skills, education, experience, etc.)
        - AI-powered industry classification (using lookup data)
        - AI-powered role tag assignment (supports multiple roles)
        - AI summary generation using Azure OpenAI
        - Embedding generation for semantic search
        - Progress tracking and detailed reporting
        
        **SWAGGER UI USERS**: Use the individual file fields (file1, file2, etc.) below.
        Each field accepts one PDF file. You can upload up to 20 files at once via Swagger UI.
        
        **API CLIENTS**: Send files as 'resume_files' array in multipart/form-data format.
        Can handle up to 50 files per batch (configurable via MAX_FILES_PER_BATCH).
        
        **CONFIGURATION LIMITS**:
        - MAX_FILES_PER_BATCH: Maximum files per batch (default: 50)
        - BATCH_UPLOAD_LIMIT: Total size limit for all files (default: 200MB)
        - MAX_CONTENT_LENGTH: Individual file size limit (default: 16MB)
        
        **PROCESSING PIPELINE**:
        1. Parse resume content using configured method (spacy/azure_di/langextract)
        2. AI classification - determine industry and role tags from lookup data
        3. Create candidate profile with all related records and classifications
        4. Generate AI summary using Azure OpenAI
        5. Generate embedding vector for semantic search
        6. Store complete profile in database
        
        **THREADING CONFIGURATION**:
        - AI_BULK_MAX_CONCURRENT_WORKERS: Maximum concurrent workers (default: 5)
        - AI_BULK_RATE_LIMIT_DELAY_SECONDS: Delay between operations (default: 1.0)
        
        Features:
        - Parallel processing of multiple resumes
        - Automatic handling of missing mandatory fields (filled with empty strings)
        - Batch tracking with metadata for each candidate
        - Status tracking: completed vs incomplete profiles
        - Progress monitoring and error reporting
        
        Returns a job ID for monitoring progress via the status endpoint.
        """
        try:
            # Debug: Log request details to understand the parsing issue
            logger.info(f"Request Content-Type: {request.content_type}")
            logger.info(f"Request Content-Length: {request.content_length}")
            logger.info(f"Request method: {request.method}")
            
            try:
                # IMPORTANT: Handle incorrect Content-Type from frontend
                # Frontend should send multipart/form-data but sometimes sends application/x-www-form-urlencoded
                # This causes werkzeug to try parsing binary data as URL-encoded text
                
                if request.content_type == 'application/x-www-form-urlencoded':
                    logger.warning("Frontend sent incorrect Content-Type: application/x-www-form-urlencoded for file upload")
                    logger.warning("This should be multipart/form-data. Please fix the frontend.")
                    candidate_profile_ns.abort(400, 
                        'Invalid request format: File uploads must use multipart/form-data content type, '
                        'not application/x-www-form-urlencoded. Please check your frontend implementation.')
                
                # Handle both original format (resume_files array) and Swagger UI format (individual files)
                resume_files = []
                
                # Try original format first (for API clients)
                original_files = request.files.getlist('resume_files')
                if original_files:
                    resume_files = original_files
                    logger.info(f"Using original format: found {len(resume_files)} files in 'resume_files' array")
                else:
                    # Try Swagger UI format (individual file fields)
                    try:
                        args = swagger_batch_upload_parser.parse_args()
                        # Check all possible file fields dynamically
                        for i in range(1, 21):  # Support up to 20 files from Swagger
                            field_name = f'file{i}'
                            file_obj = args.get(field_name)
                            if file_obj and file_obj.filename:  # Check if file was actually uploaded
                                resume_files.append(file_obj)
                        logger.info(f"Using Swagger format: found {len(resume_files)} files from individual fields")
                    except Exception as parse_error:
                        logger.error(f"Parser fallback failed: {str(parse_error)}")
                        # Final fallback - try to get any files from request
                        all_files = []
                        for key in request.files:
                            all_files.extend(request.files.getlist(key))
                        resume_files = [f for f in all_files if f.filename]
                        logger.info(f"Emergency fallback: found {len(resume_files)} files from any field")
            except Exception as parse_error:
                error_msg = str(parse_error)
                logger.error(f"Request parsing error: {error_msg}")
                
                # Handle specific error types
                if 'UnicodeDecodeError' in error_msg or 'utf-8' in error_msg:
                    candidate_profile_ns.abort(400, 
                        'Invalid file encoding detected. Please ensure all files are valid PDFs and try again.')
                elif 'Request Entity Too Large' in error_msg or 'exceeds the capacity limit' in error_msg:
                    batch_limit = int(os.getenv('BATCH_UPLOAD_LIMIT', 200 * 1024 * 1024))
                    batch_limit_mb = batch_limit / 1024 / 1024
                    candidate_profile_ns.abort(413, 
                        f'Total request size is too large. Maximum allowed: {batch_limit_mb:.1f}MB total. '
                        f'Please reduce the number of files or file sizes and try again.')
                elif '413' in error_msg or 'too large' in error_msg.lower():
                    batch_limit = int(os.getenv('BATCH_UPLOAD_LIMIT', 200 * 1024 * 1024))
                    batch_limit_mb = batch_limit / 1024 / 1024
                    candidate_profile_ns.abort(413, 
                        f'Upload size exceeds limit. Maximum allowed: {batch_limit_mb:.1f}MB total.')
                else:
                    # Generic request parsing error
                    candidate_profile_ns.abort(400, f'Invalid request format: {error_msg}')
            
            # Ensure we have files
            if not resume_files:
                candidate_profile_ns.abort(400, 'No resume files provided')
            
            # Ensure all files are provided (handle single file case)
            if not isinstance(resume_files, list):
                resume_files = [resume_files]
            
            # Validate file count (configurable via environment variable)
            max_files_per_batch = int(os.getenv('MAX_FILES_PER_BATCH', 50))
            if len(resume_files) > max_files_per_batch:
                candidate_profile_ns.abort(400, f'Too many files. Maximum {max_files_per_batch} files per batch. '
                                              f'To process more files, split them into multiple batches or increase MAX_FILES_PER_BATCH.')
            
            # Validate files and prepare them for processing
            max_individual_file_size = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
            batch_upload_limit = int(os.getenv('BATCH_UPLOAD_LIMIT', 200 * 1024 * 1024))
            total_size = 0
            validated_files = []
            
            for file in resume_files:
                # Basic validation
                if not file or not file.filename:
                    candidate_profile_ns.abort(400, 'All files must have valid filenames')
                if not file.filename.lower().endswith('.pdf'):
                    candidate_profile_ns.abort(400, f'File {file.filename} is not a PDF. Only PDF files are supported.')
                
                try:
                    # Read file content and get size
                    file.seek(0)  # Ensure we're at the beginning
                    file_content = file.read()
                    file_size = len(file_content)
                    
                    # Validate that we actually read some content
                    if file_size == 0:
                        candidate_profile_ns.abort(400, f'File {file.filename} is empty or corrupted.')
                        
                except Exception as file_read_error:
                    logger.error(f"Error reading file {file.filename}: {str(file_read_error)}")
                    candidate_profile_ns.abort(400, f'Error reading file {file.filename}. Please ensure the file is not corrupted.')
                
                # Check individual file size
                if file_size > max_individual_file_size:
                    max_size_mb = max_individual_file_size / 1024 / 1024
                    file_size_mb = file_size / 1024 / 1024
                    candidate_profile_ns.abort(413, 
                        f'File {file.filename} is too large ({file_size_mb:.1f}MB). '
                        f'Maximum individual file size: {max_size_mb:.1f}MB')
                
                total_size += file_size
                
                # Store validated file info with content
                validated_files.append({
                    'filename': file.filename,
                    'content': file_content,
                    'size': file_size
                })
            
            # Check total batch size
            if total_size > batch_upload_limit:
                total_size_mb = total_size / 1024 / 1024
                batch_limit_mb = batch_upload_limit / 1024 / 1024
                logger.warning(f"Batch size check failed: {total_size_mb:.1f}MB > {batch_limit_mb:.1f}MB")
                candidate_profile_ns.abort(413, 
                    f'Total batch size ({total_size_mb:.1f}MB) exceeds limit. '
                    f'Maximum batch size: {batch_limit_mb:.1f}MB')
            
            # Log successful validation
            total_size_mb = total_size / 1024 / 1024
            batch_limit_mb = batch_upload_limit / 1024 / 1024
            logger.info(f"File validation passed: {len(validated_files)} files, {total_size_mb:.3f}MB total (limit: {batch_limit_mb:.1f}MB)")
            
            # Set Flask app context for the service
            batch_resume_parser_service.set_app(current_app._get_current_object())
            
            # Start batch processing with validated file data
            job_id = batch_resume_parser_service.start_batch_parsing(validated_files, created_by='user')
            job_status = batch_resume_parser_service.get_job_status(job_id)
            
            return {
                'success': True,
                'message': f'Batch parsing started successfully. Processing {len(validated_files)} files.',
                'job_id': job_id,
                'batch_number': job_status['batch_number'],
                'total_files': len(validated_files)
            }, 202  # Accepted
            
        except ValueError as ve:
            candidate_profile_ns.abort(400, str(ve))
        except Exception as e:
            error_msg = str(e)
            # Handle file size limit errors specifically
            if '413' in error_msg or 'Request Entity Too Large' in error_msg or 'exceeds the capacity limit' in error_msg:
                batch_limit = int(os.getenv('BATCH_UPLOAD_LIMIT', 200 * 1024 * 1024))
                batch_limit_mb = batch_limit / 1024 / 1024
                candidate_profile_ns.abort(413, 
                    f'File upload size exceeds limit. Maximum allowed: {batch_limit_mb:.1f}MB total. '
                    f'Please reduce the number of files or file sizes and try again.')
            candidate_profile_ns.abort(500, f'Failed to start batch parsing: {error_msg}')

@candidate_profile_ns.route('/batch-parse-resumes/<string:job_id>/status')
class BatchParseStatus(Resource):
    @candidate_profile_ns.doc('get_batch_parse_status')
    @candidate_profile_ns.marshal_with(batch_job_status_model)
    @candidate_profile_ns.response(404, 'Batch job not found')
    @candidate_profile_ns.response(500, 'Internal server error')
    def get(self, job_id):
        """
        Get the status of a batch resume parsing job
        
        Returns detailed information about the batch processing progress including:
        - Overall job status and progress percentage
        - Number of files processed, successful, completed, and incomplete
        - Detailed results for each file processed
        - Any errors encountered during processing
        """
        # Log the job_id for debugging
        logger.info(f"Getting status for batch job: {job_id}")
        
        # Ensure the service is properly initialized
        if not batch_resume_parser_service:
            logger.error("batch_resume_parser_service is not initialized")
            candidate_profile_ns.abort(500, 'Batch parsing service not available')
        
        # Get job status from service (with error handling)
        try:
            job_status = batch_resume_parser_service.get_job_status(job_id)
        except Exception as e:
            # Log the exception for debugging service errors
            logger.error(f"Service error getting batch job status for {job_id}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            candidate_profile_ns.abort(500, f'Service error: {str(e)}')
        
        # Check if job exists - return 404 if not found (outside try-catch)
        if job_status is None:
            logger.warning(f"Batch job not found: {job_id}")
            candidate_profile_ns.abort(404, f'Batch job {job_id} not found')
        
        logger.info(f"Successfully retrieved status for batch job: {job_id}")
        return job_status, 200

@candidate_profile_ns.route('/batch-parse-resumes/<string:job_id>/cancel')
class BatchParseCancel(Resource):
    @candidate_profile_ns.doc('cancel_batch_parse')
    def post(self, job_id):
        """
        Cancel a running batch resume parsing job
        
        Note: Jobs that are already processing individual files cannot be 
        immediately stopped, but the job will be marked as cancelled.
        """
        try:
            success = batch_resume_parser_service.cancel_job(job_id)
            
            if not success:
                candidate_profile_ns.abort(400, f'Job {job_id} cannot be cancelled (not found or already completed)')
            
            return {
                'success': True,
                'message': f'Batch job {job_id} has been cancelled'
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to cancel job: {str(e)}')

@candidate_profile_ns.route('/batch-parse-resumes/jobs')
class BatchParseJobs(Resource):
    @candidate_profile_ns.doc('get_all_batch_jobs')
    def get(self):
        """
        Get status of all active batch resume parsing jobs
        
        Returns a list of all currently tracked batch jobs with their status.
        Useful for monitoring multiple batch operations.
        """
        try:
            all_jobs = batch_resume_parser_service.list_jobs()
            
            return {
                'jobs': all_jobs,
                'total_jobs': len(all_jobs)
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get job list: {str(e)}')

@candidate_profile_ns.route('/batch-parse-resumes/config')
class BatchParseConfig(Resource):
    @candidate_profile_ns.doc('get_batch_config')
    def get(self):
        """
        Get current batch upload configuration limits
        
        Useful for debugging upload size issues and verifying configuration.
        """
        try:
            individual_file_limit = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
            batch_upload_limit = int(os.getenv('BATCH_UPLOAD_LIMIT', 200 * 1024 * 1024))
            flask_max_content = current_app.config.get('MAX_CONTENT_LENGTH', 0)
            
            return {
                'limits': {
                    'individual_file_limit_bytes': individual_file_limit,
                    'individual_file_limit_mb': round(individual_file_limit / 1024 / 1024, 1),
                    'batch_upload_limit_bytes': batch_upload_limit,
                    'batch_upload_limit_mb': round(batch_upload_limit / 1024 / 1024, 1),
                    'flask_max_content_length_bytes': flask_max_content,
                    'flask_max_content_length_mb': round(flask_max_content / 1024 / 1024, 1),
                    'max_files_per_batch': 50
                },
                'environment_variables': {
                    'MAX_CONTENT_LENGTH': os.getenv('MAX_CONTENT_LENGTH', 'Not set (default: 16MB)'),
                    'BATCH_UPLOAD_LIMIT': os.getenv('BATCH_UPLOAD_LIMIT', 'Not set (default: 200MB)')
                },
                'recommendations': {
                    'message': 'Flask uses the maximum of individual and batch limits as the hard limit.',
                    'current_effective_limit_mb': round(flask_max_content / 1024 / 1024, 1)
                }
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get configuration: {str(e)}')

@candidate_profile_ns.route('/batch-parse-resumes/debug')
class BatchParseDebug(Resource):
    @candidate_profile_ns.doc('debug_batch_service')
    def get(self):
        """
        Debug endpoint to check batch parsing service status
        
        Useful for troubleshooting 500 errors and service initialization issues.
        """
        try:
            debug_info = {
                'service_initialized': batch_resume_parser_service is not None,
                'service_type': type(batch_resume_parser_service).__name__ if batch_resume_parser_service else None,
                'active_jobs_count': 0,
                'active_jobs_keys': [],
                'service_has_active_jobs_attr': False,
                'service_errors': []
            }
            
            if batch_resume_parser_service:
                try:
                    debug_info['service_has_active_jobs_attr'] = hasattr(batch_resume_parser_service, 'active_jobs')
                    if hasattr(batch_resume_parser_service, 'active_jobs'):
                        active_jobs = getattr(batch_resume_parser_service, 'active_jobs', {})
                        debug_info['active_jobs_count'] = len(active_jobs)
                        debug_info['active_jobs_keys'] = list(active_jobs.keys())
                        debug_info['active_jobs_type'] = type(active_jobs).__name__
                    else:
                        debug_info['service_errors'].append('Service missing active_jobs attribute')
                        
                    # Test getting a non-existent job
                    test_result = batch_resume_parser_service.get_job_status('test_non_existent')
                    debug_info['test_non_existent_job_result'] = {
                        'result': test_result,
                        'result_type': type(test_result).__name__,
                        'is_none': test_result is None
                    }
                except Exception as service_error:
                    debug_info['service_errors'].append(f'Error testing service: {str(service_error)}')
            else:
                debug_info['service_errors'].append('Service is None or not initialized')
            
            return debug_info, 200
            
        except Exception as e:
            return {
                'debug_error': f'Failed to debug service: {str(e)}',
                'traceback': str(e)
            }, 500

@candidate_profile_ns.route('/batch-parse-resumes/classification-stats')
class ClassificationStats(Resource):
    @candidate_profile_ns.doc('get_classification_stats')
    def get(self):
        """
        Get statistics about available classification options
        
        Shows the available industry classifications and role tags that the AI
        can assign to candidates during batch processing.
        """
        try:
            from services.candidate_classification_service import candidate_classification_service
            
            stats = candidate_classification_service.get_classification_statistics()
            
            return {
                'classification_statistics': stats,
                'message': 'AI classification uses these lookup codes for automatic candidate classification'
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get classification statistics: {str(e)}')

@candidate_profile_ns.route('/batch-parse-resumes/<string:job_id>/failed-files')
class BatchParseFailedFiles(Resource):
    @candidate_profile_ns.doc('get_batch_failed_files')
    def get(self, job_id):
        """
        Get detailed information about failed files in a batch job
        
        Returns a list of files that failed to process with detailed error information
        including filename, error reason, failure stage, and other metadata.
        """
        try:
            # Get the batch job
            job_record = BatchJobStatus.query.filter_by(job_id=job_id).first()
            if not job_record:
                candidate_profile_ns.abort(404, f'Batch job {job_id} not found')
            
            # Get failed files for this job
            failed_files = BatchJobFailedFile.query.filter_by(batch_job_id=job_record.id).all()
            
            return {
                'job_id': job_id,
                'batch_number': job_record.batch_number,
                'total_failed_files': len(failed_files),
                'failed_files': [failed_file.to_dict() for failed_file in failed_files]
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get failed files: {str(e)}')

@candidate_profile_ns.route('/batch-parse-resumes/history')
class BatchParseHistory(Resource):
    @candidate_profile_ns.doc('get_batch_history')
    @candidate_profile_ns.param('page', 'Page number', type=int, default=1)
    @candidate_profile_ns.param('per_page', 'Items per page', type=int, default=20)
    @candidate_profile_ns.param('status', 'Filter by status (queued, processing, completed, failed, cancelled)')
    @candidate_profile_ns.param('created_by', 'Filter by user who created the job')
    def get(self):
        """
        Get paginated history of all batch parsing jobs
        
        Returns a paginated list of batch jobs with filtering options.
        Useful for monitoring and auditing batch operations.
        """
        try:
            page = request.args.get('page', 1, type=int)
            per_page = min(request.args.get('per_page', 20, type=int), 100)
            status_filter = request.args.get('status')
            created_by_filter = request.args.get('created_by')
            
            # Build query
            query = BatchJobStatus.query
            
            if status_filter:
                query = query.filter(BatchJobStatus.status == status_filter)
            
            if created_by_filter:
                query = query.filter(BatchJobStatus.created_by.ilike(f'%{created_by_filter}%'))
            
            # Order by creation date (most recent first)
            query = query.order_by(BatchJobStatus.created_at.desc())
            
            # Paginate
            paginated_jobs = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'jobs': [job.to_dict(include_details=False) for job in paginated_jobs.items],
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': paginated_jobs.total,
                    'pages': paginated_jobs.pages,
                    'has_next': paginated_jobs.has_next,
                    'has_prev': paginated_jobs.has_prev
                },
                'filters': {
                    'status': status_filter,
                    'created_by': created_by_filter
                }
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get batch history: {str(e)}')

@candidate_profile_ns.route('/batch-parse-resumes/statistics')
class BatchParseStatistics(Resource):
    @candidate_profile_ns.doc('get_batch_statistics')
    def get(self):
        """
        Get overall statistics about batch parsing operations
        
        Returns summary statistics including total jobs, success rates,
        processing times, and other metrics.
        """
        try:
            # Get overall job statistics
            total_jobs = BatchJobStatus.query.count()
            completed_jobs = BatchJobStatus.query.filter_by(status='completed').count()
            failed_jobs = BatchJobStatus.query.filter_by(status='failed').count()
            processing_jobs = BatchJobStatus.query.filter_by(status='processing').count()
            queued_jobs = BatchJobStatus.query.filter_by(status='queued').count()
            cancelled_jobs = BatchJobStatus.query.filter_by(status='cancelled').count()
            
            # Get file processing statistics
            total_files_processed = db.session.query(db.func.sum(BatchJobStatus.processed_files)).scalar() or 0
            total_successful_profiles = db.session.query(db.func.sum(BatchJobStatus.successful_profiles)).scalar() or 0
            total_failed_files = db.session.query(db.func.sum(BatchJobStatus.failed_files)).scalar() or 0
            total_completed_profiles = db.session.query(db.func.sum(BatchJobStatus.completed_profiles)).scalar() or 0
            total_incomplete_profiles = db.session.query(db.func.sum(BatchJobStatus.incomplete_profiles)).scalar() or 0
            
            # Calculate success rates
            job_success_rate = (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0
            file_success_rate = (total_successful_profiles / total_files_processed * 100) if total_files_processed > 0 else 0
            profile_completion_rate = (total_completed_profiles / total_successful_profiles * 100) if total_successful_profiles > 0 else 0
            
            # Get AI processing statistics
            total_ai_summaries_generated = db.session.query(db.func.sum(BatchJobStatus.ai_summaries_generated)).scalar() or 0
            total_ai_summaries_failed = db.session.query(db.func.sum(BatchJobStatus.ai_summaries_failed)).scalar() or 0
            total_classifications_generated = db.session.query(db.func.sum(BatchJobStatus.classifications_generated)).scalar() or 0
            total_classifications_failed = db.session.query(db.func.sum(BatchJobStatus.classifications_failed)).scalar() or 0
            
            ai_summary_success_rate = (total_ai_summaries_generated / (total_ai_summaries_generated + total_ai_summaries_failed) * 100) if (total_ai_summaries_generated + total_ai_summaries_failed) > 0 else 0
            classification_success_rate = (total_classifications_generated / (total_classifications_generated + total_classifications_failed) * 100) if (total_classifications_generated + total_classifications_failed) > 0 else 0
            
            # Get recent activity (last 24 hours)
            from datetime import datetime, timedelta
            last_24h = datetime.utcnow() - timedelta(hours=24)
            recent_jobs = BatchJobStatus.query.filter(BatchJobStatus.created_at >= last_24h).count()
            
            return {
                'job_statistics': {
                    'total_jobs': total_jobs,
                    'completed_jobs': completed_jobs,
                    'failed_jobs': failed_jobs,
                    'processing_jobs': processing_jobs,
                    'queued_jobs': queued_jobs,
                    'cancelled_jobs': cancelled_jobs,
                    'job_success_rate_percentage': round(job_success_rate, 2),
                    'recent_jobs_24h': recent_jobs
                },
                'file_processing_statistics': {
                    'total_files_processed': total_files_processed,
                    'total_successful_profiles': total_successful_profiles,
                    'total_failed_files': total_failed_files,
                    'total_completed_profiles': total_completed_profiles,
                    'total_incomplete_profiles': total_incomplete_profiles,
                    'file_success_rate_percentage': round(file_success_rate, 2),
                    'profile_completion_rate_percentage': round(profile_completion_rate, 2)
                },
                'ai_processing_statistics': {
                    'ai_summaries_generated': total_ai_summaries_generated,
                    'ai_summaries_failed': total_ai_summaries_failed,
                    'ai_summary_success_rate_percentage': round(ai_summary_success_rate, 2),
                    'classifications_generated': total_classifications_generated,
                    'classifications_failed': total_classifications_failed,
                    'classification_success_rate_percentage': round(classification_success_rate, 2)
                }
            }, 200
            
        except Exception as e:
            candidate_profile_ns.abort(500, f'Failed to get batch statistics: {str(e)}') 