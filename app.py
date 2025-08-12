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

# Initialize bulk AI regeneration service with app context
from services.bulk_ai_regeneration_service import bulk_ai_regeneration_service
with app.app_context():
    bulk_ai_regeneration_service.set_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment-based configuration
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
DEBUG_MODE = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

# Set Flask configuration based on environment
if FLASK_ENV == 'development':
    app.config['DEBUG'] = True
    app.config['TESTING'] = False
    logger.info("Running in DEVELOPMENT mode")
else:
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    logger.info("Running in PRODUCTION mode")

# Security configurations for production
if FLASK_ENV == 'production':
    app.config['PREFERRED_URL_SCHEME'] = 'https'
    # Disable detailed error messages in production
    app.config['PROPAGATE_EXCEPTIONS'] = False
    # Security headers
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    # Disable debug mode
    app.debug = False
    app.testing = False

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
    # Only run Flask development server in development mode
    if FLASK_ENV == 'development':
        logger.info("Starting Flask development server...")
        app.run(
            debug=DEBUG_MODE,
            use_debugger=DEBUG_MODE,
            use_reloader=DEBUG_MODE,
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', 5000))
        )
    else:
        logger.info("Production mode: Use Gunicorn or production WSGI server")
        logger.info("Run with: gunicorn -w 4 -b 0.0.0.0:5000 app:app")