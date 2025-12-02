from waitress import serve
from app import app
import os

if __name__ == "__main__":
    print("----------------------------------------------------------------")
    print("STARTING PRODUCTION SERVER (WAITRESS)")
    print("Serving on http://0.0.0.0:5000")
    print("----------------------------------------------------------------")
    serve(app, host='0.0.0.0', port=5000)
