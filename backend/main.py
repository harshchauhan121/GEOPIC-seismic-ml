"""
backend/main.py
---------------
FastAPI REST API for the GEOPIC Seismic Dashboard.
Serves pre-computed ML outputs (numpy arrays, CSVs, PNGs) from the
seismic clustering pipeline.

Run with:
    uvicorn main:app --reload --port 8000
"""

import base64
import io
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from PIL import Image

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# ── app ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="GEOPIC Seismic Dashboard API",
    version="1.0",
    description="Serves pre-computed seismic ML outputs for the F3 Block dashboard.",
)

# ── CORS ──────────────────────────────────────────────────────────────
ALLOWED_ORIGINS = [
    "http://localhost:5173",          # Vite dev server
    "https://your-app.vercel.app",    # TODO: replace with actual Vercel URL after deploy
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── paths ─────────────────────────────────────────────────────────────
OUTPUTS = Path(__file__).resolve().parent.parent / "outputs"


# ── health ────────────────────────────────────────────────────────────
@app.get("/health", tags=["Meta"])
def health():
    """Simple liveness check."""
    return {"status": "ok"}


# ── seismic section ───────────────────────────────────────────────────
@app.get("/api/seismic-section", tags=["Seismic"])
def seismic_section(
    downsample: int = Query(default=4, ge=1, le=20,
                            description="Take every Nth sample in both axes."),
):
    """
    Return a downsampled, percentile-clipped, base64-encoded PNG of the
    inline seismic section together with its width, height, and inline index.
    """
    section_path = OUTPUTS / "inline_section.npy"
    index_path   = OUTPUTS / "inline_index.npy"

    if not section_path.exists():
        raise HTTPException(status_code=404, detail="inline_section.npy not found")
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="inline_index.npy not found")

    # 1. Load
    section      = np.load(section_path)                 # shape (n_samples, n_traces)
    inline_index = int(np.load(index_path))

    # 2. Downsample (every Nth row and column)
    section_ds = section[::downsample, ::downsample]

    # 3. Percentile clip then normalise to 0.0 - 1.0 float
    vmin, vmax = np.percentile(section_ds, [2, 98])
    clipped    = np.clip(section_ds, vmin, vmax)
    normed     = (clipped - vmin) / (vmax - vmin)

    # 4. Transpose to landscape (time, crosslines) and apply colormap
    # Apply matplotlib Greys colormap for identical quality to seismic_section.png
    normed_T = normed.T
    cmap = cm.get_cmap('Greys')
    colored = cmap(normed_T)  # returns RGBA float array 0-1
    colored_uint8 = (colored[:, :, :3] * 255).astype(np.uint8)  # drop alpha, keep RGB

    # 5. Convert to PIL Image and Upscale
    img = Image.fromarray(colored_uint8, mode='RGB')
    img = img.resize((2100, 900), Image.LANCZOS)

    # 5. Encode as PNG into a BytesIO buffer
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    image_b64 = base64.b64encode(buf.read()).decode("utf-8")

    # 6. Return JSON
    return JSONResponse({
        "image_b64":    image_b64,
        "width":        img.width,
        "height":       img.height,
        "inline_index": inline_index,
        "downsample":   downsample,
    })


# ── cluster labels ────────────────────────────────────────────────────
VALID_METHODS = {"kmeans", "gmm"}

@app.get("/api/cluster-labels", tags=["Clustering"])
def cluster_labels(
    method: str = Query(
        default="kmeans",
        description="Clustering method: 'kmeans' or 'gmm'.",
    ),
    downsample: int = Query(
        default=4, ge=1, le=20,
        description="Take every Nth element in both axes.",
    ),
):
    """
    Return a downsampled 2D label map for the chosen clustering method,
    transposed to match the seismic section orientation (time downward).
    """
    if method not in VALID_METHODS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid method '{method}'. Choose from: {sorted(VALID_METHODS)}",
        )

    label_path = OUTPUTS / f"label_map_{method}.npy"
    if not label_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Label map not found for method '{method}': {label_path.name}",
        )

    # 1. Load — shape (n_samples, n_traces), i.e. (time, trace)
    label_map = np.load(label_path)

    # 2. Downsample
    label_ds = label_map[::downsample, ::downsample]

    # 3. Transpose so axis-0 = trace (x) and axis-1 = time (y),
    #    matching how the frontend renders columns left-to-right.
    label_ds_T = label_ds.T

    # 4. Return JSON
    return JSONResponse({
        "labels":     label_ds_T.tolist(),
        "n_clusters": int(np.max(label_ds) + 1),
        "method":     method,
        "downsample": downsample,
        "shape":      list(label_ds_T.shape),   # [n_traces, n_samples] after transpose
    })


# ── attribute statistics ──────────────────────────────────────────────
@app.get("/api/attribute-stats", tags=["Clustering"])
def attribute_stats():
    """
    Return per-cluster descriptive statistics for all seismic features.

    Loads the full feature matrix, K-Means cluster labels, and feature
    names from OUTPUTS, then computes — for each unique cluster ID — the
    mean, standard deviation, and sample count of every feature column.

    Response schema
    ───────────────
    {
        "features": ["feat_a", "feat_b", ...],          // 8 feature names
        "clusters": {
            "0": {"mean": [...], "std": [...], "count": 1234},
            "1": {"mean": [...], "std": [...], "count":  987},
            ...
        }
    }
    """
    feat_matrix_path = OUTPUTS / "feature_matrix.npy"
    labels_path      = OUTPUTS / "kmeans_labels.npy"
    feat_names_path  = OUTPUTS / "feature_names.npy"

    # ── guard: verify all required files exist ────────────────────────
    for path in (feat_matrix_path, labels_path, feat_names_path):
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"{path.name} not found in outputs directory.",
            )

    # ── load ──────────────────────────────────────────────────────────
    feature_matrix = np.load(feat_matrix_path)          # shape (N, n_features)
    kmeans_labels  = np.load(labels_path)               # shape (N,)  — int cluster IDs
    feature_names  = np.load(feat_names_path,
                             allow_pickle=True).tolist() # list of str, length n_features

    # ── basic shape validation ────────────────────────────────────────
    if feature_matrix.ndim != 2:
        raise HTTPException(
            status_code=500,
            detail="feature_matrix.npy must be 2-D (samples × features).",
        )
    if feature_matrix.shape[0] != kmeans_labels.shape[0]:
        raise HTTPException(
            status_code=500,
            detail=(
                "Row count mismatch: feature_matrix has "
                f"{feature_matrix.shape[0]} rows but kmeans_labels has "
                f"{kmeans_labels.shape[0]} entries."
            ),
        )

    # ── compute per-cluster statistics ───────────────────────────────
    cluster_stats: dict[str, dict] = {}

    for cluster_id in sorted(np.unique(kmeans_labels)):
        mask   = kmeans_labels == cluster_id          # boolean index for this cluster
        subset = feature_matrix[mask]                 # shape (count, n_features)

        cluster_stats[str(int(cluster_id))] = {
            "mean":  subset.mean(axis=0).tolist(),    # list[float], length n_features
            "std":   subset.std(axis=0).tolist(),     # list[float], length n_features
            "count": int(mask.sum()),                 # scalar int
        }

    return JSONResponse({
        "features": feature_names,
        "clusters": cluster_stats,
    })


# ── t-SNE projection ──────────────────────────────────────────────────
@app.get("/api/tsne", tags=["Clustering"])
def tsne():
    """
    Return the 2-D t-SNE projection of the seismic feature matrix together
    with the K-Means cluster label assigned to each sample.

    Response schema
    ───────────────
    {
        "x":      [float, ...],   // t-SNE dimension-1 coordinate per sample
        "y":      [float, ...],   // t-SNE dimension-2 coordinate per sample
        "labels": [int,   ...]    // cluster ID per sample (same length as x/y)
    }
    """
    tsne_path   = OUTPUTS / "tsne_2d.npy"
    labels_path = OUTPUTS / "tsne_labels.npy"

    # ── guard: verify both files exist ───────────────────────────────
    for path in (tsne_path, labels_path):
        if not path.exists():
            raise HTTPException(
                status_code=404,
                detail=f"{path.name} not found in outputs directory.",
            )

    # ── load ──────────────────────────────────────────────────────────
    tsne_coords = np.load(tsne_path)     # shape (N, 2)
    tsne_labels = np.load(labels_path)   # shape (N,) — int cluster IDs

    # ── basic shape validation ────────────────────────────────────────
    if tsne_coords.ndim != 2 or tsne_coords.shape[1] != 2:
        raise HTTPException(
            status_code=500,
            detail=(
                "tsne_2d.npy must be 2-D with exactly 2 columns (N × 2); "
                f"got shape {list(tsne_coords.shape)}."
            ),
        )
    if tsne_coords.shape[0] != tsne_labels.shape[0]:
        raise HTTPException(
            status_code=500,
            detail=(
                "Row count mismatch: tsne_2d has "
                f"{tsne_coords.shape[0]} rows but tsne_labels has "
                f"{tsne_labels.shape[0]} entries."
            ),
        )

    # ── return ────────────────────────────────────────────────────────
    return JSONResponse({
        "x":      tsne_coords[:, 0].tolist(),          # list[float]
        "y":      tsne_coords[:, 1].tolist(),          # list[float]
        "labels": tsne_labels.astype(int).tolist(),    # list[int]
    })
