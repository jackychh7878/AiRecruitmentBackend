from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector

class CandidateMasterProfile(db.Model):
    __tablename__ = 'candidate_master_profile'
    
    id = db.Column(db.Integer, primary_key=True)
    last_name = db.Column(db.String(100), nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255))
    email = db.Column(db.String(255), unique=True, nullable=False)
    phone_number = db.Column(db.String(20))
    personal_summary = db.Column(db.Text)
    availability_weeks = db.Column(db.Integer)
    preferred_work_types = db.Column(db.String(255))
    right_to_work = db.Column(db.Boolean, default=False)
    salary_expectation = db.Column(db.Numeric(12, 2))
    classification_of_interest = db.Column(db.String(255))
    sub_classification_of_interest = db.Column(db.String(255))
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
    
    def to_dict(self, include_relationships=False):
        data = {
            'id': self.id,
            'last_name': self.last_name,
            'first_name': self.first_name,
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
            'is_active': self.is_active,
            'remarks': self.remarks,
            'ai_short_summary': self.ai_short_summary,
            'metadata_json': self.metadata_json,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }
        
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
    azure_blob_url = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(255))
    file_size = db.Column(db.BigInteger)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_date = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'candidate_id': self.candidate_id,
            'azure_blob_url': self.azure_blob_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'upload_date': self.upload_date.isoformat() if self.upload_date else None,
            'is_active': self.is_active,
            'created_date': self.created_date.isoformat() if self.created_date else None,
            'last_modified_date': self.last_modified_date.isoformat() if self.last_modified_date else None
        }

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