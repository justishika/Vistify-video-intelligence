import google.generativeai as genai
import os
from config import GEMINI_API_KEY

api_key = os.environ.get('GEMINI_API_KEY') or GEMINI_API_KEY
genai.configure(api_key=api_key)

print("Listing available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods or 'embedContent' in m.supported_generation_methods:
            print(f"- {m.name} ({m.supported_generation_methods})")
except Exception as e:
    print(f"Error listing models: {e}")
