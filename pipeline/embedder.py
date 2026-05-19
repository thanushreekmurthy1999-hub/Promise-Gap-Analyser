"""
Sentence embedding module using sentence-transformers.
"""

import json
import numpy as np
from pathlib import Path
from typing import List, Dict

# Lazy load model
_model = None

def get_model():
    """Lazy load the sentence transformer model."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        print("  Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer('all-MiniLM-L6-v2')
    return _model


def embed_chunks(chunks: List[Dict], batch_size: int = 32) -> List[Dict]:
    """
    Create embeddings for a list of text chunks.
    Adds 'embedding' field to each chunk dict.
    """
    if not chunks:
        return chunks
    
    model = get_model()
    texts = [c['text'] for c in chunks]
    
    print(f"    Embedding {len(texts)} chunks...")
    
    # Batch process
    embeddings = model.encode(
        texts, 
        batch_size=batch_size,
        show_progress_bar=False,
        convert_to_numpy=True
    )
    
    # Add embeddings back to chunks
    for i, chunk in enumerate(chunks):
        chunk['embedding'] = embeddings[i].tolist()
    
    return chunks


def embed_film_corpus(film_slug: str, cleaned_data: Dict) -> Dict:
    """
    Create embeddings for both promise and delivery chunks.
    """
    print(f"  Embedding {film_slug}...")
    
    # Embed promise chunks
    promise_embedded = embed_chunks(cleaned_data['promise_chunks'])
    
    # Embed delivery chunks
    delivery_embedded = embed_chunks(cleaned_data['delivery_chunks'])
    
    return {
        'film': film_slug,
        'promise': promise_embedded,
        'delivery': delivery_embedded,
        'promise_count': len(promise_embedded),
        'delivery_count': len(delivery_embedded)
    }


def embed_all_films(cleaned_data: Dict) -> Dict[str, Dict]:
    """Embed all film corpora."""
    embedded = {}
    for film, data in cleaned_data.items():
        embedded[film] = embed_film_corpus(film, data)
    return embedded


if __name__ == "__main__":
    from cleaner import clean_all_films
    
    print("Loading and cleaning corpora...")
    cleaned = clean_all_films()
    
    print("\nCreating embeddings...")
    embedded = embed_all_films(cleaned)
    
    print("\nEmbedding complete!")
    for film, data in embedded.items():
        print(f"  {film}: {data['promise_count']} promise, {data['delivery_count']} delivery embeddings")
