from flask import Blueprint, request, jsonify
from app import db
from models import CandidateResume, CandidateMasterProfile
from datetime import datetime

resume_bp = Blueprint('resume', __name__)

@resume_bp.route('/', methods=['GET'])
def get_all_resumes():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        is_active = request.args.get('is_active', type=bool)
        
        query = CandidateResume.query
        if is_active is not None:
            query = query.filter(CandidateResume.is_active == is_active)
        
        records = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'resumes': [record.to_dict() for record in records.items],
            'total': records.total,
            'pages': records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/<int:resume_id>', methods=['GET'])
def get_resume(resume_id):
    try:
        record = CandidateResume.query.get_or_404(resume_id)
        return jsonify(record.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate_resumes(candidate_id):
    try:
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        records = CandidateResume.query.filter_by(
            candidate_id=candidate_id, is_active=True
        ).order_by(CandidateResume.upload_date.desc()).all()
        
        return jsonify({
            'candidate_id': candidate_id,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'resumes': [record.to_dict() for record in records]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/', methods=['POST'])
def create_resume():
    try:
        data = request.get_json()
        
        if 'candidate_id' not in data or 'azure_blob_url' not in data:
            return jsonify({'error': 'candidate_id and azure_blob_url are required'}), 400
        
        candidate = CandidateMasterProfile.query.get(data['candidate_id'])
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        record = CandidateResume(
            candidate_id=data['candidate_id'],
            azure_blob_url=data['azure_blob_url'],
            file_name=data.get('file_name'),
            file_size=data.get('file_size')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'message': 'Resume record created successfully',
            'resume': record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/<int:resume_id>', methods=['PUT'])
def update_resume(resume_id):
    try:
        record = CandidateResume.query.get_or_404(resume_id)
        data = request.get_json()
        
        updatable_fields = ['azure_blob_url', 'file_name', 'file_size', 'is_active']
        for field in updatable_fields:
            if field in data:
                setattr(record, field, data[field])
        
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Resume record updated successfully',
            'resume': record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@resume_bp.route('/<int:resume_id>', methods=['DELETE'])
def delete_resume(resume_id):
    try:
        record = CandidateResume.query.get_or_404(resume_id)
        record.is_active = False
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Resume record deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 