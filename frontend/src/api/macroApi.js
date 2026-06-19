import axios from 'axios';

const GITHUB_RAW_BASE = 'https://raw.githubusercontent.com/lj22503/macroview/main/data';
const API_BASE = import.meta.env.VITE_API_URL;

const api = axios.create({
  timeout: 15000,
});

// 如果配置了 VITE_API_URL，优先用 API（开发环境）
// 否则直接从 GitHub Raw 读取 JSON（Vercel 部署环境）
export const fetchAllData = async () => {
  if (API_BASE) {
    // 开发环境：调用本地/远程 API
    const [overview, china, global_, assets] = await Promise.all([
      axios.get(`${API_BASE}/api/v1/overview`).catch(() => ({ data: {} })),
      axios.get(`${API_BASE}/api/v1/china`).catch(() => ({ data: {} })),
      axios.get(`${API_BASE}/api/v1/global`).catch(() => ({ data: {} })),
      axios.get(`${API_BASE}/api/v1/assets`).catch(() => ({ data: {} })),
    ]);
    return {
      china: china.data,
      fred: global_.data?.data,
      assets: assets.data?.data,
      overview: overview.data,
    };
  } else {
    // 生产环境（Vercel）：直接从 GitHub Raw 读取
    const resp = await axios.get(`${GITHUB_RAW_BASE}/all_indicators.json`);
    return resp.data;
  }
};

export const fetchChina = () => api.get(`${GITHUB_RAW_BASE}/all_indicators.json`).then(r => r.data.china);
export const fetchGlobal = () => api.get(`${GITHUB_RAW_BASE}/all_indicators.json`).then(r => r.data.fred);
export const fetchAssets = () => api.get(`${GITHUB_RAW_BASE}/all_indicators.json`).then(r => r.data.assets);