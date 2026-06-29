import { useState, useEffect, useCallback } from 'react';
import { fetchAttributeStats } from '../api/client';

export default function AttributeStats({ selectedCluster, onSelectCluster }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchAttributeStats();
      setStats(result);
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
          <span>Loading attribute statistics...</span>
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

  if (!stats || !stats.clusters) {
    return (
      <div className="attribute-stats">
        <div className="panel-error">No data available</div>
      </div>
    );
  }

  const features = stats.features || [];
  const clusterData = stats.clusters[selectedCluster];
  const clusterKeys = Object.keys(stats.clusters).sort((a, b) => parseInt(a) - parseInt(b));

  const maxValues = {};
  features.forEach((feature, idx) => {
    const values = clusterKeys.map((k) => stats.clusters[k].mean[idx] || 0);
    maxValues[idx] = Math.max(...values);
  });

  return (
    <div className="attribute-stats">
      <div className="cluster-tabs">
        {clusterKeys.map((k) => (
          <button
            key={k}
            className={`tab-btn ${parseInt(k) === selectedCluster ? 'active' : ''}`}
            onClick={() => onSelectCluster(parseInt(k))}
            style={{
              backgroundColor: parseInt(k) === selectedCluster ? '#06b6d4' : 'transparent',
              color: parseInt(k) === selectedCluster ? '#0a0e1a' : '#9ca3af',
              borderColor: parseInt(k) === selectedCluster ? '#06b6d4' : '#374151',
            }}
          >
            Cluster {k}
          </button>
        ))}
      </div>

      <div className="attribute-bars">
        {features.map((feature, idx) => {
          const mean = clusterData?.mean?.[idx] ?? 0;
          const std = clusterData?.std?.[idx] ?? 0;
          const maxVal = maxValues[idx] || 1;
          const widthPercent = maxVal > 0 ? (mean / maxVal) * 100 : 0;

          return (
            <div key={idx} className="bar-row">
              <span className="bar-label">{feature}</span>
              <div className="bar-track">
                <div
                  className="bar-fill"
                  style={{
                    width: `${widthPercent}%`,
                  }}
                />
              </div>
              <span className="bar-value">
                {mean.toFixed(3)} ± {std.toFixed(3)}
              </span>
            </div>
          );
        })}
      </div>

      <div className="sample-count">
        N = {clusterData?.count?.toLocaleString() || 0} samples
      </div>
    </div>
  );
}
