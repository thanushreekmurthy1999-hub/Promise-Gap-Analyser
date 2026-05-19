#!/usr/bin/env python3
"""
Helper script to manually add YouTube transcripts when automated scraping is blocked.

Usage:
    python scripts/add_manual_transcript.py snow_white
    
Then follow prompts to paste video IDs and transcripts.
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import FILMS_SCRAPE_CONFIG


def add_manual_transcript(film_slug: str):
    """Interactive helper to add manual transcripts."""
    
    if film_slug not in FILMS_SCRAPE_CONFIG:
        print(f"Unknown film: {film_slug}")
        print(f"Available: {list(FILMS_SCRAPE_CONFIG.keys())}")
        return
    
    config = FILMS_SCRAPE_CONFIG[film_slug]
    marketing_path = f"data/raw/{film_slug}_marketing.json"
    
    # Load existing marketing data if present
    if Path(marketing_path).exists():
        with open(marketing_path) as f:
            data = json.load(f)
    else:
        data = {
            "film": film_slug,
            "title": config['title'],
            "year": config['year'],
            "youtube_transcripts": [],
            "wikipedia_marketing": "",
            "tmdb_marketing": {},
            "scrape_summary": {
                "transcripts_kept": 0,
                "transcripts_attempted": len(config['trailer_ids']),
                "wikipedia_chars": 0,
                "tmdb_chars": 0,
                "total_marketing_chars": 0
            }
        }
    
    print(f"\n{'='*60}")
    print(f"Adding manual transcripts for: {config['title']} ({config['year']})")
    print(f"{'='*60}")
    print(f"\nConfigured trailer IDs: {config['trailer_ids']}")
    print(f"\nExisting transcripts: {len(data.get('youtube_transcripts', []))}")
    
    # Show existing transcripts
    existing_ids = [t['video_id'] for t in data.get('youtube_transcripts', [])]
    if existing_ids:
        print(f"Already have: {existing_ids}")
    
    # Show which IDs are still needed
    needed_ids = [vid for vid in config['trailer_ids'] if vid not in existing_ids]
    if needed_ids:
        print(f"\nStill need transcripts for: {needed_ids}")
    else:
        print("\n✓ All configured trailer IDs already have transcripts!")
        add_more = input("\nAdd additional transcripts? (y/n): ").strip().lower()
        if add_more != 'y':
            return
        needed_ids = ['custom_' + str(i) for i in range(1, 10)]  # Allow custom entries
    
    # Add transcripts one by one
    for video_id in needed_ids:
        print(f"\n{'-'*60}")
        
        if video_id.startswith('custom_'):
            custom_id = input(f"Enter video ID (or 'skip' to finish, 'done' to save): ").strip()
            if custom_id.lower() in ['skip', 'done', '']:
                break
            video_id = custom_id
        
        # Check if already exists
        if any(t['video_id'] == video_id for t in data.get('youtube_transcripts', [])):
            print(f"  ⚠️  Transcript for {video_id} already exists. Skipping.")
            continue
        
        print(f"\n📺 Video ID: {video_id}")
        print("   Paste the transcript text below (press Ctrl+D or type 'END' on new line when done):\n")
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == 'END':
                    break
                lines.append(line)
            except EOFError:  # Ctrl+D
                break
        
        transcript_text = '\n'.join(lines).strip()
        
        if not transcript_text:
            print("  ⚠️  Empty transcript. Skipping.")
            continue
        
        if len(transcript_text) < 50:
            print(f"  ⚠️  Transcript very short ({len(transcript_text)} chars). Include anyway? (y/n): ", end='')
            if input().strip().lower() != 'y':
                continue
        
        # Add to data
        if 'youtube_transcripts' not in data:
            data['youtube_transcripts'] = []
        
        data['youtube_transcripts'].append({
            "video_id": video_id,
            "title": f"Trailer {video_id}",
            "transcript": transcript_text,
            "relevance_score": 1.0,  # Manual entry is trusted
            "char_count": len(transcript_text),
            "source": "manual",
            "added_at": datetime.now().isoformat()
        })
        
        print(f"  ✓ Added transcript: {len(transcript_text)} chars")
        
        # Ask if they want to add another (skip if non-interactive)
        if not video_id.startswith('custom_'):
            try:
                more = input(f"\nAdd another transcript? (y/n): ").strip().lower()
                if more != 'y':
                    break
            except EOFError:
                # Non-interactive mode (piped input) - just continue
                print("  (Non-interactive mode - finishing)")
                break
    
    # Update summary
    total_chars = sum(len(t['transcript']) for t in data.get('youtube_transcripts', []))
    data['scrape_summary']['transcripts_kept'] = len(data['youtube_transcripts'])
    data['scrape_summary']['transcripts_attempted'] = len(config['trailer_ids'])
    
    wiki_chars = len(data.get('wikipedia_marketing', ''))
    tmdb_chars = len(data.get('tmdb_marketing', {}).get('overview', '')) + \
                 len(data.get('tmdb_marketing', {}).get('tagline', ''))
    
    data['scrape_summary']['wikipedia_chars'] = wiki_chars
    data['scrape_summary']['tmdb_chars'] = tmdb_chars
    data['scrape_summary']['total_marketing_chars'] = total_chars + wiki_chars + tmdb_chars
    
    # Save
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    with open(marketing_path, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n{'='*60}")
    print(f"✓ Saved to: {marketing_path}")
    print(f"\nMarketing corpus summary:")
    print(f"  - YouTube transcripts: {len(data['youtube_transcripts'])} ({total_chars} chars)")
    print(f"  - Wikipedia: {wiki_chars} chars")
    print(f"  - TMDB: {tmdb_chars} chars")
    print(f"  - TOTAL: {data['scrape_summary']['total_marketing_chars']} chars")
    
    if data['scrape_summary']['total_marketing_chars'] < 500:
        print(f"\n  ⚠️  WARNING: Total marketing text is below 500 chars")
        print(f"      Consider adding more transcripts or checking other sources.")
    else:
        print(f"\n  ✓ Marketing corpus looks good!")
    
    print(f"{'='*60}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        film_slug = sys.argv[1]
    else:
        print("Usage: python scripts/add_manual_transcript.py <film_slug>")
        print(f"\nAvailable films: {', '.join(FILMS_SCRAPE_CONFIG.keys())}")
        sys.exit(1)
    
    add_manual_transcript(film_slug)
