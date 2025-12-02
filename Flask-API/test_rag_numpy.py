import sys
import os
import traceback

print("Testing RAG (NumPy) imports...")
try:
    import numpy as np
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain.docstore.document import Document
    print("Imports successful!")
except Exception as e:
    print("Import failed!")
    traceback.print_exc()
    sys.exit(1)

print("\nTesting Vector DB creation...")
try:
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        print("GEMINI_API_KEY not found in config.py")
        sys.exit(1)
        
    # Use the same model as in rag_manager.py
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GEMINI_API_KEY)
    
    docs = [Document(page_content="This is a test sentence about approval ratings.", metadata={"id": 1})]
    
    print("Generating embeddings...")
    texts = [d.page_content for d in docs]
    embeddings = embeddings_model.embed_documents(texts)
    vector_array = np.array(embeddings)
    print(f"Embeddings generated. Shape: {vector_array.shape}")
    
    print("Testing retrieval...")
    query = "approval ratings"
    query_embedding = embeddings_model.embed_query(query)
    query_vector = np.array(query_embedding)
    
    # Cosine Similarity
    norm_vectors = np.linalg.norm(vector_array, axis=1)
    norm_query = np.linalg.norm(query_vector)
    similarities = np.dot(vector_array, query_vector) / (norm_vectors * norm_query)
    
    print(f"Similarity score: {similarities[0]}")
    
    if similarities[0] > 0.5:
        print("RAG Test PASSED!")
    else:
        print("RAG Test FAILED (Low similarity)")
    
except Exception as e:
    print("RAG functionality test failed!")
    traceback.print_exc()
