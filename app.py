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

# Configure Flask to handle trailing slashes consistently
app.url_map.strict_slashes = False  # Allow both /api/candidates and /api/candidates/

# Configure CORS properly to handle preflight requests
# Allow multiple origins for development and production
allowed_origins = [
    "http://localhost:3000",  # React development server
    "http://127.0.0.1:3000",  # Alternative localhost
    "http://localhost:3001",  # Alternative React port
]

# Add production origins from environment if set
if os.getenv('FRONTEND_URL'):
    allowed_origins.append(os.getenv('FRONTEND_URL'))

# Comprehensive header list to handle all frontend requests
cors_headers = [
    "Accept",
    "Accept-Encoding", 
    "Accept-Language", 
    "Cache-Control",
    "Connection",
    "Content-Language",
    "Content-Type",
    "Authorization",
    "Origin",
    "Pragma",
    "Referer",
    "User-Agent",
    "X-Requested-With",
    "X-CSRFToken",
    "DNT",
    "Keep-Alive",
    "X-CustomHeader"
]

# Add Chrome security headers
chrome_headers = [
    "Sec-CH-UA", "Sec-CH-UA-Mobile", "Sec-CH-UA-Platform",
    "Sec-Fetch-Site", "Sec-Fetch-Mode", "Sec-Fetch-Dest"
]
cors_headers.extend(chrome_headers)

CORS(app, 
     origins=allowed_origins,
     methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
     allow_headers=cors_headers,
     supports_credentials=True,
     expose_headers=["Content-Range", "X-Total-Count"]
)

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
api.add_namespace(licenses_certifications_ns, path='/licenses_certifications')
api.add_namespace(languages_ns, path='/languages')
api.add_namespace(resume_ns, path='/resumes')
api.add_namespace(lookup_ns, path='/lookups')

# Ensure all responses have proper CORS headers
@app.after_request
def after_request(response):
    # Additional CORS headers for better compatibility
    origin = request.headers.get('Origin')
    if origin in allowed_origins:
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
        # Join all allowed headers into a single string
        response.headers['Access-Control-Allow-Headers'] = ', '.join(cors_headers)
    return response

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

# Global OPTIONS handler for CORS preflight requests
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        origin = request.headers.get('Origin')
        if origin in allowed_origins:
            response = jsonify({'status': 'OK'})
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, PATCH, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = ', '.join(cors_headers)
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            response.status_code = 200
            return response

# Debug endpoint to see request headers (development only)
@app.route('/api/debug/headers', methods=['GET', 'POST', 'OPTIONS'])
def debug_headers():
    """Debug endpoint to inspect request headers"""
    if FLASK_ENV != 'development':
        return jsonify({'error': 'Debug endpoint only available in development'}), 403
    
    headers_dict = dict(request.headers)
    return jsonify({
        'method': request.method,
        'headers': headers_dict,
        'origin': request.headers.get('Origin'),
        'content_type': request.headers.get('Content-Type'),
        'user_agent': request.headers.get('User-Agent'),
        'timestamp': datetime.utcnow().isoformat()
    }), 200

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