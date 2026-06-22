import { useState, useEffect } from 'react';
import { fetchDashboard } from '../api/macroApi';
import VIXChart from './VIXChart';
import '../styles/dashboard.css';

// 指标解释数据（从 docs/页面指标解释.txt）
const FIELD_EXPLANATIONS = {
  // === 中国内核模块 ===
  '官方制造业PMI': '经济体温计。>50=经济在扩张（发热），<50=在收缩（发冷）。每月第一个公布，最领先指标。',
  '财新制造业PMI': '中小企业+出口景气度。与官方PMI背离时需警惕（可能反映结构分化）。',
  'M1-M2剪刀差': '企业花钱意愿指数。收窄=企业敢花钱，经济变好；走阔=企业躺平，经济萎靡。',
  'CPI同比': '物价涨速。<1%=通缩（东西太便宜），>3%=通胀（东西太贵），1-2%最舒服。',
  'PPI同比': '工厂产品卖得好不好。负值=打折也卖不动（利润承压），正值=能涨价（利润改善）。',
  'LPR (1年)': '企业贷款基准利率。下调=宽松（利好），上调=收紧（利空）。',
  '社融增量': '实体经济拿到多少资金。回升=信用扩张（利好），回落=借不到钱（利空）。',
  '北向资金': '外资买卖A股的金额。持续流入=外资看好，持续流出=外资撤退。',

  // === 全球宏观模块 ===
  '美国ISM PMI': '全球经济风向标。>50=美国经济好（利好全球），<50=美国经济差（拖累全球）。',
  '核心PCE': '美联储最关心的通胀指标。>3%=不能降息（利空），<2.5%=可以降息（利好全球）。',
  '美国CPI同比': '公众通胀数据，市场波动最大的通胀指标。超预期→股跌债涨。',
  '联邦基金利率': '美国基准利率（美联储政策利率）。高位=全球流动性收紧。',
  '美联储资产负债表': '全球资金水龙头。扩表=放水（利好），缩表=抽水（利空）。',
  '隔夜逆回购': '市场闲钱多少。规模大=资金充裕，接近0=流动性紧张预警。',

  // === 美元与流动性模块 ===
  'DXY美元指数': '美元强弱。>105=强势美元（压制A股），<100=弱势美元（利好A股）。',
  '中美利差': '外资流向总开关。收窄=资本回流中国（利好），走阔=资本外逃（利空）。',
  'USD/CNH': '人民币汇率。>7.30=贬值压力（利空A股），<7.10=升值（利好）。',
  'USD/JPY': '套息交易温度。日元急升=套息平仓（危险信号，可能引发流动性危机）。',

  // === 全球核心资产模块 ===
  '标普500': '美股大盘。涨=全球风险偏好高，跌=全球避险。',
  '沪深300': 'A股大盘。中国最大300家公司，A股成绩单。',
  '恒生指数': '港股晴雨表。对全球流动性特别敏感，美元强时港股通常承压。',
  '日经225': '日本股市。套息交易+出口导向，对全球流动性高度敏感。',
  '黄金': '避险资产。地缘风险+实际利率下行时上涨。',
  'WTI原油': '通胀油门。>90$=通胀压力大（利空），<70$=通胀压力小（利好）。',
  '比特币': '极致Risk On流动性末梢。流动性极度充裕时上涨，流动性危机时暴跌。',
  '10Y美债收益率': '全球资产定价之锚。收益率上行=利率冲击（利空成长股）。',
  '10Y中债收益率': '人民币资产定价锚。与美债利差影响外资流向。',

  // === 波动率与风险模块 ===
  'VIX恐慌指数': '全球心跳。VIX>25=市场恐慌（利空），<15=过度自满（警惕变盘）。',
  'MOVE指数': '债市恐慌温度。急升=债券市场剧烈波动，预示更大风险。',
  '高收益债利差': '企业借钱难易度。>600bp=危险（可能爆发危机），<450bp=安全。',
  'A股VIX': 'A股恐慌指数。>35=A股恐慌性抛售（可能见底），<15=过于平静（警惕变盘）。',

  // === 顶层概览 ===
  '全球风险偏好': '就像开车时的红绿灯。RISK_ON=绿灯（可加速进攻），RISK_OFF=红灯（踩刹车防守），NEUTRAL=黄灯（减速观察）。',
  '置信度': '这个判断有多大的把握。置信度越高，越值得相信当前的信号。',
  '权益仓位建议': '现在建议把多少比例的钱买股票。剩下的是债券/黄金/现金。',
  '主要驱动因素': '今天市场上涨/下跌的主要原因。告诉你需要盯住什么因素。',
};

// 获取信号颜色和文字
const getSignalInfo = (signal) => {
  if (signal > 0) return { class: 'signal-bull', text: '看多', color: 'var(--green)' };
  if (signal < 0) return { class: 'signal-bear', text: '看空', color: 'var(--red)' };
  return { class: 'signal-neutral', text: '中性', color: 'var(--yellow)' };
};

// 单个指标卡片（带 tooltip）
function MetricCard({ title, value, unit = '', note, signal, explanation }) {
  const [showTip, setShowTip] = useState(false);
  const signalInfo = signal != null ? getSignalInfo(signal) : null;
  const explanation_text = FIELD_EXPLANATIONS[title] || explanation || '';

  return (
    <div className="card">
      <div className="title-row">
        <div className="title">{title}</div>
        {explanation_text && (
          <span
            className="info-btn"
            onMouseEnter={() => setShowTip(true)}
            onMouseLeave={() => setShowTip(false)}
            style={{ position: 'relative' }}
          >
            ❓
            {showTip && (
              <div className="tooltip" style={{ top: '100%', left: 0 }}>
                {explanation_text}
              </div>
            )}
          </span>
        )}
      </div>
      <div className="number">
        {value ?? '--'}
        {unit && <span style={{ fontSize: 14, color: 'var(--text-dim)', marginLeft: 4 }}>{unit}</span>}
      </div>
      {note && <div className="note">{note}</div>}
      {signalInfo && (
        <span className={`signal ${signalInfo.class}`} style={{ color: signalInfo.color }}>
          {signalInfo.text}
        </span>
      )}
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchAll = () => {
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
  };

  useEffect(() => { fetchAll(); }, []);

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

  // 计算中美利差
  const cn10yYield = china_core.cn_10y_yield?.value || 0;
  const us10yYield = global_macro.us_10y_yield?.value || 0;
  const cnUsSpread = (cn10yYield && us10yYield) ? ((cn10yYield - us10yYield) * 100).toFixed(0) : null;

  return (
    <div className="dashboard">
      {/* 顶部标题栏 */}
      <div className="header">
        <h1>📊 宏观量化仪表盘 · 中国视角</h1>
        <span className="update-time">
          📅 {meta.data_date || '--'}
        </span>
      </div>

      {/* ========== 一、顶层概览 ========== */}
      <div className="section-title" style={{ marginTop: 0 }}>
        📋 一、顶层概览
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: 8 }}>
          — 仪表盘的「结论区」，告诉你现在该怎么办
        </span>
      </div>
      <div className="top-level">
        {/* 风险偏好 */}
        <div className="risk-card">
          <div className="label">🌍 全球风险偏好 <span style={{ fontSize: 11, opacity: 0.7 }}>（信号灯）</span></div>
          <div className={`value ${riskClass}`}>{riskText}</div>
          <div className="sub">置信度 {overview.confidence || '--'}%</div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
            VIX {risk_monitor.vix?.value?.toFixed(2) || '--'} · MOVE {risk_monitor.move_idx?.value?.toFixed(2) || '--'}
          </div>
        </div>

        {/* 主要驱动因素 */}
        <div className="driver-card">
          <div className="label">⚡ 主要驱动因素 <span style={{ fontSize: 11, opacity: 0.7 }}>（今天看什么）</span></div>
          <div className="tags">
            {(overview.primary_driver || []).map((d, i) => (
              <span key={i} className="tag">{d}</span>
            ))}
            {(!overview.primary_driver || overview.primary_driver.length === 0) && (
              <span className="tag">等待信号</span>
            )}
          </div>
          {overview.narrative && (
            <div style={{ marginTop: 10, fontSize: 13, color: 'var(--text-secondary)', borderTop: '1px solid #1e2a3a', paddingTop: 10, lineHeight: 1.5 }}>
              📌 {overview.narrative}
            </div>
          )}
        </div>

        {/* 配置建议 */}
        <div className="risk-card">
          <div className="label">🎯 仓位建议 <span style={{ fontSize: 11, opacity: 0.7 }}>（怎么配）</span></div>
          <div className="value" style={{ color: 'var(--green)' }}>{overview.suggestions?.equity || '--'}%</div>
          <div className="sub">{overview.label || '--'}</div>
          <div style={{ marginTop: 8, fontSize: 13, color: 'var(--text-secondary)', display: 'flex', gap: 16, flexWrap: 'wrap' }}>
            <span>债券 <span style={{ color: 'var(--yellow)' }}>{overview.suggestions?.bond || '--'}%</span></span>
            <span>黄金 <span style={{ color: 'var(--yellow)' }}>{overview.suggestions?.gold || '--'}%</span></span>
            <span>现金 <span style={{ color: 'var(--text-muted)' }}>{overview.suggestions?.cash || '--'}%</span></span>
          </div>
        </div>
      </div>

      {/* ========== 二、中国内核 ========== */}
      <div className="section-title">
        🇨🇳 二、中国内核
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: 8 }}>
          — 中国经济的「体检报告」
        </span>
      </div>
      <div className="grid-4">
        <MetricCard title="官方制造业PMI" value={china_core.cn_pmi_official?.value} note=">50扩张，<50收缩" signal={fd.m1_m2_spread?.signal} />
        <MetricCard title="M1-M2剪刀差" value={china_core.cn_m1_m2_spread?.spread?.toFixed(1)} unit="%" note="收窄=企业敢花钱" signal={fd.m1_m2_spread?.signal} />
        <MetricCard title="CPI同比" value={china_core.cn_cpi_yy?.value} unit="%" note="<1%通缩，>3%通胀" />
        <MetricCard title="PPI同比" value={china_core.cn_ppi_yy?.value} unit="%" note="负值=工业承压" />
      </div>
      <div className="grid-4">
        <MetricCard title="LPR (1年)" value={china_core.cn_lpr_1y?.value} unit="%" note="企业贷款基准利率" />
        <MetricCard title="社融增量" value={china_core.cn_social_financing?.value ? (china_core.cn_social_financing.value / 1e8).toFixed(0) : '--'} unit="亿" note="实体拿到多少钱" />
        <MetricCard title="北向资金" value={china_core.north_money_3d?.value?.toFixed(0)} unit="亿" note="持续流入=外资看好" signal={fd.north_money?.signal} />
        <MetricCard title="财新制造业PMI" value={china_core.cn_pmi_caixin?.value} note="中小企业+出口，与官方背离需警惕" />
      </div>
      <div className="grid-4">
        <MetricCard title="10Y中债收益率" value={cn10yYield ? (cn10yYield * 100).toFixed(2) : '--'} unit="%" note="人民币资产定价锚" />
      </div>

      {/* ========== 三、全球宏观 ========== */}
      <div className="section-title">
        🌐 三、全球宏观
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: 8 }}>
          — 「外部世界」的天气预报
        </span>
      </div>
      <div className="grid-4">
        <MetricCard title="美国ISM PMI" value={global_macro.us_ism_pmi?.value} note=">50=扩张，<50=收缩" />
        <MetricCard title="核心PCE" value={global_macro.us_core_pce_yy?.value} unit="%" note="美联储降息开关" />
        <MetricCard title="美国CPI同比" value={global_macro.us_cpi_yy?.value} unit="%" note="公众通胀数据，超预期→股跌债涨" />
        <MetricCard title="联邦基金利率" value={global_macro.fed_funds_rate?.value} unit="%" note="美国基准利率，高位=流动性收紧" />
      </div>
      <div className="grid-4">
        <MetricCard
          title="美联储资产负债表"
          value={global_macro.fed_balance_sheet?.value ? (global_macro.fed_balance_sheet.value / 1e12).toFixed(1) : '--'}
          unit="万亿"
          note="扩表=放水，缩表=抽水"
        />
        <MetricCard
          title="隔夜逆回购"
          value={global_macro.on_rrp_balance?.value ? (global_macro.on_rrp_balance.value / 1e12).toFixed(1) : '--'}
          unit="万亿"
          note="市场闲钱多少，接近0=紧张"
        />
      </div>

      {/* ========== 四、美元与流动性 ========== */}
      <div className="section-title">
        💵 四、美元与流动性
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: 8 }}>
          — 汇率与「水位」
        </span>
      </div>
      <div className="grid-4">
        <MetricCard title="DXY美元指数" value={fx_liquidity.dxy_idx?.value?.toFixed(2)} note=">105=强势美元" />
        <MetricCard title="中美利差" value={cnUsSpread} unit="bp" note="收窄=外资回流，走阔=外逃" signal={fd.cn_us_spread?.signal} />
        <MetricCard title="USD/CNH" value={fx_liquidity.usd_cnh?.value?.toFixed(4)} note=">7.30=贬值压力" />
        <MetricCard title="USD/JPY" value={fx_liquidity.usd_jpy?.value?.toFixed(2)} note="套息交易温度" />
      </div>

      {/* ========== 五、全球核心资产 ========== */}
      <div className="section-title">
        📈 五、全球核心资产
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: 8 }}>
          — 各类资产的「价格」
        </span>
      </div>
      <div className="grid-4">
        <MetricCard title="标普500" value={assets.spx?.value?.toLocaleString()} note="美股大盘" />
        <MetricCard title="沪深300" value={assets.hs300?.value?.toLocaleString()} note="A股大盘基准" />
        <MetricCard title="恒生指数" value={assets.hsi?.value?.toLocaleString()} note="港股晴雨表" />
        <MetricCard title="日经225" value={assets.nk225?.value?.toLocaleString()} note="对全球流动性高度敏感" />
      </div>
      <div className="grid-4">
        <MetricCard title="黄金" value={assets.gold_spot?.value?.toLocaleString()} unit="$" note="避险资产" />
        <MetricCard title="比特币" value={assets.btc_usd?.value?.toLocaleString()} unit="$" note="Risk On流动性末梢" />
        <MetricCard title="WTI原油" value={assets.wti_oil?.value?.toFixed(2)} unit="$" note=">90=通胀压力大" />
        <MetricCard title="10Y美债收益率" value={assets.us_10y_yield?.value} unit="%" note="全球资产定价之锚" />
      </div>
      <div className="grid-4">
        <MetricCard title="2Y美债收益率" value={global_macro.us_2y_yield?.value} unit="%" note="短期利率预期" />
        <MetricCard title="10Y中债收益率" value={cn10yYield ? (cn10yYield * 100).toFixed(2) : '--'} unit="%" note="人民币资产定价锚" />
      </div>

      {/* ========== 六、波动率与风险 ========== */}
      <div className="section-title">
        ⚠️ 六、波动率与风险
        <span style={{ fontSize: 12, color: 'var(--text-muted)', fontWeight: 'normal', marginLeft: 8 }}>
          — 市场的「警报器」
        </span>
      </div>
      <div className="grid-4">
        <MetricCard title="VIX恐慌指数" value={risk_monitor.vix?.value?.toFixed(2)} note="全球心跳，>25恐慌" signal={fd.vix?.signal} />
        <MetricCard title="MOVE指数" value={risk_monitor.move_idx?.value?.toFixed(2)} note="债市恐慌温度" />
        <MetricCard title="高收益债利差" value={risk_monitor.hy_spread_oas?.value?.toFixed(0)} unit="bp" note=">600bp=危机预警" signal={fd.credit_spread?.signal} />
        <MetricCard title="A股VIX" value={risk_monitor.cn_vix?.value?.toFixed(2)} note="A股恐慌，>35可能见底" />
      </div>
      <div className="grid-4">
        <MetricCard title="TED利差" value={risk_monitor.ted_spread?.value?.toFixed(2)} unit="bp" note="银行间借贷风险" />
      </div>

      {/* 底部 */}
      <div className="footer">
        <span>📊 数据来源：FRED · AKShare · yfinance</span>
        <span>更新：{meta.updated_at ? new Date(meta.updated_at).toLocaleString('zh-CN') : '--'}</span>
      </div>
    </div>
  );
}
