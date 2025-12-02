from youtube_transcript_api import YouTubeTranscriptApi
import traceback

video_id = "CqIr8pX3vR4"

print(f"Testing transcript fetch for video: {video_id}")

try:
    print("Attempting YouTubeTranscriptApi.get_transcript(video_id)...")
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    print("SUCCESS: Fetched transcript directly.")
    print(f"First 5 lines: {transcript[:5]}")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

print("\nAttempting list_transcripts...")
try:
    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
    print("Available transcripts:")
    for t in transcript_list:
        print(f" - Language: {t.language}, Code: {t.language_code}, Generated: {t.is_generated}")
        
    print("\nAttempting to find 'en'...")
    try:
        t = transcript_list.find_transcript(['en'])
        print(f"Found 'en': {t}")
        print(t.fetch()[:2])
    except:
        print("Could not find 'en' manually.")
        
    print("\nAttempting to find generated 'en'...")
    try:
        t = transcript_list.find_generated_transcript(['en'])
        print(f"Found generated 'en': {t}")
        print(t.fetch()[:2])
    except:
        print("Could not find generated 'en'.")

except Exception as e:
    print(f"FAILED list_transcripts: {e}")
    traceback.print_exc()
