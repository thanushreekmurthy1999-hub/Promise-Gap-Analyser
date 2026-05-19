"""Letterboxd review scraper using Apify actors."""

import os
import time
from scrapers.verify import is_relevant

# Map our film slugs to Letterboxd film URLs
LETTERBOXD_URLS = {
    "snow_white": "https://letterboxd.com/film/snow-white-2025/",
    "wicked": "https://letterboxd.com/film/wicked-2024/",
    "minecraft": "https://letterboxd.com/film/a-minecraft-movie/",
    "lilo_stitch": "https://letterboxd.com/film/lilo-stitch-2025/",
    "thunderbolts": "https://letterboxd.com/film/thunderbolts-2025/",
    "joker_2": "https://letterboxd.com/film/joker-folie-a-deux/",
    "paddington": "https://letterboxd.com/film/paddington-in-peru/"
}


def scrape_letterboxd_apify(film_slug: str, config: dict, max_reviews: int = 30) -> list[dict]:
    """
    Scrape reviews from Letterboxd using Apify website-content-crawler actor.
    """
    api_token = os.environ.get('APIFY_API_TOKEN')
    if not api_token or api_token == 'your_apify_token_here':
        return []
    
    url = LETTERBOXD_URLS.get(film_slug)
    if not url:
        return []
    
    print(f"  Fetching Letterboxd via Apify: {url}")
    
    try:
        from apify_client import ApifyClient
        client = ApifyClient(api_token)
        
        # Use web scraper actor
        reviews_url = f"{url}reviews/"
        
        run_input = {
            "startUrls": [{"url": reviews_url}],
            "maxCrawlDepth": 1,
            "maxPagesPerCrawl": 5,
            "waitFor": ".film-detail",
            "extractor": {
                "type": "cheerio",
                "selector": ".film-detail",
                "data": {
                    "text": ".body-text",
                    "author": ".avatar",
                    "rating": ".rating"
                }
            }
        }
        
        print(f"  Starting Apify actor...")
        run = client.actor("apify/website-content-crawler").call(run_input=run_input)
        
        print(f"  Run ID: {run['id']}")
        
        # Wait for completion (max 3 minutes)
        run_id = run['id']
        for i in range(36):  # 36 * 5s = 3 minutes
            run_status = client.run(run_id).get()
            status = run_status.get('status')
            
            if status in ['SUCCEEDED', 'FAILED', 'TIMED-OUT']:
                break
            
            if i % 6 == 0:  # Print every 30s
                print(f"  ... status: {status} ({(i+1)*5}s)")
            time.sleep(5)
        
        # Get results
        dataset = client.dataset(run['defaultDatasetId'])
        items = list(dataset.iterate_items())
        
        print(f"  Apify returned {len(items)} items")
        
        reviews = []
        for item in items:
            text = item.get('text', '').strip()
            if not text or len(text) < 40:
                continue
            
            # Relevance check
            relevant, rel_score = is_relevant(
                text, config['title'], config['year'], threshold=0.10
            )
            
            if not relevant:
                continue
            
            # Parse rating from class
            rating_class = item.get('rating', '')
            rating = None
            if 'rated-' in str(rating_class):
                try:
                    rating = int(str(rating_class).split('rated-')[1].split()[0])
                except:
                    pass
            
            reviews.append({
                "text": text,
                "rating": rating,
                "author": str(item.get('author', '')).strip('/'),
                "source": "letterboxd",
                "relevance_score": rel_score
            })
            
            if len(reviews) >= max_reviews:
                break
        
        print(f"  Letterboxd reviews kept: {len(reviews)}")
        return reviews
        
    except Exception as e:
        print(f"  ERROR: {e}")
        return []
