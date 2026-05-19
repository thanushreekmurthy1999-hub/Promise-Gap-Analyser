"""
Quick recalculation of composite scores with new weights.
Uses already-computed JSD and Embedding values.
"""

# Previous results with old weights (0.6 JSD + 0.4 Emb)
# We have the individual JSD and Embedding values
results = [
    {"film": "snow_white", "jsd": 23.2, "emb": 23.9},
    {"film": "wicked", "jsd": 19.0, "emb": 30.1},
    {"film": "minecraft", "jsd": 18.9, "emb": 31.6},
    {"film": "lilo_stitch", "jsd": 18.0, "emb": 54.7},
    {"film": "thunderbolts", "jsd": 23.0, "emb": 50.6},
    {"film": "joker_2", "jsd": 33.3, "emb": 52.0},
    {"film": "paddington", "jsd": 40.2, "emb": 42.1},
]

print("="*65)
print("UPDATED GAP SCORES (0.85 JSD + 0.15 Embedding)")
print("="*65)
print(f"{'Film':<25} {'JSD':>8} {'Emb Gap':>10} {'Composite':>12}")
print("-"*65)

for r in results:
    # New formula: 85% topic_divergence (JSD) + 15% centroid_distance (Embedding)
    composite = round(0.85 * r["jsd"] + 0.15 * r["emb"], 1)
    print(f"{r['film']:<25} {r['jsd']:>8.1f} {r['emb']:>10.1f} {composite:>12.1f}")

print("="*65)
