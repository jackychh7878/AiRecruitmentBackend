from flask import Blueprint, request, jsonify
from database import db
from models import CandidateCareerHistory, CandidateMasterProfile
from datetime import datetime, date

career_history_bp = Blueprint('career_history', __name__)

@career_history_bp.route('/', methods=['GET'])
def get_all_career_history():
    """Get all career history records with optional filtering"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        is_active = request.args.get('is_active', type=bool)
        company_name = request.args.get('company_name')
        job_title = request.args.get('job_title')
        
        # Build query
        query = CandidateCareerHistory.query
        
        if is_active is not None:
            query = query.filter(CandidateCareerHistory.is_active == is_active)
        if company_name:
            query = query.filter(CandidateCareerHistory.company_name.ilike(f'%{company_name}%'))
        if job_title:
            query = query.filter(CandidateCareerHistory.job_title.ilike(f'%{job_title}%'))
        
        # Pagination
        career_records = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'career_history': [record.to_dict() for record in career_records.items],
            'total': career_records.total,
            'pages': career_records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/<int:career_id>', methods=['GET'])
def get_career_history(career_id):
    """Get a specific career history record by ID"""
    try:
        career_record = CandidateCareerHistory.query.get_or_404(career_id)
        return jsonify(career_record.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate_career_history(candidate_id):
    """Get all career history for a specific candidate"""
    try:
        # Verify candidate exists
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        
        # Get career history
        career_records = CandidateCareerHistory.query.filter_by(
            candidate_id=candidate_id,
            is_active=True
        ).order_by(CandidateCareerHistory.start_date.desc()).all()
        
        return jsonify({
            'candidate_id': candidate_id,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'career_history': [record.to_dict() for record in career_records]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/', methods=['POST'])
def create_career_history():
    """Create a new career history record"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['candidate_id', 'job_title', 'company_name', 'start_date']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify candidate exists
        candidate = CandidateMasterProfile.query.get(data['candidate_id'])
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Parse dates
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = None
            if data.get('end_date'):
                end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Validate date logic
        if end_date and end_date < start_date:
            return jsonify({'error': 'End date cannot be before start date'}), 400
        
        # Create new career history record
        career_record = CandidateCareerHistory(
            candidate_id=data['candidate_id'],
            job_title=data['job_title'],
            company_name=data['company_name'],
            start_date=start_date,
            end_date=end_date,
            description=data.get('description')
        )
        
        db.session.add(career_record)
        db.session.commit()
        
        return jsonify({
            'message': 'Career history record created successfully',
            'career_history': career_record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/<int:career_id>', methods=['PUT'])
def update_career_history(career_id):
    """Update an existing career history record"""
    try:
        career_record = CandidateCareerHistory.query.get_or_404(career_id)
        data = request.get_json()
        
        # Update fields
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
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if 'end_date' in data:
            if data['end_date']:
                try:
                    career_record.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
            else:
                career_record.end_date = None
        
        # Validate date logic
        if career_record.end_date and career_record.end_date < career_record.start_date:
            return jsonify({'error': 'End date cannot be before start date'}), 400
        
        career_record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Career history record updated successfully',
            'career_history': career_record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/<int:career_id>', methods=['DELETE'])
def delete_career_history(career_id):
    """Delete a career history record (soft delete)"""
    try:
        career_record = CandidateCareerHistory.query.get_or_404(career_id)
        
        # Soft delete by setting is_active to False
        career_record.is_active = False
        career_record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Career history record deleted successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/<int:career_id>/hard-delete', methods=['DELETE'])
def hard_delete_career_history(career_id):
    """Permanently delete a career history record"""
    try:
        career_record = CandidateCareerHistory.query.get_or_404(career_id)
        
        db.session.delete(career_record)
        db.session.commit()
        
        return jsonify({'message': 'Career history record permanently deleted'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/current-positions', methods=['GET'])
def get_current_positions():
    """Get all current positions (end_date is null)"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Query for current positions
        query = CandidateCareerHistory.query.filter(
            CandidateCareerHistory.end_date.is_(None),
            CandidateCareerHistory.is_active == True
        ).order_by(CandidateCareerHistory.start_date.desc())
        
        current_positions = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'current_positions': [record.to_dict() for record in current_positions.items],
            'total': current_positions.total,
            'pages': current_positions.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@career_history_bp.route('/stats', methods=['GET'])
def get_career_history_stats():
    """Get career history statistics"""
    try:
        total_records = CandidateCareerHistory.query.filter_by(is_active=True).count()
        current_positions = CandidateCareerHistory.query.filter(
            CandidateCareerHistory.end_date.is_(None),
            CandidateCareerHistory.is_active == True
        ).count()
        
        # Top companies by number of employees
        company_stats = db.session.query(
            CandidateCareerHistory.company_name,
            db.func.count(CandidateCareerHistory.id)
        ).filter(CandidateCareerHistory.is_active == True).group_by(
            CandidateCareerHistory.company_name
        ).order_by(db.func.count(CandidateCareerHistory.id).desc()).limit(10).all()
        
        # Top job titles
        job_title_stats = db.session.query(
            CandidateCareerHistory.job_title,
            db.func.count(CandidateCareerHistory.id)
        ).filter(CandidateCareerHistory.is_active == True).group_by(
            CandidateCareerHistory.job_title
        ).order_by(db.func.count(CandidateCareerHistory.id).desc()).limit(10).all()
        
        return jsonify({
            'total_records': total_records,
            'current_positions': current_positions,
            'top_companies': [
                {'company': stat[0], 'count': stat[1]} 
                for stat in company_stats
            ],
            'top_job_titles': [
                {'job_title': stat[0], 'count': stat[1]} 
                for stat in job_title_stats
            ]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 