-- Complete Database Initialization Script
-- AI Recruitment Backend Database Setup
-- Run this script to create the database, schema, and load sample data

-- Create database (run as superuser)
-- CREATE DATABASE ai_recruitment_db;
-- \c ai_recruitment_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;

-- Check if extensions are properly installed
SELECT 
    extname,
    extversion 
FROM pg_extension 
WHERE extname = 'vector';

\echo 'Creating database schema...'

-- Import the main schema
\i database_schema.sql

\echo 'Database schema created successfully!'

\echo 'Loading sample data...'

-- Import sample data
\i sample_data.sql

\echo 'Sample data loaded successfully!'

-- Verify the setup
\echo 'Verifying database setup...'

-- Check table creation
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check sample data
SELECT 
    'candidate_master_profile' as table_name,
    COUNT(*) as record_count
FROM candidate_master_profile
UNION ALL
SELECT 
    'candidate_career_history',
    COUNT(*)
FROM candidate_career_history
UNION ALL
SELECT 
    'candidate_skills',
    COUNT(*)
FROM candidate_skills
UNION ALL
SELECT 
    'candidate_education',
    COUNT(*)
FROM candidate_education
UNION ALL
SELECT 
    'candidate_languages',
    COUNT(*)
FROM candidate_languages
UNION ALL
SELECT 
    'candidate_licenses_certifications',
    COUNT(*)
FROM candidate_licenses_certifications
UNION ALL
SELECT 
    'ai_recruitment_com_code',
    COUNT(*)
FROM ai_recruitment_com_code;

\echo 'Database initialization completed successfully!'
\echo 'You can now start using the AI Recruitment Backend database.' 