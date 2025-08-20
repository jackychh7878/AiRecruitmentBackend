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

# Configure logging early so we can use logger everywhere
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Add frontend URLs from environment (supports multiple URLs, comma-separated)
frontend_urls = os.getenv('FRONTEND_URL', '').strip()
if frontend_urls:
    for url in frontend_urls.split(','):
        url = url.strip()
        if url and url not in allowed_origins:
            allowed_origins.append(url)
            logger.info(f"Added frontend URL to CORS origins: {url}")

# Add additional CORS origins from environment (comma-separated)
additional_origins = os.getenv('ADDITIONAL_CORS_ORIGINS', '').strip()
if additional_origins:
    for origin in additional_origins.split(','):
        origin = origin.strip()
        if origin and origin not in allowed_origins:
            allowed_origins.append(origin)
            logger.info(f"Added additional CORS origin: {origin}")

logger.info(f"CORS allowed origins: {allowed_origins}")

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

# Configure file upload limits for batch resume processing
# Individual file size limit (used for validation in application logic)
individual_file_limit = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))  # 16MB default

# Total batch upload size limit (used for validation in application logic)
batch_upload_limit = int(os.getenv('BATCH_UPLOAD_LIMIT', 200 * 1024 * 1024))  # 200MB default

# Flask's MAX_CONTENT_LENGTH must be set to the maximum of individual and batch limits
# This is a hard limit that Flask enforces before the request reaches our code
# Add significant buffer for form data overhead (headers, boundaries, etc.)
# Form data can add 20-30% overhead, so we add 100MB buffer to be safe
flask_max_content_length = max(individual_file_limit, batch_upload_limit) + (100 * 1024 * 1024)  # +100MB buffer
app.config['MAX_CONTENT_LENGTH'] = flask_max_content_length

# Configure werkzeug form data parser limits
# Set this to be generous to handle large multipart uploads
app.config['MAX_FORM_MEMORY_SIZE'] = flask_max_content_length * 2  # Double the content length for form parsing

# Configure additional Werkzeug settings for better file upload handling
app.config['MAX_FORM_PARTS'] = 1000  # Maximum number of form parts
app.config['UPLOAD_FOLDER'] = '/tmp'  # Temporary folder for large uploads

# Additional werkzeug multipart parsing settings to handle the specific parsing issue
# The error suggests werkzeug is trying to parse multipart data as URL-encoded
# Let's be more explicit about multipart handling
import tempfile
app.config['MAX_FORM_MEMORY_SIZE'] = flask_max_content_length  # Restore the memory size limit
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching for uploads

# Set a temporary directory for file uploads to avoid memory issues
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# Additional Flask/Werkzeug settings to handle multipart parsing issues
# These help prevent the "exceeds capacity limit" error with form parsing
app.config['MAX_CONTENT_PATH'] = None  # Remove path length restrictions
app.config['APPLICATION_ROOT'] = '/'  # Ensure proper root path

logger.info(f"File upload limits configured:")
logger.info(f"  Flask MAX_CONTENT_LENGTH: {app.config['MAX_CONTENT_LENGTH'] / 1024 / 1024:.1f}MB")
logger.info(f"  Flask MAX_FORM_MEMORY_SIZE: {app.config['MAX_FORM_MEMORY_SIZE'] / 1024 / 1024:.1f}MB")
logger.info(f"  Individual file limit: {individual_file_limit / 1024 / 1024:.1f}MB")
logger.info(f"  Batch upload limit: {batch_upload_limit / 1024 / 1024:.1f}MB")

# Initialize SQLAlchemy with app
db.init_app(app)

# Add a before_request handler to help debug multipart parsing issues
@app.before_request
def before_request():
    """Log request details for debugging multipart upload issues"""
    if request.endpoint and 'batch-parse-resumes' in request.endpoint:
        logger.info(f"Before request - Content-Type: {request.content_type}")
        logger.info(f"Before request - Content-Length: {request.content_length}")
        # Force multipart parsing to happen in a controlled way
        if request.content_type and 'multipart/form-data' in request.content_type:
            try:
                # This forces werkzeug to parse the form data early
                # which can help identify parsing issues
                _ = len(request.form)
                logger.info("Form data parsing successful")
            except Exception as e:
                logger.error(f"Form data parsing failed: {str(e)}")

# Add error handlers for request size limits
@app.errorhandler(413)
def request_entity_too_large(error):
    """Handle request entity too large errors with user-friendly messages"""
    batch_limit = int(os.getenv('BATCH_UPLOAD_LIMIT', 200 * 1024 * 1024))
    batch_limit_mb = batch_limit / 1024 / 1024
    return jsonify({
        'error': 'Request too large',
        'message': f'Upload size exceeds the maximum limit of {batch_limit_mb:.1f}MB. Please reduce the number of files or file sizes and try again.',
        'code': 413
    }), 413

@app.errorhandler(400)
def bad_request(error):
    """Handle bad request errors, including form parsing issues"""
    error_description = getattr(error, 'description', str(error))
    if 'UnicodeDecodeError' in str(error_description) or 'utf-8' in str(error_description):
        return jsonify({
            'error': 'Invalid file encoding',
            'message': 'Invalid file encoding detected. Please ensure all files are valid PDFs.',
            'code': 400
        }), 400
    return jsonify({
        'error': 'Bad request',
        'message': str(error_description),
        'code': 400
    }), 400

# Initialize bulk AI regeneration service with app context
from services.bulk_ai_regeneration_service import bulk_ai_regeneration_service
from services.batch_resume_parser import batch_resume_parser_service
with app.app_context():
    bulk_ai_regeneration_service.set_app(app)
    batch_resume_parser_service.set_app(app)

# Logging already configured at the top of the file

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