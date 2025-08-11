from flask import Blueprint, request, jsonify
from database import db
from models import CandidateEducation, CandidateMasterProfile
from datetime import datetime

education_bp = Blueprint('education', __name__)

@education_bp.route('/', methods=['GET'])
def get_all_education():
    """Get all education records with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        is_active = request.args.get('is_active', type=bool)
        school = request.args.get('school')
        degree = request.args.get('degree')
        
        query = CandidateEducation.query
        
        if is_active is not None:
            query = query.filter(CandidateEducation.is_active == is_active)
        if school:
            query = query.filter(CandidateEducation.school.ilike(f'%{school}%'))
        if degree:
            query = query.filter(CandidateEducation.degree.ilike(f'%{degree}%'))
        
        education_records = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'education': [record.to_dict() for record in education_records.items],
            'total': education_records.total,
            'pages': education_records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@education_bp.route('/<int:education_id>', methods=['GET'])
def get_education(education_id):
    """Get a specific education record by ID"""
    try:
        education_record = CandidateEducation.query.get_or_404(education_id)
        return jsonify(education_record.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@education_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate_education(candidate_id):
    """Get all education for a specific candidate"""
    try:
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        education_records = CandidateEducation.query.filter_by(
            candidate_id=candidate_id, is_active=True
        ).order_by(CandidateEducation.end_date.desc()).all()
        
        return jsonify({
            'candidate_id': candidate_id,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'education': [record.to_dict() for record in education_records]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@education_bp.route('/', methods=['POST'])
def create_education():
    """Create a new education record"""
    try:
        data = request.get_json()
        
        required_fields = ['candidate_id', 'school']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        candidate = CandidateMasterProfile.query.get(data['candidate_id'])
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Parse dates if provided
        start_date = end_date = None
        if data.get('start_date'):
            try:
                start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if data.get('end_date'):
            try:
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        education_record = CandidateEducation(
            candidate_id=data['candidate_id'],
            school=data['school'],
            degree=data.get('degree'),
            field_of_study=data.get('field_of_study'),
            start_date=start_date,
            end_date=end_date,
            grade=data.get('grade'),
            description=data.get('description')
        )
        
        db.session.add(education_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Education record created successfully',
            'education': education_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@education_bp.route('/<int:education_id>', methods=['PUT'])
def update_education(education_id):
    """Update an existing education record"""
    try:
        education_record = CandidateEducation.query.get_or_404(education_id)
        data = request.get_json()
        
        updatable_fields = ['school', 'degree', 'field_of_study', 'grade', 'description', 'is_active']
        for field in updatable_fields:
            if field in data:
                setattr(education_record, field, data[field])
        
        # Handle date updates
        if 'start_date' in data:
            if data['start_date']:
                try:
                    education_record.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
            else:
                education_record.start_date = None
        
        if 'end_date' in data:
            if data['end_date']:
                try:
                    education_record.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
            else:
                education_record.end_date = None
        
        education_record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Education record updated successfully',
            'education': education_record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@education_bp.route('/<int:education_id>', methods=['DELETE'])
def delete_education(education_id):
    """Delete an education record (soft delete)"""
    try:
        education_record = CandidateEducation.query.get_or_404(education_id)
        education_record.is_active = False
        education_record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Education record deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 