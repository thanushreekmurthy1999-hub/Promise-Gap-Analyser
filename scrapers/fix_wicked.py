#!/usr/bin/env python3
"""
Fix Wicked review count by re-scraping with extended sources.
Step 1: Extended Reddit
Step 2: IMDB pagination (if Reddit < 30)
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scrapers.reddit_wicked import scrape_reddit_wicked
from scrapers.imdb_paginated import scrape_imdb_paginated
from scrapers.tmdb_reviews import get_tmdb_reviews

def fix_wicked():
    print("="*60)
    print("FIXING WICKED REVIEW COUNT")
    print("="*60)
    
    config = {
        'title': 'Wicked',
        'year': 2024,
        'imdb_id': 'tt1262426'
    }
    
    # STEP 1: Extended Reddit scraping
    print("\n[STEP 1] Extended Reddit scraping...")
    reddit_comments = scrape_reddit_wicked(max_comments=50)
    
    print(f"\n  Reddit results: {len(reddit_comments)} comments")
    
    # STEP 2: IMDB pagination if needed
    imdb_reviews = []
    if len(reddit_comments) < 30:
        print(f"\n[STEP 2] Reddit count ({len(reddit_comments)}) < 30, adding IMDB pagination...")
        imdb_reviews = scrape_imdb_paginated(
            config['imdb_id'], 
            config, 
            max_pages=5
        )
    else:
        print(f"\n[STEP 2] Reddit count ({len(reddit_comments)}) >= 30, skipping IMDB")
    
    # Also get TMDB reviews (we already have these but include for completeness)
    print(f"\n[STEP 3] Fetching TMDB reviews...")
    tmdb_reviews = get_tmdb_reviews('wicked', config)
    
    # Combine all reviews
    total_reviews = len(reddit_comments) + len(imdb_reviews) + len(tmdb_reviews)
    
    print(f"\n{'='*60}")
    print("FINAL COUNT")
    print(f"{'='*60}")
    print(f"  Reddit:    {len(reddit_comments)}")
    print(f"  IMDB:      {len(imdb_reviews)}")
    print(f"  TMDB:      {len(tmdb_reviews)}")
    print(f"  TOTAL:     {total_reviews}")
    print(f"{'='*60}")
    
    # Show sample reviews
    if total_reviews > 0:
        print("\n[SAMPLE REVIEWS - First 3]:")
        all_reviews = reddit_comments + imdb_reviews + tmdb_reviews
        for i, review in enumerate(all_reviews[:3], 1):
            source = review.get('source', review.get('subreddit', 'unknown'))
            text = review['text'][:100]
            print(f"\n  {i}. [{source}] {text}...")
    
    # Save to file
    reviews_data = {
        "film": "wicked",
        "title": "Wicked",
        "year": 2024,
        "reddit": reddit_comments,
        "imdb": imdb_reviews,
        "tmdb": tmdb_reviews,
        "scrape_summary": {
            "reddit_kept": len(reddit_comments),
            "imdb_kept": len(imdb_reviews),
            "tmdb_kept": len(tmdb_reviews),
            "total_reviews": total_reviews,
            "note": "Extended scraping with multiple subreddits and IMDB pagination"
        }
    }
    
    output_path = "data/raw/wicked_reviews.json"
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(reviews_data, f, indent=2)
    
    print(f"\n✓ Saved to: {output_path}")
    
    if total_reviews < 20:
        print(f"\n  ⚠️  WARNING: Still only {total_reviews} reviews (below 20 minimum)")
    else:
        print(f"\n  ✅ Review count is now healthy: {total_reviews} reviews")
    
    return total_reviews


if __name__ == "__main__":
    count = fix_wicked()
    sys.exit(0 if count >= 20 else 1)
