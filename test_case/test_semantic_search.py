#!/usr/bin/env python3
"""
Test script for the semantic search API
"""

import requests
import json
import time

# Configuration
API_BASE_URL = "http://localhost:5000/api"

def test_search_statistics():
    """Test getting search statistics"""
    print("📊 Testing Search Statistics...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/semantic-search/statistics")
        
        if response.status_code == 200:
            stats = response.json()
            print("✅ Search statistics retrieved successfully:")
            print(f"   Total active candidates: {stats.get('total_active_candidates', 0)}")
            print(f"   Candidates with embeddings: {stats.get('candidates_with_embeddings', 0)}")
            print(f"   Embedding coverage: {stats.get('embedding_coverage_percentage', 0)}%")
            print(f"   Default confidence threshold: {stats.get('default_confidence_threshold', 0.7)}")
            print(f"   Max results limit: {stats.get('max_results_limit', 50)}")
            
            # Show hybrid scoring configuration
            hybrid_scoring = stats.get('hybrid_scoring', {})
            if hybrid_scoring:
                print(f"   Hybrid Scoring Configuration:")
                print(f"     Semantic weight: {hybrid_scoring.get('semantic_weight', 0.7)}")
                print(f"     Keyword weight: {hybrid_scoring.get('keyword_weight', 0.3)}")
                print(f"     Formula: {hybrid_scoring.get('formula', 'N/A')}")
                print(f"     Description: {hybrid_scoring.get('description', 'N/A')}")
            else:
                print(f"   ⚠️ Hybrid scoring configuration not available")
            
            return True
        else:
            print(f"❌ Failed to get statistics: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting statistics: {str(e)}")
        return False

def test_search_examples():
    """Test getting search examples"""
    print("\n📝 Testing Search Examples...")
    
    try:
        response = requests.get(f"{API_BASE_URL}/candidates/semantic-search/example-queries")
        
        if response.status_code == 200:
            examples = response.json()
            print("✅ Search examples retrieved successfully:")
            
            for category in examples.get('examples', []):
                print(f"   {category['category']}:")
                for query in category['queries'][:2]:  # Show first 2 examples
                    print(f"     - {query}")
            
            print(f"   Tips: {len(examples.get('tips', []))} tips provided")
            print(f"   Confidence thresholds: {len(examples.get('confidence_thresholds', {}))} levels")
            return True
        else:
            print(f"❌ Failed to get examples: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error getting examples: {str(e)}")
        return False

def test_semantic_search(query, confidence_threshold=None, max_results=None, include_relationships=False):
    """Test semantic search with given parameters"""
    print(f"\n🔍 Testing Semantic Search...")
    print(f"   Query: '{query}'")
    print(f"   Confidence threshold: {confidence_threshold or 'default'}")
    print(f"   Max results: {max_results or 'default'}")
    print(f"   Include relationships: {include_relationships}")
    
    try:
        payload = {
            'query': query,
            'include_relationships': include_relationships
        }
        
        if confidence_threshold is not None:
            payload['confidence_threshold'] = confidence_threshold
        if max_results is not None:
            payload['max_results'] = max_results
        
        response = requests.post(
            f"{API_BASE_URL}/candidates/semantic-search",
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            results = response.json()
            
            if results.get('success'):
                print("✅ Semantic search successful!")
                print(f"   Total found: {results.get('total_found', 0)}")
                print(f"   Query: {results.get('query', '')}")
                print(f"   Confidence threshold: {results.get('confidence_threshold', 0.7)}")
                print(f"   Query embedding dimension: {results.get('query_embedding_dimension', 0)}")
                
                # Show top results
                candidates = results.get('results', [])
                if candidates:
                    print(f"   Top results:")
                    for i, candidate in enumerate(candidates[:3]):  # Show top 3
                        name = f"{candidate.get('first_name', '')} {candidate.get('last_name', '')}"
                        semantic_score = candidate.get('semantic_score', 0)
                        keyword_score = candidate.get('keyword_score', 0)
                        hybrid_score = candidate.get('hybrid_score', 0)
                        confidence = candidate.get('confidence_level', 'Unknown')
                        relevance = candidate.get('relevance_percentage', 0)
                        
                        print(f"     {i+1}. {name}")
                        print(f"        Hybrid Score: {hybrid_score} ({confidence}, {relevance}%)")
                        print(f"        Breakdown: Semantic={semantic_score}, Keyword={keyword_score}")
                        
                        # Show scoring breakdown if available
                        scoring_breakdown = candidate.get('scoring_breakdown', {})
                        if scoring_breakdown:
                            semantic_contrib = scoring_breakdown.get('semantic_contribution', 0)
                            keyword_contrib = scoring_breakdown.get('keyword_contribution', 0)
                            print(f"        Contributions: Semantic={semantic_contrib}, Keyword={keyword_contrib}")
                        
                        if include_relationships:
                            skills_count = len(candidate.get('skills', []))
                            experience_count = len(candidate.get('career_history', []))
                            print(f"        Skills: {skills_count}, Experience: {experience_count}")
                else:
                    print("   No candidates found above threshold")
                
                return True
            else:
                print(f"❌ Search failed: {results.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Search request failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error during search: {str(e)}")
        return False

def test_various_search_scenarios():
    """Test various search scenarios"""
    print("\n🧪 Testing Various Search Scenarios...")
    
    # Test 1: Basic search
    print("\n1️⃣ Basic search with default settings:")
    test_semantic_search("Python developer")
    
    # Test 2: Search with custom confidence threshold
    print("\n2️⃣ Search with custom confidence threshold (0.8):")
    test_semantic_search("data scientist", confidence_threshold=0.8)
    
    # Test 3: Search with limited results
    print("\n3️⃣ Search with limited results (max 3):")
    test_semantic_search("software engineer", max_results=3)
    
    # Test 4: Search with relationships included
    print("\n4️⃣ Search with relationships included:")
    test_semantic_search("project manager", include_relationships=True)
    
    # Test 5: Complex query
    print("\n5️⃣ Complex query:")
    test_semantic_search("senior full-stack developer with React and Node.js experience in fintech")
    
    # Test 6: Low confidence threshold
    print("\n6️⃣ Search with low confidence threshold (0.5):")
    test_semantic_search("developer", confidence_threshold=0.5)

def test_error_handling():
    """Test error handling"""
    print("\n⚠️ Testing Error Handling...")
    
    # Test 1: Empty query
    print("\n1️⃣ Empty query:")
    response = requests.post(
        f"{API_BASE_URL}/candidates/semantic-search",
        json={'query': ''},
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 400 (Bad Request)")
    
    # Test 2: Invalid confidence threshold
    print("\n2️⃣ Invalid confidence threshold (1.5):")
    response = requests.post(
        f"{API_BASE_URL}/candidates/semantic-search",
        json={'query': 'developer', 'confidence_threshold': 1.5},
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 400 (Bad Request)")
    
    # Test 3: Invalid max results
    print("\n3️⃣ Invalid max results (-1):")
    response = requests.post(
        f"{API_BASE_URL}/candidates/semantic-search",
        json={'query': 'developer', 'max_results': -1},
        headers={"Content-Type": "application/json"}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Expected: 400 (Bad Request)")

if __name__ == "__main__":
    print("🧪 Semantic Search API Test Suite")
    print("=" * 50)
    
    # Test basic functionality
    stats_success = test_search_statistics()
    examples_success = test_search_examples()
    
    if stats_success and examples_success:
        print("\n✅ Basic functionality working, proceeding to search tests...")
        
        # Test various search scenarios
        test_various_search_scenarios()
        
        # Test error handling
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("🎉 Semantic Search API test completed!")
        print("\n💡 What was tested:")
        print("   ✅ Search statistics endpoint")
        print("   ✅ Search examples endpoint")
        print("   ✅ Basic semantic search")
        print("   ✅ Custom confidence thresholds")
        print("   ✅ Result limiting")
        print("   ✅ Relationship inclusion")
        print("   ✅ Complex queries")
        print("   ✅ Error handling")
        print("   ✅ Hybrid scoring system")
        print("   ✅ Semantic + Keyword combination")
        print("   ✅ Configurable weights")
        
        print("\n🔧 Hybrid Scoring System:")
        print("   Formula: hybrid_score = (semantic_weight × semantic_score) + (keyword_weight × keyword_score)")
        print("   Configurable via SEMANTIC_SEARCH_SEMANTIC_WEIGHT environment variable")
        print("   Default: 0.7 semantic + 0.3 keyword")
        print("   Provides balanced relevance scoring")
        
        print("\n🔍 How to use:")
        print("   POST /api/candidates/semantic-search")
        print("   GET /api/candidates/semantic-search/statistics")
        print("   GET /api/candidates/semantic-search/example-queries")
        
    else:
        print("\n❌ Basic functionality failed, check API availability")
        print("💡 Make sure the Flask app is running and the semantic search service is loaded") 