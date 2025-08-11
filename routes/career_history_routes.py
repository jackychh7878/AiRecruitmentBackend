from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import CandidateCareerHistory, CandidateMasterProfile
from datetime import datetime, date

# Create namespace
career_history_ns = Namespace('career_history', description='Career history operations')

# Define data models for Swagger documentation
career_history_model = career_history_ns.model('CareerHistory', {
    'id': fields.Integer(readonly=True, description='Career history ID'),
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'job_title': fields.String(required=True, description='Job title'),
    'company_name': fields.String(required=True, description='Company name'),
    'start_date': fields.Date(required=True, description='Start date'),
    'end_date': fields.Date(description='End date'),
    'description': fields.String(description='Job description'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

career_history_input_model = career_history_ns.model('CareerHistoryInput', {
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'job_title': fields.String(required=True, description='Job title'),
    'company_name': fields.String(required=True, description='Company name'),
    'start_date': fields.String(required=True, description='Start date (YYYY-MM-DD)'),
    'end_date': fields.String(description='End date (YYYY-MM-DD)'),
    'description': fields.String(description='Job description')
})

@career_history_ns.route('/')
class CareerHistoryList(Resource):
    @career_history_ns.doc('get_all_career_history')
    @career_history_ns.param('page', 'Page number', type=int, default=1)
    @career_history_ns.param('per_page', 'Items per page', type=int, default=10)
    @career_history_ns.param('candidate_id', 'Filter by candidate ID', type=int)
    @career_history_ns.param('is_active', 'Filter by active status', type=bool)
    def get(self):
        """Get all career history records"""
        try:
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            candidate_id = request.args.get('candidate_id', type=int)
            is_active = request.args.get('is_active', type=bool)
            
            query = CandidateCareerHistory.query
            if candidate_id:
                query = query.filter(CandidateCareerHistory.candidate_id == candidate_id)
            if is_active is not None:
                query = query.filter(CandidateCareerHistory.is_active == is_active)
            
            records = query.order_by(CandidateCareerHistory.start_date.desc()).paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'career_history': [record.to_dict() for record in records.items],
                'total': records.total,
                'pages': records.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
        except Exception as e:
            career_history_ns.abort(500, str(e))

    @career_history_ns.doc('create_career_history')
    @career_history_ns.expect(career_history_input_model)
    @career_history_ns.marshal_with(career_history_model, code=201)
    def post(self):
        """Create a new career history record"""
        try:
            data = request.get_json()
            
            # Validate required fields
            required_fields = ['candidate_id', 'job_title', 'company_name', 'start_date']
            for field in required_fields:
                if field not in data or not data[field]:
                    career_history_ns.abort(400, f'{field} is required')
            
            # Validate candidate exists
            candidate = CandidateMasterProfile.query.get(data['candidate_id'])
            if not candidate:
                career_history_ns.abort(404, 'Candidate not found')
            
            # Parse dates
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                end_date = None
                if data.get('end_date'):
                    end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                career_history_ns.abort(400, 'Invalid date format. Use YYYY-MM-DD')
            
            record = CandidateCareerHistory(
                candidate_id=data['candidate_id'],
                job_title=data['job_title'],
                company_name=data['company_name'],
                start_date=start_date,
                end_date=end_date,
                description=data.get('description')
            )
            
            db.session.add(record)
            db.session.commit()
            
            return record.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            career_history_ns.abort(500, str(e))

@career_history_ns.route('/<int:career_id>')
@career_history_ns.param('career_id', 'Career history ID')
class CareerHistory(Resource):
    @career_history_ns.doc('get_career_history')
    @career_history_ns.marshal_with(career_history_model)
    def get(self, career_id):
        """Get a specific career history record by ID"""
        try:
            career_record = CandidateCareerHistory.query.get_or_404(career_id)
            return career_record.to_dict(), 200
        except Exception as e:
            career_history_ns.abort(500, str(e))

    @career_history_ns.doc('update_career_history')
    @career_history_ns.expect(career_history_input_model)
    @career_history_ns.marshal_with(career_history_model)
    def put(self, career_id):
        """Update an existing career history record"""
        try:
            career_record = CandidateCareerHistory.query.get_or_404(career_id)
            data = request.get_json()
            
            # Update basic fields
            if 'job_title' in data:
                career_record.job_title = data['job_title']
            if 'company_name' in data:
                career_record.company_name = data['company_name']
            if 'description' in data:
                career_record.description = data['description']
            if 'is_active' in data:
                career_record.is_active = data['is_active']
            
            # Handle date updates
            if 'start_date' in data:
                try:
                    career_record.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                except ValueError:
                    career_history_ns.abort(400, 'Invalid start_date format. Use YYYY-MM-DD')
            
            if 'end_date' in data:
                if data['end_date']:
                    try:
                        career_record.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                    except ValueError:
                        career_history_ns.abort(400, 'Invalid end_date format. Use YYYY-MM-DD')
                else:
                    career_record.end_date = None
            
            # Validate date logic
            if career_record.end_date and career_record.end_date < career_record.start_date:
                career_history_ns.abort(400, 'End date cannot be before start date')
            
            career_record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return career_record.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            career_history_ns.abort(500, str(e))

    @career_history_ns.doc('delete_career_history')
    def delete(self, career_id):
        """Delete a career history record (soft delete)"""
        try:
            career_record = CandidateCareerHistory.query.get_or_404(career_id)
            
            # Soft delete by setting is_active to False
            career_record.is_active = False
            career_record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'Career history record deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            career_history_ns.abort(500, str(e))

@career_history_ns.route('/candidate/<int:candidate_id>')
@career_history_ns.param('candidate_id', 'Candidate ID')
class CandidateCareerHistoryList(Resource):
    @career_history_ns.doc('get_candidate_career_history')
    def get(self, candidate_id):
        """Get all career history for a specific candidate"""
        try:
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            # Get career history
            career_records = CandidateCareerHistory.query.filter_by(
                candidate_id=candidate_id,
                is_active=True
            ).order_by(CandidateCareerHistory.start_date.desc()).all()
            
            return {
                'candidate_id': candidate_id,
                'candidate_name': f"{candidate.first_name} {candidate.last_name}",
                'career_history': [record.to_dict() for record in career_records]
            }, 200
            
        except Exception as e:
            career_history_ns.abort(500, str(e))

@career_history_ns.route('/stats')
class CareerHistoryStats(Resource):
    @career_history_ns.doc('get_career_history_stats')
    def get(self):
        """Get career history statistics"""
        try:
            total_records = CandidateCareerHistory.query.filter_by(is_active=True).count()
            current_positions = CandidateCareerHistory.query.filter_by(
                is_active=True, end_date=None
            ).count()
            
            return {
                'total_records': total_records,
                'current_positions': current_positions,
                'past_positions': total_records - current_positions
            }, 200
            
        except Exception as e:
            career_history_ns.abort(500, str(e)) 