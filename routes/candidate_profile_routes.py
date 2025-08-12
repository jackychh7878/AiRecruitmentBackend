from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import (
    CandidateMasterProfile, CandidateCareerHistory, CandidateSkills,
    CandidateEducation, CandidateLicensesCertifications, CandidateLanguages,
    CandidateResume, AiPromptTemplate
)
from datetime import datetime
import json
from werkzeug.datastructures import FileStorage
from services.resume_parser import resume_parser
from services.ai_summary_service import ai_summary_service
from services.bulk_ai_regeneration_service import bulk_ai_regeneration_service
from flask import current_app

# Create namespace
candidate_profile_ns = Namespace('candidates', description='Candidate profile operations')

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

# Define data models for Swagger documentation
candidate_model = candidate_profile_ns.model('Candidate', {
    'id': fields.Integer(readonly=True, description='Candidate ID'),
    'first_name': fields.String(required=True, description='First name'),
    'last_name': fields.String(required=True, description='Last name'),
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

@candidate_profile_ns.route('/')
class CandidateList(Resource):
    @candidate_profile_ns.doc('get_all_candidates')
    @candidate_profile_ns.param('page', 'Page number', type=int, default=1)
    @candidate_profile_ns.param('per_page', 'Items per page', type=int, default=10)
    @candidate_profile_ns.param('is_active', 'Filter by active status', type=bool)
    @candidate_profile_ns.param('classification', 'Filter by classification')
    @candidate_profile_ns.param('sub_classification', 'Filter by sub-classification')
    @candidate_profile_ns.param('location', 'Filter by location')
    @candidate_profile_ns.param('include_relationships', 'Include related data', type=bool, default=False)
    def get(self):
        """Get all candidates with optional filtering"""
        try:
            # Query parameters for filtering
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            is_active = request.args.get('is_active', type=bool)
            classification = request.args.get('classification')
            sub_classification = request.args.get('sub_classification')
            location = request.args.get('location')
            include_relationships = request.args.get('include_relationships', 'false').lower() == 'true'
            
            # Build query
            query = CandidateMasterProfile.query
            
            if is_active is not None:
                query = query.filter(CandidateMasterProfile.is_active == is_active)
            if classification:
                query = query.filter(CandidateMasterProfile.classification_of_interest.ilike(f'%{classification}%'))
            if sub_classification:
                query = query.filter(CandidateMasterProfile.sub_classification_of_interest.ilike(f'%{sub_classification}%'))
            if location:
                query = query.filter(CandidateMasterProfile.location.ilike(f'%{location}%'))
            
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
                'first_name', 'last_name', 'email', 'location', 'phone_number',
                'personal_summary', 'availability_weeks', 'preferred_work_types',
                'right_to_work', 'salary_expectation', 'classification_of_interest',
                'sub_classification_of_interest', 'is_active', 'remarks',
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
                    'first_name', 'last_name', 'email', 'location', 'phone_number',
                    'personal_summary', 'availability_weeks', 'preferred_work_types',
                    'right_to_work', 'salary_expectation', 'classification_of_interest',
                    'sub_classification_of_interest', 'is_active', 'remarks', 'metadata_json'
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
                    CandidateMasterProfile.sub_classification_of_interest.ilike(f'%{query_text}%')
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
        Parse PDF resume and extract candidate information using NER
        
        This endpoint uses Named Entity Recognition (NER) and PDF text extraction 
        to automatically extract candidate profile information from uploaded resume PDFs.
        
        Based on methodology from: https://medium.com/pythons-gurus/performing-resum%C3%A9-analysis-using-ner-with-cosine-similarity-8eb99879cda4
        
        Returns structured candidate data that can be used to prefill 
        candidate creation forms in the frontend.
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
            
            # Parse the resume using NER service
            try:
                parsed_data = resume_parser.parse_resume(file)
                
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
                        'last_name': bool(parsed_data.get('last_name'))
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
                
                # Prepare response
                response_data = {
                    'success': True,
                    'message': f'Resume parsed successfully. Extracted {sum(parsing_stats["entities_extracted"].values())} entities with {parsing_stats["completeness_score"]}% completeness.',
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
                        'First name', 'Last name', 'Email', 'Phone number', 'Location'
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