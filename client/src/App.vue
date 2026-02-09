<template>
  <div class="app-container">
    <nav class="navbar">
      <div class="brand">
        <span class="logo">🎓</span>
        <span class="title">儿童认知自适应阅读系统</span>
      </div>
      
      <div class="status-panel" v-if="readingStatus !== 'LIBRARY'">
        <button class="btn-text" @click="backToLibrary">⬅ 返回书架</button>
        <div class="divider"></div>
        <div class="indicator">
          <span class="label">专注度:</span>
          <span class="value" :class="focusLevel">{{ focusText[focusLevel] }}</span>
        </div>
        <div class="indicator">
          <span class="label">设备:</span>
          <span class="dot" :class="{ active: isDeviceConnected }"></span>
          <span class="status-text">{{ isDeviceConnected ? '已连接' : '未连接' }}</span>
        </div>
      </div>
    </nav>

    <main class="main-stage">
      
      <transition name="fade">
        <div v-if="readingStatus === 'LIBRARY'" class="layout-full-width" key="library">
          <div class="library-container">
            <div class="library-header">
              <h2>我的书架</h2>
              <p>请选择一本喜欢的绘本开始阅读</p>
            </div>

            <div v-if="isLoadingBooks" class="loading">
              <div class="spinner"></div> 正在获取书籍列表...
            </div>

            <div class="book-grid">
              <div 
                v-for="book in bookList" 
                :key="book.id" 
                class="book-card" 
                @click="selectBook(book)"
              >
                <div class="book-cover">
                  <span class="book-icon">{{ book.cover || '📘' }}</span>
                </div>
                <div class="book-info">
                  <h3>{{ book.title }}</h3>
                  <span class="tag">推荐阅读</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      

      <div v-else class="layout-split" key="reader">
          
          <div class="left-panel">
            
            <div v-if="readingStatus === 'IDLE'" class="setup-container">
              <div class="setup-card">
                <div class="icon-pulse">🎧</div>
                <h2>{{ currentBookTitle }}</h2>
                <p>请为儿童佩戴设备，系统将自动校准</p>
                <div class="signal-status">
                   <span>信号质量：优</span>
                   <div class="signal-bars"><i></i><i></i><i></i></div>
                </div>
                <button class="btn-start" @click="startReading" :disabled="isStarting">
                  {{ isStarting ? '系统启动中...' : '🚀 开始同步记录' }}
                </button>
              </div>
            </div>

            <div v-else class="reader-container" :style="adaptiveStyle" ref="readerRef">
              <div class="paper-sheet">
                 <div class="content-flow">
                    <h3 class="chapter-title">{{ currentChapter.title }}</h3>
                    <p v-for="(para, idx) in currentChapter.content" :key="idx">
                      {{ para }}
                    </p>
                 </div>
                 
                 <div class="touch-zone prev" @click="prevPage" title="上一页"></div>
                 <div class="touch-zone next" @click="nextPage" title="下一页"></div>

                 <div class="page-number">
                   {{ currentVisualPage + 1 }} / {{ totalVisualPages }}
                 </div>
              </div>

              <div v-if="focusLevel === 'LOW'" class="interaction-tip" @click="handleInteraction">
                 <span class="mascot">🐰</span>
                 <span class="text">小朋友，这里有个有趣的问题点我一下！</span>
              </div>
            </div>
          </div>

          <aside class="right-panel">
            <div class="control-card">
              <button class="btn-stop" @click="stopReading">
                <span class="icon">⏹</span> 结束阅读
              </button>
              <div class="timer">时长: {{ formatTime(totalTime) }}</div>
            </div>

            <div class="monitor-card">
              <h4>实时脑血氧 (HbO)</h4>
              <div class="chart-wrapper">
                <NirsMonitor :latestData="nirsData" :isConnected="isDeviceConnected" />
              </div>
            </div>

            <div class="log-card">
              <h4>系统日志</h4>
              <div class="log-list">
                 <div v-for="(log, i) in actionLogs" :key="i" class="log-item">{{ log }}</div>
              </div>
            </div>
          </aside>
        </div>
      </transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import axios from 'axios';
import NirsMonitor from './components/NirsMonitor.vue';

// --- 类型与状态 ---
type Status = 'LIBRARY' | 'IDLE' | 'ACTIVE' | 'FINISHED';
const readingStatus = ref<Status>('LIBRARY');
const bookList = ref<any[]>([]);
const isLoadingBooks = ref(false);
const currentBookTitle = ref("");
const currentBookData = ref<any>(null);

// 信号与设备
const focusLevel = ref('NORMAL');
const focusText: Record<string, string> = { 'LOW': '走神', 'NORMAL': '良好', 'HIGH': '专注' };
const isDeviceConnected = ref(false);
const nirsData = ref(null);
const isStarting = ref(false);
const currentSessionId = ref<number | null>(null);
const actionLogs = ref<string[]>([]);
const sessionStartTime = ref(0);
const totalTime = ref(0);
let timerInterval: any = null;

// 阅读器状态
const currentChapterIndex = ref(0);
const currentVisualPage = ref(0);
const totalVisualPages = ref(1);
const readerRef = ref<HTMLElement | null>(null);
const pageWidth = ref(0);
const columnGap = 160;

// --- 核心逻辑 ---

// 1. 获取书架
const fetchBookList = async () => {
  isLoadingBooks.value = true;
  try {
    const res = await axios.get('http://localhost:8000/api/v1/books/list');
    bookList.value = res.data.data;
  } catch(e) {} finally { isLoadingBooks.value = false; }
};

const selectBook = async (book: any) => {
  try {
    const res = await axios.get(`http://localhost:8000/api/v1/books/content/${book.id}`);
    currentBookData.value = res.data.data;
    currentBookTitle.value = res.data.data.title;
    readingStatus.value = 'IDLE'; // 进入准备界面
    connectSocket(); // 提前连接 WS
  } catch(e) { alert("书籍加载失败"); }
};

// 2. 启动同步记录 (Multi-modal Synchronization)
let socket: WebSocket | null = null;

const connectSocket = () => {
  if (socket && socket.readyState === WebSocket.OPEN) return;
  socket = new WebSocket('ws://localhost:8000/api/v1/stream/ws');
  socket.onopen = () => { isDeviceConnected.value = true; };
  socket.onmessage = (e) => {
    const data = JSON.parse(e.data);
    nirsData.value = data;
    if (data.analysis?.focus_level) focusLevel.value = data.analysis.focus_level;
  };
  socket.onclose = () => { isDeviceConnected.value = false; };
};

const startReading = async () => {
  isStarting.value = true;
  try {
    // A. 告诉后端：创建数据库 Session (行为数据以此 ID 存储)
    const res = await axios.post('http://localhost:8000/api/v1/behavior/start_session', {
      subject_id: 1, 
      book_title: currentBookTitle.value
    });
    
    if (res.data.status === 'success') {
      currentSessionId.value = res.data.session_id;
      
      // B. 告诉后端：开始 NIRS 录制 (生理数据以此 ID 存储，且使用同一时间基准)
      if (socket) {
        socket.send(JSON.stringify({ 
          command: "START", 
          session_id: currentSessionId.value 
        }));
      }
      
      // C. 前端状态切换
      readingStatus.value = 'ACTIVE';
      currentChapterIndex.value = 0;
      currentVisualPage.value = 0;
      sessionStartTime.value = Date.now();
      startTimer();
      
      // D. 等待 DOM 渲染后计算页数
      nextTick(() => {
        setTimeout(calculatePages, 100);
      });
    }
  } catch (e) {
    alert("系统启动失败，请检查后端");
  } finally {
    isStarting.value = false;
  }
};

const stopReading = async () => {
  // 停止 NIRS 流
  if (socket) socket.send(JSON.stringify({ command: "STOP" }));
  // 结束 Session
  if (currentSessionId.value) {
    await axios.post(`http://localhost:8000/api/v1/behavior/end_session/${currentSessionId.value}`);
  }
  stopTimer();
  readingStatus.value = 'LIBRARY';
  currentSessionId.value = null;
};

// 3. 阅读器逻辑 (CSS Columns + Transform)
const currentChapter = computed(() => {
  if (!currentBookData.value) return { title: '', content: [] };
  return currentBookData.value.chapters[currentChapterIndex.value];
});

const adaptiveStyle = computed(() => {
  const transformX = currentVisualPage.value * (pageWidth.value + columnGap);
  if (focusLevel.value === 'LOW') {
    return { 
      '--font-size': '26px', 
      '--line-height': '2.0', 
      '--bg-color': '#fffbf0',
      '--transform-x': `-${transformX}px`,
      '--column-width': `${pageWidth.value}px`
    };
  }
  return { 
    '--font-size': '20px', 
    '--line-height': '1.8', 
    '--bg-color': '#ffffff',
    '--transform-x': `-${transformX}px`,
    '--column-width': `${pageWidth.value}px`
  };
});

// 当样式改变时，重新计算总页数，防止溢出
watch(focusLevel, () => { 
  setTimeout(() => {
    calculatePages();
  }, 300); 
});

const calculatePages = () => {
  const container = document.querySelector('.paper-sheet') as HTMLElement;
  const el = document.querySelector('.content-flow') as HTMLElement;
  if (container && el) {
    // 计算实际可见宽度（减去左右padding）
    const computedStyle = window.getComputedStyle(container);
    const paddingLeft = parseFloat(computedStyle.paddingLeft) || 0;
    const paddingRight = parseFloat(computedStyle.paddingRight) || 0;
    const newPageWidth = container.clientWidth - paddingLeft - paddingRight;
    
    if (newPageWidth > 0) {
      pageWidth.value = newPageWidth;
      
      // 暂时移除 transform 来准确测量内容宽度
      const oldTransform = el.style.transform;
      const oldColumnWidth = el.style.columnWidth;
      el.style.transform = 'translateX(0px)';
      el.style.columnWidth = `${newPageWidth}px`;
      
      // 等待浏览器重新计算列布局
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          // CSS columns 的总宽度计算：scrollWidth 包含所有列和间隙
          const contentWidth = el.scrollWidth;
          // 每页宽度 = 列宽 + 列间隙
          const pageUnit = pageWidth.value + columnGap;
          const calculatedPages = Math.max(1, Math.ceil(contentWidth / pageUnit));
          totalVisualPages.value = calculatedPages;
          
          // 确保当前页数不超出总页数
          if (currentVisualPage.value >= calculatedPages) {
            currentVisualPage.value = Math.max(0, calculatedPages - 1);
          }
          
          // 恢复 transform 和 column-width（通过CSS变量）
          el.style.transform = oldTransform || '';
          el.style.columnWidth = oldColumnWidth || '';
        });
      });
    }
  }
};
// 监听窗口大小变化
window.addEventListener('resize', calculatePages);

const changePage = (offset: number) => {
  const target = currentVisualPage.value + offset;
  
  if (target >= 0 && target < totalVisualPages.value) {
    // 页内翻页
    currentVisualPage.value = target;
    logBehavior(offset > 0 ? 'NEXT_PAGE' : 'PREV_PAGE', `Page ${target+1}`);
  } else if (target >= totalVisualPages.value) {
    // 下一章
    if (currentChapterIndex.value < currentBookData.value.chapters.length - 1) {
      currentChapterIndex.value++;
      currentVisualPage.value = 0;
      nextTick(() => {
        setTimeout(calculatePages, 100);
      });
    } else {
      stopReading();
    }
  } else if (target < 0 && currentChapterIndex.value > 0) {
    // 上一章
    currentChapterIndex.value--;
    currentVisualPage.value = 0; 
    nextTick(() => {
      setTimeout(calculatePages, 100);
    });
  }
};
const prevPage = () => changePage(-1);
const nextPage = () => changePage(1);

// 4. 辅助功能
const logBehavior = (type: string, val: string) => {
  const msg = `${type}: ${val}`;
  actionLogs.value.unshift(msg);
  if (currentSessionId.value) {
    axios.post('http://localhost:8000/api/v1/behavior/log', {
      session_id: currentSessionId.value, event_type: type, event_value: val, timestamp: new Date().toISOString()
    });
  }
};
const handleInteraction = () => { logBehavior("INTERACTION", "Clicked Tip"); alert("记录成功"); };
const backToLibrary = () => { stopReading(); };
const startTimer = () => { timerInterval = setInterval(() => { totalTime.value = Math.floor((Date.now() - sessionStartTime.value)/1000); }, 1000); };
const stopTimer = () => clearInterval(timerInterval);
const formatTime = (s: number) => { const m = Math.floor(s/60); const sec = s%60; return `${m}:${sec.toString().padStart(2,'0')}`; };

onMounted(() => fetchBookList());
onUnmounted(() => { if(socket) socket.close(); window.removeEventListener('resize', calculatePages); });
</script>

<style scoped>
/* === 全局与布局 === */
.app-container {
  height: 100vh; display: flex; flex-direction: column; background: #f5f7fa; font-family: 'PingFang SC', sans-serif;
}

.navbar {
  height: 60px; background: white; padding: 0 30px; display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05); z-index: 100; flex-shrink: 0;
}
.brand { font-size: 20px; font-weight: bold; color: #333; }
.status-panel { display: flex; align-items: center; gap: 20px; font-size: 14px; }
.btn-text { background: none; border: 1px solid #ddd; padding: 5px 12px; border-radius: 4px; cursor: pointer; }
.indicator { display: flex; align-items: center; gap: 6px; }
.value.LOW { color: #ff4d4f; font-weight: bold; }
.dot { width: 8px; height: 8px; background: #ccc; border-radius: 50%; }
.dot.active { background: #52c41a; box-shadow: 0 0 4px #52c41a; }

.main-stage { 
  flex: 1; 
  overflow: hidden; 
  position: relative; 
  width: 100%;
}

/* === 布局 A: 全宽书架 (Library) === */
.layout-full-width {
  width: 100%; 
  height: 100%; 
  overflow-y: auto; 
  padding: 0; 
  box-sizing: border-box;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  background-attachment: fixed;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}
.library-container { 
  width: 100%; 
  max-width: none;
  padding: 40px 30px; 
  box-sizing: border-box;
  min-height: 100%;
  margin: 0;
  display: flex;
  flex-direction: column;
}
.library-header {
  text-align: center; 
  margin-bottom: 50px;
  color: white;
  width: 100%;
}
.library-header h2 {
  font-size: 42px; 
  font-weight: 700; 
  margin: 0 0 15px 0;
  text-shadow: 0 2px 10px rgba(0,0,0,0.2);
  letter-spacing: 2px;
}
.library-header p {
  font-size: 18px; 
  opacity: 0.95;
  font-weight: 300;
}
.loading {
  display: flex; 
  align-items: center; 
  justify-content: center; 
  gap: 15px; 
  color: white; 
  font-size: 18px;
  padding: 60px 0;
  width: 100%;
}
.spinner {
  width: 24px; 
  height: 24px; 
  border: 3px solid rgba(255,255,255,0.3); 
  border-top-color: white; 
  border-radius: 50%; 
  animation: spin 0.8s linear infinite;
}
@keyframes spin { 
  to { transform: rotate(360deg); } 
}
.book-grid {
  display: grid;
  /* 铺满全屏，响应式布局 - 使用 auto-fit 确保铺满 */
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 25px;
  width: 100%;
  max-width: none;
  grid-auto-flow: row;
}
.book-card {
  background: white; 
  border-radius: 16px; 
  overflow: hidden; 
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  cursor: pointer; 
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  position: relative;
  transform: translateY(0);
}
.book-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, #667eea, #764ba2, #f093fb);
  opacity: 0;
  transition: opacity 0.3s;
}
.book-card:hover::before {
  opacity: 1;
}
.book-card:hover { 
  transform: translateY(-12px) scale(1.02); 
  box-shadow: 0 16px 40px rgba(0,0,0,0.25);
}
.book-cover {
  height: 320px; 
  background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
  display: flex; 
  align-items: center; 
  justify-content: center; 
  font-size: 90px;
  position: relative;
  overflow: hidden;
}
.book-cover::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
  animation: shimmer 3s infinite;
}
@keyframes shimmer {
  0%, 100% { transform: translate(-50%, -50%) rotate(0deg); }
  50% { transform: translate(-50%, -50%) rotate(180deg); }
}
.book-icon {
  position: relative;
  z-index: 1;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.2));
}
.book-info { 
  padding: 24px 20px; 
  text-align: center; 
  background: white;
}
.book-info h3 { 
  margin: 0 0 12px 0; 
  color: #333; 
  font-size: 20px; 
  font-weight: 600;
  line-height: 1.4;
}
.tag {
  display: inline-block;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: white;
  padding: 6px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

/* === 布局 B: 分栏模式 (Reader + Sidebar) === */
.layout-split {
  display: flex; width: 100%; height: 100%;
}

/* 左侧：阅读区 (Flex 1 自动占满剩余空间) */
.left-panel {
  flex: 1; position: relative; display: flex; justify-content: center; align-items: center;
  background: #f0f2f5; padding: 20px;
}

/* 右侧：监控区 (固定宽度 300px) */
.right-panel {
  width: 320px; background: white; border-left: 1px solid #eee; display: flex; flex-direction: column;
  padding: 20px; gap: 20px; flex-shrink: 0; z-index: 50;
}

/* 核心组件：控制卡片 */
.control-card {
  background: #fff1f0; border: 1px solid #ffa39e; padding: 20px; border-radius: 8px; text-align: center;
}
.btn-stop {
  width: 100%; background: #ff4d4f; color: white; border: none; padding: 12px; font-size: 16px; 
  border-radius: 6px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 8px;
}
.btn-stop:hover { background: #ff7875; }
.timer { margin-top: 10px; font-family: monospace; font-size: 16px; color: #cf1322; }

/* 核心组件：波形卡片 */
.monitor-card {
  flex: 1; display: flex; flex-direction: column; background: #fff; border: 1px solid #eee; border-radius: 8px; padding: 10px;
}
.chart-wrapper { flex: 1; min-height: 200px; }

.log-card {
  height: 150px; background: #333; color: #0f0; padding: 10px; border-radius: 8px; font-size: 12px; overflow-y: auto; font-family: monospace;
}

/* === 阅读器内部样式 === */
.setup-container { width: 100%; display: flex; justify-content: center; }
.setup-card { background: white; padding: 50px; border-radius: 20px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.08); }
.btn-start { background: #1890ff; color: white; border: none; padding: 15px 40px; border-radius: 30px; font-size: 18px; cursor: pointer; margin-top: 20px; }

.reader-container {
  width: 100%; height: 100%; max-width: 1000px; /* 限制最大阅读宽，防止太宽读着累 */
  display: flex; justify-content: center;
}

.paper-sheet {
  width: 100%; height: 100%;
  background-color: var(--bg-color);
  box-shadow: 0 5px 30px rgba(0,0,0,0.08);
  border-radius: 8px;
  padding: 60px 80px;
  box-sizing: border-box;
  overflow: hidden; /* 关键：隐藏多余列 */
  position: relative;
  transition: background 0.5s;
}

/* CSS 分栏核心 */
.content-flow {
  height: 90%;
  column-width: var(--column-width, 1000px); /* 动态列宽，让浏览器每页只显示一栏 */
  column-gap: 160px; /* 页间距 */
  column-fill: auto;
  transform: translateX(var(--transform-x, 0px)); /* 翻页动画 */
  transition: transform 0.5s cubic-bezier(0.25, 1, 0.5, 1);
  
  font-size: var(--font-size);
  line-height: var(--line-height);
  color: #333;
  text-align: justify;
  white-space: normal;
  word-wrap: break-word;
}

.chapter-title { margin-top: 0; color: #1890ff; margin-bottom: 30px; }
.page-number { position: absolute; bottom: 20px; right: 40px; color: #ccc; font-size: 14px; }

.touch-zone { position: absolute; top: 0; bottom: 0; width: 15%; cursor: pointer; z-index: 10; }
.touch-zone.prev { left: 0; }
.touch-zone.next { right: 0; }
.touch-zone:hover { background: linear-gradient(90deg, rgba(0,0,0,0.03), transparent); }

.interaction-tip {
  position: absolute; bottom: 50px; right: 50px; background: #ff7875; color: white; 
  padding: 15px 25px; border-radius: 30px; cursor: pointer; animation: pop 0.5s; z-index: 20;
}
@keyframes pop { from { transform: translateY(20px); opacity: 0; } to { transform: translateY(0); opacity: 1; } }

/* === 过渡动画 === */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>