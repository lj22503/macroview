import { useEffect, useState, useCallback } from 'react';
import { fetchDashboard } from '../api/macroApi';
import VIXChart from './VIXChart';
import '../styles/dashboard.css';

// 获取因子信号颜色
const getSignalColor = (signal) => {
  if (signal > 0) return 'green';
  if (signal < 0) return 'red';
  return 'yellow';
};

const getSignalLabel = (signal) => {
  if (signal > 0) return '看多';
  if (signal < 0) return '看空';
  return '中性';
};

// 单个指标卡片
function MetricCard({ title, value, change, note, signal, unit = '' }) {
  const signalClass = signal > 0 ? 'signal-bull' : signal < 0 ? 'signal-bear' : 'signal-neutral';
  const signalText = signal != null ? getSignalLabel(signal) : null;

  return (
    <div className="card">
      <div className="title">{title}</div>
      <div className="number">
        {value ?? '--'}
        {unit && <span style={{ fontSize: 14, color: 'var(--text-dim)', marginLeft: 4 }}>{unit}</span>}
        {change && <span className={`change ${change > 0 ? 'up' : 'down'}`}>{change > 0 ? '+' : ''}{change}</span>}
      </div>
      {note && <div className="note">{note}</div>}
      {signalText && <span className={`signal ${signalClass}`}>{signalText}</span>}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchAll = useCallback(() => {
    setLoading(true);
    setError(false);
    fetchDashboard()
      .then(d => {
        if (!d || !d.meta) { setError(true); return; }
        setData(d);
        setError(false);
      })
      .catch(() => setError(true))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { fetchAll(); }, [fetchAll]);

  if (loading) {
    return (
      <div className="loading-screen">
        {[...Array(6)].map((_, i) => <div key={i} className="skeleton-card" />)}
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="error-screen">
        <p>数据加载失败，请检查网络或稍后重试</p>
        <button className="retry-btn" onClick={fetchAll}>重新加载</button>
      </div>
    );
  }

  const { overview = {}, china_core = {}, global_macro = {}, fx_liquidity = {}, assets = {}, risk_monitor = {}, meta = {} } = data;
  const fd = overview.factor_details || {};

  const riskClass = overview.bias === 'RISK_ON' ? 'risk-on' : overview.bias === 'RISK_OFF' ? 'risk-off' : 'neutral';
  const riskText = overview.bias === 'RISK_ON' ? 'RISK ON' : overview.bias === 'RISK_OFF' ? 'RISK OFF' : 'NEUTRAL';

  return (
    <div className="dashboard">
      {/* 顶部标题栏 */}
      <div className="header">
        <h1>📊 宏观量化仪表盘 · 中国视角</h1>
        <span className="update-time">📅 {meta.data_date || '--'} {meta.updated_at ? new Date(meta.updated_at).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : ''}</span>
      </div>

      {/* 顶层三栏 */}
      <div className="top-level">
        {/* 风险偏好 */}
        <div className="risk-card">
          <div className="label">🌍 全球风险偏好</div>
          <div className={`value ${riskClass}`}>{riskText}</div>
          <div className="sub">置信度 {overview.confidence || '--'}%</div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
            VIX {risk_monitor.vix?.value?.toFixed(2) || '--'} · MOVE {risk_monitor.move_idx?.value || '--'}
          </div>
        </div>

        {/* 主要驱动因素 */}
        <div className="driver-card">
          <div className="label">⚡ 主要驱动因素</div>
          <div className="tags">
            {(overview.primary_driver || []).map((d, i) => (
              <span key={i} className="tag">{d}</span>
            ))}
            {(!overview.primary_driver || overview.primary_driver.length === 0) && (
              <span className="tag">数据加载中</span>
            )}
          </div>
          {overview.narrative && (
            <div style={{ marginTop: 10, fontSize: 13, color: 'var(--text-secondary)', borderTop: '1px solid #1e2a3a', paddingTop: 10 }}>
              {overview.narrative}
            </div>
          )}
        </div>

        {/* 配置建议 */}
        <div className="risk-card">
          <div className="label">🎯 权益仓位建议</div>
          <div className="value" style={{ color: 'var(--green)' }}>{overview.suggestions?.equity || '--'}%</div>
          <div className="sub">状态：{overview.label || '--'}</div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 16 }}>
            <span>债券 <span style={{ color: 'var(--yellow)' }}>{overview.suggestions?.bond || '--'}%</span></span>
            <span>黄金 <span style={{ color: 'var(--yellow)' }}>{overview.suggestions?.gold || '--'}%</span></span>
            <span>现金 <span style={{ color: 'var(--text-dim)' }}>{overview.suggestions?.cash || '--'}%</span></span>
          </div>
        </div>
      </div>

      {/* 模块二：中国内核 */}
      <div className="section-title">🇨🇳 模块二 · 中国内核</div>
      <div className="grid-4">
        <MetricCard
          title="📈 官方制造业PMI"
          value={china_core.cn_pmi_official?.value}
          note="经济冷热（>50扩张）"
          signal={fd.m1_m2_spread?.signal}
        />
        <MetricCard
          title="📊 M1-M2 剪刀差"
          value={china_core.cn_m1_m2_spread?.spread?.toFixed(1)}
          unit="%"
          note="资金活化（收窄=牛市）"
          signal={fd.m1_m2_spread?.signal}
        />
        <MetricCard
          title="🏷️ CPI / PPI 同比"
          value={`${china_core.cn_cpi_yy?.value ?? '--'} / ${china_core.cn_ppi_yy?.value ?? '--'}`}
          unit="%"
          note="居民通胀 / 工业出厂价格"
        />
        <MetricCard
          title="🏦 LPR（1Y）"
          value={china_core.cn_lpr_1y?.value}
          unit="%"
          note="货币政策锚"
        />
      </div>
      <div className="grid-2">
        <MetricCard
          title="📦 社融增量"
          value={china_core.cn_social_financing?.value}
          unit="万亿"
          note="信用扩张总闸门"
        />
        <MetricCard
          title="💰 北向资金3日累计"
          value={china_core.north_money_3d?.value}
          unit="亿"
          note="外资净买入A股"
          signal={fd.north_money?.signal}
        />
      </div>

      {/* 模块三：全球宏观 */}
      <div className="section-title">🌐 模块三 · 全球宏观（外部环境过滤器）</div>
      <div className="grid-3">
        <MetricCard
          title="🏭 美国ISM制造业PMI"
          value={global_macro.us_ism_pmi?.value}
          note="全球经济风向标"
        />
        <MetricCard
          title="🎯 美国核心PCE同比"
          value={global_macro.us_core_pce_yy?.value}
          unit="%"
          note="美联储降息开关"
          signal={global_macro.us_core_pce_yy?.value > 2.5 ? -1 : 1}
        />
        <MetricCard
          title="🏛️ 美联储资产负债表"
          value={global_macro.fed_balance_sheet?.value ? (global_macro.fed_balance_sheet.value / 10000000000000).toFixed(1) : '--'}
          unit="万亿"
          note="QE/QT力度"
        />
      </div>

      {/* 模块四：美元与流动性 */}
      <div className="section-title">💵 模块四 · 美元与全球流动性</div>
      <div className="grid-4">
        <MetricCard
          title="📌 DXY美元指数"
          value={fx_liquidity.dxy_idx?.value?.toFixed(2)}
          note=">105强势美元"
          signal={fx_liquidity.dxy_idx?.value > 105 ? -1 : fx_liquidity.dxy_idx?.value < 102 ? 1 : 0}
        />
        <MetricCard
          title="🇨🇳🇺🇸 中美10Y利差"
          value={fx_liquidity.cn_us_10y_spread?.value?.toFixed(0)}
          unit="bp"
          note="资本流向总开关"
          signal={fd.cn_us_spread?.signal}
        />
        <MetricCard
          title="🇨🇳 离岸人民币 USD/CNH"
          value={fx_liquidity.usd_cnh?.value?.toFixed(4)}
          note=">7.30贬值压力"
          signal={fx_liquidity.usd_cnh?.value > 7.3 ? -1 : 0}
        />
        <MetricCard
          title="🇯🇵 USD/JPY"
          value={fx_liquidity.usd_jpy?.value?.toFixed(2)}
          note="套息交易温度"
        />
      </div>

      {/* 模块五：全球核心资产 */}
      <div className="section-title">📈 模块五 · 全球核心资产行情</div>
      <div className="grid-4">
        <MetricCard
          title="🇺🇸 标普500"
          value={assets.spx?.value?.toLocaleString()}
          note="全球风险之锚"
        />
        <MetricCard
          title="🇨🇳 沪深300"
          value={assets.hs300?.value?.toLocaleString()}
          note="A股大盘基准"
        />
        <MetricCard
          title="🥇 黄金现货"
          value={assets.gold_spot?.value?.toLocaleString()}
          unit="$"
          note="避险+实际利率"
        />
        <MetricCard
          title="🛢️ WTI原油"
          value={assets.wti_oil?.value?.toFixed(2)}
          unit="$"
          note=">90压制制造业"
        />
      </div>
      <div className="grid-2">
        <MetricCard
          title="🏦 10Y美债收益率"
          value={assets.us_10y_yield?.value}
          unit="%"
          note="全球资产定价之锚"
        />
        <MetricCard
          title="🏛️ 10Y中债收益率"
          value={china_core.cn_10y_yield?.value ? (china_core.cn_10y_yield.value * 100).toFixed(2) : '--'}
          unit="%"
          note="人民币资产定价锚"
        />
      </div>

      {/* 模块六：波动率与风险 */}
      <div className="section-title">⚠️ 模块六 · 波动率与金融风险</div>
      <div className="grid-3">
        <MetricCard
          title="📊 VIX恐慌指数"
          value={risk_monitor.vix?.value?.toFixed(2)}
          note="美股隐含波动率"
          signal={fd.vix?.signal}
        />
        <MetricCard
          title="📈 MOVE债市波动率"
          value={risk_monitor.move_idx?.value?.toFixed(2)}
          note="美债恐慌温度计"
        />
        <MetricCard
          title="💳 美国高收益债利差"
          value={risk_monitor.hy_spread_oas?.value?.toFixed(0)}
          unit="bp"
          note="信用危机先兆"
          signal={fd.credit_spread?.signal}
        />
      </div>

      {/* 底部 */}
      <div className="footer">
        <span>📊 数据来源：FRED · AKShare · yfinance</span>
        <span>更新：{meta.updated_at ? new Date(meta.updated_at).toLocaleString('zh-CN') : '--'}</span>
      </div>
    </div>
  );
}
