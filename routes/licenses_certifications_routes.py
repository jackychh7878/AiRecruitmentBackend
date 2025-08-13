from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import CandidateLicensesCertifications, CandidateMasterProfile
from datetime import datetime

licenses_certifications_ns = Namespace('licenses_certifications', description='Licenses and certifications operations')

# Define Swagger models
license_certification_model = licenses_certifications_ns.model('LicenseCertification', {
    'id': fields.Integer(readonly=True, description='License/Certification ID'),
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'license_certification_name': fields.String(required=True, description='License/Certification name'),
    'issuing_organisation': fields.String(description='Issuing organisation'),
    'issue_date': fields.String(description='Issue date'),
    'expiry_date': fields.String(description='Expiry date'),
    'is_no_expiry': fields.Boolean(description='Has no expiry date'),
    'description': fields.String(description='Description'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

license_certification_input_model = licenses_certifications_ns.model('LicenseCertificationInput', {
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'license_certification_name': fields.String(required=True, description='License/Certification name'),
    'issuing_organisation': fields.String(description='Issuing organisation'),
    'issue_date': fields.String(description='Issue date (YYYY-MM-DD)'),
    'expiry_date': fields.String(description='Expiry date (YYYY-MM-DD)'),
    'is_no_expiry': fields.Boolean(description='Has no expiry date'),
    'description': fields.String(description='Description')
})

license_certification_list_model = licenses_certifications_ns.model('LicenseCertificationList', {
    'licenses_certifications': fields.List(fields.Nested(license_certification_model)),
    'total': fields.Integer(description='Total number of licenses/certifications'),
    'pages': fields.Integer(description='Total number of pages'),
    'current_page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page')
})

@licenses_certifications_ns.route('/')
class LicensesCertificationsList(Resource):
    @licenses_certifications_ns.doc('get_all_licenses_certifications')
    @licenses_certifications_ns.param('page', 'Page number', type=int, default=1)
    @licenses_certifications_ns.param('per_page', 'Items per page', type=int, default=10)
    @licenses_certifications_ns.param('candidate_id', 'Filter by candidate ID', type=int)
    @licenses_certifications_ns.param('license_certification_name', 'Filter by license/certification name')
    @licenses_certifications_ns.param('issuing_organisation', 'Filter by issuing organisation')
    @licenses_certifications_ns.param('is_active', 'Filter by active status', type=bool)
    def get(self):
        """Get all licenses and certifications with optional filtering"""
        try:
            # Query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            candidate_id = request.args.get('candidate_id', type=int)
            license_certification_name = request.args.get('license_certification_name')
            issuing_organisation = request.args.get('issuing_organisation')
            is_active = request.args.get('is_active', type=bool)
            
            # Build query
            query = CandidateLicensesCertifications.query
            
            if candidate_id:
                query = query.filter(CandidateLicensesCertifications.candidate_id == candidate_id)
            if license_certification_name:
                query = query.filter(CandidateLicensesCertifications.license_certification_name.ilike(f'%{license_certification_name}%'))
            if issuing_organisation:
                query = query.filter(CandidateLicensesCertifications.issuing_organisation.ilike(f'%{issuing_organisation}%'))
            if is_active is not None:
                query = query.filter(CandidateLicensesCertifications.is_active == is_active)
            
            # Pagination
            records = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'licenses_certifications': [record.to_dict() for record in records.items],
                'total': records.total,
                'pages': records.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
            
        except Exception as e:
            licenses_certifications_ns.abort(500, str(e))

    @licenses_certifications_ns.doc('create_license_certification')
    @licenses_certifications_ns.expect(license_certification_input_model)
    def post(self):
        """Create a new license or certification record"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('candidate_id'):
                licenses_certifications_ns.abort(400, 'candidate_id is required')
            if not data.get('license_certification_name'):
                licenses_certifications_ns.abort(400, 'license_certification_name is required')
            
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get(data['candidate_id'])
            if not candidate:
                licenses_certifications_ns.abort(404, 'Candidate not found')
            
            # Parse dates if provided
            issue_date = None
            expiry_date = None
            if data.get('issue_date'):
                try:
                    issue_date = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
                except ValueError:
                    licenses_certifications_ns.abort(400, 'issue_date must be in YYYY-MM-DD format')
            
            if data.get('expiry_date'):
                try:
                    expiry_date = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                except ValueError:
                    licenses_certifications_ns.abort(400, 'expiry_date must be in YYYY-MM-DD format')
            
            # Create new license/certification record
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
            
            return record.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            licenses_certifications_ns.abort(500, str(e))

    def options(self):
        """Handle CORS preflight request"""
        return '', 200

@licenses_certifications_ns.route('/<int:record_id>')
@licenses_certifications_ns.param('record_id', 'License/Certification ID')
class LicenseCertification(Resource):
    @licenses_certifications_ns.doc('get_license_certification')
    def get(self, record_id):
        """Get a specific license or certification by ID"""
        try:
            record = CandidateLicensesCertifications.query.get_or_404(record_id)
            return record.to_dict(), 200
            
        except Exception as e:
            licenses_certifications_ns.abort(500, str(e))

    @licenses_certifications_ns.doc('update_license_certification')
    @licenses_certifications_ns.expect(license_certification_input_model)
    def put(self, record_id):
        """Update an existing license or certification"""
        try:
            record = CandidateLicensesCertifications.query.get_or_404(record_id)
            data = request.get_json()
            
            # Verify candidate exists if being changed
            if 'candidate_id' in data:
                candidate = CandidateMasterProfile.query.get(data['candidate_id'])
                if not candidate:
                    licenses_certifications_ns.abort(404, 'Candidate not found')
            
            # Parse dates if provided
            if 'issue_date' in data and data['issue_date']:
                try:
                    data['issue_date'] = datetime.strptime(data['issue_date'], '%Y-%m-%d').date()
                except ValueError:
                    licenses_certifications_ns.abort(400, 'issue_date must be in YYYY-MM-DD format')
            
            if 'expiry_date' in data and data['expiry_date']:
                try:
                    data['expiry_date'] = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date()
                except ValueError:
                    licenses_certifications_ns.abort(400, 'expiry_date must be in YYYY-MM-DD format')
            
            # Update fields
            updatable_fields = [
                'candidate_id', 'license_certification_name', 'issuing_organisation', 'issue_date', 
                'expiry_date', 'is_no_expiry', 'description', 'is_active'
            ]
            
            for field in updatable_fields:
                if field in data:
                    setattr(record, field, data[field])
            
            record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return record.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            licenses_certifications_ns.abort(500, str(e))

    @licenses_certifications_ns.doc('delete_license_certification')
    def delete(self, record_id):
        """Delete a license or certification (soft delete)"""
        try:
            record = CandidateLicensesCertifications.query.get_or_404(record_id)
            
            # Soft delete
            record.is_active = False
            record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'License/certification deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            licenses_certifications_ns.abort(500, str(e))

@licenses_certifications_ns.route('/<int:record_id>/hard-delete')
@licenses_certifications_ns.param('record_id', 'License/Certification ID')
class LicenseCertificationHardDelete(Resource):
    @licenses_certifications_ns.doc('hard_delete_license_certification')
    def delete(self, record_id):
        """Permanently delete a license or certification"""
        try:
            record = CandidateLicensesCertifications.query.get_or_404(record_id)
            
            db.session.delete(record)
            db.session.commit()
            
            return {'message': 'License/certification permanently deleted'}, 200
            
        except Exception as e:
            db.session.rollback()
            licenses_certifications_ns.abort(500, str(e))

@licenses_certifications_ns.route('/candidate/<int:candidate_id>')
@licenses_certifications_ns.param('candidate_id', 'Candidate ID')
class CandidateLicensesCertificationsList(Resource):
    @licenses_certifications_ns.doc('get_candidate_licenses_certifications')
    @licenses_certifications_ns.param('is_active', 'Filter by active status', type=bool)
    @licenses_certifications_ns.param('expired', 'Filter by expiration status (true for expired, false for active)', type=bool)
    def get(self, candidate_id):
        """Get all licenses and certifications for a specific candidate"""
        try:
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            is_active = request.args.get('is_active', type=bool)
            expired = request.args.get('expired', type=bool)
            
            query = CandidateLicensesCertifications.query.filter(CandidateLicensesCertifications.candidate_id == candidate_id)
            
            if is_active is not None:
                query = query.filter(CandidateLicensesCertifications.is_active == is_active)
            
            if expired is not None:
                today = datetime.utcnow().date()
                if expired:
                    query = query.filter(CandidateLicensesCertifications.expiry_date < today)
                else:
                    query = query.filter(db.or_(
                        CandidateLicensesCertifications.expiry_date >= today,
                        CandidateLicensesCertifications.expiry_date.is_(None),
                        CandidateLicensesCertifications.is_no_expiry == True
                    ))
            
            records = query.all()
            
            return {
                'candidate_id': candidate_id,
                'licenses_certifications': [record.to_dict() for record in records],
                'total': len(records)
            }, 200
            
        except Exception as e:
            licenses_certifications_ns.abort(500, str(e)) 