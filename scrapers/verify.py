"""Text verification using sentence embeddings or keyword fallback."""

try:
    from sentence_transformers import SentenceTransformer, util
    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    _SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("  WARNING: sentence-transformers not available, using keyword fallback for relevance")

_verifier_model = None


def load_verifier():
    """Load the MiniLM model for relevance verification (lazy singleton)."""
    global _verifier_model
    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    if _verifier_model is None:
        _verifier_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _verifier_model


def _keyword_relevance(text: str, film_title: str, year: int) -> float:
    """Simple keyword-based relevance as fallback."""
    text_lower = text.lower()
    title_parts = [p for p in film_title.lower().split() if len(p) > 3]
    
    # Build keyword list with variations
    keywords = set()
    keywords.add(str(year))
    keywords.add(film_title.lower())
    keywords.update(title_parts)
    
    # Also add key terms from title (without "the", "and", "in", etc.)
    stopwords = {'the', 'and', 'in', 'of', 'a', 'an', 'to', 'for', 'on', 'at'}
    keywords.update([p for p in title_parts if p not in stopwords])
    
    # Count matches
    matches = 0
    for kw in keywords:
        if len(kw) <= 2:
            continue
        # Check if keyword appears
        if kw in text_lower:
            matches += 1
        # Also check partial matches for compound words
        elif len(kw) > 5 and kw[:5] in text_lower:
            matches += 0.5
    
    # Calculate score - be more lenient
    score = min(matches / 2.0, 1.0)  # Need only 2 keyword matches for full score
    
    return score


def is_relevant(text: str, film_title: str, year: int,
                threshold: float = 0.25) -> tuple[bool, float]:
    """
    Check if a scraped text is actually about this specific film.
    
    Returns (is_relevant: bool, score: float)
    """
    if not text or len(text.strip()) < 30:
        return False, 0.0

    model = load_verifier()
    
    if model is None:
        # Fallback to keyword matching
        score = _keyword_relevance(text, film_title, year)
        return score >= threshold, round(score, 3)
    
    # Use sentence embeddings
    reference = (
        f"This is about the {year} film {film_title}. "
        f"It discusses the movie's story, characters, "
        f"performances, marketing, or audience reception."
    )
    
    ref_vec = model.encode(reference, convert_to_tensor=True)
    text_vec = model.encode(text[:500], convert_to_tensor=True)
    score = float(util.cos_sim(ref_vec, text_vec))
    
    return score >= threshold, round(score, 3)
