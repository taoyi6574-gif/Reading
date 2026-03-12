<template>
  <div class="app-container">
    <!-- 背景白噪音，音量由设置控制，后端可配置音源 -->
    <audio ref="bgNoiseRef" loop muted playsinline></audio>
    <!-- 登录界面 -->
    <div v-if="!isLoggedIn" class="login-page">
      <div class="login-card">
        <h1 class="login-title">儿童认知自适应阅读系统</h1>
        <p class="login-subtitle">请输入账号密码，进入对应端</p>

        <div class="login-form">
          <div class="form-item">
            <label>账号</label>
            <input
              v-model="loginForm.username"
              type="text"
              placeholder="例如：child / parent / admin"
            />
          </div>

          <div class="form-item">
            <label>密码</label>
            <input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
            />
          </div>

          <button class="btn-login" @click="handleLogin">
            登 录
          </button>

          <div class="login-tips">
            <p>示例账号：</p>
            <p>儿童端：child / 123456</p>
            <p>家长端：parent / 123456</p>
            <p>管理员端：admin / 123456</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 登录后主界面 -->
    <template v-else>
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

        <div class="user-panel">
          <span class="user-role">
            当前端口：
            <span v-if="currentRole === 'CHILD'">儿童端</span>
            <span v-else-if="currentRole === 'PARENT'">家长端</span>
            <span v-else-if="currentRole === 'ADMIN'">管理员端</span>
          </span>
          <button class="btn-text" @click="logout">退出登录</button>
        </div>
      </nav>

      <main class="main-stage">
        <!-- 儿童端：保留原有阅读界面 -->
        <div v-if="currentRole === 'CHILD'" class="child-layout">
          <transition name="fade">
            <!-- 书架主页 -->
            <div v-if="readingStatus === 'LIBRARY' && childView === 'LIBRARY'" class="layout-full-width" key="library">
              <div class="library-container">
                <div class="library-header">
                  <h2>我的书架</h2>
                  <p>请选择一本喜欢的绘本开始阅读</p>
                </div>

                <div class="device-summary">
                  <div class="device-status">
                    <span class="dot" :class="{ active: isDeviceConnected }"></span>
                    <span class="text" v-if="isDeviceConnected">设备已连接</span>
                    <span class="text" v-else>
                      设备未连接
                      <button type="button" class="link-btn" @click.stop="openDeviceConnect">去连接设备</button>
                    </span>
                    <button v-if="isDeviceConnected" type="button" class="link-btn link-btn-subtle" @click.stop="openDeviceConnect">连接说明</button>
                  </div>
                  <div class="hbo-status">
                    <span class="label">当前脑血氧 (HbO):</span>
                    <span class="value" v-if="currentHbO !== null">{{ currentHbO.toFixed(3) }} μmol/L</span>
                    <span class="value placeholder" v-else>--</span>
                  </div>
                </div>

                <div v-if="isLoadingBooks" class="loading">
                  <div class="spinner"></div> 正在获取书籍列表...
                </div>

                <div class="book-grid">
                  <div 
                    v-for="book in bookList" 
                    :key="book.id" 
                    class="book-card" 
                    @click="openBookDetail(book)"
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

            <!-- 我的阅读：阅读记录列表 -->
            <div v-else-if="readingStatus === 'LIBRARY' && childView === 'MY_READING'" class="layout-full-width" key="my-reading">
              <div class="library-container my-reading-page">
                <div class="library-header">
                  <h2>我的阅读</h2>
                  <p>最近阅读过的绘本记录</p>
                </div>
                <div v-if="!readingHistory.length" class="empty-hint">还没有阅读记录，可以先从书架选一本绘本开始阅读。</div>
                <ul v-else class="history-list">
                  <li v-for="item in readingHistory" :key="item.bookId" class="history-item">
                    <div class="history-main">
                      <span class="history-title">{{ item.title }}</span>
                      <span class="history-meta">最近阅读：{{ formatRecordTime(item.lastReadAt) }}</span>
                    </div>
                    <button type="button" class="nav-btn primary small" @click="continueBook(item)">继续阅读</button>
                  </li>
                </ul>
                <button type="button" class="nav-btn back-btn" @click="goLibraryHome">返回书架</button>
              </div>
            </div>

            <!-- 设备连接：操作指南、连接/断开/状态 -->
            <div v-else-if="readingStatus === 'LIBRARY' && childView === 'DEVICE'" class="layout-full-width" key="device">
              <div class="library-container device-connect-page">
                <div class="library-header">
                  <h2>设备连接</h2>
                  <p>请按以下步骤完成设备佩戴与连接</p>
                </div>

                <div class="device-control-card">
                  <div class="device-status-row">
                    <span class="dot" :class="{ active: isDeviceConnected }"></span>
                    <span class="status-label">{{ isDeviceConnected ? '已连接' : '未连接' }}</span>
                    <span class="mode-tag">{{ deviceMode === 'sim' ? '模拟模式' : '硬件模式' }}</span>
                  </div>
                  <div class="device-mode-row">
                    <span class="mode-label">数据源模式</span>
                    <select v-model="deviceMode" class="mode-select" :disabled="deviceSwitching">
                      <option value="sim">模拟模式</option>
                      <option value="hardware">硬件模式（NDI/Matlab）</option>
                    </select>
                    <button type="button" class="btn-device secondary" :disabled="deviceSwitching" @click="deviceApplyMode">
                      {{ deviceSwitching ? '切换中...' : '应用' }}
                    </button>
                  </div>
                  <p v-if="deviceMessage" class="device-message">{{ deviceMessage }}</p>
                  <div class="device-actions">
                    <button
                      type="button"
                      class="btn-device primary"
                      :disabled="deviceConnecting"
                      @click="deviceConnect"
                    >
                      {{ deviceConnecting ? '连接中...' : '连接设备' }}
                    </button>
                    <button
                      type="button"
                      class="btn-device"
                      :disabled="deviceDisconnecting"
                      @click="deviceDisconnect"
                    >
                      {{ deviceDisconnecting ? '断开中...' : '断开设备' }}
                    </button>
                    <button
                      type="button"
                      class="btn-device secondary"
                      :disabled="deviceLoadingStatus"
                      @click="deviceFetchStatus"
                    >
                      {{ deviceLoadingStatus ? '查询中...' : '刷新状态' }}
                    </button>
                  </div>
                  <p v-if="deviceError" class="device-error">{{ deviceError }}</p>
                </div>

                <div class="device-steps">
                  <div class="step">
                    <span class="step-num">1</span>
                    <div class="step-body">
                      <h4>佩戴 NIRS 头戴设备</h4>
                      <p>探头紧贴头皮，松紧适中，确保儿童佩戴舒适。</p>
                    </div>
                  </div>
                  <div class="step">
                    <span class="step-num">2</span>
                    <div class="step-body">
                      <h4>启动数据采集软件</h4>
                      <p>在采集端选择当前被试并开始推流。</p>
                    </div>
                  </div>
                  <div class="step">
                    <span class="step-num">3</span>
                    <div class="step-body">
                      <h4>确认连接状态</h4>
                      <p>
                        当前状态：
                        <strong :class="{ 'status-ok': isDeviceConnected, 'status-warn': !isDeviceConnected }">
                          {{ isDeviceConnected ? '已连接，可开始采集' : '未连接，请点击上方「连接设备」' }}
                        </strong>
                      </p>
                    </div>
                  </div>
                </div>
                <button type="button" class="nav-btn back-btn" @click="goLibraryHome">返回书架</button>
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

                    <!-- 低注意力互动弹窗 -->
                    <div v-if="showInteractionPanel" class="interaction-modal">
                      <div class="interaction-card">
                        <button class="interaction-close" @click="closeInteractionPanel">✕</button>
                        <div v-if="interactionType === 'ILLUSTRATION'" class="interaction-content">
                          <div class="illustration-box" @click.stop>
                            <span class="emoji">🌈</span>
                            <p>看看这幅插图里有什么？和刚才读到的内容有什么关系呢？</p>
                          </div>
                        </div>
                        <div v-else class="interaction-content">
                          <p class="question">小问题：刚才故事里出现了哪一个小动物？</p>
                          <input
                            v-model="interactionAnswer"
                            class="answer-input"
                            placeholder="在这里回答一两句～"
                          />
                          <button class="nav-btn primary small" @click="submitInteractionAnswer">完成</button>
                        </div>

                        <div v-if="showReward" class="reward">
                          <span class="emoji">🏅</span>
                          <span>{{ rewardMessage }}</span>
                        </div>
                      </div>
                    </div>

                    <!-- 自适应调整反馈提示 -->
                    <div v-if="showAdaptToast" class="adapt-toast">
                      {{ adaptMessage }}
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
          
          <!-- 底部功能按钮，仅在主界面（书架）展示 -->
          <div v-if="readingStatus === 'LIBRARY'" class="child-bottom-nav">
            <button class="nav-btn primary" @click="handleQuickStart">开始阅读</button>
            <button class="nav-btn" @click="openMyReading">我的阅读</button>
            <button class="nav-btn" @click="openSettings">设置</button>
          </div>

          <!-- 书籍详情弹层：简单介绍与推荐理由 -->
          <div v-if="showBookDetail && selectedBook" class="overlay">
            <div class="sheet">
              <div class="sheet-header">
                <h3>{{ selectedBook.title }}</h3>
                <button class="sheet-close" @click="closeBookDetail">✕</button>
              </div>
              <p class="sheet-subtitle">{{ bookIntro(selectedBook) }}</p>
              <div class="sheet-body">
                <p>{{ bookRecommend(selectedBook) }}</p>
              </div>
              <div class="sheet-footer">
                <button class="nav-btn primary" @click="startFromDetail">开始阅读</button>
              </div>
            </div>
          </div>

          <!-- 设置弹层 -->
          <div v-if="showSettings" class="overlay">
            <div class="sheet">
              <div class="sheet-header">
                <h3>阅读设置</h3>
                <button class="sheet-close" @click="closeSettings">✕</button>
              </div>
              <div class="sheet-body">
                <div class="setting-item">
                  <span>字体大小</span>
                  <input type="range" min="16" max="28" v-model.number="settings.fontSize" />
                  <span>{{ settings.fontSize }}px</span>
                </div>
                <div class="setting-item">
                  <span>音量</span>
                  <input type="range" min="0" max="100" v-model.number="settings.volume" />
                  <span>{{ settings.volume }}</span>
                </div>
              </div>
              <div class="sheet-footer">
                <button class="nav-btn primary" @click="applySettings">保存设置</button>
              </div>
            </div>
          </div>

        </div>

        <ParentApp v-else-if="currentRole === 'PARENT'" :parent-username="currentUsername" />
        <AdminApp v-else-if="currentRole === 'ADMIN'" />
      </main>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue';
import axios from 'axios';
import NirsMonitor from './components/NirsMonitor.vue';
import ParentApp from './components/ParentApp.vue';
import AdminApp from './components/AdminApp.vue';

// --- 类型与状态 ---
type Status = 'LIBRARY' | 'IDLE' | 'ACTIVE' | 'FINISHED';
type UserRole = 'CHILD' | 'PARENT' | 'ADMIN';
type InteractionType = 'ILLUSTRATION' | 'QA';
type ChildView = 'LIBRARY' | 'MY_READING' | 'DEVICE';

const isLoggedIn = ref(false);
const currentRole = ref<UserRole | null>(null);
const currentUsername = ref('');
const childView = ref<ChildView>('LIBRARY');
const loginForm = ref({
  username: '',
  password: ''
});

const readingStatus = ref<Status>('LIBRARY');
const bookList = ref<any[]>([]);
const isLoadingBooks = ref(false);
const currentBookTitle = ref("");
const currentBookData = ref<any>(null);

// 信号与设备
const focusLevel = ref('NORMAL');
const focusText: Record<string, string> = { 'LOW': '走神', 'NORMAL': '良好', 'HIGH': '专注' };
const isDeviceConnected = ref(false);
// 设备连接页：模式、状态、按钮 loading
const deviceMode = ref<'sim' | 'hardware'>('sim');
const deviceMessage = ref('');
const deviceError = ref('');
const deviceConnecting = ref(false);
const deviceDisconnecting = ref(false);
const deviceLoadingStatus = ref(false);
const deviceSwitching = ref(false);

const API_BASE = 'http://localhost:8000/api/v1';
const nirsData = ref<any | null>(null);
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

// 儿童端主界面扩展状态
const lastBookId = ref<number | null>(null);
const selectedBook = ref<any | null>(null);
const showBookDetail = ref(false);

const showSettings = ref(false);
const readingHistory = ref<{ bookId: string | number; title: string; lastReadAt: string }[]>([]);
const settings = ref({
  fontSize: 20,
  volume: 70
});
const bgNoiseRef = ref<HTMLAudioElement | null>(null);

// 生理数值展示
const currentHbO = computed(() => {
  if (!nirsData.value || !nirsData.value.raw_data) return null;
  return nirsData.value.raw_data.hbo as number;
});

// 低注意力互动与奖励
const showInteractionPanel = ref(false);
const interactionType = ref<InteractionType>('QA');
const interactionAnswer = ref('');
const showReward = ref(false);
const rewardMessage = ref('');

// 自适应提示
const showAdaptToast = ref(false);
const adaptMessage = ref('');
let adaptTimer: any = null;

// --- 核心逻辑 ---

// 登录逻辑（后续可接入后端）
const handleLogin = () => {
  const username = loginForm.value.username.trim();
  const password = loginForm.value.password.trim();

  if (!username || !password) {
    alert("请输入账号和密码");
    return;
  }

  // 示例：本地账号密码，后续可改成调用后端接口
  if (username === 'child' && password === '123456') {
    currentRole.value = 'CHILD';
  } else if (username === 'parent' && password === '123456') {
    currentRole.value = 'PARENT';
  } else if (username === 'admin' && password === '123456') {
    currentRole.value = 'ADMIN';
  } else {
    alert("账号或密码错误");
    return;
  }
  currentUsername.value = username;
  isLoggedIn.value = true;
  readingStatus.value = 'LIBRARY';
  if (currentRole.value === 'CHILD') {
    deviceFetchStatus();
  }
};

// 1. 获取书架
const fetchBookList = async () => {
  isLoadingBooks.value = true;
  try {
    const res = await axios.get('http://localhost:8000/api/v1/books/list');
    bookList.value = res.data.data;
  } catch(e) {} finally { isLoadingBooks.value = false; }
};

const selectBook = async (book: any) => {
  const entry = { bookId: book.id, title: book.title || '未知', lastReadAt: new Date().toISOString() };
  const idx = readingHistory.value.findIndex((r) => r.bookId === book.id);
  if (idx >= 0) readingHistory.value[idx] = entry;
  else readingHistory.value.unshift(entry);

  try {
    const res = await axios.get(`http://localhost:8000/api/v1/books/content/${book.id}`);
    currentBookData.value = res.data.data;
    currentBookTitle.value = res.data.data.title;
    readingStatus.value = 'IDLE'; // 进入准备界面
    lastBookId.value = book.id;
    connectSocket(); // 提前连接 WS
  } catch(e) { alert("书籍加载失败"); }
};

// 从书架封面进入“详情”弹层
const openBookDetail = (book: any) => {
  selectedBook.value = book;
  showBookDetail.value = true;
};

const closeBookDetail = () => {
  showBookDetail.value = false;
};

const startFromDetail = () => {
  if (!selectedBook.value) return;
  selectBook(selectedBook.value);
  showBookDetail.value = false;
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
      book_title: currentBookTitle.value,
      book_id: lastBookId.value ?? undefined
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

// 通过底部快捷按钮进入最近阅读
const handleQuickStart = () => {
  if (lastBookId.value) {
    const target = bookList.value.find((b: any) => b.id === lastBookId.value);
    if (target) {
      selectBook(target);
      return;
    }
  }
  alert('还没有最近阅读记录，请先选择一本绘本');
};

// 设置 & 我的阅读
const openSettings = () => { showSettings.value = true; };
const closeSettings = () => { showSettings.value = false; };
const applySettings = () => { showSettings.value = false; };

const openMyReading = async () => {
  childView.value = 'MY_READING';
  try {
    const res = await axios.get('http://localhost:8000/api/v1/reading/history', { params: { subject_id: 1 } });
    if (res.data?.data) readingHistory.value = res.data.data.map((r: { bookId: string; title: string; lastReadAt: string }) => ({
      bookId: r.bookId,
      title: r.title,
      lastReadAt: r.lastReadAt
    }));
  } catch (_) {}
};
const openDeviceConnect = () => {
  childView.value = 'DEVICE';
  deviceError.value = '';
  deviceFetchStatus();
};

async function deviceFetchStatus() {
  deviceLoadingStatus.value = true;
  deviceError.value = '';
  try {
    const res = await axios.get(`${API_BASE}/device/status`);
    const d = res.data;
    isDeviceConnected.value = d?.connected ?? false;
    deviceMode.value = (d?.mode ?? 'sim') as 'sim' | 'hardware';
    deviceMessage.value = d?.message ?? '';
  } catch (e: any) {
    deviceError.value = e?.response?.data?.message ?? e?.message ?? '查询状态失败';
  } finally {
    deviceLoadingStatus.value = false;
  }
}

async function deviceConnect() {
  // 硬件连接前，确保模式已经切到 hardware
  if (deviceMode.value !== 'hardware') {
    deviceError.value = '当前为模拟模式，请先切换到硬件模式再连接设备。';
    return;
  }
  deviceConnecting.value = true;
  deviceError.value = '';
  try {
    const res = await axios.post(`${API_BASE}/device/connect`);
    const d = res.data;
    isDeviceConnected.value = d?.ok && (d?.connected ?? false);
    deviceMode.value = (d?.mode ?? deviceMode.value) as 'sim' | 'hardware';
    deviceMessage.value = d?.message ?? '';
    if (!d?.ok) deviceError.value = d?.message ?? '连接失败';
  } catch (e: any) {
    deviceError.value = e?.response?.data?.message ?? e?.message ?? '连接请求失败';
  } finally {
    deviceConnecting.value = false;
  }
}

async function deviceApplyMode() {
  deviceSwitching.value = true;
  deviceError.value = '';
  try {
    const res = await axios.post(`${API_BASE}/device/mode`, { mode: deviceMode.value });
    const d = res.data;
    if (!d?.ok) {
      deviceError.value = d?.message ?? '切换失败';
      return;
    }
    deviceMessage.value = d?.message ?? '';
    await deviceFetchStatus();
  } catch (e: any) {
    deviceError.value = e?.response?.data?.message ?? e?.message ?? '切换请求失败';
  } finally {
    deviceSwitching.value = false;
  }
}

async function deviceDisconnect() {
  deviceDisconnecting.value = true;
  deviceError.value = '';
  try {
    const res = await axios.post(`${API_BASE}/device/disconnect`);
    const d = res.data;
    isDeviceConnected.value = false;
    deviceMode.value = (d?.mode ?? deviceMode.value) as 'sim' | 'hardware';
    deviceMessage.value = d?.message ?? '已断开';
  } catch (e: any) {
    deviceError.value = e?.response?.data?.message ?? e?.message ?? '断开请求失败';
  } finally {
    deviceDisconnecting.value = false;
  }
}
const goLibraryHome = () => { childView.value = 'LIBRARY'; };

const formatRecordTime = (iso: string) => {
  const d = new Date(iso);
  return d.toLocaleDateString('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' });
};

const continueBook = (item: { bookId: string | number; title: string }) => {
  const book = bookList.value.find((b: any) => b.id === item.bookId);
  if (book) selectBook(book);
};

const bookIntro = (book: any) => book?.description || '适读年龄 3～8 岁，图文并茂，支持互动阅读。';
const bookRecommend = (book: any) => book?.recommendReason || '推荐理由：适合培养专注力与阅读兴趣，可与脑血氧监测配合使用。';

// 退出登录
const logout = () => {
  if (readingStatus.value !== 'LIBRARY') {
    stopReading();
  }
  isLoggedIn.value = false;
  currentRole.value = null;
  currentUsername.value = '';
  loginForm.value.username = '';
  loginForm.value.password = '';
};

// 3. 阅读器逻辑 (CSS Columns + Transform)
const currentChapter = computed(() => {
  if (!currentBookData.value) return { title: '', content: [] };
  return currentBookData.value.chapters[currentChapterIndex.value];
});

const adaptiveStyle = computed(() => {
  const transformX = currentVisualPage.value * (pageWidth.value + columnGap);
  const baseFont = settings.value.fontSize || 20;

  if (focusLevel.value === 'LOW') {
    return { 
      '--font-size': `${baseFont + 6}px`, 
      '--line-height': '2.0', 
      '--bg-color': '#fffbf0',
      '--transform-x': `-${transformX}px`,
      '--column-width': `${pageWidth.value}px`
    };
  }
  return { 
    '--font-size': `${baseFont}px`, 
    '--line-height': '1.8', 
    '--bg-color': '#ffffff',
    '--transform-x': `-${transformX}px`,
    '--column-width': `${pageWidth.value}px`
  };
});

// 自适应反馈提示
const showAdaptiveFeedback = (level: string) => {
  if (readingStatus.value !== 'ACTIVE') return;

  let msg = '';
  if (level === 'LOW') {
    msg = '字体变大啦，宝贝继续加油～';
  } else if (level === 'HIGH') {
    msg = '你很专注，系统为你保持当前设置';
  } else {
    msg = '系统已为你调整到舒适模式';
  }

  adaptMessage.value = msg;
  showAdaptToast.value = true;
  if (adaptTimer) clearTimeout(adaptTimer);
  adaptTimer = setTimeout(() => {
    showAdaptToast.value = false;
  }, 3000);
};

// 当样式 / 注意力改变时，重新计算总页数，防止溢出，并给出提示
watch(focusLevel, (val) => { 
  showAdaptiveFeedback(val);
  setTimeout(() => {
    calculatePages();
  }, 300); 
});

// 音量同步到背景白噪音（后端可提供白噪音音源 URL）
watch(() => settings.value.volume, (v) => {
  if (bgNoiseRef.value) bgNoiseRef.value.volume = (v ?? 0) / 100;
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
const handleInteraction = () => { 
  logBehavior("INTERACTION", "Open Panel");
  interactionType.value = Math.random() > 0.5 ? 'ILLUSTRATION' : 'QA';
  interactionAnswer.value = '';
  showReward.value = false;
  showInteractionPanel.value = true;
};

const submitInteractionAnswer = () => {
  logBehavior('INTERACTION_ANSWER', interactionAnswer.value || 'EMPTY');
  rewardMessage.value = '获得一朵小红花 🌸';
  showReward.value = true;
  setTimeout(() => {
    showInteractionPanel.value = false;
    showReward.value = false;
  }, 2000);
};

const closeInteractionPanel = () => {
  showInteractionPanel.value = false;
};
const backToLibrary = () => { stopReading(); };
const startTimer = () => { timerInterval = setInterval(() => { totalTime.value = Math.floor((Date.now() - sessionStartTime.value)/1000); }, 1000); };
const stopTimer = () => clearInterval(timerInterval);
const formatTime = (s: number) => { const m = Math.floor(s/60); const sec = s%60; return `${m}:${sec.toString().padStart(2,'0')}`; };

onMounted(() => {
  fetchBookList();
  nextTick(() => {
    if (bgNoiseRef.value) bgNoiseRef.value.volume = (settings.value.volume ?? 70) / 100;
  });
});
onUnmounted(() => { if(socket) socket.close(); window.removeEventListener('resize', calculatePages); });
</script>

<style scoped>
/* === 全局与布局 === */
.app-container {
  height: 100vh; display: flex; flex-direction: column; background: #f5f7fa; font-family: 'PingFang SC', sans-serif;
}
.app-container > audio {
  position: absolute;
  width: 0;
  height: 0;
  opacity: 0;
  pointer-events: none;
}

/* 登录页样式 */
.login-page {
  height: 100vh;
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 420px;
  padding: 40px 36px 32px;
  border-radius: 20px;
  background: #ffffff;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.18);
}
.login-title {
  margin: 0;
  font-size: 26px;
  font-weight: 700;
  text-align: center;
  color: #222;
}
.login-subtitle {
  margin: 8px 0 24px;
  font-size: 14px;
  text-align: center;
  color: #888;
}
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-item label {
  font-size: 14px;
  color: #555;
}
.form-item input {
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid #d9d9d9;
  outline: none;
  font-size: 14px;
  transition: all 0.2s;
}
.form-item input:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}
.btn-login {
  margin-top: 8px;
  width: 100%;
  border: none;
  border-radius: 999px;
  padding: 10px 0;
  font-size: 15px;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #667eea, #764ba2);
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.45);
  transition: all 0.2s;
}
.btn-login:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 26px rgba(102, 126, 234, 0.55);
}
.login-tips {
  margin-top: 16px;
  font-size: 12px;
  color: #999;
  line-height: 1.6;
}
.login-tips p {
  margin: 0;
}

.navbar {
  height: 60px; background: white; padding: 0 30px; display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 2px 10px rgba(0,0,0,0.05); z-index: 100; flex-shrink: 0;
}
.brand { font-size: 20px; font-weight: bold; color: #333; }
.user-panel {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 14px;
}
.user-role {
  color: #555;
}
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
.device-summary {
  margin: 0 auto 30px;
  padding: 12px 18px;
  max-width: 760px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #fff;
  font-size: 14px;
}
.device-status {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.device-status .text {
  font-weight: 500;
}
.link-btn {
  margin-left: 4px;
  padding: 2px 10px;
  border-radius: 999px;
  border: none;
  font-size: 12px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.95);
  color: #333;
}
.link-btn-subtle {
  margin-left: 8px;
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: underline;
}
.hbo-status {
  display: flex;
  align-items: center;
  gap: 6px;
}
.hbo-status .label {
  opacity: 0.9;
}
.hbo-status .value {
  font-weight: 600;
}
.hbo-status .placeholder {
  opacity: 0.7;
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

/* 儿童端底部功能栏 */
.child-bottom-nav {
  position: absolute;
  left: 50%;
  bottom: 24px;
  transform: translateX(-50%);
  display: flex;
  gap: 14px;
}
.nav-btn {
  min-width: 110px;
  padding: 10px 16px;
  border-radius: 999px;
  border: none;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.9);
  color: #333;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.18);
}
.nav-btn.primary {
  background: linear-gradient(135deg, #ff9a9e, #fecf99);
  color: #6b1b1b;
}
.nav-btn.small {
  min-width: 80px;
  padding-inline: 12px;
  font-size: 13px;
}

/* 我的阅读页 */
.my-reading-page {
  align-items: flex-start;
}
.empty-hint {
  margin-top: 12px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.95);
}
.history-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  width: 100%;
  max-width: 560px;
  margin-inline: auto;
}
.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
}
.history-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.history-title {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.history-meta {
  font-size: 12px;
  color: #6b7280;
}
.back-btn {
  margin-top: 20px;
}

/* 设备连接页 */
.device-connect-page {
  align-items: flex-start;
}
.device-control-card {
  width: 100%;
  max-width: 560px;
  margin: 0 auto 24px;
  padding: 20px 24px;
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}
.device-status-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.device-status-row .dot {
  width: 12px;
  height: 12px;
}
.device-status-row .status-label {
  font-size: 16px;
  font-weight: 600;
  color: #111827;
}
.device-mode-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 12px;
}
.mode-label {
  font-size: 13px;
  color: #4b5563;
  min-width: 72px;
}
.mode-select {
  flex: 1;
  min-width: 200px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #fff;
  font-size: 13px;
}
.mode-tag {
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: rgba(255, 255, 255, 0.95);
}
.device-message {
  margin: 0 0 14px;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}
.device-error {
  margin: 12px 0 0;
  font-size: 13px;
  color: #dc2626;
}
.device-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}
.btn-device {
  padding: 10px 18px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  background: #f9fafb;
  color: #374151;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-device:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.btn-device.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  color: #fff;
}
.btn-device.primary:hover:not(:disabled) {
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}
.btn-device.secondary {
  background: transparent;
  border-color: #667eea;
  color: #667eea;
}
.device-steps {
  display: flex;
  flex-direction: column;
  gap: 14px;
  width: 100%;
  max-width: 560px;
  margin-inline: auto;
}
.device-connect-page .step {
  display: flex;
  gap: 12px;
  padding: 14px 18px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.95);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.12);
}
.step-num {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea, #764ba2);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
}
.step-body h4 {
  margin: 0 0 6px;
  font-size: 15px;
  color: #111827;
}
.step-body p {
  margin: 0;
  font-size: 13px;
  color: #4b5563;
  line-height: 1.5;
}
.status-ok {
  color: #16a34a;
}
.status-warn {
  color: #dc2626;
}
.device-connect-page .back-btn {
  margin-top: 24px;
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

/* 互动弹窗与自适应提示 */
.interaction-modal {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.25);
  z-index: 30;
}
.interaction-card {
  width: 360px;
  max-width: 90%;
  background: #fff;
  border-radius: 16px;
  padding: 18px 18px 14px;
  position: relative;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.25);
}
.interaction-close {
  position: absolute;
  top: 10px;
  right: 10px;
  border: none;
  background: transparent;
  cursor: pointer;
}
.interaction-content {
  margin-top: 10px;
}
.illustration-box {
  border-radius: 12px;
  padding: 18px;
  background: linear-gradient(135deg, #ffecd2, #fcb69f);
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.illustration-box .emoji {
  font-size: 32px;
}
.question {
  margin: 0 0 8px;
  font-size: 14px;
  color: #333;
}
.answer-input {
  width: 100%;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid #d9d9d9;
  font-size: 13px;
  margin-bottom: 8px;
}
.reward {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #faad14;
}
.reward .emoji {
  font-size: 18px;
}
.adapt-toast {
  position: absolute;
  left: 50%;
  top: 16px;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.75);
  color: #fff;
  padding: 8px 14px;
  border-radius: 999px;
  font-size: 13px;
  z-index: 40;
}

/* 通用弹层样式：设置、书籍详情、我的阅读 */
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  z-index: 120;
}
.sheet {
  width: 100%;
  max-width: 500px;
  background: #fff;
  border-radius: 18px 18px 0 0;
  padding: 16px 18px 18px;
  box-shadow: 0 -10px 30px rgba(0, 0, 0, 0.25);
}
.sheet-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.sheet-header h3 {
  margin: 0;
  font-size: 18px;
}
.sheet-close {
  border: none;
  background: transparent;
  cursor: pointer;
}
.sheet-subtitle {
  margin: 0 0 10px;
  font-size: 13px;
  color: #666;
}
.sheet-body {
  font-size: 14px;
  color: #444;
}
.sheet-footer {
  margin-top: 14px;
  display: flex;
  justify-content: flex-end;
}
.setting-item {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}
.setting-item span:first-child {
  min-width: 72px;
}
.setting-item input[type="range"] {
  flex: 1;
}

/* === 过渡动画 === */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.3s ease;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>