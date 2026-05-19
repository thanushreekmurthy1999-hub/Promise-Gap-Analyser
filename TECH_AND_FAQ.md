# Promise Gap Analyser — Technology & FAQ

Single reference for **what this project is built with** and **questions people often ask**.

---

## Technology stack

### Core language & runtime

| Item | Role |
|------|------|
| **Python 3** (3.9+ recommended) | Scrapers, cleaning, embeddings, gap scoring, verdict scripts, HTTP server |
| **Shell** | One-off data fixes, venv setup |

### Data collection (scraping & APIs)

| Technology | Role |
|------------|------|
| **requests** | HTTP to TMDB, Wikipedia, Reddit, YouTube pages |
| **BeautifulSoup4** | HTML parsing (e.g. Wikipedia) |
| **youtube-transcript-api** | YouTube trailer captions / transcripts |
| **TMDB API** | Film metadata, taglines, overviews, user reviews |
| **Reddit** (search / JSON) | Posts and comments for the delivery corpus |
| **Apify** (optional / attempted) | IMDb, Letterboxd when direct access is hard |
| **python-dotenv** | Load `ANTHROPIC_API_KEY`, `TMDB_API_KEY`, etc. from `.env` |

### NLP & machine learning

| Technology | Role |
|------------|------|
| **Sentence Transformers** | `all-MiniLM-L6-v2` — turn text into dense vectors (embeddings) |
| **PyTorch** | Backend for the embedding model (pulled in via sentence-transformers) |
| **scikit-learn** | `KMeans` — cluster embedded chunks to form topic-style distributions |
| **NumPy** | Vector math for means, distributions |
| **SciPy** | `jensenshannon` — Jensen–Shannon distance between topic distributions |

**Gap score (as implemented in code):**

- Build topic distributions from **KMeans** labels on **MiniLM** embeddings (promise vs delivery, separately per film).
- **JSD (×100):** compare those two discrete distributions.
- **Embedding gap (×100):** cosine-style distance between **centroids** of promise vs delivery embeddings.
- **Composite:** `0.85 × JSD_component + 0.15 × embedding_component` (rounded).

### LLM (verdicts)

| Technology | Role |
|------------|------|
| **Anthropic API** | `claude-sonnet-4-20250514` in `pipeline/verdict.py` — structured marketing judgment (JSON) |
| **anthropic** Python SDK | API calls from `verdict.py` / `claude_verdict.py` |

### Data storage & formats

| Item | Role |
|------|------|
| **JSON** | `data/raw/*_marketing.json`, `data/raw/*_reviews.json`, `data/processed/*_result.json` |
| **Plain text** | README, this file |

### Web UI & server

| Technology | Role |
|------------|------|
| **Vanilla HTML / CSS / JavaScript** | Single-page `index.html` (dark theme, charts, API fetch) |
| **Google Fonts** (Inter, Fraunces, Bebas Neue, JetBrains Mono) | Typography |
| **Python `http.server` + `HTTPServer`** | `server.py` — static files + `/api/films`, `/api/film/<slug>` (default port **5001**) |
| **SVG** | Gauge, scatter plot in the browser |

### Configuration & project layout

| Item | Role |
|------|------|
| **`config.py`** | `FILMS_SCRAPE_CONFIG` — per-film YouTube IDs, Wikipedia slugs, Reddit queries, IMDb IDs |
| **`pipeline/`** | `cleaner`, `embedder`, `gap_scorer`, `verdict`, `claude_verdict` |
| **`scrapers/`** | YouTube, Wikipedia, TMDB, Reddit, optional IMDb/Letterboxd helpers |
| **`main.py`** | CLI entry to run structured verdicts |

### Optional / roadmap (not the core “implemented” path)

- **VADER, ABSA, BERTopic, RAG, ChromaDB, LDA** — may appear in older docs or UI copy; the **shipped** scoring path is **KMeans on MiniLM + JSD + centroid gap** unless you add those libraries explicitly.
- **TikTok / influencer / paid social** — not in the default scraper set.

---

## FAQ

### What does this project do?

It compares **what marketing said** (trailers, TMDB, Wikipedia) with **what audiences said** (reviews, Reddit) and outputs a **numeric gap**, optional **RT/CinemaScore** context, and a **Claude-written** marketing-style verdict (labels, recommendations).

### What is the main KPI?

The **Gap Score (0–100)**: a **weighted mix** of **topic-divergence (JSD on KMeans-based distributions)** and **semantic centroid distance** between promise and delivery embeddings.

### Does it use BERTopic / LDA in production code?

**No** — not in the `gap_scorer` path. Topics come from **KMeans** on **MiniLM** embeddings. Any slide or doc that still says BERTopic/LDA should be updated to match the repo (or the code should be upgraded to match the slide).

### Does it use VADER for sentiment in the Python pipeline?

**Not by default** — the repo’s verdict prompts may reference sentiment fields from JSON; those come from your **processed** data / pipeline design, not a mandatory VADER import in the gap scorer.

### Which APIs or keys do I need?

- **`ANTHROPIC_API_KEY`** — to generate or refresh Claude verdicts.  
- **`TMDB` key** (if your scrapers use TMDB) — set as your project expects (often in `.env`).  
- **Reddit** — depends on your scraper (official API with token vs public JSON patterns).

### How do I run the dashboard?

1. `cd promise-gap-analyzer`  
2. `python server.py`  
3. Open **http://localhost:5001**

### Why does a film’s gap not match my intuition?

- **Corpus size** — thin promise or delivery data moves the **embedding** leg more.  
- **Controversy** — people may talk about the *same* film title (low keyword mismatch) but opposite sentiment.  
- **Time window** — reviews are from a slice of release buzz, not “forever” reception.  
- **Language** — pipeline is **English-biased** in practice.

### Can I add another film?

Yes: extend **`FILMS_SCRAPE_CONFIG`**, run scrapers, then cleaning → embed → gap → (optional) `main.py` / `claude_verdict` to build `data/processed/<slug>_result.json` in the shape the **UI and server** expect.

### Is the data “legal to scrape” for production?

**Research / personal use** is different from **commercial** use. Public APIs and ToS (Reddit, IMDb, YouTube) matter. The README’s **Risks** section covers licensing; treat production as a **separate** legal product decision.

### What if Claude returns invalid JSON?

`pipeline/verdict.py` has **`_fallback_verdict()`** — rule-based labels and short text if the API fails or JSON is malformed.

### What port does the server use?

**5001** (see `server.py`). If “address in use,” stop the old process or change the port in code.

### How do I update only the UI text?

Edit **`index.html`** in `promise-gap-analyzer/` (or whichever copy `server.py` serves). Keep API field names in sync with `data/processed/*_result.json` and `server.py` responses.

### Where is “ground truth” for accuracy (e.g. 80% vs experts)?

**Not automated in the repo** — you’d add a labeled dataset and a small evaluation script. Good for a **roadmap** KPI, not a current built-in metric.

### Single sentence for an exec?

**“We score how much studio language and audience language diverge—using sentence embeddings, clustering, Jensen–Shannon distance, and an AI narrative—with Rotten Tomatoes and CinemaScore as context.”**

---

*Last updated to reflect the KMeans + MiniLM + JSD + centroid implementation and the `server.py` + `index.html` UI path.*
