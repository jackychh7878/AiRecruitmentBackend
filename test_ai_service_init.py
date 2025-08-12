#!/usr/bin/env python3
"""
Simple test to check AI service initialization
Run this to verify the AI service can be loaded without errors
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_variables():
    """Test if required environment variables are set"""
    print("🔍 Checking environment variables...")
    
    required_vars = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_API_KEY',
        'AZURE_OPENAI_DEPLOYMENT_NAME',
        'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: Set (length: {len(value)})")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("\n✅ All required environment variables are set")
        return True

def test_imports():
    """Test if all required packages can be imported"""
    print("\n🔍 Testing imports...")
    
    try:
        import langchain_openai
        print("✅ langchain_openai imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langchain_openai: {e}")
        return False
    
    try:
        from langchain_core.prompts import PromptTemplate
        print("✅ langchain_core.prompts imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langchain_core.prompts: {e}")
        return False
    
    try:
        from langchain_core.documents import Document
        print("✅ langchain_core.documents imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import langchain_core.documents: {e}")
        return False
    
    try:
        import openai
        print(f"✅ openai imported successfully (version: {openai.__version__})")
    except ImportError as e:
        print(f"❌ Failed to import openai: {e}")
        return False
    
    print("\n✅ All imports successful")
    return True

def test_ai_service_initialization():
    """Test if AI service can be initialized"""
    print("\n🔍 Testing AI service initialization...")
    
    try:
        from services.ai_summary_service import CandidateAISummaryService
        print("✅ AI service module imported successfully")
        
        # Try to initialize the service
        service = CandidateAISummaryService()
        print("✅ AI service initialized successfully")
        
        # Test prompt template
        template = service.prompt_template.template
        print(f"✅ Prompt template loaded (length: {len(template)})")
        
        return True
        
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Failed to initialize AI service: {e}")
        print(f"Error traceback: {error_traceback}")
        return False

def test_ai_service_singleton():
    """Test if AI service singleton can be imported"""
    print("\n🔍 Testing AI service singleton import...")
    
    try:
        from services.ai_summary_service import ai_summary_service
        print("✅ AI service singleton imported successfully")
        
        if ai_summary_service:
            print("✅ AI service singleton is not None")
            return True
        else:
            print("❌ AI service singleton is None")
            return False
            
    except Exception as e:
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Failed to import AI service singleton: {e}")
        print(f"Error traceback: {error_traceback}")
        return False

def main():
    """Run all tests"""
    print("🧪 AI Service Initialization Test")
    print("=" * 50)
    
    tests = [
        ("Environment Variables", test_environment_variables),
        ("Package Imports", test_imports),
        ("AI Service Initialization", test_ai_service_initialization),
        ("AI Service Singleton", test_ai_service_singleton)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        success = test_func()
        results.append((test_name, success))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY:")
    
    all_passed = True
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! AI service should work correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
        print("\n🔧 Common solutions:")
        print("1. Set up Azure OpenAI environment variables in .env file")
        print("2. Install/upgrade required packages: pip install -r requirements.txt")
        print("3. Check Azure OpenAI deployment names and API versions")

if __name__ == "__main__":
    main() 