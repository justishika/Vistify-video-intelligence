import sys
import os
import traceback
import json

print("--- DIAGNOSTIC START ---")

# 1. Check Imports
print("Checking imports...")
try:
    import numpy
    print(f"NumPy version: {numpy.__version__}")
except ImportError:
    print("CRITICAL: NumPy not found!")

try:
    import sklearn
    from sklearn.feature_extraction.text import TfidfVectorizer
    print(f"Scikit-learn version: {sklearn.__version__}")
except ImportError:
    print("CRITICAL: Scikit-learn not found!")

try:
    import faiss
    print(f"FAISS version: {faiss.__version__}")
except ImportError:
    print("WARNING: FAISS not found (this is okay if fallback works)")

try:
    import google.generativeai as genai
    print(f"GenAI version: {genai.__version__}")
except ImportError:
    print("CRITICAL: Google GenAI not found!")

# 2. Setup Flask Test Client
print("\nSetting up Flask Test Client...")
try:
    from app import app, transcript_cache
    
    # Mock transcript to avoid YouTube API calls
    video_id = "test_vid_123"
    mock_transcript = [
        {'text': "The tech together mentality is about collaboration.", 'start': 0.0, 'duration': 5.0},
        {'text': "It means working together to solve problems.", 'start': 5.0, 'duration': 5.0},
        {'text': "This approach fosters innovation.", 'start': 10.0, 'duration': 5.0}
    ]
    transcript_cache[video_id] = mock_transcript
    print("Mock transcript injected.")

    client = app.test_client()

    # 3. Simulate Request (Test Fallback)
    print("\nSimulating /ask request with FORCED API FAILURE...")
    
    # Monkeypatch to force error
    import langchain_google_genai
    original_embeddings = langchain_google_genai.GoogleGenerativeAIEmbeddings
    
    class BrokenEmbeddings:
        def __init__(self, **kwargs):
            pass
        def embed_documents(self, texts):
            raise Exception("Forced Quota Error")
        def embed_query(self, text):
            raise Exception("Forced Quota Error")
            
    langchain_google_genai.GoogleGenerativeAIEmbeddings = BrokenEmbeddings
    print("Monkeypatched GoogleGenerativeAIEmbeddings to fail.")

    payload = {
        "video_id": video_id,
        "question": "What's 'tech together mentality'?",
        "history": []
    }
    
    # Clear cache to force recreation
    from rag_manager import vector_store_cache
    vector_store_cache.clear()
    
    response = client.post('/ask', json=payload)
    
    print(f"\nResponse Status: {response.status_code}")
    print(f"Response Data: {response.get_data(as_text=True)}")
    
    # Restore
    langchain_google_genai.GoogleGenerativeAIEmbeddings = original_embeddings
    
    data = response.get_json()
    if data and data.get('error'):
        print(f"\nERROR DETECTED IN RESPONSE: {data.get('data')}")
    else:
        print("\nSUCCESS: Request handled correctly.")

except Exception as e:
    print(f"\nCRITICAL EXCEPTION DURING TEST: {e}")
    traceback.print_exc()

print("--- DIAGNOSTIC END ---")
