# Promise Gap Analyzer

4-stage NLP pipeline quantifying the gap between film marketing promises and audience reception, validated against CinemaScore exit poll data across 7 major releases.

## Problem
Studios spend enormous resources crafting marketing narratives — trailers, posters, taglines — but these narratives don't always align with how audiences actually experience the film. This project quantifies the *promise gap* between studio marketing claims and audience reception, surfacing patterns that correlate with real exit-poll data.

## Pipeline

### Stage 1 — Sentence Embeddings
Generate vector embeddings for marketing materials (trailers, posters, taglines, press) and audience reviews using MiniLM sentence transformers.

### Stage 2 — Thematic Clustering
K-Means clustering on each side independently to identify thematic clusters in marketing vs. reception language.

### Stage 3 — Distribution Comparison
Jensen-Shannon Divergence (JSD) scoring to quantify alignment between marketing cluster distributions and reception cluster distributions. Higher JSD = larger promise gap.

### Stage 4 — Diagnostic Verdicts
LLM (Claude API) generates qualitative diagnostic verdicts characterizing the type and severity of each promise gap — e.g., "misframed genre," "overpromised emotional intensity," "underrepresented runtime."

## Validation
Promise gap scores were validated against CinemaScore exit poll grades, confirming that the patterns surfaced by the pipeline align with real audience reaction.

## Tech stack
- **Language:** Python
- **Embeddings:** Sentence Transformers (MiniLM)
- **Clustering:** scikit-learn (KMeans)
- **LLM:** Claude API
- **Metric:** Jensen-Shannon Divergence

## How to run
1. Clone the repo
2. `pip install -r requirements.txt`
3. Set environment variable: `ANTHROPIC_API_KEY`
4. Run `python main.py` (or the notebook)

## Films analyzed
7 major theatrical releases (2024–2025). See `results/` for per-film breakdowns.
