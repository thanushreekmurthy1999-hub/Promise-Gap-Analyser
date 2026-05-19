"""Reddit discussion scraper with per-comment relevance verification."""

import time
import requests
from scrapers.verify import is_relevant

REDDIT_HEADERS = {
    'User-Agent': 'promise-gap-analyser/1.0 (academic research, non-commercial)'
}


def scrape_reddit(film_slug: str, config: dict,
                  max_threads: int = 5) -> list[dict]:
    """
    Search Reddit for film discussion threads.
    Verify each comment is actually about the film before keeping it.
    Pull from r/movies and r/boxoffice.
    """
    subreddits = ['movies', 'boxoffice', 'flicks']
    all_comments = []
    
    for subreddit in subreddits:
        print(f"  Searching r/{subreddit}...")
        
        try:
            # Search for threads about this film
            search_url = f"https://www.reddit.com/r/{subreddit}/search.json"
            params = {
                'q': config['reddit_query'],
                'restrict_sr': 'on',
                'sort': 'top',
                't': 'year',
                'limit': max_threads
            }
            
            r = requests.get(search_url, params=params,
                           headers=REDDIT_HEADERS, timeout=10)
            time.sleep(1.5)  # respect rate limit
            
            if r.status_code != 200:
                print(f"  ERROR r/{subreddit}: status {r.status_code}")
                continue
            
            threads = r.json()['data']['children']
            print(f"  Found {len(threads)} threads in r/{subreddit}")
            
            for thread in threads:
                thread_data = thread['data']
                thread_title = thread_data.get('title', '')
                thread_url = thread_data.get('permalink', '')
                
                # Quick title check — does the thread title mention
                # anything related to the film? Use very lenient threshold for titles
                title_relevant, title_score = is_relevant(
                    thread_title,
                    config['title'],
                    config['year'],
                    threshold=0.01  # very lenient for short titles
                )
                
                # Also check if title contains key terms directly
                title_lower = thread_title.lower()
                has_key_term = any(term.lower() in title_lower for term in config['title'].split())
                
                if not title_relevant and not has_key_term:
                    print(f"  SKIP thread: '{thread_title[:50]}' "
                          f"(score {title_score})")
                    continue
                
                print(f"  FETCHING thread: '{thread_title[:50]}'")
                
                # Fetch comments
                comments_url = (f"https://www.reddit.com"
                               f"{thread_url}.json?limit=100&sort=top")
                
                cr = requests.get(comments_url,
                                 headers=REDDIT_HEADERS, timeout=10)
                time.sleep(1.5)
                
                if cr.status_code != 200:
                    continue
                
                comment_data = cr.json()
                if len(comment_data) < 2:
                    continue
                
                comments = comment_data[1]['data']['children']
                
                for comment in comments:
                    if comment['kind'] != 't1':
                        continue
                    
                    body = comment['data'].get('body', '')
                    score = comment['data'].get('score', 0)
                    
                    # Basic quality gates first (cheap)
                    if body in ['[deleted]', '[removed]', '']:
                        continue
                    if score < 1:
                        continue
                    if len(body) < 40:
                        continue
                    if body.strip().endswith('?') and len(body) < 150:
                        continue  # pure questions, no opinion
                    
                    # Relevance check — for Reddit we mostly trust the thread title
                    # since comments about a film don't always mention the film title
                    # Only discard if clearly about something completely different
                    relevant, rel_score = is_relevant(
                        body,
                        config['title'],
                        config['year'],
                        threshold=0.05  # Very lenient for Reddit comments
                    )
                    
                    # Also check if comment is about a completely different movie
                    # by looking for strong signals of being off-topic
                    body_lower = body.lower()
                    has_film_reference = any(term in body_lower for term in [
                        'movie', 'film', 'watch', 'seen', 'theater', 'cinema',
                        'actor', 'director', 'scene', 'ending', 'plot', 'character'
                    ])
                    
                    if not relevant and not has_film_reference:
                        print(f"  DISCARD comment: score={rel_score} "
                              f"| '{body[:50]}...'")
                        continue
                    
                    all_comments.append({
                        "text": body,
                        "score": score,
                        "subreddit": subreddit,
                        "thread_title": thread_title,
                        "relevance_score": rel_score
                    })
        
        except Exception as e:
            print(f"  ERROR r/{subreddit}: {e}")
            continue
    
    print(f"  Total Reddit comments kept: {len(all_comments)}")
    return all_comments
