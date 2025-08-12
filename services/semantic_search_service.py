import asyncio
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from database import db
from models import CandidateMasterProfile
from services.ai_summary_service import ai_summary_service
from sklearn.metrics.pairwise import cosine_similarity
import logging
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CandidateSemanticSearchService:
    """
    Service for hybrid semantic search of candidate profiles using:
    1. Semantic similarity (embeddings + cosine similarity)
    2. Exact keyword matching (text analysis)
    3. Weighted combination for final relevance score
    """
    
    def __init__(self):
        """Initialize the semantic search service"""
        self.default_confidence_threshold = 0.7  # Default similarity threshold
        self.max_results = 50  # Maximum number of results to return
        
        # Hybrid scoring weights (configurable via environment variables)
        self.semantic_weight = float(os.getenv('SEMANTIC_SEARCH_SEMANTIC_WEIGHT', 0.7))  # Weight for semantic similarity
        self.keyword_weight = 1.0 - self.semantic_weight  # Weight for exact keyword matching
        
        logger.info(f"Semantic Search Service initialized with weights:")
        logger.info(f"  Semantic weight: {self.semantic_weight}")
        logger.info(f"  Keyword weight: {self.keyword_weight}")
        logger.info(f"  Default confidence threshold: {self.default_confidence_threshold}")
        
    async def search_candidates(
        self, 
        query: str, 
        confidence_threshold: Optional[float] = None,
        max_results: Optional[int] = None,
        include_relationships: bool = False
    ) -> Dict[str, Any]:
        """
        Search candidates using semantic similarity
        
        Args:
            query (str): Natural language search query
            confidence_threshold (float, optional): Minimum similarity score (0.0 to 1.0)
            max_results (int, optional): Maximum number of results to return
            include_relationships (bool): Whether to include relationship data
            
        Returns:
            Dict: Search results with candidates and metadata
        """
        try:
            # Set defaults
            threshold = confidence_threshold if confidence_threshold is not None else self.default_confidence_threshold
            max_res = max_results if max_results is not None else self.max_results
            
            logger.info(f"Starting semantic search for query: '{query}' with threshold: {threshold}")
            
            # Validate threshold
            if not 0.0 <= threshold <= 1.0:
                raise ValueError("Confidence threshold must be between 0.0 and 1.0")
            
            # Generate embedding for the search query
            query_embedding = await self._generate_query_embedding(query)
            if query_embedding is None:
                return {
                    'success': False,
                    'error': 'Failed to generate query embedding',
                    'results': [],
                    'total_found': 0,
                    'query': query,
                    'confidence_threshold': threshold
                }
            
            # Search for similar candidates using hybrid approach
            search_results = await self._find_similar_candidates(
                query_embedding, 
                query,  # Pass original query text for keyword matching
                threshold, 
                max_res,
                include_relationships
            )
            
            return {
                'success': True,
                'results': search_results,
                'total_found': len(search_results),
                'query': query,
                'confidence_threshold': threshold,
                'query_embedding_dimension': len(query_embedding) if query_embedding is not None else 0
            }
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'results': [],
                'total_found': 0,
                'query': query,
                'confidence_threshold': threshold if 'threshold' in locals() else self.default_confidence_threshold
            }
    
    async def _generate_query_embedding(self, query: str) -> Optional[List[float]]:
        """
        Generate embedding for the search query using the same model as AI summaries
        
        Args:
            query (str): Search query text
            
        Returns:
            List[float]: Query embedding vector
        """
        try:
            logger.info(f"Generating embedding for query: '{query[:100]}...'")
            
            # Use the same embedding service as AI summaries
            embedding = await ai_summary_service.generate_embedding(query)
            
            if embedding and len(embedding) > 0:
                logger.info(f"Generated query embedding with dimension: {len(embedding)}")
                return embedding
            else:
                logger.error("Generated embedding is empty or None")
                return None
                
        except Exception as e:
            logger.error(f"Error generating query embedding: {str(e)}")
            return None
    
    async def _find_similar_candidates(
        self, 
        query_embedding: List[float], 
        query_text: str,
        threshold: float,
        max_results: int,
        include_relationships: bool
    ) -> List[Dict[str, Any]]:
        """
        Find candidates using hybrid approach: semantic similarity + keyword matching
        
        Args:
            query_embedding (List[float]): Query embedding vector
            query_text (str): Original search query text
            threshold (float): Minimum similarity threshold
            max_results (int): Maximum number of results
            include_relationships (bool): Whether to include relationship data
            
        Returns:
            List[Dict]: List of candidate results with hybrid relevance scores
        """
        try:
            logger.info(f"Searching for candidates with hybrid approach (threshold: {threshold})")
            
            # Get all candidates with embeddings
            candidates_with_embeddings = db.session.query(CandidateMasterProfile).filter(
                CandidateMasterProfile.embedding_vector.isnot(None),
                CandidateMasterProfile.is_active == True
            ).all()
            
            if not candidates_with_embeddings:
                logger.info("No candidates with embeddings found")
                return []
            
            logger.info(f"Found {len(candidates_with_embeddings)} candidates with embeddings")
            
            # Calculate hybrid scores for all candidates
            candidate_scores = []
            for candidate in candidates_with_embeddings:
                try:
                    # Get candidate embedding
                    candidate_embedding = candidate.embedding_vector
                    
                    if candidate_embedding is not None:
                        # Convert to list if it's a numpy array
                        if hasattr(candidate_embedding, 'tolist'):
                            candidate_embedding = candidate_embedding.tolist()
                        
                        # Calculate semantic similarity
                        semantic_score = self._calculate_cosine_similarity(
                            query_embedding, 
                            candidate_embedding
                        )
                        
                        # Calculate keyword matching score
                        keyword_score = self._calculate_keyword_matching_score(
                            query_text, 
                            candidate
                        )
                        
                        # Calculate hybrid score using weighted formula
                        hybrid_score = (
                            self.semantic_weight * semantic_score + 
                            self.keyword_weight * keyword_score
                        )
                        
                        logger.debug(f"Candidate {candidate.id}: semantic={semantic_score:.4f}, keyword={keyword_score:.4f}, hybrid={hybrid_score:.4f}")
                        
                        if hybrid_score >= threshold:
                            candidate_scores.append({
                                'candidate': candidate,
                                'semantic_score': semantic_score,
                                'keyword_score': keyword_score,
                                'hybrid_score': hybrid_score
                            })
                            
                except Exception as e:
                    logger.warning(f"Error calculating scores for candidate {candidate.id}: {str(e)}")
                    continue
            
            # Sort by hybrid score (highest first)
            candidate_scores.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # Limit results
            top_candidates = candidate_scores[:max_results]
            
            logger.info(f"Found {len(top_candidates)} candidates above threshold {threshold}")
            
            # Convert to response format
            results = []
            for item in top_candidates:
                candidate = item['candidate']
                semantic_score = item['semantic_score']
                keyword_score = item['keyword_score']
                hybrid_score = item['hybrid_score']
                
                # Convert candidate to dict
                candidate_dict = candidate.to_dict(include_relationships=include_relationships)
                
                # Add hybrid scoring and metadata
                result_item = {
                    **candidate_dict,
                    'semantic_score': round(semantic_score, 4),
                    'keyword_score': round(keyword_score, 4),
                    'hybrid_score': round(hybrid_score, 4),
                    'confidence_level': self._get_confidence_level(hybrid_score),
                    'relevance_percentage': round(hybrid_score * 100, 1),
                    'scoring_breakdown': {
                        'semantic_weight': self.semantic_weight,
                        'keyword_weight': self.keyword_weight,
                        'semantic_contribution': round(self.semantic_weight * semantic_score, 4),
                        'keyword_contribution': round(self.keyword_weight * keyword_score, 4)
                    }
                }
                
                results.append(result_item)
            
            return results
            
        except Exception as e:
            logger.error(f"Error finding similar candidates: {str(e)}")
            return []
            
        except Exception as e:
            logger.error(f"Error finding similar candidates: {str(e)}")
            return []
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        
        Args:
            vec1 (List[float]): First vector
            vec2 (List[float]): Second vector
            
        Returns:
            float: Cosine similarity score (0.0 to 1.0)
        """
        try:
            # Convert to numpy arrays
            v1 = np.array(vec1).reshape(1, -1)
            v2 = np.array(vec2).reshape(1, -1)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(v1, v2)[0][0]
            
            # Ensure result is between 0 and 1
            return max(0.0, min(1.0, similarity))
            
        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {str(e)}")
            return 0.0
    
    def _calculate_keyword_matching_score(self, query_text: str, candidate: CandidateMasterProfile) -> float:
        """
        Calculate keyword matching score based on exact text matches
        
        Args:
            query_text (str): Search query text
            candidate (CandidateMasterProfile): Candidate profile to analyze
            
        Returns:
            float: Keyword matching score (0.0 to 1.0)
        """
        try:
            # Normalize query text
            query_lower = query_text.lower().strip()
            query_words = set(re.findall(r'\b\w+\b', query_lower))
            
            # Remove common stop words that don't add value
            stop_words = {
                'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 
                'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 
                'to', 'was', 'will', 'with', 'the', 'this', 'but', 'they', 'have', 
                'had', 'what', 'said', 'each', 'which', 'she', 'do', 'how', 'their', 
                'if', 'up', 'out', 'many', 'then', 'them', 'these', 'so', 'some', 
                'her', 'would', 'make', 'like', 'into', 'him', 'time', 'two', 'more', 
                'go', 'no', 'way', 'could', 'my', 'than', 'first', 'been', 'call', 
                'who', 'its', 'now', 'find', 'down', 'day', 'did', 'get', 'come', 
                'made', 'may', 'part', 'over', 'new', 'sound', 'take', 'only', 'little', 
                'work', 'know', 'place', 'year', 'live', 'me', 'back', 'give', 'most', 
                'very', 'after', 'thing', 'our', 'just', 'name', 'good', 'sentence', 
                'man', 'think', 'say', 'great', 'where', 'help', 'through', 'much', 
                'before', 'line', 'right', 'too', 'mean', 'old', 'any', 'same', 'tell', 
                'boy', 'follow', 'came', 'want', 'show', 'also', 'around', 'form', 
                'three', 'small', 'set', 'put', 'end', 'does', 'another', 'well', 
                'large', 'must', 'big', 'even', 'such', 'because', 'turn', 'here', 
                'why', 'ask', 'went', 'men', 'read', 'need', 'land', 'different', 
                'home', 'us', 'move', 'try', 'kind', 'hand', 'picture', 'change', 
                'off', 'play', 'spell', 'air', 'away', 'animal', 'house', 'point', 
                'page', 'letter', 'mother', 'answer', 'found', 'study', 'still', 'learn', 
                'should', 'America', 'world', 'high', 'every', 'near', 'add', 'food', 
                'between', 'own', 'below', 'country', 'plant', 'last', 'school', 'father', 
                'keep', 'tree', 'never', 'start', 'city', 'earth', 'eye', 'light', 
                'thought', 'head', 'under', 'story', 'saw', 'left', 'don\'t', 'few', 
                'while', 'along', 'might', 'close', 'something', 'seem', 'next', 'hard', 
                'open', 'example', 'begin', 'life', 'always', 'those', 'both', 'paper', 
                'together', 'got', 'group', 'often', 'run', 'important', 'until', 'children', 
                'side', 'feet', 'car', 'miles', 'night', 'walk', 'white', 'sea', 'began', 
                'grew', 'took', 'river', 'four', 'carry', 'state', 'once', 'book', 
                'hear', 'stop', 'without', 'second', 'late', 'miss', 'idea', 'enough', 
                'eat', 'face', 'watch', 'far', 'Indian', 'real', 'almost', 'let', 'above', 
                'girl', 'sometimes', 'mountain', 'cut', 'young', 'talk', 'soon', 'list', 
                'song', 'being', 'leave', 'family', 'it\'s'
            }
            
            # Filter out stop words from query
            query_words = query_words - stop_words
            
            if not query_words:
                return 0.0  # No meaningful words to match
            
            # Collect all searchable text from candidate profile
            searchable_texts = []
            
            # AI summary (highest weight)
            if candidate.ai_short_summary:
                searchable_texts.append(('ai_summary', candidate.ai_short_summary.lower()))
            
            # Personal summary
            if candidate.personal_summary:
                searchable_texts.append(('personal_summary', candidate.personal_summary.lower()))
            
            # Classification fields
            if candidate.classification_of_interest:
                searchable_texts.append(('classification', candidate.classification_of_interest.lower()))
            if candidate.sub_classification_of_interest:
                searchable_texts.append(('sub_classification', candidate.sub_classification_of_interest.lower()))
            
            # Remarks
            if candidate.remarks:
                searchable_texts.append(('remarks', candidate.remarks.lower()))
            
            # Calculate keyword matches with different weights
            total_score = 0.0
            max_possible_score = 0.0
            
            for field_name, text in searchable_texts:
                # Count exact word matches
                matches = 0
                for word in query_words:
                    if word in text:
                        matches += 1
                
                # Calculate field score based on match ratio
                field_score = matches / len(query_words) if query_words else 0.0
                
                # Apply field weights (AI summary gets highest weight)
                if field_name == 'ai_summary':
                    field_weight = 1.0
                elif field_name == 'personal_summary':
                    field_weight = 0.8
                elif field_name in ['classification', 'sub_classification']:
                    field_weight = 0.6
                else:
                    field_weight = 0.4
                
                total_score += field_score * field_weight
                max_possible_score += field_weight
            
            # Normalize to 0-1 range
            if max_possible_score > 0:
                keyword_score = total_score / max_possible_score
            else:
                keyword_score = 0.0
            
            # Boost score for exact phrase matches
            if query_lower in candidate.ai_short_summary.lower() if candidate.ai_short_summary else False:
                keyword_score = min(1.0, keyword_score + 0.2)  # Boost for exact phrase match
            
            return min(1.0, keyword_score)
            
        except Exception as e:
            logger.warning(f"Error calculating keyword score for candidate {candidate.id}: {str(e)}")
            return 0.0
    
    def _get_confidence_level(self, similarity_score: float) -> str:
        """
        Convert similarity score to confidence level description
        
        Args:
            similarity_score (float): Similarity score (0.0 to 1.0)
            
        Returns:
            str: Confidence level description
        """
        if similarity_score >= 0.5:
            return "Very High"
        elif similarity_score >= 0.4:
            return "High"
        elif similarity_score >= 0.3:
            return "Good"
        elif similarity_score >= 0.2:
            return "Moderate"
        elif similarity_score >= 0.1:
            return "Low"
        else:
            return "Very Low"
    
    def get_search_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the search system
        
        Returns:
            Dict: Search system statistics
        """
        try:
            total_candidates = db.session.query(CandidateMasterProfile).filter(
                CandidateMasterProfile.is_active == True
            ).count()
            
            candidates_with_embeddings = db.session.query(CandidateMasterProfile).filter(
                CandidateMasterProfile.embedding_vector.isnot(None),
                CandidateMasterProfile.is_active == True
            ).count()
            
            candidates_without_embeddings = total_candidates - candidates_with_embeddings
            
            return {
                'total_active_candidates': total_candidates,
                'candidates_with_embeddings': candidates_with_embeddings,
                'candidates_without_embeddings': candidates_without_embeddings,
                'embedding_coverage_percentage': round((candidates_with_embeddings / total_candidates * 100), 1) if total_candidates > 0 else 0,
                'default_confidence_threshold': self.default_confidence_threshold,
                'max_results_limit': self.max_results,
                'hybrid_scoring': {
                    'semantic_weight': self.semantic_weight,
                    'keyword_weight': self.keyword_weight,
                    'formula': f"{self.semantic_weight} × semantic_score + {self.keyword_weight} × keyword_score",
                    'description': 'Hybrid scoring combines semantic similarity with exact keyword matching'
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting search statistics: {str(e)}")
            return {
                'error': str(e)
            }

# Create singleton instance
semantic_search_service = CandidateSemanticSearchService() 