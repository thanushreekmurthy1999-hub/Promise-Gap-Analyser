#!/usr/bin/env python3
"""
Structured Marketing Verdict Generator using Claude.

Produces studio-facing marketing judgments that answer:
1. What did we promise?
2. What did audiences receive?
3. What did we get right or wrong — and what should we change?
"""

import os
import json


# The six marketing verdict labels
MARKETING_VERDICT_LABELS = {
    "GOT_IT_RIGHT": (
        "Promise matched delivery. "
        "Audiences received what marketing set up."
    ),
    "UNDERSOLD_IT": (
        "Film was better than marketing suggested. "
        "Audiences were pleasantly surprised."
    ),
    "OVERSOLD_IT": (
        "Marketing promised more than the film delivered. "
        "Audiences felt let down."
    ),
    "HID_SOMETHING": (
        "A key element of the film was deliberately "
        "concealed or downplayed in marketing."
    ),
    "LOST_NARRATIVE": (
        "Outside discourse — controversy, politics, "
        "casting debate — drowned out the marketing message."
    ),
    "INSUFFICIENT_DATA": (
        "Data quality too low for a confident judgment. "
        "Treat as indicative only."
    )
}


def get_claude_verdict(
    film_config: dict,
    gap_result: dict,
    sentiment: dict,
    rule_verdict: str
) -> dict:
    """
    Call Claude to produce a structured marketing judgment.
    
    Returns a dict with these keys:
    - what_was_promised: str (one sentence)
    - what_was_received: str (one sentence)  
    - marketing_label: str (one of the six labels)
    - marketing_explanation: str (two sentences max)
    - recommendation: str (one specific actionable sentence)
    - lost_audience: str (one sentence)
    - full_verdict: str (combined prose for UI display)
    """
    
    import anthropic
    
    client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    
    # Build keyword strings
    promise_kw = ', '.join([
        f"'{k}'" for k in gap_result.get('promise_keywords', [])[:6]
    ])
    delivery_kw = ', '.join([
        f"'{k}'" for k in gap_result.get('delivery_keywords', [])[:6]
    ])
    
    # Sentiment label
    sentiment_mean = sentiment.get('mean', 0)
    if sentiment_mean > 0.2:
        sentiment_label = "strongly positive"
    elif sentiment_mean > 0.05:
        sentiment_label = "mildly positive"
    elif sentiment_mean > -0.05:
        sentiment_label = "neutral"
    elif sentiment_mean > -0.2:
        sentiment_label = "mildly negative"
    else:
        sentiment_label = "strongly negative"
    
    # Data quality flag
    is_low_quality = film_config.get(
        'data_quality_flag', ''
    ) == 'low_sample_delivery_corpus'
    
    quality_note = (
        "\n\nIMPORTANT: This film has a low-quality data flag "
        "(thin corpus, synthetic promise side). Choose "
        "INSUFFICIENT_DATA as the marketing label and be "
        "explicitly cautious in your language."
        if is_low_quality else ""
    )
    
    prompt = f"""You are a film marketing analyst reviewing whether
a studio's marketing campaign accurately represented their film.

You have quantitative evidence from an NLP pipeline that compared
marketing language against audience reviews.

FILM: {film_config['title']} ({film_config['year']})

QUANTITATIVE SIGNALS:
- Gap Score: {gap_result['composite']}/100
  (0 = perfect alignment, 100 = complete divergence)
- Topic Divergence (JSD): {gap_result['topic_divergence']}
- Semantic Distance: {gap_result['centroid_distance']}
- Audience Sentiment: {sentiment_mean} ({sentiment_label})
- Positive Reviews: {sentiment.get('positive_ratio', 0)*100:.0f}%
- Negative Reviews: {sentiment.get('negative_ratio', 0)*100:.0f}%
- Rotten Tomatoes Score: {film_config.get('rt_score', 'N/A')}%
- Audience Score: {film_config.get('audience_score', 'N/A')}%
- CinemaScore: {film_config.get('cinemascore', 'N/A')}

WHAT MARKETING TALKED ABOUT (promise keywords):
{promise_kw}

WHAT AUDIENCES TALKED ABOUT (delivery keywords):
{delivery_kw}

RULE-BASED VERDICT: {rule_verdict}
{quality_note}

---

Your task is to produce a structured marketing judgment.
Respond ONLY with a valid JSON object. No preamble, no explanation
outside the JSON, no markdown code fences.

The JSON must have exactly these keys:

{{
  "what_was_promised": "One sentence. What story did the marketing tell? Start with the studio name if known.",
  "what_was_received": "One sentence. What did audiences actually discuss and experience?",
  "marketing_label": "Exactly one of: GOT_IT_RIGHT | UNDERSOLD_IT | OVERSOLD_IT | HID_SOMETHING | LOST_NARRATIVE | INSUFFICIENT_DATA",
  "marketing_explanation": "Two sentences maximum. Why does this label apply? Cite specific keywords as evidence.",
  "recommendation": "One specific, actionable sentence. If you could change one thing about how this film was marketed, what would it be? Be concrete — name the specific element to change.",
  "lost_audience": "One sentence. Which audience segment was most let down by the gap between promise and delivery, and why?",
  "full_verdict": "Three to four sentences combining all of the above into readable prose for a studio executive. Plain English. No jargon. No mention of NLP, JSD, or technical terms."
}}

Rules:
- full_verdict must be readable by a non-technical person
- marketing_label must be exactly one of the six options
- recommendation must name a specific change, not generic advice
  (BAD: 'consider different marketing angles'
   GOOD: 'release a secondary trailer foregrounding the musical 
          numbers six weeks before opening')
- Do not use the words 'JSD', 'centroid', 'corpus', 'NLP',
  'embedding', or 'pipeline' anywhere in any field
- Do not exceed the sentence limits per field
- If sentiment is positive but gap is high, that is
  UNDERSOLD_IT not OVERSOLD_IT
- If controversy keywords dominate delivery, that is
  LOST_NARRATIVE not OVERSOLD_IT"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw = response.content[0].text.strip()
        
        # Strip markdown fences if Claude added them anyway
        if raw.startswith('```'):
            raw = raw.split('```')[1]
            if raw.startswith('json'):
                raw = raw[4:]
        raw = raw.strip()
        
        verdict_dict = json.loads(raw)
        
        # Validate all required keys present
        required_keys = [
            'what_was_promised', 'what_was_received',
            'marketing_label', 'marketing_explanation',
            'recommendation', 'lost_audience', 'full_verdict'
        ]
        for key in required_keys:
            if key not in verdict_dict:
                raise ValueError(f"Missing key in Claude response: {key}")
        
        # Validate marketing_label is one of the six
        valid_labels = [
            'GOT_IT_RIGHT', 'UNDERSOLD_IT', 'OVERSOLD_IT',
            'HID_SOMETHING', 'LOST_NARRATIVE', 'INSUFFICIENT_DATA'
        ]
        if verdict_dict['marketing_label'] not in valid_labels:
            verdict_dict['marketing_label'] = 'INSUFFICIENT_DATA'
        
        return verdict_dict
        
    except json.JSONDecodeError as e:
        print(f"  WARNING: Claude returned invalid JSON: {e}")
        print(f"  Raw response: {raw[:200]}")
        return _fallback_verdict(film_config, gap_result,
                                sentiment, rule_verdict)
    
    except Exception as e:
        print(f"  WARNING: Claude API error: {e}")
        return _fallback_verdict(film_config, gap_result,
                                sentiment, rule_verdict)


def _fallback_verdict(
    film_config: dict,
    gap_result: dict,
    sentiment: dict,
    rule_verdict: str
) -> dict:
    """
    Rule-based fallback if Claude API fails or returns bad JSON.
    Produces a minimal but valid verdict dict.
    """
    gap = gap_result['composite']
    sent = sentiment.get('mean', 0)
    
    if gap < 20 and sent > 0.1:
        label = 'GOT_IT_RIGHT'
        explanation = (
            "Marketing and audience vocabulary are closely aligned. "
            "Audiences received what the campaign promised."
        )
    elif gap >= 25 and sent > 0.2:
        label = 'UNDERSOLD_IT'
        explanation = (
            "High gap with positive sentiment suggests the film "
            "exceeded its marketing. Audiences were pleasantly surprised."
        )
    elif gap >= 25 and sent < -0.05:
        label = 'OVERSOLD_IT'
        explanation = (
            "High gap with negative sentiment suggests marketing "
            "misrepresented the film. Audiences felt let down."
        )
    else:
        label = 'INSUFFICIENT_DATA'
        explanation = (
            "Gap score and sentiment signals are ambiguous. "
            "Manual review recommended."
        )
    
    return {
        "what_was_promised": (
            f"Marketing positioned {film_config['title']} around: "
            f"{', '.join(gap_result.get('promise_keywords', [])[:3])}."
        ),
        "what_was_received": (
            f"Audiences discussed: "
            f"{', '.join(gap_result.get('delivery_keywords', [])[:3])}."
        ),
        "marketing_label": label,
        "marketing_explanation": explanation,
        "recommendation": (
            "Review the gap between promise and delivery keywords "
            "to identify specific messaging adjustments."
        ),
        "lost_audience": (
            "Unable to determine without Claude API response."
        ),
        "full_verdict": (
            f"{film_config['title']} has a gap score of "
            f"{gap_result['composite']}. "
            f"Rule-based classification: {rule_verdict}. "
            f"{explanation}"
        )
    }
