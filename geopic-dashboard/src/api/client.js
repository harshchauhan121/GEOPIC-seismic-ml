const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function fetchWithFallback(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error.message);
    throw error;
  }
}

export async function fetchSeismicSection(downsample = 1) {
  return fetchWithFallback(`/api/seismic-section?downsample=${downsample}`);
}

export async function fetchClusterLabels(method = 'kmeans', downsample = 1) {
  return fetchWithFallback(`/api/cluster-labels?method=${method}&downsample=${downsample}`);
}

export async function fetchAttributeStats() {
  return fetchWithFallback('/api/attribute-stats');
}

export async function fetchTSNE() {
  return fetchWithFallback('/api/tsne');
}

export async function checkApiHealth() {
  try {
    const response = await fetch(`${BASE_URL}/health`, {
      method: 'GET',
    });
    return response.ok;
  } catch {
    return false;
  }
}
