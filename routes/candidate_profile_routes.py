from flask import Blueprint, request, jsonify
from app import db
from models import CandidateMasterProfile
from datetime import datetime
import json

candidate_profile_bp = Blueprint('candidate_profile', __name__)

@candidate_profile_bp.route('/', methods=['GET'])
def get_all_candidates():
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
        
        return jsonify({
            'candidates': [candidate.to_dict(include_relationships=include_relationships) for candidate in candidates.items],
            'total': candidates.total,
            'pages': candidates.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@candidate_profile_bp.route('/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    """Get a specific candidate by ID"""
    try:
        include_relationships = request.args.get('include_relationships', 'true').lower() == 'true'
        
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        return jsonify(candidate.to_dict(include_relationships=include_relationships)), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@candidate_profile_bp.route('/', methods=['POST'])
def create_candidate():
    """Create a new candidate"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if email already exists
        existing_candidate = CandidateMasterProfile.query.filter_by(email=data['email']).first()
        if existing_candidate:
            return jsonify({'error': 'Email already exists'}), 400
        
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
        
        return jsonify({
            'message': 'Candidate created successfully',
            'candidate': candidate.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@candidate_profile_bp.route('/<int:candidate_id>', methods=['PUT'])
def update_candidate(candidate_id):
    """Update an existing candidate"""
    try:
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        data = request.get_json()
        
        # Check if email is being changed and if new email already exists
        if 'email' in data and data['email'] != candidate.email:
            existing_candidate = CandidateMasterProfile.query.filter_by(email=data['email']).first()
            if existing_candidate:
                return jsonify({'error': 'Email already exists'}), 400
        
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
        
        return jsonify({
            'message': 'Candidate updated successfully',
            'candidate': candidate.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@candidate_profile_bp.route('/<int:candidate_id>', methods=['DELETE'])
def delete_candidate(candidate_id):
    """Delete a candidate (soft delete)"""
    try:
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        
        # Soft delete by setting is_active to False
        candidate.is_active = False
        candidate.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Candidate deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@candidate_profile_bp.route('/<int:candidate_id>/hard-delete', methods=['DELETE'])
def hard_delete_candidate(candidate_id):
    """Permanently delete a candidate and all related records"""
    try:
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        
        # This will cascade delete all related records due to relationship configuration
        db.session.delete(candidate)
        db.session.commit()
        
        return jsonify({'message': 'Candidate permanently deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@candidate_profile_bp.route('/search', methods=['GET'])
def search_candidates():
    """Advanced search for candidates"""
    try:
        # Search parameters
        query_text = request.args.get('q', '')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        if not query_text:
            return jsonify({'error': 'Search query is required'}), 400
        
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
        
        return jsonify({
            'candidates': [candidate.to_dict() for candidate in candidates.items],
            'total': candidates.total,
            'pages': candidates.pages,
            'current_page': page,
            'per_page': per_page,
            'search_query': query_text
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@candidate_profile_bp.route('/stats', methods=['GET'])
def get_candidate_stats():
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
        
        return jsonify({
            'total_candidates': total_candidates,
            'active_candidates': active_candidates,
            'inactive_candidates': inactive_candidates,
            'classification_breakdown': [
                {'classification': stat[0], 'count': stat[1]} 
                for stat in classification_stats if stat[0]
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 