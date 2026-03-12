<template>
  <div class="page">
    <header class="header">
      <div>
        <h2 class="title">管理员端</h2>
        <p class="subtitle">用户管理 · 阅读数据管理</p>
      </div>
    </header>

    <nav class="tabs">
      <button
        type="button"
        class="tab"
        :class="{ active: tab === 'users' }"
        @click="tab = 'users'"
      >
        用户管理
      </button>
      <button
        type="button"
        class="tab"
        :class="{ active: tab === 'data' }"
        @click="tab = 'data'"
      >
        数据管理
      </button>
    </nav>

    <!-- 用户管理 -->
    <section v-show="tab === 'users'" class="panel">
      <div class="block">
        <div class="block-head">
          <h3>账号列表</h3>
          <div class="filters">
            <select v-model="userRoleFilter" @change="fetchUsers">
              <option value="">全部角色</option>
              <option value="CHILD">儿童</option>
              <option value="PARENT">家长</option>
              <option value="ADMIN">管理员</option>
            </select>
            <button type="button" class="btn primary" @click="openUserForm()">新增账号</button>
          </div>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>账号</th>
                <th>角色</th>
                <th>显示名</th>
                <th>被试编号</th>
                <th>创建时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="u in users" :key="u.id">
                <td>{{ u.id }}</td>
                <td>{{ u.username }}</td>
                <td>{{ u.role }}</td>
                <td>{{ u.display_name || '-' }}</td>
                <td>{{ u.subject_code || '-' }}</td>
                <td>{{ formatDate(u.created_at) }}</td>
                <td>
                  <button type="button" class="btn-sm" @click="openUserForm(u)">编辑</button>
                  <button type="button" class="btn-sm danger" @click="deleteUser(u)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="users.length === 0 && !loadingUsers" class="empty">暂无用户</p>
        </div>
      </div>

      <div class="block">
        <div class="block-head">
          <h3>家长-儿童关联关系</h3>
          <button type="button" class="btn primary" @click="openBindingForm()">新增绑定</button>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>家长</th>
                <th>儿童</th>
                <th>绑定时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="b in bindings" :key="b.id">
                <td>{{ b.id }}</td>
                <td>{{ b.parent_name || b.parent_username }}</td>
                <td>{{ b.child_name || b.child_username }}</td>
                <td>{{ formatDate(b.created_at) }}</td>
                <td>
                  <button type="button" class="btn-sm danger" @click="deleteBinding(b)">解绑</button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="bindings.length === 0 && !loadingBindings" class="empty">暂无绑定</p>
        </div>
      </div>
    </section>

    <!-- 数据管理：阅读记录 -->
    <section v-show="tab === 'data'" class="panel">
      <div class="block">
        <div class="block-head">
          <h3>阅读记录</h3>
          <div class="filters">
            <select v-model="dataSubjectId" @change="fetchSessions">
              <option value="">全部儿童</option>
              <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.subject_code }} (ID {{ s.id }})</option>
            </select>
            <input v-model="dataBookTitle" type="text" placeholder="书名" class="input-sm" @keyup.enter="fetchSessions" />
            <input v-model="dataStartDate" type="date" class="input-sm" />
            <input v-model="dataEndDate" type="date" class="input-sm" />
            <button type="button" class="btn" @click="fetchSessions">查询</button>
            <button type="button" class="btn primary" @click="openSessionForm()">新增记录</button>
          </div>
        </div>
        <div class="table-wrap">
          <table class="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>儿童</th>
                <th>书名</th>
                <th>开始时间</th>
                <th>结束时间</th>
                <th>平均专注度</th>
                <th>干预次数</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in sessions" :key="s.id">
                <td>{{ s.id }}</td>
                <td>{{ s.child_display_name || s.child_username || s.subject_code }}</td>
                <td>{{ s.book_title }}</td>
                <td>{{ formatDateTime(s.start_time) }}</td>
                <td>{{ formatDateTime(s.end_time) }}</td>
                <td>{{ s.avg_focus_score }}</td>
                <td>{{ s.intervention_count }}</td>
                <td>
                  <button type="button" class="btn-sm" @click="openSessionForm(s)">编辑</button>
                  <button type="button" class="btn-sm danger" @click="deleteSession(s)">删除</button>
                </td>
              </tr>
            </tbody>
          </table>
          <p v-if="sessions.length === 0 && !loadingSessions" class="empty">暂无记录</p>
          <p v-else class="total">共 {{ totalSessions }} 条</p>
        </div>
      </div>
    </section>

    <!-- 用户 新增/编辑 弹层 -->
    <div v-if="showUserModal" class="overlay" @click.self="showUserModal = false">
      <div class="modal">
        <h3>{{ editingUser ? '编辑用户' : '新增用户' }}</h3>
        <div class="form-item">
          <label>账号</label>
          <input v-model="userForm.username" type="text" :disabled="!!editingUser" placeholder="登录用账号" />
        </div>
        <div class="form-item">
          <label>密码</label>
          <input v-model="userForm.password" type="password" :placeholder="editingUser ? '留空则不修改' : '请输入密码'" />
        </div>
        <div class="form-item">
          <label>角色</label>
          <select v-model="userForm.role" :disabled="!!editingUser">
            <option value="CHILD">儿童</option>
            <option value="PARENT">家长</option>
            <option value="ADMIN">管理员</option>
          </select>
        </div>
        <div class="form-item">
          <label>显示名</label>
          <input v-model="userForm.display_name" type="text" placeholder="如 小明、家长" />
        </div>
        <div v-if="userForm.role === 'CHILD' && !editingUser" class="form-item">
          <label>关联被试</label>
          <select v-model="userForm.subject_id">
            <option :value="undefined">自动创建新被试</option>
            <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.subject_code }} (ID {{ s.id }})</option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="showUserModal = false">取消</button>
          <button type="button" class="btn primary" :disabled="userSaving" @click="saveUser">{{ userSaving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- 关联关系 新增 弹层 -->
    <div v-if="showBindingModal" class="overlay" @click.self="showBindingModal = false">
      <div class="modal">
        <h3>新增绑定</h3>
        <div class="form-item">
          <label>家长</label>
          <select v-model="bindingForm.parent_id">
            <option :value="0">请选择</option>
            <option v-for="u in usersFiltered('PARENT')" :key="u.id" :value="u.id">{{ u.display_name || u.username }} ({{ u.username }})</option>
          </select>
        </div>
        <div class="form-item">
          <label>儿童</label>
          <select v-model="bindingForm.child_id">
            <option :value="0">请选择</option>
            <option v-for="u in usersFiltered('CHILD')" :key="u.id" :value="u.id">{{ u.display_name || u.username }} ({{ u.username }})</option>
          </select>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="showBindingModal = false">取消</button>
          <button type="button" class="btn primary" :disabled="bindingSaving" @click="saveBinding">{{ bindingSaving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>

    <!-- 阅读记录 新增/编辑 弹层 -->
    <div v-if="showSessionModal" class="overlay" @click.self="showSessionModal = false">
      <div class="modal modal-wide">
        <h3>{{ editingSession ? '编辑阅读记录' : '新增阅读记录' }}</h3>
        <div class="form-item">
          <label>儿童（被试）</label>
          <select v-model="sessionForm.subject_id" :disabled="!!editingSession">
            <option :value="0">请选择</option>
            <option v-for="s in subjects" :key="s.id" :value="s.id">{{ s.subject_code }} (ID {{ s.id }})</option>
          </select>
        </div>
        <div class="form-item">
          <label>书名</label>
          <input v-model="sessionForm.book_title" type="text" placeholder="如 小王子" />
        </div>
        <div class="form-item">
          <label>书籍ID</label>
          <input v-model="sessionForm.book_id" type="text" placeholder="如 小王子.txt，可留空" />
        </div>
        <div v-if="editingSession" class="form-row">
          <div class="form-item">
            <label>结束时间</label>
            <input v-model="sessionForm.end_time" type="datetime-local" />
          </div>
        </div>
        <div class="form-row">
          <div class="form-item">
            <label>平均专注度</label>
            <input v-model.number="sessionForm.avg_focus_score" type="number" step="0.1" />
          </div>
          <div class="form-item">
            <label>干预次数</label>
            <input v-model.number="sessionForm.intervention_count" type="number" />
          </div>
        </div>
        <div class="modal-actions">
          <button type="button" class="btn" @click="showSessionModal = false">取消</button>
          <button type="button" class="btn primary" :disabled="sessionSaving" @click="saveSession">{{ sessionSaving ? '保存中...' : '保存' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import axios from 'axios';

const API = 'http://localhost:8000/api/v1';

const tab = ref<'users' | 'data'>('users');

// 用户
const users = ref<any[]>([]);
const loadingUsers = ref(false);
const userRoleFilter = ref('');
const showUserModal = ref(false);
const editingUser = ref<any>(null);
const userSaving = ref(false);
const userForm = ref({
  username: '',
  password: '',
  role: 'CHILD',
  display_name: '',
  subject_id: undefined as number | undefined,
});

// 绑定
const bindings = ref<any[]>([]);
const loadingBindings = ref(false);
const showBindingModal = ref(false);
const bindingSaving = ref(false);
const bindingForm = ref({ parent_id: 0, child_id: 0 });

// 被试（儿童）
const subjects = ref<{ id: number; subject_code: string; age?: number; gender?: string }[]>([]);

// 阅读记录
const sessions = ref<any[]>([]);
const totalSessions = ref(0);
const loadingSessions = ref(false);
const dataSubjectId = ref<number | ''>('');
const dataBookTitle = ref('');
const dataStartDate = ref('');
const dataEndDate = ref('');
const showSessionModal = ref(false);
const editingSession = ref<any>(null);
const sessionSaving = ref(false);
const sessionForm = ref({
  subject_id: 0,
  book_title: '',
  book_id: '',
  start_time: '',
  end_time: '',
  avg_focus_score: 0,
  intervention_count: 0,
});

function formatDate(iso: string | null) {
  if (!iso) return '-';
  return new Date(iso).toLocaleDateString('zh-CN');
}
function formatDateTime(iso: string | null) {
  if (!iso) return '-';
  return new Date(iso).toLocaleString('zh-CN');
}

function usersFiltered(role: string) {
  return users.value.filter((u: any) => u.role === role);
}

async function fetchSubjects() {
  try {
    const res = await axios.get(`${API}/admin/subjects`);
    if (res.data?.status === 'success') subjects.value = res.data.data || [];
  } catch (_) {
    subjects.value = [];
  }
}

async function fetchUsers() {
  loadingUsers.value = true;
  try {
    const params: any = {};
    if (userRoleFilter.value) params.role = userRoleFilter.value;
    const res = await axios.get(`${API}/admin/users`, { params });
    if (res.data?.status === 'success') users.value = res.data.data || [];
    else users.value = [];
  } catch (_) {
    users.value = [];
  } finally {
    loadingUsers.value = false;
  }
}

async function fetchBindings() {
  loadingBindings.value = true;
  try {
    const res = await axios.get(`${API}/admin/bindings`);
    if (res.data?.status === 'success') bindings.value = res.data.data || [];
    else bindings.value = [];
  } catch (_) {
    bindings.value = [];
  } finally {
    loadingBindings.value = false;
  }
}

async function fetchSessions() {
  loadingSessions.value = true;
  try {
    const params: any = { limit: 200, offset: 0 };
    if (dataSubjectId.value !== '') params.subject_id = dataSubjectId.value;
    if (dataBookTitle.value) params.book_title = dataBookTitle.value;
    if (dataStartDate.value) params.start_date = dataStartDate.value;
    if (dataEndDate.value) params.end_date = dataEndDate.value;
    const res = await axios.get(`${API}/admin/reading-sessions`, { params });
    if (res.data?.status === 'success') {
      sessions.value = res.data.data || [];
      totalSessions.value = res.data.total ?? sessions.value.length;
    } else {
      sessions.value = [];
      totalSessions.value = 0;
    }
  } catch (_) {
    sessions.value = [];
    totalSessions.value = 0;
  } finally {
    loadingSessions.value = false;
  }
}

function openUserForm(u?: any) {
  editingUser.value = u ?? null;
  if (u) {
    userForm.value = {
      username: u.username,
      password: '',
      role: u.role,
      display_name: u.display_name || '',
      subject_id: u.subject_id ?? undefined,
    };
  } else {
    userForm.value = {
      username: '',
      password: '',
      role: 'CHILD',
      display_name: '',
      subject_id: undefined,
    };
  }
  showUserModal.value = true;
}

async function saveUser() {
  if (!userForm.value.username.trim()) {
    alert('请输入账号');
    return;
  }
  if (!editingUser.value && !userForm.value.password) {
    alert('请输入密码');
    return;
  }
  userSaving.value = true;
  try {
    if (editingUser.value) {
      await axios.put(`${API}/admin/users/${editingUser.value.id}`, {
        display_name: userForm.value.display_name || undefined,
        password: userForm.value.password || undefined,
      });
      alert('保存成功');
    } else {
      await axios.post(`${API}/admin/users`, {
        username: userForm.value.username.trim(),
        password: userForm.value.password,
        role: userForm.value.role,
        display_name: userForm.value.display_name || undefined,
        subject_id: userForm.value.subject_id || undefined,
      });
      alert('创建成功');
    }
    showUserModal.value = false;
    fetchUsers();
    fetchSubjects();
  } catch (e: any) {
    const msg = e.response?.data?.detail ?? e.message ?? '操作失败';
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
  } finally {
    userSaving.value = false;
  }
}

function deleteUser(u: any) {
  if (!confirm(`确定删除用户「${u.username}」？其关联的绑定关系也会被移除。`)) return;
  axios.delete(`${API}/admin/users/${u.id}`).then(() => {
    fetchUsers();
    fetchBindings();
    fetchSubjects();
  }).catch((e: any) => {
    alert(e.response?.data?.detail ?? '删除失败');
  });
}

function openBindingForm() {
  bindingForm.value = { parent_id: 0, child_id: 0 };
  showBindingModal.value = true;
}

async function saveBinding() {
  if (!bindingForm.value.parent_id || !bindingForm.value.child_id) {
    alert('请选择家长和儿童');
    return;
  }
  bindingSaving.value = true;
  try {
    await axios.post(`${API}/admin/bindings`, bindingForm.value);
    alert('绑定成功');
    showBindingModal.value = false;
    fetchBindings();
  } catch (e: any) {
    const msg = e.response?.data?.detail ?? e.message ?? '操作失败';
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
  } finally {
    bindingSaving.value = false;
  }
}

function deleteBinding(b: any) {
  if (!confirm(`确定解除「${b.parent_username}」与「${b.child_username}」的绑定？`)) return;
  axios.delete(`${API}/admin/bindings/${b.id}`).then(() => {
    fetchBindings();
  }).catch((e: any) => {
    alert(e.response?.data?.detail ?? '操作失败');
  });
}

function openSessionForm(s?: any) {
  editingSession.value = s ?? null;
  if (s) {
    sessionForm.value = {
      subject_id: s.subject_id,
      book_title: s.book_title,
      book_id: s.book_id || '',
      start_time: '',
      end_time: s.end_time ? s.end_time.slice(0, 16) : '',
      avg_focus_score: s.avg_focus_score ?? 0,
      intervention_count: s.intervention_count ?? 0,
    };
  } else {
    sessionForm.value = {
      subject_id: subjects.value[0]?.id ?? 0,
      book_title: '',
      book_id: '',
      start_time: '',
      end_time: '',
      avg_focus_score: 0,
      intervention_count: 0,
    };
  }
  showSessionModal.value = true;
}

async function saveSession() {
  if (!sessionForm.value.subject_id || !sessionForm.value.book_title.trim()) {
    alert('请选择儿童并填写书名');
    return;
  }
  sessionSaving.value = true;
  try {
    if (editingSession.value) {
      await axios.put(`${API}/admin/reading-sessions/${editingSession.value.id}`, {
        book_title: sessionForm.value.book_title,
        book_id: sessionForm.value.book_id || undefined,
        end_time: sessionForm.value.end_time ? new Date(sessionForm.value.end_time).toISOString() : undefined,
        avg_focus_score: sessionForm.value.avg_focus_score,
        intervention_count: sessionForm.value.intervention_count,
      });
      alert('保存成功');
    } else {
      await axios.post(`${API}/admin/reading-sessions`, {
        subject_id: sessionForm.value.subject_id,
        book_title: sessionForm.value.book_title,
        book_id: sessionForm.value.book_id || undefined,
        avg_focus_score: sessionForm.value.avg_focus_score,
        intervention_count: sessionForm.value.intervention_count,
      });
      alert('创建成功');
    }
    showSessionModal.value = false;
    fetchSessions();
  } catch (e: any) {
    const msg = e.response?.data?.detail ?? e.message ?? '操作失败';
    alert(typeof msg === 'string' ? msg : JSON.stringify(msg));
  } finally {
    sessionSaving.value = false;
  }
}

function deleteSession(s: any) {
  if (!confirm(`确定删除阅读记录 #${s.id}？`)) return;
  axios.delete(`${API}/admin/reading-sessions/${s.id}`).then(() => {
    fetchSessions();
  }).catch((e: any) => {
    alert(e.response?.data?.detail ?? '删除失败');
  });
}

watch(tab, (t) => {
  if (t === 'users') {
    fetchUsers();
    fetchBindings();
  } else {
    fetchSubjects();
    fetchSessions();
  }
}, { immediate: true });
</script>

<style scoped>
.page {
  height: 100%;
  width: 100%;
  padding: 24px;
  box-sizing: border-box;
  overflow: auto;
  background: linear-gradient(135deg, #0b1220 0%, #111827 60%, #1f2937 100%);
}
.header {
  margin-bottom: 18px;
}
.title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #f9fafb;
  letter-spacing: 0.5px;
}
.subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: rgba(249, 250, 251, 0.7);
}
.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}
.tab {
  padding: 10px 20px;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 10px;
  background: rgba(255,255,255,0.05);
  color: rgba(249,250,251,0.9);
  cursor: pointer;
  font-size: 14px;
}
.tab.active {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border-color: transparent;
  color: #fff;
}
.panel {
  margin-bottom: 32px;
}
.block {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 20px;
}
.block-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.block-head h3 {
  margin: 0;
  font-size: 16px;
  color: #f9fafb;
}
.filters {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}
.input-sm {
  padding: 6px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(0,0,0,0.2);
  color: #f9fafb;
  font-size: 13px;
}
.table-wrap {
  overflow-x: auto;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.table th,
.table td {
  padding: 10px 12px;
  text-align: left;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  color: rgba(249,250,251,0.9);
}
.table th {
  color: rgba(249,250,251,0.7);
  font-weight: 600;
}
.empty, .total {
  margin: 12px 0 0;
  font-size: 13px;
  color: rgba(249,250,251,0.6);
}
.btn {
  padding: 8px 14px;
  border-radius: 8px;
  border: 1px solid rgba(255,255,255,0.25);
  background: rgba(255,255,255,0.1);
  color: #f9fafb;
  cursor: pointer;
  font-size: 13px;
}
.btn.primary {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  border: none;
}
.btn-sm {
  padding: 4px 10px;
  margin-right: 6px;
  border-radius: 6px;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.08);
  color: #e0e7ff;
  cursor: pointer;
  font-size: 12px;
}
.btn-sm.danger {
  border-color: rgba(248,113,113,0.5);
  color: #fca5a5;
}
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 20px;
}
.modal {
  background: #1f2937;
  border-radius: 16px;
  padding: 24px;
  width: 100%;
  max-width: 400px;
  border: 1px solid rgba(255,255,255,0.1);
}
.modal-wide {
  max-width: 480px;
}
.modal h3 {
  margin: 0 0 20px;
  font-size: 18px;
  color: #f9fafb;
}
.form-item {
  margin-bottom: 14px;
}
.form-item label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: rgba(249,250,251,0.7);
}
.form-item input,
.form-item select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  background: rgba(0,0,0,0.3);
  color: #f9fafb;
  font-size: 14px;
  box-sizing: border-box;
}
.form-row {
  display: flex;
  gap: 12px;
}
.form-row .form-item {
  flex: 1;
}
.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
