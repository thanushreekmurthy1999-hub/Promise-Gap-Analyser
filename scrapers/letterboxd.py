"""Letterboxd review scraper using BeautifulSoup."""

import time
import requests
from bs4 import BeautifulSoup
from scrapers.verify import is_relevant

# Map our film slugs to Letterboxd film slugs
LETTERBOXD_SLUGS = {
    "snow_white": "snow-white-2025",
    "wicked": "wicked-2024",
    "minecraft": "a-minecraft-movie",
    "lilo_stitch": "lilo-stitch-2025",
    "thunderbolts": "thunderbolts-2025",
    "joker_2": "joker-folie-a-deux",
    "paddington": "paddington-in-peru"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
}


def scrape_letterboxd(film_slug: str, config: dict, max_reviews: int = 30) -> list[dict]:
    """
    Scrape reviews from Letterboxd.
    
    Letterboxd uses infinite scroll pagination. We'll fetch first 2-3 pages
    of reviews which are available server-side rendered.
    """
    lb_slug = LETTERBOXD_SLUGS.get(film_slug)
    if not lb_slug:
        print(f"  No Letterboxd slug configured for {film_slug}")
        return []
    
    print(f"  Fetching Letterboxd reviews: {lb_slug}")
    
    reviews = []
    page = 1
    
    while len(reviews) < max_reviews and page <= 3:  # Max 3 pages to be polite
        url = f"https://letterboxd.com/film/{lb_slug}/reviews/page/{page}/"
        
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            time.sleep(2)  # Be polite to Letterboxd
            
            if r.status_code != 200:
                print(f"  ERROR Letterboxd page {page}: status {r.status_code}")
                break
            
            soup = BeautifulSoup(r.text, 'html.parser')
            
            # Find review containers
            review_containers = soup.select('.film-detail')
            
            if not review_containers:
                print(f"  No more reviews found on page {page}")
                break
            
            print(f"  Page {page}: Found {len(review_containers)} reviews")
            
            for container in review_containers:
                if len(reviews) >= max_reviews:
                    break
                
                try:
                    # Extract review text
                    body_el = container.select_one('.body-text')
                    if not body_el:
                        continue
                    
                    # Get text, preserving paragraphs
                    paragraphs = body_el.find_all('p')
                    if paragraphs:
                        text = ' '.join([p.get_text(strip=True) for p in paragraphs])
                    else:
                        text = body_el.get_text(strip=True)
                    
                    if not text or len(text) < 40:
                        continue
                    
                    # Extract rating if present
                    rating_el = container.select_one('.rating')
                    rating = None
                    if rating_el:
                        # Letterboxd uses class like "rated-4" for 4 stars
                        rating_class = rating_el.get('class', [])
                        for cls in rating_class:
                            if cls.startswith('rated-'):
                                try:
                                    rating = int(cls.replace('rated-', ''))
                                except:
                                    pass
                    
                    # Extract reviewer
                    reviewer_el = container.select_one('.avatar')
                    reviewer = reviewer_el.get('href', '').strip('/') if reviewer_el else 'Unknown'
                    
                    # Extract likes
                    likes_el = container.select_one('.likes .count')
                    likes = 0
                    if likes_el:
                        try:
                            likes = int(likes_el.get_text(strip=True).replace(',', ''))
                        except:
                            pass
                    
                    # Relevance check
                    relevant, rel_score = is_relevant(
                        text,
                        config['title'],
                        config['year'],
                        threshold=0.10  # Lenient for reviews
                    )
                    
                    if not relevant:
                        print(f"  DISCARD Letterboxd: score={rel_score} | '{text[:50]}...'")
                        continue
                    
                    reviews.append({
                        "text": text,
                        "rating": rating,
                        "author": reviewer,
                        "likes": likes,
                        "source": "letterboxd",
                        "page": page,
                        "relevance_score": rel_score
                    })
                    
                except Exception as e:
                    continue
            
            # Check if there's a next page
            next_page = soup.select_one('.pagination .next')
            if not next_page or 'disabled' in str(next_page.get('class', [])):
                break
            
            page += 1
            
        except Exception as e:
            print(f"  ERROR Letterboxd page {page}: {e}")
            break
    
    print(f"  Total Letterboxd reviews kept: {len(reviews)}")
    return reviews
