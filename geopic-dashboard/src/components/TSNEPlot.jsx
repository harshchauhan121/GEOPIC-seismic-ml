import { useState, useEffect, useCallback } from 'react';
import Plot from 'react-plotly.js';
import { fetchTSNE } from '../api/client';
import { CLUSTER_COLORS_HEX } from '../constants/clusterColors';

export default function TSNEPlot() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchTSNE();
      setData(result);
      setLoading(false);
    } catch {
      setError('Failed to load t-SNE projection');
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (loading) {
    return (
      <div className="tsne-container">
        <div className="skeleton skeleton-plot">
          <span>Loading t-SNE projection...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="tsne-container">
        <div className="panel-error">
          <span>{error}</span>
          <button onClick={loadData} className="retry-link">Retry</button>
        </div>
      </div>
    );
  }

  if (!data || !data.x || !data.y || !data.labels) {
    return (
      <div className="tsne-container">
        <div className="panel-error">No data available</div>
      </div>
    );
  }

  const traces = [];
  for (let i = 0; i < 6; i++) {
    const clusterX = [];
    const clusterY = [];
    for (let j = 0; j < data.labels.length; j++) {
      if (data.labels[j] === i) {
        clusterX.push(data.x[j]);
        clusterY.push(data.y[j]);
      }
    }
    traces.push({
      x: clusterX,
      y: clusterY,
      type: 'scattergl',
      mode: 'markers',
      marker: {
        color: CLUSTER_COLORS_HEX[i],
        size: 3,
        opacity: 0.7,
      },
      name: `Cluster ${i}`,
      hoverinfo: 'skip',
    });
  }

  const layout = {
    paper_bgcolor: '#0a0e1a',
    plot_bgcolor: '#0a0e1a',
    margin: { l: 40, r: 20, t: 20, b: 40 },
    xaxis: {
      showgrid: false,
      zeroline: false,
      showticklabels: true,
      tickfont: { color: '#6b7280', family: 'JetBrains Mono' },
      linecolor: '#374151',
    },
    yaxis: {
      showgrid: false,
      zeroline: false,
      showticklabels: true,
      tickfont: { color: '#6b7280', family: 'JetBrains Mono' },
      linecolor: '#374151',
    },
    showlegend: false,
    autosize: true,
    height: 350,
  };

  const config = {
    displayModeBar: false,
    responsive: true,
  };

  return (
    <div className="tsne-container">
      <div className="tsne-plot-wrapper" style={{ width: '100%' }}>
        <Plot
          data={traces}
          layout={layout}
          config={config}
          style={{ width: '100%', height: '350px' }}
          useResizeHandler={true}
        />
      </div>
      <div className="tsne-legend">
        {CLUSTER_COLORS_HEX.map((color, idx) => (
          <span key={idx} className="legend-pill" style={{ borderColor: color }}>
            Cluster {idx}
          </span>
        ))}
      </div>
    </div>
  );
}
