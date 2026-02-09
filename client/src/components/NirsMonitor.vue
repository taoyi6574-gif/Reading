<template>
  <div class="monitor-panel">
    <h3>🧠 NIRS 脑血氧实时监测</h3>
    <div ref="chartRef" class="chart-container"></div>
    
    <div class="status-bar">
      状态: <span :class="statusClass">{{ statusText }}</span>
      <span class="latency" v-if="lastLatency"> (延迟: {{ lastLatency }}ms)</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';

// 定义接收的数据格式
interface NirsPacket {
  timestamp: number;
  raw_data: { hbo: number; hbr: number };
  analysis: { focus_level: string };
}

const props = defineProps<{
  latestData: NirsPacket | null;
  isConnected: boolean;
}>();

const chartRef = ref<HTMLElement | null>(null);
let myChart: echarts.ECharts | null = null;

// 数据队列（用于滚动显示波形）
const maxPoints = 100;
const dataHbO: number[] = [];
const dataHbR: number[] = [];
const xAxisData: string[] = [];

// 状态显示
const statusText = ref('未连接');
const statusClass = ref('disconnected');
const lastLatency = ref(0);

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return;
  
  myChart = echarts.init(chartRef.value);
  const option = {
    tooltip: { trigger: 'axis' },
    legend: { data: ['氧合血红蛋白 (HbO)', '脱氧血红蛋白 (HbR)'], bottom: 0 },
    grid: { left: '3%', right: '4%', bottom: '10%', top: '15%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: xAxisData, show: false },
    yAxis: { type: 'value', min: -1.0, max: 1.0, name: '浓度变化 (μmol/L)' },
    series: [
      { name: '氧合血红蛋白 (HbO)', type: 'line', smooth: true, showSymbol: false, data: dataHbO, color: '#ff4d4f', lineStyle: { width: 2 } },
      { name: '脱氧血红蛋白 (HbR)', type: 'line', smooth: true, showSymbol: false, data: dataHbR, color: '#1890ff', lineStyle: { width: 2 } }
    ]
  };
  myChart.setOption(option);
};

// 监听数据更新
watch(() => props.latestData, (newVal) => {
  if (!newVal) return;
  
  // 计算延迟 (当前时间 - 数据包时间)
  const now = Date.now() / 1000;
  lastLatency.value = Math.floor((now - newVal.timestamp) * 1000);

  // 更新队列
  if (dataHbO.length > maxPoints) {
    dataHbO.shift();
    dataHbR.shift();
    xAxisData.shift();
  }
  
  dataHbO.push(newVal.raw_data.hbo);
  dataHbR.push(newVal.raw_data.hbr);
  xAxisData.push(new Date().toLocaleTimeString());

  // 刷新图表
  myChart?.setOption({
    xAxis: { data: xAxisData },
    series: [{ data: dataHbO }, { data: dataHbR }]
  });
});

// 监听连接状态
watch(() => props.isConnected, (val) => {
  statusText.value = val ? '实时监测中' : '连接断开';
  statusClass.value = val ? 'connected' : 'disconnected';
});

onMounted(() => {
  initChart();
  window.addEventListener('resize', () => myChart?.resize());
});
</script>

<style scoped>
.monitor-panel {
  background: white;
  padding: 15px;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
  border: 1px solid #eee;
}
.chart-container {
  width: 100%;
  height: 250px;
}
.status-bar {
  margin-top: 10px;
  font-size: 14px;
  text-align: right;
  color: #666;
}
.connected { color: #52c41a; font-weight: bold; }
.disconnected { color: #ff4d4f; font-weight: bold; }
</style>