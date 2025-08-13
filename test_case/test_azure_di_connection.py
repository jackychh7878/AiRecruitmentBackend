#!/usr/bin/env python3
"""
Simple Azure Document Intelligence connection test script
This script helps debug Azure DI configuration and endpoint issues
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_azure_di_import():
    """Test if Azure DI SDK can be imported"""
    print("Testing Azure Document Intelligence SDK import...")
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
        from azure.core.credentials import AzureKeyCredential
        print("✓ Azure DI SDK imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Azure DI SDK import failed: {e}")
        print("  Solution: pip install azure-ai-documentintelligence==1.0.0b4")
        return False

def test_environment_variables():
    """Test if required environment variables are set"""
    print("\nTesting environment variables...")
    
    use_azure_di = os.getenv('USE_AZURE_DOCUMENT_INTELLIGENCE', 'false').lower()
    endpoint = os.getenv('AZURE_DI_ENDPOINT')
    api_key = os.getenv('AZURE_DI_API_KEY')
    
    print(f"USE_AZURE_DOCUMENT_INTELLIGENCE: {use_azure_di}")
    print(f"AZURE_DI_ENDPOINT: {'SET' if endpoint else 'NOT SET'}")
    print(f"AZURE_DI_API_KEY: {'SET' if api_key else 'NOT SET'}")
    
    if use_azure_di == 'true':
        if not endpoint:
            print("✗ AZURE_DI_ENDPOINT is required when USE_AZURE_DOCUMENT_INTELLIGENCE=true")
            return False
        if not api_key:
            print("✗ AZURE_DI_API_KEY is required when USE_AZURE_DOCUMENT_INTELLIGENCE=true")
            return False
        
        # Validate endpoint format
        if not endpoint.startswith('https://'):
            print("✗ AZURE_DI_ENDPOINT should start with https://")
            return False
        
        if not endpoint.endswith('.cognitiveservices.azure.com/'):
            print("⚠ AZURE_DI_ENDPOINT should typically end with .cognitiveservices.azure.com/")
        
        print("✓ Environment variables are properly configured")
        return True
    else:
        print("ℹ Azure DI is disabled, skipping endpoint validation")
        return True

def test_azure_di_client():
    """Test if Azure DI client can be initialized"""
    print("\nTesting Azure DI client initialization...")
    
    use_azure_di = os.getenv('USE_AZURE_DOCUMENT_INTELLIGENCE', 'false').lower()
    if use_azure_di != 'true':
        print("ℹ Azure DI is disabled, skipping client test")
        return True
    
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv('AZURE_DI_ENDPOINT')
        api_key = os.getenv('AZURE_DI_API_KEY')
        
        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        print("✓ Azure DI client initialized successfully")
        print(f"  Endpoint: {endpoint}")
        return True
        
    except Exception as e:
        print(f"✗ Azure DI client initialization failed: {e}")
        return False

def test_simple_api_call():
    """Test a simple API call with model availability check"""
    print("\nTesting model availability...")
    
    use_azure_di = os.getenv('USE_AZURE_DOCUMENT_INTELLIGENCE', 'false').lower()
    if use_azure_di != 'true':
        print("ℹ Azure DI is disabled, skipping API test")
        return True
    
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv('AZURE_DI_ENDPOINT')
        api_key = os.getenv('AZURE_DI_API_KEY')
        
        print(f"  Using endpoint: {endpoint}")
        print(f"  Region appears to be: {endpoint.split('.')[0].split('-')[-1] if '.' in endpoint else 'unknown'}")
        
        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        print("  Testing model availability without sending document...")
        print("  Model: prebuilt-layout")
        print("  SDK Version: 1.0.0b4")
        
        # Test with empty request to check model availability
        # This will fail with InvalidRequest but won't fail with 404 if model exists
        try:
            analyze_request = AnalyzeDocumentRequest(bytes_source=b"")
            poller = client.begin_analyze_document("prebuilt-layout", analyze_request)
        except Exception as model_test_error:
            if "404" in str(model_test_error):
                print("✗ prebuilt-layout model not available (404)")
                return False
            elif "InvalidRequest" in str(model_test_error) or "InvalidContent" in str(model_test_error):
                print("✓ prebuilt-layout model is available (endpoint reachable)")
                print("  Note: Model exists but expects valid document content")
                return True
            else:
                print(f"✗ Unexpected error: {model_test_error}")
                return False
        
        # If we get here without exception, that's also good
        print("✓ API call initiated successfully (endpoint is reachable)")
        return True
        
    except Exception as e:
        error_msg = str(e)
        print(f"✗ API test failed: {error_msg}")
        
        if "404" in error_msg:
            print("  This is a 404 error. Model not available in this region.")
        elif "401" in error_msg:
            print("  This is an authentication error. Check your API key.")
        elif "403" in error_msg:
            print("  This is an authorization error. Check your resource permissions.")
        
        return False

def test_alternative_models():
    """Test alternative models that might be available"""
    print("\nTesting alternative models...")
    
    use_azure_di = os.getenv('USE_AZURE_DOCUMENT_INTELLIGENCE', 'false').lower()
    if use_azure_di != 'true':
        print("ℹ Azure DI is disabled, skipping alternative model test")
        return True
    
    try:
        from azure.ai.documentintelligence import DocumentIntelligenceClient
        from azure.ai.documentintelligence.models import AnalyzeDocumentRequest
        from azure.core.credentials import AzureKeyCredential
        
        endpoint = os.getenv('AZURE_DI_ENDPOINT')
        api_key = os.getenv('AZURE_DI_API_KEY')
        
        client = DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(api_key)
        )
        
        models_to_test = ["prebuilt-read", "prebuilt-document"]
        available_models = []
        
        for model_name in models_to_test:
            print(f"  Testing '{model_name}' model...")
            
            try:
                # Test with empty request to check model availability
                analyze_request = AnalyzeDocumentRequest(bytes_source=b"")
                poller = client.begin_analyze_document(model_name, analyze_request)
                print(f"✓ '{model_name}' model is available")
                available_models.append(model_name)
            except Exception as model_error:
                if "404" in str(model_error):
                    print(f"✗ '{model_name}' model not available (404)")
                elif "InvalidRequest" in str(model_error) or "InvalidContent" in str(model_error):
                    print(f"✓ '{model_name}' model is available")
                    available_models.append(model_name)
                else:
                    print(f"✗ '{model_name}' model failed with: {model_error}")
        
        if available_models:
            print(f"✓ Available models: {', '.join(available_models)}")
            return True
        else:
            print("✗ No alternative models found to work")
            return False
        
    except Exception as e:
        print(f"✗ Alternative model test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Azure Document Intelligence Connection Test")
    print("=" * 50)
    
    tests = [
        test_azure_di_import,
        test_environment_variables,
        test_azure_di_client,
        test_simple_api_call,
        test_alternative_models
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    
    all_passed = all(results)
    if all_passed:
        print("✓ All tests passed! Azure DI should work correctly.")
    else:
        print("✗ Some tests failed. Please review the issues above.")
        
    if not all_passed:
        print("\nTroubleshooting tips:")
        print("1. Verify your Azure DI resource is created and active")
        print("2. Check that the endpoint URL is exactly as shown in Azure portal")
        print("3. Ensure your API key is valid and not expired")
        print("4. Verify that Document Intelligence service is available in your region")
        print("5. Try the Azure portal's 'Test' feature to confirm the service works")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main()) 