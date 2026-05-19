"""IMDB review scraper using Apify actors."""

import os
import time
from scrapers.verify import is_relevant


def scrape_imdb_apify(film_slug: str, config: dict, max_reviews: int = 30) -> list[dict]:
    """
    Scrape reviews from IMDB using Apify website-content-crawler actor.
    """
    api_token = os.environ.get('APIFY_API_TOKEN')
    if not api_token or api_token == 'your_apify_token_here':
        return []
    
    imdb_id = config.get('imdb_id')
    if not imdb_id:
        return []
    
    reviews_url = f"https://www.imdb.com/title/{imdb_id}/reviews/"
    print(f"  Fetching IMDB via Apify: {reviews_url}")
    
    try:
        from apify_client import ApifyClient
        client = ApifyClient(api_token)
        
        run_input = {
            "startUrls": [{"url": reviews_url}],
            "maxCrawlDepth": 1,
            "maxPagesPerCrawl": 3,
            "waitFor": ".review-container",
            "extractor": {
                "type": "cheerio",
                "selector": ".review-container",
                "data": {
                    "text": ".text.show-more__control",
                    "title": ".title",
                    "rating": ".rating-other-user-rating span"
                }
            }
        }
        
        print(f"  Starting Apify IMDB actor...")
        run = client.actor("apify/website-content-crawler").call(run_input=run_input)
        
        print(f"  Run ID: {run['id']}")
        
        # Wait for completion
        run_id = run['id']
        for i in range(36):  # 3 minutes max
            run_status = client.run(run_id).get()
            status = run_status.get('status')
            
            if status in ['SUCCEEDED', 'FAILED', 'TIMED-OUT']:
                break
            
            if i % 6 == 0:
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
            
            # Parse rating
            rating = None
            rating_text = item.get('rating', '')
            if rating_text:
                try:
                    rating = int(rating_text.split('/')[0])
                except:
                    pass
            
            reviews.append({
                "text": text,
                "rating": rating,
                "title": item.get('title', ''),
                "source": "imdb",
                "relevance_score": rel_score
            })
            
            if len(reviews) >= max_reviews:
                break
        
        print(f"  IMDB reviews kept: {len(reviews)}")
        return reviews
        
    except Exception as e:
        print(f"  ERROR Apify IMDB: {e}")
        return []
