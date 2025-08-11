from flask import Blueprint, request, jsonify
from app import db
from models import CandidateSkills, CandidateMasterProfile, CandidateCareerHistory
from datetime import datetime

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('/', methods=['GET'])
def get_all_skills():
    """Get all skills with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        is_active = request.args.get('is_active', type=bool)
        skill_name = request.args.get('skill_name')
        
        # Build query
        query = CandidateSkills.query
        
        if is_active is not None:
            query = query.filter(CandidateSkills.is_active == is_active)
        if skill_name:
            query = query.filter(CandidateSkills.skills.ilike(f'%{skill_name}%'))
        
        # Pagination
        skills_records = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'skills': [record.to_dict() for record in skills_records.items],
            'total': skills_records.total,
            'pages': skills_records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/<int:skill_id>', methods=['GET'])
def get_skill(skill_id):
    """Get a specific skill record by ID"""
    try:
        skill_record = CandidateSkills.query.get_or_404(skill_id)
        return jsonify(skill_record.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate_skills(candidate_id):
    """Get all skills for a specific candidate"""
    try:
        # Verify candidate exists
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        
        # Get skills
        skills_records = CandidateSkills.query.filter_by(
            candidate_id=candidate_id,
            is_active=True
        ).all()
        
        return jsonify({
            'candidate_id': candidate_id,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'skills': [record.to_dict() for record in skills_records]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/', methods=['POST'])
def create_skill():
    """Create a new skill record"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['candidate_id', 'skills']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify candidate exists
        candidate = CandidateMasterProfile.query.get(data['candidate_id'])
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Verify career history exists if provided
        if data.get('career_history_id'):
            career_history = CandidateCareerHistory.query.get(data['career_history_id'])
            if not career_history:
                return jsonify({'error': 'Career history not found'}), 404
            if career_history.candidate_id != data['candidate_id']:
                return jsonify({'error': 'Career history does not belong to this candidate'}), 400
        
        # Create new skill record
        skill_record = CandidateSkills(
            candidate_id=data['candidate_id'],
            career_history_id=data.get('career_history_id'),
            skills=data['skills']
        )
        
        db.session.add(skill_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Skill record created successfully',
            'skill': skill_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/<int:skill_id>', methods=['PUT'])
def update_skill(skill_id):
    """Update an existing skill record"""
    try:
        skill_record = CandidateSkills.query.get_or_404(skill_id)
        data = request.get_json()
        
        # Update fields
        if 'skills' in data:
            skill_record.skills = data['skills']
        if 'career_history_id' in data:
            if data['career_history_id']:
                # Verify career history exists and belongs to the same candidate
                career_history = CandidateCareerHistory.query.get(data['career_history_id'])
                if not career_history:
                    return jsonify({'error': 'Career history not found'}), 404
                if career_history.candidate_id != skill_record.candidate_id:
                    return jsonify({'error': 'Career history does not belong to this candidate'}), 400
            skill_record.career_history_id = data['career_history_id']
        if 'is_active' in data:
            skill_record.is_active = data['is_active']
        
        skill_record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Skill record updated successfully',
            'skill': skill_record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/<int:skill_id>', methods=['DELETE'])
def delete_skill(skill_id):
    """Delete a skill record (soft delete)"""
    try:
        skill_record = CandidateSkills.query.get_or_404(skill_id)
        
        # Soft delete by setting is_active to False
        skill_record.is_active = False
        skill_record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Skill record deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/popular', methods=['GET'])
def get_popular_skills():
    """Get most popular skills across all candidates"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        # Get skill popularity
        skill_stats = db.session.query(
            CandidateSkills.skills,
            db.func.count(CandidateSkills.id).label('count'),
            db.func.count(db.distinct(CandidateSkills.candidate_id)).label('unique_candidates')
        ).filter(CandidateSkills.is_active == True).group_by(
            CandidateSkills.skills
        ).order_by(db.func.count(CandidateSkills.id).desc()).limit(limit).all()
        
        return jsonify({
            'popular_skills': [
                {
                    'skill': stat[0], 
                    'total_occurrences': stat[1],
                    'unique_candidates': stat[2]
                } 
                for stat in skill_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@skills_bp.route('/bulk', methods=['POST'])
def create_bulk_skills():
    """Create multiple skills for a candidate at once"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if 'candidate_id' not in data or not data['candidate_id']:
            return jsonify({'error': 'candidate_id is required'}), 400
        if 'skills' not in data or not isinstance(data['skills'], list):
            return jsonify({'error': 'skills array is required'}), 400
        
        # Verify candidate exists
        candidate = CandidateMasterProfile.query.get(data['candidate_id'])
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        created_skills = []
        
        for skill_name in data['skills']:
            if skill_name and skill_name.strip():
                skill_record = CandidateSkills(
                    candidate_id=data['candidate_id'],
                    career_history_id=data.get('career_history_id'),
                    skills=skill_name.strip()
                )
                db.session.add(skill_record)
                created_skills.append(skill_record)
        
        db.session.commit()
        
        return jsonify({
            'message': f'{len(created_skills)} skill records created successfully',
            'skills': [skill.to_dict() for skill in created_skills]
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 