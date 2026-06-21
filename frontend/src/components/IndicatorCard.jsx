export default function IndicatorCard({ label, value, unit = '', trend = null, view = null, narrative = null }) {
  const trendColor = trend === 'up' ? 'positive' : trend === 'down' ? 'negative' : '';
  const signalColor = view ? (view.includes('看多') || view.includes('流入') || view.includes('资本回流') ? 'positive' : view.includes('看空') || view.includes('流出') || view.includes('外逃') ? 'negative' : 'neutral') : '';

  return (
    <div className="indicator-item">
      <div className="indicator-label">{label}</div>
      <div className={`indicator-value ${trendColor || signalColor}`}>
        {value ?? '--'}
        {unit && <span className="card-unit">{unit}</span>}
      </div>
      {view && (
        <div className={`indicator-view ${signalColor}`}>{view}</div>
      )}
      {narrative && (
        <div className="indicator-narrative">{narrative}</div>
      )}
    </div>
  );
}
