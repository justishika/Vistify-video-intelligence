import sys
import os
import traceback

print("Testing RAG imports...")
try:
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain_community.vectorstores import FAISS
    from langchain.docstore.document import Document
    import numpy as np
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
        
    embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key=GEMINI_API_KEY)
    
    docs = [Document(page_content="This is a test sentence.", metadata={"id": 1})]
    
    print("Creating FAISS index...")
    vector_store = FAISS.from_documents(docs, embeddings)
    print("FAISS index created successfully!")
    
    print("Testing retrieval...")
    results = vector_store.similarity_search("test", k=1)
    print(f"Retrieval successful! Found: {results[0].page_content}")
    
except Exception as e:
    print("RAG functionality test failed!")
    traceback.print_exc()
