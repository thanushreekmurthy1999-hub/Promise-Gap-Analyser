"""IMDB review scraper with relevance verification."""

import time
import requests
from bs4 import BeautifulSoup
from scrapers.verify import is_relevant


def scrape_imdb_reviews(film_slug: str, config: dict,
                        max_reviews: int = 50) -> list[dict]:
    """
    Scrape IMDB user reviews.
    Verify each review is about the actual film content
    before keeping it.
    """
    imdb_id = config['imdb_id']
    url = f"https://www.imdb.com/title/{imdb_id}/reviews"
    
    headers = {
        'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                      'AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/120.0.0.0 Safari/537.36'),
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    print(f"  Fetching IMDB reviews: {imdb_id}")
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        time.sleep(2)
        
        if r.status_code != 200:
            print(f"  ERROR IMDB: status {r.status_code}")
            return []
        
        soup = BeautifulSoup(r.text, 'html.parser')
        review_containers = soup.select('.review-container')
        
        if not review_containers:
            # Try alternative selector
            review_containers = soup.select('[data-testid="review-card"]')
        
        if not review_containers:
            print(f"  WARNING: No reviews found on IMDB page")
            return []
        
        print(f"  Found {len(review_containers)} raw reviews on IMDB")
        
        kept_reviews = []
        
        for container in review_containers[:max_reviews]:
            try:
                # Extract review text
                text_el = (container.select_one('.text.show-more__control')
                          or container.select_one('.content .text')
                          or container.select_one('[data-testid="review-text"]'))
                
                if not text_el:
                    continue
                
                text = text_el.get_text(strip=True)
                
                # Extract rating if present
                rating_el = (container.select_one('.rating-other-user-rating')
                            or container.select_one('[data-testid="review-score"]'))
                rating = None
                if rating_el:
                    rating_text = rating_el.get_text(strip=True)
                    try:
                        rating = int(rating_text.split('/')[0].strip())
                    except Exception:
                        rating = None
                
                # Basic quality gates first
                if len(text) < 40:
                    continue
                
                # Relevance check
                relevant, rel_score = is_relevant(
                    text,
                    config['title'],
                    config['year'],
                    threshold=0.20
                )
                
                if not relevant:
                    print(f"  DISCARD IMDB: score={rel_score} "
                          f"| '{text[:50]}...'")
                    continue
                
                kept_reviews.append({
                    "text": text,
                    "rating": rating,
                    "helpful_votes": 0,
                    "relevance_score": rel_score
                })
                
            except Exception as e:
                continue
        
        print(f"  Total IMDB reviews kept: {len(kept_reviews)}")
        return kept_reviews
        
    except Exception as e:
        print(f"  ERROR IMDB: {e}")
        return []
