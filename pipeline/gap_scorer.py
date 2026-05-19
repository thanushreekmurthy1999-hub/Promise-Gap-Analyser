"""
Gap score calculation module.

Computes two metrics:
1. Topic-based gap using clustering of embeddings
2. Embedding centroid distance
3. Composite score (weighted combination)
"""

import numpy as np
from scipy.spatial.distance import jensenshannon, cosine
from sklearn.cluster import KMeans
from typing import List, Dict, Tuple


def compute_topic_distribution(chunks: List[Dict], n_topics: int = 5) -> np.ndarray:
    """
    Cluster embeddings into topics and return topic distribution.
    """
    if not chunks:
        return np.ones(n_topics) / n_topics  # Uniform if no data
    
    embeddings = np.array([c['embedding'] for c in chunks])
    n_samples = len(embeddings)
    
    # Adjust n_topics if too few samples
    actual_k = min(n_topics, n_samples // 3)
    if actual_k < 2:
        actual_k = 2
    
    # K-means clustering
    kmeans = KMeans(n_clusters=actual_k, random_state=42, n_init=10)
    labels = kmeans.fit_predict(embeddings)
    
    # Compute topic distribution (normalized histogram)
    distribution = np.bincount(labels, minlength=actual_k).astype(float)
    distribution = distribution / distribution.sum()
    
    # Pad to standard size if needed
    if len(distribution) < n_topics:
        padded = np.zeros(n_topics)
        padded[:len(distribution)] = distribution
        distribution = padded
    
    return distribution


def compute_jsd_gap(promise_chunks: List[Dict], delivery_chunks: List[Dict]) -> float:
    """
    Compute Jensen-Shannon divergence between promise and delivery topic distributions.
    Returns score 0-100.
    """
    # Get topic distributions
    promise_dist = compute_topic_distribution(promise_chunks, n_topics=5)
    delivery_dist = compute_topic_distribution(delivery_chunks, n_topics=5)
    
    # Pad to same size
    max_len = max(len(promise_dist), len(delivery_dist))
    if len(promise_dist) < max_len:
        promise_dist = np.pad(promise_dist, (0, max_len - len(promise_dist)))
    if len(delivery_dist) < max_len:
        delivery_dist = np.pad(delivery_dist, (0, max_len - len(delivery_dist)))
    
    # Add small epsilon to avoid zeros
    promise_dist = promise_dist + 1e-10
    delivery_dist = delivery_dist + 1e-10
    promise_dist = promise_dist / promise_dist.sum()
    delivery_dist = delivery_dist / delivery_dist.sum()
    
    # Compute JSD (returns value 0-1)
    jsd = jensenshannon(promise_dist, delivery_dist)
    if np.isnan(jsd):
        jsd = 0.5  # Default if computation fails
    
    # Scale to 0-100
    return round(float(jsd) * 100, 1)


def compute_embedding_gap(promise_chunks: List[Dict], delivery_chunks: List[Dict]) -> float:
    """
    Compute cosine distance between mean embeddings of promise and delivery.
    Returns score 0-100.
    """
    if not promise_chunks or not delivery_chunks:
        return 50.0  # Default if missing data
    
    # Get mean embeddings
    promise_emb = np.mean([c['embedding'] for c in promise_chunks], axis=0)
    delivery_emb = np.mean([c['embedding'] for c in delivery_chunks], axis=0)
    
    # Normalize
    promise_emb = promise_emb / (np.linalg.norm(promise_emb) + 1e-10)
    delivery_emb = delivery_emb / (np.linalg.norm(delivery_emb) + 1e-10)
    
    # Cosine distance = 1 - cosine similarity
    cosine_sim = np.dot(promise_emb, delivery_emb)
    distance = 1 - cosine_sim
    
    # Scale to 0-100
    return round(float(distance) * 100, 1)


def compute_composite_gap(jsd_gap: float, embedding_gap: float) -> float:
    """
    Compute composite gap score.
    Weights: 85% JSD (topic divergence), 15% embedding distance (centroid)
    """
    composite = 0.85 * jsd_gap + 0.15 * embedding_gap
    return round(composite, 1)


def compute_film_gap(film_data: Dict) -> Dict:
    """
    Compute all gap metrics for a film.
    """
    promise = film_data['promise']
    delivery = film_data['delivery']
    
    # Compute metrics
    jsd_gap = compute_jsd_gap(promise, delivery)
    embedding_gap = compute_embedding_gap(promise, delivery)
    composite = compute_composite_gap(jsd_gap, embedding_gap)
    
    return {
        'film': film_data['film'],
        'jsd_gap': jsd_gap,
        'embedding_gap': embedding_gap,
        'composite_gap': composite,
        'promise_count': len(promise),
        'delivery_count': len(delivery)
    }


def compute_all_gaps(embedded_data: Dict) -> List[Dict]:
    """Compute gap scores for all films."""
    results = []
    for film, data in embedded_data.items():
        result = compute_film_gap(data)
        results.append(result)
    return results


if __name__ == "__main__":
    from cleaner import clean_all_films
    from embedder import embed_all_films
    
    print("Running full pipeline...")
    print("\n1. Cleaning corpora...")
    cleaned = clean_all_films()
    
    print("\n2. Creating embeddings...")
    embedded = embed_all_films(cleaned)
    
    print("\n3. Computing gap scores...")
    results = compute_all_gaps(embedded)
    
    print("\n" + "="*60)
    print("GAP SCORES")
    print("="*60)
    print(f"{'Film':<25} {'JSD':>8} {'Emb':>8} {'Composite':>10}")
    print("-"*60)
    
    for r in results:
        print(f"{r['film']:<25} {r['jsd_gap']:>8.1f} {r['embedding_gap']:>8.1f} {r['composite_gap']:>10.1f}")
