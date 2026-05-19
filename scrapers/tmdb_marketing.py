"""TMDB marketing data scraper for promise corpus."""

import os
import requests
import time


def get_tmdb_marketing(film_slug: str, config: dict) -> dict:
    """
    Fetch marketing data from TMDB (overview, tagline, title variants).
    This supplements YouTube/Wikipedia sources.
    
    Returns dict with keys: overview, tagline, title
    """
    api_key = os.environ.get('TMDB_API_KEY')
    if not api_key:
        print(f"  WARNING: TMDB_API_KEY not set. Skipping TMDB marketing.")
        return {}
    
    imdb_id = config.get('imdb_id') or config.get('tmdb_id')
    if not imdb_id:
        print(f"  WARNING: No ID available for TMDB lookup")
        return {}
    
    print(f"  Fetching TMDB marketing data for: {config['title']}")
    
    try:
        # First, find the TMDB ID from IMDB ID if needed
        tmdb_id = None
        if imdb_id.startswith('tt'):
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
            return {}
        
        # Fetch movie details
        details_url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        params = {
            'api_key': api_key,
            'language': 'en-US'
        }
        
        r = requests.get(details_url, params=params, timeout=10)
        time.sleep(0.5)
        
        if r.status_code != 200:
            print(f"  ERROR TMDB details: status {r.status_code}")
            return {}
        
        data = r.json()
        
        result = {
            'overview': data.get('overview', ''),
            'tagline': data.get('tagline', ''),
            'title': data.get('title', config['title']),
            'release_date': data.get('release_date', ''),
            'genres': [g['name'] for g in data.get('genres', [])],
            'tmdb_id': tmdb_id
        }
        
        total_chars = len(result['overview']) + len(result['tagline'])
        print(f"  TMDB marketing: {total_chars} chars (overview + tagline)")
        
        return result
        
    except Exception as e:
        print(f"  ERROR TMDB marketing: {e}")
        return {}
