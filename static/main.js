/* ─────────────────────────────────────────────
   EduAnalytics — Main JavaScript
   ───────────────────────────────────────────── */

const API = '';   // same-origin Flask
Chart.defaults.color = '#7b7f9a';
Chart.defaults.borderColor = 'rgba(255,255,255,0.06)';
Chart.defaults.font.family = 'Inter, system-ui, sans-serif';

// ── Chart registry ──────────────────────────────
const charts = {};

function destroyChart(id) {
  if (charts[id]) { charts[id].destroy(); delete charts[id]; }
}

// ── Gradient helper ──────────────────────────────
function gradient(ctx, colors) {
  const g = ctx.createLinearGradient(0, 0, 0, 300);
  colors.forEach(([stop, c]) => g.addColorStop(stop, c));
  return g;
}

// ── Palette ──────────────────────────────────────
const PAL = ['#6366f1','#8b5cf6','#06b6d4','#10b981','#f59e0b','#f43f5e','#ec4899'];

// ── Tab navigation ──────────────────────────────
const tabMeta = {
  dashboard: { title: 'Dashboard',       sub: 'Student Performance Overview' },
  data:      { title: 'Data Explorer',   sub: 'Browse & filter student records' },
  viz:       { title: 'Visualizations',  sub: 'Interactive charts & correlations' },
  model:     { title: 'ML Model',        sub: 'Random Forest classifier & predictions' },
  insights:  { title: 'Insights',        sub: 'Key findings from the dataset' },
};

document.querySelectorAll('.nav-item').forEach(el => {
  el.addEventListener('click', e => {
    e.preventDefault();
    const tab = el.dataset.tab;
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    el.classList.add('active');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.getElementById(`tab-${tab}`).classList.add('active');
    document.getElementById('page-title').textContent   = tabMeta[tab].title;
    document.getElementById('page-subtitle').textContent = tabMeta[tab].sub;
    loadTab(tab);
  });
});

const loaded = new Set();
function loadTab(tab) {
  if (loaded.has(tab)) return;
  loaded.add(tab);
  if (tab === 'dashboard') initDashboard();
  if (tab === 'data')      initData();
  if (tab === 'viz')       initViz();
  if (tab === 'model')     initModel();
  if (tab === 'insights')  initInsights();
}

// ── Utility ──────────────────────────────────────
async function api(path) { const r = await fetch(API + path); return r.json(); }

function animCount(el, end, suffix = '') {
  let start = 0;
  const step = end / 40;
  const t = setInterval(() => {
    start = Math.min(start + step, end);
    el.textContent = Number.isInteger(end) ? Math.round(start) + suffix : start.toFixed(1) + suffix;
    if (start >= end) clearInterval(t);
  }, 20);
}

// ══════════════════════════════════════════════════
// DASHBOARD
// ══════════════════════════════════════════════════
async function initDashboard() {
  const d = await api('/api/stats');

  // KPI
  const kpis = [
    { id:'total', val: d.total_students, suffix:'', sub:'5 departments represented' },
    { id:'pass',  val: d.pass_rate,      suffix:'%', sub:`${Math.round(d.total_students*d.pass_rate/100)} students passed` },
    { id:'score', val: d.avg_score,      suffix:'', sub:'out of 100 max' },
    { id:'study', val: d.avg_study_hours,suffix:'h', sub:'per day average' },
  ];
  kpis.forEach(k => {
    const card = document.getElementById(`kpi-${k.id}`);
    card.classList.remove('loading');
    animCount(document.getElementById(`v-${k.id}`), k.val, k.suffix);
    document.getElementById(`s-${k.id}`).textContent = k.sub;
  });

  // Department pass rate
  const depts = Object.keys(d.pass_by_dept);
  const passVals = Object.values(d.pass_by_dept);
  const ctx1 = document.getElementById('chart-dept-pass').getContext('2d');
  destroyChart('dept-pass');
  charts['dept-pass'] = new Chart(ctx1, {
    type: 'bar',
    data: {
      labels: depts,
      datasets: [{
        label: 'Pass Rate (%)',
        data: passVals,
        backgroundColor: PAL.map(c => c + '55'),
        borderColor: PAL,
        borderWidth: 2,
        borderRadius: 6,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { min: 0, max: 100, ticks: { callback: v => v + '%' }, grid: { color: 'rgba(255,255,255,.05)' } },
        x: { grid: { display: false } }
      }
    }
  });

  // Gender donut
  const ctx2 = document.getElementById('chart-gender').getContext('2d');
  destroyChart('gender');
  charts['gender'] = new Chart(ctx2, {
    type: 'doughnut',
    data: {
      labels: Object.keys(d.gender_counts),
      datasets: [{ data: Object.values(d.gender_counts), backgroundColor: ['#6366f1','#ec4899'], borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { padding: 16, boxWidth: 12 } } },
      cutout: '65%',
    }
  });

  // Avg score by dept
  const ctx3 = document.getElementById('chart-dept-score').getContext('2d');
  destroyChart('dept-score');
  charts['dept-score'] = new Chart(ctx3, {
    type: 'bar',
    data: {
      labels: Object.keys(d.avg_score_by_dept),
      datasets: [{
        label: 'Avg Score',
        data: Object.values(d.avg_score_by_dept),
        backgroundColor: gradient(ctx3, [[0,'rgba(99,102,241,.8)'], [1,'rgba(139,92,246,.4)']]),
        borderRadius: 6, borderWidth: 0,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { min: 0, max: 100, grid: { color: 'rgba(255,255,255,.05)' } },
        y: { grid: { display: false } }
      }
    }
  });
}

// ══════════════════════════════════════════════════
// DATA EXPLORER
// ══════════════════════════════════════════════════
let dataPage = 1;
const dataLimit = 15;
let dataTotal  = 0;

async function initData() { await fetchData(); }

document.getElementById('btn-filter').addEventListener('click', () => {
  loaded.delete('data');
  dataPage = 1;
  loaded.add('data');
  fetchData();
});

async function fetchData() {
  const dept   = document.getElementById('filter-dept').value;
  const gender = document.getElementById('filter-gender').value;
  const res    = await api(`/api/data?page=${dataPage}&limit=${dataLimit}&dept=${dept}&gender=${gender}`);
  dataTotal    = res.total;
  renderTable(res.rows);
  renderPagination();
}

function renderTable(rows) {
  const tbody = document.getElementById('table-body');
  tbody.innerHTML = rows.map(r => `
    <tr>
      <td><span style="font-family:var(--mono);color:var(--accent)">${r.student_id}</span></td>
      <td>${r.age}</td>
      <td>${r.gender}</td>
      <td><span style="color:var(--cyan)">${r.department}</span></td>
      <td>${r.study_hours}h</td>
      <td>${r.attendance}%</td>
      <td>${r.prev_score}</td>
      <td>${r.sleep_hours}h</td>
      <td>${r.assignments}/10</td>
      <td>${r.extracurricular ? '✅' : '❌'}</td>
      <td style="font-weight:700">${r.final_score}</td>
      <td><span class="badge badge-${r.pass_fail ? 'pass' : 'fail'}">${r.pass_fail ? 'Pass' : 'Fail'}</span></td>
    </tr>`).join('');
}

function renderPagination() {
  const totalPages = Math.ceil(dataTotal / dataLimit);
  const pg = document.getElementById('pagination');
  pg.innerHTML = '';
  const makeBtn = (label, page, active) => {
    const b = document.createElement('button');
    b.className = 'page-btn' + (active ? ' active' : '');
    b.textContent = label;
    b.addEventListener('click', () => { dataPage = page; fetchData(); });
    return b;
  };
  if (dataPage > 1) pg.appendChild(makeBtn('‹', dataPage - 1, false));
  for (let i = Math.max(1, dataPage - 2); i <= Math.min(totalPages, dataPage + 2); i++)
    pg.appendChild(makeBtn(i, i, i === dataPage));
  if (dataPage < totalPages) pg.appendChild(makeBtn('›', dataPage + 1, false));
}

// ══════════════════════════════════════════════════
// VISUALIZATIONS
// ══════════════════════════════════════════════════
async function initViz() {
  await Promise.all([loadScatter(), loadHist(), loadCorr()]);
  document.getElementById('btn-viz-update').addEventListener('click', async () => {
    await Promise.all([loadScatter(), loadHist()]);
  });
}

async function loadScatter() {
  const x = document.getElementById('scatter-x').value;
  const y = document.getElementById('scatter-y').value;
  const data = await api(`/api/scatter?x=${x}&y=${y}`);
  const passed = data.filter(d => d.pass_fail === 1);
  const failed = data.filter(d => d.pass_fail === 0);
  destroyChart('scatter');
  const ctx = document.getElementById('chart-scatter').getContext('2d');
  charts['scatter'] = new Chart(ctx, {
    type: 'scatter',
    data: {
      datasets: [
        { label: 'Pass', data: passed.map(d => ({ x: d[x], y: d[y] })), backgroundColor: 'rgba(16,185,129,.65)', pointRadius: 5, pointHoverRadius: 7 },
        { label: 'Fail', data: failed.map(d => ({ x: d[x], y: d[y] })), backgroundColor: 'rgba(244,63,94,.65)', pointRadius: 5, pointHoverRadius: 7 },
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        x: { title: { display: true, text: x.replace(/_/g,' ') }, grid: { color: 'rgba(255,255,255,.05)' } },
        y: { title: { display: true, text: y.replace(/_/g,' ') }, grid: { color: 'rgba(255,255,255,.05)' } }
      }
    }
  });
}

async function loadHist() {
  const col  = document.getElementById('hist-col').value;
  const data = await api(`/api/histogram?col=${col}`);
  const min  = Math.min(...data.data);
  const max  = Math.max(...data.data);
  const bins = 15;
  const binSize = (max - min) / bins;
  const counts  = new Array(bins).fill(0);
  const labels  = [];
  for (let i = 0; i < bins; i++) labels.push((min + i * binSize).toFixed(0));
  data.data.forEach(v => {
    const idx = Math.min(Math.floor((v - min) / binSize), bins - 1);
    counts[idx]++;
  });
  destroyChart('hist');
  const ctx = document.getElementById('chart-hist').getContext('2d');
  charts['hist'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: col.replace(/_/g, ' '),
        data: counts,
        backgroundColor: gradient(ctx, [[0,'rgba(139,92,246,.8)'], [1,'rgba(6,182,212,.4)']]),
        borderRadius: 4, borderWidth: 0,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: 'rgba(255,255,255,.05)' } }
      }
    }
  });
}

async function loadCorr() {
  const { columns, matrix } = await api('/api/correlation');
  const container = document.getElementById('heatmap-container');
  const table = document.createElement('table');
  table.className = 'heatmap-table';
  const labels = columns.map(c => c.replace(/_/g, ' '));

  // header
  const thead = table.createTHead();
  const hr = thead.insertRow();
  hr.insertCell().textContent = '';
  labels.forEach(l => { const th = document.createElement('th'); th.textContent = l; hr.appendChild(th); });

  // body
  const tbody = table.createTBody();
  matrix.forEach((row, ri) => {
    const tr = tbody.insertRow();
    const th = document.createElement('th'); th.textContent = labels[ri]; tr.appendChild(th);
    row.forEach(val => {
      const td = tr.insertCell();
      td.textContent = val.toFixed(2);
      const abs = Math.abs(val);
      let bg, fg;
      if (val > 0.7)       { bg = `rgba(16,185,129,${abs})`; fg = '#fff'; }
      else if (val > 0.3)  { bg = `rgba(99,102,241,${abs})`; fg = '#fff'; }
      else if (val > 0)    { bg = `rgba(99,102,241,${abs*0.5})`; fg = '#ccc'; }
      else if (val > -0.3) { bg = `rgba(244,63,94,${abs*0.5})`; fg = '#ccc'; }
      else                 { bg = `rgba(244,63,94,${abs})`; fg = '#fff'; }
      td.style.cssText = `background:${bg};color:${fg}`;
    });
  });
  container.innerHTML = '';
  container.appendChild(table);
}

// ══════════════════════════════════════════════════
// ML MODEL
// ══════════════════════════════════════════════════
async function initModel() {
  const d = await api('/api/model');

  document.getElementById('m-accuracy').textContent = d.accuracy + '%';
  document.getElementById('m-accuracy').style.color = d.accuracy > 80 ? 'var(--green)' : 'var(--amber)';
  document.getElementById('m-train').textContent = d.samples_train;
  document.getElementById('m-test').textContent  = d.samples_test;

  // Feature importance
  const feats  = Object.keys(d.feature_importances).map(k => k.replace(/_/g,' '));
  const values = Object.values(d.feature_importances);
  destroyChart('feat-imp');
  const ctx = document.getElementById('chart-feat-imp').getContext('2d');
  charts['feat-imp'] = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: feats,
      datasets: [{
        label: 'Importance',
        data: values,
        backgroundColor: PAL.map(c => c + 'bb'),
        borderColor: PAL,
        borderWidth: 1.5, borderRadius: 5,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,.05)' } },
        y: { grid: { display: false } }
      }
    }
  });

  // Confusion matrix
  const [[tn,fp],[fn,tp]] = d.confusion_matrix;
  document.getElementById('confusion-matrix').innerHTML = `
    <div style="text-align:center;margin-bottom:8px;color:var(--muted);font-size:.75rem">Predicted →</div>
    <div class="cm-grid">
      <div class="cm-label"></div>
      <div class="cm-label">Fail</div>
      <div class="cm-label">Pass</div>
      <div class="cm-label" style="writing-mode:vertical-lr;transform:rotate(180deg)">Actual</div>
      <div class="cm-cell" style="background:rgba(16,185,129,.25);color:var(--green)">${tn}<br><small style="font-size:.65rem;font-family:var(--font);font-weight:400">TN</small></div>
      <div class="cm-cell" style="background:rgba(244,63,94,.15);color:var(--rose)">${fp}<br><small style="font-size:.65rem;font-family:var(--font);font-weight:400">FP</small></div>
      <div class="cm-cell" style="background:rgba(244,63,94,.15);color:var(--rose)">${fn}<br><small style="font-size:.65rem;font-family:var(--font);font-weight:400">FN</small></div>
      <div class="cm-cell" style="background:rgba(16,185,129,.25);color:var(--green)">${tp}<br><small style="font-size:.65rem;font-family:var(--font);font-weight:400">TP</small></div>
    </div>`;

  // Predict button
  document.getElementById('btn-predict').addEventListener('click', runPrediction);
}

async function runPrediction() {
  const body = {
    study_hours:    document.getElementById('p-study').value,
    attendance:     document.getElementById('p-attend').value,
    prev_score:     document.getElementById('p-prev').value,
    sleep_hours:    document.getElementById('p-sleep').value,
    assignments:    document.getElementById('p-assign').value,
    extracurricular:document.getElementById('p-extra').value,
  };
  const r = await fetch('/api/predict', { method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(body) });
  const d = await r.json();
  const div = document.getElementById('predict-result');
  div.style.display = 'block';
  div.className = 'predict-result ' + (d.prediction === 'Pass' ? 'pass' : 'fail');
  const prob = d.prediction === 'Pass' ? d.probability_pass : d.probability_fail;
  const color = d.prediction === 'Pass' ? '#10b981' : '#f43f5e';
  div.innerHTML = `
    <div class="result-label" style="color:${color}">${d.prediction === 'Pass' ? '🎓' : '⚠️'} ${d.prediction}</div>
    <div class="result-prob">Confidence: ${prob}%</div>
    <div class="prob-bar"><div class="prob-fill" style="width:${prob}%;background:${color}"></div></div>
    <div style="margin-top:8px;font-size:.75rem;color:var(--muted)">Pass: ${d.probability_pass}% · Fail: ${d.probability_fail}%</div>`;
}

// ══════════════════════════════════════════════════
// INSIGHTS
// ══════════════════════════════════════════════════
async function initInsights() {
  const d = await api('/api/insights');
  const ecYes = d.extracurricular_effect[1] || d.extracurricular_effect['1'];
  const ecNo  = d.extracurricular_effect[0] || d.extracurricular_effect['0'];

  const cards = [
    { emoji:'🏆', title:'Top Department', value: d.top_department, desc:'Highest average final score across all departments.', color:'#6366f1' },
    { emoji:'🔑', title:'Strongest Predictor', value: d.strongest_predictor, desc:'Feature with the highest correlation to final exam score.', color:'#10b981' },
    { emoji:'🎓', title:'High Achievers', value: d.high_achievers + ' students', desc:'Scored 80 or above — top performers in the cohort.', color:'#f59e0b' },
    { emoji:'⚠️', title:'At Risk', value: d.at_risk + ' students', desc:'Scored below 45 — require immediate academic support.', color:'#f43f5e' },
    { emoji:'🏃', title:'Extracurricular Boost', value: '+' + (ecYes - ecNo).toFixed(1) + '% pass rate', desc:`Students in activities: ${ecYes}% pass vs ${ecNo}% without.`, color:'#06b6d4' },
    { emoji:'⚤', title:'Gender Score Gap', value: Object.entries(d.gender_avg_score).map(([k,v]) => `${k}: ${v}`).join(' vs '), desc:'Average final scores by gender.', color:'#8b5cf6' },
  ];

  document.getElementById('insights-grid').innerHTML = cards.map(c => `
    <div class="insight-card" style="--line-color:${c.color}">
      <div class="insight-emoji">${c.emoji}</div>
      <div class="insight-title">${c.title}</div>
      <div class="insight-value">${c.value}</div>
      <div class="insight-desc">${c.desc}</div>
    </div>`).join('');
}

// ── Init: load dashboard first ──────────────────
loadTab('dashboard');
