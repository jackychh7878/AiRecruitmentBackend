from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import CandidateLanguages, CandidateMasterProfile
from datetime import datetime

languages_ns = Namespace('languages', description='Languages operations')

# Define Swagger models
language_model = languages_ns.model('Language', {
    'id': fields.Integer(readonly=True, description='Language ID'),
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'language': fields.String(required=True, description='Language name'),
    'proficiency_level': fields.String(description='Proficiency level (e.g., Beginner, Intermediate, Advanced, Native)'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

language_input_model = languages_ns.model('LanguageInput', {
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'language': fields.String(required=True, description='Language name'),
    'proficiency_level': fields.String(description='Proficiency level (e.g., Beginner, Intermediate, Advanced, Native)')
})

language_list_model = languages_ns.model('LanguageList', {
    'languages': fields.List(fields.Nested(language_model)),
    'total': fields.Integer(description='Total number of language records'),
    'pages': fields.Integer(description='Total number of pages'),
    'current_page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page')
})

@languages_ns.route('/')
class LanguagesList(Resource):
    @languages_ns.doc('get_all_languages')
    @languages_ns.param('page', 'Page number', type=int, default=1)
    @languages_ns.param('per_page', 'Items per page', type=int, default=10)
    @languages_ns.param('candidate_id', 'Filter by candidate ID', type=int)
    @languages_ns.param('language', 'Filter by language name')
    @languages_ns.param('proficiency_level', 'Filter by proficiency level')
    @languages_ns.param('is_active', 'Filter by active status', type=bool)
    def get(self):
        """Get all language records with optional filtering"""
        try:
            # Query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            candidate_id = request.args.get('candidate_id', type=int)
            language = request.args.get('language')
            proficiency_level = request.args.get('proficiency_level')
            is_active = request.args.get('is_active', type=bool)
            
            # Build query
            query = CandidateLanguages.query
            
            if candidate_id:
                query = query.filter(CandidateLanguages.candidate_id == candidate_id)
            if language:
                query = query.filter(CandidateLanguages.language.ilike(f'%{language}%'))
            if proficiency_level:
                query = query.filter(CandidateLanguages.proficiency_level.ilike(f'%{proficiency_level}%'))
            if is_active is not None:
                query = query.filter(CandidateLanguages.is_active == is_active)
            
            # Pagination
            language_records = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'languages': [lang.to_dict() for lang in language_records.items],
                'total': language_records.total,
                'pages': language_records.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
            
        except Exception as e:
            languages_ns.abort(500, str(e))

    @languages_ns.doc('create_language')
    @languages_ns.expect(language_input_model)
    def post(self):
        """Create a new language record"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('candidate_id'):
                languages_ns.abort(400, 'candidate_id is required')
            if not data.get('language'):
                languages_ns.abort(400, 'language is required')
            
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get(data['candidate_id'])
            if not candidate:
                languages_ns.abort(404, 'Candidate not found')
            
            # Check for duplicate language for the same candidate
            existing_language = CandidateLanguages.query.filter(
                CandidateLanguages.candidate_id == data['candidate_id'],
                CandidateLanguages.language.ilike(data['language']),
                CandidateLanguages.is_active == True
            ).first()
            
            if existing_language:
                languages_ns.abort(400, f'Language "{data["language"]}" already exists for this candidate')
            
            # Create new language record
            language_record = CandidateLanguages(
                candidate_id=data['candidate_id'],
                language=data['language'],
                proficiency_level=data.get('proficiency_level')
            )
            
            db.session.add(language_record)
            db.session.commit()
            
            return language_record.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            languages_ns.abort(500, str(e))

@languages_ns.route('/<int:language_id>')
@languages_ns.param('language_id', 'Language ID')
class Language(Resource):
    @languages_ns.doc('get_language')
    def get(self, language_id):
        """Get a specific language record by ID"""
        try:
            language_record = CandidateLanguages.query.get_or_404(language_id)
            return language_record.to_dict(), 200
            
        except Exception as e:
            languages_ns.abort(500, str(e))

    @languages_ns.doc('update_language')
    @languages_ns.expect(language_input_model)
    def put(self, language_id):
        """Update an existing language record"""
        try:
            language_record = CandidateLanguages.query.get_or_404(language_id)
            data = request.get_json()
            
            # Verify candidate exists if being changed
            if 'candidate_id' in data:
                candidate = CandidateMasterProfile.query.get(data['candidate_id'])
                if not candidate:
                    languages_ns.abort(404, 'Candidate not found')
            
            # Check for duplicate language if language is being changed
            if 'language' in data and data['language'] != language_record.language:
                candidate_id = data.get('candidate_id', language_record.candidate_id)
                existing_language = CandidateLanguages.query.filter(
                    CandidateLanguages.candidate_id == candidate_id,
                    CandidateLanguages.language.ilike(data['language']),
                    CandidateLanguages.is_active == True,
                    CandidateLanguages.id != language_id
                ).first()
                
                if existing_language:
                    languages_ns.abort(400, f'Language "{data["language"]}" already exists for this candidate')
            
            # Update fields
            updatable_fields = ['candidate_id', 'language', 'proficiency_level', 'is_active']
            
            for field in updatable_fields:
                if field in data:
                    setattr(language_record, field, data[field])
            
            language_record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return language_record.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            languages_ns.abort(500, str(e))

    @languages_ns.doc('delete_language')
    def delete(self, language_id):
        """Delete a language record (soft delete)"""
        try:
            language_record = CandidateLanguages.query.get_or_404(language_id)
            
            # Soft delete
            language_record.is_active = False
            language_record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'Language record deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            languages_ns.abort(500, str(e))

@languages_ns.route('/<int:language_id>/hard-delete')
@languages_ns.param('language_id', 'Language ID')
class LanguageHardDelete(Resource):
    @languages_ns.doc('hard_delete_language')
    def delete(self, language_id):
        """Permanently delete a language record"""
        try:
            language_record = CandidateLanguages.query.get_or_404(language_id)
            
            db.session.delete(language_record)
            db.session.commit()
            
            return {'message': 'Language record permanently deleted'}, 200
            
        except Exception as e:
            db.session.rollback()
            languages_ns.abort(500, str(e))

@languages_ns.route('/candidate/<int:candidate_id>')
@languages_ns.param('candidate_id', 'Candidate ID')
class CandidateLanguagesList(Resource):
    @languages_ns.doc('get_candidate_languages')
    @languages_ns.param('is_active', 'Filter by active status', type=bool)
    @languages_ns.param('proficiency_level', 'Filter by proficiency level')
    def get(self, candidate_id):
        """Get all language records for a specific candidate"""
        try:
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            is_active = request.args.get('is_active', type=bool)
            proficiency_level = request.args.get('proficiency_level')
            
            query = CandidateLanguages.query.filter(CandidateLanguages.candidate_id == candidate_id)
            
            if is_active is not None:
                query = query.filter(CandidateLanguages.is_active == is_active)
            
            if proficiency_level:
                query = query.filter(CandidateLanguages.proficiency_level.ilike(f'%{proficiency_level}%'))
            
            language_records = query.all()
            
            return {
                'candidate_id': candidate_id,
                'languages': [lang.to_dict() for lang in language_records],
                'total': len(language_records)
            }, 200
            
        except Exception as e:
            languages_ns.abort(500, str(e))

@languages_ns.route('/proficiency-levels')
class LanguageProficiencyLevels(Resource):
    @languages_ns.doc('get_proficiency_levels')
    def get(self):
        """Get suggested language proficiency levels"""
        try:
            # Common language proficiency levels
            proficiency_levels = [
                {
                    'level': 'Beginner',
                    'description': 'Basic understanding and limited vocabulary'
                },
                {
                    'level': 'Elementary',
                    'description': 'Basic conversational ability'
                },
                {
                    'level': 'Intermediate',
                    'description': 'Good working knowledge'
                },
                {
                    'level': 'Advanced',
                    'description': 'Fluent with good comprehension'
                },
                {
                    'level': 'Proficient',
                    'description': 'Highly proficient, near-native level'
                },
                {
                    'level': 'Native',
                    'description': 'Native speaker'
                }
            ]
            
            return {
                'proficiency_levels': proficiency_levels
            }, 200
            
        except Exception as e:
            languages_ns.abort(500, str(e)) 