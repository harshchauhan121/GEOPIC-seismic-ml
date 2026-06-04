"""
01_load_segy.py -- SEG-Y Header Inspection for the F3 Block Dataset
===================================================================
Opens the F3 Demo 2006 SEG-Y file and prints key survey geometry:
  - Inline range and count
  - Crossline range and count
  - Sample (time) range and count
  - Sample interval in milliseconds

Run from the pipeline/ directory:
    python 01_load_segy.py
"""

import segyio
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
SEGY_PATH  = SCRIPT_DIR / ".." / "data" / "Dutch Government_F3_entire_8bit seismic.segy"

INLINE_BYTE  = 189
XLINE_BYTE   = 193


def inspect_headers(path: str) -> None:
    """Open the SEG-Y file and print survey geometry information."""

    with segyio.open(path, mode="r", iline=INLINE_BYTE, xline=XLINE_BYTE) as f:
        f.mmap()

        # --- 1.1: Header inspection ---
        inlines = f.ilines
        print(f"Inlines  : {inlines[0]} to {inlines[-1]}  (count: {len(inlines)})")

        xlines = f.xlines
        print(f"Crosslines: {xlines[0]} to {xlines[-1]}  (count: {len(xlines)})")

        samples = f.samples
        print(f"Samples  : {samples[0]:.1f} ms to {samples[-1]:.1f} ms  (count: {len(samples)})")

        dt_us = segyio.tools.dt(f)
        print(f"Sample interval: {dt_us / 1000.0} ms  ({dt_us} us)")

        t0 = f.trace[0]
        print(f"First trace dtype: {t0.dtype}")
        print(f"Value range      : {t0.min():.4f} to {t0.max():.4f}")

        # --- 1.2: Extract middle inline section ---
        mid_inline = f.ilines[len(f.ilines) // 2]
        print(f"Extracting inline : {mid_inline}")

        section = f.iline[mid_inline].astype(np.float32)

        print(f"Section shape     : {section.shape}")
        print(f"Section min/max   : {section.min():.2f} / {section.max():.2f}")
        print(f"Section mean      : {section.mean():.2f}")

        # Save to outputs/
        OUTPUTS = SCRIPT_DIR / ".." / "outputs"
        OUTPUTS.mkdir(exist_ok=True)

        np.save(OUTPUTS / "inline_section.npy", section)
        np.save(OUTPUTS / "inline_index.npy", np.array(mid_inline))
        print("Saved: outputs/inline_section.npy")
        print("Saved: outputs/inline_index.npy")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  F3 Block -- SEG-Y Header Inspection & Inline Extraction")
    print("=" * 60)
    inspect_headers(SEGY_PATH)
    print("=" * 60)
    print("Done.")