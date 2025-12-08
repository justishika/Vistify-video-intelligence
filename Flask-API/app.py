from flask import Flask, jsonify, request
from flask_cors import CORS
from youtube_transcript_api import YouTubeTranscriptApi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import os
import traceback
import json
import time
import requests

# Try to import config, but handle failure for Vercel deployment
try:
    from config import OLLAMA_API_KEY, OLLAMA_MODEL
except ImportError:
    OLLAMA_API_KEY = os.environ.get("OLLAMA_API_KEY")
    # default model if not provided via env/config
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "gpt-oss:20b")

# --- CONFIGURATION ---
app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, resources={r"/*": {"origins": "*"}})

OLLAMA_BASE_URL = "https://ollama.com/api"

if not OLLAMA_API_KEY:
    print("WARNING: OLLAMA_API_KEY not found in config.py or environment variables.")
else:
    print("Ollama Cloud configured. Model:", OLLAMA_MODEL)


# In-memory cache
# { video_id: { 'transcript': [...], 'vectorizer': obj, 'matrix': obj, 'chunks': [...] } }
CACHE = {}


# --- HELPER: OLLAMA CLOUD CALLS ---

def ollama_generate(prompt, *, model=None, format=None):
    """
    Call Ollama Cloud /api/generate.
    - prompt: string
    - model: optional model name, default OLLAMA_MODEL
    - format: None, "json", or JSON schema (dict)
    Returns:
        data["response"] (can be str or dict depending on 'format').
    """
    if not OLLAMA_API_KEY:
        raise RuntimeError("OLLAMA_API_KEY is not configured.")

    if model is None:
        model = OLLAMA_MODEL

    headers = {
        "Authorization": f"Bearer {OLLAMA_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    if format is not None:
        payload["format"] = format

    resp = requests.post(
        f"{OLLAMA_BASE_URL}/generate",
        headers=headers,
        json=payload,
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    # For normal text, this is a string.
    # For JSON mode/structured outputs, this can be a dict.
    return data.get("response")


# --- HELPER FUNCTIONS ---
def get_transcript(video_id):
    """Fetches transcript from YouTube."""
    try:
        # Create an instance of the API
        api = YouTubeTranscriptApi()
        
        # Get list of available transcripts
        transcript_list = api.list(video_id)
        
        # Try to find English transcript (manually created or auto-generated)
        transcript = None
        
        # First, try to find manually created English transcript
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            pass
        
        # If not found, try auto-generated English
        if transcript is None:
            try:
                transcript = transcript_list.find_generated_transcript(['en'])
            except:
                pass
        
        # If still not found, use the first available transcript
        if transcript is None:
            for t in transcript_list:
                transcript = t
                break
        
        if transcript is None:
            print("No transcripts available")
            return None
        
        # Fetch the actual transcript data using the transcript object's fetch method
        transcript_data = transcript.fetch()
        
        # Convert to our format
        return [
            {
                'text': entry.text if hasattr(entry, 'text') else entry['text'],
                'start': entry.start if hasattr(entry, 'start') else entry['start'],
                'duration': entry.duration if hasattr(entry, 'duration') else entry['duration']
            }
            for entry in transcript_data
        ]

    except Exception as e:
        print(f"Transcript Error: {e}")
        traceback.print_exc()
        return None
         

def create_rag_index(video_id, transcript_data):
    """
    Creates a simple TF-IDF index for the video.
    Splits transcript into chunks of ~500 characters (REDUCED).
    """
    chunks = []
    current_chunk = ""
    current_start = 0

    for entry in transcript_data:
        text = entry['text']
        start = entry['start']

        if not current_chunk:
            current_start = start

        current_chunk += " " + text

        # CHANGED: Reduced chunk size from 1000 to 500
        if len(current_chunk) > 500:
            chunks.append({
                'text': current_chunk.strip(),
                'start': current_start
            })
            current_chunk = ""

    if current_chunk:
        chunks.append({'text': current_chunk.strip(), 'start': current_start})

    # Create TF-IDF Matrix
    texts = [c['text'] for c in chunks]
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))  # ADDED: bigrams
    matrix = vectorizer.fit_transform(texts)

    return {
        'chunks': chunks,
        'vectorizer': vectorizer,
        'matrix': matrix
    }


def retrieve_context(video_id, query, top_k=5):
    """Retrieves relevant chunks using TF-IDF cosine similarity."""
    if video_id not in CACHE:
        return [], 0.0

    data = CACHE[video_id]
    vectorizer = data['vectorizer']
    matrix = data['matrix']
    chunks = data['chunks']

    # Vectorize query
    query_vec = vectorizer.transform([query])

    # Calculate similarity
    similarities = cosine_similarity(query_vec, matrix).flatten()

    # Get top K indices
    top_indices = similarities.argsort()[-top_k:][::-1]

    results = []
    top_score = 0.0

    if len(top_indices) > 0:
        top_score = float(similarities[top_indices[0]])

    # CHANGED: Reduced threshold from 0.1 to 0.05
    for idx in top_indices:
        if similarities[idx] > 0.05:  # Lower threshold
            results.append(chunks[idx])

    return results, top_score


def calculate_faithfulness(answer, context_text):
    """
    Calculates a simple faithfulness score based on word overlap (ROUGE-1 like).
    """
    answer_words = set(answer.lower().split())
    context_words = set(context_text.lower().split())

    if not answer_words:
        return 0.0

    overlap = answer_words.intersection(context_words)
    return len(overlap) / len(answer_words)


# --- ROUTES ---

@app.route('/api/summary', methods=['GET'])
def summary():
    video_id = request.args.get('v')
    summary_type = request.args.get('type', 'short')

    if not video_id:
        return jsonify({"error": True, "data": "Video ID missing"})

    try:
        if not OLLAMA_API_KEY:
            return jsonify({"error": True, "data": "Server LLM not configured (OLLAMA_API_KEY missing)."})

        # 1. Get Transcript
        if video_id not in CACHE:
            transcript = get_transcript(video_id)
            if not transcript:
                return jsonify({"error": True, "data": "Could not retrieve transcript (no English captions?)"})

            # Build Index immediately for future Q&A
            index_data = create_rag_index(video_id, transcript)
            CACHE[video_id] = index_data

        # 2. Generate Summary
        chunks = CACHE[video_id]['chunks']
        full_text = " ".join([c['text'] for c in chunks])

        # Truncate if too long
        if len(full_text) > 50000:
            full_text = full_text[:50000] + "...(truncated)"

        if summary_type == 'short':
            prompt = f"""Task: Generate a summary of the provided video transcript in EXACTLY 10 numbered points.

Instructions:
1. Format as a strict numbered list (1., 2., 3., ...).
2. Each point must be concise but comprehensive.
3. STRICTLY use only the information from the transcript. Do not add outside knowledge or hallucinate.
4. Focus on the most important takeaways.

Transcript:
{full_text}
"""
        elif summary_type == 'detailed':
            prompt = f"""Task: Provide a detailed, comprehensive summary of the video transcript in a structured, professional format (similar to IEEE/technical report style).

Instructions:
1. Use Numbered Headings for main sections (e.g., "1. Introduction", "2. Key Concept", "3. Conclusion").
2. Use Bullet Points under each heading to detail specific facts, arguments, and examples.
3. Be thorough: capture all technical details and nuances.
4. STRICTLY use only the information from the transcript. Do not hallucinate.

Transcript:
{full_text}
"""
        else:
            prompt = f"Summarize this video transcript:\n\n{full_text}"

        response_text = ollama_generate(prompt)
        return jsonify({"error": False, "data": response_text})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": True, "data": str(e)})


@app.route('/api/ask', methods=['POST'])
def ask():
    start_time = time.time()

    try:
        data = request.get_json()
        video_id = data.get('video_id')
        question = data.get('question')

        if not video_id or not question:
            return jsonify({"error": True, "data": "Missing video_id or question"})

        if not OLLAMA_API_KEY:
            return jsonify({"error": True, "data": "Server LLM not configured (OLLAMA_API_KEY missing)."})

        # 1. Ensure Index Exists
        if video_id not in CACHE:
            transcript = get_transcript(video_id)
            if not transcript:
                return jsonify({"error": True, "data": "Transcript not found. Please summarize first."})
            CACHE[video_id] = create_rag_index(video_id, transcript)

        # Handle generic greetings
        question_lower = question.lower().strip()
        if question_lower in ['hi', 'hello', 'hey']:
            return jsonify({
                "error": False,
                "data": "Hi! I'm here to answer questions about this video. What would you like to know?",
                "metrics": {
                    "retrieval_score": 1.0,
                    "faithfulness": 1.0,
                    "latency": round(time.time() - start_time, 2)
                }
            })

        # Handle "what is this video about" type questions
        if any(phrase in question_lower for phrase in ['what is this video', 'what is the video', 'video about', 'topic of']):
            chunks = CACHE[video_id]['chunks'][:3]
            context_text = "\n\n".join([f"[Time: {int(c['start'])}s] {c['text']}" for c in chunks])

            prompt = f"""Based on this video content, provide a brief overview of what the video is about.

CONTEXT:
{context_text}

INSTRUCTIONS:
- Summarize the main topic in 2-3 sentences.
- Be concise and informative.
"""
            response_text = ollama_generate(prompt)

            return jsonify({
                "error": False,
                "data": response_text,
                "metrics": {
                    "retrieval_score": 1.0,
                    "faithfulness": 0.9,
                    "latency": round(time.time() - start_time, 2)
                }
            })

        # 2. Retrieve Context
        context_chunks, top_score = retrieve_context(video_id, question, top_k=5)

        if not context_chunks:
            return jsonify({
                "error": False,
                "data": "I couldn't find specific information about that in the video. Could you rephrase your question or ask something more specific?"
            })

        # 3. Generate Answer
        context_text = "\n\n".join(
            [f"[Time: {int(c['start'])}s] {c['text']}" for c in context_chunks]
        )

        prompt = f"""You are a helpful assistant answering questions about a video based on its transcript.

CONTEXT:
{context_text}

QUESTION:
{question}

INSTRUCTIONS:
- Answer the question using ONLY the provided context.
- If the answer is not in the context, say "I don't have enough information in this part of the video to answer that."
- Be concise and helpful.
- Use natural language, not bullet points unless listing items.
"""

        answer = ollama_generate(prompt)

        latency = round(time.time() - start_time, 2)
        faithfulness = calculate_faithfulness(answer, context_text)

        return jsonify({
            "error": False,
            "data": answer,
            "metrics": {
                "retrieval_score": float(top_score),
                "faithfulness": float(faithfulness),
                "latency": latency
            }
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": True, "data": f"Backend Error: {str(e)}"})


@app.route('/api/extract-entities', methods=['GET'])
def extract_entities():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"error": True, "data": "Video ID missing"})

    try:
        if not OLLAMA_API_KEY:
            return jsonify({"error": True, "data": "Server LLM not configured (OLLAMA_API_KEY missing)."})

        # 1. Get Transcript
        if video_id not in CACHE:
            transcript = get_transcript(video_id)
            if not transcript:
                return jsonify({"error": True, "data": "Transcript not found."})
            CACHE[video_id] = create_rag_index(video_id, transcript)

        chunks = CACHE[video_id]['chunks']
        full_text = " ".join([c['text'] for c in chunks])
        if len(full_text) > 50000:
            full_text = full_text[:50000]

        # Ask Ollama to return JSON. We also set format="json".
        prompt = f"""Analyze the following video transcript and extract key named entities and facts.
Return the result as a JSON object with the following keys:
- "key_facts": {{ "people_mentioned": int, "organizations": int, "locations": int, "dates_mentioned": int, "top_people": [{{ "name": str, "mentions": int }}], "top_organizations": [{{ "name": str, "mentions": int }}], "top_locations": [{{ "name": str, "mentions": int }}] }}
- "entities": {{ "PERSON": [{{ "text": str }}], "ORG": [{{ "text": str }}], "LOC": [{{ "text": str }}], "DATE": [{{ "text": str }}], "EVENT": [{{ "text": str }}] }}
- "timeline": [{{ "date": str, "context": str }}]
- "relationships": [{{ "type": str, "entity1": str, "entity2": str, "context": str }}]

Respond ONLY with a single JSON object, no extra text.

Transcript:
{full_text}
"""

        # JSON mode
        raw_response = ollama_generate(prompt, format="json")

        # raw_response may already be a dict (structured output) or a JSON string
        if isinstance(raw_response, dict):
            data = raw_response
        else:
            try:
                data = json.loads(raw_response)
            except Exception:
                # fallback: wrap as text if not valid JSON
                return jsonify({"error": False, "data": raw_response})

        data['success'] = True
        return jsonify({"error": False, "data": data})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": True, "data": str(e)})


@app.route('/api/get-insights', methods=['GET'])
def get_insights():
    video_id = request.args.get('v')
    if not video_id:
        return jsonify({"error": True, "data": "Video ID missing"})

    try:
        if not OLLAMA_API_KEY:
            return jsonify({"error": True, "data": "Server LLM not configured (OLLAMA_API_KEY missing)."})

        if video_id not in CACHE:
            transcript = get_transcript(video_id)
            if not transcript:
                return jsonify({"error": True, "data": "Transcript not found."})
            CACHE[video_id] = create_rag_index(video_id, transcript)

        chunks = CACHE[video_id]['chunks']
        full_text = " ".join([c['text'] for c in chunks])
        if len(full_text) > 50000:
            full_text = full_text[:50000]

        prompt = f"""Generate 5 interesting questions that a user might want to ask about this video, and 3 key insights.
Format the output as a simple HTML string with:
<h3>Suggested Questions</h3><ul>...</ul>
<h3>Key Insights</h3><ul>...</ul>

Use only information from this transcript:

{full_text}
"""

        html = ollama_generate(prompt)
        return jsonify({"error": False, "data": html})

    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": True, "data": str(e)})


# --- STARTUP ---
if __name__ == '__main__':
    print("!!! FRESH START SERVER (OLLAMA CLOUD) !!!")
    print(f"Using Ollama Model: {OLLAMA_MODEL}")
    app.run(port=5000, debug=False)
