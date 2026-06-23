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

    # 3. Percentile clip then normalise to 0-255
    vmin, vmax = np.percentile(section_ds, [2, 98])
    clipped    = np.clip(section_ds, vmin, vmax)
    normalised = ((clipped - vmin) / (vmax - vmin) * 255).astype(np.uint8)

    # 4. Convert to PIL Image — shape is (n_samples, n_traces) which is
    #    already (rows=time, cols=trace), so time goes downward naturally.
    img = Image.fromarray(normalised, mode="L")

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
