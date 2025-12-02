import sys
import os
from rag_manager import create_vector_db, get_relevant_chunks

# Mock transcript data
# Assuming the video is about politics/midterms based on the question
transcript_list = [
    {'text': "Welcome back to the channel.", 'start': 0.0, 'duration': 5.0},
    {'text': "Today we are discussing whether approval ratings can actually predict the outcome of midterm elections.", 'start': 5.0, 'duration': 10.0},
    {'text': "Historically, low presidential approval ratings have correlated with losses for the president's party in midterms.", 'start': 15.0, 'duration': 10.0},
    {'text': "However, there are exceptions to this rule.", 'start': 25.0, 'duration': 5.0},
    {'text': "So the answer is yes, but it's not a perfect predictor.", 'start': 30.0, 'duration': 5.0}
]

video_id = "test_video_123"
question = "Can approval ratings predict midterms?"

print(f"Testing RAG with Question: '{question}'")

# 1. Create Vector DB
print("Creating Vector DB...")
store = create_vector_db(video_id, transcript_list)

if not store:
    print("Failed to create Vector DB")
    sys.exit(1)

# 2. Retrieve Chunks
print("Retrieving Chunks...")
# Using the default threshold from rag_manager (0.05)
relevant_docs = get_relevant_chunks(video_id, question)

print(f"Found {len(relevant_docs)} relevant docs.")

for i, doc in enumerate(relevant_docs):
    print(f"Doc {i+1}: {doc.page_content}")
    
if not relevant_docs:
    print("ISSUE REPRODUCED: No relevant documents found.")
else:
    print("Relevant documents found. The issue might be in the generation step or the threshold is fine for this exact match.")
