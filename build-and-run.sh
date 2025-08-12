#!/bin/bash

# AI Recruitment Backend - Build and Run Script
set -e

echo "🚀 Building and running AI Recruitment Backend..."

# Configuration
IMAGE_NAME="ai-recruitment-backend"
CONTAINER_NAME="ai-recruitment-backend"
PORT=5000

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f .env.prod_example ]; then
        cp .env.prod_example .env
        print_status "Created .env from env.example. Please edit it with your configuration."
        print_warning "You need to set your DATABASE_URL and other environment variables."
        exit 1
    else
        print_error "env.example not found. Please create a .env file with your configuration."
        exit 1
    fi
fi

# Stop and remove existing container if running
if docker ps -q -f name=$CONTAINER_NAME | grep -q .; then
    print_status "Stopping existing container..."
    docker stop $CONTAINER_NAME
fi

if docker ps -aq -f name=$CONTAINER_NAME | grep -q .; then
    print_status "Removing existing container..."
    docker rm $CONTAINER_NAME
fi

# Build the Docker image
print_status "Building Docker image..."
docker build -t $IMAGE_NAME .

if [ $? -eq 0 ]; then
    print_status "Docker image built successfully!"
else
    print_error "Failed to build Docker image."
    exit 1
fi

# Run the container
print_status "Starting container..."
docker run -d \
    --name $CONTAINER_NAME \
    -p $PORT:$PORT \
    --env-file .env \
    $IMAGE_NAME

if [ $? -eq 0 ]; then
    print_status "Container started successfully!"
    print_status "Application URL: http://localhost:$PORT"
    print_status "Swagger UI: http://localhost:$PORT/swagger/"
    print_status "Health Check: http://localhost:$PORT/api/health"
    
    echo ""
    echo "📋 Useful commands:"
    echo "   View logs: docker logs $CONTAINER_NAME"
    echo "   Stop container: docker stop $CONTAINER_NAME"
    echo "   Remove container: docker rm $CONTAINER_NAME"
    echo "   Enter container: docker exec -it $CONTAINER_NAME bash"
    
    echo ""
    echo "⏳ Waiting for application to start..."
    sleep 10
    
    # Test health endpoint
    if curl -f http://localhost:$PORT/api/health > /dev/null 2>&1; then
        print_status "✅ Application is healthy and running!"
    else
        print_warning "⚠️ Health check failed. Check logs with: docker logs $CONTAINER_NAME"
    fi
    
else
    print_error "Failed to start container."
    exit 1
fi 