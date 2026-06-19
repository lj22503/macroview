import { useEffect, useState } from 'react';
import { fetchOverview, fetchChina, fetchGlobal, fetchAssets } from '../api/macroApi';
import StatusBar from './StatusBar';
import VIXChart from './VIXChart';
import IndicatorCard from './IndicatorCard';
import '../styles/dashboard.css';

export default function Dashboard() {
  const [overview, setOverview] = useState(null);
  const [china, setChina] = useState(null);
  const [globalData, setGlobalData] = useState(null);
  const [assets, setAssets] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchOverview().catch(() => ({ data: {} })),
      fetchChina().catch(() => ({})),
      fetchGlobal().catch(() => ({ data: {} })),
      fetchAssets().catch(() => ({ data: {} })),
    ]).then(([ov, cn, gl, as]) => {
      setOverview(ov.data);
      setChina(cn.data || cn);
      setGlobalData(gl.data);
      setAssets(as.data);
      setLoading(false);
    });
  }, []);

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', color: '#9ca3af' }}>
        加载中...
      </div>
    );
  }

  const indicators = overview?.indicators || {};
  const global = globalData || {};
  const assetData = assets || {};

  return (
    <div>
      <StatusBar />

      <div className="main-content">
        <div className="card">
          <div className="card-header">
            <span className="card-title">VIX 恐慌指数</span>
          </div>
          <div className={`card-value ${(indicators.VIXCLS || 17) < 20 ? 'positive' : 'negative'}`}>
            {indicators.VIXCLS || '--'}
          </div>
          <VIXChart value={indicators.VIXCLS} />
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">10Y 美债收益率</span>
          </div>
          <div className="card-value neutral">
            {global.dgs10?.value ? `${global.dgs10.value}%` : '--'}
          </div>
          <div className="card-meta">美国国债收益率曲线锚点</div>
        </div>

        <div className="card">
          <div className="card-header">
            <span className="card-title">核心 PCE</span>
          </div>
          <div className="card-value positive">
            {global.pce?.value ? `${global.pce.value}%` : '--'}
          </div>
          <div className="card-meta">美联储最关注的通胀指标</div>
        </div>

        <div className="module-title">中国内核</div>

        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="中国 PMI" value={china?.pmi?.value} trend="up" />
          <IndicatorCard label="CPI" value={china?.cpi?.value} unit="%" />
          <IndicatorCard label="PPI" value={china?.ppi?.value} unit="%" />
          <IndicatorCard label="M1-M2 剪刀差" value={china?.m1m2?.value} unit="%" />
          <IndicatorCard label="社融增量" value={china?.social?.value} unit="万亿" />
          <IndicatorCard label="LPR (1Y)" value={china?.lpr?.value} unit="%" />
        </div>

        <div className="module-title">全球宏观</div>

        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="ISM 制造业 PMI" value={global.ism?.value} />
          <IndicatorCard label="DXY 美元指数" value={global.dxy?.value} />
          <IndicatorCard label="美联储资产负债表" value={global.walcl?.value} unit="万亿" />
          <IndicatorCard label="高收益债利差" value={global.baml?.value} unit="bp" />
        </div>

        <div className="module-title">美元与流动性</div>

        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="USD/CNH" value={assetData.usd_cnh?.price} />
          <IndicatorCard label="2Y 美债" value={global.dgs2?.value} unit="%" />
        </div>

        <div className="module-title">全球核心资产</div>

        <div className="indicator-grid" style={{ gridColumn: '1 / -1' }}>
          <IndicatorCard label="标普 500" value={assetData.sp500?.price} />
          <IndicatorCard label="沪深 300" value={assetData.hs300?.price} />
          <IndicatorCard label="黄金" value={assetData.gold?.price} unit="USD" />
          <IndicatorCard label="原油" value={assetData.crude?.price} unit="USD" />
        </div>
      </div>
    </div>
  );
}
