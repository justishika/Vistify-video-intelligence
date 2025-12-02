try:
    from config import GEMINI_API_KEY
    if GEMINI_API_KEY and GEMINI_API_KEY.strip() and GEMINI_API_KEY != 'YOUR_ACTUAL_API_KEY_HERE':
        print("Config check PASSED: API Key is present.")
    else:
        print("Config check FAILED: API Key is missing or default.")
except Exception as e:
    print(f"Config check FAILED: {e}")
