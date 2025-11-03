import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor to include auth token if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('auth_token');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// API endpoints
export const jobsAPI = {
  getAll: () => api.get('/api/jobs'),
  search: (query) => api.get(`/api/jobs/search?query=${encodeURIComponent(query)}`),
  getById: (id) => api.get(`/api/jobs/${id}`),
  scrape: (url) => api.post('/api/jobs/scrape', { url }),
  score: (jobId) => api.post(`/api/jobs/${jobId}/score`),
  apply: (jobId, applicationData) => api.post(`/api/jobs/${jobId}/apply`, applicationData),
};

export const applicationsAPI = {
  getAll: () => api.get('/api/applications'),
  getById: (id) => api.get(`/api/applications/${id}`),
  update: (id, data) => api.put(`/api/applications/${id}`, data),
  delete: (id) => api.delete(`/api/applications/${id}`),
};

export const profileAPI = {
  get: () => api.get('/api/profile'),
  update: (data) => api.put('/api/profile', data),
  uploadResume: (file) => {
    const formData = new FormData();
    formData.append('resume', file);
    return api.post('/api/upload/resume', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};

export const preferencesAPI = {
  get: () => api.get('/api/preferences'),
  update: (data) => api.put('/api/preferences', data),
};

export const settingsAPI = {
  get: () => api.get('/api/settings'),
  update: (data) => api.put('/api/settings', data),
};

export const statsAPI = {
  get: (days = 30) => api.get(`/api/stats?days=${days}`),
  dashboard: () => api.get('/api/stats/dashboard'),
};

export const agentsAPI = {
  scraper: {
    scrape: (url) => api.post('/api/agents/scraper/scrape', { url }),
    status: () => api.get('/api/agents/scraper/status'),
  },
  scorer: {
    score: (jobId, resumeText) => api.post('/api/agents/scorer/score', { job_id: jobId, resume_text: resumeText }),
    bulkScore: (jobIds) => api.post('/api/agents/scorer/bulk-score', { job_ids: jobIds }),
  },
  autoApply: {
    apply: (jobId) => api.post('/api/agents/auto-apply/apply', { job_id: jobId }),
    configure: (settings) => api.put('/api/agents/auto-apply/settings', settings),
  },
  tracker: {
    track: (applicationId) => api.post('/api/agents/tracker/track', { application_id: applicationId }),
    updateStatus: (applicationId, status) => api.put(`/api/agents/tracker/applications/${applicationId}`, { status }),
  },
  supervisor: {
    status: () => api.get('/api/agents/supervisor/status'),
    coordinate: (task) => api.post('/api/agents/supervisor/coordinate', task),
  },
};

export default api;
