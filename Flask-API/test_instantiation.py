from youtube_transcript_api import YouTubeTranscriptApi

print("Trying to instantiate...")
try:
    api = YouTubeTranscriptApi()
    print("Instantiated successfully.")
    
    print("Calling api.list('CqIr8pX3vR4')...")
    transcript_list = api.list('CqIr8pX3vR4')
    print(f"List result type: {type(transcript_list)}")
    
    # Try to find transcript in the list
    try:
        t = transcript_list.find_transcript(['en'])
        print("Found English transcript.")
        print(t.fetch()[:2])
    except:
        print("Could not find English transcript.")
        # Try first one
        try:
            first = next(iter(transcript_list))
            print(f"First transcript: {first}")
            print(first.fetch()[:2])
        except:
            print("List is empty.")

except Exception as e:
    print(f"Error with instance: {e}")

print("\nTrying static list call again with explicit args?")
# Maybe it's not static?
