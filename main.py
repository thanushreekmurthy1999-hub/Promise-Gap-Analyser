#!/usr/bin/env python3
"""
Promise Gap Analyser - Main Entry Point

Run individual films or all films to generate structured marketing verdicts.

Usage:
    python main.py joker_2          # Run single film
    python main.py --all            # Run all 7 films
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from pipeline.claude_verdict import process_film, process_all_films


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '--all':
            process_all_films()
        else:
            film_slug = sys.argv[1]
            try:
                result = process_film(film_slug)
                print(f"\n✓ Successfully processed {film_slug}")
            except Exception as e:
                print(f"\n✗ Error processing {film_slug}: {e}")
                sys.exit(1)
    else:
        print("Usage:")
        print("  python main.py <film_slug>   # Process single film")
        print("  python main.py --all         # Process all films")
        print("")
        print("Available films:")
        print("  joker_2, wicked, minecraft, snow_white,")
        print("  lilo_stitch, thunderbolts, paddington")
