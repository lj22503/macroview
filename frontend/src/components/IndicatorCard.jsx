import { useState } from 'react';

export default function IndicatorCard({
  label,
  value,
  unit = '',
  color = '',
  change = null,
  note = null,
  signal = null,
  signalText = '',
  explanation = null,
}) {
  const [showTip, setShowTip] = useState(false);
  const numberColor = color ? `value-${color}` : '';
  const changeClass = change != null ? (change >= 0 ? 'up' : 'down') : '';

  return (
    <div className="card">
      <div className="title-row">
        <div className="title">{label}</div>
        {explanation && (
          <button
            className="info-btn"
            onClick={() => setShowTip(v => !v)}
            aria-label={`查看${label}的解释`}
          >
            ❓
            {showTip && (
              <div className="tooltip" style={{ top: '100%', left: 0 }}>
                {explanation}
              </div>
            )}
          </button>
        )}
      </div>
      <div>
        <span className={`number ${numberColor}`}>
          {value != null ? value : '--'}
        </span>
        {unit && <span className="change">{unit}</span>}
        {change != null && (
          <span className={`change ${changeClass}`}>
            {change >= 0 ? '+' : ''}{change}%
          </span>
        )}
      </div>
      {note && <div className="note">{note}</div>}
      {signal && (
        <div className={`signal signal-${signal}`}>{signalText}</div>
      )}
    </div>
  );
}
