"""
Text cleaning and chunking module for Promise Gap Analyser.

Cleans both promise (marketing) and delivery (review) corpora.
"""

import re
import json
from pathlib import Path
from typing import List, Dict, Tuple


def clean_text(text: str) -> str:
    """
    Aggressive text cleaning for NLP quality.
    Removes URLs, handles, special chars, normalizes whitespace.
    """
    if not text:
        return ""
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove Reddit-style handles u/username and r/subreddit
    text = re.sub(r'/?[ur]/\w+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove excessive punctuation
    text = re.sub(r'[!?.]{2,}', '!', text)
    text = re.sub(r'[,;]{2,}', ',', text)
    
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?\'-]', ' ', text)
    
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def chunk_text(text: str, min_length: int = 30, max_length: int = 500) -> List[str]:
    """
    Split text into sentence-level chunks.
    Filters out very short chunks.
    """
    # Split on sentence boundaries
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    chunks = []
    for sent in sentences:
        sent = sent.strip()
        if len(sent) >= min_length:
            # Truncate if too long
            if len(sent) > max_length:
                sent = sent[:max_length].rsplit(' ', 1)[0] + '...'
            chunks.append(sent)
    
    return chunks


def load_film_data(film_slug: str) -> Tuple[List[str], List[str]]:
    """
    Load marketing and review data for a film.
    Returns: (promise_chunks, delivery_chunks)
    """
    raw_dir = Path("data/raw")
    
    # Load marketing data
    marketing_path = raw_dir / f"{film_slug}_marketing.json"
    promise_texts = []
    
    if marketing_path.exists():
        with open(marketing_path) as f:
            mdata = json.load(f)
        
        # YouTube transcripts
        for yt in mdata.get('youtube_transcripts', []):
            text = yt.get('transcript', '')
            if text:
                promise_texts.append(('youtube', text))
        
        # Wikipedia
        wiki = mdata.get('wikipedia_marketing', '')
        if wiki:
            promise_texts.append(('wikipedia', wiki))
        
        # TMDB
        tmdb = mdata.get('tmdb_marketing', {})
        tmdb_text = tmdb.get('overview', '') + ' ' + tmdb.get('tagline', '')
        if tmdb_text.strip():
            promise_texts.append(('tmdb', tmdb_text))
    
    # Load review data
    reviews_path = raw_dir / f"{film_slug}_reviews.json"
    delivery_texts = []
    
    if reviews_path.exists():
        with open(reviews_path) as f:
            rdata = json.load(f)
        
        # Reddit
        for r in rdata.get('reddit', []):
            text = r.get('text', '')
            if text:
                delivery_texts.append(('reddit', text))
        
        # IMDB
        for r in rdata.get('imdb', []):
            text = r.get('text', '')
            if text:
                delivery_texts.append(('imdb', text))
        
        # TMDB
        for r in rdata.get('tmdb', []):
            text = r.get('text', '')
            if text:
                delivery_texts.append(('tmdb_review', text))
    
    return promise_texts, delivery_texts


def clean_film_corpus(film_slug: str) -> Dict:
    """
    Clean and chunk all text for a film.
    Returns cleaned corpus with metadata.
    """
    promise_texts, delivery_texts = load_film_data(film_slug)
    
    # Clean and chunk promise corpus
    promise_chunks = []
    for source, text in promise_texts:
        cleaned = clean_text(text)
        chunks = chunk_text(cleaned, min_length=20, max_length=400)
        for chunk in chunks:
            promise_chunks.append({
                'text': chunk,
                'source': source,
                'film': film_slug,
                'type': 'promise'
            })
    
    # Clean and chunk delivery corpus
    delivery_chunks = []
    for source, text in delivery_texts:
        cleaned = clean_text(text)
        chunks = chunk_text(cleaned, min_length=30, max_length=500)
        for chunk in chunks:
            delivery_chunks.append({
                'text': chunk,
                'source': source,
                'film': film_slug,
                'type': 'delivery'
            })
    
    return {
        'film': film_slug,
        'promise_chunks': promise_chunks,
        'delivery_chunks': delivery_chunks,
        'promise_count': len(promise_chunks),
        'delivery_count': len(delivery_chunks),
        'promise_sources': list(set(c['source'] for c in promise_chunks)),
        'delivery_sources': list(set(c['source'] for c in delivery_chunks))
    }


def clean_all_films() -> Dict[str, Dict]:
    """Clean corpus for all 7 films."""
    films = ['snow_white', 'wicked', 'minecraft', 'lilo_stitch', 
             'thunderbolts', 'joker_2', 'paddington']
    
    results = {}
    for film in films:
        print(f"  Cleaning {film}...")
        results[film] = clean_film_corpus(film)
    
    return results


if __name__ == "__main__":
    print("Cleaning all film corpora...")
    results = clean_all_films()
    
    for film, data in results.items():
        print(f"\n{film}:")
        print(f"  Promise: {data['promise_count']} chunks")
        print(f"  Delivery: {data['delivery_count']} chunks")
