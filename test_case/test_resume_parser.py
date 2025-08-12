#!/usr/bin/env python3
"""
Test script for resume parsing functionality
Run this to verify that all dependencies are installed correctly
"""

import sys
import os

def test_imports():
    """Test if all required packages can be imported"""
    print("Testing imports...")
    
    try:
        import PyPDF2
        print("✓ PyPDF2 imported successfully")
    except ImportError as e:
        print(f"✗ PyPDF2 import failed: {e}")
        return False
        
    try:
        import spacy
        print("✓ spaCy imported successfully")
    except ImportError as e:
        print(f"✗ spaCy import failed: {e}")
        return False
        
    try:
        import nltk
        print("✓ NLTK imported successfully")
    except ImportError as e:
        print(f"✗ NLTK import failed: {e}")
        return False
        
    try:
        import sklearn
        print("✓ scikit-learn imported successfully")
    except ImportError as e:
        print(f"✗ scikit-learn import failed: {e}")
        return False
        
    return True

def test_spacy_model():
    """Test if spaCy English model is available"""
    print("\nTesting spaCy English model...")
    
    try:
        import spacy
        nlp = spacy.load('en_core_web_sm')
        print("✓ spaCy English model loaded successfully")
        
        # Test basic NER
        doc = nlp("John Doe works at Microsoft in Seattle.")
        entities = [(ent.text, ent.label_) for ent in doc.ents]
        print(f"✓ NER test found entities: {entities}")
        return True
        
    except OSError as e:
        print(f"✗ spaCy English model not found: {e}")
        print("Please install it using: python -m spacy download en_core_web_sm")
        return False
    except Exception as e:
        print(f"✗ spaCy model test failed: {e}")
        return False

def test_nltk_data():
    """Test if required NLTK data is available"""
    print("\nTesting NLTK data...")
    
    try:
        import nltk
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        from nltk.tokenize import word_tokenize
        
        # Test stopwords
        try:
            stop_words = stopwords.words('english')
            print("✓ NLTK stopwords available")
        except LookupError:
            print("Downloading NLTK stopwords...")
            nltk.download('stopwords')
            stop_words = stopwords.words('english')
            print("✓ NLTK stopwords downloaded and available")
            
        # Test WordNet lemmatizer
        try:
            lemmatizer = WordNetLemmatizer()
            test_word = lemmatizer.lemmatize('running')
            print("✓ NLTK WordNet lemmatizer available")
        except LookupError:
            print("Downloading NLTK wordnet...")
            nltk.download('wordnet')
            lemmatizer = WordNetLemmatizer()
            test_word = lemmatizer.lemmatize('running')
            print("✓ NLTK WordNet downloaded and available")
            
        # Test punkt tokenizer
        try:
            tokens = word_tokenize("This is a test sentence.")
            print("✓ NLTK punkt tokenizer available")
        except LookupError:
            print("Downloading NLTK punkt...")
            nltk.download('punkt')
            tokens = word_tokenize("This is a test sentence.")
            print("✓ NLTK punkt downloaded and available")
            
        return True
        
    except Exception as e:
        print(f"✗ NLTK data test failed: {e}")
        return False

def test_resume_parser_service():
    """Test the resume parser service"""
    print("\nTesting resume parser service...")
    
    try:
        # Add the project root to Python path
        project_root = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, project_root)
        
        from services.resume_parser import ResumeParser
        
        # Initialize parser
        parser = ResumeParser()
        print("✓ ResumeParser initialized successfully")
        
        # Test text cleaning
        test_text = "This is a test resume with special characters !@#$%"
        cleaned = parser.clean_text(test_text)
        print(f"✓ Text cleaning works: '{cleaned}'")
        
        # Test contact info extraction
        contact_text = "Contact me at john.doe@example.com or call (555) 123-4567"
        contact_info = parser.extract_contact_info(contact_text)
        print(f"✓ Contact extraction works: {contact_info}")
        
        # Test summary extraction
        summary_text = """
        EXECUTIVE SUMMARY
        
        Experienced software engineer with 5+ years of experience in full-stack development.
        Proven track record of delivering high-quality applications using modern technologies.
        
        EXPERIENCE
        
        Senior Developer at Tech Corp...
        """
        extracted_summary = parser._extract_summary_section(summary_text)
        print(f"✓ Summary extraction works: '{extracted_summary[:100]}...'" if extracted_summary else "✓ Summary extraction works: None")
        
        return True
        
    except Exception as e:
        print(f"✗ Resume parser service test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Resume Parser Dependency Test")
    print("=" * 40)
    
    all_passed = True
    
    # Test imports
    if not test_imports():
        all_passed = False
        
    # Test spaCy model
    if not test_spacy_model():
        all_passed = False
        
    # Test NLTK data
    if not test_nltk_data():
        all_passed = False
        
    # Test resume parser service
    if not test_resume_parser_service():
        all_passed = False
    
    print("\n" + "=" * 40)
    if all_passed:
        print("🎉 All tests passed! Resume parsing is ready to use.")
        print("\nNext steps:")
        print("1. Start your Flask application")
        print("2. Navigate to /candidates/parse-resume in Swagger UI")
        print("3. Upload a PDF resume to test the parsing functionality")
    else:
        print("❌ Some tests failed. Please install missing dependencies:")
        print("1. pip install -r requirements.txt")
        print("2. python -m spacy download en_core_web_sm")
        
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 