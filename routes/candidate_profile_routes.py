from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import CandidateMasterProfile
from datetime import datetime
import json
from werkzeug.datastructures import FileStorage
from services.resume_parser import resume_parser

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
    'azure_blob_url': fields.String(description='Azure blob URL'),
    'file_name': fields.String(description='File name'),
    'file_size': fields.Integer(description='File size'),
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