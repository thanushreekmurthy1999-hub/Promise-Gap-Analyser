"""IMDB review scraper with pagination for Wicked."""

import time
import requests
from bs4 import BeautifulSoup
from scrapers.verify import is_relevant

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}


def scrape_imdb_paginated(imdb_id: str, config: dict, max_pages: int = 5) -> list[dict]:
    """
    Scrape IMDB reviews with pagination.
    IMDB uses ?start=0, 25, 50, etc. for pagination (25 reviews per page).
    """
    all_reviews = []
    seen_texts = set()  # Deduplication
    
    for page_num in range(max_pages):
        start = page_num * 25
        url = f"https://www.imdb.com/title/{imdb_id}/reviews?start={start}"
        
        print(f"  Fetching IMDB page (start={start})...")
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            time.sleep(2)  # Delay between pages
            
            if r.status_code != 200:
                print(f"    Status {r.status_code}, stopping pagination")
                break
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Try multiple selectors for review containers
            review_containers = soup.select('.review-container')
            if not review_containers:
                review_containers = soup.select('[data-testid="review-card"]')
            if not review_containers:
                review_containers = soup.select('.lister-item')
            
            if not review_containers:
                print(f"    No reviews found on this page")
                break
            
            print(f"    Found {len(review_containers)} reviews")
            
            page_kept = 0
            for container in review_containers:
                try:
                    # Extract text
                    text_el = (container.select_one('.text.show-more__control')
                              or container.select_one('.content .text')
                              or container.select_one('[data-testid="review-text"]')
                              or container.select_one('.review-text'))
                    
                    if not text_el:
                        continue
                    
                    text = text_el.get_text(strip=True)
                    
                    # Deduplicate
                    text_hash = hash(text[:100])
                    if text_hash in seen_texts:
                        continue
                    seen_texts.add(text_hash)
                    
                    if len(text) < 40:
                        continue
                    
                    # Extract rating
                    rating = None
                    rating_el = (container.select_one('.rating-other-user-rating')
                                or container.select_one('[data-testid="review-score"]'))
                    if rating_el:
                        rating_text = rating_el.get_text(strip=True)
                        try:
                            rating = int(rating_text.split('/')[0])
                        except:
                            pass
                    
                    # Relevance check
                    relevant, rel_score = is_relevant(
                        text, config['title'], config['year'], threshold=0.10
                    )
                    
                    if not relevant:
                        continue
                    
                    all_reviews.append({
                        "text": text,
                        "rating": rating,
                        "source": "imdb",
                        "page": page_num + 1,
                        "relevance_score": rel_score
                    })
                    page_kept += 1
                    
                except Exception as e:
                    continue
            
            print(f"    Kept {page_kept} reviews from this page")
            
            # Stop if we got no reviews from this page
            if page_kept == 0 and len(review_containers) > 0:
                print(f"    All reviews filtered out, stopping")
                break
                
        except Exception as e:
            print(f"    Error: {e}")
            break
    
    print(f"  Total IMDB reviews kept: {len(all_reviews)}")
    return all_reviews
