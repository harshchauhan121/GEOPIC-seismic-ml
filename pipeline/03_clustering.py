"""
03_clustering.py
----------------
Step 3.1 – Evaluate KMeans clustering (k = 3..8) on the seismic feature matrix.
         Outputs an elbow + silhouette plot to ../outputs/cluster_selection.png.
Step 3.2 – Run KMeans and GMM with the chosen K on the full feature matrix.
         Saves label arrays to ../outputs/kmeans_labels.npy and gmm_labels.npy.
Step 3.3 – Generate facies map: reshape labels to 2D and overlay on seismic section.
         Saves ../outputs/label_map_kmeans.npy and ../outputs/facies_map.png.
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from pathlib import Path

# ── paths ────────────────────────────────────────────────────────────
OUT_DIR      = Path(__file__).resolve().parent.parent / "outputs"
FEATURE_PATH = OUT_DIR / "feature_matrix.npy"
OUTPUT_PATH  = OUT_DIR / "cluster_selection.png"
KMEANS_PATH  = OUT_DIR / "kmeans_labels.npy"
GMM_PATH     = OUT_DIR / "gmm_labels.npy"
SECTION_PATH = OUT_DIR / "inline_section.npy"
LABELMAP_PATH= OUT_DIR / "label_map_kmeans.npy"
FACIES_PATH  = OUT_DIR / "facies_map.png"

# ── constants ────────────────────────────────────────────────────────
SEED         = 42
SUBSAMPLE_N  = 50_000
K_RANGE      = range(3, 9)          # 3, 4, 5, 6, 7, 8
SIL_SAMPLE   = 10_000

# ── load & subsample ────────────────────────────────────────────────
print(f"Loading features from {FEATURE_PATH} ...")
features = np.load(FEATURE_PATH)
print(f"  Shape: {features.shape}")

rng = np.random.default_rng(SEED)

if features.shape[0] > SUBSAMPLE_N:
    idx = rng.choice(features.shape[0], size=SUBSAMPLE_N, replace=False)
    X = features[idx]
    print(f"  Subsampled to {X.shape[0]:,} points (seed={SEED})")
else:
    X = features
    print(f"  Using all {X.shape[0]:,} points (below subsample threshold)")

# ── clustering sweep ────────────────────────────────────────────────
inertias    = []
silhouettes = []

print(f"\n{'k':>3}  {'Inertia':>14}  {'Silhouette':>10}")
print("-" * 32)

for k in K_RANGE:
    km = KMeans(n_clusters=k, n_init=10, random_state=SEED)
    labels = km.fit_predict(X)

    inertia = km.inertia_
    sil = silhouette_score(X, labels, sample_size=SIL_SAMPLE, random_state=SEED)

    inertias.append(inertia)
    silhouettes.append(sil)

    print(f"{k:>3}  {inertia:>14.2f}  {sil:>10.4f}")

# ── plot ─────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

ks = list(K_RANGE)

# Elbow curve
ax1.plot(ks, inertias, "o-", linewidth=2, markersize=7, color="#2563eb")
ax1.set_xlabel("Number of clusters (k)")
ax1.set_ylabel("Inertia")
ax1.set_title("Elbow Curve")
ax1.set_xticks(ks)
ax1.grid(True, alpha=0.3)

# Silhouette scores
ax2.plot(ks, silhouettes, "s-", linewidth=2, markersize=7, color="#dc2626")
ax2.set_xlabel("Number of clusters (k)")
ax2.set_ylabel("Silhouette Score")
ax2.set_title("Silhouette Analysis")
ax2.set_xticks(ks)
ax2.grid(True, alpha=0.3)

fig.suptitle("KMeans Cluster Selection", fontsize=14, fontweight="bold")
fig.tight_layout()

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUTPUT_PATH, dpi=150, bbox_inches="tight")
print(f"\nPlot saved to {OUTPUT_PATH}")

# ══════════════════════════════════════════════════════════════════════
# Step 3.2 – Full clustering with chosen K
# ══════════════════════════════════════════════════════════════════════
K = 6

print(f"\n{'='*50}")
print(f"Step 3.2: Full clustering with K = {K}")
print(f"{'='*50}")
print(f"  Using full feature matrix: {features.shape}")

# ── KMeans ───────────────────────────────────────────────────────────
print("\nRunning KMeans ...")
km_full = KMeans(n_clusters=K, n_init=10, random_state=SEED)
km_labels = km_full.fit_predict(features)
np.save(KMEANS_PATH, km_labels)
print(f"  Unique labels : {np.unique(km_labels)}")
print(f"  Saved to      : {KMEANS_PATH}")

# ── Gaussian Mixture ─────────────────────────────────────────────────
print("\nRunning GaussianMixture ...")
gmm = GaussianMixture(
    n_components=K,
    covariance_type="diag",
    max_iter=200,
    random_state=SEED,
)
gmm.fit(features)
gmm_labels = gmm.predict(features)
np.save(GMM_PATH, gmm_labels)
print(f"  Unique labels : {np.unique(gmm_labels)}")
print(f"  Saved to      : {GMM_PATH}")

# ══════════════════════════════════════════════════════════════════════
# Step 3.3 – Facies map visualisation
# ══════════════════════════════════════════════════════════════════════
print(f"\n{'='*50}")
print("Step 3.3: Facies map generation")
print(f"{'='*50}")

# ── load section & reshape labels ────────────────────────────────────
section = np.load(SECTION_PATH)
print(f"  Inline section shape : {section.shape}")

label_map = km_labels.reshape(section.shape)
np.save(LABELMAP_PATH, label_map)
print(f"  Label map saved to   : {LABELMAP_PATH}")

# ── percentile clip for seismic display ──────────────────────────────
vmin, vmax = np.percentile(section, [2, 98])

# ── colour palette for 6 clusters ───────────────────────────────────
FACIES_COLORS = ListedColormap([
    "#e63946",   # red
    "#457b9d",   # steel blue
    "#2a9d8f",   # teal
    "#e9c46a",   # sandy yellow
    "#f4a261",   # orange
    "#264653",   # dark charcoal
])

# ── plot ─────────────────────────────────────────────────────────────
fig, (ax_seis, ax_fac) = plt.subplots(1, 2, figsize=(18, 6))

# Left – raw seismic
ax_seis.imshow(section, cmap="Greys", aspect="auto", vmin=vmin, vmax=vmax)
ax_seis.set_title("Raw Seismic Section")
ax_seis.set_xlabel("Trace")
ax_seis.set_ylabel("Sample")

# Right – seismic + cluster overlay
ax_fac.imshow(section, cmap="Greys", aspect="auto", vmin=vmin, vmax=vmax, alpha=0.4)
im = ax_fac.imshow(label_map, cmap=FACIES_COLORS, aspect="auto",
                   alpha=0.6, vmin=0, vmax=K - 1)
ax_fac.set_title(f"KMeans Facies Map  (K = {K})")
ax_fac.set_xlabel("Trace")
ax_fac.set_ylabel("Sample")

cbar = fig.colorbar(im, ax=ax_fac, ticks=range(K), shrink=0.8)
cbar.set_label("Cluster")

fig.tight_layout()
fig.savefig(FACIES_PATH, dpi=150, bbox_inches="tight")
print(f"  Facies map saved to  : {FACIES_PATH}")

print("\nDone.")
