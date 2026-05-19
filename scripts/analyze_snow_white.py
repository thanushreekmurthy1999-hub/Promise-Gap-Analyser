#!/usr/bin/env python3
"""Analyze Snow White reviews for controversy-related keywords."""

import json
from pathlib import Path

# Load the reviews file
reviews_path = Path("data/raw/snow_white_reviews.json")
with open(reviews_path) as f:
    data = json.load(f)

# Collect all reviews
all_reviews = []

# Reddit reviews
for r in data.get('reddit', []):
    text = r.get('text', '')
    if text:
        all_reviews.append(('reddit', text))

# TMDB reviews
for r in data.get('tmdb', []):
    text = r.get('text', '')
    if text:
        all_reviews.append(('tmdb', text))

# Keywords to search for
keywords = [
    'zegler', 'rachel', 'gadot', 'gal', 'controversy', 'woke', 'political',
    'boycott', 'casting', 'remake', 'diverse', 'representation'
]

# Count reviews containing any keyword
reviews_with_keywords = 0
matched_reviews = []

for source, text in all_reviews:
    text_lower = text.lower()
    found_keywords = [kw for kw in keywords if kw in text_lower]
    if found_keywords:
        reviews_with_keywords += 1
        matched_reviews.append((source, found_keywords, text[:200]))

# Print results
print("="*70)
print("SNOW WHITE REVIEWS ANALYSIS")
print("="*70)
print(f"\nTotal reviews: {len(all_reviews)}")
print(f"  - Reddit: {len([r for r in all_reviews if r[0] == 'reddit'])}")
print(f"  - TMDB: {len([r for r in all_reviews if r[0] == 'tmdb'])}")
print(f"\nReviews containing controversy keywords: {reviews_with_keywords}")
print(f"Percentage: {reviews_with_keywords / len(all_reviews) * 100:.1f}%")

print("\n" + "="*70)
print("FIRST 5 REVIEW TEXTS:")
print("="*70)

for i, (source, text) in enumerate(all_reviews[:5], 1):
    print(f"\n--- Review {i} ({source}) ---")
    # Truncate long reviews for display
    display_text = text[:500] + "..." if len(text) > 500 else text
    print(display_text)

print("\n" + "="*70)
print("REVIEWS WITH CONTROVERSY KEYWORDS (sample):")
print("="*70)

for i, (source, found_kws, preview) in enumerate(matched_reviews[:10], 1):
    print(f"\n{i}. [{source}] Keywords: {', '.join(found_kws)}")
    print(f"   Preview: {preview[:150]}...")

print(f"\n{'='*70}")
print(f"SUMMARY: {reviews_with_keywords}/{len(all_reviews)} reviews ({reviews_with_keywords / len(all_reviews) * 100:.1f}%) mention controversy-related terms")
print("="*70)
