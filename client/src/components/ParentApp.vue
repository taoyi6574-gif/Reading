<template>
  <div class="parent-page">
    <header class="header">
      <h2 class="title">家长端</h2>
      <p class="subtitle">查看孩子阅读数据与成长报告</p>
    </header>

    <!-- 未绑定：仅显示关联入口 -->
    <template v-if="!loadingBound && boundChildren.length === 0">
      <div class="empty-bind">
        <p>尚未关联任何儿童账号</p>
        <p class="hint-small">输入孩子的账号和密码完成绑定，即可查看其阅读数据</p>
        <button type="button" class="btn primary" @click="showBindModal = true">关联儿童账号</button>
      </div>
    </template>
    <template v-else-if="loadingBound">
      <div class="empty-bind">
        <p>加载中...</p>
      </div>
    </template>

    <!-- 已绑定：首页数据概览 -->
    <template v-else>
      <!-- 儿童切换：左右滑动 / 指示点 -->
      <div class="child-switcher">
        <button type="button" class="arrow" :disabled="currentChildIndex <= 0" @click="prevChild">‹</button>
        <div class="child-name">{{ currentChild?.name || currentChild?.account || '孩子' }}</div>
        <button type="button" class="arrow" :disabled="currentChildIndex >= boundChildren.length - 1" @click="nextChild">›</button>
        <button type="button" class="btn-unbind" @click="doUnbind" title="解绑该儿童">解绑</button>
      </div>
      <div class="child-dots">
        <span
          v-for="(c, i) in boundChildren"
          :key="c.id"
          class="dot"
          :class="{ active: i === currentChildIndex }"
          @click="currentChildIndex = i"
        />
      </div>

      <!-- 阅读数据概览区（支持左右滑动切换儿童） -->
      <section class="overview" @touchstart="onTouchStart" @touchend="onTouchEnd">
        <div class="overview-cards">
          <div class="card">
            <span class="card-label">最近阅读时长</span>
            <span class="card-value">{{ overview.recentMinutes }} 分钟</span>
          </div>
          <div class="card">
            <span class="card-label">平均专注度</span>
            <span class="card-value">{{ overview.avgFocus }}%</span>
          </div>
          <div class="card">
            <span class="card-label">理解难度匹配度</span>
            <span class="card-value">{{ overview.matchRate }}%</span>
          </div>
        </div>

        <!-- 图表区（可点击查看详情） -->
        <div class="charts-row">
          <div class="chart-wrap" @click="chartDetail = 'focus'">
            <div ref="focusChartRef" class="chart"></div>
            <p class="chart-title">专注度变化曲线</p>
          </div>
          <div class="chart-wrap" @click="chartDetail = 'hbo'">
            <div ref="hboChartRef" class="chart"></div>
            <p class="chart-title">血氧浓度变化曲线</p>
          </div>
          <div class="chart-wrap" @click="chartDetail = 'duration'">
            <div ref="durationChartRef" class="chart"></div>
            <p class="chart-title">阅读时长统计</p>
          </div>
        </div>
      </section>

      <!-- 底部功能入口 -->
      <nav class="bottom-nav" v-if="view === 'home'">
        <button type="button" class="nav-item" @click="view = 'report'">
          <span class="icon">📊</span>
          <span>阅读报告</span>
        </button>
        <button type="button" class="nav-item" @click="view = 'log'">
          <span class="icon">📝</span>
          <span>调整日志</span>
        </button>
        <button type="button" class="nav-item" @click="view = 'recommend'">
          <span class="icon">📚</span>
          <span>内容推荐</span>
        </button>
      </nav>
    </template>

    <!-- 子页面：阅读报告 -->
    <section v-if="view === 'report'" class="sub-page">
      <div class="sub-header">
        <button type="button" class="back" @click="view = 'home'">← 返回</button>
        <h3>阅读报告</h3>
      </div>
      <div class="sub-body">
        <p>本周/本月阅读汇总、完成书籍、阅读偏好分析等。支持导出便于留存。</p>
        <div class="export-actions">
          <button type="button" class="btn primary" @click="exportExcel">导出 Excel</button>
          <button type="button" class="btn secondary" @click="exportPDF">导出 PDF</button>
        </div>
        <div id="report-print-area" class="report-preview">
          <h4>阅读报告预览</h4>
          <p>儿童：{{ currentChild?.name || currentChild?.account }}</p>
          <p>最近阅读时长：{{ overview.recentMinutes }} 分钟</p>
          <p>平均专注度：{{ overview.avgFocus }}%</p>
          <p>理解难度匹配度：{{ overview.matchRate }}%</p>
          <p>报告生成时间：{{ reportTime }}</p>
        </div>
      </div>
    </section>

    <!-- 子页面：调整日志 -->
    <section v-if="view === 'log'" class="sub-page">
      <div class="sub-header">
        <button type="button" class="back" @click="view = 'home'">← 返回</button>
        <h3>调整日志</h3>
      </div>
      <div class="sub-body">
        <p>系统根据专注度与血氧数据进行的自适应调整记录。</p>
        <ul class="log-list">
          <li v-for="(entry, i) in adjustLogs" :key="i" class="log-item">
            <span class="time">{{ entry.time }}</span>
            <span class="text">{{ entry.text }}</span>
          </li>
        </ul>
      </div>
    </section>

    <!-- 子页面：内容推荐 -->
    <section v-if="view === 'recommend'" class="sub-page">
      <div class="sub-header">
        <button type="button" class="back" @click="view = 'home'">← 返回</button>
        <h3>内容推荐</h3>
      </div>
      <div class="sub-body">
        <p>根据当前专注度与阅读表现推荐的绘本与难度。</p>
        <ul class="recommend-list">
          <li v-for="(item, i) in recommendList" :key="i" class="recommend-item">
            <span class="name">{{ item.name }}</span>
            <span class="reason">{{ item.reason }}</span>
          </li>
        </ul>
      </div>
    </section>

    <!-- 关联弹层 -->
    <div v-if="showBindModal" class="overlay" @click.self="showBindModal = false">
      <div class="modal">
        <h3>关联儿童账号</h3>
        <p class="hint">输入儿童的账号和密码完成绑定，绑定后可查看该儿童的阅读数据。</p>
        <div class="form-item">
          <label>儿童账号</label>
          <input v-model="bindForm.account" type="text" placeholder="请输入儿童账号" />
        </div>
        <div class="form-item">
          <label>儿童密码</label>
          <input v-model="bindForm.password" type="password" placeholder="请输入儿童密码" />
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="showBindModal = false">取消</button>
          <button type="button" class="btn primary" :disabled="bindLoading" @click="doBind">{{ bindLoading ? '校验中...' : '确认关联' }}</button>
        </div>
      </div>
    </div>

    <!-- 图表详情浮层（点击图表后） -->
    <div v-if="chartDetail" class="overlay" @click="chartDetail = null">
      <div class="chart-detail-modal" @click.stop>
        <button type="button" class="close" @click="chartDetail = null">✕</button>
        <h3>{{ chartDetailTitle }}</h3>
        <div class="chart-detail-body">
          <template v-if="chartDetail === 'focus'">
            <p>近 7 日专注度变化，可用于观察孩子阅读时的注意力稳定性。</p>
            <div ref="focusDetailRef" class="detail-chart"></div>
          </template>
          <template v-else-if="chartDetail === 'hbo'">
            <p>脑血氧 HbO 浓度变化，反映认知负荷与投入程度。</p>
            <div ref="hboDetailRef" class="detail-chart"></div>
          </template>
          <template v-else-if="chartDetail === 'duration'">
            <p>每日/每周阅读时长分布。</p>
            <div ref="durationDetailRef" class="detail-chart"></div>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted } from 'vue';
import axios from 'axios';
import * as echarts from 'echarts';
import * as XLSX from 'xlsx';
import printJS from 'print-js';

const props = withDefaults(defineProps<{ parentUsername?: string }>(), { parentUsername: '' });

interface BoundChild {
  id: string;
  name: string;
  account: string;
  subject_id?: number;
}

const API = 'http://localhost:8000/api/v1';

const boundChildren = ref<BoundChild[]>([]);
const currentChildIndex = ref(0);
const currentChild = computed(() => boundChildren.value[currentChildIndex.value] ?? null);
const loadingBound = ref(false);
const bindLoading = ref(false);

const showBindModal = ref(false);
const bindForm = ref({ account: '', password: '' });

const view = ref<'home' | 'report' | 'log' | 'recommend'>('home');
const chartDetail = ref<'' | 'focus' | 'hbo' | 'duration'>('');

// 概览与图表用 mock 数据（按当前儿童索引可扩展为按儿童拉取）
const overview = computed(() => {
  const base = { recentMinutes: 42, avgFocus: 78, matchRate: 85 };
  const i = currentChildIndex.value;
  return {
    recentMinutes: base.recentMinutes + i * 5,
    avgFocus: Math.min(99, base.avgFocus + i * 2),
    matchRate: Math.min(99, base.matchRate + i),
  };
});

const reportTime = computed(() => new Date().toLocaleString('zh-CN'));

const adjustLogs = ref([
  { time: '14:32', text: '检测到专注度下降，已调大字体并提高对比度' },
  { time: '14:28', text: '血氧波动正常，保持当前难度' },
  { time: '14:15', text: '进入新章节，难度匹配度 +5%' },
]);

const recommendList = ref([
  { name: '《小王子》绘本版', reason: '与当前专注度与理解能力匹配' },
  { name: '《恐龙大陆》', reason: '兴趣标签匹配，建议下一本' },
]);

// 图表 ref
const focusChartRef = ref<HTMLElement | null>(null);
const hboChartRef = ref<HTMLElement | null>(null);
const durationChartRef = ref<HTMLElement | null>(null);
const focusDetailRef = ref<HTMLElement | null>(null);
const hboDetailRef = ref<HTMLElement | null>(null);
const durationDetailRef = ref<HTMLElement | null>(null);

let focusChart: echarts.ECharts | null = null;
let hboChart: echarts.ECharts | null = null;
let durationChart: echarts.ECharts | null = null;
let focusDetailChart: echarts.ECharts | null = null;
let hboDetailChart: echarts.ECharts | null = null;
let durationDetailChart: echarts.ECharts | null = null;

const chartDetailTitle = computed(() => {
  if (chartDetail.value === 'focus') return '专注度变化曲线（详细）';
  if (chartDetail.value === 'hbo') return '血氧浓度变化曲线（详细）';
  if (chartDetail.value === 'duration') return '阅读时长统计（详细）';
  return '';
});

function getFocusData() {
  const dates = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  const values = [72, 78, 75, 82, 80, 85, 78];
  return { dates, values };
}

function getHboData() {
  const times = ['10:00', '10:15', '10:30', '10:45', '11:00', '11:15', '11:30'];
  const values = [0.12, 0.18, 0.15, 0.22, 0.19, 0.25, 0.21];
  return { times, values };
}

function getDurationData() {
  const days = ['周一', '周二', '周三', '周四', '周五', '周六', '周日'];
  const values = [15, 25, 20, 35, 30, 42, 28];
  return { days, values };
}

function initFocusChart(el: HTMLElement) {
  if (focusChart) focusChart.dispose();
  focusChart = echarts.init(el);
  const { dates, values } = getFocusData();
  focusChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '12%', right: '4%', bottom: '15%', top: '10%' },
    xAxis: { type: 'category', data: dates },
    yAxis: { type: 'value', name: '专注度(%)', min: 0, max: 100 },
    series: [{ name: '专注度', type: 'line', smooth: true, data: values, color: '#667eea' }],
  });
}

function initHboChart(el: HTMLElement) {
  if (hboChart) hboChart.dispose();
  hboChart = echarts.init(el);
  const { times, values } = getHboData();
  hboChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '12%', right: '4%', bottom: '15%', top: '10%' },
    xAxis: { type: 'category', data: times },
    yAxis: { type: 'value', name: 'HbO (μmol/L)' },
    series: [{ name: '血氧浓度', type: 'line', smooth: true, data: values, color: '#f59e0b' }],
  });
}

function initDurationChart(el: HTMLElement) {
  if (durationChart) durationChart.dispose();
  durationChart = echarts.init(el);
  const { days, values } = getDurationData();
  durationChart.setOption({
    tooltip: { trigger: 'axis' },
    grid: { left: '12%', right: '4%', bottom: '15%', top: '10%' },
    xAxis: { type: 'category', data: days },
    yAxis: { type: 'value', name: '分钟' },
    series: [{ name: '阅读时长', type: 'bar', data: values, color: '#10b981' }],
  });
}

function initDetailCharts() {
  if (chartDetail.value === 'focus' && focusDetailRef.value) {
    focusDetailChart?.dispose();
    focusDetailChart = echarts.init(focusDetailRef.value);
    const { dates, values } = getFocusData();
    focusDetailChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '10%', right: '4%', bottom: '12%', top: '8%' },
      xAxis: { type: 'category', data: dates },
      yAxis: { type: 'value', name: '专注度(%)', min: 0, max: 100 },
      series: [{ name: '专注度', type: 'line', smooth: true, data: values, color: '#667eea' }],
    });
  }
  if (chartDetail.value === 'hbo' && hboDetailRef.value) {
    hboDetailChart?.dispose();
    hboDetailChart = echarts.init(hboDetailRef.value);
    const { times, values } = getHboData();
    hboDetailChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '10%', right: '4%', bottom: '12%', top: '8%' },
      xAxis: { type: 'category', data: times },
      yAxis: { type: 'value', name: 'HbO' },
      series: [{ name: '血氧浓度', type: 'line', smooth: true, data: values, color: '#f59e0b' }],
    });
  }
  if (chartDetail.value === 'duration' && durationDetailRef.value) {
    durationDetailChart?.dispose();
    durationDetailChart = echarts.init(durationDetailRef.value);
    const { days, values } = getDurationData();
    durationDetailChart.setOption({
      tooltip: { trigger: 'axis' },
      grid: { left: '10%', right: '4%', bottom: '12%', top: '8%' },
      xAxis: { type: 'category', data: days },
      yAxis: { type: 'value', name: '分钟' },
      series: [{ name: '阅读时长', type: 'bar', data: values, color: '#10b981' }],
    });
  }
}

async function fetchBoundChildren() {
  if (!props.parentUsername) return;
  loadingBound.value = true;
  try {
    const res = await axios.get(`${API}/parent/bound-children`, {
      params: { parent_username: props.parentUsername },
    });
    if (res.data?.status === 'success' && Array.isArray(res.data.data)) {
      boundChildren.value = res.data.data.map((c: { id: string; name?: string; account: string; subject_id?: number }) => ({
        id: String(c.id),
        name: c.name ?? c.account,
        account: c.account,
        subject_id: c.subject_id,
      }));
      if (currentChildIndex.value >= boundChildren.value.length) currentChildIndex.value = Math.max(0, boundChildren.value.length - 1);
    } else {
      boundChildren.value = [];
    }
  } catch (_) {
    boundChildren.value = [];
  } finally {
    loadingBound.value = false;
  }
}

async function doBind() {
  const account = bindForm.value.account.trim();
  const password = bindForm.value.password.trim();
  if (!account || !password) {
    alert('请输入儿童账号和密码');
    return;
  }
  if (!props.parentUsername) {
    alert('请先登录家长账号');
    return;
  }
  bindLoading.value = true;
  try {
    const res = await axios.post(`${API}/parent/bind`, {
      parent_username: props.parentUsername,
      child_username: account,
      child_password: password,
    });
    if (res.data?.status === 'success') {
      bindForm.value = { account: '', password: '' };
      showBindModal.value = false;
      await fetchBoundChildren();
    } else {
      alert(res.data?.message ?? '关联失败');
    }
  } catch (e: any) {
    const msg = e.response?.data?.detail ?? e.message ?? '关联失败';
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
  } finally {
    bindLoading.value = false;
  }
}

async function doUnbind() {
  const cur = currentChild.value;
  if (!cur || !props.parentUsername) return;
  if (!confirm(`确定要解除与「${cur.name || cur.account}」的关联吗？`)) return;
  try {
    const res = await axios.post(`${API}/parent/unbind`, {
      parent_username: props.parentUsername,
      child_id: Number(cur.id),
    });
    if (res.data?.status === 'success') {
      await fetchBoundChildren();
    } else {
      alert(res.data?.message ?? '解绑失败');
    }
  } catch (e: any) {
    const msg = e.response?.data?.detail ?? e.message ?? '解绑失败';
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }
}

function prevChild() {
  if (currentChildIndex.value > 0) currentChildIndex.value--;
}

function nextChild() {
  if (currentChildIndex.value < boundChildren.value.length - 1) currentChildIndex.value++;
}

// 触摸滑动切换儿童（简单实现）
let touchStartX = 0;
function onTouchStart(e: TouchEvent) {
  touchStartX = e.touches[0].clientX;
}
function onTouchEnd(e: TouchEvent) {
  const dx = e.changedTouches[0].clientX - touchStartX;
  if (dx > 50) prevChild();
  else if (dx < -50) nextChild();
}

function exportExcel() {
  const data = [
    ['阅读报告', ''],
    ['儿童', currentChild.value?.name || currentChild.value?.account || ''],
    ['最近阅读时长(分钟)', overview.value.recentMinutes],
    ['平均专注度(%)', overview.value.avgFocus],
    ['理解难度匹配度(%)', overview.value.matchRate],
    ['生成时间', reportTime.value],
  ];
  const ws = XLSX.utils.aoa_to_sheet(data);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, '阅读报告');
  XLSX.writeFile(wb, `阅读报告_${currentChild.value?.account || 'export'}.xlsx`);
}

function exportPDF() {
  printJS({
    printable: 'report-print-area',
    type: 'html',
    documentTitle: '阅读报告',
    targetStyles: ['*'],
  });
}

watch([focusChartRef, currentChildIndex], () => {
  if (focusChartRef.value && boundChildren.value.length) {
    initFocusChart(focusChartRef.value);
  }
});
watch([hboChartRef, currentChildIndex], () => {
  if (hboChartRef.value && boundChildren.value.length) {
    initHboChart(hboChartRef.value);
  }
});
watch([durationChartRef, currentChildIndex], () => {
  if (durationChartRef.value && boundChildren.value.length) {
    initDurationChart(durationChartRef.value);
  }
});

watch(chartDetail, (v) => {
  if (v) {
    setTimeout(initDetailCharts, 50);
  } else {
    focusDetailChart?.dispose();
    hboDetailChart?.dispose();
    durationDetailChart?.dispose();
    focusDetailChart = hboDetailChart = durationDetailChart = null;
  }
});

onMounted(() => {
  if (focusChartRef.value && boundChildren.value.length) initFocusChart(focusChartRef.value);
  if (hboChartRef.value && boundChildren.value.length) initHboChart(hboChartRef.value);
  if (durationChartRef.value && boundChildren.value.length) initDurationChart(durationChartRef.value);
  window.addEventListener('resize', () => {
    focusChart?.resize();
    hboChart?.resize();
    durationChart?.resize();
    focusDetailChart?.resize();
    hboDetailChart?.resize();
    durationDetailChart?.resize();
  });
});

onUnmounted(() => {
  focusChart?.dispose();
  hboChart?.dispose();
  durationChart?.dispose();
  focusDetailChart?.dispose();
  hboDetailChart?.dispose();
  durationDetailChart?.dispose();
});

watch(() => props.parentUsername, () => {
  fetchBoundChildren();
}, { immediate: true });
</script>

<style scoped>
.parent-page {
  height: 100%;
  width: 100%;
  padding: 20px;
  box-sizing: border-box;
  overflow: auto;
  background: linear-gradient(135deg, #f5f7fa 0%, #eef2ff 100%);
  position: relative;
}

.header {
  margin-bottom: 16px;
}
.title {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #1f2937;
}
.subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}

.empty-bind {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  gap: 16px;
}
.empty-bind p {
  margin: 0;
  color: #6b7280;
}
.hint-small {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px !important;
}
.btn-unbind {
  margin-left: 8px;
  padding: 6px 12px;
  font-size: 12px;
  border-radius: 8px;
  border: 1px solid #fca5a5;
  background: #fef2f2;
  color: #dc2626;
  cursor: pointer;
}
.btn-unbind:hover {
  background: #fee2e2;
}
.btn {
  padding: 10px 20px;
  border-radius: 999px;
  border: 1px solid #ddd;
  background: #fff;
  cursor: pointer;
  font-size: 14px;
}
.btn.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  border: none;
}
.btn.secondary {
  background: #eef2ff;
  color: #667eea;
  border: none;
}

.child-switcher {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 8px;
  touch-action: pan-y;
}
.child-switcher .child-name {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
  min-width: 80px;
  text-align: center;
}
.arrow {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  font-size: 20px;
  color: #6b7280;
}
.arrow:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.child-dots {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-bottom: 20px;
}
.child-dots .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #d1d5db;
  cursor: pointer;
}
.child-dots .dot.active {
  background: #667eea;
  transform: scale(1.2);
}

.overview {
  margin-bottom: 24px;
}
.overview-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}
.overview-cards .card {
  background: #fff;
  border-radius: 14px;
  padding: 14px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.card-label {
  font-size: 12px;
  color: #6b7280;
}
.card-value {
  font-size: 18px;
  font-weight: 700;
  color: #111827;
}

.charts-row {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.chart-wrap {
  background: #fff;
  border-radius: 14px;
  padding: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.06);
  cursor: pointer;
}
.chart-wrap:hover {
  box-shadow: 0 6px 20px rgba(102, 126, 234, 0.15);
}
.chart {
  width: 100%;
  height: 200px;
}
.chart-title {
  margin: 8px 0 0;
  font-size: 13px;
  color: #6b7280;
  text-align: center;
}

.bottom-nav {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: space-around;
  padding: 12px 16px;
  background: #fff;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.06);
  z-index: 10;
}
.nav-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 8px 16px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 12px;
  color: #4b5563;
}
.nav-item .icon {
  font-size: 20px;
}

.sub-page {
  padding-bottom: 80px;
}
.sub-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}
.back {
  border: none;
  background: none;
  cursor: pointer;
  color: #667eea;
  font-size: 14px;
}
.sub-header h3 {
  margin: 0;
  font-size: 18px;
  color: #111827;
}
.sub-body {
  font-size: 14px;
  color: #4b5563;
}
.export-actions {
  display: flex;
  gap: 12px;
  margin: 16px 0;
}
.report-preview {
  background: #f9fafb;
  padding: 16px;
  border-radius: 12px;
  margin-top: 12px;
}
.report-preview h4 {
  margin: 0 0 12px;
  font-size: 16px;
}
.report-preview p {
  margin: 4px 0;
}
.log-list, .recommend-list {
  list-style: none;
  margin: 0;
  padding: 0;
}
.log-item, .recommend-item {
  padding: 12px;
  border-radius: 10px;
  background: #f9fafb;
  margin-bottom: 8px;
}
.log-item .time, .recommend-item .name {
  font-weight: 600;
  margin-right: 8px;
}
.recommend-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.recommend-item .reason {
  font-size: 13px;
  color: #6b7280;
}

.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}
.modal {
  background: #fff;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 360px;
}
.modal h3 {
  margin: 0 0 8px;
  font-size: 18px;
}
.hint {
  margin: 0 0 16px;
  font-size: 13px;
  color: #6b7280;
}
.form-item {
  margin-bottom: 14px;
}
.form-item label {
  display: block;
  margin-bottom: 4px;
  font-size: 13px;
  color: #374151;
}
.form-item input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  box-sizing: border-box;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

.chart-detail-modal {
  position: relative;
  background: #fff;
  border-radius: 16px;
  padding: 20px;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  overflow: auto;
}
.chart-detail-modal .close {
  position: absolute;
  top: 12px;
  right: 12px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 18px;
  color: #6b7280;
}
.chart-detail-modal h3 {
  margin: 0 0 12px;
  font-size: 16px;
}
.chart-detail-body p {
  margin: 0 0 12px;
  font-size: 13px;
  color: #6b7280;
}
.detail-chart {
  width: 100%;
  height: 260px;
}
</style>
