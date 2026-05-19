# The Promise Gap Analyser

## Complete Project Documentation

---

## Table of Contents

1. [What Is This Project?](#what-is-this-project)
2. [The Problem We're Solving](#the-problem-were-solving)
3. [How It Works (The Simple Version)](#how-it-works-the-simple-version)
4. [The Four-Stage Pipeline](#the-four-stage-pipeline)
5. [Data Sources Explained](#data-sources-explained)
6. [The Gap Score Explained](#the-gap-score-explained)
7. [The Six Marketing Labels](#the-six-marketing-labels)
8. [The Seven Films We Analyzed](#the-seven-films-we-analyzed)
9. [Key Findings](#key-findings)
10. [How to Run the Project](#how-to-run-the-project)
11. [Project Structure](#project-structure)
12. [Technical Details (For Developers)](#technical-details-for-developers)
13. [Frequently Asked Questions](#frequently-asked-questions)
14. [Limitations and Caveats](#limitations-and-caveats)

---

## What Is This Project?

The Promise Gap Analyser is a tool that measures whether movie studios keep their marketing promises.

When a film studio releases trailers and marketing materials, they're making a promise to audiences: "This is what our movie is about. This is the experience you'll have." Sometimes that promise is kept. Sometimes it isn't.

**This tool uses artificial intelligence to measure the gap between what was promised and what was delivered.**

Think of it like a "truth meter" for movie marketing. A low score means the studio was honest. A high score means there was a significant disconnect between marketing and reality.

---

## The Problem We're Solving

### The Audience Perspective

Have you ever watched a movie trailer, gotten excited, bought a ticket, and then felt disappointed because the movie was nothing like what you expected? You're not alone. This happens constantly, and it costs audiences:

- **Time** — 2+ hours watching something they didn't sign up for
- **Money** — Ticket prices, snacks, babysitters
- **Trust** — Next time, they're less likely to believe trailers

### The Studio Perspective

Studios also suffer when there's a promise-delivery gap:

- **Bad word of mouth** — Disappointed audiences tell their friends
- **Poor CinemaScore** — Exit polls tank when expectations aren't met
- **Box office drop-off** — Second weekend crashes when word spreads
- **Franchise damage** — One bad experience can poison future films

### What We Built

A system that quantifies this gap with actual data, so studios can:

1. **Measure** how well their marketing matched the film
2. **Identify** specific areas where messaging went wrong
3. **Learn** from successes and failures
4. **Improve** future marketing campaigns

---

## How It Works (The Simple Version)

The system compares two sets of text:

### The "Promise" (Marketing Side)

What the studio said the movie would be:
- Words spoken in trailers
- Official descriptions and taglines
- Marketing materials on Wikipedia

### The "Delivery" (Audience Side)

What audiences actually experienced:
- Reviews posted after watching
- Reddit discussions about the film
- Social media reactions

### The Comparison

We use AI to find the main themes in each set of text, then measure how different they are.

**Example:**

| Film | Promise Themes | Delivery Themes | Gap |
|------|---------------|-----------------|-----|
| Joker 2 | "dark", "chaos", "villain", "psychological" | "boring", "musical", "confused", "disappointed" | HIGH |
| Wicked | "musical", "singing", "Broadway", "spectacle" | "amazing", "vocals", "stunning", "musical" | LOW |

When the themes match (like Wicked), the gap is low. When they're completely different (like Joker 2), the gap is high.

---

## The Four-Stage Pipeline

The system processes data through four stages:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   COLLECT   │ → │    CLEAN    │ → │    MODEL    │ → │  DIAGNOSE   │
│             │    │             │    │             │    │             │
│ Gather text │    │ Remove junk │    │ Find themes │    │ AI verdict  │
│ from sources│    │ and noise   │    │ measure gap │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

### Stage 1: COLLECT

**What happens:** We gather text from multiple sources.

**For the Promise side (marketing):**
- Download transcripts from official YouTube trailers
- Scrape marketing sections from Wikipedia
- Pull official descriptions from TMDB (The Movie Database)

**For the Delivery side (audience reactions):**
- Collect posts and comments from Reddit (r/movies, r/boxoffice, etc.)
- Gather user reviews from TMDB
- Attempt to collect reviews from IMDb and Letterboxd

### Stage 2: CLEAN

**What happens:** We clean up the raw text to remove noise.

**What we remove:**
- URLs and links
- Reddit usernames (u/someone) and subreddit names (r/movies)
- Email addresses
- Excessive punctuation (!!!! becomes !)
- Special characters and emojis
- Very short texts (less than 30 characters)

**What we keep:**
- Actual opinions and descriptions
- Meaningful sentences about the film
- Text that passes our relevance check

**Why this matters:** Raw internet text is messy. People include links, mention other users, go off-topic. We filter down to just the signal — actual statements about the film.

### Stage 3: MODEL

**What happens:** We use AI to understand what the text is about and measure the gap.

**Step 3a: Create Embeddings**

We convert each piece of text into numbers using a language model called "MiniLM-L6-v2". This model reads text and outputs a list of 384 numbers that capture the meaning.

*Why?* Computers can't understand words directly, but they can compare numbers. Two sentences with similar meanings will have similar numbers.

**Step 3b: Find Topic Clusters**

We group similar texts together using a technique called K-Means clustering. This finds the main "topics" being discussed.

For example, in Joker 2:
- Marketing cluster: "chaos", "madness", "villain", "dark"
- Audience cluster: "boring", "musical", "songs", "confused"

**Step 3c: Measure the Gap**

We calculate two metrics:

1. **Jensen-Shannon Distance (JSD):** Compares the topic distributions between promise and delivery. If marketing talked 80% about "action" but audiences talked 80% about "boring", that's a high JSD.

2. **Embedding Gap:** Compares the average meaning of all promise text versus all delivery text. If they point in very different directions, the gap is high.

**Step 3d: Combine into Gap Score**

Final formula:
```
Gap Score = (85% × JSD) + (15% × Embedding Gap)
```

We weight JSD more heavily because it's more stable with smaller amounts of data.

### Stage 4: DIAGNOSE

**What happens:** Claude AI reviews all the metrics and writes a human-readable verdict.

**What Claude receives:**
- The Gap Score
- The topic keywords from each side
- Audience sentiment (positive/negative/neutral)
- Rotten Tomatoes score
- CinemaScore

**What Claude produces:**
- A marketing label (GOT_IT_RIGHT, OVERSOLD_IT, etc.)
- A one-sentence summary of what was promised
- A one-sentence summary of what was received
- A specific recommendation for how to fix the marketing
- Identification of which audience segment was most let down

**Rule-based safety net:** If Claude's response doesn't make sense (e.g., saying a positively-received film was "oversold"), we have automatic rules that override impossible combinations.

---

## Data Sources Explained

### Reproducing the Data

**Important:** Raw data is not included in this repository. You can recreate the dataset using the sources below.

All data collection scripts are in the `scrapers/` folder. Run `python main.py [film_slug]` to collect fresh data for any configured film.

### Promise Side Sources

| Source | What We Get | How We Get It | Where to Find |
|--------|-------------|---------------|---------------|
| **YouTube Trailers** | The actual words spoken in trailers (from captions) | youtube-transcript-api library | Official studio channels (Warner Bros, Universal, Disney, etc.) |
| **Wikipedia** | Marketing and Release sections describing how the film was promoted | Web scraping with BeautifulSoup | Film pages like `https://en.wikipedia.org/wiki/Joker:_Folie_à_Deux` |
| **TMDB** | Official studio synopsis and tagline | TMDB API | [The Movie Database](https://www.themoviedb.org/) - requires free API key |

### Delivery Side Sources

| Source | What We Get | How We Get It | Where to Find |
|--------|-------------|---------------|---------------|
| **Reddit** | Posts and comments from r/movies, r/boxoffice, and film-specific subreddits | Reddit API | [r/movies](https://reddit.com/r/movies), [r/boxoffice](https://reddit.com/r/boxoffice), film-specific subs |
| **TMDB Reviews** | User reviews with ratings | TMDB API | User review sections on film pages |
| **IMDb** | User reviews (when accessible) | Web scraping | [IMDb](https://www.imdb.com/) film review pages |

### Specific Film Data Sources

For each film analyzed, here are the direct links to primary sources:

#### Wicked (2024)
- **Trailers:** [Official Trailer 1](https://www.youtube.com/watch?v=6COmYeLsz4c), [Trailer 2](https://www.youtube.com/watch?v=lyY7LpeATTs)
- **Wikipedia:** [Wicked (film)](https://en.wikipedia.org/wiki/Wicked_(2024_film))
- **TMDB:** [Wicked on TMDB](https://www.themoviedb.org/movie/402431-wicked)
- **Reddit:** Search "Wicked" in r/movies and r/boxoffice

#### Joker: Folie à Deux (2024)
- **Trailers:** [Official Trailer](https://www.youtube.com/watch?v=xy8aJw1vYHo)
- **Wikipedia:** [Joker: Folie à Deux](https://en.wikipedia.org/wiki/Joker:_Folie_à_Deux)
- **TMDB:** [Joker 2 on TMDB](https://www.themoviedb.org/movie/889737-joker-folie-a-deux)
- **Reddit:** Search "Joker 2" or "Folie à Deux" in r/movies

#### Snow White (2025)
- **Trailers:** [Official Trailer](https://www.youtube.com/watch?v=VkqAGYA3_vY)
- **Wikipedia:** [Snow White (2025 film)](https://en.wikipedia.org/wiki/Snow_White_(2025_film))
- **TMDB:** [Snow White on TMDB](https://www.themoviedb.org/movie/420634-snow-white)
- **Reddit:** Search "Snow White" in r/movies and r/boxoffice

#### A Minecraft Movie (2025)
- **Trailers:** [Official Teaser](https://www.youtube.com/watch?v=5rlW3nGiMyU)
- **Wikipedia:** [A Minecraft Movie](https://en.wikipedia.org/wiki/A_Minecraft_Movie)
- **TMDB:** [Minecraft on TMDB](https://www.themoviedb.org/movie/558449-a-minecraft-movie)
- **Reddit:** Search "Minecraft Movie" in r/movies

#### Paddington in Peru (2024)
- **Trailers:** [Official Trailer](https://www.youtube.com/watch?v=QXbQlApdZns) (may be geo-restricted)
- **Wikipedia:** [Paddington in Peru](https://en.wikipedia.org/wiki/Paddington_in_Peru)
- **TMDB:** [Paddington in Peru on TMDB](https://www.themoviedb.org/movie/950782-paddington-in-peru)
- **Reddit:** Search "Paddington Peru" in r/movies

#### Lilo & Stitch (2025)
- **Trailers:** [Official Teaser](https://www.youtube.com/watch?v=BwQX1Q-_cUU)
- **Wikipedia:** [Lilo & Stitch (2025 film)](https://en.wikipedia.org/wiki/Lilo_%26_Stitch_(2025_film))
- **TMDB:** [Lilo & Stitch on TMDB](https://www.themoviedb.org/movie/995803-lilo-stitch)
- **Reddit:** Search "Lilo Stitch" in r/movies

#### Thunderbolts* (2025)
- **Trailers:** [Official Trailer](https://www.youtube.com/watch?v=mEhLYqPZgqI)
- **Wikipedia:** [Thunderbolts (film)](https://en.wikipedia.org/wiki/Thunderbolts_(film))
- **TMDB:** [Thunderbolts on TMDB](https://www.themoviedb.org/movie/986555-thunderbolts)
- **Reddit:** Search "Thunderbolts" in r/marvelstudios and r/movies

### Why These Sources?

**YouTube Trailers:** This is literally what studios show audiences before the film. The words spoken, the tone, the emphasis — it's the clearest expression of the marketing promise.

**Wikipedia Marketing Sections:** Journalists and editors compile how the film was marketed, including press releases, premiere events, and promotional campaigns.

**Reddit:** Unlike professional reviews, Reddit captures raw audience reactions — what regular people actually thought and discussed. It's unfiltered.

**TMDB Reviews:** Another source of genuine audience opinions, often more detailed than social media.

---

## The Gap Score Explained

### The Scale (0-100)

| Score Range | Interpretation | What It Means |
|-------------|----------------|---------------|
| **0-15** | Excellent alignment | Marketing perfectly matched the film |
| **15-22** | Good alignment | Minor differences, mostly accurate |
| **22-28** | Moderate gap | Noticeable differences audiences may notice |
| **28-35** | Significant gap | Marketing meaningfully misrepresented something |
| **35-50** | Severe gap | Major disconnect between promise and delivery |
| **50+** | Extreme gap | Almost completely different product than advertised |

### What Affects the Score

**Things that increase the gap:**
- Marketing emphasizes action, audiences discuss boredom
- Trailers hide a major element (like it being a musical)
- The tone promised doesn't match the tone delivered
- Controversy dominates discussion instead of the actual film

**Things that decrease the gap:**
- Marketing themes match audience themes
- Audiences discuss what was advertised
- Reviews validate the marketing's claims
- Word-of-mouth matches trailer impressions

### Important Notes

**A low gap doesn't mean the film is good.** It means audiences got what they expected. A film can be accurately marketed as mediocre, have a low gap, but still get bad reviews.

**A high gap doesn't mean the film is bad.** It could mean the film was *better* than expected (undersold) or *different* than expected (which can be good or bad).

---

## The Six Marketing Labels

After calculating the gap, Claude assigns one of six labels:

### GOT_IT_RIGHT ✓

**Meaning:** The marketing accurately represented the film.

**When assigned:** Low gap score, audience themes match promise themes.

**Example:** Wicked — marketed as a grand Broadway musical, delivered exactly that.

---

### UNDERSOLD_IT ↑

**Meaning:** The film was better than marketing suggested.

**When assigned:** High gap but positive audience sentiment.

**Example:** Audiences were pleasantly surprised; the film exceeded expectations.

---

### OVERSOLD_IT ↓

**Meaning:** Marketing promised more than the film delivered.

**When assigned:** High gap with negative audience sentiment.

**Example:** Trailers made it look more exciting/funny/dramatic than it actually was.

---

### HID_SOMETHING 🔒

**Meaning:** A key element was deliberately concealed.

**When assigned:** Major element in delivery that wasn't in promise.

**Example:** Joker 2 — trailers hid that it was a musical with 16 song numbers.

---

### LOST_NARRATIVE 📢

**Meaning:** Outside discourse drowned out the marketing message.

**When assigned:** Controversy keywords dominate delivery.

**Example:** Snow White — casting controversy and CGI debates overwhelmed actual film discussion.

---

### INSUFFICIENT_DATA ⚠️

**Meaning:** Not enough data for a confident judgment.

**When assigned:** Very thin corpus, unreliable sources, or conflicting signals.

**Example:** Paddington — trailer was geo-blocked, limiting our marketing data.

---

## The Seven Films We Analyzed

### 1. Wicked (2024)
- **Gap Score:** 20.7
- **Label:** UNDERSOLD_IT
- **What Happened:** Universal promised a grand Broadway musical with Ariana Grande and Cynthia Erivo. Audiences received exactly that, but were even more impressed than expected by the vocal performances. The alignment was near-perfect.

### 2. A Minecraft Movie (2025)
- **Gap Score:** 20.8
- **Label:** UNDERSOLD_IT
- **What Happened:** Warner Bros marketed it as a silly Jack Black adventure. Audiences found it funnier and more entertaining than the trailers suggested. Self-aware marketing that didn't oversell worked in their favor.

### 3. Snow White (2025)
- **Gap Score:** 23.3
- **Label:** LOST_NARRATIVE
- **What Happened:** Disney promised a magical fairy tale remake. But audience discussion was dominated by controversy — casting debates, CGI criticism, and political discourse. The actual film got lost in the noise.

### 4. Lilo & Stitch (2025)
- **Gap Score:** 23.5
- **Label:** UNDERSOLD_IT
- **What Happened:** Disney marketed the "ohana" family theme. Audiences found it sweeter and more heartwarming than expected, praising the faithful adaptation.

### 5. Thunderbolts* (2025)
- **Gap Score:** 27.1
- **Label:** HID_SOMETHING
- **What Happened:** Marvel marketed it as an action team-up. But the film featured significant mental health themes that weren't in trailers. Audiences who came for action were surprised by the emotional depth.

### 6. Joker: Folie à Deux (2024)
- **Gap Score:** 36.1
- **Label:** HID_SOMETHING
- **What Happened:** Warner Bros marketed it as a dark psychological thriller sequel. They completely hid that it was a musical with 16 song numbers. Audiences felt deceived. The film earned a rare "D" CinemaScore.

### 7. Paddington in Peru (2024)
- **Gap Score:** 40.5
- **Label:** UNDERSOLD_IT
- **What Happened:** Despite the high gap score (caused by limited data), audiences loved it. The Paddington brand delivered its signature charm, and word-of-mouth was excellent.

---

## Key Findings

### What We Learned

**1. Hiding major elements backfires catastrophically**

Joker 2's decision to hide the musical format led to the biggest disconnect in our dataset. Audiences felt betrayed, not surprised. If your film is a musical, *lead with that*.

**2. Accurate marketing leads to audience satisfaction**

Wicked's near-perfect alignment shows that when you market honestly, audiences arrive with correct expectations and leave satisfied. No tricks needed.

**3. Controversy can hijack your entire campaign**

Snow White's moderate gap score is misleading. The actual film wasn't discussed — the controversy was. Studios need strategies to redirect conversation back to the product.

**4. Underselling can be a winning strategy**

Multiple films (Minecraft, Lilo & Stitch, Paddington) scored "UNDERSOLD_IT" — and audiences responded positively. Managing expectations downward can create pleasant surprises.

**5. Mental health themes need careful positioning**

Thunderbolts* surprised audiences with its emotional depth. Some appreciated it; others felt misled. If your film has unexpected depth, consider secondary marketing that signals this to receptive audiences.

---

## How to Run the Project

### Prerequisites

You need:
- Python 3.9 or higher
- An Anthropic API key (for Claude)

### Step 1: Install Dependencies

Open your terminal and navigate to the project folder:

```bash
cd promise-gap-analyzer
```

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Mac/Linux
# or
venv\Scripts\activate  # On Windows
```

Install required packages:

```bash
pip install -r requirements.txt
```

### Step 2: Set Up API Keys

Create a file called `.env` in the project folder:

```
ANTHROPIC_API_KEY=your-api-key-here
TMDB_API_KEY=your-tmdb-key-here
```

### Step 3: Run the Analysis

To analyze a single film:

```bash
python main.py joker_2
```

To analyze all seven films:

```bash
python main.py --all
```

### Step 4: View Results

Start the web server:

```bash
python server.py
```

Open your browser to:

```
http://localhost:5001
```

You'll see an interactive dashboard with all the films and their analysis.

---

## Project Structure

```
promise-gap-analyzer/
│
├── config.py              # Film configurations (trailer IDs, Wikipedia pages, etc.)
├── server.py              # Web server for the UI
├── main.py                # Main entry point to run analysis
│
├── scrapers/              # Data collection scripts
│   ├── youtube.py         # Extracts trailer transcripts
│   ├── wikipedia.py       # Scrapes marketing sections
│   ├── tmdb_marketing.py  # Gets official descriptions
│   ├── tmdb_reviews.py    # Collects user reviews
│   ├── reddit.py          # Gathers Reddit discussions
│   └── verify.py          # Checks if text is relevant to the film
│
├── pipeline/              # Data processing scripts
│   ├── cleaner.py         # Removes noise from text
│   ├── embedder.py        # Converts text to numerical vectors
│   ├── gap_scorer.py      # Calculates the gap metrics
│   ├── verdict.py         # Claude prompt for structured verdicts
│   └── claude_verdict.py  # Runs the verdict generation
│
├── data/
│   ├── raw/               # Original scraped data
│   └── processed/         # Analysis results (JSON files)
│
└── index.html             # Web interface
```

---

## Technical Details (For Developers)

### Embedding Model

**Model:** all-MiniLM-L6-v2 from Sentence Transformers

**Why this model:**
- Fast (processes thousands of sentences quickly)
- Good quality (captures semantic meaning well)
- Small size (80MB, runs on any laptop)
- Well-tested for semantic similarity tasks

**Output:** 384-dimensional vectors

### Clustering Algorithm

**Method:** K-Means with k=5 topics

**Why K-Means:**
- Simple and reliable
- Works well with sentence embeddings
- Produces interpretable topic distributions

**Why not full BERTopic:**
- BERTopic requires more data to work well
- K-Means is sufficient for our 5-topic model
- Simpler = fewer things to go wrong

### Gap Calculation

**Jensen-Shannon Distance:**
```python
from scipy.spatial.distance import jensenshannon
jsd = jensenshannon(promise_distribution, delivery_distribution)
```

JSD ranges from 0 to 1, where 0 means identical distributions.

**Embedding Gap:**
```python
cosine_distance = 1 - cosine_similarity(mean_promise_embedding, mean_delivery_embedding)
```

Cosine distance ranges from 0 to 2, where 0 means identical vectors.

**Composite Score:**
```python
gap_score = 0.85 * (jsd * 100) + 0.15 * (embedding_gap * 100)
```

We weight JSD higher because it's more stable with small corpora.

### Claude Integration

**Model:** claude-sonnet-4-20250514

**Prompt design:** Structured JSON output with strict field requirements

**Fallback:** If Claude returns invalid JSON, we use rule-based classification

---

## Frequently Asked Questions

### "Can this system be fooled?"

Yes. If studios create fake positive reviews or manipulate Reddit discussions, our delivery data would be contaminated. We're measuring *reported* audience reactions, not ground truth.

### "Why only these seven films?"

These films represent a range of outcomes:
- Critical/commercial successes (Wicked)
- Controversial releases (Snow White)
- Major marketing failures (Joker 2)
- Beloved franchises (Paddington)
- Video game adaptations (Minecraft)

They give us variety to test the system.

### "How accurate are the scores?"

The scores are consistent and reproducible — run the same data twice, get the same result. Whether they capture "true" promise-delivery gap is harder to verify, since that's subjective.

We've validated against CinemaScore (exit poll data) and found correlation: films with high gaps tend to have lower CinemaScores.

### "Can I add new films?"

Yes. Add a new entry to `config.py` with:
- Film title and year
- YouTube trailer IDs
- Wikipedia page slug
- IMDB ID
- Reddit search query

Then run the scrapers and pipeline.

### "Why isn't [specific film] included?"

We focused on 2024-2025 releases where data was available. Older films often have geo-blocked trailers or archived Reddit discussions that are harder to access.

### "Does this work for TV shows?"

Not currently. The system assumes film-length marketing cycles. TV shows have different patterns (seasonal marketing, episode-by-episode reactions) that would need different handling.

---

## Limitations and Caveats

### Data Limitations

1. **Trailer geo-blocking:** Some trailers aren't available in all regions, limiting our transcript data (affected Paddington).

2. **Reddit bias:** Reddit users skew younger and more male than general audiences. Their reactions may not represent all moviegoers.

3. **Review timing:** We collect reviews from the first few weeks. Long-term reception may differ.

4. **Language:** We only analyze English-language content. International reception is not captured.

### Methodological Limitations

1. **Topic simplification:** We reduce rich discussions to 5 topics. Nuance is lost.

2. **Equal weighting:** All reviews count equally. A 1000-word thoughtful review counts the same as a 50-word rant.

3. **Sarcasm and irony:** The AI may misread sarcastic praise as genuine or vice versa.

4. **Context blindness:** We don't know if a negative review is from someone who watched the film or just joined the pile-on.

### Interpretation Caveats

1. **Gap ≠ Quality:** A low gap means accurate marketing, not good quality.

2. **Context matters:** A 25 gap score means different things for a blockbuster vs. an indie film.

3. **One metric isn't everything:** The gap score is one signal among many. It shouldn't be the sole basis for decisions.

---

## Risks and Mitigations

This section outlines the key risks facing the Promise Gap Analyser if deployed at scale, along with recommended mitigations.

### Risk 1: Data Provider Access

| Risk | Mitigation |
|------|------------|
| **Data providers (Letterboxd, Reddit) block API access or change Terms of Service** | Negotiate official data licensing agreements; build partnerships with review aggregators like Metacritic or Fandango |

**Current Status:** ⚠️ Not mitigated — we use direct API calls and scraping without formal agreements.

**Why it matters:** Reddit has already restricted API access (2023). Letterboxd has no public API. If these sources block access, our delivery corpus shrinks dramatically.

---

### Risk 2: Multilingual Content

| Risk | Mitigation |
|------|------------|
| **Topic models degrade on non-English or multilingual content as the tool scales globally** | Integrate multilingual NLP models (e.g., XLM-R); offer language-specific pipelines as a premium tier |

**Current Status:** ⚠️ Partially mitigated — we request `language=en-US` from APIs, but cannot analyze non-English markets.

**Why it matters:** International box office often exceeds domestic. A film can fail in the US but succeed in China, or vice versa. Without multilingual support, we miss half the picture.

---

### Risk 3: Internal Competition

| Risk | Mitigation |
|------|------------|
| **Studios already have internal analytics teams that resist buying external tools** | Position as an independent audit layer — internal teams may want to avoid surfacing bad marketing decisions to leadership |

**Current Status:** N/A — this is a business/positioning strategy, not a technical implementation.

**Why it matters:** Studios like Disney, Warner Bros, and Universal have massive data science teams. They may view this tool as redundant or threatening to internal metrics.

**Positioning strategy:** Frame the tool as an *independent external audit* that provides objectivity internal teams cannot. Internal teams have incentives to present positive results; an external tool doesn't.

---

### Risk 4: Legal and Terms of Service Compliance

| Risk | Mitigation |
|------|------------|
| **Scraping public review platforms at commercial scale violates ToS and exposes the company to litigation** | Secure licensed data partnerships before commercial launch; engage entertainment IP lawyers to audit all data collection methods |

**Current Status:** ❌ Not mitigated — we scrape directly without licenses.

**Why it matters:** 
- IMDb's ToS explicitly prohibits scraping
- Reddit's API terms limit commercial use
- Letterboxd has no public API at all
- TMDB requires attribution and has rate limits

**For commercial deployment:** Must either (a) obtain official data licenses, (b) use only fully permitted APIs within their terms, or (c) accept legal risk.

---

### Risk 5: Fragmented Marketing Channels

| Risk | Mitigation |
|------|------------|
| **Gap scores lose validity as marketing becomes more fragmented (TikTok, influencer campaigns not captured in trailers)** | Expand promise corpus to include TikTok audio, influencer brief analysis, and paid social copy as additional data streams |

**Current Status:** ❌ Not mitigated — we only capture YouTube trailers, Wikipedia, and TMDB.

**Why it matters:** Modern film marketing extends far beyond trailers:

| Channel | Captured? | Importance |
|---------|-----------|------------|
| YouTube trailers | ✅ Yes | High |
| TV spots | ❌ No | Medium |
| TikTok campaigns | ❌ No | High (growing) |
| Influencer partnerships | ❌ No | Medium |
| Paid social ads (FB/IG) | ❌ No | High |
| Press junket interviews | ❌ No | Medium |
| Podcast appearances | ❌ No | Low |

**Future expansion needed:**
- TikTok audio extraction
- Instagram Reels analysis
- Influencer content tracking
- Paid ad creative analysis (via Facebook Ad Library)

---

### Risk Summary Table

| Risk | Severity | Likelihood | Mitigated? |
|------|----------|------------|------------|
| API access blocked | High | Medium | ❌ No |
| Multilingual gaps | Medium | High | ⚠️ Partial |
| Internal team resistance | Medium | High | N/A |
| Legal/ToS violations | High | High | ❌ No |
| Fragmented marketing | High | Certain | ❌ No |

---

### Implementation Status

**What we have:**
- English-only pipeline (acknowledged limitation)
- Basic relevance filtering
- Single-language embedding model (MiniLM)

**What we need for production:**
- Formal data licensing agreements
- Multilingual NLP models (XLM-RoBERTa)
- TikTok and social media scrapers
- Legal review of all data collection
- Rate limiting and respectful scraping practices

---

## Conclusion

The Promise Gap Analyser demonstrates that the disconnect between movie marketing and audience experience can be measured. While not perfect, it provides a quantitative framework for understanding a phenomenon that previously only existed as a feeling.

**The core insight:** Honest marketing works. Studios that accurately represent their films see better audience satisfaction, even when those films aren't universally loved. Studios that hide surprises or misrepresent tone face backlash that damages not just the current release, but audience trust in future marketing.

**The recommendation:** Use this tool not to "game" marketing, but to audit it. Before release, ask: "Does our marketing reflect what audiences will actually experience?" If not, adjust the campaign — or accept the consequences.

---

*Built as part of an unstructured data analysis project exploring the relationship between film marketing and audience reception.*

**Tech Stack:**
- Python 3.9+
- Sentence Transformers (MiniLM-L6-v2)
- K-Means Clustering
- Jensen-Shannon Distance
- Claude AI (Anthropic)
- HTML/CSS/JavaScript UI
