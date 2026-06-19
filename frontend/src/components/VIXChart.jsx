import ReactECharts from 'echarts-for-react';

export default function VIXChart({ value }) {
  const option = {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a2235',
      borderColor: '#2d3748',
      textStyle: { color: '#e8e8e8' },
    },
    grid: { left: 40, right: 10, top: 10, bottom: 25 },
    xAxis: {
      type: 'category',
      data: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
      axisLine: { lineStyle: { color: '#2d3748' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      min: 10,
      max: 30,
      axisLine: { show: false },
      splitLine: { lineStyle: { color: '#2d3748', type: 'dashed' } },
      axisLabel: { color: '#6b7280', fontSize: 10 },
    },
    series: [{
      data: [18.5, 17.2, 19.1, 17.8, 16.9, value || 17.44, value || 17.44],
      type: 'line',
      smooth: true,
      lineStyle: { color: '#f0b90b', width: 2 },
      areaStyle: {
        color: {
          type: 'linear',
          x: 0, y: 0, x2: 0, y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(240, 185, 11, 0.3)' },
            { offset: 1, color: 'rgba(240, 185, 11, 0.0)' },
          ],
        },
      },
      symbol: 'circle',
      symbolSize: 4,
    }],
  };

  return <ReactECharts option={option} style={{ height: 160 }} />;
}
