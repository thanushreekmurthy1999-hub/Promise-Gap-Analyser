"""Scrapers package for Promise Gap Analyser."""

from scrapers.verify import is_relevant, load_verifier
from scrapers.youtube import scrape_youtube_transcripts
from scrapers.wikipedia import scrape_wikipedia_marketing
from scrapers.reddit import scrape_reddit
from scrapers.imdb import scrape_imdb_reviews
from scrapers.tmdb_reviews import get_tmdb_reviews
from scrapers.letterboxd_apify import scrape_letterboxd_apify

__all__ = [
    'is_relevant',
    'load_verifier',
    'scrape_youtube_transcripts',
    'scrape_wikipedia_marketing',
    'scrape_reddit',
    'scrape_imdb_reviews',
    'get_tmdb_reviews',
    'scrape_letterboxd_apify',
]
