"""Master scraper runner with health checks and summary reporting."""

import json
import time
import sys
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import FILMS_SCRAPE_CONFIG
from scrapers.youtube import scrape_youtube_transcripts
from scrapers.wikipedia import scrape_wikipedia_marketing
from scrapers.reddit import scrape_reddit
from scrapers.tmdb_reviews import get_tmdb_reviews
from scrapers.tmdb_marketing import get_tmdb_marketing
from scrapers.letterboxd_apify import scrape_letterboxd_apify


def scrape_film(film_slug: str, config: dict):
    print(f"\n{'='*55}")
    print(f"SCRAPING: {config['title']} ({config['year']})")
    print(f"{'='*55}")
    
    # --- MARKETING SIDE ---
    print("\n[PROMISE CORPUS]")
    
    transcripts = scrape_youtube_transcripts(film_slug, config)
    wiki_text = scrape_wikipedia_marketing(film_slug, config)
    tmdb_marketing = get_tmdb_marketing(film_slug, config)
    
    # Combine marketing sources
    total_marketing_chars = (
        sum(len(t['transcript']) for t in transcripts) +
        len(wiki_text) +
        len(tmdb_marketing.get('overview', '')) +
        len(tmdb_marketing.get('tagline', ''))
    )
    
    marketing_data = {
        "film": film_slug,
        "title": config['title'],
        "year": config['year'],
        "youtube_transcripts": transcripts,
        "wikipedia_marketing": wiki_text,
        "tmdb_marketing": tmdb_marketing,
        "scrape_summary": {
            "transcripts_kept": len(transcripts),
            "transcripts_attempted": len(config['trailer_ids']),
            "wikipedia_chars": len(wiki_text),
            "tmdb_chars": len(tmdb_marketing.get('overview', '')) + len(tmdb_marketing.get('tagline', '')),
            "total_marketing_chars": total_marketing_chars
        }
    }
    
    # --- DELIVERY SIDE ---
    print("\n[DELIVERY CORPUS]")
    
    reddit_comments = scrape_reddit(film_slug, config)
    tmdb_reviews = get_tmdb_reviews(film_slug, config)
    letterboxd_reviews = scrape_letterboxd_apify(film_slug, config)
    
    reviews_data = {
        "film": film_slug,
        "title": config['title'],
        "year": config['year'],
        "reddit": reddit_comments,
        "tmdb": tmdb_reviews,
        "letterboxd": letterboxd_reviews,
        "scrape_summary": {
            "reddit_kept": len(reddit_comments),
            "tmdb_kept": len(tmdb_reviews),
            "letterboxd_kept": len(letterboxd_reviews),
            "total_reviews": len(reddit_comments) + len(tmdb_reviews) + len(letterboxd_reviews)
        }
    }
    
    # --- SAVE ---
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    marketing_path = f"data/raw/{film_slug}_marketing.json"
    reviews_path = f"data/raw/{film_slug}_reviews.json"
    
    with open(marketing_path, 'w') as f:
        json.dump(marketing_data, f, indent=2)
    with open(reviews_path, 'w') as f:
        json.dump(reviews_data, f, indent=2)
    
    # --- HEALTH CHECK ---
    print(f"\n[HEALTH CHECK: {config['title']}]")
    
    total_reviews = len(reddit_comments) + len(tmdb_reviews) + len(letterboxd_reviews)
    
    warnings = []
    
    if len(transcripts) == 0:
        warnings.append("NO YouTube transcripts — configure HTTP_PROXY to use a proxy/VPN")
    if len(wiki_text) < 100:
        warnings.append("Wikipedia marketing section very short or missing")
    if total_marketing_chars < 500:
        warnings.append(f"CRITICAL: Total marketing text only {total_marketing_chars} chars — gap score will be unreliable")
    if total_reviews < 20:
        warnings.append(f"Only {total_reviews} reviews — delivery corpus too thin")
    
    if warnings:
        print("  WARNINGS:")
        for w in warnings:
            print(f"    ⚠️  {w}")
    else:
        print("  ✅ Corpus health looks good")
    
    print(f"\n  Marketing sources:")
    print(f"    - YouTube: {len(transcripts)} transcripts")
    print(f"    - Wikipedia: {len(wiki_text)} chars")
    print(f"    - TMDB: {marketing_data['scrape_summary']['tmdb_chars']} chars")
    print(f"    - TOTAL: {total_marketing_chars} chars")
    print(f"\n  Reviews: {len(reddit_comments)} Reddit + {len(tmdb_reviews)} TMDB + {len(letterboxd_reviews)} Letterboxd = {total_reviews} total")
    print(f"  Saved:   {marketing_path}")
    print(f"           {reviews_path}")
    
    return marketing_data, reviews_data, warnings


def scrape_all():
    summary = {}
    all_warnings = {}
    
    for slug, config in FILMS_SCRAPE_CONFIG.items():
        marketing, reviews, warnings = scrape_film(slug, config)
        summary[slug] = {
            "transcripts": marketing['scrape_summary']['transcripts_kept'],
            "wiki_chars": marketing['scrape_summary']['wikipedia_chars'],
            "tmdb_marketing": marketing['scrape_summary']['tmdb_chars'],
            "total_marketing": marketing['scrape_summary']['total_marketing_chars'],
            "reddit": reviews['scrape_summary']['reddit_kept'],
            "tmdb_reviews": reviews['scrape_summary']['tmdb_kept'],
            "letterboxd_reviews": reviews['scrape_summary']['letterboxd_kept'],
            "total_reviews": reviews['scrape_summary']['total_reviews']
        }
        all_warnings[slug] = warnings
        time.sleep(3)  # pause between films
    
    # Print final summary table
    print(f"\n{'='*100}")
    print("SCRAPE COMPLETE — CORPUS SUMMARY")
    print(f"{'='*100}")
    print(f"{'Film':<20} {'Marketing (chars)':>35} {'Reviews':>40}")
    print(f"{'':20} {'YT':>6} {'Wiki':>8} {'TMDB':>8} {'Total':>8} {'Reddit':>8} {'TMDB':>7} {'LB':>6} {'Total':>8}")
    print(f"{'-'*100}")
    
    for slug, s in summary.items():
        title = FILMS_SCRAPE_CONFIG[slug]['title'][:18]
        print(f"{title:<20} {s['transcripts']:>6} {s['wiki_chars']:>8} "
              f"{s['tmdb_marketing']:>8} {s['total_marketing']:>8} "
              f"{s['reddit']:>8} {s['tmdb_reviews']:>7} {s['letterboxd_reviews']:>6} {s['total_reviews']:>8}")
    
    # Print any warnings
    films_with_warnings = [(s, w) for s, w in all_warnings.items() if w]
    if films_with_warnings:
        print(f"\n{'!'*70}")
        print("FILMS WITH WARNINGS — REVIEW BEFORE PROCEEDING")
        print(f"{'!'*70}")
        for slug, warnings in films_with_warnings:
            title = FILMS_SCRAPE_CONFIG[slug]['title']
            print(f"\n  {title}:")
            for w in warnings:
                print(f"    ⚠️  {w}")
    
    print(f"\n{'='*100}")
    print("STOP HERE. Review the table above before running the pipeline.")
    print("Any film with <500 marketing chars or <20 total reviews needs attention.")
    print("Configure HTTP_PROXY in .env if YouTube transcripts are blocked.")
    print(f"{'='*100}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] != "--all":
        film_slug = sys.argv[1]
        if film_slug in FILMS_SCRAPE_CONFIG:
            scrape_film(film_slug, FILMS_SCRAPE_CONFIG[film_slug])
        else:
            print(f"Unknown film: {film_slug}")
            print(f"Available: {list(FILMS_SCRAPE_CONFIG.keys())}")
    else:
        scrape_all()
