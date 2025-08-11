from flask import Blueprint, request, jsonify
from database import db
from models import CandidateLicensesCertifications, CandidateMasterProfile
from datetime import datetime

licenses_certifications_bp = Blueprint('licenses_certifications', __name__)

@licenses_certifications_bp.route('/', methods=['GET'])
def get_all_licenses_certifications():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        is_active = request.args.get('is_active', type=bool)
        
        query = CandidateLicensesCertifications.query
        if is_active is not None:
            query = query.filter(CandidateLicensesCertifications.is_active == is_active)
        
        records = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'licenses_certifications': [record.to_dict() for record in records.items],
            'total': records.total,
            'pages': records.pages,
            'current_page': page,
            'per_page': per_page
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@licenses_certifications_bp.route('/<int:license_id>', methods=['GET'])
def get_license_certification(license_id):
    try:
        record = CandidateLicensesCertifications.query.get_or_404(license_id)
        return jsonify(record.to_dict()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@licenses_certifications_bp.route('/candidate/<int:candidate_id>', methods=['GET'])
def get_candidate_licenses_certifications(candidate_id):
    try:
        candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
        records = CandidateLicensesCertifications.query.filter_by(
            candidate_id=candidate_id, is_active=True
        ).all()
        
        return jsonify({
            'candidate_id': candidate_id,
            'candidate_name': f"{candidate.first_name} {candidate.last_name}",
            'licenses_certifications': [record.to_dict() for record in records]
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@licenses_certifications_bp.route('/', methods=['POST'])
def create_license_certification():
    try:
        data = request.get_json()
        
        if 'candidate_id' not in data or 'license_certification_name' not in data:
            return jsonify({'error': 'candidate_id and license_certification_name are required'}), 400
        
        candidate = CandidateMasterProfile.query.get(data['candidate_id'])
        if not candidate:
            return jsonify({'error': 'Candidate not found'}), 404
        
        # Parse dates
        issue_date = expiry_date = None
        if data.get('issue_date'):
            try:
                issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid issue_date format. Use YYYY-MM-DD'}), 400
        
        if data.get('expiry_date'):
            try:
                expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid expiry_date format. Use YYYY-MM-DD'}), 400
        
        record = CandidateLicensesCertifications(
            candidate_id=data['candidate_id'],
            license_certification_name=data['license_certification_name'],
            issuing_organisation=data.get('issuing_organisation'),
            issue_date=issue_date,
            expiry_date=expiry_date,
            is_no_expiry=data.get('is_no_expiry', False),
            description=data.get('description')
        )
        
        db.session.add(record)
        db.session.commit()
        
        return jsonify({
            'message': 'License/Certification created successfully',
            'license_certification': record.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@licenses_certifications_bp.route('/<int:license_id>', methods=['PUT'])
def update_license_certification(license_id):
    try:
        record = CandidateLicensesCertifications.query.get_or_404(license_id)
        data = request.get_json()
        
        updatable_fields = ['license_certification_name', 'issuing_organisation', 'is_no_expiry', 'description', 'is_active']
        for field in updatable_fields:
            if field in data:
                setattr(record, field, data[field])
        
        # Handle date updates
        if 'issue_date' in data:
            if data['issue_date']:
                try:
                    record.issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid issue_date format. Use YYYY-MM-DD'}), 400
            else:
                record.issue_date = None
        
        if 'expiry_date' in data:
            if data['expiry_date']:
                try:
                    record.expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid expiry_date format. Use YYYY-MM-DD'}), 400
            else:
                record.expiry_date = None
        
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'License/Certification updated successfully',
            'license_certification': record.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@licenses_certifications_bp.route('/<int:license_id>', methods=['DELETE'])
def delete_license_certification(license_id):
    try:
        record = CandidateLicensesCertifications.query.get_or_404(license_id)
        record.is_active = False
        record.last_modified_date = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'License/Certification deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500 