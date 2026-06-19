export default function IndicatorCard({ label, value, unit = '', trend = null }) {
  const trendColor = trend === 'up' ? 'positive' : trend === 'down' ? 'negative' : '';

  return (
    <div className="indicator-item">
      <div className="indicator-label">{label}</div>
      <div className={`indicator-value ${trendColor}`}>
        {value ?? '--'}
        {unit && <span className="card-unit">{unit}</span>}
      </div>
    </div>
  );
}
