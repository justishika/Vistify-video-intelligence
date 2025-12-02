import google.generativeai as genai
from config import GEMINI_API_KEY
import os

# Configure API
os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
genai.configure(api_key=GEMINI_API_KEY)

print("--- Available Embedding Models ---")
try:
    for m in genai.list_models():
        if 'embed' in m.name.lower():
            print(f"Name: {m.name}")
            print(f"Display Name: {m.display_name}")
            print(f"Input Token Limit: {m.input_token_limit}")
            print("-" * 20)
except Exception as e:
    print(f"Error listing models: {e}")
