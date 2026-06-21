export default function StatusBar({ data }) {
  // 新 API 结构：data = overview
  const bias = data?.bias || 'NEUTRAL';
  const confidence = data?.confidence || 50;
  const primaryDriver = data?.primary_driver || [];
  const label = data?.label || '数据加载中';

  const badgeClass = bias === 'RISK_ON' ? 'risk-on'
    : bias === 'RISK_OFF' ? 'risk-off' : 'neutral';

  const biasText = bias === 'RISK_ON' ? 'RISK ON'
    : bias === 'RISK_OFF' ? 'RISK OFF' : 'NEUTRAL';

  return (
    <div className="status-bar">
      <div className={`status-badge ${badgeClass}`}>{biasText}</div>
      <div className="confidence">置信度: {confidence}%</div>
      <div className="drivers">状态: {label}</div>
      {primaryDriver.length > 0 && (
        <div className="drivers">驱动: {primaryDriver.join(' + ')}</div>
      )}
      <div className="card-meta" style={{ marginLeft: 'auto' }}>
        更新: {data?.updated_at ? new Date(data.updated_at).toLocaleString('zh-CN') : '--'}
      </div>
    </div>
  );
}
