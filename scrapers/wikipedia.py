"""Wikipedia marketing section scraper with relevance verification."""

import re
import requests
from scrapers.verify import is_relevant


def scrape_wikipedia_marketing(film_slug: str, config: dict) -> str:
    """
    Fetch Wikipedia page and extract only the Marketing and
    Release sections. Verify the content is about the actual film.
    Discard anything that is not.
    """
    print(f"  Fetching Wikipedia: {config['wikipedia_page']}")
    
    try:
        headers = {
            'User-Agent': 'PromiseGapAnalyser/1.0 (research project; non-commercial)'
        }
        r = requests.get('https://en.wikipedia.org/w/api.php', params={
            'action': 'parse',
            'page': config['wikipedia_page'],
            'prop': 'wikitext',
            'format': 'json'
        }, headers=headers, timeout=10)
        
        if r.status_code != 200:
            print(f"  ERROR: Wikipedia returned {r.status_code}")
            return ""
        
        data = r.json()
        if 'error' in data:
            print(f"  ERROR: Wikipedia page not found: {data['error']}")
            return ""
        
        wikitext = data['parse']['wikitext']['*']
        
        # Extract marketing-related sections
        # Look for multiple possible section names
        target_sections = ['marketing', 'release', 'promotion', 'campaign', 
                          'production', 'development', 'advertising', 'trailer',
                          'promotional', 'media', 'publicity', 'box office']
        
        extracted_sections = []
        current_section = None
        current_text = []
        
        for line in wikitext.split('\n'):
            # Detect section headers == Section Name ==
            section_match = re.match(r'==+\s*(.+?)\s*==+', line)
            if section_match:
                # Save previous section if it was a target
                if current_section and current_text:
                    section_content = ' '.join(current_text).strip()
                    if len(section_content) > 100:
                        extracted_sections.append(section_content)
                
                current_section = section_match.group(1).lower()
                current_text = []
            elif current_section and any(
                t in current_section for t in target_sections
            ):
                # Clean wikitext markup from line
                clean_line = re.sub(r'\[\[([^\]|]+\|)?([^\]]+)\]\]',
                                   r'\2', line)
                clean_line = re.sub(r'\{\{[^}]+\}\}', '', clean_line)
                clean_line = re.sub(r"'{2,}", '', clean_line)
                clean_line = re.sub(r'<[^>]+>', '', clean_line)
                clean_line = clean_line.strip()
                if clean_line:
                    current_text.append(clean_line)
        
        # Save last section
        if current_section and current_text:
            section_content = ' '.join(current_text).strip()
            if len(section_content) > 100:
                extracted_sections.append(section_content)
        
        if not extracted_sections:
            print(f"  WARNING: No marketing/release sections found in Wikipedia")
            return ""
        
        combined = ' '.join(extracted_sections)
        
        # Verify the Wikipedia content is about the actual film
        relevant, score = is_relevant(
            combined,
            config['title'],
            config['year'],
            threshold=0.25
        )
        
        if not relevant:
            print(f"  DISCARD Wikipedia: relevance score {score}")
            return ""
        
        print(f"  KEEP Wikipedia: score {score}, {len(combined)} chars")
        return combined
        
    except Exception as e:
        print(f"  ERROR Wikipedia: {e}")
        return ""
