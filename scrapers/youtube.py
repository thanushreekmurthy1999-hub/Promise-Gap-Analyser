"""YouTube transcript scraper with relevance verification and proxy support."""

import os
import time
from youtube_transcript_api import YouTubeTranscriptApi
from scrapers.verify import is_relevant


def get_proxy_config():
    """Get proxy configuration from environment variables."""
    http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('http_proxy')
    https_proxy = os.environ.get('HTTPS_PROXY') or os.environ.get('https_proxy')
    
    proxies = {}
    if http_proxy:
        proxies['http'] = http_proxy
    if https_proxy:
        proxies['https'] = https_proxy
    
    return proxies if proxies else None


def scrape_youtube_transcripts(film_slug: str, config: dict) -> list[dict]:
    """
    Scrape transcripts for all trailer IDs for a film.
    Verify each transcript is actually about the film before keeping it.
    Supports proxy configuration via HTTP_PROXY/HTTPS_PROXY env vars.
    """
    results = []
    proxies = get_proxy_config()
    
    if proxies:
        print(f"  Using proxy: {proxies}")
    
    for video_id in config['trailer_ids']:
        print(f"  Fetching transcript: {video_id}")
        time.sleep(1)  # polite delay
        
        try:
            # Create API instance with proxy if configured
            if proxies:
                ytt_api = YouTubeTranscriptApi(proxies=proxies)
            else:
                ytt_api = YouTubeTranscriptApi()
            
            transcript = ytt_api.fetch(video_id)
            raw_text = ' '.join([snippet.text for snippet in transcript])
            
            # Remove pure sound descriptions
            cleaned_lines = []
            for line in raw_text.split('.'):
                stripped = line.strip()
                if stripped.startswith('[') and stripped.endswith(']'):
                    continue
                cleaned_lines.append(stripped)
            cleaned_text = ' '.join(cleaned_lines).strip()
            
            if len(cleaned_text) < 50:
                print(f"  SKIP {video_id}: transcript too short after cleaning")
                continue
            
            # Verify it is about the actual film
            # Use lower threshold (0.05) for transcripts since video IDs are pre-verified
            relevant, score = is_relevant(
                cleaned_text,
                config['title'],
                config['year'],
                threshold=0.05
            )
            
            if not relevant:
                print(f"  DISCARD {video_id}: relevance score {score} below threshold (likely off-topic)")
                continue
            
            print(f"  KEEP {video_id}: relevance score {score}, {len(cleaned_text)} chars")
            results.append({
                "video_id": video_id,
                "title": f"Trailer {video_id}",
                "transcript": cleaned_text,
                "relevance_score": score,
                "char_count": len(cleaned_text)
            })
            
        except Exception as e:
            error_msg = str(e)
            if "IP has been blocked" in error_msg or "blocked" in error_msg.lower():
                print(f"  ERROR {video_id}: YouTube IP block detected. Configure HTTP_PROXY to use a proxy.")
            else:
                print(f"  ERROR {video_id}: {e}")
            continue
    
    return results
