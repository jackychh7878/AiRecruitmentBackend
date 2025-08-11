from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import CandidateSkills, CandidateMasterProfile, CandidateCareerHistory
from datetime import datetime

skills_ns = Namespace('skills', description='Skills operations')

# Define Swagger models
skill_model = skills_ns.model('Skill', {
    'id': fields.Integer(readonly=True, description='Skill ID'),
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'career_history_id': fields.Integer(description='Career history ID (optional)'),
    'skills': fields.String(required=True, description='Skills description'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

skill_input_model = skills_ns.model('SkillInput', {
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'career_history_id': fields.Integer(description='Career history ID (optional)'),
    'skills': fields.String(required=True, description='Skills description')
})

skill_list_model = skills_ns.model('SkillList', {
    'skills': fields.List(fields.Nested(skill_model)),
    'total': fields.Integer(description='Total number of skills'),
    'pages': fields.Integer(description='Total number of pages'),
    'current_page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page')
})

@skills_ns.route('/')
class SkillsList(Resource):
    @skills_ns.doc('get_all_skills')
    @skills_ns.param('page', 'Page number', type=int, default=1)
    @skills_ns.param('per_page', 'Items per page', type=int, default=10)
    @skills_ns.param('candidate_id', 'Filter by candidate ID', type=int)
    @skills_ns.param('career_history_id', 'Filter by career history ID', type=int)
    @skills_ns.param('is_active', 'Filter by active status', type=bool)
    def get(self):
        """Get all skills with optional filtering"""
        try:
            # Query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            candidate_id = request.args.get('candidate_id', type=int)
            career_history_id = request.args.get('career_history_id', type=int)
            is_active = request.args.get('is_active', type=bool)
            
            # Build query
            query = CandidateSkills.query
            
            if candidate_id:
                query = query.filter(CandidateSkills.candidate_id == candidate_id)
            if career_history_id:
                query = query.filter(CandidateSkills.career_history_id == career_history_id)
            if is_active is not None:
                query = query.filter(CandidateSkills.is_active == is_active)
            
            # Pagination
            skills = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'skills': [skill.to_dict() for skill in skills.items],
                'total': skills.total,
                'pages': skills.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
            
        except Exception as e:
            skills_ns.abort(500, str(e))

    @skills_ns.doc('create_skill')
    @skills_ns.expect(skill_input_model)
    def post(self):
        """Create a new skill record"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('candidate_id'):
                skills_ns.abort(400, 'candidate_id is required')
            if not data.get('skills'):
                skills_ns.abort(400, 'skills is required')
            
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get(data['candidate_id'])
            if not candidate:
                skills_ns.abort(404, 'Candidate not found')
            
            # Verify career history exists if provided
            if data.get('career_history_id'):
                career_history = CandidateCareerHistory.query.get(data['career_history_id'])
                if not career_history:
                    skills_ns.abort(404, 'Career history not found')
                if career_history.candidate_id != data['candidate_id']:
                    skills_ns.abort(400, 'Career history does not belong to the specified candidate')
            
            # Create new skill
            skill = CandidateSkills(
                candidate_id=data['candidate_id'],
                career_history_id=data.get('career_history_id'),
                skills=data['skills']
            )
            
            db.session.add(skill)
            db.session.commit()
            
            return skill.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            skills_ns.abort(500, str(e))

@skills_ns.route('/<int:skill_id>')
@skills_ns.param('skill_id', 'Skill ID')
class Skill(Resource):
    @skills_ns.doc('get_skill')
    def get(self, skill_id):
        """Get a specific skill by ID"""
        try:
            skill = CandidateSkills.query.get_or_404(skill_id)
            return skill.to_dict(), 200
            
        except Exception as e:
            skills_ns.abort(500, str(e))

    @skills_ns.doc('update_skill')
    @skills_ns.expect(skill_input_model)
    def put(self, skill_id):
        """Update an existing skill"""
        try:
            skill = CandidateSkills.query.get_or_404(skill_id)
            data = request.get_json()
            
            # Verify candidate exists if being changed
            if 'candidate_id' in data:
                candidate = CandidateMasterProfile.query.get(data['candidate_id'])
                if not candidate:
                    skills_ns.abort(404, 'Candidate not found')
            
            # Verify career history exists if provided
            if 'career_history_id' in data and data['career_history_id']:
                career_history = CandidateCareerHistory.query.get(data['career_history_id'])
                if not career_history:
                    skills_ns.abort(404, 'Career history not found')
                candidate_id = data.get('candidate_id', skill.candidate_id)
                if career_history.candidate_id != candidate_id:
                    skills_ns.abort(400, 'Career history does not belong to the specified candidate')
            
            # Update fields
            updatable_fields = ['candidate_id', 'career_history_id', 'skills', 'is_active']
            for field in updatable_fields:
                if field in data:
                    setattr(skill, field, data[field])
            
            skill.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return skill.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            skills_ns.abort(500, str(e))

    @skills_ns.doc('delete_skill')
    def delete(self, skill_id):
        """Delete a skill (soft delete)"""
        try:
            skill = CandidateSkills.query.get_or_404(skill_id)
            
            # Soft delete
            skill.is_active = False
            skill.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'Skill deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            skills_ns.abort(500, str(e))

@skills_ns.route('/<int:skill_id>/hard-delete')
@skills_ns.param('skill_id', 'Skill ID')
class SkillHardDelete(Resource):
    @skills_ns.doc('hard_delete_skill')
    def delete(self, skill_id):
        """Permanently delete a skill"""
        try:
            skill = CandidateSkills.query.get_or_404(skill_id)
            
            db.session.delete(skill)
            db.session.commit()
            
            return {'message': 'Skill permanently deleted'}, 200
            
        except Exception as e:
            db.session.rollback()
            skills_ns.abort(500, str(e))

@skills_ns.route('/candidate/<int:candidate_id>')
@skills_ns.param('candidate_id', 'Candidate ID')
class CandidateSkillsList(Resource):
    @skills_ns.doc('get_candidate_skills')
    @skills_ns.param('is_active', 'Filter by active status', type=bool)
    def get(self, candidate_id):
        """Get all skills for a specific candidate"""
        try:
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            is_active = request.args.get('is_active', type=bool)
            
            query = CandidateSkills.query.filter(CandidateSkills.candidate_id == candidate_id)
            
            if is_active is not None:
                query = query.filter(CandidateSkills.is_active == is_active)
            
            skills = query.all()
            
            return {
                'candidate_id': candidate_id,
                'skills': [skill.to_dict() for skill in skills],
                'total': len(skills)
            }, 200
            
        except Exception as e:
            skills_ns.abort(500, str(e)) 