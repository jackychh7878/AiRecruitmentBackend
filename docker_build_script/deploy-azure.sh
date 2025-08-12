#!/bin/bash

# Azure Container Apps Deployment Script for AI Recruitment Backend
set -e

echo "🚀 Deploying AI Recruitment Backend to Azure Container Apps..."

# Configuration
RESOURCE_GROUP="ai-recruitment-rg"
LOCATION="eastus"
CONTAINER_APP_NAME="ai-recruitment-backend"
CONTAINER_REGISTRY_NAME="airecruitmentregistry"
IMAGE_NAME="ai-recruitment-backend"
IMAGE_TAG="latest"
ENVIRONMENT_NAME="ai-recruitment-env"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install it first."
    exit 1
fi

# Check if logged into Azure
print_status "Checking Azure login status..."
if ! az account show &> /dev/null; then
    print_warning "Not logged into Azure. Please run 'az login' first."
    az login
fi

# Set subscription (optional - uncomment and modify if needed)
# print_status "Setting Azure subscription..."
# az account set --subscription "your-subscription-id"

# Create resource group
print_status "Creating resource group: $RESOURCE_GROUP"
az group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

# Create Azure Container Registry
print_status "Creating Azure Container Registry: $CONTAINER_REGISTRY_NAME"
az acr create \
    --resource-group $RESOURCE_GROUP \
    --name $CONTAINER_REGISTRY_NAME \
    --sku Basic \
    --admin-enabled true \
    --output table

# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name $CONTAINER_REGISTRY_NAME --resource-group $RESOURCE_GROUP --query "loginServer" --output tsv)
print_status "ACR Login Server: $ACR_LOGIN_SERVER"

# Login to ACR
print_status "Logging into Azure Container Registry..."
az acr login --name $CONTAINER_REGISTRY_NAME

# Build and push Docker image
print_status "Building Docker image..."
docker build -t $IMAGE_NAME:$IMAGE_TAG .

print_status "Tagging image for ACR..."
docker tag $IMAGE_NAME:$IMAGE_TAG $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

print_status "Pushing image to ACR..."
docker push $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG

# Create Container Apps Environment
print_status "Creating Container Apps Environment: $ENVIRONMENT_NAME"
az containerapp env create \
    --name $ENVIRONMENT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

# Create Container App
print_status "Creating Container App: $CONTAINER_APP_NAME"
az containerapp create \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --environment $ENVIRONMENT_NAME \
    --image $ACR_LOGIN_SERVER/$IMAGE_NAME:$IMAGE_TAG \
    --target-port 5000 \
    --ingress external \
    --registry-server $ACR_LOGIN_SERVER \
    --registry-username $(az acr credential show --name $CONTAINER_REGISTRY_NAME --query "username" --output tsv) \
    --registry-password $(az acr credential show --name $CONTAINER_REGISTRY_NAME --query "passwords[0].value" --output tsv) \
    --cpu 1.0 \
    --memory 2.0Gi \
    --min-replicas 1 \
    --max-replicas 5 \
    --env-vars \
        FLASK_ENV=production \
        HOST=0.0.0.0 \
        PORT=5000 \
        WORKERS=2 \
        DATABASE_URL="$DATABASE_URL" \
        OPENAI_API_KEY="$OPENAI_API_KEY" \
        AZURE_OPENAI_API_KEY="$AZURE_OPENAI_API_KEY" \
        AZURE_OPENAI_ENDPOINT="$AZURE_OPENAI_ENDPOINT" \
        AZURE_OPENAI_API_VERSION="$AZURE_OPENAI_API_VERSION" \
    --output table

# Get the Container App URL
CONTAINER_APP_URL=$(az containerapp show \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query "properties.configuration.ingress.fqdn" \
    --output tsv)

print_status "Container App deployed successfully!"
print_status "URL: https://$CONTAINER_APP_URL"
print_status "Swagger UI: https://$CONTAINER_APP_URL/swagger/"

# Create Application Insights (optional)
print_status "Creating Application Insights..."
az monitor app-insights component create \
    --app ai-recruitment-insights \
    --location $LOCATION \
    --resource-group $RESOURCE_GROUP \
    --application-type web \
    --output table

# Get Application Insights key
INSIGHTS_KEY=$(az monitor app-insights component show \
    --app ai-recruitment-insights \
    --resource-group $RESOURCE_GROUP \
    --query "instrumentationKey" \
    --output tsv)

print_status "Application Insights Key: $INSIGHTS_KEY"

# Update Container App with Application Insights
print_status "Updating Container App with Application Insights..."
az containerapp update \
    --name $CONTAINER_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --set-env-vars APPLICATIONINSIGHTS_CONNECTION_STRING="InstrumentationKey=$INSIGHTS_KEY" \
    --output table

# Create custom domain (optional)
if [ -n "$CUSTOM_DOMAIN" ]; then
    print_status "Setting up custom domain: $CUSTOM_DOMAIN"
    az containerapp hostname add \
        --hostname $CUSTOM_DOMAIN \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --output table
fi

# Create SSL certificate (optional)
if [ -n "$SSL_CERT_PATH" ] && [ -n "$SSL_KEY_PATH" ]; then
    print_status "Setting up SSL certificate..."
    az containerapp hostname bind \
        --hostname $CUSTOM_DOMAIN \
        --name $CONTAINER_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --certificate $SSL_CERT_PATH \
        --key $SSL_KEY_PATH \
        --output table
fi

print_status "Deployment completed successfully!"
echo ""
echo "📋 Summary:"
echo "   Resource Group: $RESOURCE_GROUP"
echo "   Container App: $CONTAINER_APP_NAME"
echo "   Container Registry: $CONTAINER_REGISTRY_NAME"
echo "   Environment: $ENVIRONMENT_NAME"
echo "   URL: https://$CONTAINER_APP_URL"
echo "   Swagger UI: https://$CONTAINER_APP_URL/swagger/"
echo ""
echo "🔧 Next steps:"
echo "   1. Configure your database connection"
echo "   2. Set your OpenAI API keys"
echo "   3. Test the health endpoint: https://$CONTAINER_APP_URL/api/health"
echo "   4. Access Swagger documentation: https://$CONTAINER_APP_URL/swagger/"
echo ""
echo "📚 Useful commands:"
echo "   View logs: az containerapp logs show --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP"
echo "   Scale app: az containerapp revision set-mode --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --mode single"
echo "   Update image: az containerapp update --name $CONTAINER_APP_NAME --resource-group $RESOURCE_GROUP --image $ACR_LOGIN_SERVER/$IMAGE_NAME:new-tag" 