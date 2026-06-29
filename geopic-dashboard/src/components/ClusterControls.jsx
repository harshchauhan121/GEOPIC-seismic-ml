export default function ClusterControls({
  showOverlay,
  onToggleOverlay,
  clusterMethod,
  onChangeMethod,
  nClusters = 6,
}) {
  return (
    <div className="cluster-controls">
      <button
        className={`toggle-btn ${showOverlay ? 'active' : ''}`}
        onClick={onToggleOverlay}
        style={{
          backgroundColor: showOverlay ? '#06b6d4' : 'transparent',
          color: showOverlay ? '#0a0e1a' : '#9ca3af',
          border: showOverlay ? '1px solid #06b6d4' : '1px solid #374151',
        }}
      >
        Facies Overlay
      </button>

      <div className="segmented-control">
        <button
          className={`segment-btn ${clusterMethod === 'kmeans' ? 'active' : ''}`}
          onClick={() => onChangeMethod('kmeans')}
          style={{
            backgroundColor: clusterMethod === 'kmeans' ? '#06b6d4' : 'transparent',
            color: clusterMethod === 'kmeans' ? '#0a0e1a' : '#9ca3af',
            borderColor: clusterMethod === 'kmeans' ? '#06b6d4' : '#374151',
          }}
        >
          K-Means
        </button>
        <button
          className={`segment-btn ${clusterMethod === 'gmm' ? 'active' : ''}`}
          onClick={() => onChangeMethod('gmm')}
          style={{
            backgroundColor: clusterMethod === 'gmm' ? '#06b6d4' : 'transparent',
            color: clusterMethod === 'gmm' ? '#0a0e1a' : '#9ca3af',
            borderColor: clusterMethod === 'gmm' ? '#06b6d4' : '#374151',
          }}
        >
          GMM
        </button>
      </div>

      <span className="cluster-count">
        {nClusters} Clusters
      </span>
    </div>
  );
}
