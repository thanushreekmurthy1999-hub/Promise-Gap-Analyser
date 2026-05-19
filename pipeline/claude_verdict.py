#!/usr/bin/env python3
"""
Claude-powered verdict generation for Promise Gap Analyser.

Uses the structured marketing verdict from verdict.py to produce
studio-facing marketing judgments.
"""

import os
import json
from pathlib import Path

try:
    from .verdict import get_claude_verdict, MARKETING_VERDICT_LABELS
except ImportError:
    from verdict import get_claude_verdict, MARKETING_VERDICT_LABELS


def classify_verdict(gap_score: float, sentiment_mean: float) -> str:
    """
    Classify verdict based on gap score and sentiment.
    
    Quadrants:
    - Low gap + positive sentiment = Aligned Success
    - Low gap + negative sentiment = Aligned Failure  
    - High gap + positive sentiment = Translation Success
    - High gap + negative sentiment = Translation Failure
    - Middle zone = Translation Zone
    """
    if gap_score < 22:
        if sentiment_mean > 0:
            return "Aligned Success"
        else:
            return "Aligned Failure"
    elif gap_score > 30:
        if sentiment_mean > 0:
            return "Translation Success"
        else:
            return "Translation Failure"
    else:
        return "Translation Zone"


def process_film(film_slug: str) -> dict:
    """
    Load film data, compute verdict, call Claude, save result.
    """
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(exist_ok=True)
    
    # Load marketing data
    marketing_path = raw_dir / f"{film_slug}_marketing.json"
    reviews_path = raw_dir / f"{film_slug}_reviews.json"
    
    if not marketing_path.exists() or not reviews_path.exists():
        raise FileNotFoundError(f"Missing data files for {film_slug}")
    
    with open(marketing_path) as f:
        marketing = json.load(f)
    with open(reviews_path) as f:
        reviews = json.load(f)
    
    # Get film title and year
    title = marketing.get('title', film_slug.replace('_', ' ').title())
    year = marketing.get('year', 2025)
    
    # Load existing processed result (has gap scores)
    result_path = processed_dir / f"{film_slug}_result.json"
    if result_path.exists():
        with open(result_path) as f:
            result = json.load(f)
    else:
        raise FileNotFoundError(f"Run gap_scorer.py first to generate {result_path}")
    
    # Build film_config for the verdict function
    film_config = {
        'title': title,
        'year': year,
        'rt_score': result.get('rtScore', 'N/A'),
        'audience_score': result.get('audienceScore', 'N/A'),
        'cinemascore': result.get('cinemaScore', 'N/A'),
        'data_quality_flag': result.get('data_quality_flag', '')
    }
    
    # Build gap_result dict
    gap_result = {
        'composite': result.get('gapScore', result.get('gap_score', 0)),
        'topic_divergence': result.get('topic_divergence', result.get('gapScore', 0)),
        'centroid_distance': result.get('embeddingGap', result.get('centroid_distance', 0)),
        'promise_keywords': result.get('promiseThemes', result.get('promise_keywords', [])),
        'delivery_keywords': result.get('deliveryThemes', result.get('delivery_keywords', []))
    }
    
    # Build sentiment dict
    sentiment_data = result.get('deliverySentiment', result.get('sentiment', {}))
    if isinstance(sentiment_data, dict):
        sentiment = {
            'mean': sentiment_data.get('mean', 0),
            'positive_ratio': sentiment_data.get('positive', 0),
            'negative_ratio': sentiment_data.get('negative', 0)
        }
    else:
        sentiment = {'mean': 0, 'positive_ratio': 0, 'negative_ratio': 0}
    
    # Classify rule-based verdict
    rule_verdict = classify_verdict(
        gap_result['composite'], 
        sentiment['mean']
    )
    
    # Generate Claude verdict (now returns structured dict)
    print(f"  Generating structured verdict for {title}...")
    claude_verdict = get_claude_verdict(
        film_config=film_config,
        gap_result=gap_result,
        sentiment=sentiment,
        rule_verdict=rule_verdict
    )
    
    # Update result with new structured fields
    result['verdict'] = rule_verdict
    result['marketing_label'] = claude_verdict['marketing_label']
    result['what_was_promised'] = claude_verdict['what_was_promised']
    result['what_was_received'] = claude_verdict['what_was_received']
    result['marketing_explanation'] = claude_verdict['marketing_explanation']
    result['recommendation'] = claude_verdict['recommendation']
    result['lost_audience'] = claude_verdict['lost_audience']
    result['full_verdict'] = claude_verdict['full_verdict']
    
    # Keep backwards compatibility
    result['claude_verdict'] = claude_verdict['full_verdict']
    result['verdictSummary'] = claude_verdict['full_verdict']
    result['diagnosis'] = claude_verdict['full_verdict']
    
    # Save updated result
    with open(result_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nRESULT: {title}")
    print(f"  Gap Score:       {gap_result['composite']}")
    print(f"  Sentiment:       {sentiment['mean']}")
    print(f"  Rule Verdict:    {rule_verdict}")
    print(f"  Marketing Label: {claude_verdict['marketing_label']}")
    print(f"  Recommendation:  {claude_verdict['recommendation']}")
    print(f"  Saved to:        {result_path}")
    
    return result


def process_all_films():
    """Process all films and generate Claude verdicts."""
    films = ['snow_white', 'wicked', 'minecraft', 'lilo_stitch', 
             'thunderbolts', 'joker_2', 'paddington']
    
    print("Generating structured marketing verdicts for all films...\n")
    print("=" * 60)
    
    results = []
    for film in films:
        try:
            result = process_film(film)
            results.append({
                'film': film,
                'title': result.get('filmTitle', result.get('title', film)),
                'gap': result.get('gapScore', result.get('gap_score', 0)),
                'label': result.get('marketing_label', 'N/A')
            })
        except Exception as e:
            print(f"  ✗ {film}: {e}")
            results.append({
                'film': film,
                'title': film,
                'gap': 'ERR',
                'label': 'ERROR'
            })
        print()
        print("=" * 60)
    
    # Print summary table
    print("\n" + "=" * 60)
    print("SUMMARY TABLE")
    print("=" * 60)
    print(f"{'Film':<25} | {'Gap':>5} | {'Label':<20}")
    print("-" * 60)
    for r in results:
        gap_str = f"{r['gap']:.1f}" if isinstance(r['gap'], (int, float)) else r['gap']
        print(f"{r['title']:<25} | {gap_str:>5} | {r['label']:<20}")
    print("=" * 60)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            process_all_films()
        else:
            process_film(sys.argv[1])
    else:
        process_all_films()
