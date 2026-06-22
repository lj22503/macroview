import { useEffect, useState, useCallback } from 'react';
import { fetchAllData } from '../api/macroApi';
import VIXChart from './VIXChart';
import IndicatorCard from './IndicatorCard';
import '../styles/dashboard.css';

// 指标解释数据（小白版 tooltip）
const FIELD_EXPLANATIONS = {
  '制造业 PMI': '经济体温计。>50=经济在扩张（发热），<50=在收缩（发冷）。每月第一个公布，最领先指标。',
  'CPI 同比': '物价涨速。<1%=通缩（东西太便宜），>3%=通胀（东西太贵），1-2%最舒服。',
  'PPI 同比': '工厂产品卖得好不好。负值=打折也卖不动（利润承压），正值=能涨价（利润改善）。',
  'M1-M2 剪刀差': '企业花钱意愿指数。收窄=企业敢花钱，经济变好；走阔=企业躺平，经济萎靡。',
  '社融增量': '实体经济拿到多少资金。回升=信用扩张（利好），回落=借不到钱（利空）。',
  'LPR 1年期': '企业贷款基准利率。下调=宽松（利好），上调=收紧（利空）。',
  '北向资金': '外资买卖A股的金额。持续流入=外资看好，持续流出=外资撤退。',
  '风险偏好': '就像开车时的红绿灯。RISK_ON=绿灯（可加速进攻），RISK_OFF=红灯（踩刹车防守），NEUTRAL=黄灯（减速观察）。',
  'ISM 制造业 PMI': '全球经济风向标。>50=美国经济好（利好全球），<50=美国经济差（拖累全球）。',
  'DXY 美元指数': '美元强弱。>105=强势美元（压制A股），<100=弱势美元（利好A股）。',
  '高收益债利差': '企业借钱难易度。>500bp=危险（可能爆发危机），<350bp=安全。',
  '中美利差 10Y-2Y': '外资流向总开关。收窄=资本回流中国（利好），走阔=资本外逃（利空）。',
  'MOVE 指数': '债市恐慌温度。急升=债券市场剧烈波动，预示更大风险。',
  'A股隐含波动率': 'A股恐慌指数。>30=A股恐慌性抛售（可能见底），<15=过于平静（警惕变盘）。',
  '标普 500': '美股大盘。涨=全球风险偏好高，跌=全球避险。',
  '沪深 300': 'A股大盘。中国最大300家公司，A股成绩单。',
  '黄金': '避险资产。地缘风险+实际利率下行时上涨。',
  'WTI 原油': '通胀油门。>90$=通胀压力大（利空），<70$=通胀压力小（利好）。',
  'USD/CNH': '人民币汇率。>7.30=贬值压力（利空A股），<7.10=升值（利好）。',
};

function fmtTime(ts) {
  if (!ts) return '--';
  try { return new Date(ts).toLocaleString('zh-CN'); }
  catch { return ts; }
}

function computeDrivers(fred, china) {
  const tags = [];
  const vix = fred?.vix?.value;
  const spread = china?.m1m2?.spread;
  if (vix != null) {
    tags.push(vix < 18 ? '极低波动' : vix < 25 ? '正常波动' : '高波动预警');
  }
  if (spread != null) {
    tags.push(spread > -3 ? '流动性宽松' : spread < -8 ? '流动性偏紧' : '流动性中性');
  }
  if (fred?.dgs10?.value != null) {
    tags.push(`10Y ${fred.dgs10.value}%`);
  }
  if (!tags.length) tags.push('数据加载中');
  return tags;
}

function computeBias(fred, china) {
  const vix = fred?.vix?.value ?? 20;
  const spread = china?.m1m2?.spread ?? -5;
  let score = 50;
  if (vix < 18) score += 12;
  else if (vix > 28) score -= 15;
  else if (vix > 22) score -= 5;
  if (spread > -3) score += 15;
  else if (spread < -8) score -= 10;
  score = Math.min(95, Math.max(5, score));
  const bias = score >= 62 ? 'RISK ON' : score <= 42 ? 'RISK OFF' : 'NEUTRAL';
  return { bias, confidence: score };
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchAll = useCallback(() => {
    setLoading(true);
    setError(false);
    fetchAllData()
      .then(d => {
        const keys = ['overview', 'china', 'fred', 'assets'];
        const hasAny = keys.some(k => d?.[k] && Object.keys(d[k]).length > 0);
        if (!hasAny) { setError(true); return; }
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
        <p>数据加载失败，请检查后端服务或网络连接</p>
        <button className="retry-btn" onClick={fetchAll}>重新加载</button>
      </div>
    );
  }

  const { china = {}, fred = {}, assets = {}, overview = {}, updated_at } = data;
  const vixVal = fred.vix?.value;
  const { bias, confidence } = computeBias(fred, china);
  const drivers = computeDrivers(fred, china);
  const biasClass = bias === 'RISK ON' ? 'risk-on' : bias === 'RISK OFF' ? 'risk-off' : 'neutral';
  const vixClass = vixVal != null ? (vixVal < 20 ? 'risk-on' : 'risk-off') : '';
  const cnUsSpread = (fred.dgs10?.value != null && fred.dgs2?.value != null)
    ? (fred.dgs10.value - fred.dgs2.value) : null;
  const riskScore = overview?.confidence ?? china?.confidence ?? china?.sentiment?.value;

  return (
    <div className="dashboard">
      {/* ---- 标题栏 ---- */}
      <div className="header">
        <h1>MacroView 宏观仪表盘</h1>
        <div className="update-time">
          数据更新 <span>{fmtTime(updated_at)}</span>
        </div>
      </div>

      {/* ---- 顶层：风险状态 + 驱动 + VIX ---- */}
      <div className="top-level">
        <div className="risk-card">
          <div className="label">宏观风险状态</div>
          <div className={`value ${biasClass}`}>{bias}</div>
          <div className="sub">综合置信度 {confidence}%</div>
        </div>

        <div className="driver-card">
          <div className="label">信号驱动</div>
          <div className="tags">
            {drivers.map((d, i) => (
              <span className="tag" key={i}>{d}</span>
            ))}
          </div>
        </div>

        <div className="risk-card">
          <div className="label">恐慌指数 VIX</div>
          <div className={`value ${vixClass}`}>
            {vixVal != null ? vixVal.toFixed(2) : '--'}
          </div>
          <VIXChart value={vixVal} compact />
        </div>
      </div>

      {/* ---- 模块一：中国内核 ---- */}
      <div className="section-title">中国内核</div>
      <div className="grid-4">
        <IndicatorCard label="制造业 PMI" value={china.pmi?.value}
          color={china.pmi?.value >= 50 ? 'green' : 'red'}
          explanation={FIELD_EXPLANATIONS['制造业 PMI']} />
        <IndicatorCard label="CPI 同比" value={china.cpi?.value} unit="%" color="yellow"
          explanation={FIELD_EXPLANATIONS['CPI 同比']} />
        <IndicatorCard label="PPI 同比" value={china.ppi?.value} unit="%" color="yellow"
          explanation={FIELD_EXPLANATIONS['PPI 同比']} />
        <IndicatorCard label="M1-M2 剪刀差" value={china.m1m2?.spread} unit="%"
          color={china.m1m2?.spread > 0 ? 'green' : 'red'}
          explanation={FIELD_EXPLANATIONS['M1-M2 剪刀差']} />
        <IndicatorCard label="社融增量" value={china.social?.value} unit="万亿" color="blue"
          explanation={FIELD_EXPLANATIONS['社融增量']} />
        <IndicatorCard label="LPR 1年期" value={china.lpr?.value} unit="%" color="yellow"
          explanation={FIELD_EXPLANATIONS['LPR 1年期']} />
        <IndicatorCard label="北向资金" value={china.north_bound?.value} unit="亿"
          color={china.north_bound?.value > 0 ? 'green' : 'red'}
          signal={china.north_bound?.value > 0 ? 'bull' : 'bear'}
          signalText={china.north_bound?.value > 0 ? '净流入' : '净流出'}
          explanation={FIELD_EXPLANATIONS['北向资金']} />
        <IndicatorCard label="风险偏好" value={riskScore} unit="分"
          color={riskScore >= 70 ? 'green' : riskScore <= 40 ? 'red' : 'yellow'}
          explanation={FIELD_EXPLANATIONS['风险偏好']} />
      </div>

      {/* ---- 模块二：全球宏观 & 波动率风险 ---- */}
      <div className="section-title">全球宏观 · 波动率风险</div>
      <div className="grid-3">
        <IndicatorCard label="ISM 制造业 PMI" value={fred.ism?.value}
          color={fred.ism?.value >= 50 ? 'green' : 'red'}
          explanation={FIELD_EXPLANATIONS['ISM 制造业 PMI']} />
        <IndicatorCard label="DXY 美元指数" value={fred.dxy?.value}
          color={fred.dxy?.value > 105 ? 'blue' : 'yellow'}
          explanation={FIELD_EXPLANATIONS['DXY 美元指数']} />
        <IndicatorCard label="高收益债利差" value={fred.baml?.value} unit="bp"
          color={fred.baml?.value > 500 ? 'red' : fred.baml?.value < 350 ? 'green' : 'yellow'}
          explanation={FIELD_EXPLANATIONS['高收益债利差']} />
        <IndicatorCard label="中美利差 10Y-2Y" value={cnUsSpread} unit="bp"
          color={cnUsSpread > 0 ? 'green' : 'red'}
          explanation={FIELD_EXPLANATIONS['中美利差 10Y-2Y']} />
        <IndicatorCard label="MOVE 指数" value={fred.move?.value}
          color={fred.move?.value > 120 ? 'red' : fred.move?.value < 80 ? 'green' : 'yellow'}
          explanation={FIELD_EXPLANATIONS['MOVE 指数']} />
        <IndicatorCard label="A股隐含波动率" value={china.a_share_iv?.value ?? china.vix_fix?.value} unit="%"
          color={china.a_share_iv?.value > 30 ? 'red' : china.a_share_iv?.value < 20 ? 'green' : 'yellow'}
          explanation={FIELD_EXPLANATIONS['A股隐含波动率']} />
      </div>

      {/* ---- 模块三：全球核心资产 ---- */}
      <div className="section-title">全球核心资产</div>
      <div className="grid-3">
        <IndicatorCard label="标普 500" value={assets.sp500?.value}
          color="green"
          change={assets.sp500?.change_pct}
          explanation={FIELD_EXPLANATIONS['标普 500']} />
        <IndicatorCard label="沪深 300" value={assets.hs300?.value}
          color={assets.hs300?.change_pct >= 0 ? 'green' : 'red'}
          change={assets.hs300?.change_pct}
          explanation={FIELD_EXPLANATIONS['沪深 300']} />
        <IndicatorCard label="黄金" value={assets.gold?.value} unit="USD"
          color="yellow" change={assets.gold?.change_pct}
          explanation={FIELD_EXPLANATIONS['黄金']} />
        <IndicatorCard label="WTI 原油" value={assets.crude?.value} unit="USD"
          color="blue" change={assets.crude?.change_pct}
          explanation={FIELD_EXPLANATIONS['WTI 原油']} />
        <IndicatorCard label="USD/CNH" value={assets.usd_cnh?.value}
          color={assets.usd_cnh?.value > 7.2 ? 'red' : 'green'}
          explanation={FIELD_EXPLANATIONS['USD/CNH']} />
      </div>

      {/* ---- 底部 ---- */}
      <div className="footer">
        <span>数据源: FRED · CME · AKShare</span>
        <span>MacroView v0.2</span>
      </div>
    </div>
  );
}
