from flask import Blueprint, request, jsonify
from database import db
from models import CandidateLanguages, CandidateMasterProfile
from datetime import datetime

languages_bp = Blueprint('languages', __name__)

@languages_bp.route('/', methods=['GET'])
def get_all_languages():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        is_active = request.args.get('is_active', type=bool)
        language = request.args.get('language')
        
        query = CandidateLanguages.query
        if is_active is not None:
            query = query.filter(CandidateLanguages.is_active == is_active)
        if language:
            query = query.filter(CandidateLanguages.language.ilike(f'%{language}%'))
        
        records = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'languages': [record.to_dict() for record in records.items],
            'total': records.total,
            'pages': records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/<int:language_id>', methods=['GET'])
def get_language(language_id):
    try:
        record = CandidateLanguages.query.get_or_404(language_id)
        return jsonify(record.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate_languages(candidate_id):
    try:
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        records = CandidateLanguages.query.filter_by(
            candidate_id=candidate_id, is_active=True
        ).all()
        
        return jsonify({
            'candidate_id': candidate_id,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'languages': [record.to_dict() for record in records]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/', methods=['POST'])
def create_language():
    try:
        data = request.get_json()
        
        if 'candidate_id' not in data or 'language' not in data:
            return jsonify({'error': 'candidate_id and language are required'}), 400
        
        candidate = CandidateMasterProfile.query.get(data['candidate_id'])
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        record = CandidateLanguages(
            candidate_id=data['candidate_id'],
            language=data['language'],
            proficiency_level=data.get('proficiency_level')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'message': 'Language record created successfully',
            'language': record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/<int:language_id>', methods=['PUT'])
def update_language(language_id):
    try:
        record = CandidateLanguages.query.get_or_404(language_id)
        data = request.get_json()
        
        updatable_fields = ['language', 'proficiency_level', 'is_active']
        for field in updatable_fields:
            if field in data:
                setattr(record, field, data[field])
        
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Language record updated successfully',
            'language': record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@languages_bp.route('/<int:language_id>', methods=['DELETE'])
def delete_language(language_id):
    try:
        record = CandidateLanguages.query.get_or_404(language_id)
        record.is_active = False
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Language record deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 