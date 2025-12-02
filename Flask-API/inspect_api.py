from youtube_transcript_api import YouTubeTranscriptApi
import inspect

print("Inspecting YouTubeTranscriptApi...")
print(f"Type: {type(YouTubeTranscriptApi)}")
print(f"Dir: {dir(YouTubeTranscriptApi)}")

try:
    print("\nTrying YouTubeTranscriptApi.list('CqIr8pX3vR4')...")
    result = YouTubeTranscriptApi.list('CqIr8pX3vR4')
    print(f"Result type: {type(result)}")
    print(f"Result: {result}")
except Exception as e:
    print(f"Error calling list: {e}")

try:
    print("\nTrying YouTubeTranscriptApi.get_transcript('CqIr8pX3vR4')...")
    result = YouTubeTranscriptApi.get_transcript('CqIr8pX3vR4')
    print(f"Result type: {type(result)}")
    print(f"Result: {result[:2]}")
except Exception as e:
    print(f"Error calling get_transcript: {e}")
