"""
Named Entity Recognition (NER) module for extracting entities from video transcripts.
Uses spaCy with downloadable models for local processing.
"""

import spacy
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Global variable to store loaded model
nlp_model = None

# Common false positives to ignore
IGNORE_LIST = {
    'youtube', 'video', 'channel', 'subscribe', 'like', 'comment', 'guys', 'hey', 'hello', 
    'today', 'tomorrow', 'yesterday', 'now', 'then', 'here', 'there', 'this', 'that',
    'one', 'two', 'three', 'first', 'second', 'third', 'example', 'thing', 'way', 'lot',
    'bit', 'kind', 'sort', 'part', 'side', 'top', 'bottom', 'left', 'right', 'front', 'back',
    'poll', 'percentage', 'number', 'point', 'points'
}

# Known entities to force-correct (spaCy small model often mistakes these)
ENTITY_CORRECTIONS = {
    'obama': 'PERSON',
    'barack obama': 'PERSON',
    'biden': 'PERSON',
    'joe biden': 'PERSON',
    'trump': 'PERSON',
    'donald trump': 'PERSON',
    'clinton': 'PERSON',
    'hillary clinton': 'PERSON',
    'bush': 'PERSON',
    'george bush': 'PERSON',
    'america': 'GPE',
    'usa': 'GPE',
    'us': 'GPE',
    'united states': 'GPE',
    'white house': 'ORG',
    'congress': 'ORG',
    'senate': 'ORG'
}

def load_ner_model():
    """Load spaCy NER model. Downloads if not available."""
    global nlp_model
    
    if nlp_model is not None:
        return nlp_model
    
    try:
        # Try to load the English model
        nlp_model = spacy.load("en_core_web_sm")
        print("Loaded spaCy model: en_core_web_sm")
    except OSError:
        print("Model 'en_core_web_sm' not found. Please download it using:")
        print("python -m spacy download en_core_web_sm")
        raise Exception("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    
    return nlp_model

def extract_entities(transcript: str) -> Dict[str, List[Dict[str, Any]]]:
    """
    Extract named entities from transcript.
    Returns entities grouped by type.
    """
    nlp = load_ner_model()
    # Increase max length for large transcripts
    nlp.max_length = 2000000 
    doc = nlp(transcript)
    
    entities = {
        'PERSON': [],
        'ORG': [],
        'GPE': [],  # Geopolitical entities (countries, cities, states)
        'LOC': [],  # Non-geopolitical locations
        'DATE': [],
        'TIME': [],
        'MONEY': [],
        'PERCENT': [],
        'EVENT': [],
        'PRODUCT': [],
        'LAW': [],
        'LANGUAGE': [],
        'NORP': []  # Nationalities or religious or political groups
    }
    
    # First pass: Count frequencies to filter noise
    entity_counts = Counter()
    for ent in doc.ents:
        clean_text = ent.text.strip().lower()
        if len(clean_text) > 2 and clean_text not in IGNORE_LIST:
            entity_counts[clean_text] += 1
            
    seen_entities = set()
    
    for ent in doc.ents:
        entity_text = ent.text.strip()
        clean_text = entity_text.lower()
        
        # Filter noise
        if len(clean_text) <= 2 or clean_text in IGNORE_LIST:
            continue
            
        # For common types, require frequency > 1 unless it's a short transcript
        if len(transcript) > 5000 and ent.label_ not in ['GPE', 'LOC', 'DATE', 'TIME', 'MONEY']:
             if entity_counts[clean_text] < 2:
                 continue

        # CORRECT MISCLASSIFICATIONS
        label = ent.label_
        if clean_text in ENTITY_CORRECTIONS:
            label = ENTITY_CORRECTIONS[clean_text]

        entity_key = f"{label}:{clean_text}"
        
        # Avoid duplicates
        if entity_key in seen_entities:
            continue
        seen_entities.add(entity_key)
        
        entity_info = {
            'text': entity_text,
            'label': label,
            'start': ent.start_char,
            'end': ent.end_char,
            'description': spacy.explain(label) or label,
            'count': entity_counts[clean_text]
        }
        
        # Map spaCy labels to our categories
        if label in entities:
             entities[label].append(entity_info)
        elif label == 'ORGANIZATION': # Handle alias
             entities['ORG'].append(entity_info)
    
    # Sort by frequency
    for key in entities:
        entities[key].sort(key=lambda x: x['count'], reverse=True)

    # Remove empty categories
    return {k: v for k, v in entities.items() if v}

def extract_timeline(transcript: str) -> List[Dict[str, Any]]:
    """
    Extract timeline of events and dates from transcript.
    """
    nlp = load_ner_model()
    doc = nlp(transcript)
    
    timeline = []
    seen_dates = set()
    
    # Extract dates and their context
    for ent in doc.ents:
        if ent.label_ == 'DATE':
            date_text = ent.text.strip()
            if date_text.lower() in seen_dates or date_text.lower() in IGNORE_LIST:
                continue
            seen_dates.add(date_text.lower())
            
            # Get surrounding context (sentence)
            sentence = ent.sent.text.strip()
            
            timeline_item = {
                'date': date_text,
                'context': sentence,
                'position': ent.start_char
            }
            timeline.append(timeline_item)
    
    # Sort by position in transcript
    timeline.sort(key=lambda x: x['position'])
    
    return timeline

def extract_key_facts(transcript: str, entities: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    """
    Extract key facts from transcript using entities and patterns.
    """
    
    facts = {
        'people_mentioned': len(entities.get('PERSON', [])),
        'organizations': len(entities.get('ORG', [])),
        'locations': len(entities.get('GPE', [])) + len(entities.get('LOC', [])),
        'dates_mentioned': len(entities.get('DATE', [])),
        'top_people': [],
        'top_organizations': [],
        'top_locations': []
    }
    
    # Get most mentioned people (already sorted by count)
    facts['top_people'] = [{'name': e['text'], 'mentions': e['count']} 
                          for e in entities.get('PERSON', [])[:5]]
    
    # Get most mentioned organizations
    facts['top_organizations'] = [{'name': e['text'], 'mentions': e['count']} 
                                 for e in entities.get('ORG', [])[:5]]
    
    # Get most mentioned locations
    locs = entities.get('GPE', []) + entities.get('LOC', [])
    locs.sort(key=lambda x: x['count'], reverse=True)
    facts['top_locations'] = [{'name': e['text'], 'mentions': e['count']} 
                             for e in locs[:5]]
    
    # Extract numbers and statistics
    numbers = re.findall(r'\b\d+(?:,\d{3})*(?:\.\d+)?\b', transcript)
    facts['numbers_mentioned'] = len(numbers)
    
    # Extract questions (sentences ending with ?)
    questions = [s.strip() for s in transcript.split('.') if '?' in s]
    facts['questions_asked'] = len(questions)
    
    return facts

def extract_relationships(transcript: str, entities: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    """
    Extract relationships between entities (basic co-occurrence analysis).
    """
    nlp = load_ner_model()
    doc = nlp(transcript)
    
    relationships = []
    people = [e['text'] for e in entities.get('PERSON', [])]
    orgs = [e['text'] for e in entities.get('ORG', [])]
    locations = [e['text'] for e in entities.get('GPE', []) + entities.get('LOC', [])]
    
    # Helper to check if relationship is valid
    def is_valid_relationship(e1, e2):
        s1 = e1.lower()
        s2 = e2.lower()
        # Prevent self-loops
        if s1 == s2: return False
        # Prevent substring matches (e.g. "Trump" -> "Donald Trump")
        if s1 in s2 or s2 in s1: return False
        return True

    # Find co-occurrences in sentences
    for sent in doc.sents:
        sent_text = sent.text
        sent_people = [p for p in people if p in sent_text]
        sent_orgs = [o for o in orgs if o in sent_text]
        sent_locations = [l for l in locations if l in sent_text]
        
        # Person-Organization relationships
        for person in sent_people:
            for org in sent_orgs:
                if is_valid_relationship(person, org):
                    relationships.append({
                        'type': 'PERSON-ORG',
                        'entity1': person,
                        'entity2': org,
                        'context': sent_text[:200]
                    })
        
        # Person-Location relationships
        for person in sent_people:
            for loc in sent_locations:
                if is_valid_relationship(person, loc):
                    relationships.append({
                        'type': 'PERSON-LOC',
                        'entity1': person,
                        'entity2': loc,
                        'context': sent_text[:200]
                    })
        
        # Organization-Location relationships
        for org in sent_orgs:
            for loc in sent_locations:
                if is_valid_relationship(org, loc):
                    relationships.append({
                        'type': 'ORG-LOC',
                        'entity1': org,
                        'entity2': loc,
                        'context': sent_text[:200]
                    })
    
    # Remove duplicates
    seen = set()
    unique_relationships = []
    for rel in relationships:
        key = (rel['type'], rel['entity1'], rel['entity2'])
        if key not in seen:
            seen.add(key)
            unique_relationships.append(rel)
    
    return unique_relationships[:20]  # Limit to top 20

def process_transcript(transcript: str) -> Dict[str, Any]:
    """
    Main function to process transcript and extract all NER information.
    """
    try:
        entities = extract_entities(transcript)
        timeline = extract_timeline(transcript)
        facts = extract_key_facts(transcript, entities)
        relationships = extract_relationships(transcript, entities)
        
        return {
            'entities': entities,
            'timeline': timeline,
            'key_facts': facts,
            'relationships': relationships,
            'success': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
