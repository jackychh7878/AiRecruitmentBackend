from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import CandidateEducation, CandidateMasterProfile
from datetime import datetime

education_ns = Namespace('education', description='Education operations')

# Define Swagger models
education_model = education_ns.model('Education', {
    'id': fields.Integer(readonly=True, description='Education ID'),
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'school': fields.String(required=True, description='School name'),
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

education_input_model = education_ns.model('EducationInput', {
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'school': fields.String(required=True, description='School name'),
    'degree': fields.String(description='Degree'),
    'field_of_study': fields.String(description='Field of study'),
    'start_date': fields.String(description='Start date (YYYY-MM-DD)'),
    'end_date': fields.String(description='End date (YYYY-MM-DD)'),
    'grade': fields.String(description='Grade'),
    'description': fields.String(description='Description')
})

education_list_model = education_ns.model('EducationList', {
    'education': fields.List(fields.Nested(education_model)),
    'total': fields.Integer(description='Total number of education records'),
    'pages': fields.Integer(description='Total number of pages'),
    'current_page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page')
})

@education_ns.route('/')
class EducationList(Resource):
    @education_ns.doc('get_all_education')
    @education_ns.param('page', 'Page number', type=int, default=1)
    @education_ns.param('per_page', 'Items per page', type=int, default=10)
    @education_ns.param('candidate_id', 'Filter by candidate ID', type=int)
    @education_ns.param('school', 'Filter by school name')
    @education_ns.param('degree', 'Filter by degree')
    @education_ns.param('is_active', 'Filter by active status', type=bool)
    def get(self):
        """Get all education records with optional filtering"""
        try:
            # Query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            candidate_id = request.args.get('candidate_id', type=int)
            school = request.args.get('school')
            degree = request.args.get('degree')
            is_active = request.args.get('is_active', type=bool)
            
            # Build query
            query = CandidateEducation.query
            
            if candidate_id:
                query = query.filter(CandidateEducation.candidate_id == candidate_id)
            if school:
                query = query.filter(CandidateEducation.school.ilike(f'%{school}%'))
            if degree:
                query = query.filter(CandidateEducation.degree.ilike(f'%{degree}%'))
            if is_active is not None:
                query = query.filter(CandidateEducation.is_active == is_active)
            
            # Pagination
            education_records = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'education': [edu.to_dict() for edu in education_records.items],
                'total': education_records.total,
                'pages': education_records.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
            
        except Exception as e:
            education_ns.abort(500, str(e))

    @education_ns.doc('create_education')
    @education_ns.expect(education_input_model)
    def post(self):
        """Create a new education record"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('candidate_id'):
                education_ns.abort(400, 'candidate_id is required')
            if not data.get('school'):
                education_ns.abort(400, 'school is required')
            
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get(data['candidate_id'])
            if not candidate:
                education_ns.abort(404, 'Candidate not found')
            
            # Parse dates if provided
            start_date = None
            end_date = None
            if data.get('start_date'):
                try:
                    start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                except ValueError:
                    education_ns.abort(400, 'start_date must be in YYYY-MM-DD format')
            
            if data.get('end_date'):
                try:
                    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                except ValueError:
                    education_ns.abort(400, 'end_date must be in YYYY-MM-DD format')
            
            # Create new education record
            education = CandidateEducation(
                candidate_id=data['candidate_id'],
                school=data['school'],
                degree=data.get('degree'),
                field_of_study=data.get('field_of_study'),
                start_date=start_date,
                end_date=end_date,
                grade=data.get('grade'),
                description=data.get('description')
            )
            
            db.session.add(education)
            db.session.commit()
            
            return education.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            education_ns.abort(500, str(e))

@education_ns.route('/<int:education_id>')
@education_ns.param('education_id', 'Education ID')
class Education(Resource):
    @education_ns.doc('get_education')
    def get(self, education_id):
        """Get a specific education record by ID"""
        try:
            education = CandidateEducation.query.get_or_404(education_id)
            return education.to_dict(), 200
            
        except Exception as e:
            education_ns.abort(500, str(e))

    @education_ns.doc('update_education')
    @education_ns.expect(education_input_model)
    def put(self, education_id):
        """Update an existing education record"""
        try:
            education = CandidateEducation.query.get_or_404(education_id)
            data = request.get_json()
            
            # Verify candidate exists if being changed
            if 'candidate_id' in data:
                candidate = CandidateMasterProfile.query.get(data['candidate_id'])
                if not candidate:
                    education_ns.abort(404, 'Candidate not found')
            
            # Parse dates if provided
            if 'start_date' in data and data['start_date']:
                try:
                    data['start_date'] = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                except ValueError:
                    education_ns.abort(400, 'start_date must be in YYYY-MM-DD format')
            
            if 'end_date' in data and data['end_date']:
                try:
                    data['end_date'] = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                except ValueError:
                    education_ns.abort(400, 'end_date must be in YYYY-MM-DD format')
            
            # Update fields
            updatable_fields = [
                'candidate_id', 'school', 'degree', 'field_of_study', 
                'start_date', 'end_date', 'grade', 'description', 'is_active'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(education, field, data[field])
            
            education.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return education.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            education_ns.abort(500, str(e))

    @education_ns.doc('delete_education')
    def delete(self, education_id):
        """Delete an education record (soft delete)"""
        try:
            education = CandidateEducation.query.get_or_404(education_id)
            
            # Soft delete
            education.is_active = False
            education.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'Education record deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            education_ns.abort(500, str(e))

@education_ns.route('/<int:education_id>/hard-delete')
@education_ns.param('education_id', 'Education ID')
class EducationHardDelete(Resource):
    @education_ns.doc('hard_delete_education')
    def delete(self, education_id):
        """Permanently delete an education record"""
        try:
            education = CandidateEducation.query.get_or_404(education_id)
            
            db.session.delete(education)
            db.session.commit()
            
            return {'message': 'Education record permanently deleted'}, 200
            
        except Exception as e:
            db.session.rollback()
            education_ns.abort(500, str(e))

@education_ns.route('/candidate/<int:candidate_id>')
@education_ns.param('candidate_id', 'Candidate ID')
class CandidateEducationList(Resource):
    @education_ns.doc('get_candidate_education')
    @education_ns.param('is_active', 'Filter by active status', type=bool)
    def get(self, candidate_id):
        """Get all education records for a specific candidate"""
        try:
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            is_active = request.args.get('is_active', type=bool)
            
            query = CandidateEducation.query.filter(CandidateEducation.candidate_id == candidate_id)
            
            if is_active is not None:
                query = query.filter(CandidateEducation.is_active == is_active)
            
            education_records = query.all()
            
            return {
                'candidate_id': candidate_id,
                'education': [edu.to_dict() for edu in education_records],
                'total': len(education_records)
            }, 200
            
        except Exception as e:
            education_ns.abort(500, str(e)) 