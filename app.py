from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from sqlalchemy import text
import logging
from database import db

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL', 
    'postgresql://username:password@localhost:5432/ai_recruitment_db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy with app
db.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import all route modules
from routes.candidate_profile_routes import candidate_profile_bp
from routes.career_history_routes import career_history_bp
from routes.skills_routes import skills_bp
from routes.education_routes import education_bp
from routes.licenses_certifications_routes import licenses_certifications_bp
from routes.languages_routes import languages_bp
from routes.resume_routes import resume_bp
from routes.lookup_routes import lookup_bp

# Register blueprints
app.register_blueprint(candidate_profile_bp, url_prefix='/api/candidates')
app.register_blueprint(career_history_bp, url_prefix='/api/career-history')
app.register_blueprint(skills_bp, url_prefix='/api/skills')
app.register_blueprint(education_bp, url_prefix='/api/education')
app.register_blueprint(licenses_certifications_bp, url_prefix='/api/licenses-certifications')
app.register_blueprint(languages_bp, url_prefix='/api/languages')
app.register_blueprint(resume_bp, url_prefix='/api/resumes')
app.register_blueprint(lookup_bp, url_prefix='/api/lookups')

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        db.session.execute(text('SELECT 1'))
        return jsonify({
            'status': 'healthy',
            'message': 'AI Recruitment API is running',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'message': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

# Error handlers
@app.errorhandler(400)
def bad_request(error):
    return jsonify({'error': 'Bad request', 'message': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found', 'message': 'Resource not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return jsonify({'error': 'Internal server error', 'message': str(error)}), 500

# API documentation endpoint
@app.route('/api/docs', methods=['GET'])
def api_docs():
    """API documentation endpoint"""
    endpoints = {
        'candidates': {
            'GET /api/candidates': 'Get all candidates',
            'GET /api/candidates/{id}': 'Get candidate by ID',
            'POST /api/candidates': 'Create new candidate',
            'PUT /api/candidates/{id}': 'Update candidate',
            'DELETE /api/candidates/{id}': 'Delete candidate'
        },
        'career_history': {
            'GET /api/career-history': 'Get all career history records',
            'GET /api/career-history/{id}': 'Get career history by ID',
            'GET /api/career-history/candidate/{candidate_id}': 'Get career history for candidate',
            'POST /api/career-history': 'Create career history record',
            'PUT /api/career-history/{id}': 'Update career history record',
            'DELETE /api/career-history/{id}': 'Delete career history record'
        },
        'skills': {
            'GET /api/skills': 'Get all skills',
            'GET /api/skills/{id}': 'Get skill by ID',
            'GET /api/skills/candidate/{candidate_id}': 'Get skills for candidate',
            'POST /api/skills': 'Create skill record',
            'PUT /api/skills/{id}': 'Update skill record',
            'DELETE /api/skills/{id}': 'Delete skill record'
        },
        'education': {
            'GET /api/education': 'Get all education records',
            'GET /api/education/{id}': 'Get education by ID',
            'GET /api/education/candidate/{candidate_id}': 'Get education for candidate',
            'POST /api/education': 'Create education record',
            'PUT /api/education/{id}': 'Update education record',
            'DELETE /api/education/{id}': 'Delete education record'
        },
        'licenses_certifications': {
            'GET /api/licenses-certifications': 'Get all licenses/certifications',
            'GET /api/licenses-certifications/{id}': 'Get license/certification by ID',
            'GET /api/licenses-certifications/candidate/{candidate_id}': 'Get licenses/certifications for candidate',
            'POST /api/licenses-certifications': 'Create license/certification record',
            'PUT /api/licenses-certifications/{id}': 'Update license/certification record',
            'DELETE /api/licenses-certifications/{id}': 'Delete license/certification record'
        },
        'languages': {
            'GET /api/languages': 'Get all language records',
            'GET /api/languages/{id}': 'Get language by ID',
            'GET /api/languages/candidate/{candidate_id}': 'Get languages for candidate',
            'POST /api/languages': 'Create language record',
            'PUT /api/languages/{id}': 'Update language record',
            'DELETE /api/languages/{id}': 'Delete language record'
        },
        'resumes': {
            'GET /api/resumes': 'Get all resume records',
            'GET /api/resumes/{id}': 'Get resume by ID',
            'GET /api/resumes/candidate/{candidate_id}': 'Get resumes for candidate',
            'POST /api/resumes': 'Create resume record',
            'PUT /api/resumes/{id}': 'Update resume record',
            'DELETE /api/resumes/{id}': 'Delete resume record'
        },
        'lookups': {
            'GET /api/lookups': 'Get all lookup codes',
            'GET /api/lookups/{category}': 'Get lookup codes by category',
            'POST /api/lookups': 'Create lookup code',
            'PUT /api/lookups/{id}': 'Update lookup code',
            'DELETE /api/lookups/{id}': 'Delete lookup code'
        }
    }
    
    return jsonify({
        'message': 'AI Recruitment API Documentation',
        'version': '1.0.0',
        'endpoints': endpoints
    })

if __name__ == '__main__':
    app.run(debug=True, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)