import { useEffect, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { fetchVixHistory } from '../api/macroApi';

export default function VIXChart({ value }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVixHistory(30)
      .then(res => setHistory(res.data?.data || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="chart-placeholder">加载图表…</div>;
  }

  if (!history.length) {
    return <div className="chart-placeholder">暂无历史数据</div>;
  }

  // 补充当前值（API 可能有延迟）
  const chartData = [...history];
  if (value && chartData.length > 0) {
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
        const color = v < baseline ? '#00d26a' : '#f6465d';
        return `<span style="color:#9ca3af">${p.axisValue}</span><br/>
          <span style="font-family:JetBrains Mono,monospace;font-size:14px;color:${color}">VIX ${v.toFixed(2)}</span>`;
      },
    },
    grid: { left: 42, right: 12, top: 8, bottom: 28 },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#2d3748' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      min: Math.floor(Math.min(...values, baseline) * 0.9),
      max: Math.ceil(Math.max(...values, baseline) * 1.1),
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#2d3748', type: 'dashed' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
    },
    series: [{
      data: values,
      type: 'line',
      smooth: true,
      lineStyle: { width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(240, 185, 11, 0.25)' },
            { offset: 1, color: 'rgba(240, 185, 11, 0.0)' },
          ],
        },
      },
      symbol: 'circle',
      symbolSize: 5,
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#4b5563', type: 'dashed', width: 1 },
        label: { color: '#6b7280', fontSize: 10, formatter: '恐慌线 20' },
        data: [{ yAxis: baseline }],
      },
    }],
  };

  return <ReactECharts option={option} style={{ height: 160 }} />;
}
