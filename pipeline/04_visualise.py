"""
04_visualise.py -- Seismic Visualisation Functions
===================================================
Visualisation utilities for the GEOPIC seismic ML project.
Run this script directly to produce outputs/seismic_section.png
"""

import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUTS    = SCRIPT_DIR / ".." / "outputs"


def plot_seismic_section(section: np.ndarray, title: str, save_path=None) -> None:
    """
    Plot a 2D seismic section as a greyscale image.

    Parameters
    ----------
    section   : 2D array of shape (n_crosslines, n_samples)
    title     : plot title string
    save_path : optional path to save the PNG
    """
    # Clip display range to 2nd-98th percentile to avoid outliers washing out image
    vmin = np.percentile(section, 2)
    vmax = np.percentile(section, 98)

    fig, ax = plt.subplots(figsize=(14, 6))

    # Transpose so time goes downward (samples on Y axis, crosslines on X axis)
    ax.imshow(
        section.T,
        cmap="Greys",
        aspect="auto",
        vmin=vmin,
        vmax=vmax,
        origin="upper"
    )

    ax.set_xlabel("Crossline Number")
    ax.set_ylabel("Time Sample (ms)")
    ax.set_title(title)
    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved: {save_path}")

    plt.close()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    section_path = OUTPUTS / "inline_section.npy"
    save_path    = OUTPUTS / "seismic_section.png"

    print("Loading inline_section.npy ...")
    section = np.load(section_path)
    print(f"Section shape: {section.shape}")

    plot_seismic_section(
        section=section,
        title="F3 Block -- Inline 425 Seismic Section",
        save_path=save_path
    )
    print("Done.")