import { useState, useEffect } from 'react';
import { checkApiHealth } from './api/client';
import StatusPill from './components/StatusPill';
import SeismicViewer from './components/SeismicViewer';
import ClusterControls from './components/ClusterControls';
import TSNEPlot from './components/TSNEPlot';
import AttributeStats from './components/AttributeStats';
import AttributeComparison from './components/AttributeComparison';
import ClusterDistribution from './components/ClusterDistribution';
import './App.css';

export default function App() {
  const [showOverlay, setShowOverlay] = useState(false);
  const [clusterMethod, setClusterMethod] = useState('kmeans');
  const [selectedCluster, setSelectedCluster] = useState(0);
  const [apiStatus, setApiStatus] = useState('checking');

  useEffect(() => {
    const checkHealth = async () => {
      setApiStatus('checking');
      const isHealthy = await checkApiHealth();
      setApiStatus(isHealthy ? 'connected' : 'offline');
    };
    checkHealth();
  }, []);

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <span className="brand">SeisLytics</span>
          <span className="divider" />
          <span className="header-subtitle">ONGC GEOPIC | F3 Block | 3D Seismic Analysis</span>
        </div>
        <div className="header-right">
          <StatusPill status={apiStatus} />
        </div>
      </header>

      <main className="main-content">
        <div className="dashboard-stack">
          {/* SECTION 1 — Seismic Section */}
          <div className="panel panel-seismic">
            <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h2>Inline Section — F3 Block</h2>
            </div>
            <SeismicViewer
              showOverlay={showOverlay}
              clusterMethod={clusterMethod}
            />
            <div style={{ padding: '12px 0' }}>
              <ClusterControls
                showOverlay={showOverlay}
                onToggleOverlay={() => setShowOverlay(!showOverlay)}
                clusterMethod={clusterMethod}
                onChangeMethod={(method) => setClusterMethod(method)}
                nClusters={6}
              />
            </div>
          </div>

          {/* SECTION 2 — TSNE and Cluster Distribution */}
          <div className="two-col">
            <div className="panel panel-tsne">
              <div className="panel-header">
                <h2>t-SNE Cluster Separation</h2>
              </div>
              <TSNEPlot />
            </div>

            <div className="panel panel-distribution">
              <div className="panel-header">
                <h2>Cluster Sample Distribution</h2>
              </div>
              <ClusterDistribution />
            </div>
          </div>

          {/* SECTION 3 — Attribute Profiles */}
          <div className="panel panel-stats">
            <div className="panel-header">
              <h2>Per-Cluster Attribute Profiles</h2>
            </div>
            <AttributeStats
              selectedCluster={selectedCluster}
              onSelectCluster={(c) => setSelectedCluster(c)}
            />
          </div>

          {/* SECTION 4 — Attribute Comparison Across Clusters */}
          <div className="panel panel-stats">
            <div className="panel-header">
              <h2>Attribute Comparison Across Clusters</h2>
            </div>
            <AttributeComparison />
          </div>
        </div>
      </main>
    </div>
  );
}
