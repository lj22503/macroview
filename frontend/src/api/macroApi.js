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
    }
  }
  // Fallback：从 GitHub 读取静态数据
  try {
    const resp = await axios.get(`${GITHUB_RAW_BASE}/all_indicators.json`);
    return normalizeGithubData(resp.data);
  } catch (e) {
    console.error('GitHub fetch failed:', e);
    throw e;
  }
};

// 将 GitHub JSON 格式转换为前端期望的格式
function normalizeGithubData(raw) {
  const { meta, overview, china, fred, assets } = raw;

  // 构建 factor_details（如果不存在）
  const factorDetails = overview?.factor_details || generateFactorDetails(fred, china);

  return {
    meta: meta || { updated_at: new Date().toISOString(), data_date: new Date().toISOString().slice(0, 10), status: 'success' },
    overview: {
      bias: overview?.bias || 'NEUTRAL',
      confidence: overview?.confidence || 50,
      score: overview?.score || 0,
      label: overview?.label || '数据加载中',
      primary_driver: overview?.primary_driver || [],
      suggestions: overview?.suggestions || { equity: 50, bond: 30, gold: 10, cash: 10 },
      narrative: overview?.narrative || '数据加载中',
      factor_details: factorDetails,
    },
    china_core: normalizeChinaData(china),
    global_macro: normalizeFredGlobal(fred),
    fx_liquidity: normalizeFxLiquidity(fred, assets),
    assets: normalizeAssets(assets, fred),
    risk_monitor: normalizeRiskMonitor(fred),
  };
}

function generateFactorDetails(fred, china) {
  const vix = fred?.vix?.value;
  const spread = calculateSpread(china?.cn_10y_yield?.value, fred?.us_10y_yield?.value);
  const hySpread = fred?.hy_spread_oas?.value;
  const northMoney = china?.north_money_3d?.value;

  return {
    vix: { signal: vix ? (vix < 14 ? 2 : vix < 18 ? 1 : vix < 22 ? 0 : vix < 28 ? -1 : -2) : 0, weight: 0.15, view: '--', narrative: '' },
    cn_us_spread: { signal: spread ? (spread > -150 ? 2 : spread > -200 ? 1 : spread > -250 ? 0 : -1) : 0, weight: 0.20, view: '--', narrative: '' },
    m1_m2_spread: { signal: 0, weight: 0.25, view: '--', narrative: '' },
    north_money: { signal: northMoney ? (northMoney > 100 ? 2 : northMoney > 50 ? 1 : northMoney > -50 ? 0 : northMoney > -100 ? -1 : -2) : 0, weight: 0.15, view: '--', narrative: '' },
    credit_spread: { signal: hySpread ? (hySpread < 350 ? 2 : hySpread < 450 ? 1 : hySpread < 550 ? 0 : hySpread < 700 ? -1 : -2) : 0, weight: 0.25, view: '--', narrative: '' },
  };
}

function calculateSpread(cnYield, usYield) {
  if (cnYield && usYield) return (cnYield - usYield) * 100;
  return null;
}

function normalizeChinaData(china) {
  return {
    cn_pmi_official: { value: china?.cn_pmi_official?.value, source: 'AKShare' },
    cn_pmi_caixin: { value: china?.cn_pmi_caixin?.value, source: 'AKShare' },
    cn_cpi_yy: { value: china?.cn_cpi_yy?.value, source: 'AKShare' },
    cn_ppi_yy: { value: china?.cn_ppi_yy?.value, source: 'AKShare' },
    cn_m1_m2_spread: china?.cn_m1_m2_spread || null,
    cn_lpr_1y: { value: china?.cn_lpr_1y?.value, source: 'AKShare' },
    cn_social_financing: { value: china?.cn_social_financing?.value, source: 'AKShare' },
    cn_10y_yield: china?.cn_10y_yield || null,
    north_money_3d: { value: china?.north_money_3d?.value || china?.north_money?.value, source: 'AKShare' },
    north_money: { value: china?.north_money?.value, source: 'AKShare' },
  };
}

function normalizeFredGlobal(fred) {
  return {
    us_ism_pmi: { value: fred?.us_ism_pmi?.value, source: 'FRED' },
    us_core_pce_yy: { value: fred?.us_core_pce_yy?.value, source: 'FRED' },
    fed_balance_sheet: { value: fred?.fed_balance_sheet?.value, source: 'FRED' },
    on_rrp_balance: { value: fred?.on_rrp_balance?.value, source: 'FRED' },
    us_10y_yield: { value: fred?.us_10y_yield?.value, source: 'FRED' },
    us_2y_yield: { value: fred?.us_2y_yield?.value, source: 'FRED' },
  };
}

function normalizeFxLiquidity(fred, assets) {
  const cn10y = assets?.cn_10y_yield?.value || fred?.cn_10y_yield;
  const us10y = fred?.us_10y_yield?.value;
  const spread = cn10y && us10y ? (cn10y - us10y) * 100 : null;

  return {
    dxy_idx: { value: fred?.dxy_idx?.value, source: 'FRED' },
    cn_us_10y_spread: { value: spread, source: 'calculated' },
    usd_cnh: { value: assets?.usd_cnh?.value, source: 'yfinance' },
    usd_jpy: { value: assets?.usd_jpy?.value, source: 'yfinance' },
  };
}

function normalizeAssets(assets, fred) {
  return {
    spx: { value: assets?.spx?.value || fred?.spx?.value, source: 'FRED/yfinance' },
    hs300: { value: assets?.hs300?.value, source: 'yfinance' },
    gold_spot: { value: assets?.gold_spot?.value || assets?.gold?.value, source: 'yfinance' },
    wti_oil: { value: assets?.wti_oil?.value || assets?.crude?.value, source: 'yfinance' },
    us_10y_yield: { value: fred?.us_10y_yield?.value, unit: '%', source: 'FRED' },
  };
}

function normalizeRiskMonitor(fred) {
  return {
    vix: { value: fred?.vix?.value, source: 'FRED' },
    move_idx: { value: fred?.move_idx?.value, source: 'FRED' },
    hy_spread_oas: { value: fred?.hy_spread_oas?.value, source: 'FRED' },
    ted_spread: { value: fred?.ted_spread?.value, source: 'FRED' },
    cn_vix: { value: fred?.cn_vix?.value, source: 'FRED' },
  };
}

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
