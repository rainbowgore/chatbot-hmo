import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.services.knowledge_base import KnowledgeBaseService
from app.services.embeddings import EmbeddingsService

def test_knowledge_base():
    print("Testing Knowledge Base Service...")
    
    # Initialize service
    kb_service = KnowledgeBaseService()
    
    # Load knowledge base
    try:
        kb_service.load_knowledge_base()
        print(f"✅ Successfully loaded {len(kb_service.chunks)} chunks")
        
        # Show summary
        summary = kb_service.get_summary()
        print("\n📊 Knowledge Base Summary:")
        print(f"Total chunks: {summary['total_chunks']}")
        print("\nBy service type:")
        for service, count in summary['by_service'].items():
            print(f"  - {service}: {count} chunks")
            
        print("\nBy HMO:")
        for hmo, count in summary['by_hmo'].items():
            print(f"  - {hmo}: {count} chunks")
            
        # Test user filtering
        print("\n🔍 Testing user filtering...")
        maccabi_gold_chunks = kb_service.get_chunks_for_user("מכבי", "זהב")
        print(f"Maccabi Gold relevant chunks: {len(maccabi_gold_chunks)}")
        
        # Show a sample chunk
        if kb_service.chunks:
            sample_chunk = kb_service.chunks[0]
            print(f"\n📄 Sample chunk:")
            print(f"Service: {sample_chunk.service_type}")
            print(f"Source: {sample_chunk.source_file}")
            print(f"HMOs: {sample_chunk.hmos}")
            print(f"Tiers: {sample_chunk.tiers}")
            print(f"Content preview: {sample_chunk.content[:200]}...")
            
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_embeddings_search(query):
    print(f"\n🔍 Testing Embeddings Search for: '{query}'")
    print("="*60)
    
    try:
        # Initialize embeddings service (this will load KB and generate embeddings)
        embeddings_service = EmbeddingsService()
        embeddings_service.initialize_knowledge_base()
        
        print(f"\n✅ Embeddings service initialized with {len(embeddings_service.chunks)} chunks")
        
        # Test search without profile filtering
        print(f"\n🔎 Searching without profile filter...")
        results = embeddings_service.search_similar(query, top_k=5)
        
        # Test search with HMO filtering
        print(f"\n🔎 Searching with Maccabi Gold filter...")
        maccabi_results = embeddings_service.search_similar(query, user_hmo="מכבי", user_tier="זהב", top_k=5)
        
        # Test search with different HMO
        print(f"\n🔎 Searching with Clalit Silver filter...")
        clalit_results = embeddings_service.search_similar(query, user_hmo="כללית", user_tier="כסף", top_k=5)
        
        print(f"\n✅ Search completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Embeddings search error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check if query argument provided
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        success = test_embeddings_search(query)
    else:
        # Run basic KB test
        success = test_knowledge_base()
        
        # Also run a sample embeddings test
        print("\n" + "="*60)
        print("Running sample embeddings search...")
        success = success and test_embeddings_search("pregnancy services")
        
    sys.exit(0 if success else 1)
