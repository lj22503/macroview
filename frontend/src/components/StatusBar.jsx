import '../styles/dashboard.css';

export default function StatusBar({ data }) {
  const vix = data?.fred?.vix?.value;
  const cnUsSpread = (data?.china?.m1m2?.spread || 0);

  // 简化 RISK ON/OFF 计算
  let riskStatus = 'NEUTRAL';
  let confidence = 50;
  let drivers = '数据加载中';

  if (data?.updated_at) {
    const vixScore = vix && vix < 20 ? 30 : vix && vix > 30 ? -20 : 0;
    const spreadScore = cnUsSpread > -5 ? 20 : cnUsSpread < -8 ? -15 : 0;
    const total = 50 + vixScore + spreadScore;
    confidence = Math.min(95, Math.max(30, total));
    riskStatus = total >= 65 ? 'RISK ON' : total <= 45 ? 'RISK OFF' : 'NEUTRAL';
    drivers = 'VIX + M1-M2剪刀差';
  }

  const badgeClass = riskStatus === 'RISK ON' ? 'risk-on'
    : riskStatus === 'RISK OFF' ? 'risk-off' : 'neutral';

  return (
    <div className="status-bar">
      <div className={`status-badge ${badgeClass}`}>{riskStatus}</div>
      <div className="confidence">置信度: {confidence}%</div>
      <div className="drivers">主要驱动: {drivers}</div>
      <div className="card-meta" style={{ marginLeft: 'auto' }}>
        更新: {data?.updated_at ? new Date(data.updated_at).toLocaleString('zh-CN') : '--'}
      </div>
    </div>
  );
}