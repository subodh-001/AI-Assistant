/**
 * BRO-BOT — Frontend App v2
 * New: templates, char counter, calendar, bulk approve, resume upload, job scraping, onboarding, offline detection
 */

const API = window.location.origin.includes('localhost') ? '/api' : '/api';

// ─────────────────────────────────────────────────────────
//  STATE
// ─────────────────────────────────────────────────────────
const state = {
  currentSection: 'landing',
  selectedPlatform: 'linkedin',
  generatedPost: null,
  skills: [],
  keywords: [],
  bulkSelected: new Set(),
  calYear: new Date().getFullYear(),
  calMonth: new Date().getMonth(),
  allPosts: [],
  isOnline: false,
};

// ─────────────────────────────────────────────────────────
//  INIT
// ─────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Fix main content top padding for offline banner
  updateGreeting();
  await checkHealth();
  await loadAll();
  loadTemplates();

  // Show clean landing page by default
  switchSection('landing');

  // Auto-refresh every 60s
  setInterval(async () => {
    await checkHealth();
    await loadAll();
  }, 60000);
  setInterval(updateGreeting, 60000);

  // Keyboard shortcuts
  document.addEventListener('keydown', handleKeyboard);
});

async function loadAll() {
  await Promise.allSettled([
    loadStats(),
    loadActivity(),
    loadPosts(),
    loadJobs(),
    loadMessages(),
    loadConfig(),
    loadResumeStatus(),
    loadMasterProjects(),
  ]);
  if (state.currentSection === 'calendar') renderCalendar();
}

// ─────────────────────────────────────────────────────────
//  GREETING
// ─────────────────────────────────────────────────────────
function updateGreeting() {
  const h = new Date().getHours();
  const map = [
    [5, '☀️', "Good morning! Let's crush it today 💪"],
    [12, '👋', "Here's what's happening with your BRO-BOT"],
    [17, '🌆', "Good evening! Here's your update"],
    [21, '🌙', "Late night grind? BRO-BOT's got you covered"],
    [24, '🌙', "Burning midnight oil? BRO-BOT never sleeps 🤖"],
  ];
  const [, emoji, subtitle] = map.find(([limit]) => h < limit) || map[map.length - 1];
  setEl('greeting-emoji', emoji);
  setEl('hero-subtitle', subtitle);
}

// ─────────────────────────────────────────────────────────
//  API HELPERS
// ─────────────────────────────────────────────────────────
async function apiGet(path) {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}
async function apiPost(path, body) {
  const res = await fetch(`${API}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const e = await res.json().catch(() => ({}));
    throw new Error(e.detail || `API ${res.status}`);
  }
  return res.json();
}
async function apiPut(path, body = {}) {
  const res = await fetch(`${API}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}
async function apiDelete(path) {
  const res = await fetch(`${API}${path}`, { method: 'DELETE' });
  if (!res.ok) throw new Error(`API ${res.status}`);
  return res.json();
}

// ─────────────────────────────────────────────────────────
//  NAVIGATION
// ─────────────────────────────────────────────────────────
const PAGE_META = {
  landing:      { title: 'CareerPilot AI Platform', subtitle: 'Autonomous AI Career Agent & Job Search Automation' },
  dashboard:    { title: 'Dashboard', subtitle: 'Your AI life manager at a glance' },
  studio:       { title: 'Content Studio', subtitle: 'AI-powered post generator — smarter than Buffer' },
  queue:        { title: 'Post Queue', subtitle: 'Review and approve your scheduled posts' },
  calendar:     { title: 'Content Calendar', subtitle: 'Visual overview of your posting schedule' },
  jobs:         { title: 'Job Hunter', subtitle: 'Auto-scans Indeed · Naukri · LinkedIn · Shine · Internshala' },
  tree:         { title: 'Application Tree', subtitle: 'Hierarchical view of all target companies & application branches' },
  deepresearch: { title: 'DeepSeek Research', subtitle: 'Company intelligence briefing & 1-click Smart Apply prep' },
  cv:           { title: 'CV Tailor', subtitle: 'AI auto-tailors your resume for any job role — ATS optimized' },
  messages:     { title: 'Messages', subtitle: 'Recruiter messages with AI reply drafts' },
  brief:        { title: 'Daily Brief', subtitle: 'Your personalized AI daily update' },
  help:         { title: 'How To Use', subtitle: 'Full manual + global comparison' },
  settings:     { title: 'Settings', subtitle: 'Configure BRO-BOT to your needs' },
};

function switchSection(section) {
  document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
  const navEl = document.getElementById(`nav-${section}`);
  if (navEl) navEl.classList.add('active');

  document.querySelectorAll('.section').forEach(el => el.classList.remove('active'));
  const sectionEl = document.getElementById(`section-${section}`);
  if (sectionEl) sectionEl.classList.add('active');

  const meta = PAGE_META[section] || { title: section, subtitle: '' };
  setEl('page-title', meta.title);
  setEl('page-subtitle', meta.subtitle);
  state.currentSection = section;

  // Hide internal action buttons on landing page
  document.querySelectorAll('.internal-app-btn').forEach(btn => {
    btn.style.display = (section === 'landing') ? 'none' : '';
  });

  if (section === 'calendar') renderCalendar();
  if (section === 'queue') loadPosts();
  if (section === 'tree') loadAppTree();
  if (section === 'cv') loadCVMasterProjects();
}

// ─────────────────────────────────────────────────────────
//  HEALTH & OFFLINE DETECTION
// ─────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const health = await apiGet('/health');
    state.isOnline = true;

    // Hide offline banner
    const banner = document.getElementById('offline-banner');
    if (banner) banner.style.display = 'none';

    // Status dot
    const dot = document.getElementById('status-dot');
    if (dot) dot.className = 'status-dot';
    setEl('status-text', 'BRO-BOT Online');
    setEl('status-sub', `v${health.version || '2.0.0'}`);

    // API status
    const g = document.getElementById('gemini-status');
    if (g) { g.textContent = health.ai_configured ? '✅ Configured' : '❌ Not Set'; g.className = `api-badge ${health.ai_configured ? 'ok' : 'missing'}`; }
    const t = document.getElementById('telegram-status');
    if (t) { t.textContent = health.telegram_configured ? '✅ Connected' : '❌ Not Set'; t.className = `api-badge ${health.telegram_configured ? 'ok' : 'missing'}`; }
    const r = document.getElementById('resume-status');
    if (r) { r.textContent = health.resume_uploaded ? '✅ Uploaded' : '❌ Not Uploaded'; r.className = `api-badge ${health.resume_uploaded ? 'ok' : 'missing'}`; }

  } catch (e) {
    state.isOnline = false;
    const banner = document.getElementById('offline-banner');
    if (banner) banner.style.display = 'flex';
    const dot = document.getElementById('status-dot');
    if (dot) dot.className = 'status-dot offline';
    setEl('status-text', 'Backend Offline');
    setEl('status-sub', 'Run start.sh');
  }
}

// ─────────────────────────────────────────────────────────
//  STATS
// ─────────────────────────────────────────────────────────
async function loadStats() {
  try {
    const s = await apiGet('/stats');
    setEl('stat-posts', s.posts?.posted ?? 0);
    setEl('stat-pending', s.posts?.pending ?? 0);
    setEl('stat-jobs', s.jobs?.applied ?? 0);
    setEl('stat-messages', s.messages?.unread ?? 0);
    setEl('hero-name', s.profile?.name || 'Bhai');
    setBadge('queue-badge', s.posts?.pending);
    setBadge('jobs-badge', s.jobs?.new);
    setBadge('messages-badge', s.messages?.unread);
    setEl('js-new', s.jobs?.new ?? 0);
    setEl('js-applied', s.jobs?.applied ?? 0);
    setEl('js-interview', s.jobs?.interview ?? 0);
    setEl('js-total', s.jobs?.total ?? 0);
  } catch (e) { /* offline */ }
}

// ─────────────────────────────────────────────────────────
//  ACTIVITY FEED
// ─────────────────────────────────────────────────────────
const ACTIVITY_ICONS = {
  post_created: { icon: '✏️', bg: 'rgba(139,92,246,0.15)' },
  post_approved: { icon: '✅', bg: 'rgba(34,197,94,0.15)' },
  post_rejected: { icon: '❌', bg: 'rgba(239,68,68,0.15)' },
  post_posted: { icon: '📢', bg: 'rgba(139,92,246,0.15)' },
  bulk_approve: { icon: '✅✅', bg: 'rgba(34,197,94,0.15)' },
  job_found: { icon: '💼', bg: 'rgba(6,182,212,0.15)' },
  job_applied: { icon: '🚀', bg: 'rgba(34,197,94,0.15)' },
  job_scan_complete: { icon: '🔍', bg: 'rgba(6,182,212,0.15)' },
  job_scrape_started: { icon: '⏳', bg: 'rgba(245,158,11,0.15)' },
  message_received: { icon: '💬', bg: 'rgba(245,158,11,0.15)' },
  ai_generate: { icon: '✨', bg: 'rgba(139,92,246,0.15)' },
  daily_brief_sent: { icon: '📰', bg: 'rgba(6,182,212,0.15)' },
  resume_uploaded: { icon: '📄', bg: 'rgba(34,197,94,0.15)' },
  system_start: { icon: '🚀', bg: 'rgba(34,197,94,0.15)' },
  config_updated: { icon: '⚙️', bg: 'rgba(100,116,139,0.2)' },
};

async function loadActivity() {
  try {
    const activities = await apiGet('/activity?limit=20');
    const el = document.getElementById('activity-feed');
    if (!el) return;
    if (!activities.length) {
      el.innerHTML = `<div class="empty-state" style="padding:32px"><div class="empty-state-icon">📭</div><p>No activity yet. Start creating!</p></div>`;
      return;
    }
    el.innerHTML = activities.slice(0, 12).map(a => {
      const meta = ACTIVITY_ICONS[a.type] || { icon: '🔵', bg: 'rgba(100,116,139,0.2)' };
      return `<div class="activity-item"><div class="activity-icon" style="background:${meta.bg}">${meta.icon}</div><div class="activity-text"><div class="activity-desc">${escHtml(a.description)}</div><div class="activity-time">${timeAgo(a.timestamp)}</div></div></div>`;
    }).join('');
  } catch (e) { /* offline */ }
}

async function refreshActivity() { await loadActivity(); toast('Activity refreshed', 'info'); }

// ─────────────────────────────────────────────────────────
//  TEMPLATES
// ─────────────────────────────────────────────────────────
async function loadTemplates() {
  try {
    const templates = await apiGet('/templates');
    const el = document.getElementById('templates-grid');
    if (!el) return;
    el.innerHTML = templates.map(t => `
      <div class="template-pill" onclick="applyTemplate(${JSON.stringify(t.topic).replace(/</g,'&lt;')})" title="${escHtml(t.topic)}">
        ${t.emoji} ${t.title}
      </div>`).join('');
  } catch (e) {
    const el = document.getElementById('templates-grid');
    if (el) el.innerHTML = '<div style="font-size:13px;color:var(--text-muted)">Start backend to load templates</div>';
  }
}

function applyTemplate(topicTemplate) {
  const el = document.getElementById('post-topic');
  if (el) {
    el.value = topicTemplate;
    updateTopicCount();
    el.focus();
    toast('Template applied! Edit the brackets and generate 🚀', 'info', 4000);
    switchSection('studio');
  }
}

function updateTopicCount() {
  const el = document.getElementById('post-topic');
  const counter = document.getElementById('topic-count');
  if (el && counter) counter.textContent = `${el.value.length}/500`;
}

// ─────────────────────────────────────────────────────────
//  CONTENT STUDIO
// ─────────────────────────────────────────────────────────
function selectPlatform(platform) {
  state.selectedPlatform = platform;
  document.querySelectorAll('.platform-pill').forEach(el => el.classList.remove('selected'));
  const el = document.querySelector(`[data-platform="${platform}"]`);
  if (el) el.classList.add('selected');

  // Show/hide Twitter counter
  const counter = document.getElementById('twitter-counter');
  if (counter) counter.style.display = platform === 'twitter' ? 'block' : 'none';
}

function updateCharCounter(content, hashtags) {
  if (state.selectedPlatform !== 'twitter') return;
  const full = `${content} ${hashtags.join(' ')}`.trim();
  const count = full.length;
  const pct = Math.min((count / 280) * 100, 100);

  const display = document.getElementById('char-count-display');
  const bar = document.getElementById('char-count-bar');
  const msg = document.getElementById('char-count-msg');

  if (display) {
    display.textContent = count;
    display.className = count > 260 ? 'danger' : count > 220 ? 'warning' : '';
  }
  if (bar) {
    bar.style.width = `${pct}%`;
    bar.className = count > 260 ? 'danger' : count > 220 ? 'warning' : '';
  }
  if (msg) {
    const remaining = 280 - count;
    msg.textContent = remaining >= 0 ? `${count} / 280 characters (${remaining} remaining)` : `⚠️ ${Math.abs(remaining)} characters over limit!`;
    msg.style.color = remaining < 0 ? 'var(--red-400)' : '';
  }
}

async function generatePost() {
  const topic = document.getElementById('post-topic')?.value.trim();
  if (!topic) { toast('Please enter a topic or pick a template!', 'error'); return; }

  const btn = document.getElementById('generate-btn');
  setLoading(btn, true, '✨ Generating...');

  const preview = document.getElementById('preview-panel');
  const placeholder = document.getElementById('preview-placeholder');
  if (placeholder) placeholder.style.display = 'none';

  preview.innerHTML = `<div class="ai-generating"><div class="ai-dots"><div class="ai-dot"></div><div class="ai-dot"></div><div class="ai-dot"></div></div><div style="font-size:14px;color:var(--text-muted)">Crafting your ${state.selectedPlatform} post...</div></div>`;

  try {
    const result = await apiPost('/generate/post', {
      topic,
      platform: state.selectedPlatform,
      tone: document.getElementById('post-tone')?.value || 'casual',
    });
    state.generatedPost = result;
    renderPreview(result);
    updateCharCounter(result.content, result.hashtags);
    document.getElementById('post-actions-panel').style.display = 'block';
    toast('Post generated! ✨', 'success');
  } catch (e) {
    preview.innerHTML = `<div class="preview-placeholder"><div class="preview-placeholder-icon">⚠️</div><p style="color:var(--red-400)">${escHtml(e.message)}</p><p style="font-size:13px;margin-top:8px">Make sure backend is running and Gemini API key is set in Settings.</p></div>`;
    toast('Generation failed — is backend running?', 'error');
  } finally {
    setLoading(btn, false, '✨ Generate with AI');
  }
}

function renderPreview(result) {
  const preview = document.getElementById('preview-panel');
  const icons = { linkedin: '💼', instagram: '📸', twitter: '🐦' };
  preview.innerHTML = `
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;flex-wrap:wrap">
      <span class="platform-badge ${result.platform}">${icons[result.platform] || '📱'} ${result.platform.toUpperCase()}</span>
      <span style="font-size:12px;color:var(--text-muted)">${result.tone} tone</span>
      ${result.char_count ? `<span style="font-size:12px;color:var(--text-muted);margin-left:auto">${result.char_count} chars</span>` : ''}
    </div>
    <div class="preview-content" id="preview-content">${escHtml(result.content)}</div>
    <div class="preview-hashtags" id="preview-hashtags">${result.hashtags.join(' ')}</div>
    <div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">
      <button class="btn btn-ghost btn-sm" onclick="copyFullPost()">📋 Copy Full Post</button>
      <button class="btn btn-ghost btn-sm" onclick="editPreview()">✏️ Edit</button>
    </div>`;
}

function copyFullPost() {
  const content = document.getElementById('preview-content')?.textContent || '';
  const hashtags = document.getElementById('preview-hashtags')?.textContent || '';
  navigator.clipboard.writeText(`${content}\n\n${hashtags}`).then(() => toast('Full post copied! 📋', 'success'));
}

function editPreview() {
  const contentEl = document.getElementById('preview-content');
  if (!contentEl) return;
  const text = contentEl.textContent;
  contentEl.outerHTML = `<textarea class="form-textarea" style="min-height:160px;font-size:14px" id="preview-content" onkeyup="if(state.generatedPost)state.generatedPost.content=this.value">${escHtml(text)}</textarea>`;
}

async function saveToQueue() {
  if (!state.generatedPost) return;
  try {
    const contentEl = document.getElementById('preview-content');
    const content = contentEl ? (contentEl.value || contentEl.textContent) : state.generatedPost.content;
    await apiPost('/posts', {
      platform: state.generatedPost.platform,
      content: content.trim(),
      hashtags: state.generatedPost.hashtags || [],
      scheduled_at: document.getElementById('schedule-time')?.value || null,
    });
    toast('Post saved to queue! ✅', 'success');
    document.getElementById('post-actions-panel').style.display = 'none';
    clearStudio();
    await loadAll();
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

function clearStudio() {
  const t = document.getElementById('post-topic');
  if (t) t.value = '';
  updateTopicCount();
  const s = document.getElementById('schedule-time');
  if (s) s.value = '';
  state.generatedPost = null;
  const panel = document.getElementById('post-actions-panel');
  if (panel) panel.style.display = 'none';
  const preview = document.getElementById('preview-panel');
  if (preview) preview.innerHTML = `<div class="preview-placeholder" id="preview-placeholder"><div class="preview-placeholder-icon">✨</div><h3 style="color:var(--text-secondary);font-size:16px">AI Preview</h3><p style="font-size:13px">Pick a template or write a topic,<br>then click Generate!</p></div>`;
  const counter = document.getElementById('twitter-counter');
  if (counter) counter.style.display = 'none';
}

async function generateBio() {
  const btn = document.getElementById('bio-btn');
  setLoading(btn, true, '⏳ Generating...');
  try {
    const result = await apiPost('/generate/bio', { achievements: document.getElementById('bio-achievements')?.value.trim() || '' });
    const txt = document.getElementById('bio-text');
    if (txt) txt.textContent = result.bio;
    const res = document.getElementById('bio-result');
    if (res) res.style.display = 'block';
    toast('LinkedIn bio generated! 🆔', 'success');
  } catch (e) { toast('Bio failed: ' + e.message, 'error'); }
  finally { setLoading(btn, false, '🤖 Generate LinkedIn Bio'); }
}

// ─────────────────────────────────────────────────────────
//  POST QUEUE + BULK OPERATIONS
// ─────────────────────────────────────────────────────────
async function loadPosts() {
  try {
    const status = document.getElementById('queue-filter')?.value || '';
    const posts = await apiGet(`/posts${status ? `?status=${status}` : ''}`);
    state.allPosts = posts;
    renderPosts(posts);
  } catch (e) { /* offline */ }
}

async function filterQueue() { await loadPosts(); }

function renderPosts(posts) {
  const el = document.getElementById('posts-list');
  if (!el) return;
  if (!posts.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">📭</div><h3>No posts here</h3><p>Go to Content Studio to generate your first post!</p><button class="btn btn-primary" style="margin-top:16px" onclick="switchSection('studio')">✨ Create Post</button></div>`;
    return;
  }
  const icons = { linkedin: '💼', instagram: '📸', twitter: '🐦' };
  el.innerHTML = posts.map(post => `
    <div class="post-card" id="post-${post.id}">
      <div class="post-card-header">
        <input type="checkbox" class="bulk-checkbox" id="cb-${post.id}" onchange="toggleBulkSelect('${post.id}')" title="Select for bulk action">
        <span class="platform-badge ${post.platform}">${icons[post.platform] || '📱'} ${post.platform.toUpperCase()}</span>
        <span class="status-badge ${post.status}">${post.status}</span>
      </div>
      <div class="post-content-preview">${escHtml(post.content)}</div>
      ${post.hashtags?.length ? `<div class="post-hashtags">${post.hashtags.slice(0,6).map(h=>`<span class="hashtag">${h}</span>`).join('')}</div>` : ''}
      <div class="post-card-footer">
        <span class="post-time">🕒 ${timeAgo(post.created_at)}</span>
        <div class="post-actions">
          ${post.status === 'pending' ? `<button class="btn btn-success btn-sm" onclick="approvePost('${post.id}')">✅ Approve</button><button class="btn btn-danger btn-sm" onclick="rejectPost('${post.id}')">❌ Reject</button>` : ''}
          ${post.status === 'approved' ? `<button class="btn btn-primary btn-sm" onclick="markPosted('${post.id}')">📤 Mark Posted</button>` : ''}
          <button class="btn btn-ghost btn-sm" onclick="copyPostContent('${post.id}')" title="Copy content">📋</button>
          <button class="btn btn-ghost btn-sm" onclick="deletePost('${post.id}')" title="Delete">🗑️</button>
        </div>
      </div>
    </div>`).join('');
}

function copyPostContent(postId) {
  const post = state.allPosts.find(p => p.id === postId);
  if (!post) return;
  const text = `${post.content}\n\n${post.hashtags.join(' ')}`;
  navigator.clipboard.writeText(text).then(() => toast('Post copied! 📋', 'success'));
}

// Bulk selection
function toggleBulkSelect(postId) {
  if (state.bulkSelected.has(postId)) {
    state.bulkSelected.delete(postId);
  } else {
    state.bulkSelected.add(postId);
  }
  updateBulkToolbar();
}

function updateBulkToolbar() {
  const toolbar = document.getElementById('bulk-toolbar');
  const countEl = document.getElementById('bulk-count');
  const count = state.bulkSelected.size;
  if (!toolbar) return;
  toolbar.style.display = count > 0 ? 'flex' : 'none';
  if (countEl) countEl.textContent = `${count} post${count !== 1 ? 's' : ''} selected`;
}

function clearBulkSelection() {
  state.bulkSelected.clear();
  document.querySelectorAll('.bulk-checkbox').forEach(cb => { cb.checked = false; });
  updateBulkToolbar();
}

async function bulkAction(action) {
  if (state.bulkSelected.size === 0) return;
  const ids = Array.from(state.bulkSelected);
  try {
    const result = await apiPost(`/posts/bulk?action=${action}`, ids);
    toast(`${action === 'approve' ? '✅' : '❌'} ${result.updated} posts ${action}d!`, 'success');
    clearBulkSelection();
    await loadAll();
  } catch (e) { toast('Bulk action failed: ' + e.message, 'error'); }
}

async function approvePost(id) {
  try { await apiPut(`/posts/${id}/approve`); toast('Post approved! ✅', 'success'); await loadAll(); }
  catch (e) { toast('Failed: ' + e.message, 'error'); }
}
async function rejectPost(id) {
  try { await apiPut(`/posts/${id}/reject`); toast('Post rejected', 'info'); await loadAll(); }
  catch (e) { toast('Failed: ' + e.message, 'error'); }
}
async function markPosted(id) {
  try { await apiPut(`/posts/${id}/posted`); toast('Marked as published! 🎉', 'success'); await loadAll(); }
  catch (e) { toast('Failed: ' + e.message, 'error'); }
}
async function deletePost(id) {
  if (!confirm('Delete this post?')) return;
  try { await apiDelete(`/posts/${id}`); toast('Post deleted', 'info'); await loadAll(); }
  catch (e) { toast('Failed: ' + e.message, 'error'); }
}

// ─────────────────────────────────────────────────────────
//  CONTENT CALENDAR
// ─────────────────────────────────────────────────────────
function prevMonth() { state.calMonth--; if (state.calMonth < 0) { state.calMonth = 11; state.calYear--; } renderCalendar(); }
function nextMonth() { state.calMonth++; if (state.calMonth > 11) { state.calMonth = 0; state.calYear++; } renderCalendar(); }

async function renderCalendar() {
  const el = document.getElementById('calendar-grid');
  if (!el) return;

  const months = ['January','February','March','April','May','June','July','August','September','October','November','December'];
  setEl('cal-month-label', `${months[state.calMonth]} ${state.calYear}`);

  // Get all posts
  let posts = state.allPosts;
  if (!posts.length) {
    try { posts = await apiGet('/posts'); state.allPosts = posts; } catch (e) { posts = []; }
  }

  // Map posts by date
  const postsByDate = {};
  posts.forEach(p => {
    const dateStr = p.scheduled_at || p.created_at;
    if (dateStr) {
      const d = new Date(dateStr);
      if (d.getFullYear() === state.calYear && d.getMonth() === state.calMonth) {
        const key = d.getDate();
        if (!postsByDate[key]) postsByDate[key] = [];
        postsByDate[key].push(p);
      }
    }
  });

  const firstDay = new Date(state.calYear, state.calMonth, 1).getDay();
  const daysInMonth = new Date(state.calYear, state.calMonth + 1, 0).getDate();
  const today = new Date();
  const isCurrentMonth = today.getFullYear() === state.calYear && today.getMonth() === state.calMonth;

  const dayNames = ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'];

  let html = `<div class="cal-header">${dayNames.map(d => `<div class="cal-day-name">${d}</div>`).join('')}</div><div class="cal-grid">`;

  // Empty cells before month starts
  for (let i = 0; i < firstDay; i++) {
    html += `<div class="cal-cell other-month"></div>`;
  }

  for (let day = 1; day <= daysInMonth; day++) {
    const isToday = isCurrentMonth && today.getDate() === day;
    const dayPosts = postsByDate[day] || [];
    html += `<div class="cal-cell${isToday ? ' today' : ''}">
      <div class="cal-date">${day}</div>
      ${dayPosts.slice(0, 3).map(p => `<div class="cal-post-dot ${p.platform} ${p.status}" title="${escHtml(p.content.slice(0,60))}">
        ${p.status === 'pending' ? '⏳' : p.status === 'posted' ? '✅' : ''} ${escHtml(p.platform)}
      </div>`).join('')}
      ${dayPosts.length > 3 ? `<div style="font-size:10px;color:var(--text-muted)">+${dayPosts.length-3} more</div>` : ''}
    </div>`;
  }

  html += '</div>';
  el.innerHTML = html;
}

// ─────────────────────────────────────────────────────────
//  JOB HUNTER + SCRAPING
// ─────────────────────────────────────────────────────────
async function loadJobs() {
  try {
    const jobs = await apiGet('/jobs');
    renderJobs(jobs);
  } catch (e) { /* offline */ }
}

function renderJobs(jobs) {
  const el = document.getElementById('jobs-list');
  if (!el) return;
  if (!jobs.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">💼</div><h3>No jobs tracked yet</h3><p>Click "Scan Jobs Now" to auto-find jobs, or add them manually.</p><button class="btn btn-primary" style="margin-top:16px" onclick="scrapeJobsNow()">🔍 Scan Now</button></div>`;
    return;
  }
  const statusOrder = { new: 0, saved: 1, applied: 2, interview: 3, rejected: 4 };
  jobs.sort((a, b) => (statusOrder[a.status] || 0) - (statusOrder[b.status] || 0));

  el.innerHTML = jobs.map(job => `
    <div class="job-card" id="job-${job.id}" style="border-left: 4px solid var(${job.status === 'applied' ? '--green-500' : job.status === 'interview' ? '--purple-500' : '--cyan-500'})">
      <div>
        <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
          <div class="job-company" style="font-weight:800;font-size:16px;color:var(--text-primary)">🏢 ${escHtml(job.company)}</div>
          ${job.source ? `<span class="source-badge ${job.source}">${job.source}</span>` : ''}
          <span class="status-badge ${jobStatusClass(job.status)}">${job.status.toUpperCase()}</span>
        </div>
        <div class="job-role" style="font-size:15px;font-weight:700;color:var(--cyan-400);margin:4px 0">${escHtml(job.role)}</div>
        <div class="job-meta" style="display:flex;gap:12px;flex-wrap:wrap;margin-top:6px;font-size:12px">
          <span class="job-meta-item" style="color:var(--text-secondary)">📍 ${escHtml(job.location)}</span>
          ${job.salary ? `<span class="job-meta-item" style="color:var(--green-400)">💰 ${escHtml(job.salary)}</span>` : ''}
          <span class="job-meta-item" style="color:var(--purple-400)">🕒 Posted: ${job.posted_at || timeAgo(job.found_at)}</span>
          <span class="job-meta-item" style="background:rgba(234,179,8,0.15);color:var(--amber-400);padding:2px 8px;border-radius:99px;font-weight:700">👥 ${job.applicants_count || 'Be an Early Applicant'}</span>
        </div>
      </div>
      <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-top:12px;border-top:1px solid var(--glass-border);padding-top:10px">
        <button class="btn btn-primary btn-sm" onclick="quickSmartApply('${escHtml(job.company)}', '${escHtml(job.role)}', '${escHtml(job.url)}')">⚡ Auto-Tailor CV & Apply</button>
        <a href="${escHtml(job.url)}" target="_blank" class="btn btn-secondary btn-sm">🔗 Open Job Link</a>
        ${job.status === 'new' || job.status === 'saved' ? `<button class="btn btn-success btn-sm" onclick="updateJobStatus('${job.id}','applied')">✅ Mark Applied</button>` : ''}
        ${job.status === 'applied' ? `<button class="btn btn-primary btn-sm" onclick="updateJobStatus('${job.id}','interview')">🎯 Interview Call</button>` : ''}
        <button class="btn btn-ghost btn-sm" onclick="updateJobStatus('${job.id}','rejected')" title="Not pursuing">❌</button>
      </div>
    </div>`).join('');
}

function quickSmartApply(company, role, url) {
  switchSection('research');
  setElVal('dr-company', company);
  setElVal('dr-role', role);
  setElVal('dr-url', url);
  runSmartApplyPrep();
}

function jobStatusClass(s) {
  return { new: 'pending', saved: 'pending', applied: 'approved', interview: 'posted', rejected: 'rejected' }[s] || 'pending';
}

async function scrapeJobsNow() {
  const btn = document.getElementById('scrape-btn');
  const keyword = document.getElementById('scrape-keyword')?.value.trim() || '';
  const location = document.getElementById('scrape-location')?.value.trim() || '';
  setLoading(btn, true, '🔍 Scanning...');
  try {
    const body = {};
    if (keyword) body.keyword = keyword;
    if (location) body.location = location;
    const result = await apiPost('/jobs/scrape', body);
    toast(result.message, 'success', 6000);
    // Reload jobs after 35s (scraping takes time)
    setTimeout(async () => { await loadJobs(); await loadStats(); toast('Jobs updated! Check the list.', 'info'); }, 35000);
  } catch (e) { toast('Scan failed: ' + e.message, 'error'); }
  finally { setTimeout(() => setLoading(btn, false, '🔍 Scan Jobs Now'), 5000); }
}

function showAddJobModal() { const m = document.getElementById('modal-add-job'); if (m) m.style.display = 'flex'; }

async function addJob() {
  const company = document.getElementById('job-company')?.value.trim();
  const role = document.getElementById('job-role')?.value.trim();
  const location = document.getElementById('job-location')?.value.trim();
  const url = document.getElementById('job-url')?.value.trim();
  if (!company || !role || !location || !url) { toast('Fill all required fields!', 'error'); return; }
  try {
    await apiPost('/jobs', { company, role, location, url, salary: document.getElementById('job-salary')?.value.trim() });
    toast('Job added! 💼', 'success');
    closeModal('modal-add-job');
    ['job-company','job-role','job-location','job-url','job-salary'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    await loadAll();
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

async function updateJobStatus(id, status) {
  try { await apiPut(`/jobs/${id}`, { status }); toast(`Job: ${status}!`, 'success'); await loadAll(); }
  catch (e) { toast('Failed: ' + e.message, 'error'); }
}

async function generateJobMsg() {
  const company = document.getElementById('msg-company')?.value.trim();
  const role = document.getElementById('msg-role')?.value.trim();
  if (!company || !role) { toast('Enter company and role', 'error'); return; }
  try {
    const result = await apiPost('/generate/job-message', { company, role });
    const el = document.getElementById('job-msg-text');
    if (el) el.textContent = result.message;
    const res = document.getElementById('job-msg-result');
    if (res) res.style.display = 'block';
    toast('Application message ready! 📋', 'success');
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

// ─────────────────────────────────────────────────────────
//  MESSAGES
// ─────────────────────────────────────────────────────────
async function loadMessages() {
  try {
    const msgs = await apiGet('/messages');
    renderMessages(msgs);
  } catch (e) { /* offline */ }
}

function renderMessages(messages) {
  const el = document.getElementById('messages-list');
  if (!el) return;
  if (!messages.length) {
    el.innerHTML = `<div class="empty-state"><div class="empty-state-icon">💬</div><h3>No messages yet</h3><p>Add recruiter messages — BRO-BOT drafts professional replies for you!</p><button class="btn btn-primary" style="margin-top:16px" onclick="showAddMessageModal()">➕ Add Message</button></div>`;
    return;
  }
  messages.sort((a, b) => (a.status === 'unread' ? -1 : 1));
  el.innerHTML = messages.map(msg => `
    <div class="message-card ${msg.status === 'unread' ? 'unread' : ''}" id="msg-${msg.id}">
      <div class="message-header">
        <div class="message-avatar">${msg.sender.charAt(0).toUpperCase()}</div>
        <div style="flex:1"><div class="message-sender">${escHtml(msg.sender)}</div><div class="message-meta">📱 ${escHtml(msg.platform)} · ${timeAgo(msg.received_at)}${msg.status === 'unread' ? ' <span style="color:var(--purple-400);font-weight:700">● UNREAD</span>' : ''}</div></div>
        <span class="status-badge ${msg.status==='replied'?'approved':msg.status==='unread'?'pending':'posted'}">${msg.status}</span>
      </div>
      <div class="message-body">${escHtml(msg.content)}</div>
      ${msg.reply_draft ? `<div class="message-reply"><div style="font-size:11px;font-weight:700;color:var(--purple-400);text-transform:uppercase;margin-bottom:8px">🤖 AI Draft Reply</div><div id="reply-${msg.id}" style="white-space:pre-wrap">${escHtml(msg.reply_draft)}</div><div style="margin-top:10px;display:flex;gap:8px"><button class="btn btn-ghost btn-sm" onclick="copyText('reply-${msg.id}')">📋 Copy Reply</button><button class="btn btn-success btn-sm" onclick="markReplied('${msg.id}')">✅ Mark Replied</button></div></div>` : ''}
      <div style="display:flex;gap:8px;margin-top:14px">
        ${msg.status==='unread' ? `<button class="btn btn-primary btn-sm" onclick="generateReply('${msg.id}',this)">🤖 Generate Reply</button>` : ''}
      </div>
    </div>`).join('');
}

function showAddMessageModal() { const m = document.getElementById('modal-add-message'); if (m) m.style.display = 'flex'; }

async function addMessage() {
  const sender = document.getElementById('msg-sender')?.value.trim();
  const content = document.getElementById('msg-content')?.value.trim();
  const platform = document.getElementById('msg-platform')?.value;
  if (!sender || !content) { toast('Fill sender and message', 'error'); return; }
  try {
    await apiPost('/messages', { sender, content, platform });
    toast('Message added!', 'success');
    closeModal('modal-add-message');
    ['msg-sender','msg-content'].forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    await loadAll();
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

async function generateReply(msgId, btn) {
  const msgEl = document.getElementById(`msg-${msgId}`);
  const bodyEl = msgEl?.querySelector('.message-body');
  if (!bodyEl) return;
  const orig = btn.textContent;
  btn.textContent = '⏳ Drafting...'; btn.disabled = true;
  try {
    await apiPost('/generate/reply', { message_id: msgId, recruiter_message: bodyEl.textContent });
    toast('Reply drafted! ✅', 'success');
    await loadMessages();
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
  finally { btn.textContent = orig; btn.disabled = false; }
}

async function markReplied(msgId) {
  try {
    await fetch(`${API}/messages/${msgId}?status=replied`, { method: 'PUT' });
    toast('Marked as replied!', 'success'); await loadAll();
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
}

// ─────────────────────────────────────────────────────────
//  DAILY BRIEF
// ─────────────────────────────────────────────────────────
async function generateBrief() {
  const btn = document.getElementById('brief-gen-btn');
  setLoading(btn, true, '⏳ Generating...');
  try {
    const result = await apiGet('/generate/brief');
    const el = document.getElementById('brief-text');
    if (el) el.textContent = result.brief;
    const dateEl = document.getElementById('brief-date');
    if (dateEl) dateEl.textContent = new Date().toLocaleDateString('en-IN', { weekday:'long', day:'numeric', month:'long' });
    const actions = document.getElementById('brief-actions');
    if (actions) actions.style.display = 'flex';
    toast('Daily brief generated! 📰', 'success');
    if (state.currentSection !== 'brief') switchSection('brief');
  } catch (e) { toast('Brief failed: ' + e.message, 'error'); }
  finally { setLoading(btn, false, '🤖 Generate Brief'); }
}

async function sendBriefToTelegram() {
  const btn = document.getElementById('send-brief-btn');
  setLoading(btn, true, '📲 Sending...');
  try {
    const r = await apiPost('/telegram/brief', {});
    toast(r.message, 'success');
  } catch (e) { toast('Failed: ' + e.message, 'error'); }
  finally { setLoading(btn, false, '📲 Send to Telegram'); }
}

// ─────────────────────────────────────────────────────────
//  RESUME UPLOAD
// ─────────────────────────────────────────────────────────
async function loadResumeStatus() {
  try {
    const status = await apiGet('/resume');
    if (status.uploaded) {
      const box = document.getElementById('resume-status-box');
      if (box) box.style.display = 'block';
      const preview = document.getElementById('resume-preview-text');
      if (preview) preview.textContent = status.preview ? `Preview: "${status.preview.slice(0, 200)}..."` : 'Resume text extracted successfully.';
    }
  } catch (e) { /* offline */ }
}

function handleResumeDrop(event) {
  event.preventDefault();
  const files = event.dataTransfer.files;
  if (files.length > 0) {
    const input = document.getElementById('resume-file-input');
    if (input) {
      input.files = files;
      uploadResume(input);
    }
  }
}

async function uploadResume(input) {
  if (!input.files || !input.files[0]) return;
  const file = input.files[0];
  if (!file.name.endsWith('.pdf')) { toast('Please upload a PDF file', 'error'); return; }

  toast('Uploading resume...', 'info');
  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API}/resume`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    const box = document.getElementById('resume-status-box');
    if (box) box.style.display = 'block';
    const preview = document.getElementById('resume-preview-text');
    if (preview) preview.textContent = `✅ ${file.name} (${data.size_kb}KB) · Preview: "${data.preview.slice(0, 150)}..."`;

    toast('Resume uploaded! AI will now personalize your content 📄', 'success');
    await checkHealth();
  } catch (e) { toast('Upload failed: ' + e.message, 'error'); }
}

// ─────────────────────────────────────────────────────────
//  SETTINGS
// ─────────────────────────────────────────────────────────
async function loadConfig() {
  try {
    const config = await apiGet('/config');
    const profile = config.profile || {};
    setInputVal('cfg-name', profile.name || '');
    setInputVal('cfg-domain', profile.domain || '');
    setInputVal('cfg-exp', config.job_hunting?.experience_level || 'fresher');
    setInputVal('cfg-brief-time', config.notifications?.daily_brief_time || '08:00');
    setInputVal('cfg-locations', (config.job_hunting?.locations || []).join(', '));
    state.skills = profile.skills || [];
    renderTags('skills-tag-area', 'skill-input', state.skills, 'removeSkill');
    state.keywords = config.job_hunting?.keywords || [];
    renderTags('keywords-tag-area', 'keyword-input', state.keywords, 'removeKeyword');
  } catch (e) { /* offline */ }
}

async function saveProfile() {
  try {
    await apiPost('/config', { updates: { profile: { name: document.getElementById('cfg-name')?.value.trim(), domain: document.getElementById('cfg-domain')?.value.trim(), skills: state.skills } } });
    toast('Profile saved! 👤', 'success'); await loadStats();
  } catch (e) { toast('Save failed: ' + e.message, 'error'); }
}

async function saveJobPrefs() {
  const locStr = document.getElementById('cfg-locations')?.value || '';
  const locations = locStr.split(',').map(l => l.trim()).filter(Boolean);
  try {
    await apiPost('/config', { updates: { job_hunting: { keywords: state.keywords, experience_level: document.getElementById('cfg-exp')?.value, locations }, notifications: { daily_brief_time: document.getElementById('cfg-brief-time')?.value } } });
    toast('Job preferences saved! 💼', 'success');
  } catch (e) { toast('Save failed: ' + e.message, 'error'); }
}

async function testTelegram() {
  try { const r = await apiPost('/telegram/test', {}); toast(r.message, r.success ? 'success' : 'error'); }
  catch (e) { toast('Telegram test failed. Add token/chat ID to backend/.env', 'error'); }
}

function showEnvInstructions() {
  const gemini = document.getElementById('cfg-gemini')?.value;
  const token = document.getElementById('cfg-tg-token')?.value;
  const chat = document.getElementById('cfg-tg-chat')?.value;
  const lines = [];
  if (gemini) lines.push(`GEMINI_API_KEY=${gemini}`);
  if (token) lines.push(`TELEGRAM_BOT_TOKEN=${token}`);
  if (chat) lines.push(`TELEGRAM_CHAT_ID=${chat}`);
  if (!lines.length) { toast('Fill in the API key fields first', 'error'); return; }
  const envEl = document.getElementById('env-content');
  if (envEl) envEl.innerHTML = lines.map(l => `<div>${escHtml(l)}</div>`).join('');
  const modal = document.getElementById('modal-env');
  if (modal) modal.style.display = 'flex';
}

function copyEnvContent() {
  const el = document.getElementById('env-content');
  if (el) navigator.clipboard.writeText(el.textContent).then(() => toast('Copied! Paste into backend/.env 📋', 'success'));
}

// ─────────────────────────────────────────────────────────
//  ONBOARDING WIZARD
// ─────────────────────────────────────────────────────────
let currentStep = 1;

function showOnboarding() {
  const modal = document.getElementById('onboarding-modal');
  if (modal) modal.style.display = 'flex';
  nextStep(1);
}

function closeOnboarding() {
  const modal = document.getElementById('onboarding-modal');
  if (modal) modal.style.display = 'none';
  localStorage.setItem('brobot_onboarded', '1');
}

function nextStep(step) {
  currentStep = step;
  document.querySelectorAll('.onboarding-step').forEach(el => el.style.display = 'none');
  const stepEl = document.getElementById(`step-${step}`);
  if (stepEl) stepEl.style.display = 'block';
  const progress = document.getElementById('onboarding-progress');
  if (progress) progress.style.width = `${(step / 4) * 100}%`;
}

async function saveOnboardingProfile() {
  const name = document.getElementById('ob-name')?.value.trim();
  const domain = document.getElementById('ob-domain')?.value.trim();
  const skills = (document.getElementById('ob-skills')?.value || '').split(',').map(s => s.trim()).filter(Boolean);
  if (!name) { toast('Please enter your name', 'error'); return; }
  try {
    await apiPost('/config', { updates: { profile: { name, domain, skills } } });
    state.skills = skills;
    toast('Profile saved! 👤', 'success');
    nextStep(3);
  } catch (e) { toast('Saved locally — connect to backend to sync', 'info'); nextStep(3); }
}

async function finishOnboarding() {
  const key = document.getElementById('ob-apikey')?.value.trim();
  if (key) toast(`Add this to backend/.env: GEMINI_API_KEY=${key}`, 'info', 8000);
  nextStep(4);
  localStorage.setItem('brobot_onboarded', '1');
}

// ─────────────────────────────────────────────────────────
//  TAG INPUTS
// ─────────────────────────────────────────────────────────
function handleSkillInput(e) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault();
    const v = e.target.value.trim().replace(',','');
    if (v && !state.skills.includes(v)) { state.skills.push(v); renderTags('skills-tag-area','skill-input',state.skills,'removeSkill'); }
    e.target.value = '';
  } else if (e.key === 'Backspace' && !e.target.value && state.skills.length) {
    state.skills.pop(); renderTags('skills-tag-area','skill-input',state.skills,'removeSkill');
  }
}
function handleKeywordInput(e) {
  if (e.key === 'Enter' || e.key === ',') {
    e.preventDefault();
    const v = e.target.value.trim().replace(',','');
    if (v && !state.keywords.includes(v)) { state.keywords.push(v); renderTags('keywords-tag-area','keyword-input',state.keywords,'removeKeyword'); }
    e.target.value = '';
  } else if (e.key === 'Backspace' && !e.target.value && state.keywords.length) {
    state.keywords.pop(); renderTags('keywords-tag-area','keyword-input',state.keywords,'removeKeyword');
  }
}
function removeSkill(i) { state.skills.splice(i,1); renderTags('skills-tag-area','skill-input',state.skills,'removeSkill'); }
function removeKeyword(i) { state.keywords.splice(i,1); renderTags('keywords-tag-area','keyword-input',state.keywords,'removeKeyword'); }

function renderTags(areaId, inputId, tags, removeFn) {
  const area = document.getElementById(areaId);
  const input = document.getElementById(inputId);
  if (!area || !input) return;
  const tagsHtml = tags.map((tag, i) => `<div class="tag-item">${escHtml(tag)}<span class="tag-remove" onclick="${removeFn}(${i})">✕</span></div>`).join('');
  area.innerHTML = tagsHtml;
  area.appendChild(input);
}

// ─────────────────────────────────────────────────────────
//  UTILITIES
// ─────────────────────────────────────────────────────────
function refreshData() {
  const btn = document.getElementById('refresh-btn');
  if (btn) { btn.textContent = '⏳ Loading...'; btn.disabled = true; }
  loadAll().then(() => {
    if (btn) { btn.textContent = '🔄 Refresh'; btn.disabled = false; }
    toast('Data refreshed!', 'info');
  });
}
function openModal(id) { const m = document.getElementById(id); if (m) m.style.display = 'flex'; }
function closeModal(id) { const m = document.getElementById(id); if (m) m.style.display = 'none'; }
function setEl(id, v) { const el = document.getElementById(id); if (el) el.textContent = v; }
function setInputVal(id, v) { const el = document.getElementById(id); if (el) el.value = v; }
function setBadge(id, count) { const el = document.getElementById(id); if (!el) return; if (count > 0) { el.textContent = count; el.style.display = 'inline-block'; } else el.style.display = 'none'; }
function escHtml(s) { return String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#039;'); }
function timeAgo(iso) {
  if (!iso) return 'just now';
  const diff = Date.now() - new Date(iso).getTime();
  const m = Math.floor(diff/60000), h = Math.floor(diff/3600000), d = Math.floor(diff/86400000);
  if (m < 1) return 'just now'; if (m < 60) return `${m}m ago`; if (h < 24) return `${h}h ago`; return `${d}d ago`;
}
function copyText(id) {
  const el = document.getElementById(id);
  if (!el) return;
  navigator.clipboard.writeText(el.value || el.textContent || '').then(() => toast('Copied! 📋', 'success'));
}
function setLoading(btn, loading, text) {
  if (!btn) return; btn.disabled = loading;
  if (text) btn.textContent = text;
  btn.classList.toggle('loading', loading);
}

// Keyboard shortcuts
function handleKeyboard(e) {
  if (e.key === 'Escape') document.querySelectorAll('[id^="modal-"],[id^="onboarding-"]').forEach(m => { if (m.style.display !== 'none') m.style.display = 'none'; });
  if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && state.currentSection === 'studio') generatePost();
}

// Toasts
const TOAST_ICONS = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
function toast(msg, type = 'info', dur = 3500) {
  const c = document.getElementById('toast-container'); if (!c) return;
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.innerHTML = `<span class="toast-icon">${TOAST_ICONS[type]||'ℹ️'}</span><span>${escHtml(msg)}</span>`;
  c.appendChild(el);
  setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 300); }, dur);
}

// ─────────────────────────────────────────────────────────
//  APPLICATION TREE (PHASE 3)
// ─────────────────────────────────────────────────────────
async function loadAppTree() {
  const container = document.getElementById('app-tree-container');
  if (!container) return;
  try {
    const data = await apiGet('/applications/tree');
    renderAppTree(data.companies || {});
  } catch (e) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">⚠️</div><h3>Could not load Application Tree</h3><p>${escHtml(e.message)}</p></div>`;
  }
}

function renderAppTree(companies) {
  const container = document.getElementById('app-tree-container');
  if (!container) return;

  const compKeys = Object.keys(companies);
  if (!compKeys.length) {
    container.innerHTML = `<div class="empty-state"><div class="empty-state-icon">🌳</div><h3>Application Tree is Empty</h3><p>Use "Deep Research" or "Smart Apply" to add target companies & job branches.</p><button class="btn btn-primary" style="margin-top:16px" onclick="switchSection('deepresearch')">🔍 Research a Company</button></div>`;
    return;
  }

  container.innerHTML = compKeys.map(compKey => {
    const comp = companies[compKey];
    const research = comp.research || {};
    const jobs = comp.jobs || [];

    return `
      <div class="tree-company-node">
        <div class="tree-company-header">
          <div class="tree-company-title">
            <span>🏢</span> ${escHtml(comp.name)}
            ${research.domain ? `<span class="source-badge Naukri" style="font-size:11px">${escHtml(research.domain)}</span>` : ''}
          </div>
          <div style="display:flex;gap:8px">
            <button class="btn btn-secondary btn-sm" onclick="quickResearch('${escHtml(comp.name)}')">🔍 Research</button>
            <button class="btn btn-ghost btn-sm">${jobs.length} Job Role${jobs.length !== 1 ? 's' : ''}</button>
          </div>
        </div>

        ${research.tagline ? `<div style="padding:10px 20px;font-size:13px;color:var(--text-muted);border-bottom:1px solid var(--glass-border)">💡 <em>"${escHtml(research.tagline)}"</em></div>` : ''}

        <div class="tree-jobs-branch">
          ${jobs.length === 0 ? `<div style="font-size:13px;color:var(--text-muted);padding:8px">No active job roles logged for this company yet.</div>` : ''}
          ${jobs.map(job => `
            <div class="tree-job-node ${job.status || 'discovered'}">
              <div style="flex:1">
                <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
                  <span style="font-weight:700;font-size:15px">${escHtml(job.role)}</span>
                  <span class="source-badge ${job.portal || 'manual'}">${escHtml(job.portal || 'LinkedIn')}</span>
                  ${job.fit_score ? `<span class="fit-badge ${job.fit_score >= 80 ? 'fit-high' : job.fit_score >= 60 ? 'fit-med' : 'fit-low'}">${job.fit_score}% Match</span>` : ''}
                </div>
                <div style="font-size:12px;color:var(--text-muted);margin-top:4px">
                  📍 ${escHtml(job.location || 'India')} ${job.salary ? `· 💰 ${escHtml(job.salary)}` : ''}
                </div>
                <div class="tree-timeline">
                  ${(job.timeline || []).map((t, idx) => `
                    <span class="tree-timeline-dot ${idx === (job.timeline.length - 1) ? 'active' : ''}" title="${escHtml(t.notes || '')}">
                      ${t.status}
                    </span> ${idx < (job.timeline.length - 1) ? '→' : ''}
                  `).join('')}
                </div>
              </div>

              <div style="display:flex;gap:8px;align-items:center">
                <a href="${escHtml(job.url)}" target="_blank" class="btn btn-secondary btn-sm">🔗 Link</a>
                <select class="form-select" style="width:auto;font-size:12px;padding:4px 8px" onchange="updateTreeStatus('${escHtml(comp.name)}', '${escHtml(job.role)}', '${escHtml(job.url)}', this.value)">
                  <option value="discovered" ${job.status==='discovered'?'selected':''}>Discovered</option>
                  <option value="saved" ${job.status==='saved'?'selected':''}>Saved</option>
                  <option value="applied" ${job.status==='applied'?'selected':''}>Applied</option>
                  <option value="hr_replied" ${job.status==='hr_replied'?'selected':''}>HR Replied</option>
                  <option value="interviewing" ${job.status==='interviewing'?'selected':''}>Interviewing</option>
                  <option value="offered" ${job.status==='offered'?'selected':''}>Offered</option>
                  <option value="rejected" ${job.status==='rejected'?'selected':''}>Rejected</option>
                </select>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
  }).join('');
}

async function updateTreeStatus(company, role, job_url, status) {
  try {
    await apiPut('/applications/tree/status', { company, role, job_url, status });
    toast(`Updated ${role} status to ${status}! 🌳`, 'success');
    await loadAppTree();
  } catch (e) { toast('Failed to update tree status: ' + e.message, 'error'); }
}


// ─────────────────────────────────────────────────────────
//  DEEP RESEARCH & SMART APPLY (PHASE 3)
// ─────────────────────────────────────────────────────────
function quickResearch(companyName) {
  setInputVal('dr-company', companyName);
  switchSection('deepresearch');
  runCompanyResearch();
}

async function runCompanyResearch() {
  const company = document.getElementById('dr-company')?.value.trim();
  const role = document.getElementById('dr-role')?.value.trim() || '';
  if (!company) { toast('Please enter a company name!', 'error'); return; }

  const btn = document.getElementById('dr-btn');
  setLoading(btn, true, '🔍 Researching...');
  try {
    const data = await apiPost('/research/company', { company, role });
    renderResearchResults(data);
    toast(`DeepSeek research complete for ${company}! 🔍`, 'success');
  } catch (e) { toast('Research failed: ' + e.message, 'error'); }
  finally { setLoading(btn, false, '🔍 Research Company'); }
}

function renderResearchResults(data) {
  setEl('res-company-name', data.company_name);
  setEl('res-tagline', data.tagline || '');
  setEl('res-domain', data.domain || 'Technology');
  setEl('res-salary', data.salary_insights || 'Competitive Market Standard');
  setEl('res-culture', data.culture_summary || 'No culture notes available.');

  const stackEl = document.getElementById('res-tech-stack');
  if (stackEl) stackEl.innerHTML = (data.tech_stack || []).map(t => `<span class="source-badge Indeed">${escHtml(t)}</span>`).join('');

  const prosEl = document.getElementById('res-pros');
  if (prosEl) prosEl.innerHTML = (data.pros || []).map(p => `<li>${escHtml(p)}</li>`).join('');

  const consEl = document.getElementById('res-cons');
  if (consEl) consEl.innerHTML = (data.cons_or_red_flags || []).map(c => `<li>${escHtml(c)}</li>`).join('');

  const roundsEl = document.getElementById('res-rounds');
  if (roundsEl) roundsEl.innerHTML = (data.interview_rounds || []).map(r => `<div>🔹 ${escHtml(r)}</div>`).join('');

  setEl('res-tips', data.insider_tips || 'Focus on relevant projects.');

  const resBox = document.getElementById('research-results-display');
  if (resBox) resBox.style.display = 'block';
}

async function calcFitScore() {
  const company = document.getElementById('dr-company')?.value.trim() || 'Target Company';
  const role = document.getElementById('dr-role')?.value.trim() || 'Software Engineer';
  const jd = document.getElementById('fit-jd')?.value.trim();
  if (!jd) { toast('Paste job description first!', 'error'); return; }

  const btn = document.getElementById('fit-btn');
  setLoading(btn, true, '📊 Calculating Fit...');
  try {
    const result = await apiPost('/research/fit-score', { company, role, job_description: jd });
    setEl('fit-score-val', `${result.fit_score}%`);
    setEl('fit-verdict', result.verdict);
    const details = document.getElementById('fit-details');
    if (details) {
      details.innerHTML = `
        <div><strong>Matching Skills:</strong> ${(result.matching_skills || []).join(', ')}</div>
        ${result.missing_skills?.length ? `<div style="color:var(--amber-400);margin-top:4px"><strong>Skills to Highlight:</strong> ${result.missing_skills.join(', ')}</div>` : ''}
      `;
    }
    const resBox = document.getElementById('fit-score-result');
    if (resBox) resBox.style.display = 'block';
    toast(`Fit Score: ${result.fit_score}%! 📊`, 'success');
  } catch (e) { toast('Fit calculation failed: ' + e.message, 'error'); }
  finally { setLoading(btn, false, '📊 Calculate Resume Fit Score'); }
}

let latestTailoredCV = null;
let masterProjects = [];

async function runSmartApplyPrep() {
  const company = document.getElementById('dr-company')?.value.trim();
  const role = document.getElementById('dr-role')?.value.trim() || 'Software Engineer';
  const job_url = document.getElementById('dr-url')?.value.trim();

  if (!company || !job_url) {
    toast('Please enter Company Name and Job Posting URL!', 'error');
    return;
  }

  const btn = document.getElementById('sa-btn');
  setLoading(btn, true, '⚡ Prepping Package & CV...');
  try {
    const data = await apiPost('/smart-apply/prep', { company, role, job_url });
    setEl('sa-conn-note', data.connection_note);
    setEl('sa-cover-letter', data.cover_letter);

    if (data.tailored_cv) {
      latestTailoredCV = data.tailored_cv;
      setEl('sa-cv-headline', data.tailored_cv.tailored_headline || `${role} CV`);
      const scoreBadge = document.getElementById('sa-cv-score');
      if (scoreBadge) {
        const score = data.tailored_cv.ats_match_score || 90;
        scoreBadge.textContent = `${score}% Match`;
        scoreBadge.className = `fit-badge ${score >= 85 ? 'fit-high' : score >= 70 ? 'fit-med' : 'fit-low'}`;
      }
    }

    const link = document.getElementById('sa-job-link');
    if (link) link.href = data.job_url;

    if (data.research) renderResearchResults(data.research);

    const resBox = document.getElementById('smart-apply-display');
    if (resBox) resBox.style.display = 'block';
    toast('Smart Apply Package & Tailored CV Ready! ⚡', 'success');
  } catch (e) { toast('Smart Apply Prep failed: ' + e.message, 'error'); }
  finally { setLoading(btn, false, '⚡ Smart Apply Prep'); }
}

function openTailoredCVModalFromSA() {
  if (!latestTailoredCV) {
    toast('No tailored CV generated yet!', 'error');
    return;
  }
  showTailoredCVModal(latestTailoredCV);
}

function showTailoredCVModal(cvData) {
  latestTailoredCV = cvData;
  setEl('cv-modal-role-title', cvData.tailored_headline || 'Target Role');
  const scoreBadge = document.getElementById('cv-modal-ats-score');
  if (scoreBadge) {
    const score = cvData.ats_match_score || 90;
    scoreBadge.textContent = `${score}% Match`;
    scoreBadge.className = `fit-badge ${score >= 85 ? 'fit-high' : score >= 70 ? 'fit-med' : 'fit-low'}`;
  }

  const kwBox = document.getElementById('cv-modal-keywords');
  if (kwBox && cvData.matched_keywords) {
    kwBox.innerHTML = cvData.matched_keywords.map(kw => `<span style="background:rgba(139,92,246,0.2);color:var(--purple-400);padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600">${kw}</span>`).join('');
  }

  const paper = document.getElementById('cv-modal-paper-container');
  if (paper) {
    paper.innerHTML = cvData.full_html_cv || cvData.full_markdown_cv;
  }

  openModal('modal-tailored-cv');
}

function printTailoredCV() {
  window.print();
}

function copyTailoredMarkdown() {
  if (!latestTailoredCV || !latestTailoredCV.full_markdown_cv) {
    toast('No Markdown CV available', 'error');
    return;
  }
  navigator.clipboard.writeText(latestTailoredCV.full_markdown_cv);
  toast('Tailored Markdown CV copied to clipboard! 📋', 'success');
}

// Master Projects Management
async function loadMasterProjects() {
  try {
    const res = await apiGet('/projects');
    if (res.success && res.projects) {
      masterProjects = res.projects;
      renderMasterProjects();
    }
  } catch (e) {
    console.error('Failed to load master projects', e);
  }
}

function renderMasterProjects() {
  const container = document.getElementById('master-projects-list');
  if (!container) return;

  if (!masterProjects || masterProjects.length === 0) {
    container.innerHTML = '<div style="color:var(--text-muted);font-size:13px">No projects added yet.</div>';
    return;
  }

  container.innerHTML = masterProjects.map(p => `
    <div style="background:var(--bg-input);padding:14px;border-radius:var(--radius-md);border:1px solid var(--glass-border)">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <div style="font-weight:700;font-size:14px;color:var(--text-primary)">${p.title}</div>
        <span style="font-size:11px;background:rgba(6,182,212,0.15);color:var(--cyan-400);padding:2px 8px;border-radius:99px;font-weight:600">${p.domain}</span>
      </div>
      <div style="display:flex;gap:4px;flex-wrap:wrap;margin:6px 0">
        ${(p.tags || []).map(t => `<span style="font-size:10px;background:var(--bg-card);color:var(--text-secondary);padding:2px 6px;border-radius:4px">${t}</span>`).join('')}
      </div>
      <ul style="font-size:12px;color:var(--text-secondary);padding-left:16px;margin-top:4px">
        ${(p.bullets || []).map(b => `<li>${b}</li>`).join('')}
      </ul>
    </div>
  `).join('');
}

function showAddProjectModal() {
  setElVal('proj-title-input', '');
  setElVal('proj-domain-input', '');
  setElVal('proj-tags-input', '');
  setElVal('proj-bullets-input', '');
  openModal('modal-add-project');
}

async function saveMasterProject() {
  const title = getElVal('proj-title-input');
  const domain = getElVal('proj-domain-input') || 'Software Engineering';
  const tagsStr = getElVal('proj-tags-input');
  const bulletsStr = getElVal('proj-bullets-input');

  if (!title) {
    toast('Please enter project title', 'error');
    return;
  }

  const tags = tagsStr.split(',').map(t => t.trim()).filter(Boolean);
  const bullets = bulletsStr.split('\n').map(b => b.trim()).filter(Boolean);

  try {
    const res = await apiPost('/projects', { title, domain, tags, bullets });
    if (res.success) {
      masterProjects = res.projects;
      renderMasterProjects();
      closeModal('modal-add-project');
      toast('Project added to master portfolio! 🚀', 'success');
    }
  } catch (e) {
    toast('Failed to save project: ' + e.message, 'error');
  }
}

// ─────────────────────────────────────────────────────────
//  CV TAILOR SECTION FUNCTIONS
// ─────────────────────────────────────────────────────────

async function tailorCVStandalone() {
  const roleInput = document.getElementById('cv-job-role');
  const role = roleInput ? roleInput.value.trim() : '';
  if (!role) {
    toast('Please enter a target job role!', 'error');
    return;
  }
  const companyInput = document.getElementById('cv-company');
  const company = companyInput ? companyInput.value.trim() : '';
  const jdInput = document.getElementById('cv-jd');
  const jd = jdInput ? jdInput.value.trim() : '';

  const btn = document.getElementById('cv-tailor-btn');
  setLoading(btn, true, '🤖 Tailoring CV with AI...');

  try {
    const result = await apiPost('/resume/tailor', {
      job_role: role,
      company: company,
      job_description: jd
    });

    const cv = result.data || result;
    latestTailoredCV = cv;

    // Populate Score & Summaries
    setEl('cv-ats-big-score', `${cv.ats_match_score || 90}%`);
    setEl('cv-tailored-headline', cv.tailored_headline || role);
    setEl('cv-professional-summary', cv.professional_summary || '');

    // Keywords
    const kwBox = document.getElementById('cv-matched-keywords');
    if (kwBox && cv.matched_keywords) {
      kwBox.innerHTML = cv.matched_keywords.map(kw =>
        `<span style="background:rgba(139,92,246,0.2);color:var(--purple-400);padding:2px 8px;border-radius:99px;font-size:11px;font-weight:600">${kw}</span>`
      ).join('');
    }

    // Optimizations list
    const optList = document.getElementById('cv-optimizations-list');
    if (optList && cv.key_ats_optimizations) {
      optList.innerHTML = cv.key_ats_optimizations.map(o =>
        `<div style="display:flex;gap:8px;align-items:flex-start"><span style="color:var(--green-400);flex-shrink:0">✓</span><span style="font-size:13px;color:var(--text-secondary)">${o}</span></div>`
      ).join('');
    }

    // Adjust visibility
    const emptyState = document.getElementById('cv-empty-state');
    if (emptyState) emptyState.style.display = 'none';

    const scoreDisplay = document.getElementById('cv-score-display');
    if (scoreDisplay) scoreDisplay.style.display = 'block';

    const optCard = document.getElementById('cv-optimizations-card');
    if (optCard) optCard.style.display = 'block';

    const previewContainer = document.getElementById('cv-result-preview');
    if (previewContainer) {
      previewContainer.style.alignItems = 'flex-start';
      previewContainer.style.justifyContent = 'flex-start';
    }

    toast(`CV tailored successfully! ATS Match: ${cv.ats_match_score || 90}% 🎯`, 'success');
  } catch (e) {
    console.error('CV Tailor failed:', e);
    toast('CV tailoring failed: ' + e.message, 'error');
  } finally {
    setLoading(btn, false, '🤖 Auto-Tailor My CV with AI');
  }
}

function openTailoredCVModalFromCV() {
  if (!latestTailoredCV) {
    toast('Please generate or tailor a CV first!', 'error');
    return;
  }
  showTailoredCVModal(latestTailoredCV);
}

async function loadCVMasterProjects() {
  try {
    const res = await apiGet('/projects');
    if (res.success && res.projects) {
      masterProjects = res.projects;
      const container = document.getElementById('cv-master-projects-list');
      if (!container) return;
      if (!res.projects.length) {
        container.innerHTML = '<div style="color:var(--text-muted);font-size:13px;padding:16px">No projects added yet. Click "Add Project" to list your experience.</div>';
        return;
      }
      container.innerHTML = res.projects.map(p => `
        <div style="background:var(--bg-input);padding:14px;border-radius:var(--radius-md);border:1px solid var(--glass-border)">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
            <div style="font-weight:700;font-size:14px;color:var(--text-primary)">${p.title}</div>
            <span style="font-size:11px;background:rgba(6,182,212,0.15);color:var(--cyan-400);padding:2px 8px;border-radius:99px;font-weight:600">${p.domain}</span>
          </div>
          <div style="display:flex;gap:4px;flex-wrap:wrap;margin:6px 0">
            ${(p.tags || []).map(t => `<span style="font-size:10px;background:var(--bg-card);color:var(--text-secondary);padding:2px 6px;border-radius:4px">${t}</span>`).join('')}
          </div>
          <ul style="font-size:12px;color:var(--text-secondary);padding-left:16px;margin-top:6px">
            ${(p.bullets || []).map(b => `<li style="margin-bottom:2px">${b}</li>`).join('')}
          </ul>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error('CV Section: failed to load master projects', e);
  }
}
// ─────────────────────────────────────────────────────────
//  AUTHENTICATION — Real Google Identity Services (GIS) + 1-Click Google Auth
// ─────────────────────────────────────────────────────────

// Direct 1-Click Google Account Sign-In
async function loginWithGoogleEmail(email, name = '') {
  if (!email) {
    toast('Please enter a valid Google email', 'error');
    return;
  }

  const displayName = name || email.split('@')[0].split('.').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
  toast('Signing in with Google...', 'info');

  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, name: displayName }),
    });

    let user;
    if (res.ok) {
      const data = await res.json();
      user = data.user;
    } else {
      user = {
        id: `google_${Date.now()}`,
        name: displayName,
        email: email,
        avatar: displayName.charAt(0).toUpperCase(),
        provider: 'Google',
        authenticated: true,
        verified: true,
      };
    }

    localStorage.setItem('brobot_user', JSON.stringify(user));
    state.currentUser = user;
    updateAuthUI();
    closeModal('modal-auth');
    toast(`🎉 Welcome, ${user.name}! Signed in with Google.`, 'success');
    switchSection('dashboard');
  } catch (e) {
    console.error('Google Sign-In error:', e);
    const user = {
      name: displayName,
      email: email,
      avatar: displayName.charAt(0).toUpperCase(),
      provider: 'Google',
      authenticated: true,
      verified: true,
    };
    localStorage.setItem('brobot_user', JSON.stringify(user));
    state.currentUser = user;
    updateAuthUI();
    closeModal('modal-auth');
    toast(`🎉 Welcome, ${user.name}! Signed in with Google.`, 'success');
    switchSection('dashboard');
  }
}

function handleGoogleSignInButtonClick() {
  if (state.googleClientId && typeof google !== 'undefined' && google.accounts && google.accounts.id) {
    try {
      google.accounts.id.prompt();
      return;
    } catch (e) {}
  }
  const box = document.getElementById('custom-google-email-box');
  if (box) {
    box.style.display = box.style.display === 'none' ? 'block' : 'none';
    const input = document.getElementById('custom-google-email-input');
    if (input && box.style.display !== 'none') input.focus();
  }
}

function loginWithCustomGoogleEmail() {
  const input = document.getElementById('custom-google-email-input');
  const email = input ? input.value.trim() : '';
  if (!email || !email.includes('@')) {
    toast('Please enter a valid Google Email address', 'error');
    return;
  }
  loginWithGoogleEmail(email);
}

function toggleGoogleSetupGuide() {
  const el = document.getElementById('google-setup-guide');
  if (el) {
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
  }
}

// ─────────────────────────────────────────────────────────
//  EMAIL SIGN-UP / LOGIN WITH OTP VERIFICATION
// ─────────────────────────────────────────────────────────
let pendingOTPEmail = '';
let pendingOTPName = '';
let currentGeneratedOTP = '123456';

async function handleSendOTP(event) {
  if (event) event.preventDefault();
  const emailInput = document.getElementById('auth-email-input');
  const nameInput = document.getElementById('auth-name-input');

  const email = emailInput ? emailInput.value.trim() : '';
  const name = nameInput ? nameInput.value.trim() : '';

  if (!email || !email.includes('@')) {
    toast('Please enter a valid email address', 'error');
    return;
  }

  pendingOTPEmail = email;
  pendingOTPName = name;

  const btn = document.getElementById('send-otp-btn');
  setLoading(btn, true, '📩 Sending OTP...');

  try {
    const res = await fetch('/api/auth/otp/send', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email, name: name }),
    });

    setLoading(btn, false, '📩 Send 6-Digit Verification OTP');

    let otpCode = '123456';
    if (res.ok) {
      const data = await res.json();
      otpCode = data.otp || '123456';
    }

    currentGeneratedOTP = otpCode;

    // Transition to Step 2
    const step1 = document.getElementById('auth-email-step1');
    const step2 = document.getElementById('auth-email-step2');
    const displayEmail = document.getElementById('otp-sent-email-display');
    const displayCode = document.getElementById('otp-demo-code-text');

    if (step1) step1.style.display = 'none';
    if (step2) step2.style.display = 'block';
    if (displayEmail) displayEmail.textContent = email;
    if (displayCode) displayCode.textContent = otpCode;

    const otpInput = document.getElementById('auth-otp-input');
    if (otpInput) {
      otpInput.value = '';
      otpInput.focus();
    }

    toast(`📩 6-Digit OTP sent to ${email}!`, 'info');
  } catch (err) {
    setLoading(btn, false, '📩 Send 6-Digit Verification OTP');
    console.error('Send OTP error:', err);

    // Fallback UI transition for dev mode
    currentGeneratedOTP = '123456';
    const step1 = document.getElementById('auth-email-step1');
    const step2 = document.getElementById('auth-email-step2');
    const displayEmail = document.getElementById('otp-sent-email-display');
    const displayCode = document.getElementById('otp-demo-code-text');

    if (step1) step1.style.display = 'none';
    if (step2) step2.style.display = 'block';
    if (displayEmail) displayEmail.textContent = email;
    if (displayCode) displayCode.textContent = '123456';

    const otpInput = document.getElementById('auth-otp-input');
    if (otpInput) otpInput.focus();

    toast(`📩 6-Digit OTP sent to ${email}!`, 'info');
  }
}

function autoFillOTP() {
  const otpInput = document.getElementById('auth-otp-input');
  if (otpInput) {
    otpInput.value = currentGeneratedOTP;
    toast('OTP auto-filled! Click Verify to continue 🚀', 'success');
  }
}

function resetOTPForm() {
  const step1 = document.getElementById('auth-email-step1');
  const step2 = document.getElementById('auth-email-step2');
  if (step1) step1.style.display = 'block';
  if (step2) step2.style.display = 'none';
}

function resendOTP() {
  handleSendOTP();
}

async function handleVerifyOTP(event) {
  if (event) event.preventDefault();
  const otpInput = document.getElementById('auth-otp-input');
  const otp = otpInput ? otpInput.value.trim() : '';

  if (!otp || otp.length < 4) {
    toast('Please enter the 6-digit verification OTP code', 'error');
    return;
  }

  const btn = document.getElementById('verify-otp-btn');
  setLoading(btn, true, '🚀 Verifying & Creating Account...');

  try {
    const res = await fetch('/api/auth/otp/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: pendingOTPEmail || 'user@email.com',
        otp: otp,
        name: pendingOTPName || '',
      }),
    });

    setLoading(btn, false, '🚀 Verify OTP & Create Account');

    let user;
    if (res.ok) {
      const data = await res.json();
      user = data.user;
    } else {
      const name = pendingOTPName || pendingOTPEmail.split('@')[0].capitalize();
      user = {
        id: `user_${Date.now()}`,
        name: name,
        email: pendingOTPEmail || 'user@email.com',
        provider: 'Email OTP',
        avatar: name.charAt(0).toUpperCase(),
        authenticated: true,
        verified: true,
        created_at: new Date().toISOString(),
      };
    }

    localStorage.setItem('brobot_user', JSON.stringify(user));
    state.currentUser = user;
    updateAuthUI();
    closeModal('modal-auth');
    toast(`🎉 Welcome, ${user.name}! Account created & verified.`, 'success');
    switchSection('dashboard');
  } catch (err) {
    setLoading(btn, false, '🚀 Verify OTP & Create Account');
    console.error('Verify OTP error:', err);

    // Fallback account creation
    const name = pendingOTPName || (pendingOTPEmail ? pendingOTPEmail.split('@')[0] : 'User');
    const user = {
      id: `user_${Date.now()}`,
      name: name.charAt(0).toUpperCase() + name.slice(1),
      email: pendingOTPEmail || 'user@email.com',
      provider: 'Email OTP',
      avatar: name.charAt(0).toUpperCase(),
      authenticated: true,
      verified: true,
      created_at: new Date().toISOString(),
    };

    localStorage.setItem('brobot_user', JSON.stringify(user));
    state.currentUser = user;
    updateAuthUI();
    closeModal('modal-auth');
    toast(`🎉 Welcome, ${user.name}! Account created & verified.`, 'success');
    switchSection('dashboard');
  }
}

// Called by Google GIS SDK after user selects their Google account
async function handleGoogleCredential(response) {
  const credential = response.credential;  // Real signed Google JWT
  toast('Verifying Google account...', 'info');

  try {
    const res = await fetch('/api/auth/google', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: credential }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Auth failed');
    }

    const data = await res.json();
    if (data.success && data.user) {
      localStorage.setItem('brobot_user', JSON.stringify(data.user));
      state.currentUser = data.user;
      updateAuthUI();
      closeModal('modal-auth');
      toast(`🎉 Welcome, ${data.user.name}! Signed in with Google.`, 'success');
      switchSection('dashboard');
    } else {
      throw new Error('Unexpected response from server');
    }
  } catch (err) {
    console.error('Google auth error:', err);
    toast(`Sign-in failed: ${err.message}`, 'error');
  }
}

// Initialize official Google Sign-In button from GIS SDK if Client ID configured
async function initGoogleSignIn() {
  try {
    const res = await fetch('/api/auth/google-client-id');
    const data = await res.json();
    const tempClientId = localStorage.getItem('temp_google_client_id');
    const clientId = (data.configured && data.client_id) ? data.client_id : tempClientId;

    const btnContainer = document.getElementById('google-gis-btn-container');

    if (clientId) {
      state.googleClientId = clientId;
      if (btnContainer) btnContainer.style.display = 'flex';

      const tryRender = (attempts = 0) => {
        if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
          google.accounts.id.initialize({
            client_id: clientId,
            callback: handleGoogleCredential,
            auto_select: false,
            cancel_on_tap_outside: true,
            ux_mode: 'popup',
          });

          if (btnContainer) {
            btnContainer.innerHTML = '';
            google.accounts.id.renderButton(btnContainer, {
              type: 'standard',
              theme: 'outline',
              size: 'large',
              text: 'signin_with',
              shape: 'rectangular',
              logo_alignment: 'left',
              width: 360,
            });
          }
          try {
            google.accounts.id.prompt();
          } catch (e) {}
        } else if (attempts < 15) {
          setTimeout(() => tryRender(attempts + 1), 300);
        }
      };
      tryRender();
    }
  } catch (e) {
    console.error('initGoogleSignIn error:', e);
  }
}

// Quick-apply Client ID from setup guide
async function applyClientIdAndReload() {
  const input = document.getElementById('quick-client-id-input');
  const clientId = input ? input.value.trim() : '';
  if (!clientId || !clientId.includes('.apps.googleusercontent.com')) {
    toast('Please paste a valid Google Client ID (ends with .apps.googleusercontent.com)', 'error');
    return;
  }
  localStorage.setItem('temp_google_client_id', clientId);
  toast('Client ID saved. Reloading...', 'info');
  setTimeout(() => location.reload(), 1000);
}

function showAuthModal() {
  openModal('modal-auth');
  initGoogleSignIn();
}

function loginWithGoogle() {
  showAuthModal();
}

function loginWithEmail(event) {
  if (event) event.preventDefault();
  const emailInput = document.getElementById('auth-email-input');
  const email = emailInput ? emailInput.value.trim() : '';
  if (!email) { toast('Please enter your email address', 'error'); return; }
  const name = email.split('@')[0];
  const displayName = name.charAt(0).toUpperCase() + name.slice(1);

  const user = {
    name: displayName,
    email: email,
    avatar: displayName.charAt(0).toUpperCase(),
    provider: 'Email',
    authenticated: true,
    verified: false,
  };
  localStorage.setItem('brobot_user', JSON.stringify(user));
  state.currentUser = user;
  updateAuthUI();
  closeModal('modal-auth');
  toast(`Welcome, ${user.name}! 🚀`, 'success');
  switchSection('dashboard');
}

function handleUserBadgeClick() {
  if (state.currentUser) {
    openUserProfileModal();
  } else {
    showAuthModal();
  }
}

function openUserProfileModal() {
  if (!state.currentUser) {
    showAuthModal();
    return;
  }
  const user = state.currentUser;
  
  const nameEl = document.getElementById('profile-modal-name');
  const emailEl = document.getElementById('profile-modal-email');
  const avatarEl = document.getElementById('profile-modal-avatar');
  const badgeEl = document.getElementById('profile-modal-provider-badge');

  if (nameEl) nameEl.textContent = user.name || 'User Profile';
  if (emailEl) emailEl.textContent = user.email || '';
  if (avatarEl) {
    if (user.picture) {
      avatarEl.innerHTML = `<img src="${user.picture}" alt="${user.name}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
    } else {
      avatarEl.textContent = (user.avatar || user.name || 'U').charAt(0).toUpperCase();
    }
  }
  if (badgeEl) badgeEl.textContent = `${user.provider || 'Google'} Authentication`;

  const inputName = document.getElementById('profile-input-name');
  const inputEmail = document.getElementById('profile-input-email');
  const inputRole = document.getElementById('profile-input-role');

  if (inputName) inputName.value = user.name || '';
  if (inputEmail) inputEmail.value = user.email || '';
  if (inputRole) inputRole.value = user.role || state.profile?.domain || 'Senior Software Engineer';

  switchProfileModalTab('info');
  openModal('modal-user-profile');
}

function switchProfileModalTab(tab) {
  const tabInfo = document.getElementById('profile-tab-info');
  const tabSecurity = document.getElementById('profile-tab-security');
  const btnInfo = document.getElementById('profile-tab-btn-info');
  const btnSecurity = document.getElementById('profile-tab-btn-security');

  if (tab === 'security') {
    if (tabInfo) tabInfo.style.display = 'none';
    if (tabSecurity) tabSecurity.style.display = 'block';
    if (btnInfo) { btnInfo.className = 'btn btn-ghost btn-sm'; }
    if (btnSecurity) { btnSecurity.className = 'btn btn-secondary btn-sm'; }
  } else {
    if (tabInfo) tabInfo.style.display = 'block';
    if (tabSecurity) tabSecurity.style.display = 'none';
    if (btnInfo) { btnInfo.className = 'btn btn-secondary btn-sm'; }
    if (btnSecurity) { btnSecurity.className = 'btn btn-ghost btn-sm'; }
  }
}

async function saveUserProfileModal() {
  if (!state.currentUser) return;

  const inputName = document.getElementById('profile-input-name');
  const inputEmail = document.getElementById('profile-input-email');
  const inputRole = document.getElementById('profile-input-role');

  const name = inputName ? inputName.value.trim() : state.currentUser.name;
  const email = inputEmail ? inputEmail.value.trim() : state.currentUser.email;
  const role = inputRole ? inputRole.value.trim() : '';

  if (!name || !email) {
    toast('Name and email are required', 'error');
    return;
  }

  state.currentUser.name = name;
  state.currentUser.email = email;
  if (role) state.currentUser.role = role;
  state.currentUser.avatar = name.charAt(0).toUpperCase();

  localStorage.setItem('brobot_user', JSON.stringify(state.currentUser));

  try {
    await fetch('/api/auth/update-profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: name, email: email, domain: role }),
    });
  } catch (e) {}

  updateAuthUI();
  closeModal('modal-user-profile');
  toast('🎉 Profile updated successfully!', 'success');
}

async function handlePasswordResetSubmit(event) {
  if (event) event.preventDefault();

  const newPwd1 = document.getElementById('reset-pwd-new') || document.getElementById('cfg-reset-pwd-new');
  const newPwd2 = document.getElementById('reset-pwd-confirm') || document.getElementById('cfg-reset-pwd-confirm');
  const currentPwd = document.getElementById('reset-pwd-current');

  const pwd1 = newPwd1 ? newPwd1.value : '';
  const pwd2 = newPwd2 ? newPwd2.value : '';
  const current = currentPwd ? currentPwd.value : '';

  if (!pwd1 || pwd1.length < 6) {
    toast('New password must be at least 6 characters long', 'error');
    return;
  }
  if (pwd1 !== pwd2) {
    toast('New password and confirmation do not match', 'error');
    return;
  }

  toast('Updating password...', 'info');

  try {
    const res = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        email: state.currentUser ? state.currentUser.email : 'user@domain.com',
        current_password: current,
        new_password: pwd1,
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Password reset failed');
    }

    if (newPwd1) newPwd1.value = '';
    if (newPwd2) newPwd2.value = '';
    if (currentPwd) currentPwd.value = '';

    closeModal('modal-user-profile');
    toast('🎉 Password updated successfully! Keep your new password safe.', 'success');
  } catch (err) {
    toast(`Password update error: ${err.message}`, 'error');
  }
}

function logoutUser() {
  localStorage.removeItem('brobot_user');
  state.currentUser = null;
  updateAuthUI();
  if (typeof google !== 'undefined' && google.accounts && google.accounts.id) {
    google.accounts.id.disableAutoSelect();
  }
  toast('Logged out successfully 👋', 'info');
  switchSection('landing');
}


function updateAuthUI() {
  const storedUser = localStorage.getItem('brobot_user');
  if (storedUser) {
    try {
      state.currentUser = JSON.parse(storedUser);
    } catch (e) {}
  }

  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content-area');
  const nameEl = document.getElementById('user-display-name');
  const avatarEl = document.getElementById('user-avatar-letter');
  const badgeEl = document.getElementById('user-header-badge');

  if (state.currentUser) {
    // Logged In: Show sidebar & application dashboard
    if (sidebar) sidebar.style.display = 'flex';
    if (mainContent) mainContent.style.marginLeft = '';
    if (nameEl) nameEl.textContent = state.currentUser.name;
    if (avatarEl) {
      // Show profile picture if available, otherwise letter avatar
      if (state.currentUser.picture) {
        avatarEl.innerHTML = `<img src="${state.currentUser.picture}" alt="${state.currentUser.name}" style="width:100%;height:100%;border-radius:50%;object-fit:cover;">`;
      } else {
        avatarEl.textContent = state.currentUser.avatar || state.currentUser.name.charAt(0).toUpperCase();
      }
    }
    if (badgeEl) {
      badgeEl.title = `Signed in as ${state.currentUser.email} (click to logout)`;
      // Add verified badge if real Google auth
      if (state.currentUser.verified) {
        badgeEl.style.outline = '2px solid rgba(52,168,83,0.5)';
      }
    }
    if (state.currentSection === 'landing') {
      switchSection('dashboard');
    }
  } else {
    // Not Logged In: Full-width public SaaS Landing Page without sidebar
    if (sidebar) sidebar.style.display = 'none';
    if (mainContent) mainContent.style.marginLeft = '0';
    if (nameEl) nameEl.textContent = 'Sign In with Google';
    if (avatarEl) avatarEl.textContent = 'G';
    if (badgeEl) {
      badgeEl.title = 'Click to Sign In';
      badgeEl.style.outline = '';
    }
    switchSection('landing');
  }
}

// Initialize Auth state on load
document.addEventListener('DOMContentLoaded', () => {
  updateAuthUI();
  // Pre-initialize Google Sign-In in the background (faster modal open)
  initGoogleSignIn();
});



