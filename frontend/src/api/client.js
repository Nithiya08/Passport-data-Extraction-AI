import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  timeout: 300000, // 5 minutes timeout for large multi-page PDF processing
});

export async function checkServerHealth() {
  try {
    const res = await api.get('/health');
    return res.data;
  } catch (err) {
    // Try relative /api in case proxied by Vite
    try {
      const relRes = await axios.get('/api/health');
      return relRes.data;
    } catch {
      return { status: 'offline', gemini_configured: false };
    }
  }
}

export async function extractPassportDocuments(files, onProgress, forceRefresh = false) {
  const formData = new FormData();
  files.forEach(f => {
    formData.append('files', f);
  });

  const url = forceRefresh ? '/extract?force_refresh=true' : '/extract';

  try {
    const res = await api.post(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const percent = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(percent);
        }
      },
    });
    return res.data;
  } catch (err) {
    // If localhost direct failed, try relative
    if (err.code === 'ERR_NETWORK') {
      const relUrl = forceRefresh ? '/api/extract?force_refresh=true' : '/api/extract';
      const relRes = await axios.post(relUrl, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return relRes.data;
    }
    const message = err.response?.data?.error || err.response?.data?.detail || err.message || 'Extraction failed';
    throw new Error(message);
  }
}
  
export default api;

