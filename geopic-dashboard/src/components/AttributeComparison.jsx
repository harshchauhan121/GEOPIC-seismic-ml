import { useState, useEffect, useCallback } from 'react';
import Plot from 'react-plotly.js';
import { fetchAttributeStats } from '../api/client';

const CLUSTER_COLORS = [
  '#ef4444', // red    — Cluster 0
  '#f97316', // orange — Cluster 1
  '#eab308', // yellow — Cluster 2
  '#22c55e', // green  — Cluster 3
  '#3b82f6', // blue   — Cluster 4
  '#a855f7', // purple — Cluster 5
];

const ATTRIBUTE_EXPLANATIONS = {
  envelope:
    'Measures the instantaneous amplitude strength of the seismic signal, independent of phase. Highlights reflectivity contrasts — useful for spotting bright spots and structural boundaries.',
  inst_phase:
    'Tracks the phase of the seismic wavelet at each sample, useful for tracing weak or discontinuous reflectors regardless of amplitude.',
  cosine_phase:
    'A smoothed version of instantaneous phase (cosine-transformed) that reduces noise sensitivity while preserving reflector continuity.',
  inst_freq:
    'Instantaneous frequency, derived via the Hilbert transform. Sensitive to thin-bed tuning effects and can be unstable near data edges or low-amplitude zones.',
  rms_amplitude:
    'Root-mean-square amplitude over a window — a general energy/reflectivity strength indicator, often used to detect hydrocarbon-related amplitude anomalies.',
  refl_strength:
    'Reflection strength, closely related to the envelope attribute, indicating acoustic impedance contrasts between rock layers.',
  sweetness:
    'Defined as envelope divided by the square root of instantaneous frequency. Often used to highlight sand-prone, high-amplitude/low-frequency zones, but is numerically unstable when instantaneous frequency approaches zero (e.g. near data edges).',
  spectral_30hz:
    'Spectral amplitude at the 30 Hz frequency band from time-frequency decomposition, useful for tuning and thin-bed analysis.',
};

export default function AttributeComparison() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedAttribute, setSelectedAttribute] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAttributeStats();
      setStats(result);
      if (result?.features?.length > 0 && !selectedAttribute) {
        setSelectedAttribute(result.features[0]);
      }
      setLoading(false);
    } catch {
      setError('Failed to load attribute statistics');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="attribute-stats">
        <div className="skeleton skeleton-stats">
          <span>Loading attribute comparison...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="attribute-stats">
        <div className="panel-error">
          <span>{error}</span>
          <button onClick={loadData} className="retry-link">Retry</button>
        </div>
      </div>
    );
  }

  if (!stats || !stats.clusters || !stats.features) return null;

  const features = stats.features;
  const clusterKeys = Object.keys(stats.clusters).sort(
    (a, b) => parseInt(a) - parseInt(b)
  );
  const attrIdx = features.indexOf(selectedAttribute);

  // Gather data for the selected attribute across all clusters
  const clusterLabels = clusterKeys.map((k) => `Cluster ${k}`);
  const tickLabels = clusterKeys.map(
    (k, i) => {
      const m = stats.clusters[k].mean[attrIdx] ?? 0;
      return `Cluster ${k}<br>(${m.toFixed(3)})`;
    }
  );
  const means = clusterKeys.map(
    (k) => stats.clusters[k].mean[attrIdx] ?? 0
  );
  const stds = clusterKeys.map(
    (k) => stats.clusters[k].std[attrIdx] ?? 0
  );
  const counts = clusterKeys.map(
    (k) => stats.clusters[k].count ?? 0
  );
  const barColors = clusterKeys.map((k) => CLUSTER_COLORS[parseInt(k)] || '#06b6d4');

  // Find highest / lowest cluster for this attribute
  let highIdx = 0;
  let lowIdx = 0;
  means.forEach((v, i) => {
    if (v > means[highIdx]) highIdx = i;
    if (v < means[lowIdx]) lowIdx = i;
  });

  const hoverText = clusterKeys.map(
    (k, i) =>
      `Cluster ${k}<br>Mean: ${means[i].toFixed(4)}<br>Std: ±${stds[i].toFixed(4)}<br>N = ${counts[i].toLocaleString()}`
  );

  return (
    <div className="attribute-stats">
      {/* Attribute selector tabs */}
      <div className="cluster-tabs" style={{ flexWrap: 'wrap' }}>
        {features.map((feat) => (
          <button
            key={feat}
            className={`tab-btn ${feat === selectedAttribute ? 'active' : ''}`}
            onClick={() => setSelectedAttribute(feat)}
            style={{
              backgroundColor:
                feat === selectedAttribute ? '#06b6d4' : 'transparent',
              color:
                feat === selectedAttribute ? '#0a0e1a' : '#9ca3af',
              borderColor:
                feat === selectedAttribute ? '#06b6d4' : '#374151',
            }}
          >
            {feat}
          </button>
        ))}
      </div>

      {/* Two-column layout: chart + explanation */}
      <div
        className="attr-comparison-cols"
        style={{
          display: 'flex',
          gap: '20px',
          marginTop: '16px',
          alignItems: 'flex-start',
          flexWrap: 'wrap'
        }}
      >
        {/* LEFT — Bar chart (~60%) */}
        <div style={{ flex: '0 0 60%', minWidth: 0, minWidth: '280px' }}>
          <Plot
            data={[
              {
                type: 'bar',
                x: clusterLabels,
                y: means,
                marker: { color: barColors, opacity: 0.9 },
                hovertext: hoverText,
                hoverinfo: 'text',
                hoverlabel: { namelength: -1 },
                textposition: 'none',
              },
            ]}
            layout={{
              height: 320,
              margin: { t: 30, b: 70, l: 60, r: 20 },
              hovermode: 'x',
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: '#9ca3af', size: 12 },
              xaxis: {
                title: '',
                color: '#9ca3af',
                gridcolor: '#1e293b',
                tickvals: clusterLabels,
                ticktext: tickLabels,
              },
              yaxis: {
                title: { text: `Mean (${selectedAttribute})`, standoff: 10 },
                color: '#9ca3af',
                gridcolor: '#1e293b',
                zeroline: true,
                zerolinecolor: '#374151',
                zerolinewidth: 1,
              },
              bargap: 0.35,
            }}
            config={{
              displayModeBar: false,
              responsive: true,
            }}
            useResizeHandler
            style={{ width: '100%', height: '320px' }}
          />
        </div>

        {/* RIGHT — Explanation (~40%) */}
        <div
          style={{
            flex: '0 0 38%',
            minWidth: '240px',
            padding: '16px',
            borderLeft: '1px solid #1e293b',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}
        >
          <div>
            <h3
              style={{
                margin: '0 0 8px 0',
                fontSize: '14px',
                color: '#06b6d4',
                fontWeight: 600,
              }}
            >
              {selectedAttribute}
            </h3>
            <p
              style={{
                margin: 0,
                fontSize: '13px',
                lineHeight: 1.6,
                color: '#9ca3af',
              }}
            >
              {ATTRIBUTE_EXPLANATIONS[selectedAttribute] ||
                'No description available for this attribute.'}
            </p>
          </div>

          <div
            style={{
              fontSize: '13px',
              color: '#9ca3af',
              borderTop: '1px solid #1e293b',
              paddingTop: '12px',
              lineHeight: 1.8,
            }}
          >
            <div>
              <span style={{ color: '#22c55e' }}>▲ Highest:</span>{' '}
              Cluster {clusterKeys[highIdx]} ({means[highIdx].toFixed(4)})
            </div>
            <div>
              <span style={{ color: '#ef4444' }}>▼ Lowest:</span>{' '}
              Cluster {clusterKeys[lowIdx]} ({means[lowIdx].toFixed(4)})
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
