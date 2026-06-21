import axios from 'axios';

const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/lj22503/macroview/main/data';
const API_BASE = import.meta.env.VITE_API_URL;

const api = axios.create({
  timeout: 15000,
});

// 统一全景接口（首屏使用）
export const fetchDashboard = async () => {
  if (API_BASE) {
    try {
      const resp = await axios.get(`${API_BASE}/api/v1/dashboard`);
      return resp.data;
    } catch (e) {
      console.error('Dashboard API failed:', e);
      throw e;
    }
  }
  // Fallback：从 GitHub 读取静态数据（无信号合成）
  const resp = await axios.get(`${GITHUB_RAW_BASE}/all_indicators.json`);
  return resp.data;
};

// 顶层概览（独立刷新）
export const fetchOverview = () => {
  if (!API_BASE) return Promise.reject(new Error('No API configured'));
  return axios.get(`${API_BASE}/api/v1/overview`).then(r => r.data);
};

// 各模块独立接口
export const fetchChinaCore = () => {
  if (!API_BASE) return Promise.reject(new Error('No API configured'));
  return axios.get(`${API_BASE}/api/v1/china-core`).then(r => r.data);
};

export const fetchGlobalMacro = () => {
  if (!API_BASE) return Promise.reject(new Error('No API configured'));
  return axios.get(`${API_BASE}/api/v1/global-macro`).then(r => r.data);
};

export const fetchFxLiquidity = () => {
  if (!API_BASE) return Promise.reject(new Error('No API configured'));
  return axios.get(`${API_BASE}/api/v1/fx-liquidity`).then(r => r.data);
};

export const fetchAssets = () => {
  if (!API_BASE) return Promise.reject(new Error('No API configured'));
  return axios.get(`${API_BASE}/api/v1/assets`).then(r => r.data);
};

export const fetchRisk = () => {
  if (!API_BASE) return Promise.reject(new Error('No API configured'));
  return axios.get(`${API_BASE}/api/v1/risk`).then(r => r.data);
};

export const fetchVixHistory = (days = 30) => {
  if (!API_BASE) return Promise.reject(new Error('No API configured'));
  return axios.get(`${API_BASE}/api/v1/vix-history`, { params: { days } });
};
