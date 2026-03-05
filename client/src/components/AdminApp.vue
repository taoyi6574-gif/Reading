<template>
  <div class="page">
    <header class="header">
      <div>
        <h2 class="title">管理员端</h2>
        <p class="subtitle">系统管理与运营工具（开发中）</p>
      </div>
    </header>

    <section class="grid">
      <div class="card">
        <h3>用户管理</h3>
        <p>儿童/家长账号、权限与绑定关系管理。</p>
        <button class="btn" disabled>即将上线</button>
      </div>

      <div class="card">
        <h3>书籍管理</h3>
        <p>绘本上架、章节内容维护、标签与推荐策略。</p>
        <button class="btn" disabled>即将上线</button>
      </div>

      <div class="card">
        <h3>设备与数据</h3>
        <p>NIRS 设备状态、数据流监控与异常告警。</p>
        <button class="btn" disabled>即将上线</button>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
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
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}
.card {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 18px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
  backdrop-filter: blur(6px);
}
.card h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #f9fafb;
}
.card p {
  margin: 0 0 14px;
  font-size: 13px;
  line-height: 1.6;
  color: rgba(249, 250, 251, 0.72);
}
.btn {
  border: none;
  border-radius: 999px;
  padding: 10px 14px;
  font-size: 13px;
  font-weight: 700;
  color: #0b1220;
  background: linear-gradient(135deg, #a78bfa, #60a5fa);
  cursor: not-allowed;
  opacity: 0.75;
}
</style>
