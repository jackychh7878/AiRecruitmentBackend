from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_restx import Api
from datetime import datetime
import os
from sqlalchemy import text
import logging
from database import db
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize Swagger/OpenAPI documentation
api = Api(
    app,
    version='1.0.0',
    title='AI Recruitment API',
    description='A comprehensive API for managing recruitment candidates and their profiles',
    doc='/swagger/',  # Swagger UI will be available at /swagger/
    prefix='/api'
)

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

# Import all route namespaces
from routes.candidate_profile_routes import candidate_profile_ns
from routes.career_history_routes import career_history_ns
from routes.skills_routes import skills_ns
from routes.education_routes import education_ns
from routes.licenses_certifications_routes import licenses_certifications_ns
from routes.languages_routes import languages_ns
from routes.resume_routes import resume_ns
from routes.lookup_routes import lookup_ns

# Register namespaces
api.add_namespace(candidate_profile_ns, path='/candidates')
api.add_namespace(career_history_ns, path='/career-history')
api.add_namespace(skills_ns, path='/skills')
api.add_namespace(education_ns, path='/education')
api.add_namespace(licenses_certifications_ns, path='/licenses-certifications')
api.add_namespace(languages_ns, path='/languages')
api.add_namespace(resume_ns, path='/resumes')
api.add_namespace(lookup_ns, path='/lookups')

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

# API documentation is now available at /swagger/

if __name__ == '__main__':
    app.run(debug=True, use_debugger=False, use_reloader=False, host='0.0.0.0', port=5000)