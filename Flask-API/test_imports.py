import sys
print("Starting imports...")
try:
    import numpy as np
    print("numpy imported")
    from sklearn.feature_extraction.text import TfidfVectorizer
    print("sklearn imported")
    from sklearn.metrics.pairwise import cosine_similarity
    print("cosine_similarity imported")
except Exception as e:
    print(f"Error: {e}")
print("Done")
