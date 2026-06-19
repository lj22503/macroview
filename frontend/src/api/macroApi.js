import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
});

export const fetchOverview = () => api.get('/api/v1/overview');
export const fetchChina = () => api.get('/api/v1/china');
export const fetchGlobal = () => api.get('/api/v1/global');
export const fetchAssets = () => api.get('/api/v1/assets');
export const fetchRisk = () => api.get('/api/v1/risk');
