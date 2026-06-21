import { useEffect, useState, useCallback } from 'react';
import { fetchDashboard } from '../api/macroApi';
import StatusBar from './StatusBar';
import VIXChart from './VIXChart';
import IndicatorCard from './IndicatorCard';
import '../styles/dashboard.css';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchAll = useCallback(() => {
    setLoading(true);
    setError(false);
    fetchDashboard()
      .then(d => {
        const hasData = d && d.meta && d.meta.status !== 'error';
        if (!hasData) { setError(true); return; }
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
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="skeleton-card" />
        ))}
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

  // 获取因子的观点信息
  const getFactor = (name) => overview.factor_details?.[name] || {};

  return (
    <div>
      <StatusBar data={overview} />

      <div className="main-content">
        {/* 顶部：Risk Score 概览 */}
        <div className="card" style={{ gridColumn: '1 / -1' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <div className="card-title" style={{ marginBottom: 8 }}>宏观风险评分</div>
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
                <span className={`score-value ${overview.score >= 0 ? 'positive' : 'negative'}`}>
                  {overview.score != null ? overview.score.toFixed(2) : '--'}
                </span>
                <span style={{ color: '#6b7280', fontSize: 14 }}>/ 2.0</span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div className="card-title" style={{ marginBottom: 8 }}>配置建议</div>
              <div style={{ display: 'flex', gap: 16, fontSize: 13 }}>
                <span>权益 <span className="positive">{overview.suggestions?.equity || '--'}%</span></span>
                <span>债券 <span className="neutral">{overview.suggestions?.bond || '--'}%</span></span>
                <span>黄金 <span className="neutral">{overview.suggestions?.gold || '--'}%</span></span>
                <span>现金 <span className="negative">{overview.suggestions?.cash || '--'}%</span></span>
              </div>
            </div>
          </div>
          {overview.narrative && (
            <div style={{ marginTop: 12, color: '#9ca3af', fontSize: 13 }}>
              {overview.narrative}
            </div>
          )}
        </div>

        {/* VIX 卡片 + 观点 */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">VIX 恐慌指数</span>
            <span className={`view-badge ${getFactor('vix').signal > 0 ? 'positive' : getFactor('vix').signal < 0 ? 'negative' : 'neutral'}`}>
              {getFactor('vix').view || '--'}
            </span>
          </div>
          <div className={`card-value ${getFactor('vix').signal > 0 ? 'positive' : getFactor('vix').signal < 0 ? 'negative' : 'neutral'}`}>
            {risk_monitor.vix?.value != null ? risk_monitor.vix.value.toFixed(2) : '--'}
          </div>
          <VIXChart value={risk_monitor.vix?.value} />
          {getFactor('vix').narrative && (
            <div className="card-narrative">{getFactor('vix').narrative}</div>
          )}
        </div>

        {/* 中美利差卡片 + 观点 */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">中美利差 (10Y)</span>
            <span className={`view-badge ${getFactor('cn_us_spread').signal > 0 ? 'positive' : getFactor('cn_us_spread').signal < 0 ? 'negative' : 'neutral'}`}>
              {getFactor('cn_us_spread').view || '--'}
            </span>
          </div>
          <div className={`card-value ${getFactor('cn_us_spread').signal > 0 ? 'positive' : getFactor('cn_us_spread').signal < 0 ? 'negative' : 'neutral'}`}>
            {fx_liquidity.cn_us_10y_spread?.value != null ? `${fx_liquidity.cn_us_10y_spread.value.toFixed(0)} bp` : '--'}
          </div>
          <div className="card-meta">
            趋势：{getFactor('cn_us_spread').trend || '--'}
          </div>
          {getFactor('cn_us_spread').narrative && (
            <div className="card-narrative">{getFactor('cn_us_spread').narrative}</div>
          )}
        </div>

        {/* 10Y 美债 */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">10Y 美债收益率</span>
          </div>
          <div className="card-value neutral">
            {assets.us_10y_yield?.value != null ? `${assets.us_10y_yield.value}%` : '--'}
          </div>
          <div className="card-meta">全球资产定价之锚</div>
        </div>

        {/* 核心 PCE */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">美国核心PCE</span>
          </div>
          <div className={`card-value ${(global_macro.us_core_pce_yy?.value || 0) < 2.5 ? 'positive' : 'negative'}`}>
            {global_macro.us_core_pce_yy?.value != null ? `${global_macro.us_core_pce_yy.value}%` : '--'}
          </div>
          <div className="card-meta">美联储降息唯一开关</div>
        </div>

        {/* 模块一：中国内核 */}
        <div className="module-title" style={{ gridColumn: '1 / -1' }}>中国内核</div>
        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard
            label="官方制造业PMI"
            value={china_core.cn_pmi_official?.value}
            view={china_core.cn_pmi_official?.view}
            narrative={china_core.cn_pmi_official?.narrative}
          />
          <IndicatorCard
            label="CPI同比"
            value={china_core.cn_cpi_yy?.value}
            unit="%"
            view={china_core.cn_cpi_yy?.view}
            narrative={china_core.cn_cpi_yy?.narrative}
          />
          <IndicatorCard
            label="PPI同比"
            value={china_core.cn_ppi_yy?.value}
            unit="%"
            view={china_core.cn_ppi_yy?.view}
            narrative={china_core.cn_ppi_yy?.narrative}
          />
          <IndicatorCard
            label="M1-M2剪刀差"
            value={china_core.cn_m1_m2_spread?.spread || china_core.cn_m1_m2_spread}
            unit="%"
            trend={(china_core.cn_m1_m2_spread?.trend || '持平') === '收窄' ? 'up' : 'down'}
            view={getFactor('m1_m2_spread').view}
            narrative={getFactor('m1_m2_spread').narrative}
          />
          <IndicatorCard
            label="社融增量"
            value={china_core.cn_social_financing?.value}
            unit="万亿"
            view={china_core.cn_social_financing?.view}
            narrative={china_core.cn_social_financing?.narrative}
          />
          <IndicatorCard
            label="LPR (1Y)"
            value={china_core.cn_lpr_1y?.value}
            unit="%"
            view={china_core.cn_lpr_1y?.view}
            narrative={china_core.cn_lpr_1y?.narrative}
          />
          <IndicatorCard
            label="北向资金(3日)"
            value={china_core.north_money_3d}
            unit="亿"
            view={getFactor('north_money').view}
            narrative={getFactor('north_money').narrative}
          />
        </div>

        {/* 模块二：全球宏观 */}
        <div className="module-title" style={{ gridColumn: '1 / -1' }}>全球宏观</div>
        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard
            label="美国ISM PMI"
            value={global_macro.us_ism_pmi?.value}
            view={global_macro.us_ism_pmi?.view}
            narrative={global_macro.us_ism_pmi?.narrative}
          />
          <IndicatorCard
            label="DXY美元指数"
            value={fx_liquidity.dxy_idx?.value}
            view={fx_liquidity.dxy_idx?.view}
            narrative={fx_liquidity.dxy_idx?.narrative}
          />
          <IndicatorCard
            label="高收益债利差"
            value={risk_monitor.hy_spread_oas?.value}
            unit="bp"
            view={getFactor('credit_spread').view}
            narrative={getFactor('credit_spread').narrative}
          />
        </div>

        {/* 模块三：全球核心资产 */}
        <div className="module-title" style={{ gridColumn: '1 / -1' }}>全球核心资产</div>
        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="标普 500" value={assets.spx?.value} unit={assets.spx?.currency} />
          <IndicatorCard label="沪深 300" value={assets.hs300?.value} />
          <IndicatorCard label="黄金现货" value={assets.gold_spot?.value} unit={assets.gold_spot?.currency} />
          <IndicatorCard label="WTI原油" value={assets.wti_oil?.value} unit={assets.wti_oil?.currency} />
          <IndicatorCard label="USD/CNH" value={fx_liquidity.usd_cnh?.value} />
        </div>

        {/* 模块六：波动率与风险 */}
        <div className="module-title" style={{ gridColumn: '1 / -1' }}>波动率与风险</div>
        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="MOVE指数" value={risk_monitor.move_idx?.value} />
          <IndicatorCard label="TED利差" value={risk_monitor.ted_spread?.value} unit="bp" />
          <IndicatorCard label="A股隐含波动率" value={risk_monitor.cn_vix?.value} unit="%" />
        </div>

        <div style={{ gridColumn: '1 / -1', textAlign: 'center', color: '#6b7280', fontSize: 12, marginTop: 8 }}>
          数据更新时间：{meta.updated_at || '--'} · 数据日期：{meta.data_date || '--'}
        </div>
      </div>
    </div>
  );
}
