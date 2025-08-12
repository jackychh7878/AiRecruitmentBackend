-- Sample data for AI Recruitment Backend
-- Run this after creating the main schema

-- Insert default AI recruitment prompt template
INSERT INTO ai_recruitment_prompt_templates (name, description, template_content, is_active, version_number, created_by) 
VALUES (
    'Default AI Summary Template',
    'Default template for generating candidate AI summaries',
    'You are an AI assistant specializing in creating professional candidate profile summaries for recruitment purposes.

Given the candidate profile data below, create a concise professional summary in exactly 200 words or less following this format:

"[X] years of experience in [position] in [domain field].
Graduated from [university/education].
Strengths: [key skills and strengths]
Looking for: [salary expectation and work preferences]
Open to work status: [availability and notice period]
Other remarks: [additional relevant information]"

Candidate Profile Data:
{candidate_profile_data}

Please ensure the summary is:
- Professional and concise
- Highlights key qualifications and experience
- Includes relevant education background
- Mentions salary expectations if available
- Notes work availability and preferences
- Under 200 words total

Summary:',
    true,
    1,
    'system'
);

-- Insert comprehensive communication codes for AI Recruitment system

-- Language categories
INSERT INTO ai_recruitment_com_code (category, com_code, description) VALUES
('Language', 'Chinese - Cantonese', 'Cantonese Chinese language'),
('Language', 'Chinese - Mandarin', 'Mandarin Chinese language'),
('Language', 'English', 'English language'),
('Language', 'Japanese', 'Japanese language'),
('Language', 'Korean', 'Korean language'),
('Language', 'French', 'French language'),
('Language', 'German', 'German language'),
('Language', 'Spanish', 'Spanish language'),
('Language', 'Portuguese', 'Portuguese language'),
('Language', 'Italian', 'Italian language'),
('Language', 'Russian', 'Russian language'),
('Language', 'Arabic', 'Arabic language'),
('Language', 'Hindi', 'Hindi language'),
('Language', 'Thai', 'Thai language'),
('Language', 'Vietnamese', 'Vietnamese language'),
('Language', 'Indonesian', 'Indonesian language'),
('Language', 'Malay', 'Malay language'),
('Language', 'Tagalog', 'Tagalog language'),
('Language', 'Other', 'Other languages not listed'),

-- Preferred work types
('Preferred work types', 'Full time', 'Full-time employment'),
('Preferred work types', 'Part time', 'Part-time employment'),
('Preferred work types', 'Contract', 'Contract work'),
('Preferred work types', 'Casual', 'Casual employment'),
('Preferred work types', 'Remote', 'Remote work arrangement'),

-- Hong Kong citizenship and visa status
('Your citizenship and visas', 'Hong Kong SARS Permanent Resident', 'Hong Kong Special Administrative Region Permanent Resident'),
('Your citizenship and visas', 'Hong Kong SARS Citizen', 'Hong Kong Special Administrative Region Citizen'),
('Your citizenship and visas', 'Hong Kong SARS temporary visa with restrictions on industry (e.g. TeachTAS)', 'Hong Kong SARS temporary visa with industry restrictions'),
('Your citizenship and visas', 'Hong Kong SARS temporary visa (e.g. QMAS, TTPS, IANG)', 'Hong Kong SARS temporary visa without restrictions'),
('Your citizenship and visas', 'Require sponsorship to work for a new employer in Hong Kong SARS', 'Requires employment sponsorship in Hong Kong SARS'),

-- Classification of interest (Industry categories)
('Classification of interest', 'Accounting', 'Accounting and finance roles'),
('Classification of interest', 'Administration & Office Support', 'Administrative and office support positions'),
('Classification of interest', 'Advertising, Arts & Media', 'Advertising, arts and media industry'),
('Classification of interest', 'Banking & Financial Services', 'Banking and financial services sector'),
('Classification of interest', 'Call Centre & Customer Service', 'Call centre and customer service roles'),
('Classification of interest', 'CEO & General Management', 'Executive and general management positions'),
('Classification of interest', 'Community Services & Development', 'Community services and development sector'),
('Classification of interest', 'Construction', 'Construction industry'),
('Classification of interest', 'Consulting & Strategy', 'Consulting and strategy roles'),
('Classification of interest', 'Design & Architecture', 'Design and architecture professions'),
('Classification of interest', 'Education & Training', 'Education and training sector'),
('Classification of interest', 'Engineering', 'Engineering professions'),
('Classification of interest', 'Farming, Animals & Conservation', 'Agriculture, animals and conservation'),
('Classification of interest', 'Government & Defence', 'Government and defence sector'),
('Classification of interest', 'Healthcare & Medical', 'Healthcare and medical professions'),
('Classification of interest', 'Hospitality & Tourism', 'Hospitality and tourism industry'),
('Classification of interest', 'Human Resources & Recruitment', 'Human resources and recruitment'),
('Classification of interest', 'Information & Communication Technology', 'Information and communication technology'),
('Classification of interest', 'Insurance & Superannuation', 'Insurance and superannuation sector'),
('Classification of interest', 'Legal', 'Legal professions'),
('Classification of interest', 'Manufacturing, Transport & Logistics', 'Manufacturing, transport and logistics'),
('Classification of interest', 'Marketing & Communications', 'Marketing and communications'),
('Classification of interest', 'Mining, Resources & Energy', 'Mining, resources and energy sector'),
('Classification of interest', 'Real Estate & Property', 'Real estate and property'),
('Classification of interest', 'Retail & Consumer Products', 'Retail and consumer products'),
('Classification of interest', 'Sales', 'Sales positions'),
('Classification of interest', 'Science & Technology', 'Science and technology'),
('Classification of interest', 'Self Employment', 'Self-employment and entrepreneurship'),
('Classification of interest', 'Sport & Recreation', 'Sport and recreation industry'),
('Classification of interest', 'Trades & Services', 'Trades and services'),

-- Sub-classification of interest (ICT specific roles)
('Sub classification of interest', 'Architects', 'IT/System architects'),
('Sub classification of interest', 'Business/Systems Analysts', 'Business and systems analysts'),
('Sub classification of interest', 'Computer Operators', 'Computer operators'),
('Sub classification of interest', 'Consultants', 'IT consultants'),
('Sub classification of interest', 'Database Development & Administration', 'Database development and administration'),
('Sub classification of interest', 'Developers/Programmers', 'Software developers and programmers'),
('Sub classification of interest', 'Engineering - Hardware', 'Hardware engineering'),
('Sub classification of interest', 'Engineering - Network', 'Network engineering'),
('Sub classification of interest', 'Engineering Software', 'Software engineering'),
('Sub classification of interest', 'Help Desk & IT Support', 'Help desk and IT support'),
('Sub classification of interest', 'Management', 'IT management roles'),
('Sub classification of interest', 'Networks & Systems Administration', 'Networks and systems administration'),
('Sub classification of interest', 'Product Management & Development', 'Product management and development'),
('Sub classification of interest', 'Programme & Project Management', 'Programme and project management'),
('Sub classification of interest', 'Sales - Pre & Post', 'Pre-sales and post-sales'),
('Sub classification of interest', 'Security', 'IT security and cybersecurity'),
('Sub classification of interest', 'Team Leaders', 'Technical team leaders'),
('Sub classification of interest', 'Technical Writing', 'Technical writing and documentation'),
('Sub classification of interest', 'Telecommunications', 'Telecommunications'),
('Sub classification of interest', 'Testing & Quality Assurance', 'Testing and quality assurance'),
('Sub classification of interest', 'Web Development & Production', 'Web development and production'),
('Sub classification of interest', 'Other', 'Other ICT roles not specified'),

-- Language proficiency levels (keeping for reference)
('LANGUAGE_PROFICIENCY', 'NATIVE', 'Native speaker'),
('LANGUAGE_PROFICIENCY', 'FLUENT', 'Fluent'),
('LANGUAGE_PROFICIENCY', 'ADVANCED', 'Advanced'),
('LANGUAGE_PROFICIENCY', 'INTERMEDIATE', 'Intermediate'),
('LANGUAGE_PROFICIENCY', 'BASIC', 'Basic');

-- Insert sample candidate profiles
INSERT INTO candidate_master_profile (
    last_name, first_name, location, email, phone_number, personal_summary,
    availability_weeks, preferred_work_types, right_to_work, salary_expectation,
    classification_of_interest, sub_classification_of_interest, remarks, ai_short_summary
) VALUES
(
    'Smith', 'John', 'Central, Hong Kong', 'john.smith@email.com', '+852 9123 4567',
    'Experienced software engineer with 5+ years in full-stack development. Passionate about building scalable web applications and working with modern technologies.',
    2, 'Full time,Remote', true, 480000.00,
    'Information & Communication Technology', 'Developers/Programmers',
    'Open to relocation for the right opportunity',
    'Senior software engineer with strong full-stack experience, looking for challenging role in tech company'
),
(
    'Johnson', 'Sarah', 'Tsim Sha Tsui, Hong Kong', 'sarah.johnson@email.com', '+852 9789 0123',
    'Data scientist with expertise in machine learning and statistical analysis. Strong background in Python, R, and SQL.',
    4, 'Full time,Part time', true, 420000.00,
    'Information & Communication Technology', 'Business/Systems Analysts',
    'Interested in AI/ML positions in healthcare or finance',
    'Experienced data scientist specializing in ML and statistical analysis, seeking healthcare or finance opportunities'
),
(
    'Brown', 'Michael', 'Causeway Bay, Hong Kong', 'michael.brown@email.com', '+852 9345 6789',
    'Frontend developer specializing in React and modern JavaScript frameworks. UI/UX enthusiast with eye for design.',
    1, 'Contract,Casual', true, 360000.00,
    'Information & Communication Technology', 'Web Development & Production',
    'Available for short-term contracts',
    'Frontend React developer with strong UI/UX skills, available for contract work'
),
(
    'Wong', 'Alice', 'Admiralty, Hong Kong', 'alice.wong@email.com', '+852 9567 8901',
    'Banking professional with 8+ years experience in investment banking and financial analysis. CFA charterholder with strong analytical skills.',
    3, 'Full time', true, 720000.00,
    'Banking & Financial Services', 'Other',
    'Looking for senior roles in investment banking',
    'Senior banking professional with CFA certification, seeking investment banking opportunities'
),
(
    'Lee', 'David', 'Wan Chai, Hong Kong', 'david.lee@email.com', '+852 9234 5678',
    'Marketing manager with expertise in digital marketing and brand management. Led successful campaigns for major retail brands.',
    2, 'Full time,Remote', true, 540000.00,
    'Marketing & Communications', 'Other',
    'Experienced in both B2B and B2C marketing',
    'Marketing manager with digital expertise and brand management experience'
);

-- Get the candidate IDs for relationships
DO $$
DECLARE
    john_id INTEGER;
    sarah_id INTEGER;
    michael_id INTEGER;
    alice_id INTEGER;
    david_id INTEGER;
BEGIN
    SELECT id INTO john_id FROM candidate_master_profile WHERE email = 'john.smith@email.com';
    SELECT id INTO sarah_id FROM candidate_master_profile WHERE email = 'sarah.johnson@email.com';
    SELECT id INTO michael_id FROM candidate_master_profile WHERE email = 'michael.brown@email.com';

    -- Insert career history for John Smith
    INSERT INTO candidate_career_history (candidate_id, job_title, company_name, start_date, end_date, description) VALUES
    (john_id, 'Senior Software Engineer', 'TechCorp Australia', '2021-03-01', NULL, 'Lead development of microservices architecture using Node.js and React. Mentored junior developers and implemented CI/CD pipelines.'),
    (john_id, 'Software Engineer', 'StartupXYZ', '2019-06-01', '2021-02-28', 'Full-stack development using MEAN stack. Built customer-facing web applications and REST APIs.');

    -- Insert career history for Sarah Johnson
    INSERT INTO candidate_career_history (candidate_id, job_title, company_name, start_date, end_date, description) VALUES
    (sarah_id, 'Data Scientist', 'Analytics Plus', '2020-08-01', NULL, 'Developed machine learning models for customer segmentation and churn prediction. Worked with large datasets and cloud platforms.'),
    (sarah_id, 'Junior Data Analyst', 'Data Insights Co.', '2018-09-01', '2020-07-31', 'Performed statistical analysis and created data visualizations. Worked with SQL, Python, and Tableau.');

    -- Insert career history for Michael Brown
    INSERT INTO candidate_career_history (candidate_id, job_title, company_name, start_date, end_date, description) VALUES
    (michael_id, 'Frontend Developer', 'Creative Digital', '2020-01-01', NULL, 'Developed responsive web applications using React and Vue.js. Collaborated with design team to implement modern UI/UX.'),
    (michael_id, 'Junior Web Developer', 'Web Solutions Ltd', '2018-03-01', '2019-12-31', 'Built websites using HTML, CSS, JavaScript, and jQuery. Gained experience in responsive design and cross-browser compatibility.');

    -- Insert education records
    INSERT INTO candidate_education (candidate_id, school, degree, field_of_study, start_date, end_date, grade) VALUES
    (john_id, 'University of Sydney', 'Bachelor of Engineering', 'Software Engineering', '2014-02-01', '2017-11-30', 'Distinction'),
    (sarah_id, 'University of Melbourne', 'Master of Data Science', 'Data Science', '2017-02-01', '2018-12-15', 'High Distinction'),
    (sarah_id, 'University of Melbourne', 'Bachelor of Science', 'Mathematics and Statistics', '2013-02-01', '2016-11-30', 'Distinction'),
    (michael_id, 'Queensland University of Technology', 'Bachelor of Information Technology', 'Web Development', '2015-02-01', '2017-11-30', 'Credit');

    -- Insert skills
    INSERT INTO candidate_skills (candidate_id, skills) VALUES
    (john_id, 'JavaScript'), (john_id, 'Node.js'), (john_id, 'React'), (john_id, 'PostgreSQL'), (john_id, 'Docker'), (john_id, 'AWS'),
    (sarah_id, 'Python'), (sarah_id, 'R'), (sarah_id, 'SQL'), (sarah_id, 'Machine Learning'), (sarah_id, 'Pandas'), (sarah_id, 'Scikit-learn'),
    (michael_id, 'JavaScript'), (michael_id, 'React'), (michael_id, 'Vue.js'), (michael_id, 'CSS'), (michael_id, 'HTML'), (michael_id, 'TypeScript');

    -- Get additional candidate IDs
    SELECT id INTO alice_id FROM candidate_master_profile WHERE email = 'alice.wong@email.com';
    SELECT id INTO david_id FROM candidate_master_profile WHERE email = 'david.lee@email.com';

    -- Insert more career history for new candidates
    INSERT INTO candidate_career_history (candidate_id, job_title, company_name, start_date, end_date, description) VALUES
    (alice_id, 'Senior Investment Analyst', 'Goldman Sachs Asia', '2019-08-01', NULL, 'Lead financial modeling and analysis for IPOs and M&A transactions. Managed portfolio of high-net-worth clients.'),
    (alice_id, 'Investment Analyst', 'HSBC Investment Banking', '2016-06-01', '2019-07-31', 'Conducted equity research and financial analysis. Prepared investment reports and presentations for clients.'),
    (david_id, 'Marketing Manager', 'Cathay Pacific Airways', '2021-01-01', NULL, 'Led digital marketing campaigns and brand management initiatives. Managed team of 6 marketing professionals.'),
    (david_id, 'Senior Marketing Executive', 'HKT Limited', '2018-03-01', '2020-12-31', 'Developed and executed marketing strategies for telecommunications services. Managed B2B and B2C campaigns.');

    -- Insert more education records
    INSERT INTO candidate_education (candidate_id, school, degree, field_of_study, start_date, end_date, grade) VALUES
    (alice_id, 'Hong Kong University of Science and Technology', 'Master of Business Administration', 'Finance', '2014-09-01', '2016-06-15', 'Distinction'),
    (alice_id, 'University of Hong Kong', 'Bachelor of Business Administration', 'Finance and Banking', '2010-09-01', '2014-06-30', 'First Class Honours'),
    (david_id, 'Chinese University of Hong Kong', 'Master of Science', 'Marketing', '2016-09-01', '2017-12-15', 'Distinction'),
    (david_id, 'City University of Hong Kong', 'Bachelor of Business', 'Marketing and Communications', '2012-09-01', '2016-06-30', 'Second Class Honours');

    -- Insert more skills
    INSERT INTO candidate_skills (candidate_id, skills) VALUES
    (alice_id, 'Financial Modeling'), (alice_id, 'Equity Research'), (alice_id, 'Risk Management'), (alice_id, 'Bloomberg Terminal'), (alice_id, 'Excel VBA'), (alice_id, 'PowerBI'),
    (david_id, 'Digital Marketing'), (david_id, 'Google Analytics'), (david_id, 'Social Media Marketing'), (david_id, 'Brand Management'), (david_id, 'Adobe Creative Suite'), (david_id, 'Project Management');

    -- Insert languages with updated language codes
    INSERT INTO candidate_languages (candidate_id, language, proficiency_level) VALUES
    (john_id, 'English', 'NATIVE'),
    (john_id, 'Chinese - Mandarin', 'INTERMEDIATE'),
    (sarah_id, 'English', 'NATIVE'),
    (sarah_id, 'Chinese - Mandarin', 'FLUENT'),
    (sarah_id, 'Chinese - Cantonese', 'BASIC'),
    (michael_id, 'English', 'NATIVE'),
    (michael_id, 'French', 'BASIC'),
    (alice_id, 'English', 'NATIVE'),
    (alice_id, 'Chinese - Cantonese', 'NATIVE'),
    (alice_id, 'Chinese - Mandarin', 'FLUENT'),
    (alice_id, 'Japanese', 'INTERMEDIATE'),
    (david_id, 'English', 'NATIVE'),
    (david_id, 'Chinese - Cantonese', 'NATIVE'),
    (david_id, 'Chinese - Mandarin', 'ADVANCED'),
    (david_id, 'Korean', 'BASIC');

    -- Insert licenses and certifications
    INSERT INTO candidate_licenses_certifications (candidate_id, license_certification_name, issuing_organisation, issue_date, expiry_date, is_no_expiry) VALUES
    (john_id, 'AWS Certified Solutions Architect', 'Amazon Web Services', '2022-06-15', '2025-06-15', false),
    (sarah_id, 'Certified Analytics Professional', 'INFORMS', '2021-09-01', NULL, true),
    (michael_id, 'Google UX Design Certificate', 'Google', '2021-03-20', NULL, true),
    (alice_id, 'Chartered Financial Analyst (CFA)', 'CFA Institute', '2018-09-15', NULL, true),
    (alice_id, 'Financial Risk Manager (FRM)', 'Global Association of Risk Professionals', '2019-11-20', '2024-11-20', false),
    (david_id, 'Google Analytics Certified', 'Google', '2020-05-10', '2024-05-10', false),
    (david_id, 'Digital Marketing Professional Certificate', 'Hong Kong Management Association', '2021-08-25', NULL, true);

END $$; 