#!/bin/bash

# AI Recruitment Backend Startup Script (Standalone)
set -e

echo "🚀 Starting AI Recruitment Backend..."

# Create necessary directories if they don't exist
mkdir -p /app/logs /app/uploads /app/models /app/nltk_data

# Set environment variables with defaults
export FLASK_ENV=${FLASK_ENV:-production}
export FLASK_APP=${FLASK_APP:-app.py}
export HOST=${HOST:-0.0.0.0}
export PORT=${PORT:-5000}
export WORKERS=${WORKERS:-4}

# Pre-download NLTK data if not present
echo "📚 Checking NLTK data..."
python -c "
import nltk
import os

# Download NLTK data if not present
data_path = '/app/nltk_data'
if not os.path.exists(data_path):
    os.makedirs(data_path)
    nltk.data.path.append(data_path)

try:
    nltk.data.find('tokenizers/punkt')
    print('✅ NLTK punkt tokenizer found')
except LookupError:
    print('📥 Downloading NLTK punkt tokenizer...')
    nltk.download('punkt', download_dir=data_path)

try:
    nltk.data.find('corpora/stopwords')
    print('✅ NLTK stopwords found')
except LookupError:
    print('📥 Downloading NLTK stopwords...')
    nltk.download('stopwords', download_dir=data_path)

try:
    nltk.data.find('corpora/wordnet')
    print('✅ NLTK wordnet found')
except LookupError:
    print('📥 Downloading NLTK wordnet...')
    nltk.download('wordnet', download_dir=data_path)
"

# Pre-load spaCy model
echo "🤖 Loading spaCy NER model..."
python -c "
import spacy
try:
    nlp = spacy.load('en_core_web_sm')
    print('✅ spaCy model loaded successfully')
except OSError:
    print('📥 Downloading spaCy model...')
    import subprocess
    subprocess.run(['python', '-m', 'spacy', 'download', 'en_core_web_sm'], check=True)
    print('✅ spaCy model downloaded and loaded')
"

# Start the application
echo "🌐 Starting Flask application on ${HOST}:${PORT}..."
if [ "$FLASK_ENV" = "development" ]; then
    echo "🔧 Development mode - using Flask development server"
    exec python app.py
else
    echo "🚀 Production mode - using Gunicorn with ${WORKERS} workers"
    exec gunicorn \
        --bind ${HOST}:${PORT} \
        --workers ${WORKERS} \
        --worker-class sync \
        --worker-connections 1000 \
        --max-requests 1000 \
        --max-requests-jitter 100 \
        --timeout 120 \
        --keep-alive 2 \
        --preload \
        --access-logfile /app/logs/access.log \
        --error-logfile /app/logs/error.log \
        --log-level info \
        app:app
fi 