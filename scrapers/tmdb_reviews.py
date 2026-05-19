"""TMDB reviews scraper with relevance verification."""

import os
import time
import requests
from scrapers.verify import is_relevant


def get_tmdb_reviews(film_slug: str, config: dict, max_reviews: int = 50) -> list[dict]:
    """
    Fetch user reviews from TMDB API.
    Verify each review is about the actual film before keeping it.
    
    Requires TMDB_API_KEY in environment.
    """
    api_key = os.environ.get('TMDB_API_KEY')
    if not api_key:
        print(f"  WARNING: TMDB_API_KEY not set. Skipping TMDB reviews.")
        return []
    
    imdb_id = config.get('imdb_id') or config.get('tmdb_id')
    if not imdb_id:
        print(f"  WARNING: No ID available for TMDB lookup")
        return []
    
    print(f"  Fetching TMDB reviews for: {config['title']}")
    
    try:
        # First, find the TMDB ID from IMDB ID if needed
        tmdb_id = None
        if imdb_id.startswith('tt'):
            # Lookup TMDB ID from IMDB ID
            find_url = f"https://api.themoviedb.org/3/find/{imdb_id}"
            params = {
                'api_key': api_key,
                'external_source': 'imdb_id'
            }
            r = requests.get(find_url, params=params, timeout=10)
            time.sleep(0.5)
            
            if r.status_code == 200:
                data = r.json()
                if data.get('movie_results'):
                    tmdb_id = data['movie_results'][0]['id']
                elif data.get('tv_results'):
                    tmdb_id = data['tv_results'][0]['id']
        else:
            tmdb_id = int(imdb_id)
        
        if not tmdb_id:
            print(f"  WARNING: Could not find TMDB ID for {imdb_id}")
            return []
        
        # Fetch reviews
        reviews_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/reviews"
        params = {
            'api_key': api_key,
            'language': 'en-US',
            'page': 1
        }
        
        r = requests.get(reviews_url, params=params, timeout=10)
        time.sleep(0.5)
        
        if r.status_code != 200:
            print(f"  ERROR TMDB: status {r.status_code}")
            return []
        
        data = r.json()
        raw_reviews = data.get('results', [])
        
        if not raw_reviews:
            print(f"  WARNING: No reviews found on TMDB")
            return []
        
        print(f"  Found {len(raw_reviews)} raw reviews on TMDB")
        
        kept_reviews = []
        
        for review in raw_reviews[:max_reviews]:
            author = review.get('author', 'Unknown')
            content = review.get('content', '').strip()
            rating = review.get('author_details', {}).get('rating')
            
            # Basic quality gates
            if len(content) < 40:
                continue
            
            # Relevance check
            relevant, rel_score = is_relevant(
                content,
                config['title'],
                config['year'],
                threshold=0.20
            )
            
            if not relevant:
                print(f"  DISCARD TMDB review by {author}: score={rel_score} | '{content[:50]}...'")
                continue
            
            kept_reviews.append({
                "text": content,
                "rating": rating,
                "author": author,
                "source": "tmdb",
                "relevance_score": rel_score
            })
        
        print(f"  Total TMDB reviews kept: {len(kept_reviews)}")
        return kept_reviews
        
    except Exception as e:
        print(f"  ERROR TMDB: {e}")
        return []
