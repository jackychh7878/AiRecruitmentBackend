from database import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

class CandidateMasterProfile(db.Model):
    __tablename__ = 'candidate_master_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    chinese_name = db.Column(db.String(200))  # Nullable field for Chinese name
    location = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    personal_summary = db.Column(db.Text)
    availability_weeks = db.Column(db.Integer)
    preferred_work_types = db.Column(db.String(255))
    right_to_work = db.Column(db.Boolean, default=False)
    salary_expectation = db.Column(db.Numeric(12, 2))
    classification_of_interest = db.Column(db.String(255))
    sub_classification_of_interest = db.Column(db.String(1000))  # Increased size for comma-separated tags
    citizenship = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    remarks = db.Column(db.Text)
    ai_short_summary = db.Column(db.Text)
    embedding_vector = db.Column(Vector(1536))
    metadata_json = db.Column(JSONB)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    career_history = db.relationship('CandidateCareerHistory', backref='candidate', lazy=True, cascade='all, delete-orphan')
    skills = db.relationship('CandidateSkills', backref='candidate', lazy=True, cascade='all, delete-orphan')
    education = db.relationship('CandidateEducation', backref='candidate', lazy=True, cascade='all, delete-orphan')
    licenses_certifications = db.relationship('CandidateLicensesCertifications', backref='candidate', lazy=True, cascade='all, delete-orphan')
    languages = db.relationship('CandidateLanguages', backref='candidate', lazy=True, cascade='all, delete-orphan')
    resumes = db.relationship('CandidateResume', backref='candidate', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_relationships=False, include_embedding=False):
        data = {
            'id': self.id,
            'last_name': self.last_name,
            'first_name': self.first_name,
            'chinese_name': self.chinese_name,
            'location': self.location,
            'email': self.email,
            'phone_number': self.phone_number,
            'personal_summary': self.personal_summary,
            'availability_weeks': self.availability_weeks,
            'preferred_work_types': self.preferred_work_types,
            'right_to_work': self.right_to_work,
            'salary_expectation': float(self.salary_expectation) if self.salary_expectation else None,
            'classification_of_interest': self.classification_of_interest,
            'sub_classification_of_interest': self.sub_classification_of_interest,
            'citizenship': self.citizenship,
            'is_active': self.is_active,
            'remarks': self.remarks,
            'ai_short_summary': self.ai_short_summary,
            'metadata_json': self.metadata_json,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }
        
        # Only include embedding vector if specifically requested
        if include_embedding and self.embedding_vector is not None:
            try:
                # Convert numpy array or pgvector to Python list for JSON serialization
                if hasattr(self.embedding_vector, 'tolist'):
                    data['embedding_vector'] = self.embedding_vector.tolist()
                elif isinstance(self.embedding_vector, (list, tuple)):
                    data['embedding_vector'] = list(self.embedding_vector)
                else:
                    # Handle other potential vector types
                    data['embedding_vector'] = list(self.embedding_vector)
            except (AttributeError, TypeError):
                # If conversion fails, exclude embedding from response
                pass
        
        if include_relationships:
            data.update({
                'career_history': [ch.to_dict() for ch in self.career_history],
                'skills': [s.to_dict() for s in self.skills],
                'education': [e.to_dict() for e in self.education],
                'licenses_certifications': [lc.to_dict() for lc in self.licenses_certifications],
                'languages': [l.to_dict() for l in self.languages],
                'resumes': [r.to_dict() for r in self.resumes]
            })
        
        return data

class CandidateCareerHistory(db.Model):
    __tablename__ = 'candidate_career_history'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_master_profile.id'), nullable=False)
    job_title = db.Column(db.String(255), nullable=False)
    company_name = db.Column(db.String(255), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'job_title': self.job_title,
            'company_name': self.company_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'description': self.description,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }

class CandidateSkills(db.Model):
    __tablename__ = 'candidate_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_master_profile.id'), nullable=False)
    career_history_id = db.Column(db.Integer, db.ForeignKey('candidate_career_history.id'))
    skills = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'career_history_id': self.career_history_id,
            'skills': self.skills,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }

class CandidateEducation(db.Model):
    __tablename__ = 'candidate_education'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_master_profile.id'), nullable=False)
    school = db.Column(db.String(255), nullable=False)
    degree = db.Column(db.String(255))
    field_of_study = db.Column(db.String(255))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    grade = db.Column(db.String(50))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'school': self.school,
            'degree': self.degree,
            'field_of_study': self.field_of_study,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'grade': self.grade,
            'description': self.description,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }

class CandidateLicensesCertifications(db.Model):
    __tablename__ = 'candidate_licenses_certifications'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_master_profile.id'), nullable=False)
    license_certification_name = db.Column(db.String(255), nullable=False)
    issuing_organisation = db.Column(db.String(255))
    issue_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    is_no_expiry = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'license_certification_name': self.license_certification_name,
            'issuing_organisation': self.issuing_organisation,
            'issue_date': self.issue_date.isoformat() if self.issue_date else None,
            'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None,
            'is_no_expiry': self.is_no_expiry,
            'description': self.description,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }

class CandidateLanguages(db.Model):
    __tablename__ = 'candidate_languages'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_master_profile.id'), nullable=False)
    language = db.Column(db.String(100), nullable=False)
    proficiency_level = db.Column(db.String(50))
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'language': self.language,
            'proficiency_level': self.proficiency_level,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }

class CandidateResume(db.Model):
    __tablename__ = 'candidate_resume'
    
    id = db.Column(db.Integer, primary_key=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey('candidate_master_profile.id'), nullable=False)
    pdf_data = db.Column(db.LargeBinary, nullable=False)  # Store PDF as binary data
    file_name = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False)
    content_type = db.Column(db.String(100), default='application/pdf')
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_pdf_data=False):
        data = {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'content_type': self.content_type,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }
        
        # Only include PDF data if explicitly requested (for downloads)
        if include_pdf_data and self.pdf_data:
            import base64
            data['pdf_data_base64'] = base64.b64encode(self.pdf_data).decode('utf-8')
        
        return data

class AiRecruitmentComCode(db.Model):
    __tablename__ = 'ai_recruitment_com_code'
    
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    com_code = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('category', 'com_code', name='uq_category_com_code'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'category': self.category,
            'com_code': self.com_code,
            'description': self.description,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }

class AiPromptTemplate(db.Model):
    __tablename__ = 'ai_recruitment_prompt_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    template_content = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    version_number = db.Column(db.Integer, default=1, nullable=False)
    created_by = db.Column(db.String(100))
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'template_content': self.template_content,
            'is_active': self.is_active,
            'version_number': self.version_number,
            'created_by': self.created_by,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }
    
    @staticmethod
    def get_active_template():
        """Get the currently active prompt template"""
        return AiPromptTemplate.query.filter_by(is_active=True).first()
    
    def activate(self):
        """Activate this template and deactivate all others"""
        # Deactivate all other templates
        AiPromptTemplate.query.update({'is_active': False})
        # Activate this template
        self.is_active = True
        db.session.commit()
    
    @staticmethod
    def create_new_version(base_template_id=None):
        """Create a new version number based on existing templates"""
        if base_template_id:
            base_template = AiPromptTemplate.query.get(base_template_id)
            if base_template:
                return base_template.version_number + 1
        
        # Get the highest version number and add 1
        max_version = db.session.query(db.func.max(AiPromptTemplate.version_number)).scalar()
        return (max_version or 0) + 1

class BatchJobStatus(db.Model):
    __tablename__ = 'ai_recruitment_batch_job_status'
    
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    batch_number = db.Column(db.String(100), nullable=False, index=True)
    batch_upload_datetime = db.Column(db.String(50))  # ISO datetime string
    status = db.Column(db.String(20), nullable=False, default='queued', index=True)  # queued, processing, completed, failed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    total_files = db.Column(db.Integer, default=0, nullable=False)
    processed_files = db.Column(db.Integer, default=0, nullable=False)
    successful_profiles = db.Column(db.Integer, default=0, nullable=False)
    completed_profiles = db.Column(db.Integer, default=0, nullable=False)  # Complete with all mandatory fields
    incomplete_profiles = db.Column(db.Integer, default=0, nullable=False)  # Missing some mandatory fields but still created
    failed_files = db.Column(db.Integer, default=0, nullable=False)
    ai_summaries_generated = db.Column(db.Integer, default=0, nullable=False)  # Number of candidates with AI summaries
    ai_summaries_failed = db.Column(db.Integer, default=0, nullable=False)  # Number of candidates where AI processing failed
    classifications_generated = db.Column(db.Integer, default=0, nullable=False)  # Number of candidates with AI classifications
    classifications_failed = db.Column(db.Integer, default=0, nullable=False)  # Number of candidates where classification failed
    progress_percentage = db.Column(db.Float, default=0.0, nullable=False)
    processing_time_seconds = db.Column(db.Float, default=0.0, nullable=False)
    errors = db.Column(JSONB, default=list)  # List of error messages
    results = db.Column(JSONB, default=list)  # Detailed results for each file
    created_by = db.Column(db.String(100), default='user')
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to track failed files
    failed_files_details = db.relationship('BatchJobFailedFile', backref='batch_job', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self, include_details=True):
        """Convert job status to dictionary"""
        data = {
            'id': self.id,
            'job_id': self.job_id,
            'batch_number': self.batch_number,
            'batch_upload_datetime': self.batch_upload_datetime,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_profiles': self.successful_profiles,
            'completed_profiles': self.completed_profiles,
            'incomplete_profiles': self.incomplete_profiles,
            'failed_files': self.failed_files,
            'ai_summaries_generated': self.ai_summaries_generated,
            'ai_summaries_failed': self.ai_summaries_failed,
            'classifications_generated': self.classifications_generated,
            'classifications_failed': self.classifications_failed,
            'progress_percentage': self.progress_percentage,
            'processing_time_seconds': self.processing_time_seconds,
            'created_by': self.created_by,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }
        
        if include_details:
            data['errors'] = self.errors or []
            data['results'] = self.results or []
            # Include failed file details
            data['failed_files_details'] = [failed_file.to_dict() for failed_file in self.failed_files_details]
        
        return data
    
    @classmethod
    def create_new_job(cls, job_id: str, batch_number: str, total_files: int, created_by: str = 'user'):
        """Create a new batch job status record"""
        job = cls(
            job_id=job_id,
            batch_number=batch_number,
            batch_upload_datetime=datetime.utcnow().isoformat(),
            total_files=total_files,
            created_by=created_by,
            status='queued'
        )
        db.session.add(job)
        db.session.commit()
        return job
    
    def update_status(self, status: str, **kwargs):
        """Update job status and related fields"""
        self.status = status
        self.last_modified_date = datetime.utcnow()
        
        # Update timestamp fields based on status
        if status == 'processing' and not self.started_at:
            self.started_at = datetime.utcnow()
        elif status in ['completed', 'failed', 'cancelled'] and not self.completed_at:
            self.completed_at = datetime.utcnow()
        
        # Update other fields if provided
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        db.session.commit()
    
    def add_error(self, error_message: str):
        """Add an error message to the job"""
        if not self.errors:
            self.errors = []
        self.errors.append(error_message)
        self.last_modified_date = datetime.utcnow()
        db.session.commit()
    
    def add_result(self, result: dict):
        """Add a processing result to the job"""
        if not self.results:
            self.results = []
        self.results.append(result)
        self.last_modified_date = datetime.utcnow()
        db.session.commit()

class BatchJobFailedFile(db.Model):
    __tablename__ = 'ai_recruitment_batch_job_failed_files'
    
    id = db.Column(db.Integer, primary_key=True)
    batch_job_id = db.Column(db.Integer, db.ForeignKey('ai_recruitment_batch_job_status.id'), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.BigInteger)
    failure_reason = db.Column(db.Text, nullable=False)
    error_type = db.Column(db.String(50))  # parsing_error, validation_error, database_error, etc.
    failure_stage = db.Column(db.String(50))  # parsing, validation, creation, ai_processing, etc.
    parsing_method = db.Column(db.String(50))  # spacy, azure_di, langextract
    attempted_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'batch_job_id': self.batch_job_id,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'failure_reason': self.failure_reason,
            'error_type': self.error_type,
            'failure_stage': self.failure_stage,
            'parsing_method': self.parsing_method,
            'attempted_at': self.attempted_at.isoformat() if self.attempted_at else None,
            'created_date': self.created_date.isoformat() if self.created_date else None
        } 