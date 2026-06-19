import { useEffect, useState } from 'react';
import { fetchAllData } from '../api/macroApi';
import StatusBar from './StatusBar';
import VIXChart from './VIXChart';
import IndicatorCard from './IndicatorCard';
import '../styles/dashboard.css';

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAllData()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' }}>
        加载中...
      </div>
    );
  }

  if (!data) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#f6465d' }}>
        数据加载失败，请检查网络或稍后重试
      </div>
    );
  }

  const { china = {}, fred = {}, assets = {} } = data;

  return (
    <div>
      <StatusBar data={data} />

      <div className="main-content">
        {/* VIX 卡片 */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">VIX 恐慌指数</span>
          </div>
          <div className={`card-value ${(fred.vix?.value || 20) < 20 ? 'positive' : 'negative'}`}>
            {fred.vix?.value ?? '--'}
          </div>
          <VIXChart value={fred.vix?.value} />
        </div>

        {/* 10Y 美债 */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">10Y 美债收益率</span>
          </div>
          <div className="card-value neutral">
            {fred.dgs10?.value != null ? `${fred.dgs10.value}%` : '--'}
          </div>
          <div className="card-meta">美国国债收益率曲线锚点</div>
        </div>

        {/* 核心 PCE */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">核心 PCE</span>
          </div>
          <div className="card-value positive">
            {fred.pce?.value != null ? `${fred.pce.value}%` : '--'}
          </div>
          <div className="card-meta">美联储最关注的通胀指标</div>
        </div>

        {/* 模块一：中国内核 */}
        <div className="module-title">中国内核</div>
        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="中国 PMI" value={china.pmi?.value} trend="up" />
          <IndicatorCard label="CPI" value={china.cpi?.value} unit="%" />
          <IndicatorCard label="PPI" value={china.ppi?.value} unit="%" />
          <IndicatorCard label="M1-M2 剪刀差" value={china.m1m2?.spread} unit="%" />
          <IndicatorCard label="社融增量" value={china.social?.value} unit="万亿" />
          <IndicatorCard label="LPR (1Y)" value={china.lpr?.value} unit="%" />
        </div>

        {/* 模块二：全球宏观 */}
        <div className="module-title">全球宏观</div>
        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="ISM 制造业 PMI" value={fred.ism?.value} />
          <IndicatorCard label="DXY 美元指数" value={fred.dxy?.value} />
          <IndicatorCard label="高收益债利差" value={fred.baml?.value} unit="bp" />
        </div>

        {/* 模块三：全球核心资产 */}
        <div className="module-title">全球核心资产</div>
        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="标普 500" value={assets.sp500?.value} />
          <IndicatorCard label="沪深 300" value={assets.hs300?.value} />
          <IndicatorCard label="黄金" value={assets.gold?.value} unit="USD" />
          <IndicatorCard label="原油" value={assets.crude?.value} unit="USD" />
          <IndicatorCard label="USD/CNH" value={assets.usd_cnh?.value} />
        </div>

        <div style={{ gridColumn: '1 / -1', textAlign: 'center', color: '#6b7280', fontSize: 12, marginTop: 8 }}>
          数据更新时间：{data.updated_at || '--'}
        </div>
      </div>
    </div>
  );
}