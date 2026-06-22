import { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { fetchVixHistory } from '../api/macroApi';

export default function VIXChart({ value, compact = false }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const height = compact ? 130 : 160;

  useEffect(() => {
    fetchVixHistory(30)
      .then(res => setHistory(res.data?.data || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading || !history.length) {
    return (
      <div style={{
        height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        color: 'var(--text-dim)',
        fontSize: 12,
      }}>
        {loading ? '加载图表…' : '暂无历史数据'}
      </div>
    );
  }

  const chartData = [...history];
  if (value != null && chartData.length > 0) {
    const last = chartData[chartData.length - 1];
    if (last.value !== value) {
      chartData.push({ date: '最新', value });
    }
  }

  const dates = chartData.map(d => d.date.length > 5 ? d.date.slice(5) : d.date);
  const values = chartData.map(d => d.value);
  const baseline = 20;

  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a2235',
      borderColor: '#2d3748',
      textStyle: { color: '#e8e8e8', fontSize: 12 },
      formatter: params => {
        const p = params[0];
        const v = p.value;
        const color = v < baseline ? '#4cd9a0' : '#f9757a';
        return `<span style="color:#9ca3af">${p.axisValue}</span><br/>
          <span style="font-family:JetBrains Mono,monospace;font-size:14px;color:${color}">VIX ${v.toFixed(2)}</span>`;
      },
    },
    grid: { left: 36, right: compact ? 6 : 10, top: 6, bottom: compact ? 20 : 24 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2d3748' } },
      axisLabel: { color: '#6b7280', fontSize: 9 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: Math.floor(Math.min(...values, baseline) * 0.9),
      max: Math.ceil(Math.max(...values, baseline) * 1.1),
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#2d3748', type: 'dashed' } },
      axisLabel: { color: '#6b7280', fontSize: 9 },
    },
    visualMap: {
      show: false,
      dimension: 1,
      pieces: [
        { lt: baseline, color: '#4cd9a0' },
        { gte: baseline, color: '#f9757a' },
      ],
    },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      lineStyle: { width: 1.5 },
      areaStyle: {
        color: {
          type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(240, 194, 127, 0.2)' },
            { offset: 1, color: 'rgba(240, 194, 127, 0.0)' },
          ],
        },
      },
      symbol: 'none',
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#4b5563', type: 'dashed', width: 1 },
        label: { color: '#6b7280', fontSize: 9, formatter: '恐慌线 20' },
        data: [{ yAxis: baseline }],
      },
    }],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
