import { useEffect, useRef, useState, useCallback } from 'react';
import { fetchSeismicSection, fetchClusterLabels } from '../api/client';

// RGB triplets — indexed by cluster ID (0–5)
const CLUSTER_COLORS = [
  [239, 68, 68],   // red    — Cluster 0
  [249, 115, 22],   // orange — Cluster 1
  [234, 179, 8],   // yellow — Cluster 2
  [34, 197, 94],   // green  — Cluster 3
  [59, 130, 246],  // blue   — Cluster 4
  [168, 85, 247],  // purple — Cluster 5
];

export default function SeismicViewer({ showOverlay, clusterMethod }) {
  const canvasRef = useRef(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [seismicData, setSeismicData] = useState(null);
  const [clusterData, setClusterData] = useState(null);
  const [baseImage, setBaseImage] = useState(null);
  const [overlayAlpha, setOverlayAlpha] = useState(0.40);

  // ── data fetch ──────────────────────────────────────────────────────
  const loadSeismicData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [seismic, cluster] = await Promise.all([
        fetchSeismicSection(2),
        fetchClusterLabels(clusterMethod, 2),
      ]);
      setSeismicData(seismic);
      setClusterData(cluster);

      const img = new Image();
      img.onload = () => { setBaseImage(img); setLoading(false); };
      img.onerror = () => { setError('Failed to load seismic image'); setLoading(false); };
      img.src = `data:image/png;base64,${seismic.image_b64}`;
    } catch {
      setError('Failed to load seismic section');
      setLoading(false);
    }
  }, [clusterMethod]);

  useEffect(() => { loadSeismicData(); }, [loadSeismicData]);

  // ── overlay paint ───────────────────────────────────────────────────
  useEffect(() => {
    // All four data items must be ready; canvas must exist; overlay must be on
    if (
      !canvasRef.current ||
      !baseImage ||
      !seismicData ||
      !clusterData ||
      !clusterData.labels ||
      loading ||
      !showOverlay
    ) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Match canvas resolution to the backend image (2100 × 900)
    canvas.width = seismicData.width;
    canvas.height = seismicData.height;

    // Paint cluster colours onto empty transparent canvas
    const labels = clusterData.labels;           // [time_rows][crossline_cols]
    const labelRows = labels.length;                // 462
    const labelCols = labels[0].length;             // 951

    const imageData = ctx.createImageData(canvas.width, canvas.height);
    const pixels = imageData.data;               // Uint8ClampedArray, RGBA (all 0)

    for (let y = 0; y < canvas.height; y++) {
      // Map canvas row → label row
      const labelRow = Math.min(
        Math.floor(y * (labelRows / canvas.height)),
        labelRows - 1
      );

      for (let x = 0; x < canvas.width; x++) {
        // Map canvas column → label column
        const labelCol = Math.min(
          Math.floor(x * (labelCols / canvas.width)),
          labelCols - 1
        );

        const clusterID = labels[labelRow][labelCol];

        // Skip unknown / out-of-range cluster IDs
        if (clusterID < 0 || clusterID >= CLUSTER_COLORS.length) continue;

        const [cR, cG, cB] = CLUSTER_COLORS[clusterID];
        const px = (y * canvas.width + x) * 4;  // RGBA stride

        pixels[px]     = cR;
        pixels[px + 1] = cG;
        pixels[px + 2] = cB;
        pixels[px + 3] = 255; // solid cluster colour
      }
    }

    ctx.putImageData(imageData, 0, 0);
  }, [baseImage, showOverlay, clusterData, seismicData, loading]);

  // ── shared media style ──────────────────────────────────────────────
  const mediaStyle = {
    width: '100%',
    height: 'auto',
    display: 'block',
    backgroundColor: '#000',
  };

  return (
    <div className="seismic-viewer">
      <div className="seismic-canvas-wrapper" style={{ position: 'relative' }}>

        {loading && (
          <div className="skeleton skeleton-canvas">
            <span>Loading seismic section...</span>
          </div>
        )}

        {error && (
          <div className="panel-error">
            <span>{error}</span>
            <button onClick={loadSeismicData} className="retry-link">Retry</button>
          </div>
        )}

        {!loading && !error && seismicData && (
          <>
            <div className="inline-badge">
              Inline {seismicData.inline_index}
            </div>

            {/* Base image is always rendered */}
            <img
              src={`data:image/png;base64,${seismicData.image_b64}`}
              alt="Seismic Section"
              style={mediaStyle}
            />

            {/* Canvas overlay is absolutely positioned on top, handled by CSS opacity */}
            {showOverlay && (
              <canvas 
                ref={canvasRef} 
                style={{ 
                  width: '100%',
                  height: 'auto',
                  display: 'block',
                  position: 'absolute', 
                  top: 0, 
                  left: 0, 
                  opacity: overlayAlpha 
                }} 
              />
            )}

            {showOverlay && (
              <div style={{
                display: 'flex', alignItems: 'center', gap: '10px',
                padding: '8px 12px', fontSize: '13px',
                color: 'var(--text-secondary, #aaa)'
              }}>
                <span>Opacity</span>
                <input
                  type="range"
                  min="0.15" max="0.65" step="0.05"
                  value={overlayAlpha}
                  onChange={e => setOverlayAlpha(parseFloat(e.target.value))}
                  style={{ flex: 1 }}
                />
                <span style={{ minWidth: '34px', textAlign: 'right' }}>
                  {Math.round(overlayAlpha * 100)}%
                </span>
              </div>
            )}
          </>
        )}

      </div>
    </div>
  );
}