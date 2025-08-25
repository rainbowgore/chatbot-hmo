import os
import numpy as np
import logging
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from openai import AzureOpenAI
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from .knowledge_base import KnowledgeChunk, KnowledgeBaseService

load_dotenv()
logger = logging.getLogger(__name__)

class EmbeddingsService:
    def __init__(self):
        # Azure OpenAI client for embeddings
        self.client = AzureOpenAI(
            api_key=os.getenv("AOAI_API_KEY") or os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        # Embedding deployment name (Azure uses deployment name, not model id)
        self.embedding_deployment = os.getenv(
            "AZURE_OPENAI_EMBEDDING_DEPLOYMENT",
            "text-embedding-ada-002"
        )
        
        # Storage for embeddings
        self.chunk_embeddings: Dict[str, np.ndarray] = {}
        self.chunks: List[KnowledgeChunk] = []
        
        # Knowledge base service
        self.kb_service = KnowledgeBaseService()
        
    def initialize_knowledge_base(self) -> None:
        """Load knowledge base and generate embeddings"""
        print("Loading knowledge base...")
        self.kb_service.load_knowledge_base()
        self.chunks = self.kb_service.chunks
        
        print(f"Loaded {len(self.chunks)} chunks")
        print("Generating embeddings...")
        
        # Generate embeddings for all chunks
        for i, chunk in enumerate(self.chunks):
            if i % 10 == 0:
                print(f"Processing chunk {i+1}/{len(self.chunks)}")
                
            embedding = self._get_embedding(chunk.content)
            self.chunk_embeddings[chunk.chunk_id] = embedding
            
        print("Knowledge base initialization complete!")
        
    def _get_embedding(self, text: str) -> np.ndarray:
        """Get embedding for a text using Azure OpenAI"""
        try:
            # Use Azure deployment name from env
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_deployment
            )
            
            embedding = np.array(response.data[0].embedding)
            return embedding
            
        except Exception as e:
            print(f"Error getting embedding: {e}")
            # Return zero vector as fallback
            return np.zeros(1536)  # Ada-002 embedding size
            
    def search_similar(self, query: str, user_hmo: str = None, user_tier: str = None, top_k: int = 5) -> List[Tuple[KnowledgeChunk, float]]:
        """Search for similar chunks based on query and user profile"""
        
        # Get query embedding
        query_embedding = self._get_embedding(query)
        
        # Filter chunks based on user profile
        relevant_chunks = self.kb_service.get_chunks_for_user(user_hmo, user_tier)
        
        # Calculate similarities
        similarities = []
        
        for chunk in relevant_chunks:
            if chunk.chunk_id in self.chunk_embeddings:
                chunk_embedding = self.chunk_embeddings[chunk.chunk_id]
                
                # Calculate cosine similarity
                similarity = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    chunk_embedding.reshape(1, -1)
                )[0][0]
                
                similarities.append((chunk, similarity))
                
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x[1], reverse=True)
        top_results = similarities[:top_k]
        
        # Log top 3 matches for debugging/verification using structured logging
        matches_log = []
        for i, (chunk, score) in enumerate(top_results[:3]):
            content_preview = chunk.content.replace('\n', ' ')[:60] + "..."
            matches_log.append({
                "rank": i + 1,
                "score": round(score, 3),
                "content_preview": content_preview,
                "service_type": chunk.service_type,
                "source_file": chunk.source_file
            })
        
        logger.debug(json.dumps({
            "operation": "similarity_search",
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "filter": {
                "hmo": user_hmo or "any",
                "tier": user_tier or "any"
            },
            "total_chunks_searched": len(relevant_chunks),
            "top_matches": matches_log
        }))
        
        return top_results
        
    def get_context_for_query(self, query: str, user_hmo: str = None, user_tier: str = None, max_context_length: int = 2000) -> Tuple[str, List[str]]:
        """Get relevant context for a query, respecting token limits"""
        
        # Search for relevant chunks
        similar_chunks = self.search_similar(query, user_hmo, user_tier, top_k=10)
        
        # Build context string within token limit
        context_parts = []
        sources = []
        current_length = 0
        
        for chunk, similarity in similar_chunks:
            chunk_text = f"מקור: {chunk.service_type}\n{chunk.content}\n"
            chunk_length = len(chunk_text.split())  # Rough token estimation
            
            if current_length + chunk_length <= max_context_length:
                context_parts.append(chunk_text)
                if chunk.source_file not in sources:
                    sources.append(chunk.source_file)
                current_length += chunk_length
            else:
                break
                
        context = "\n---\n".join(context_parts)
        return context, sources
        
    def get_stats(self) -> Dict:
        """Get statistics about the embeddings service"""
        return {
            "total_chunks": len(self.chunks),
            "embeddings_generated": len(self.chunk_embeddings),
            "kb_summary": self.kb_service.get_summary()
        }
        
# Global instance
embeddings_service = None

def get_embeddings_service() -> EmbeddingsService:
    """Get or create global embeddings service instance"""
    global embeddings_service
    if embeddings_service is None:
        embeddings_service = EmbeddingsService()
        embeddings_service.initialize_knowledge_base()
    return embeddings_service

# Allow running as a module for quick verification
if __name__ == "__main__":
    svc = get_embeddings_service()
    stats = svc.get_stats()
    print({
        "chunks": stats.get("total_chunks", 0),
        "embeddings": stats.get("embeddings_generated", 0)
    })
