from flask import request
from flask_restx import Namespace, Resource, fields
from database import db
from models import CandidateResume, CandidateMasterProfile
from datetime import datetime
from werkzeug.datastructures import FileStorage

resume_ns = Namespace('resumes', description='Resume operations')

# Define Swagger models
resume_model = resume_ns.model('Resume', {
    'id': fields.Integer(readonly=True, description='Resume ID'),
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'file_name': fields.String(required=True, description='Original file name'),
    'file_size': fields.Integer(required=True, description='File size in bytes'),
    'content_type': fields.String(description='MIME type of the file'),
    'upload_date': fields.DateTime(description='Upload date'),
    'is_active': fields.Boolean(description='Is active'),
    'created_date': fields.DateTime(readonly=True, description='Creation date'),
    'last_modified_date': fields.DateTime(readonly=True, description='Last modification date')
})

resume_input_model = resume_ns.model('ResumeInput', {
    'candidate_id': fields.Integer(required=True, description='Candidate ID'),
    'file_name': fields.String(required=True, description='Original file name'),
    'file_size': fields.Integer(required=True, description='File size in bytes'),
    'content_type': fields.String(description='MIME type of the file'),
    'pdf_data_base64': fields.String(required=True, description='Base64 encoded PDF data')
})

resume_list_model = resume_ns.model('ResumeList', {
    'resumes': fields.List(fields.Nested(resume_model)),
    'total': fields.Integer(description='Total number of resume records'),
    'pages': fields.Integer(description='Total number of pages'),
    'current_page': fields.Integer(description='Current page number'),
    'per_page': fields.Integer(description='Items per page')
})

@resume_ns.route('/')
class ResumeList(Resource):
    @resume_ns.doc('get_all_resumes')
    @resume_ns.param('page', 'Page number', type=int, default=1)
    @resume_ns.param('per_page', 'Items per page', type=int, default=10)
    @resume_ns.param('candidate_id', 'Filter by candidate ID', type=int)
    @resume_ns.param('file_name', 'Filter by file name')
    @resume_ns.param('is_active', 'Filter by active status', type=bool)
    @resume_ns.param('upload_date_from', 'Filter by upload date from (YYYY-MM-DD)')
    @resume_ns.param('upload_date_to', 'Filter by upload date to (YYYY-MM-DD)')
    def get(self):
        """Get all resume records with optional filtering"""
        try:
            # Query parameters
            page = request.args.get('page', 1, type=int)
            per_page = request.args.get('per_page', 10, type=int)
            candidate_id = request.args.get('candidate_id', type=int)
            file_name = request.args.get('file_name')
            is_active = request.args.get('is_active', type=bool)
            upload_date_from = request.args.get('upload_date_from')
            upload_date_to = request.args.get('upload_date_to')
            
            # Build query
            query = CandidateResume.query
            
            if candidate_id:
                query = query.filter(CandidateResume.candidate_id == candidate_id)
            if file_name:
                query = query.filter(CandidateResume.file_name.ilike(f'%{file_name}%'))
            if is_active is not None:
                query = query.filter(CandidateResume.is_active == is_active)
            
            # Date filtering
            if upload_date_from:
                try:
                    from_date = datetime.strptime(upload_date_from, '%Y-%m-%d').date()
                    query = query.filter(CandidateResume.upload_date >= from_date)
                except ValueError:
                    resume_ns.abort(400, 'upload_date_from must be in YYYY-MM-DD format')
            
            if upload_date_to:
                try:
                    to_date = datetime.strptime(upload_date_to, '%Y-%m-%d').date()
                    query = query.filter(CandidateResume.upload_date <= to_date)
                except ValueError:
                    resume_ns.abort(400, 'upload_date_to must be in YYYY-MM-DD format')
            
            # Pagination
            resume_records = query.paginate(
                page=page, per_page=per_page, error_out=False
            )
            
            return {
                'resumes': [resume.to_dict() for resume in resume_records.items],
                'total': resume_records.total,
                'pages': resume_records.pages,
                'current_page': page,
                'per_page': per_page
            }, 200
            
        except Exception as e:
            resume_ns.abort(500, str(e))

    @resume_ns.doc('create_resume')
    @resume_ns.expect(resume_input_model)
    def post(self):
        """Create a new resume record with PDF data"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('candidate_id'):
                resume_ns.abort(400, 'candidate_id is required')
            if not data.get('pdf_data_base64'):
                resume_ns.abort(400, 'pdf_data_base64 is required')
            if not data.get('file_name'):
                resume_ns.abort(400, 'file_name is required')
            if not data.get('file_size'):
                resume_ns.abort(400, 'file_size is required')
            
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get(data['candidate_id'])
            if not candidate:
                resume_ns.abort(404, 'Candidate not found')
            
            # Validate file size
            file_size = data.get('file_size')
            if file_size <= 0:
                resume_ns.abort(400, 'file_size must be a positive number')
            
            # Validate and decode PDF data
            try:
                import base64
                pdf_data = base64.b64decode(data['pdf_data_base64'])
                if len(pdf_data) == 0:
                    resume_ns.abort(400, 'PDF data is empty')
                
                # Verify file size matches actual data size
                if abs(len(pdf_data) - file_size) > 100:  # Allow small variance
                    resume_ns.abort(400, f'File size mismatch. Expected: {file_size}, Actual: {len(pdf_data)}')
                    
            except Exception as e:
                resume_ns.abort(400, f'Invalid base64 PDF data: {str(e)}')
            
            # Validate file name
            file_name = data['file_name'].strip()
            if not file_name.lower().endswith('.pdf'):
                resume_ns.abort(400, 'Only PDF files are supported')
            
            # Create new resume record
            resume_record = CandidateResume(
                candidate_id=data['candidate_id'],
                pdf_data=pdf_data,
                file_name=file_name,
                file_size=len(pdf_data),  # Use actual data size
                content_type=data.get('content_type', 'application/pdf')
            )
            
            db.session.add(resume_record)
            db.session.commit()
            
            return resume_record.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            resume_ns.abort(500, str(e))

# Add multipart parser for PDF upload
upload_parser = resume_ns.parser()
upload_parser.add_argument('pdf_file', 
                          location='files',
                          type=FileStorage,
                          required=True,
                          help='PDF resume file')
upload_parser.add_argument('candidate_id',
                          location='form',
                          type=int,
                          required=True,
                          help='Candidate ID')

@resume_ns.route('/upload')
class ResumeUpload(Resource):
    @resume_ns.doc('upload_resume_pdf')
    @resume_ns.expect(upload_parser)
    def post(self):
        """Upload a PDF resume file directly"""
        try:
            args = upload_parser.parse_args()
            pdf_file = args['pdf_file']
            candidate_id = args['candidate_id']
            
            # Validate PDF file
            if not pdf_file or pdf_file.filename == '':
                resume_ns.abort(400, 'No PDF file provided')
            
            if not pdf_file.filename.lower().endswith('.pdf'):
                resume_ns.abort(400, 'Only PDF files are allowed')
            
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get(candidate_id)
            if not candidate:
                resume_ns.abort(404, 'Candidate not found')
            
            # Read PDF file data
            pdf_data = pdf_file.read()
            if not pdf_data:
                resume_ns.abort(400, 'PDF file is empty')
            
            # Create new resume record
            resume_record = CandidateResume(
                candidate_id=candidate_id,
                pdf_data=pdf_data,
                file_name=pdf_file.filename,
                file_size=len(pdf_data),
                content_type=pdf_file.content_type or 'application/pdf'
            )
            
            db.session.add(resume_record)
            db.session.commit()
            
            return resume_record.to_dict(), 201
            
        except Exception as e:
            db.session.rollback()
            resume_ns.abort(500, str(e))

@resume_ns.route('/<int:resume_id>')
@resume_ns.param('resume_id', 'Resume ID')
class Resume(Resource):
    @resume_ns.doc('get_resume')
    def get(self, resume_id):
        """Get a specific resume record by ID"""
        try:
            resume_record = CandidateResume.query.get_or_404(resume_id)
            return resume_record.to_dict(), 200
            
        except Exception as e:
            resume_ns.abort(500, str(e))

    @resume_ns.doc('update_resume')
    @resume_ns.expect(resume_input_model)
    def put(self, resume_id):
        """Update an existing resume record"""
        try:
            resume_record = CandidateResume.query.get_or_404(resume_id)
            data = request.get_json()
            
            # Verify candidate exists if being changed
            if 'candidate_id' in data:
                candidate = CandidateMasterProfile.query.get(data['candidate_id'])
                if not candidate:
                    resume_ns.abort(404, 'Candidate not found')
            
            # Handle PDF data update if provided
            if 'pdf_data_base64' in data:
                try:
                    import base64
                    pdf_data = base64.b64decode(data['pdf_data_base64'])
                    if len(pdf_data) == 0:
                        resume_ns.abort(400, 'PDF data is empty')
                    
                    resume_record.pdf_data = pdf_data
                    resume_record.file_size = len(pdf_data)  # Update file size to match actual data
                    
                except Exception as e:
                    resume_ns.abort(400, f'Invalid base64 PDF data: {str(e)}')
            
            # Validate file size if provided separately
            if 'file_size' in data and 'pdf_data_base64' not in data:
                if data['file_size'] <= 0:
                    resume_ns.abort(400, 'file_size must be a positive number')
            
            # Validate file name if provided
            if 'file_name' in data:
                file_name = data['file_name'].strip()
                if not file_name.lower().endswith('.pdf'):
                    resume_ns.abort(400, 'Only PDF files are supported')
            
            # Update fields (excluding pdf_data_base64 as it's handled above)
            updatable_fields = [
                'candidate_id', 'file_name', 'content_type', 'is_active'
            ]
            
            # Only update file_size if PDF data wasn't provided (to avoid overriding calculated size)
            if 'pdf_data_base64' not in data and 'file_size' in data:
                updatable_fields.append('file_size')
            
            for field in updatable_fields:
                if field in data:
                    setattr(resume_record, field, data[field])
            
            resume_record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return resume_record.to_dict(), 200
            
        except Exception as e:
            db.session.rollback()
            resume_ns.abort(500, str(e))

    @resume_ns.doc('delete_resume')
    def delete(self, resume_id):
        """Delete a resume record (soft delete)"""
        try:
            resume_record = CandidateResume.query.get_or_404(resume_id)
            
            # Soft delete
            resume_record.is_active = False
            resume_record.last_modified_date = datetime.utcnow()
            db.session.commit()
            
            return {'message': 'Resume record deleted successfully'}, 200
            
        except Exception as e:
            db.session.rollback()
            resume_ns.abort(500, str(e))

@resume_ns.route('/<int:resume_id>/hard-delete')
@resume_ns.param('resume_id', 'Resume ID')
class ResumeHardDelete(Resource):
    @resume_ns.doc('hard_delete_resume')
    def delete(self, resume_id):
        """Permanently delete a resume record"""
        try:
            resume_record = CandidateResume.query.get_or_404(resume_id)
            
            db.session.delete(resume_record)
            db.session.commit()
            
            return {'message': 'Resume record permanently deleted'}, 200
            
        except Exception as e:
            db.session.rollback()
            resume_ns.abort(500, str(e))

@resume_ns.route('/candidate/<int:candidate_id>')
@resume_ns.param('candidate_id', 'Candidate ID')
class CandidateResumeList(Resource):
    @resume_ns.doc('get_candidate_resumes')
    @resume_ns.param('is_active', 'Filter by active status', type=bool)
    @resume_ns.param('latest_only', 'Return only the most recent resume', type=bool, default=False)
    def get(self, candidate_id):
        """Get all resume records for a specific candidate"""
        try:
            # Verify candidate exists
            candidate = CandidateMasterProfile.query.get_or_404(candidate_id)
            
            is_active = request.args.get('is_active', type=bool)
            latest_only = request.args.get('latest_only', 'false').lower() == 'true'
            
            query = CandidateResume.query.filter(CandidateResume.candidate_id == candidate_id)
            
            if is_active is not None:
                query = query.filter(CandidateResume.is_active == is_active)
            
            if latest_only:
                query = query.order_by(CandidateResume.upload_date.desc()).limit(1)
            else:
                query = query.order_by(CandidateResume.upload_date.desc())
            
            resume_records = query.all()
            
            return {
                'candidate_id': candidate_id,
                'resumes': [resume.to_dict() for resume in resume_records],
                'total': len(resume_records)
            }, 200
            
        except Exception as e:
            resume_ns.abort(500, str(e))

@resume_ns.route('/<int:resume_id>/download')
@resume_ns.param('resume_id', 'Resume ID')
class ResumeDownload(Resource):
    @resume_ns.doc('download_resume_pdf')
    def get(self, resume_id):
        """Download the PDF file for a specific resume"""
        try:
            from flask import Response
            
            resume_record = CandidateResume.query.get_or_404(resume_id)
            
            if not resume_record.is_active:
                resume_ns.abort(410, 'Resume is no longer active')
            
            if not resume_record.pdf_data:
                resume_ns.abort(404, 'PDF data not found')
            
            # Return PDF as binary response
            response = Response(
                resume_record.pdf_data,
                mimetype=resume_record.content_type or 'application/pdf',
                headers={
                    'Content-Disposition': f'attachment; filename="{resume_record.file_name}"',
                    'Content-Length': str(resume_record.file_size)
                }
            )
            
            return response
            
        except Exception as e:
            resume_ns.abort(500, f'Download failed: {str(e)}')

@resume_ns.route('/<int:resume_id>/info')
@resume_ns.param('resume_id', 'Resume ID')
class ResumeInfo(Resource):
    @resume_ns.doc('get_resume_info')
    def get(self, resume_id):
        """Get resume information without downloading the file"""
        try:
            resume_record = CandidateResume.query.get_or_404(resume_id)
            
            if not resume_record.is_active:
                resume_ns.abort(410, 'Resume is no longer active')
            
            return {
                'resume_id': resume_id,
                'file_name': resume_record.file_name,
                'file_size': resume_record.file_size,
                'content_type': resume_record.content_type,
                'upload_date': resume_record.upload_date.isoformat() if resume_record.upload_date else None,
                'download_url': f'/resumes/{resume_id}/download'
            }, 200
            
        except Exception as e:
            resume_ns.abort(500, str(e))

@resume_ns.route('/stats')
class ResumeStats(Resource):
    @resume_ns.doc('get_resume_stats')
    def get(self):
        """Get resume statistics"""
        try:
            total_resumes = CandidateResume.query.count()
            active_resumes = CandidateResume.query.filter_by(is_active=True).count()
            inactive_resumes = total_resumes - active_resumes
            
            # Get total file size
            total_size_result = db.session.query(
                db.func.sum(CandidateResume.file_size)
            ).filter(CandidateResume.is_active == True).first()
            total_file_size = total_size_result[0] if total_size_result[0] else 0
            
            # Get file count by extension
            file_extensions = db.session.query(
                db.func.substr(CandidateResume.file_name, 
                              db.func.position('.' in CandidateResume.file_name) + 1),
                db.func.count(CandidateResume.id)
            ).filter(
                CandidateResume.is_active == True,
                CandidateResume.file_name.contains('.')
            ).group_by(
                db.func.substr(CandidateResume.file_name, 
                              db.func.position('.' in CandidateResume.file_name) + 1)
            ).all()
            
            return {
                'total_resumes': total_resumes,
                'active_resumes': active_resumes,
                'inactive_resumes': inactive_resumes,
                'total_file_size_bytes': int(total_file_size),
                'total_file_size_mb': round(total_file_size / (1024 * 1024), 2) if total_file_size else 0,
                'file_extensions': [
                    {'extension': ext[0], 'count': ext[1]} 
                    for ext in file_extensions if ext[0]
                ]
            }, 200
            
        except Exception as e:
            resume_ns.abort(500, str(e)) 