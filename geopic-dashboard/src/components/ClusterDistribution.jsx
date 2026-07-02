import { useState, useEffect, useCallback } from 'react';
import { fetchAttributeStats } from '../api/client';
import { CLUSTER_COLORS_HEX } from '../constants/clusterColors';

export default function ClusterDistribution() {
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
      setError('Failed to load sample distribution');
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
          <span>Loading distribution...</span>
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

  if (!stats || !stats.clusters) return null;

  const clusterKeys = Object.keys(stats.clusters).sort((a, b) => parseInt(a) - parseInt(b));
  
  let totalSamples = 0;
  clusterKeys.forEach((k) => {
    totalSamples += stats.clusters[k].count;
  });

  return (
    <div className="attribute-stats" style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {clusterKeys.map((k) => {
        const count = stats.clusters[k].count;
        const percentage = totalSamples > 0 ? ((count / totalSamples) * 100).toFixed(1) : 0;
        const color = CLUSTER_COLORS_HEX[parseInt(k)];

        return (
          <div key={k} className="bar-row" style={{ gridTemplateColumns: '90px 1fr 100px', gap: '12px', alignItems: 'center' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ width: '12px', height: '12px', borderRadius: '50%', backgroundColor: color }} />
              <span className="bar-label">Cluster {k}</span>
            </div>
            
            <div className="bar-track">
              <div
                className="bar-fill"
                style={{
                  width: `${percentage}%`,
                  backgroundColor: color
                }}
              />
            </div>
            
            <span className="bar-value" style={{ textAlign: 'right' }}>
              {count.toLocaleString()} ({percentage}%)
            </span>
          </div>
        );
      })}
    </div>
  );
}
