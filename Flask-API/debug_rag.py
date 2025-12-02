import sys
import traceback
import os

print("Starting Debug Script...")

try:
    print("Importing config...")
    from config import GEMINI_API_KEY
    if not GEMINI_API_KEY:
        print("ERROR: GEMINI_API_KEY is missing in config.py")
    else:
        print("GEMINI_API_KEY is present.")

    print("Importing langchain components...")
    from langchain_community.vectorstores import FAISS
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    from langchain.docstore.document import Document
    print("Langchain components imported successfully.")

    print("Importing rag_manager...")
    from rag_manager import create_vector_db, get_relevant_chunks
    print("rag_manager imported successfully.")

    # Mock Data
    video_id = "debug_video_123"
    transcript_list = [
        {'text': "This is a test video about approval ratings.", 'start': 0.0, 'duration': 5.0},
        {'text': "Approval ratings can predict midterm election outcomes.", 'start': 5.0, 'duration': 5.0},
        {'text': "However, it is not a perfect science.", 'start': 10.0, 'duration': 5.0}
    ]
    question = "Can approval ratings predict midterms?"

    print("\n--- Testing create_vector_db ---")
    store = create_vector_db(video_id, transcript_list)
    if store:
        print("Vector DB created successfully.")
    else:
        print("ERROR: Failed to create Vector DB.")

    print("\n--- Testing get_relevant_chunks ---")
    docs = get_relevant_chunks(video_id, question)
    print(f"Retrieved {len(docs)} docs.")
    for d in docs:
        print(f" - {d.page_content}")

    if len(docs) > 0:
        print("\nSUCCESS: RAG pipeline is working.")
    else:
        print("\nFAILURE: No docs retrieved.")

except Exception as e:
    print(f"\nCRITICAL ERROR: {e}")
    traceback.print_exc()
