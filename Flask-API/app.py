from flask import Flask, jsonify, request, session
import google.generativeai as genai
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, InvalidVideoId
from config import GEMINI_API_KEY
from flask_cors import CORS
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)  # For session management
CORS(app, supports_credentials=True)

# Store transcripts temporarily (in production, use Redis or database)
transcript_cache = {}

@app.route('/summary', methods=['GET'])
def youtube_summarizer():
    video_id = request.args.get('v')
    summary_type = request.args.get('type', 'short')
    
    try:
        transcript = get_transcript(video_id)
        # Cache the transcript for Q&A feature
        transcript_cache[video_id] = transcript
        
        summary = gemini_summarize(transcript, summary_type)
    except NoTranscriptFound:
        return jsonify({"data": "No English Subtitles found", "error": True})
    except InvalidVideoId:
        return jsonify({"data": "Invalid Video Id", "error": True})
    except Exception as e:
        print(e)
        return jsonify({"data": "Unable to Summarize the video", "error": True})
    
    return jsonify({"data": summary, "error": False})

@app.route('/ask', methods=['POST'])
def ask_question():
    """Handle Q&A about the video"""
    try:
        data = request.get_json()
        video_id = data.get('video_id')
        question = data.get('question')
        conversation_history = data.get('history', [])
        
        if not video_id or not question:
            return jsonify({"data": "Missing video_id or question", "error": True})
        
        # Get transcript from cache or fetch it
        if video_id not in transcript_cache:
            transcript = get_transcript(video_id)
            transcript_cache[video_id] = transcript
        else:
            transcript = transcript_cache[video_id]
        
        # Generate answer using Gemini
        answer = gemini_answer_question(transcript, question, conversation_history)
        
        return jsonify({"data": answer, "error": False})
    
    except Exception as e:
        print(f"Error in ask_question: {repr(e)}")
        return jsonify({"data": "Unable to answer the question", "error": True})

@app.route('/get-insights', methods=['GET'])
def get_insights():
    """Generate automatic insights about the video"""
    video_id = request.args.get('v')
    
    try:
        if video_id not in transcript_cache:
            transcript = get_transcript(video_id)
            transcript_cache[video_id] = transcript
        else:
            transcript = transcript_cache[video_id]
        
        insights = gemini_generate_insights(transcript)
        return jsonify({"data": insights, "error": False})
    
    except Exception as e:
        print(f"Error generating insights: {repr(e)}")
        return jsonify({"data": "Unable to generate insights", "error": True})

def get_transcript(video_id):
    api = YouTubeTranscriptApi()
    transcript_response = None
    last_exc = None
    
    for method in ("get_transcript", "fetch", "list"):
        if hasattr(api, method):
            func = getattr(api, method)
            try:
                if method == "list":
                    resp = func(video_id)
                    if hasattr(resp, 'fetch'):
                        transcript_response = resp.fetch()
                    else:
                        transcript_response = resp
                else:
                    transcript_response = func(video_id)
                print(f"get_transcript: used method '{method}'")
                break
            except Exception as e:
                last_exc = e
                continue
    
    if transcript_response is None:
        raise last_exc or Exception("No transcript method succeeded")
    
    texts = []
    if hasattr(transcript_response, '__iter__') and not isinstance(transcript_response, (str, bytes, dict)):
        try:
            for item in transcript_response:
                if isinstance(item, dict):
                    t = item.get('text')
                    if t:
                        texts.append(t)
                elif hasattr(item, 'text'):
                    if item.text:
                        texts.append(item.text)
                elif isinstance(item, str):
                    texts.append(item)
            if texts:
                joined = ' '.join(texts)
                print(f"get_transcript: transcript length={len(joined)}")
                return joined
        except Exception as e:
            print(f"Failed to iterate response: {repr(e)}")
    
    if hasattr(transcript_response, 'entries'):
        for entry in transcript_response.entries:
            if isinstance(entry, dict):
                t = entry.get('text')
                if t:
                    texts.append(t)
            elif hasattr(entry, 'text'):
                if entry.text:
                    texts.append(entry.text)
    elif isinstance(transcript_response, list):
        for item in transcript_response:
            if isinstance(item, dict):
                t = item.get('text') or item.get('transcript')
                if t:
                    texts.append(t)
            elif isinstance(item, str):
                texts.append(item)
            elif hasattr(item, 'text'):
                if item.text:
                    texts.append(item.text)
    elif isinstance(transcript_response, dict):
        t = transcript_response.get('text') or transcript_response.get('transcript')
        if t:
            texts.append(t)
    elif isinstance(transcript_response, str):
        texts.append(transcript_response)
    else:
        raise Exception(f"Unknown transcript response type: {type(transcript_response)!r}")
    
    joined = ' '.join(texts)
    print(f"get_transcript: transcript length={len(joined)}")
    return joined

def gemini_summarize(transcript, summary_type='short'):
    api_key = os.environ.get('GEMINI_API_KEY') or GEMINI_API_KEY
    if not api_key or not api_key.strip():
        raise Exception('Gemini API key missing; set GEMINI_API_KEY or update config.py')
    
    genai.configure(api_key=api_key)
    
    max_chars = 60000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "\n\n[Truncated transcript]"
    
    if summary_type == 'detailed':
        prompt = f"""You have to provide a detailed, in-depth summary of the following YouTube video transcript.
Break it down into key sections with headings and bullet points.
Capture all the important details, examples, and nuances.

Transcript:
{transcript}"""
    else:
        prompt = f"""You have to summarize a YouTube video using its transcript in 10 concise points.

Transcript:
{transcript}"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        print("Gemini request succeeded")
        return response.text
    except Exception as e:
        print("Gemini request failed:", repr(e))
        raise

def gemini_answer_question(transcript, question, conversation_history=[]):
    """Answer questions about the video using Gemini"""
    api_key = os.environ.get('GEMINI_API_KEY') or GEMINI_API_KEY
    genai.configure(api_key=api_key)
    
    max_chars = 60000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "\n\n[Truncated transcript]"
    
    # Build conversation context
    context = "Previous conversation:\n"
    for msg in conversation_history[-4:]:  # Keep last 4 exchanges
        context += f"Q: {msg['question']}\nA: {msg['answer']}\n\n"
    
    prompt = f"""You are an AI assistant helping users understand a YouTube video. 
Based on the video transcript below, answer the user's question accurately and concisely.
If the question cannot be answered from the transcript, politely say so.

{context if conversation_history else ''}

Video Transcript:
{transcript}

User's Question: {question}

Answer the question in a clear, helpful manner. If relevant, mention specific details or timestamps from the video."""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Gemini Q&A failed:", repr(e))
        raise

def gemini_generate_insights(transcript):
    """Generate automatic insights about the video"""
    api_key = os.environ.get('GEMINI_API_KEY') or GEMINI_API_KEY
    genai.configure(api_key=api_key)
    
    max_chars = 60000
    if len(transcript) > max_chars:
        transcript = transcript[:max_chars] + "\n\n[Truncated transcript]"
    
    prompt = f"""Analyze this YouTube video transcript and provide:
1. Main Topic (one sentence)
2. Key Takeaways (3-4 bullet points)
3. Target Audience
4. Content Type (Tutorial, Review, Educational, Entertainment, etc.)
5. Suggested Questions viewers might want to ask

Format your response clearly with these sections.

Transcript:
{transcript}"""
    
    try:
        model = genai.GenerativeModel('gemini-2.0-flash')
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print("Gemini insights failed:", repr(e))
        raise

if __name__ == '__main__':
    app.run(debug=True, port=5000)