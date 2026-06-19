import { fetchOverview } from '../api/macroApi';
import { useEffect, useState } from 'react';

export default function StatusBar() {
  const [data, setData] = useState(null);

  useEffect(() => {
    fetchOverview()
      .then(res => setData(res.data))
      .catch(err => console.error('Failed to fetch overview:', err));
  }, []);

  if (!data) {
    return (
      <div className="status-bar">
        <div className="status-badge neutral">加载中...</div>
      </div>
    );
  }

  const badgeClass = data.risk_status === 'RISK ON' ? 'risk-on'
    : data.risk_status === 'RISK OFF' ? 'risk-off' : 'neutral';

  return (
    <div className="status-bar">
      <div className={`status-badge ${badgeClass}`}>
        {data.risk_status}
      </div>
      <div className="confidence">
        置信度: {data.confidence}%
      </div>
      <div className="drivers">
        主要驱动: {data.primary_drivers}
      </div>
      <div className="card-meta" style={{ marginLeft: 'auto' }}>
        更新: {new Date(data.updated_at).toLocaleString('zh-CN')}
      </div>
    </div>
  );
}
