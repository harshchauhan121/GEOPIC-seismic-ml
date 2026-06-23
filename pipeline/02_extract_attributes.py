"""
02_extract_attributes.py -- Seismic Attribute Extraction
=========================================================
8 seismic attribute functions, each taking a 2D numpy array
of shape (n_traces, n_samples) and returning the same shape.

Attributes implemented:
  1. Envelope (Instantaneous Amplitude)
  2. Instantaneous Phase
  3. Cosine of Instantaneous Phase
  4. Instantaneous Frequency
  5. RMS Amplitude
  6. Reflection Strength
  7. Sweetness
  8. Spectral Decomposition (30 Hz)
"""

import numpy as np
from scipy.signal import hilbert
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUTS    = SCRIPT_DIR / ".." / "outputs"

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def compute_analytic(section: np.ndarray) -> np.ndarray:
    """Return the complex analytic signal via Hilbert transform along time axis."""
    return hilbert(section, axis=1)


# ---------------------------------------------------------------------------
# Attribute Functions
# ---------------------------------------------------------------------------

def attr_envelope(section: np.ndarray) -> np.ndarray:
    """
    Instantaneous Amplitude / Envelope.
    Measures signal strength regardless of polarity.
    """
    analytic = compute_analytic(section)
    return np.abs(analytic).astype(np.float32)


def attr_instantaneous_phase(section: np.ndarray) -> np.ndarray:
    """
    Instantaneous Phase.
    Position in the wave cycle, in radians (-pi to +pi).
    """
    analytic = compute_analytic(section)
    return np.angle(analytic).astype(np.float32)


def attr_cosine_phase(section: np.ndarray) -> np.ndarray:
    """
    Cosine of Instantaneous Phase.
    Smoother version of phase, better suited for ML input.
    """
    phase = attr_instantaneous_phase(section)
    return np.cos(phase).astype(np.float32)


def attr_instantaneous_frequency(section: np.ndarray) -> np.ndarray:
    """
    Instantaneous Frequency.
    Derivative of the unwrapped phase along the time axis.
    Padded to preserve original shape.
    """
    analytic  = compute_analytic(section)
    phase     = np.unwrap(np.angle(analytic), axis=1)
    # Derivative along time axis (axis=1)
    freq      = np.diff(phase, axis=1)
    # Pad last column to restore original shape
    freq      = np.pad(freq, ((0, 0), (0, 1)), mode="edge")
    return freq.astype(np.float32)


def attr_rms_amplitude(section: np.ndarray, window: int = 5) -> np.ndarray:
    """
    RMS Amplitude.
    Rolling root-mean-square energy over a window of samples along time axis.
    """
    squared = section ** 2
    rms     = np.zeros_like(section, dtype=np.float32)
    half    = window // 2

    for i in range(section.shape[1]):
        start      = max(0, i - half)
        end        = min(section.shape[1], i + half + 1)
        rms[:, i]  = np.sqrt(np.mean(squared[:, start:end], axis=1))

    return rms


def attr_reflection_strength(section: np.ndarray) -> np.ndarray:
    """
    Reflection Strength.
    Same as Envelope — absolute value of the analytic signal.
    """
    return attr_envelope(section)


def attr_sweetness(section: np.ndarray) -> np.ndarray:
    """
    Sweetness.
    Ratio of envelope to sqrt of instantaneous frequency.
    Highlights gas sands (high amplitude, low frequency zones).
    """
    epsilon   = 1e-6  # avoid division by zero
    env       = attr_envelope(section)
    freq      = np.abs(attr_instantaneous_frequency(section))
    sweetness = env / (np.sqrt(freq) + epsilon)
    return sweetness.astype(np.float32)


def attr_spectral_decomp(section: np.ndarray, target_hz: float = 30.0,
                          dt: float = 0.004) -> np.ndarray:
    """
    Spectral Decomposition at 30 Hz.
    FFT magnitude at a target frequency — detects thin beds and
    lateral stratigraphic changes.

    Parameters
    ----------
    section   : 2D array (n_traces, n_samples)
    target_hz : target frequency in Hz (default 30 Hz)
    dt        : sample interval in seconds (default 0.004 = 4 ms)
    """
    n_samples  = section.shape[1]
    freqs      = np.fft.rfftfreq(n_samples, d=dt)
    target_idx = np.argmin(np.abs(freqs - target_hz))

    fft_result = np.fft.rfft(section, axis=1)
    magnitude  = np.abs(fft_result)

    # Return the magnitude at the target frequency bin, broadcast to full shape
    decomp     = np.zeros_like(section, dtype=np.float32)
    decomp[:, :] = magnitude[:, target_idx : target_idx + 1]

    return decomp


# ---------------------------------------------------------------------------
# Feature Matrix Builder
# ---------------------------------------------------------------------------

import pandas as pd
from sklearn.preprocessing import StandardScaler

def build_feature_matrix(section: np.ndarray):
    """
    Compute all 8 attributes, flatten to 1D each, build a normalised
    feature matrix of shape (n_traces * n_samples, 8).
    
    Returns
    -------
    X_scaled   : np.ndarray, shape (N, 8), float32
    feat_names : list of 8 strings
    scaler     : fitted StandardScaler (save for inverse transform later)
    """
    attr_dict = {
        "envelope"       : attr_envelope(section),
        "inst_phase"     : attr_instantaneous_phase(section),
        "cosine_phase"   : attr_cosine_phase(section),
        "inst_freq"      : attr_instantaneous_frequency(section),
        "rms_amplitude"  : attr_rms_amplitude(section),
        "refl_strength"  : attr_reflection_strength(section),
        "sweetness"      : attr_sweetness(section),
        "spectral_30hz"  : attr_spectral_decomp(section),
    }

    # Flatten each 2D attribute to 1D and stack into a DataFrame
    df = pd.DataFrame({k: v.ravel() for k, v in attr_dict.items()})

    feat_names = list(df.columns)

    # Normalise: mean 0, std 1
    scaler   = StandardScaler()
    X_scaled = scaler.fit_transform(df).astype(np.float32)

    return X_scaled, feat_names, scaler


# ---------------------------------------------------------------------------
# Main — build and save the feature matrix
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    section = np.load(OUTPUTS / "inline_section.npy")
    print(f"Input shape: {section.shape}")

    # Optional: test with 100 traces first, then remove the slice
    # section = section[:100, :]

    X, feat_names, scaler = build_feature_matrix(section)

    print(f"Feature matrix shape : {X.shape}")
    print(f"Value range          : {X.min():.3f} to {X.max():.3f}")
    print(f"Feature names        : {feat_names}")

    np.save(OUTPUTS / "feature_matrix.npy", X)
    np.save(OUTPUTS / "feature_names.npy", np.array(feat_names))

    print("\nSaved feature_matrix.npy and feature_names.npy to outputs/")
