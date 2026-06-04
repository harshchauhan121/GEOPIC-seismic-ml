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
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
SEGY_PATH  = SCRIPT_DIR / ".." / "data" / "Dutch Government_F3_entire_8bit seismic.segy"

# Standard F3 Block trace-header byte positions
INLINE_BYTE  = 189   # Inline number byte offset
XLINE_BYTE   = 193   # Crossline number byte offset


def inspect_headers(path: str) -> None:
    """Open the SEG-Y file and print survey geometry information."""

    with segyio.open(path, mode="r", iline=INLINE_BYTE, xline=XLINE_BYTE) as f:
        # Allow segyio to read files that may not be perfectly spec-compliant
        f.mmap()

        # --- Inline information ---
        inlines = f.ilines
        print(f"Inlines  : {inlines[0]} to {inlines[-1]}  (count: {len(inlines)})")

        # --- Crossline information ---
        xlines = f.xlines
        print(f"Crosslines: {xlines[0]} to {xlines[-1]}  (count: {len(xlines)})")

        # --- Sample (time / depth) information ---
        samples = f.samples           # 1-D array of sample times in ms
        n_samples = len(samples)
        print(f"Samples  : {samples[0]:.1f} ms to {samples[-1]:.1f} ms  (count: {n_samples})")

        # --- Sample interval ---
        # segyio stores the binary-header sample interval in microseconds;
        # divide by 1000 to get milliseconds.
        dt_us = segyio.tools.dt(f)    # sample interval in microseconds
        dt_ms = dt_us / 1000.0
        print(f"Sample interval: {dt_ms} ms  ({dt_us} us)")

        t0 = f.trace[0]
        print(f"First trace dtype: {t0.dtype}")
        print(f"Value range      : {t0.min():.4f} to {t0.max():.4f}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("  F3 Block -- SEG-Y Header Inspection")
    print("=" * 60)
    inspect_headers(SEGY_PATH)
    print("=" * 60)
    print("Header inspection complete.")
