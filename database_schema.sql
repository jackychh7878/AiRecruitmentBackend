-- PostgreSQL Schema for AI Recruitment Backend
-- Created for candidate profile management system

-- Enable vector extension for embedding storage (pgvector)
CREATE EXTENSION IF NOT EXISTS vector;

-- Create AI recruitment prompt templates table for managing different versions of AI prompts
CREATE TABLE ai_recruitment_prompt_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    template_content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT false,
    version_number INTEGER NOT NULL DEFAULT 1,
    created_by VARCHAR(100), -- User who created this template
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create unique partial index to ensure only one active template
CREATE UNIQUE INDEX idx_unique_active_template 
ON ai_recruitment_prompt_templates (is_active) 
WHERE is_active = true;

-- Create the main candidate master profile table
CREATE TABLE candidate_master_profile (
    id SERIAL PRIMARY KEY,
    last_name VARCHAR(100) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    chinese_name VARCHAR(200), -- Nullable field for Chinese name
    location VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    phone_number VARCHAR(20),
    personal_summary TEXT,
    availability_weeks INTEGER,
    preferred_work_types VARCHAR(255),
    right_to_work BOOLEAN DEFAULT false,
    salary_expectation DECIMAL(12,2),
    classification_of_interest VARCHAR(255),
    sub_classification_of_interest VARCHAR(1000), -- Increased size for comma-separated tags
    citizenship VARCHAR(255), -- Citizenship/visa status from predefined options
    is_active BOOLEAN DEFAULT true,
    remarks TEXT,
    ai_short_summary TEXT,
    embedding_vector vector(1536), -- Vector embedding for AI/ML purposes using pgvector
    metadata_json JSONB,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate career history table (one-to-many with candidate_master_profile)
CREATE TABLE candidate_career_history (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidate_master_profile(id) ON DELETE CASCADE,
    job_title VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE, -- NULL if still in current role
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate skills table (many-to-many relationship through career history)
CREATE TABLE candidate_skills (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidate_master_profile(id) ON DELETE CASCADE,
    career_history_id INTEGER REFERENCES candidate_career_history(id) ON DELETE SET NULL,
    skills VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate education table (one-to-many with candidate_master_profile)
CREATE TABLE candidate_education (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidate_master_profile(id) ON DELETE CASCADE,
    school VARCHAR(255) NOT NULL,
    degree VARCHAR(255),
    field_of_study VARCHAR(255),
    start_date DATE,
    end_date DATE, -- Or expected graduation date
    grade VARCHAR(50),
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate licenses & certifications table
CREATE TABLE candidate_licenses_certifications (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidate_master_profile(id) ON DELETE CASCADE,
    license_certification_name VARCHAR(255) NOT NULL,
    issuing_organisation VARCHAR(255),
    issue_date DATE,
    expiry_date DATE,
    is_no_expiry BOOLEAN DEFAULT false,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate languages table (one-to-many with candidate_master_profile)
CREATE TABLE candidate_languages (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidate_master_profile(id) ON DELETE CASCADE,
    language VARCHAR(100) NOT NULL,
    proficiency_level VARCHAR(50), -- Added proficiency level for better language tracking
    is_active BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create candidate resume table (one-to-many with candidate_master_profile)
CREATE TABLE candidate_resume (
    id SERIAL PRIMARY KEY,
    candidate_id INTEGER NOT NULL REFERENCES candidate_master_profile(id) ON DELETE CASCADE,
    pdf_data BYTEA NOT NULL, -- PDF file stored as binary data
    file_name VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    content_type VARCHAR(100) DEFAULT 'application/pdf',
    upload_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create AI recruitment communication codes lookup table
CREATE TABLE ai_recruitment_com_code (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100) NOT NULL,
    com_code VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(category, com_code)
);

-- Create indexes for better performance
CREATE INDEX idx_candidate_master_profile_email ON candidate_master_profile(email);
CREATE INDEX idx_candidate_master_profile_is_active ON candidate_master_profile(is_active);
CREATE INDEX idx_candidate_master_profile_created_date ON candidate_master_profile(created_date);
CREATE INDEX idx_candidate_master_profile_embedding ON candidate_master_profile USING ivfflat (embedding_vector vector_cosine_ops);

CREATE INDEX idx_candidate_career_history_candidate_id ON candidate_career_history(candidate_id);
CREATE INDEX idx_candidate_career_history_is_active ON candidate_career_history(is_active);

CREATE INDEX idx_candidate_skills_candidate_id ON candidate_skills(candidate_id);
CREATE INDEX idx_candidate_skills_career_history_id ON candidate_skills(career_history_id);
CREATE INDEX idx_candidate_skills_skills ON candidate_skills(skills);

CREATE INDEX idx_candidate_education_candidate_id ON candidate_education(candidate_id);
CREATE INDEX idx_candidate_education_is_active ON candidate_education(is_active);

CREATE INDEX idx_candidate_licenses_certifications_candidate_id ON candidate_licenses_certifications(candidate_id);
CREATE INDEX idx_candidate_licenses_certifications_is_active ON candidate_licenses_certifications(is_active);

CREATE INDEX idx_candidate_languages_candidate_id ON candidate_languages(candidate_id);
CREATE INDEX idx_candidate_languages_is_active ON candidate_languages(is_active);

CREATE INDEX idx_candidate_resume_candidate_id ON candidate_resume(candidate_id);
CREATE INDEX idx_candidate_resume_is_active ON candidate_resume(is_active);

CREATE INDEX idx_ai_recruitment_com_code_category ON ai_recruitment_com_code(category);
CREATE INDEX idx_ai_recruitment_com_code_is_active ON ai_recruitment_com_code(is_active);

-- Create triggers to automatically update last_modified_date
CREATE OR REPLACE FUNCTION update_last_modified_date()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_modified_date = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply the trigger to all tables
CREATE TRIGGER update_candidate_master_profile_last_modified_date
    BEFORE UPDATE ON candidate_master_profile
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_candidate_career_history_last_modified_date
    BEFORE UPDATE ON candidate_career_history
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_candidate_skills_last_modified_date
    BEFORE UPDATE ON candidate_skills
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_candidate_education_last_modified_date
    BEFORE UPDATE ON candidate_education
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_candidate_licenses_certifications_last_modified_date
    BEFORE UPDATE ON candidate_licenses_certifications
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_candidate_languages_last_modified_date
    BEFORE UPDATE ON candidate_languages
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_candidate_resume_last_modified_date
    BEFORE UPDATE ON candidate_resume
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_ai_recruitment_com_code_last_modified_date
    BEFORE UPDATE ON ai_recruitment_com_code
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

CREATE TRIGGER update_ai_recruitment_prompt_templates_last_modified_date
    BEFORE UPDATE ON ai_recruitment_prompt_templates
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

-- Create batch job status table for tracking batch resume parsing jobs
CREATE TABLE ai_recruitment_batch_job_status (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(100) UNIQUE NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    batch_upload_datetime VARCHAR(50), -- ISO datetime string
    status VARCHAR(20) NOT NULL DEFAULT 'queued', -- queued, processing, completed, failed, cancelled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    total_files INTEGER DEFAULT 0 NOT NULL,
    processed_files INTEGER DEFAULT 0 NOT NULL,
    successful_profiles INTEGER DEFAULT 0 NOT NULL,
    completed_profiles INTEGER DEFAULT 0 NOT NULL, -- Complete with all mandatory fields
    incomplete_profiles INTEGER DEFAULT 0 NOT NULL, -- Missing some mandatory fields but still created
    failed_files INTEGER DEFAULT 0 NOT NULL,
    ai_summaries_generated INTEGER DEFAULT 0 NOT NULL, -- Number of candidates with AI summaries
    ai_summaries_failed INTEGER DEFAULT 0 NOT NULL, -- Number of candidates where AI processing failed
    classifications_generated INTEGER DEFAULT 0 NOT NULL, -- Number of candidates with AI classifications
    classifications_failed INTEGER DEFAULT 0 NOT NULL, -- Number of candidates where classification failed
    progress_percentage REAL DEFAULT 0.0 NOT NULL,
    processing_time_seconds REAL DEFAULT 0.0 NOT NULL,
    errors JSONB DEFAULT '[]'::JSONB, -- List of error messages
    results JSONB DEFAULT '[]'::JSONB, -- Detailed results for each file
    created_by VARCHAR(100) DEFAULT 'user',
    last_modified_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create batch job failed files table for detailed failure tracking
CREATE TABLE ai_recruitment_batch_job_failed_files (
    id SERIAL PRIMARY KEY,
    batch_job_id INTEGER NOT NULL REFERENCES ai_recruitment_batch_job_status(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT,
    failure_reason TEXT NOT NULL,
    error_type VARCHAR(50), -- parsing_error, validation_error, database_error, etc.
    failure_stage VARCHAR(50), -- parsing, validation, creation, ai_processing, etc.
    parsing_method VARCHAR(50), -- spacy, azure_di, langextract
    attempted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Batch job status indexes for better query performance
CREATE INDEX idx_ai_recruitment_batch_job_status_job_id ON ai_recruitment_batch_job_status(job_id);
CREATE INDEX idx_ai_recruitment_batch_job_status_batch_number ON ai_recruitment_batch_job_status(batch_number);
CREATE INDEX idx_ai_recruitment_batch_job_status_status ON ai_recruitment_batch_job_status(status);
CREATE INDEX idx_ai_recruitment_batch_job_status_created_at ON ai_recruitment_batch_job_status(created_at);
CREATE INDEX idx_ai_recruitment_batch_job_failed_files_batch_job_id ON ai_recruitment_batch_job_failed_files(batch_job_id);
CREATE INDEX idx_ai_recruitment_batch_job_failed_files_filename ON ai_recruitment_batch_job_failed_files(original_filename);

-- Add trigger for batch job status table
CREATE TRIGGER update_ai_recruitment_batch_job_status_last_modified_date
    BEFORE UPDATE ON ai_recruitment_batch_job_status
    FOR EACH ROW EXECUTE FUNCTION update_last_modified_date();

-- Insert default AI recruitment prompt template
INSERT INTO ai_recruitment_prompt_templates (name, description, template_content, is_active, version_number, created_by) 
VALUES (
    'Default AI Summary Template',
    'Default template for generating candidate AI summaries',
    'Please analyze the following candidate profile data and create a professional summary within 200 words. Follow this format:

"{years_of_experience} years of experience in {primary_position} in {domain_field}. Graduated from {university_name}. 

Key Strengths: {key_skills_and_strengths}

Looking for: {career_objectives_and_interests}

Salary Expectation: {salary_range_if_available}

Work Status: {availability_and_work_preferences}

Notice Period: {availability_weeks_if_provided}

Additional Notes: {any_other_relevant_information}"

Candidate Data:
{candidate_profile_data}

Please provide a concise, professional summary that highlights the candidate''s key qualifications, experience, and career objectives.',
    true,
    1,
    'system'
); 