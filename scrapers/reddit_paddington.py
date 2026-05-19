"""Specialized Reddit scraper for Paddington with extended sources."""

import time
import requests
from scrapers.verify import is_relevant

REDDIT_HEADERS = {
    'User-Agent': 'promise-gap-analyser/1.0 (academic research, non-commercial)'
}

# Extended configuration for Paddington
PADDINGTON_SUBREDDITS = ['movies', 'boxoffice', 'flicks', 'Paddington', 'moviescirclejerk', 'TrueFilm', 'britishmovies']
PADDINGTON_SEARCH_QUERIES = [
    'Paddington in Peru 2024',
    'Paddington in Peru review 2024',
    'Paddington 3 Peru film',
    'Paddington Bear Peru movie',
    'Paddington in Peru thoughts opinions'
]


def scrape_reddit_paddington(max_comments: int = 40) -> list[dict]:
    """
    Extended Reddit scraping for Paddington with multiple subreddits and queries.
    """
    all_comments = []
    seen_comment_ids = set()
    
    config = {
        'title': 'Paddington in Peru',
        'year': 2024
    }
    
    for query in PADDINGTON_SEARCH_QUERIES:
        if len(all_comments) >= max_comments:
            break
            
        print(f"  Searching Reddit for: '{query}'")
        
        for subreddit in PADDINGTON_SUBREDDITS:
            if len(all_comments) >= max_comments:
                break
                
            print(f"    r/{subreddit}...")
            
            try:
                search_url = f"https://www.reddit.com/r/{subreddit}/search.json"
                params = {
                    'q': query,
                    'restrict_sr': 'on',
                    'sort': 'relevance',
                    't': 'year',
                    'limit': 10
                }
                
                r = requests.get(search_url, params=params,
                               headers=REDDIT_HEADERS, timeout=10)
                time.sleep(1.5)
                
                if r.status_code != 200:
                    continue
                
                data = r.json()
                threads = data.get('data', {}).get('children', [])
                
                for thread in threads:
                    if len(all_comments) >= max_comments:
                        break
                        
                    thread_data = thread.get('data', {})
                    thread_title = thread_data.get('title', '')
                    thread_url = thread_data.get('permalink', '')
                    thread_id = thread_data.get('id', '')
                    
                    # Check title relevance (lenient for Paddington)
                    title_lower = thread_title.lower()
                    has_paddington = 'paddington' in title_lower or 'peru' in title_lower
                    
                    if not has_paddington:
                        continue
                    
                    # Fetch comments
                    comments_url = f"https://www.reddit.com{thread_url}.json?limit=50&sort=top"
                    cr = requests.get(comments_url, headers=REDDIT_HEADERS, timeout=10)
                    time.sleep(1.5)
                    
                    if cr.status_code != 200:
                        continue
                    
                    try:
                        comment_data = cr.json()
                        if len(comment_data) < 2:
                            continue
                        
                        comments = comment_data[1].get('data', {}).get('children', [])
                        
                        for comment in comments:
                            if len(all_comments) >= max_comments:
                                break
                            
                            if comment.get('kind') != 't1':
                                continue
                            
                            comment_data_inner = comment.get('data', {})
                            comment_id = comment_data_inner.get('id', '')
                            
                            # Deduplicate
                            if comment_id in seen_comment_ids:
                                continue
                            seen_comment_ids.add(comment_id)
                            
                            body = comment_data_inner.get('body', '').strip()
                            score = comment_data_inner.get('score', 0)
                            
                            # Quality gates
                            if not body or body in ['[deleted]', '[removed]']:
                                continue
                            if score < 1:
                                continue
                            if len(body) < 40:
                                continue
                            
                            # Relevance check
                            relevant, rel_score = is_relevant(
                                body, config['title'], config['year'], threshold=0.05
                            )
                            
                            if not relevant:
                                continue
                            
                            all_comments.append({
                                "text": body,
                                "score": score,
                                "subreddit": subreddit,
                                "thread_title": thread_title,
                                "query": query,
                                "relevance_score": rel_score
                            })
                            
                    except Exception as e:
                        continue
                        
            except Exception as e:
                continue
    
    print(f"  Total Paddington Reddit comments: {len(all_comments)}")
    return all_comments
