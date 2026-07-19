const FALLBACK = {
  eyebrow: 'Plugin Page',
  title: '通用生图控制台',
  description: '在 AstrBot WebUI 中提交生图任务、查看队列状态并下载生成结果。',
  refresh: '刷新',
  submit: '开始生成',
  submitting: '提交中...',
  uploading: '上传中...',
  'nav.overview': '概览',
  'nav.generate': '生成',
  'nav.tasks': '任务',
  'nav.gallery': '图库',
  'overview.statsTitle': '使用统计',
  'overview.totalTasks': '总任务',
  'overview.successRate': '成功率',
  'overview.totalImages': '生成图片',
  'overview.uniqueUsers': '用户数',
  'overview.dailyTrend': '每日任务量',
  'overview.statusChart': '任务状态',
  'overview.modelChart': '模型使用',
  'overview.userChart': '活跃用户',
  'overview.sourceChart': '任务来源',
  'overview.successMeta': '成功 {success} / 终态 {terminal}',
  'overview.imageMeta': '可用 {available}',
  'overview.modelMeta': '模型 {models}',
  'overview.modelSuccessRate': '成功率 {rate}%',
  'overview.noData': '暂无统计数据',
  'overview.avgDuration': '平均耗时 {duration}',
  'message.statsLoaded': '统计已刷新',
  'detail.source': '任务来源',
  'detail.userOrigin': '用户 UMO',
  'detail.model': '模型',
  'detail.previewUnavailable': '暂无预览',
  'detail.previewFailed': '预览失败',
  'status.model': '当前模型',
  'status.queue': '队列',
  'status.queued': '排队中',
  'status.pending': '等待中',
  'status.running': '生成中',
  'status.succeeded': '已完成',
  'status.failed': '失败',
  'status.cancelling': '取消中',
  'status.cancelled': '已取消',
  'form.eyebrow': 'Create',
  'form.title': '创建生图任务',
  'form.prompt': '提示词',
  'form.promptPlaceholder': '描述你想生成的画面，也可以只选择预设或人设。',
  'form.model': '模型',
  'form.imageCount': '生成数量',
  'form.aspectRatio': '宽高比',
  'form.resolution': '分辨率',
  'form.presets': '预设',
  'form.personas': '人设',
  'form.optional': '可选',
  'form.referenceImages': '参考图',
  'form.referenceHint': '支持 jpg/png/webp/gif/heic/heif，按配置限制大小。',
  'form.referenceUnsupported': '当前适配器未声明图生图能力。',
  'form.noPresets': '暂无预设',
  'form.noPersonas': '暂无人设',
  'form.noModels': '使用当前配置模型',
  'form.unspecified': '不指定',
  'form.resultEmptyTitle': '提交后在此查看结果',
  'form.resultEmptyDescription': '生成进度、错误信息和图片结果会显示在这里，无需离开当前页面。',
  'form.resultTitle': '本次生成',
  'form.resultCount': '{count} 个任务',
  'form.openTask': '在任务页查看',
  'form.clearResult': '关闭结果',
  'tasks.eyebrow': 'Queue',
  'tasks.title': '任务队列',
  'tasks.empty': '暂无任务',
  'tasks.createdAt': '创建',
  'tasks.progress': '进度',
  'tasks.results': '结果',
  'tasks.keywordPlaceholder': '任务 ID / 提示词 / 预设 / 人设 / 模型 / UMO',
  'tasks.sourceAll': '全部来源',
  'tasks.modelAll': '全部模型',
  'tasks.count': '共 {total} 条，当前第 {page}/{pages} 页',
  'tasks.prevPage': '上一页',
  'tasks.nextPage': '下一页',
  'tasks.pageInfo': '第 {page} / {pages} 页',
  'filter.all': '全部',
  'filter.active': '进行中',
  'detail.emptyTitle': '选择一个任务查看详情',
  'detail.emptyDescription': '任务结果、错误信息和下载入口会显示在这里。',
  'detail.title': '任务详情',
  'detail.cancel': '取消任务',
  'detail.download': '下载图片',
  'detail.taskId': '任务 ID',
  'detail.createdAt': '创建时间',
  'detail.startedAt': '开始时间',
  'detail.finishedAt': '结束时间',
  'detail.duration': '耗时',
  'detail.queued': '排队',
  'detail.requested': '请求数量',
  'detail.references': '参考图',
  'detail.preset': '预设',
  'detail.persona': '人设',
  'detail.template': '模板',
  'detail.none': '无',
  'detail.expandPrompt': '展开完整提示词',
  'detail.collapsePrompt': '收起提示词',
  'detail.message': '消息',
  'detail.error': '错误',
  'detail.items': '子任务',
  'detail.results': '生成结果',
  'detail.noResults': '暂无生成结果',
  'detail.noItems': '暂无子任务详情',
  'message.stateLoaded': '状态已刷新',
  'message.taskSubmitted': '任务已提交',
  'message.uploaded': '参考图已上传',
  'message.cancelled': '已请求取消任务',
  'message.downloadStarted': '已开始下载',
  'message.galleryLoaded': '图库已刷新',
  'gallery.eyebrow': 'Gallery',
  'gallery.title': '生成图库',
  'gallery.empty': '暂无生成图片',
  'gallery.unavailable': '文件已清理',
  'gallery.keywordPlaceholder': '任务 ID / 提示词 / 预设 / 模型',
  'gallery.modelAll': '全部模型',
  'gallery.model': '模型',
  'gallery.daysAll': '全部时间',
  'gallery.days1': '近 1 天',
  'gallery.days7': '近 7 天',
  'gallery.days30': '近 30 天',
  'gallery.count': '共 {total} 张，可用 {available} 张',
  'gallery.openTask': '查看任务',
  'lightbox.close': '关闭',
  'lightbox.open': '查看大图',
  'error.generic': '操作失败',
};

const PAGE_KEYS = Object.keys(FALLBACK);
const ASPECT_RATIOS = ['不指定', '1:1', '2:3', '3:2', '3:4', '4:3', '4:5', '5:4', '9:16', '16:9', '21:9'];
const RESOLUTIONS = ['不指定', '1K', '2K', '4K'];
const VALID_VIEWS = new Set(['overview', 'generate', 'tasks', 'gallery']);
const $ = (selector) => document.querySelector(selector);
const appState = {
  bridge: null,
  strings: { ...FALLBACK },
  pluginState: null,
  tasks: [],
  tasksTotal: 0,
  tasksOffset: 0,
  tasksLimit: 30,
  tasksModels: [],
  tasksSources: [],
  galleryItems: [],
  galleryModels: [],
  galleryTotal: 0,
  galleryAvailable: 0,
  stats: null,
  trendChart: { items: [], granularity: 'day' },
  loadingStats: false,
  selectedTaskId: '',
  selectedTask: null,
  generateTasks: [],
  activeGenerateTaskId: '',
  expandedPromptByTask: {},
  lightbox: { open: false, src: '', title: '', downloadEndpoint: '', downloadName: '', taskId: '' },
  previewCache: {},
  uploads: [],
  currentView: 'overview',
  loadingTasks: false,
  loadingGallery: false,
  loadingGenerateResults: false,
  refreshingState: false,
};

function createDevFallbackBridge() {
  // Local fallback only. Plugin Page iframe must use AstrBotPluginPage bridge;
  // direct fetch is blocked by CORS from opaque iframe origins.
  const apiBase = '/api/plugin/astrbot_plugin_image_generation/';
  return {
    ready: async () => undefined,
    getContext: async () => ({}),
    onContext: () => undefined,
    t: async (_key, fallback) => fallback,
    apiGet: async (endpoint, params = {}) => {
      const url = new URL(`${apiBase}${endpoint}`, window.location.origin);
      Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          url.searchParams.set(key, value);
        }
      });
      const response = await fetch(url, { credentials: 'same-origin' });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    },
    apiPost: async (endpoint, body = {}) => {
      const response = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin',
        body: JSON.stringify(body),
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    },
    upload: async (endpoint, file) => {
      const form = new FormData();
      form.append('file', file);
      const response = await fetch(`${apiBase}${endpoint}`, {
        method: 'POST',
        body: form,
        credentials: 'same-origin',
      });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return response.json();
    },
    download: async (endpoint) => {
      window.open(`${apiBase}${endpoint}`, '_blank', 'noopener,noreferrer');
    },
  };
}

function waitForPluginBridge(timeoutMs = 8000) {
  if (window.AstrBotPluginPage) {
    return Promise.resolve(window.AstrBotPluginPage);
  }
  return new Promise((resolve, reject) => {
    const started = Date.now();
    const timer = window.setInterval(() => {
      if (window.AstrBotPluginPage) {
        window.clearInterval(timer);
        resolve(window.AstrBotPluginPage);
        return;
      }
      if (Date.now() - started >= timeoutMs) {
        window.clearInterval(timer);
        // Outside iframe (local preview) allow fallback; inside iframe keep waiting error.
        if (window.parent && window.parent !== window) {
          reject(new Error('Plugin page bridge is not ready'));
          return;
        }
        resolve(createDevFallbackBridge());
      }
    }, 50);
  });
}

async function getBridge() {
  return waitForPluginBridge();
}

function t(key, vars = {}) {
  let text = appState.strings[key] || FALLBACK[key] || key;
  Object.entries(vars).forEach(([name, value]) => {
    text = text.replaceAll(`{${name}}`, String(value));
  });
  return text;
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#39;');
}

function formatBytes(bytes) {
  const value = Number(bytes || 0);
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

function formatSeconds(seconds) {
  if (seconds === null || seconds === undefined) return '--';
  const value = Number(seconds);
  if (!Number.isFinite(value)) return '--';
  if (value < 60) return `${value.toFixed(1)}s`;
  return `${Math.floor(value / 60)}m ${Math.round(value % 60)}s`;
}

function showToast(message, isError = false) {
  const toast = $('#toast');
  toast.textContent = message;
  toast.style.borderColor = isError ? 'var(--error)' : 'var(--border)';
  toast.classList.add('show');
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => toast.classList.remove('show'), 3200);
}

function applyTheme(context) {
  const rawTheme = String(context?.theme || context?.colorTheme || context?.appearance || '').toLowerCase();
  const dark =
    rawTheme.includes('dark') ||
    context?.dark === true ||
    context?.isDark === true ||
    context?.theme?.dark === true;
  const theme = dark ? 'dark' : 'light';
  document.documentElement.dataset.theme = theme;
  document.body.dataset.theme = theme;
  document.querySelector('.dashboard-page')?.classList.toggle('is-dark', dark);
}

async function loadStrings() {
  await Promise.all(
    PAGE_KEYS.map(async (key) => {
      try {
        appState.strings[key] = await appState.bridge.t(`pages.dashboard.${key}`, FALLBACK[key]);
      } catch {
        appState.strings[key] = FALLBACK[key];
      }
    }),
  );
}

function applyStaticText(root = document) {
  root.querySelectorAll('[data-i18n]').forEach((node) => {
    node.textContent = t(node.dataset.i18n);
  });
  root.querySelectorAll('[data-i18n-placeholder]').forEach((node) => {
    node.setAttribute('placeholder', t(node.dataset.i18nPlaceholder));
  });
}

async function apiGet(endpoint, params = {}) {
  if (!appState.bridge) {
    appState.bridge = await getBridge();
  }
  try {
    const result = await appState.bridge.apiGet(endpoint, params);
    if (result?.status === 'error') throw new Error(result.message || t('error.generic'));
    return result;
  } catch (error) {
    // If we accidentally captured a local fallback before bridge injection, recover once.
    if (window.AstrBotPluginPage && appState.bridge !== window.AstrBotPluginPage) {
      appState.bridge = window.AstrBotPluginPage;
      const result = await appState.bridge.apiGet(endpoint, params);
      if (result?.status === 'error') throw new Error(result.message || t('error.generic'));
      return result;
    }
    throw error;
  }
}

async function apiPost(endpoint, body = {}) {
  if (!appState.bridge) {
    appState.bridge = await getBridge();
  }
  try {
    const result = await appState.bridge.apiPost(endpoint, body);
    if (result?.status === 'error') throw new Error(result.message || t('error.generic'));
    return result;
  } catch (error) {
    if (window.AstrBotPluginPage && appState.bridge !== window.AstrBotPluginPage) {
      appState.bridge = window.AstrBotPluginPage;
      const result = await appState.bridge.apiPost(endpoint, body);
      if (result?.status === 'error') throw new Error(result.message || t('error.generic'));
      return result;
    }
    throw error;
  }
}

function getCheckedValues(containerId) {
  return Array.from(document.querySelectorAll(`#${containerId} input:checked`)).map((item) => item.value);
}

function setView(view, { pushHash = true } = {}) {
  const nextView = VALID_VIEWS.has(view) ? view : 'overview';
  appState.currentView = nextView;
  document.querySelectorAll('.tab-btn').forEach((button) => {
    button.classList.toggle('active', button.dataset.view === nextView);
  });
  document.querySelectorAll('[data-view-panel]').forEach((panel) => {
    panel.classList.toggle('active', panel.dataset.viewPanel === nextView);
  });
  if (pushHash) {
    const hash = nextView === 'overview' ? '#overview' : `#${nextView}`;
    if (window.location.hash !== hash) {
      window.location.hash = hash;
    }
  }
  if (nextView === 'tasks' && appState.selectedTaskId) {
    loadTaskDetail(appState.selectedTaskId);
  }
  if (nextView === 'generate' && appState.generateTasks.length) {
    loadGenerateResults({ silent: true });
  }
  if (nextView === 'gallery') {
    loadGallery();
  }
  if (nextView === 'overview') {
    loadStats();
  }
}

function renderSelect(select, values, selectedValue, emptyText) {
  if (!select) return;
  select.innerHTML = '';
  if (!values.length) {
    const option = document.createElement('option');
    option.value = '';
    option.textContent = emptyText;
    select.appendChild(option);
    return;
  }
  values.forEach((value) => {
    const option = document.createElement('option');
    option.value = value;
    option.textContent = value === '不指定' ? t('form.unspecified') : value;
    if (value === selectedValue) option.selected = true;
    select.appendChild(option);
  });
}

function renderChips(container, entries, selectedValues, emptyKey) {
  if (!container) return;
  if (!entries.length) {
    container.innerHTML = `<span class="empty-inline">${escapeHtml(t(emptyKey))}</span>`;
    return;
  }
  container.innerHTML = entries
    .map((entry) => {
      const checked = selectedValues.includes(entry.name) ? 'checked' : '';
      const active = selectedValues.includes(entry.name) ? 'is-checked' : '';
      const suffix = entry.has_image ? ' · IMG' : '';
      return `<label class="chip ${active}" title="${escapeHtml(entry.summary || '')}">
        <input class="chip-input" type="checkbox" value="${escapeHtml(entry.name)}" ${checked} />
        <span class="chip-check" aria-hidden="true"></span>
        <span class="chip-text">
          <strong>${escapeHtml(entry.name)}</strong>
          ${suffix ? `<span class="chip-suffix">${escapeHtml(suffix)}</span>` : ''}
        </span>
      </label>`;
    })
    .join('');
}

function renderUploads() {
  const list = $('#uploadList');
  if (!list) return;
  if (!appState.uploads.length) {
    list.innerHTML = '';
    return;
  }
  list.innerHTML = appState.uploads
    .map(
      (item, index) => `<span class="upload-pill">
        <strong>${escapeHtml(item.filename)}</strong>
        <small>${escapeHtml(formatBytes(item.size))}</small>
        <button type="button" data-upload-remove="${index}" aria-label="Remove">×</button>
      </span>`,
    )
    .join('');
}

function maxChartCount(items) {
  return Math.max(1, ...items.map((item) => Number(item.count || 0)));
}

const PIE_COLORS = [
  '#3c96ca',
  '#52c41a',
  '#faad14',
  '#ff4d4f',
  '#722ed1',
  '#13c2c2',
  '#eb2f96',
  '#2f54eb',
  '#a0d911',
  '#fa8c16',
];

function renderBarList(container, items, labelResolver, metaResolver) {
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-inline">${escapeHtml(t('overview.noData'))}</div>`;
    return;
  }
  const max = maxChartCount(items);
  container.innerHTML = items
    .map((item) => {
      const label = labelResolver ? labelResolver(item) : item.name;
      const count = Number(item.count || 0);
      const width = Math.max(6, Math.round((count / max) * 100));
      const meta = metaResolver ? metaResolver(item) : '';
      return `<div class="chart-row">
        <div class="chart-row-head">
          <strong title="${escapeHtml(label)}">${escapeHtml(label)}</strong>
          <span class="chart-row-value">
            <em>${escapeHtml(count)}</em>
            ${meta ? `<small>${escapeHtml(meta)}</small>` : ''}
          </span>
        </div>
        <div class="chart-track"><span style="width:${width}%"></span></div>
      </div>`;
    })
    .join('');
}

function describeArc(cx, cy, radius, startAngle, endAngle) {
  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? '0' : '1';
  return `M ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y}`;
}

function polarToCartesian(cx, cy, radius, angleInDegrees) {
  const angleInRadians = ((angleInDegrees - 90) * Math.PI) / 180;
  return {
    x: cx + radius * Math.cos(angleInRadians),
    y: cy + radius * Math.sin(angleInRadians),
  };
}

function renderDonutChart(container, items, labelResolver) {
  if (!container) return;
  if (!items.length) {
    container.innerHTML = `<div class="empty-inline">${escapeHtml(t('overview.noData'))}</div>`;
    return;
  }
  const total = items.reduce((sum, item) => sum + Math.max(0, Number(item.count || 0)), 0) || 1;
  const size = 168;
  const cx = size / 2;
  const cy = size / 2;
  const radius = 58;
  const stroke = 22;
  let cursor = 0;
  const slices = items.map((item, index) => {
    const count = Math.max(0, Number(item.count || 0));
    const ratio = count / total;
    const sweep = Math.max(ratio * 360, count > 0 ? 0.8 : 0);
    const start = cursor;
    const end = Math.min(360, cursor + sweep);
    cursor = end;
    const label = labelResolver ? labelResolver(item) : item.name;
    const color = PIE_COLORS[index % PIE_COLORS.length];
    const mid = (start + end) / 2;
    return {
      label,
      count,
      ratio,
      color,
      path:
        count <= 0
          ? ''
          : Math.abs(end - start) >= 359.9
            ? `M ${cx} ${cy - radius} A ${radius} ${radius} 0 1 1 ${cx - 0.01} ${cy - radius}`
            : describeArc(cx, cy, radius, start, end),
      mid,
    };
  });
  container.innerHTML = `
    <div class="pie-layout">
      <svg class="pie-svg" viewBox="0 0 ${size} ${size}" width="${size}" height="${size}" role="img">
        <circle class="pie-track" cx="${cx}" cy="${cy}" r="${radius}"></circle>
        ${slices
          .filter((slice) => slice.path)
          .map(
            (slice) => `<path class="pie-slice" d="${slice.path}" stroke="${slice.color}" stroke-width="${stroke}" fill="none" stroke-linecap="butt">
            <title>${escapeHtml(slice.label)}: ${escapeHtml(slice.count)} (${escapeHtml((slice.ratio * 100).toFixed(1))}%)</title>
          </path>`,
          )
          .join('')}
        <text class="pie-center-value" x="${cx}" y="${cy - 2}" text-anchor="middle">${escapeHtml(total)}</text>
        <text class="pie-center-label" x="${cx}" y="${cy + 16}" text-anchor="middle">total</text>
      </svg>
      <div class="pie-legend">
        ${slices
          .map(
            (slice) => `<div class="pie-legend-item">
            <span class="pie-dot" style="background:${slice.color}"></span>
            <strong title="${escapeHtml(slice.label)}">${escapeHtml(slice.label)}</strong>
            <em>${escapeHtml(slice.count)}</em>
            <small>${escapeHtml((slice.ratio * 100).toFixed(1))}%</small>
          </div>`,
          )
          .join('')}
      </div>
    </div>`;
}

function trendLabel(item, granularity) {
  if (item.label) return String(item.label);
  if (granularity === 'hour') {
    const hour = item.hour != null ? String(item.hour).padStart(2, '0') : String(item.key || '').slice(11, 13);
    return `${hour}:00`;
  }
  const raw = String(item.date || item.key || '');
  return raw.length >= 10 ? raw.slice(5) : raw || '--';
}

function trendTickStep(count, maxTicks = 8) {
  if (count <= maxTicks) return 1;
  return Math.ceil(count / maxTicks);
}

function niceTrendMax(value) {
  const n = Math.max(0, Number(value) || 0);
  if (n <= 4) return 4;
  if (n <= 10) return 10;
  const exponent = Math.floor(Math.log10(n));
  const base = 10 ** exponent;
  const scaled = n / base;
  const nice = scaled <= 2 ? 2 : scaled <= 5 ? 5 : 10;
  return nice * base;
}

function clampNumber(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function buildSmoothPath(points, minY, maxY) {
  if (!points.length) return '';
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;
  // Monotone cubic Hermite (Fritsch–Carlson) avoids overshoot below/above data range.
  const xs = points.map((p) => p.x);
  const ys = points.map((p) => p.y);
  const n = points.length;
  const dx = [];
  const dy = [];
  const slopes = [];
  for (let i = 0; i < n - 1; i += 1) {
    dx[i] = xs[i + 1] - xs[i] || 1;
    dy[i] = ys[i + 1] - ys[i];
    slopes[i] = dy[i] / dx[i];
  }
  const tangents = new Array(n).fill(0);
  tangents[0] = slopes[0] || 0;
  tangents[n - 1] = slopes[n - 2] || 0;
  for (let i = 1; i < n - 1; i += 1) {
    if (slopes[i - 1] * slopes[i] <= 0) {
      tangents[i] = 0;
    } else {
      const w1 = 2 * dx[i] + dx[i - 1];
      const w2 = dx[i] + 2 * dx[i - 1];
      tangents[i] = (w1 + w2) ? (w1 + w2) / (w1 / slopes[i - 1] + w2 / slopes[i]) : 0;
    }
  }
  let d = `M ${xs[0]} ${ys[0]}`;
  for (let i = 0; i < n - 1; i += 1) {
    const cp1x = xs[i] + dx[i] / 3;
    const cp1y = clampNumber(ys[i] + (tangents[i] * dx[i]) / 3, minY, maxY);
    const cp2x = xs[i + 1] - dx[i] / 3;
    const cp2y = clampNumber(ys[i + 1] - (tangents[i + 1] * dx[i]) / 3, minY, maxY);
    d += ` C ${cp1x} ${cp1y}, ${cp2x} ${cp2y}, ${xs[i + 1]} ${ys[i + 1]}`;
  }
  return d;
}

function bindTrendTooltip(container, points) {
  const tooltip = container.querySelector('.trend-tooltip');
  if (!tooltip) return;
  const hide = () => {
    tooltip.hidden = true;
    container.querySelectorAll('.trend-dot.is-active').forEach((node) => node.classList.remove('is-active'));
  };
  const showAt = (point, clientX, clientY) => {
    container.querySelectorAll('.trend-dot.is-active').forEach((node) => node.classList.remove('is-active'));
    const active = container.querySelector(`.trend-dot[data-index="${point.index}"]`);
    if (active) active.classList.add('is-active');
    tooltip.hidden = false;
    tooltip.innerHTML = `<strong>${escapeHtml(point.label)}</strong><span>${escapeHtml(point.count)}</span>`;
    const rect = container.getBoundingClientRect();
    const left = clampNumber(clientX - rect.left + 12, 8, Math.max(8, rect.width - 140));
    const top = clampNumber(clientY - rect.top - 44, 8, Math.max(8, rect.height - 52));
    tooltip.style.left = `${left}px`;
    tooltip.style.top = `${top}px`;
  };
  container.onmousemove = (event) => {
    const target = event.target.closest('[data-point-index]');
    if (target) {
      const point = points[Number(target.dataset.pointIndex)];
      if (!point) return hide();
      return showAt(point, event.clientX, event.clientY);
    }
    const rect = container.getBoundingClientRect();
    const x = event.clientX - rect.left;
    if (!points.length) return hide();
    let nearest = points[0];
    let best = Math.abs(points[0].x - x);
    for (const point of points) {
      const dist = Math.abs(point.x - x);
      if (dist < best) {
        best = dist;
        nearest = point;
      }
    }
    if (best > 28) return hide();
    showAt(nearest, event.clientX, event.clientY);
  };
  container.onmouseleave = hide;
}

function renderDailyTrend(items, granularity = 'day') {
  const container = $('#dailyTrendChart');
  if (!container) return;
  appState.trendChart = { items: items || [], granularity };
  if ($('#trendSummary')) {
    const total = (items || []).reduce((sum, item) => sum + Math.max(0, Number(item.count || 0)), 0);
    $('#trendSummary').textContent = total
      ? `${total} · ${granularity === 'hour' ? '24h' : `${items.length}d`}`
      : '';
  }
  if (!items.length) {
    container.innerHTML = `<div class="empty-inline">${escapeHtml(t('overview.noData'))}</div>`;
    return;
  }

  const width = Math.max(container.clientWidth || 720, 320);
  const height = 280;
  const pad = { top: 18, right: 18, bottom: 34, left: 42 };
  const plotW = Math.max(width - pad.left - pad.right, 1);
  const plotH = Math.max(height - pad.top - pad.bottom, 1);
  const minY = pad.top;
  const maxY = pad.top + plotH;
  const maxValue = niceTrendMax(maxChartCount(items));
  const yTicks = 4;
  const stepX = items.length > 1 ? plotW / (items.length - 1) : 0;
  const points = items.map((item, index) => {
    const count = Math.max(0, Number(item.count || 0));
    return {
      index,
      x: pad.left + index * stepX,
      y: maxY - (count / maxValue) * plotH,
      count,
      label: trendLabel(item, granularity),
      key: item.key || item.date || trendLabel(item, granularity),
    };
  });
  const linePath = buildSmoothPath(points, minY, maxY);
  const areaPath = points.length
    ? `${linePath} L ${points[points.length - 1].x} ${maxY} L ${points[0].x} ${maxY} Z`
    : '';
  const labelStep = trendTickStep(items.length, width < 720 ? 6 : 8);
  const yLines = Array.from({ length: yTicks + 1 }, (_, index) => {
    const value = Math.round((maxValue / yTicks) * index);
    const y = maxY - (value / maxValue) * plotH;
    return { value, y };
  });
  const gradientId = 'trendAreaFill';
  container.innerHTML = `
    <svg class="trend-svg" viewBox="0 0 ${width} ${height}" width="100%" height="${height}" role="img" aria-label="${escapeHtml(t('overview.dailyTrend'))}">
      <defs>
        <linearGradient id="${gradientId}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="var(--primary)" stop-opacity="0.22"></stop>
          <stop offset="100%" stop-color="var(--primary)" stop-opacity="0.02"></stop>
        </linearGradient>
      </defs>
      ${yLines
        .map(
          (tick) => `<g class="trend-grid-row">
          <line x1="${pad.left}" y1="${tick.y}" x2="${width - pad.right}" y2="${tick.y}"></line>
          <text x="${pad.left - 8}" y="${tick.y + 4}" text-anchor="end">${tick.value}</text>
        </g>`,
        )
        .join('')}
      <path class="trend-area" d="${areaPath}" fill="url(#${gradientId})"></path>
      <path class="trend-line" d="${linePath}"></path>
      ${points
        .map(
          (point) => `<g class="trend-point" data-point-index="${point.index}">
          <circle class="trend-hit" cx="${point.x}" cy="${point.y}" r="12"></circle>
          <circle class="trend-dot ${point.count > 0 ? '' : 'is-empty'}" data-index="${point.index}" cx="${point.x}" cy="${point.y}" r="3.5"></circle>
        </g>`,
        )
        .join('')}
      ${points
        .map((point, index) => {
          if (index !== 0 && index !== points.length - 1 && index % labelStep !== 0) return '';
          return `<text class="trend-xlabel" x="${point.x}" y="${height - 10}" text-anchor="middle">${escapeHtml(point.label)}</text>`;
        })
        .join('')}
    </svg>
    <div class="trend-tooltip" hidden></div>`;
  bindTrendTooltip(container, points);
}

function renderOverviewSummary() {
  const stats = appState.stats || {};
  const summary = stats.summary || {};
  const total = Number(summary.total_tasks || 0);
  const success = Number(summary.success_tasks || 0);
  const failed = Number(summary.failed_tasks || 0);
  const cancelled = Number(summary.cancelled_tasks || 0);
  const terminal = success + failed + cancelled;
  if ($('#statTotalTasks')) $('#statTotalTasks').textContent = String(total);
  if ($('#statSuccessRate')) $('#statSuccessRate').textContent = `${summary.success_rate ?? 0}%`;
  if ($('#statSuccessMeta')) {
    $('#statSuccessMeta').textContent = t('overview.successMeta', {
      success,
      terminal,
    });
  }
  if ($('#statTotalImages')) $('#statTotalImages').textContent = String(summary.total_images || 0);
  if ($('#statImageMeta')) {
    $('#statImageMeta').textContent = t('overview.imageMeta', {
      available: summary.available_images || 0,
    });
  }
  if ($('#statUniqueUsers')) $('#statUniqueUsers').textContent = String(summary.unique_users || 0);
  if ($('#statModelMeta')) {
    $('#statModelMeta').textContent = t('overview.modelMeta', {
      models: summary.unique_models || 0,
    });
  }
  renderDailyTrend(stats.trend || [], stats.trend_granularity || 'day');
  renderBarList(
    $('#modelChart'),
    stats.model_distribution || [],
    (item) => item.name,
    (item) =>
      t('overview.modelSuccessRate', {
        rate: item.success_rate ?? 0,
      }),
  );
  renderBarList($('#userChart'), stats.user_distribution || []);
  renderDonutChart($('#statusChart'), stats.status_distribution || [], (item) =>
    statusLabel(item.name, item.name),
  );
  renderDonutChart($('#sourceChart'), stats.source_distribution || []);
}

async function loadStats(showMessage = false) {
  if (appState.loadingStats) return;
  appState.loadingStats = true;
  try {
    appState.stats = await apiGet('page/stats', {
      days: $('#statsDaysFilter')?.value || '7',
    });
    renderOverviewSummary();
    if (showMessage) showToast(t('message.statsLoaded'));
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  } finally {
    appState.loadingStats = false;
  }
}

function renderState() {
  const state = appState.pluginState || {};
  if ($('#headerModelPill')) {
    $('#headerModelPill').textContent = state.current_model || t('status.model');
  }

  const currentPresets = getCheckedValues('presetList');
  const currentPersonas = getCheckedValues('personaList');
  const models = [...new Set([state.current_model, ...(state.available_models || [])].filter(Boolean))];
  renderSelect($('#modelSelect'), models, state.current_model, t('form.noModels'));
  renderSelect($('#aspectRatioSelect'), ASPECT_RATIOS, state.default_aspect_ratio || '不指定', t('form.unspecified'));
  renderSelect($('#resolutionSelect'), RESOLUTIONS, state.default_resolution || '不指定', t('form.unspecified'));
  if ($('#imageCountInput')) {
    $('#imageCountInput').value = state.default_image_count || 1;
    $('#imageCountInput').max = state.max_image_count || 1;
  }
  renderChips($('#presetList'), state.presets || [], currentPresets, 'form.noPresets');
  renderChips($('#personaList'), state.personas || [], currentPersonas, 'form.noPersonas');
  if ($('#referenceInput')) {
    $('#referenceInput').disabled = !state.supports_image_to_image;
  }
  const uploadHint = $('#uploadPanel small');
  if (uploadHint) {
    uploadHint.textContent = state.supports_image_to_image
      ? t('form.referenceHint')
      : t('form.referenceUnsupported');
  }
}

async function loadState(showMessage = false) {
  if (appState.refreshingState) return;
  appState.refreshingState = true;
  if ($('#refreshStateBtn')) $('#refreshStateBtn').disabled = true;
  try {
    appState.pluginState = await apiGet('page/state');
    renderState();
    await loadStats(false);
    if (showMessage) showToast(t('message.stateLoaded'));
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  } finally {
    appState.refreshingState = false;
    if ($('#refreshStateBtn')) $('#refreshStateBtn').disabled = false;
  }
}

function statusLabel(status, fallback) {
  const key = `status.${status}`;
  const localized = t(key);
  if (localized && localized !== key) return localized;
  return fallback || status;
}

function itemStatusMeta(item) {
  const status = item?.status || 'pending';
  const label = statusLabel(status, status);
  if (status === 'succeeded') {
    return `${t('tasks.results')}: ${item.result_count || 0}`;
  }
  if (status === 'failed') {
    return item.error || t('status.failed');
  }
  if (status === 'cancelled') {
    return item.error || t('status.cancelled');
  }
  if (status === 'running') {
    const retry = Number(item.retry_attempts || 0);
    const maxRetry = Number(item.max_retry_attempts || 0);
    if (maxRetry > 0) return `${t('status.running')} · ${retry}/${maxRetry}`;
    return t('status.running');
  }
  if (status === 'pending') {
    return t('status.pending');
  }
  return item.error || label;
}

function renderTaskRows(container, tasks) {
  if (!tasks.length) {
    container.innerHTML = `<div class="empty-state"><p>${escapeHtml(t('tasks.empty'))}</p></div>`;
    return;
  }
  container.innerHTML = tasks
    .map((task) => {
      const selected = task.task_id === appState.selectedTaskId ? 'active' : '';
      return `<article class="task-row ${selected}" data-task-id="${escapeHtml(task.task_id)}">
        <div>
          <div class="task-title">
            <span class="badge ${escapeHtml(task.status)}">${escapeHtml(statusLabel(task.status, task.status_label))}</span>
            <strong>${escapeHtml(task.task_id)}</strong>
          </div>
          <p class="task-prompt">${escapeHtml(task.prompt_summary || '--')}</p>
          <div class="task-meta">
            <span>${escapeHtml(t('detail.source'))}: ${escapeHtml(task.source || '--')}</span>
            <span>${escapeHtml(t('tasks.createdAt'))}: ${escapeHtml(task.created_at || '--')}</span>
            <span>${escapeHtml(t('tasks.results'))}: ${escapeHtml(task.result_count || 0)}/${escapeHtml(task.requested_count || 0)}</span>
          </div>
        </div>
        <div class="progress" title="${escapeHtml(t('tasks.progress'))}"><span style="--progress:${Number(task.progress_percent || 0)}%"></span></div>
      </article>`;
    })
    .join('');
}

function renderEmptyDetail() {
  if (!$('#detailPanel')) return;
  $('#detailPanel').innerHTML = `<div class="empty-state" id="emptyDetail">
      <div class="empty-orb"></div>
      <h2>${escapeHtml(t('detail.emptyTitle'))}</h2>
      <p>${escapeHtml(t('detail.emptyDescription'))}</p>
    </div>`;
}

function renderTaskFilterOptions() {
  const sourceSelect = $('#tasksSourceFilter');
  if (sourceSelect) {
    const current = sourceSelect.value || '';
    const options = [
      `<option value="">${escapeHtml(t('tasks.sourceAll'))}</option>`,
      ...appState.tasksSources.map(
        (source) =>
          `<option value="${escapeHtml(source)}" ${source === current ? 'selected' : ''}>${escapeHtml(source)}</option>`,
      ),
    ];
    sourceSelect.innerHTML = options.join('');
    if (current && !appState.tasksSources.includes(current)) {
      sourceSelect.value = '';
    } else {
      sourceSelect.value = current;
    }
  }

  const modelSelect = $('#tasksModelFilter');
  if (modelSelect) {
    const current = modelSelect.value || '';
    const options = [
      `<option value="">${escapeHtml(t('tasks.modelAll'))}</option>`,
      ...appState.tasksModels.map(
        (model) =>
          `<option value="${escapeHtml(model)}" ${model === current ? 'selected' : ''}>${escapeHtml(model)}</option>`,
      ),
    ];
    modelSelect.innerHTML = options.join('');
    if (current && !appState.tasksModels.includes(current)) {
      modelSelect.value = '';
    } else {
      modelSelect.value = current;
    }
  }
}

function renderTasksMeta() {
  const countNode = $('#tasksCount');
  const pagination = $('#tasksPagination');
  const pageInfo = $('#tasksPageInfo');
  const prevBtn = $('#tasksPrevBtn');
  const nextBtn = $('#tasksNextBtn');
  const total = Number(appState.tasksTotal || 0);
  const limit = Math.max(1, Number(appState.tasksLimit || 30));
  const offset = Math.max(0, Number(appState.tasksOffset || 0));
  const pages = Math.max(1, Math.ceil(total / limit) || 1);
  const page = total === 0 ? 1 : Math.floor(offset / limit) + 1;

  if (countNode) {
    countNode.textContent = t('tasks.count', { total, page, pages });
  }
  if (pageInfo) {
    pageInfo.textContent = t('tasks.pageInfo', { page, pages });
  }
  if (pagination) {
    pagination.hidden = total <= limit && page <= 1;
  }
  if (prevBtn) prevBtn.disabled = page <= 1 || appState.loadingTasks;
  if (nextBtn) nextBtn.disabled = page >= pages || appState.loadingTasks;
}

function renderTaskList() {
  const container = $('#taskList');
  if (!container) return;
  renderTasksMeta();
  if (!appState.tasks.length) {
    container.innerHTML = `<div class="empty-state"><p>${escapeHtml(t('tasks.empty'))}</p></div>`;
    if (!appState.selectedTaskId) {
      renderEmptyDetail();
    }
  } else {
    renderTaskRows(container, appState.tasks);
  }
}

function formatNames(values, fallback = '--') {
  if (Array.isArray(values) && values.length) {
    return values.join('、');
  }
  const text = String(values || '').trim();
  return text || fallback;
}

async function loadTasks({ resetOffset = false } = {}) {
  if (appState.loadingTasks) return;
  appState.loadingTasks = true;
  if ($('#refreshTasksBtn')) $('#refreshTasksBtn').disabled = true;
  try {
    if (resetOffset) appState.tasksOffset = 0;
    const limit = Math.max(1, Number($('#limitSelect')?.value || appState.tasksLimit || 30));
    appState.tasksLimit = limit;
    const result = await apiGet('page/tasks', {
      status: $('#statusFilter')?.value || 'all',
      source: $('#tasksSourceFilter')?.value || '',
      model: $('#tasksModelFilter')?.value || '',
      days: $('#tasksDaysFilter')?.value || '0',
      keyword: $('#tasksKeyword')?.value?.trim() || '',
      limit,
      offset: appState.tasksOffset,
    });
    appState.tasks = result.tasks || [];
    appState.tasksTotal = Number(result.total || 0);
    appState.tasksLimit = Number(result.limit || limit);
    let nextOffset = Number(result.offset || appState.tasksOffset || 0);
    if (appState.tasksTotal > 0 && nextOffset >= appState.tasksTotal) {
      nextOffset = Math.max(0, (Math.ceil(appState.tasksTotal / appState.tasksLimit) - 1) * appState.tasksLimit);
    }
    if (appState.tasksTotal === 0) nextOffset = 0;
    appState.tasksOffset = nextOffset;
    appState.tasksModels = Array.isArray(result.models) ? result.models : [];
    appState.tasksSources = Array.isArray(result.sources) ? result.sources : [];
    renderTaskFilterOptions();

    if (!appState.selectedTaskId && appState.tasks.length) {
      appState.selectedTaskId = appState.tasks[0].task_id;
    }
    renderTaskList();
    if (appState.currentView === 'tasks' && appState.selectedTaskId) {
      const selected = appState.tasks.find((task) => task.task_id === appState.selectedTaskId);
      const shouldRefreshDetail =
        !appState.selectedTask ||
        appState.selectedTask.task_id !== appState.selectedTaskId ||
        selected?.active ||
        appState.selectedTask.active;
      if (shouldRefreshDetail) {
        await loadTaskDetail(appState.selectedTaskId, { silent: true });
      }
    } else if (appState.currentView === 'tasks' && !appState.selectedTaskId) {
      renderEmptyDetail();
    }
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  } finally {
    appState.loadingTasks = false;
    if ($('#refreshTasksBtn')) $('#refreshTasksBtn').disabled = false;
    renderTasksMeta();
  }
}

function renderDetail(task) {
  const active = task.active;
  const expanded = Boolean(appState.expandedPromptByTask[task.task_id]);
  const resultCards = (task.result_images || [])
    .map(
      (image) => {
        const available = image.available !== false;
        const title = image.filename || `#${image.index}`;
        return `<article class="result-card image-card">
        <button class="media-frame result-thumb ${available ? '' : 'is-missing'}" type="button"
          data-preview-endpoint="${escapeHtml(image.preview_endpoint || '')}"
          data-download-endpoint="${escapeHtml(image.download_endpoint || '')}"
          data-download-name="${escapeHtml(image.filename || '')}"
          data-task-id="${escapeHtml(task.task_id)}"
          data-available="${available ? '1' : '0'}"
          ${available ? '' : 'disabled'}
          title="${escapeHtml(t('lightbox.open'))}">
          <span>${escapeHtml(available ? title : t('detail.previewUnavailable'))}</span>
        </button>
        <div class="result-card-body">
          <div class="result-card-meta">
            <strong title="${escapeHtml(title)}">${escapeHtml(title)}</strong>
            <small>${escapeHtml(formatBytes(image.size || 0))}</small>
          </div>
          <div class="result-card-actions">
            <button class="btn subtle" type="button"
              data-preview-endpoint="${escapeHtml(image.preview_endpoint || '')}"
              data-download-endpoint="${escapeHtml(image.download_endpoint || '')}"
              data-download-name="${escapeHtml(image.filename || '')}"
              data-task-id="${escapeHtml(task.task_id)}"
              data-available="${available ? '1' : '0'}"
              ${available ? '' : 'disabled'}>${escapeHtml(t('lightbox.open'))}</button>
            <button class="btn primary" type="button"
              data-download-endpoint="${escapeHtml(image.download_endpoint || '')}"
              data-download-name="${escapeHtml(image.filename || '')}"
              ${available ? '' : 'disabled'}>${escapeHtml(t('detail.download'))}</button>
          </div>
        </div>
      </article>`;
      },
    )
    .join('');
  const itemCards = (task.items || [])
    .map((item) => {
      const status = item.status || 'pending';
      return `<article class="item-card">
        <div class="item-card-head">
          <strong>#${escapeHtml(item.index)}</strong>
          <span class="badge ${escapeHtml(status)}">${escapeHtml(statusLabel(status, status))}</span>
        </div>
        <small>${escapeHtml(itemStatusMeta(item))}</small>
      </article>`;
    })
    .join('');
  const promptSummary = task.prompt_summary || '--';
  const fullPrompt = String(task.prompt || '').trim();
  const hasExpandablePrompt = Boolean(fullPrompt && fullPrompt !== promptSummary);
  const promptBlock = hasExpandablePrompt
    ? `<div class="prompt-block">
        <p class="task-prompt" id="detailPromptSummary" ${expanded ? 'hidden' : ''}>${escapeHtml(promptSummary)}</p>
        <button class="btn subtle prompt-toggle" id="togglePromptBtn" type="button" data-expanded="${expanded ? '1' : '0'}">${escapeHtml(expanded ? t('detail.collapsePrompt') : t('detail.expandPrompt'))}</button>
        <pre class="prompt-full" id="detailPromptFull" ${expanded ? '' : 'hidden'}>${escapeHtml(fullPrompt)}</pre>
      </div>`
    : fullPrompt
      ? `<div class="prompt-block"><pre class="prompt-full is-static">${escapeHtml(fullPrompt)}</pre></div>`
      : `<p class="task-prompt">${escapeHtml(promptSummary)}</p>`;

  const presetsText = formatNames(task.presets, '');
  const personasText = formatNames(task.personas, '');
  const templateSummary = String(task.template_summary || task.preset || '').trim();
  const hasPreset = Boolean(presetsText);
  const hasPersona = Boolean(personasText);
  const hasTemplateFallback = !hasPreset && !hasPersona && Boolean(templateSummary);

  if (!$('#detailPanel')) return;
  $('#detailPanel').innerHTML = `<div class="detail-shell">
    <div class="detail-header">
      <div class="detail-heading">
        <p class="section-eyebrow">${escapeHtml(t('detail.title'))}</p>
        <h2>${escapeHtml(task.task_id)}</h2>
      </div>
      <div class="detail-actions">
        <span class="badge ${escapeHtml(task.status)}">${escapeHtml(statusLabel(task.status, task.status_label))}</span>
        ${active ? `<button class="btn danger" id="cancelTaskBtn" type="button">${escapeHtml(t('detail.cancel'))}</button>` : ''}
      </div>
    </div>
    ${promptBlock}
    <div class="detail-grid">
      <div class="detail-stat"><span>${escapeHtml(t('status.queue'))}</span><strong>${escapeHtml(statusLabel(task.status, task.status_label))}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.source'))}</span><strong>${escapeHtml(task.source || '--')}</strong></div>
      <div class="detail-stat detail-stat--wide"><span>${escapeHtml(t('detail.userOrigin'))}</span><strong title="${escapeHtml(task.unified_msg_origin || '')}">${escapeHtml(task.unified_msg_origin || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.model'))}</span><strong>${escapeHtml(task.model || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('form.aspectRatio'))}</span><strong>${escapeHtml(task.aspect_ratio || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('form.resolution'))}</span><strong>${escapeHtml(task.resolution || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.requested'))}</span><strong>${escapeHtml(task.result_count || 0)} / ${escapeHtml(task.requested_count || 0)}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.references'))}</span><strong>${escapeHtml(task.reference_image_count || 0)}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.preset'))}</span><strong>${escapeHtml(hasPreset ? presetsText : t('detail.none'))}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.persona'))}</span><strong>${escapeHtml(hasPersona ? personasText : t('detail.none'))}</strong></div>
      ${
        hasTemplateFallback
          ? `<div class="detail-stat detail-stat--wide"><span>${escapeHtml(t('detail.template'))}</span><strong>${escapeHtml(templateSummary)}</strong></div>`
          : ''
      }
      <div class="detail-stat"><span>${escapeHtml(t('detail.createdAt'))}</span><strong>${escapeHtml(task.created_at || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.startedAt'))}</span><strong>${escapeHtml(task.started_at || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.finishedAt'))}</span><strong>${escapeHtml(task.finished_at || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.duration'))}</span><strong>${escapeHtml(formatSeconds(task.duration_seconds))}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.queued'))}</span><strong>${escapeHtml(formatSeconds(task.queued_seconds))}</strong></div>
      <div class="detail-stat detail-stat--wide"><span>${escapeHtml(t('detail.taskId'))}</span><strong title="${escapeHtml(task.task_id || '')}">${escapeHtml(task.task_id || '--')}</strong></div>
    </div>
    ${task.message ? `<div class="detail-message"><strong>${escapeHtml(t('detail.message'))}</strong><br />${escapeHtml(task.message)}</div>` : ''}
    ${task.error ? `<div class="detail-error"><strong>${escapeHtml(t('detail.error'))}</strong><br />${escapeHtml(task.error)}</div>` : ''}
    <div class="detail-section">
      <div class="section-heading"><h2>${escapeHtml(t('detail.results'))}</h2></div>
      <div class="result-grid">${resultCards || `<span class="empty-inline">${escapeHtml(t('detail.noResults'))}</span>`}</div>
    </div>
    <div class="detail-section">
      <div class="section-heading"><h2>${escapeHtml(t('detail.items'))}</h2></div>
      <div class="item-grid">${itemCards || `<span class="empty-inline">${escapeHtml(t('detail.noItems'))}</span>`}</div>
    </div>
  </div>`;
  hydrateDetailPreviews();
}

async function loadPreviewData(endpoint) {
  if (!endpoint) return null;
  if (appState.previewCache[endpoint]) return appState.previewCache[endpoint];
  const preview = await apiGet(endpoint);
  if (preview?.data_url) appState.previewCache[endpoint] = preview;
  return preview;
}

function openLightbox({ src = '', title = '', downloadEndpoint = '', downloadName = '', taskId = '' } = {}) {
  appState.lightbox = {
    open: true,
    src,
    title,
    downloadEndpoint,
    downloadName,
    taskId,
  };
  const box = $('#imageLightbox');
  const img = $('#lightboxImage');
  const titleNode = $('#lightboxTitle');
  if (!box || !img || !titleNode) return;
  img.src = src || '';
  img.alt = title || '';
  titleNode.textContent = title || '--';
  box.hidden = false;
  document.body.classList.add('lightbox-open');
}

function closeLightbox() {
  appState.lightbox.open = false;
  const box = $('#imageLightbox');
  const img = $('#lightboxImage');
  if (img) img.src = '';
  if (box) box.hidden = true;
  document.body.classList.remove('lightbox-open');
}

async function openImagePreview(target) {
  if (!target) return;
  const endpoint = target.dataset.previewEndpoint || '';
  const available = target.dataset.available !== '0';
  if (!available || !endpoint) {
    showToast(t('detail.previewUnavailable'), true);
    return;
  }
  try {
    const existingImg = target.querySelector('img');
    let src = existingImg?.src || '';
    let title = target.dataset.downloadName || existingImg?.alt || '';
    if (!src) {
      const preview = await loadPreviewData(endpoint);
      if (!preview?.data_url) {
        showToast(t('detail.previewUnavailable'), true);
        return;
      }
      src = preview.data_url;
      title = preview.filename || title;
      target.innerHTML = `<img src="${src}" alt="${escapeHtml(title || '')}" loading="lazy" />`;
      target.dataset.loaded = '1';
    }
    openLightbox({
      src,
      title,
      downloadEndpoint: target.dataset.downloadEndpoint || '',
      downloadName: target.dataset.downloadName || title || 'image.png',
      taskId: target.dataset.taskId || '',
    });
  } catch (error) {
    showToast(error.message || t('detail.previewFailed'), true);
  }
}

async function hydratePreviewFrames(selector, { limit = 0 } = {}) {
  const thumbs = Array.from(document.querySelectorAll(selector));
  const targets = limit > 0 ? thumbs.slice(0, limit) : thumbs;
  for (const thumb of targets) {
    const endpoint = thumb.dataset.previewEndpoint;
    if (!endpoint || thumb.dataset.loaded === '1') continue;
    thumb.dataset.loaded = '1';
    try {
      const preview = await loadPreviewData(endpoint);
      if (!preview?.data_url) {
        thumb.classList.add('is-missing');
        thumb.innerHTML = `<span>${escapeHtml(t('detail.previewUnavailable'))}</span>`;
        continue;
      }
      thumb.innerHTML = `<img src="${preview.data_url}" alt="${escapeHtml(preview.filename || '')}" loading="lazy" />`;
    } catch {
      thumb.classList.add('is-missing');
      thumb.innerHTML = `<span>${escapeHtml(t('detail.previewFailed'))}</span>`;
    }
  }
}

async function hydrateDetailPreviews() {
  await hydratePreviewFrames('#detailPanel .result-thumb[data-available="1"]');
}

async function hydrateGeneratePreviews() {
  await hydratePreviewFrames('#generateResultPanel .result-thumb[data-available="1"]');
}

async function hydrateGalleryPreviews() {
  await hydratePreviewFrames('.gallery-thumb[data-available="1"]', { limit: 48 });
}


function detailNeedsRerender(prevTask, nextTask) {
  if (!prevTask || !nextTask) return true;
  if (prevTask.task_id !== nextTask.task_id) return true;
  if (prevTask.status !== nextTask.status) return true;
  if (prevTask.active !== nextTask.active) return true;
  if ((prevTask.result_count || 0) !== (nextTask.result_count || 0)) return true;
  if ((prevTask.message || '') !== (nextTask.message || '')) return true;
  if ((prevTask.error || '') !== (nextTask.error || '')) return true;
  if ((prevTask.progress_percent || 0) !== (nextTask.progress_percent || 0)) return true;
  const prevItems = JSON.stringify(prevTask.items || []);
  const nextItems = JSON.stringify(nextTask.items || []);
  if (prevItems !== nextItems) return true;
  const prevImages = JSON.stringify(prevTask.result_images || []);
  const nextImages = JSON.stringify(nextTask.result_images || []);
  if (prevImages !== nextImages) return true;
  return false;
}

async function loadTaskDetail(taskId, { silent = false } = {}) {
  if (!taskId) return;
  try {
    const result = await apiGet(`page/tasks/${encodeURIComponent(taskId)}`);
    const nextTask = result.task;
    const shouldRender =
      appState.currentView === 'tasks' && detailNeedsRerender(appState.selectedTask, nextTask);
    appState.selectedTask = nextTask;
    if (shouldRender) {
      renderDetail(nextTask);
    }
  } catch (error) {
    if (!silent) showToast(error.message || t('error.generic'), true);
  }
}

function renderGenerateResultEmpty() {
  const panel = $('#generateResultPanel');
  if (!panel) return;
  panel.innerHTML = `<div class="empty-state" id="generateResultEmpty">
      <div class="empty-orb"></div>
      <h2>${escapeHtml(t('form.resultEmptyTitle'))}</h2>
      <p>${escapeHtml(t('form.resultEmptyDescription'))}</p>
    </div>`;
}

function renderGenerateResultCard(task) {

  const active = Boolean(task.active);
  const progress = Math.max(0, Math.min(100, Number(task.progress_percent || 0)));
  const resultCards = (task.result_images || [])
    .map((image) => {
      const available = image.available !== false;
      const title = image.filename || `#${image.index}`;
      return `<article class="result-card image-card">
        <button class="media-frame result-thumb ${available ? '' : 'is-missing'}" type="button"
          data-preview-endpoint="${escapeHtml(image.preview_endpoint || '')}"
          data-download-endpoint="${escapeHtml(image.download_endpoint || '')}"
          data-download-name="${escapeHtml(image.filename || '')}"
          data-task-id="${escapeHtml(task.task_id)}"
          data-available="${available ? '1' : '0'}"
          ${available ? '' : 'disabled'}
          title="${escapeHtml(t('lightbox.open'))}">
          <span>${escapeHtml(available ? title : t('detail.previewUnavailable'))}</span>
        </button>
        <div class="result-card-body">
          <div class="result-card-meta">
            <strong title="${escapeHtml(title)}">${escapeHtml(title)}</strong>
            <small>${escapeHtml(formatBytes(image.size || 0))}</small>
          </div>
          <div class="result-card-actions">
            <button class="btn subtle" type="button"
              data-preview-endpoint="${escapeHtml(image.preview_endpoint || '')}"
              data-download-endpoint="${escapeHtml(image.download_endpoint || '')}"
              data-download-name="${escapeHtml(image.filename || '')}"
              data-task-id="${escapeHtml(task.task_id)}"
              data-available="${available ? '1' : '0'}"
              ${available ? '' : 'disabled'}>${escapeHtml(t('lightbox.open'))}</button>
            <button class="btn primary" type="button"
              data-download-endpoint="${escapeHtml(image.download_endpoint || '')}"
              data-download-name="${escapeHtml(image.filename || '')}"
              ${available ? '' : 'disabled'}>${escapeHtml(t('detail.download'))}</button>
          </div>
        </div>
      </article>`;
    })
    .join('');

  const presetsText = formatNames(task.presets, '');
  const personasText = formatNames(task.personas, '');

  return `<article class="generate-result-card" data-generate-task-id="${escapeHtml(task.task_id)}">
  <div class="generate-result-shell">
    <div class="generate-result-header">
      <div class="generate-result-heading">
        <p class="section-eyebrow">${escapeHtml(t('form.resultTitle'))}</p>
        <h2 title="${escapeHtml(task.task_id || '')}">${escapeHtml(task.task_id || '--')}</h2>
      </div>
      <div class="generate-result-actions">
        <span class="badge ${escapeHtml(task.status)}">${escapeHtml(statusLabel(task.status, task.status_label))}</span>
        ${active ? `<button class="btn danger" type="button" data-cancel-generate-task="${escapeHtml(task.task_id)}">${escapeHtml(t('detail.cancel'))}</button>` : ''}
        <button class="btn subtle" type="button" data-open-generate-task="${escapeHtml(task.task_id)}">${escapeHtml(t('form.openTask'))}</button>
        <button class="btn subtle" type="button" data-clear-generate-task="${escapeHtml(task.task_id)}">${escapeHtml(t('form.clearResult'))}</button>
      </div>
    </div>
    <div class="generate-progress" title="${escapeHtml(t('tasks.progress'))}">
      <span style="--progress:${progress}%"></span>
    </div>
    <div class="generate-result-meta">
      <div class="detail-stat"><span>${escapeHtml(t('detail.model'))}</span><strong>${escapeHtml(task.model || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('tasks.results'))}</span><strong>${escapeHtml(task.result_count || 0)} / ${escapeHtml(task.requested_count || 0)}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('form.aspectRatio'))}</span><strong>${escapeHtml(task.aspect_ratio || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('form.resolution'))}</span><strong>${escapeHtml(task.resolution || '--')}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.preset'))}</span><strong>${escapeHtml(presetsText || t('detail.none'))}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.persona'))}</span><strong>${escapeHtml(personasText || t('detail.none'))}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.duration'))}</span><strong>${escapeHtml(formatSeconds(task.duration_seconds))}</strong></div>
      <div class="detail-stat"><span>${escapeHtml(t('detail.createdAt'))}</span><strong>${escapeHtml(task.created_at || '--')}</strong></div>
    </div>
    ${task.message ? `<div class="detail-message"><strong>${escapeHtml(t('detail.message'))}</strong><br />${escapeHtml(task.message)}</div>` : ''}
    ${task.error ? `<div class="detail-error"><strong>${escapeHtml(t('detail.error'))}</strong><br />${escapeHtml(task.error)}</div>` : ''}
    <div class="detail-section">
      <div class="section-heading"><h2>${escapeHtml(t('detail.results'))}</h2></div>
      <div class="result-grid">${resultCards || `<span class="empty-inline">${escapeHtml(t('detail.noResults'))}</span>`}</div>
    </div>
  </div>
  </article>`;
}

function renderGenerateResults() {
  const panel = $('#generateResultPanel');
  if (!panel) return;
  if (!appState.generateTasks.length) {
    renderGenerateResultEmpty();
    return;
  }
  const activeTask =
    appState.generateTasks.find((task) => task.task_id === appState.activeGenerateTaskId) ||
    appState.generateTasks[0];
  appState.activeGenerateTaskId = activeTask.task_id;
  const taskTabs = appState.generateTasks
    .map((task, index) => {
      const selected = task.task_id === activeTask.task_id;
      const progress = Math.max(0, Math.min(100, Number(task.progress_percent || 0)));
      const label = task.prompt_summary || `${t('form.resultTitle')} ${index + 1}`;
      return `<button class="generate-task-tab ${selected ? 'active' : ''}" type="button"
        data-select-generate-task="${escapeHtml(task.task_id)}"
        title="${escapeHtml(task.task_id)}">
        <span class="badge ${escapeHtml(task.status)}">${escapeHtml(statusLabel(task.status, task.status_label))}</span>
        <span class="generate-task-tab-label">${escapeHtml(label)}</span>
        <span class="generate-task-tab-progress" style="--progress:${progress}%"></span>
      </button>`;
    })
    .join('');
  panel.innerHTML = `<div class="generate-workspace">
    <div class="generate-workspace-header">
      <p class="section-eyebrow">${escapeHtml(t('form.resultTitle'))}</p>
      <span class="generate-task-count">${escapeHtml(t('form.resultCount', { count: appState.generateTasks.length }))}</span>
    </div>
    <div class="generate-task-tabs" role="tablist">${taskTabs}</div>
    <div class="generate-results-list">${renderGenerateResultCard(activeTask)}</div>
  </div>`;
  hydrateGeneratePreviews();
}

async function loadGenerateResults({ silent = false } = {}) {
  if (!appState.generateTasks.length || appState.loadingGenerateResults) return;
  appState.loadingGenerateResults = true;
  try {
    const refreshedTasks = await Promise.all(
      appState.generateTasks.map(async (task) => {
        try {
          const result = await apiGet(`page/tasks/${encodeURIComponent(task.task_id)}`);
          return result.task || task;
        } catch {
          return task;
        }
      }),
    );
    const shouldRender = refreshedTasks.some((task, index) =>
      detailNeedsRerender(appState.generateTasks[index], task),
    );
    appState.generateTasks = refreshedTasks;
    if (appState.currentView === 'generate' && shouldRender) {
      renderGenerateResults();
    }
  } catch (error) {
    if (!silent) showToast(error.message || t('error.generic'), true);
  } finally {
    appState.loadingGenerateResults = false;
  }
}

function clearGenerateResult(taskId) {
  appState.generateTasks = appState.generateTasks.filter((task) => task.task_id !== taskId);
  if (appState.activeGenerateTaskId === taskId) {
    appState.activeGenerateTaskId = appState.generateTasks[0]?.task_id || '';
  }
  renderGenerateResults();
}

async function cancelGenerateTask(taskId) {
  if (!taskId) return;
  try {
    await apiPost(`page/tasks/${encodeURIComponent(taskId)}/cancel`, {});
    showToast(t('message.cancelled'));
    await loadGenerateResults({ silent: true });
    await loadTasks();
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  }
}

async function submitTask(event) {
  event.preventDefault();
  const button = $('#submitBtn');
  if (button) {
    button.disabled = true;
    button.textContent = t('submitting');
  }
  try {
    const result = await apiPost('page/generate', {
      prompt: $('#promptInput')?.value?.trim() || '',
      model: $('#modelSelect')?.value || '',
      image_count: $('#imageCountInput')?.value || 1,
      aspect_ratio: $('#aspectRatioSelect')?.value || '不指定',
      resolution: $('#resolutionSelect')?.value || '不指定',
      presets: getCheckedValues('presetList'),
      personas: getCheckedValues('personaList'),
      reference_tokens: appState.uploads.map((item) => item.token),
    });
    const taskId = result.task_id || '';
    appState.selectedTaskId = taskId || appState.selectedTaskId;
    const submittedTask = result.task || (taskId ? { task_id: taskId, active: true } : null);
    if (submittedTask) {
      appState.generateTasks = [
        submittedTask,
        ...appState.generateTasks.filter((task) => task.task_id !== submittedTask.task_id),
      ];
      appState.activeGenerateTaskId = submittedTask.task_id;
    }
    showToast(t('message.taskSubmitted'));
    renderGenerateResults();
    // Keep generate view; only refresh queue in background.
    loadTasks({ resetOffset: true });
    if (taskId) {
      // Follow progress/results while staying on the generate page.
      loadGenerateResults({ silent: true });
    }
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  } finally {
    if (button) {
      button.disabled = false;
      button.textContent = t('submit');
    }
  }
}

async function uploadReferences(files) {
  if (!files.length) return;
  const input = $('#referenceInput');
  if (input) input.disabled = true;
  showToast(t('uploading'));
  try {
    for (const file of files) {
      const result = await appState.bridge.upload('page/reference/upload', file);
      if (result?.status === 'error') throw new Error(result.message || t('error.generic'));
      appState.uploads.push(result);
    }
    renderUploads();
    showToast(t('message.uploaded'));
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  } finally {
    if (input) {
      input.value = '';
      input.disabled = !(appState.pluginState?.supports_image_to_image);
    }
  }
}

async function cancelSelectedTask() {
  if (!appState.selectedTaskId) return;
  try {
    await apiPost(`page/tasks/${encodeURIComponent(appState.selectedTaskId)}/cancel`, {});
    showToast(t('message.cancelled'));
    await loadTasks();
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  }
}

async function downloadImage(endpoint, filename) {
  try {
    await appState.bridge.download(endpoint, {}, filename || 'image.png');
    showToast(t('message.downloadStarted'));
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  }
}

function renderGalleryModelFilter(models) {
  const select = $('#galleryModelFilter');
  if (!select) return;
  const current = select.value || '';
  const options = ['', ...(models || []).filter(Boolean)];
  select.innerHTML = options
    .map((model) => {
      const value = model || '';
      const label = value || t('gallery.modelAll');
      const selected = value === current ? 'selected' : '';
      return `<option value="${escapeHtml(value)}" ${selected}>${escapeHtml(label)}</option>`;
    })
    .join('');
  if (current && !options.includes(current)) {
    select.value = '';
  }
}

function renderGallery() {
  const grid = $('#galleryGrid');
  const count = $('#galleryCount');
  if (count) {
    count.textContent = t('gallery.count', {
      total: appState.galleryTotal || 0,
      available: appState.galleryAvailable || 0,
    });
  }
  if (!grid) return;
  if (!appState.galleryItems.length) {
    grid.innerHTML = `<div class="empty-state"><p>${escapeHtml(t('gallery.empty'))}</p></div>`;
    return;
  }
  grid.innerHTML = appState.galleryItems
    .map((item) => {
      const available = item.available;
      const model = item.model || '--';
      return `<article class="gallery-card image-card" data-gallery-id="${escapeHtml(item.id)}">
        <button class="media-frame gallery-thumb ${available ? '' : 'is-missing'}" type="button"
          data-preview-endpoint="${escapeHtml(item.preview_endpoint || '')}"
          data-download-endpoint="${escapeHtml(item.download_endpoint || '')}"
          data-download-name="${escapeHtml(item.filename || '')}"
          data-task-id="${escapeHtml(item.task_id)}"
          data-available="${available ? '1' : '0'}"
          ${available ? '' : 'disabled'}
          title="${escapeHtml(t('lightbox.open'))}">
          <span>${escapeHtml(available ? item.filename || `#${item.image_index}` : t('gallery.unavailable'))}</span>
        </button>
        <div class="gallery-body">
          <div class="gallery-overlay-meta">
            <span class="badge ${escapeHtml(item.status)}">${escapeHtml(statusLabel(item.status, item.status_label))}</span>
            <strong title="${escapeHtml(item.task_id)}">${escapeHtml(item.task_id)}</strong>
          </div>
          <p class="gallery-model" title="${escapeHtml(model)}">${escapeHtml(t('gallery.model'))}: ${escapeHtml(model)}</p>
          <p class="task-prompt" title="${escapeHtml(item.prompt_summary || '')}">${escapeHtml(item.prompt_summary || '--')}</p>
          <div class="gallery-actions">
            <button class="btn subtle" type="button" data-gallery-task="${escapeHtml(item.task_id)}">${escapeHtml(t('gallery.openTask'))}</button>
            <button class="btn primary" type="button" data-download-endpoint="${escapeHtml(item.download_endpoint || '')}" data-download-name="${escapeHtml(item.filename || '')}" ${available ? '' : 'disabled'}>${escapeHtml(t('detail.download'))}</button>
          </div>
        </div>
      </article>`;
    })
    .join('');
  hydrateGalleryPreviews();
}


async function loadGallery(showMessage = false) {
  if (appState.loadingGallery) return;
  appState.loadingGallery = true;
  if ($('#refreshGalleryBtn')) $('#refreshGalleryBtn').disabled = true;
  try {
    const result = await apiGet('page/gallery', {
      status: $('#galleryStatusFilter')?.value || 'all',
      model: $('#galleryModelFilter')?.value || '',
      days: $('#galleryDaysFilter')?.value || '0',
      limit: $('#galleryLimitSelect')?.value || '48',
      keyword: $('#galleryKeyword')?.value?.trim() || '',
    });
    appState.galleryItems = result.items || [];
    appState.galleryModels = result.models || [];
    appState.galleryTotal = result.total || 0;
    appState.galleryAvailable = result.available_count || 0;
    renderGalleryModelFilter(appState.galleryModels);
    renderGallery();
    if (showMessage) showToast(t('message.galleryLoaded'));
  } catch (error) {
    showToast(error.message || t('error.generic'), true);
  } finally {
    appState.loadingGallery = false;
    if ($('#refreshGalleryBtn')) $('#refreshGalleryBtn').disabled = false;
  }
}

function openTask(taskId) {
  appState.selectedTaskId = taskId;
  renderTaskList();
  setView('tasks');
  loadTaskDetail(taskId);
}

function bindEvents() {
  $('#generationForm')?.addEventListener('submit', submitTask);
  $('#refreshStateBtn')?.addEventListener('click', () => loadState(true));
  $('#refreshTasksBtn')?.addEventListener('click', () => loadTasks());
  $('#refreshGalleryBtn')?.addEventListener('click', () => loadGallery(true));
  $('#statsDaysFilter')?.addEventListener('change', () => loadStats());
  let trendResizeTimer = 0;
  window.addEventListener('resize', () => {
    window.clearTimeout(trendResizeTimer);
    trendResizeTimer = window.setTimeout(() => {
      if (appState.currentView === 'overview' && appState.trendChart?.items?.length) {
        renderDailyTrend(appState.trendChart.items, appState.trendChart.granularity || 'day');
      }
    }, 120);
  });
  $('#tasksSourceFilter')?.addEventListener('change', () => loadTasks({ resetOffset: true }));
  $('#tasksModelFilter')?.addEventListener('change', () => loadTasks({ resetOffset: true }));
  $('#tasksDaysFilter')?.addEventListener('change', () => loadTasks({ resetOffset: true }));
  let tasksKeywordTimer = 0;
  $('#tasksKeyword')?.addEventListener('input', () => {
    window.clearTimeout(tasksKeywordTimer);
    tasksKeywordTimer = window.setTimeout(() => loadTasks({ resetOffset: true }), 280);
  });
  $('#tasksPrevBtn')?.addEventListener('click', () => {
    const limit = Math.max(1, Number(appState.tasksLimit || 30));
    appState.tasksOffset = Math.max(0, Number(appState.tasksOffset || 0) - limit);
    loadTasks();
  });
  $('#tasksNextBtn')?.addEventListener('click', () => {
    const limit = Math.max(1, Number(appState.tasksLimit || 30));
    const total = Number(appState.tasksTotal || 0);
    const nextOffset = Number(appState.tasksOffset || 0) + limit;
    if (nextOffset < total) {
      appState.tasksOffset = nextOffset;
      loadTasks();
    }
  });
  $('#galleryStatusFilter')?.addEventListener('change', () => loadGallery());
  $('#galleryModelFilter')?.addEventListener('change', () => loadGallery());
  $('#galleryDaysFilter')?.addEventListener('change', () => loadGallery());
  $('#galleryLimitSelect')?.addEventListener('change', () => loadGallery());
  let galleryKeywordTimer = 0;
  $('#galleryKeyword')?.addEventListener('input', () => {
    window.clearTimeout(galleryKeywordTimer);
    galleryKeywordTimer = window.setTimeout(() => loadGallery(), 280);
  });
  $('#galleryGrid')?.addEventListener('click', (event) => {
    const taskButton = event.target.closest('[data-gallery-task]');
    if (taskButton) {
      openTask(taskButton.dataset.galleryTask);
      return;
    }
    const frame = event.target.closest('.gallery-thumb[data-preview-endpoint]');
    if (frame && !frame.disabled) {
      openImagePreview(frame);
      return;
    }
    const downloadButton = event.target.closest('button[data-download-endpoint]');
    if (downloadButton && !downloadButton.disabled) {
      downloadImage(downloadButton.dataset.downloadEndpoint, downloadButton.dataset.downloadName);
    }
  });
  $('#statusFilter')?.addEventListener('change', () => {
    appState.selectedTaskId = '';
    appState.selectedTask = null;
    loadTasks({ resetOffset: true });
  });
  $('#limitSelect')?.addEventListener('change', () => loadTasks({ resetOffset: true }));
  $('#referenceInput')?.addEventListener('change', (event) =>
    uploadReferences(Array.from(event.target.files || [])),
  );
  $('#uploadList')?.addEventListener('click', (event) => {
    const index = event.target?.dataset?.uploadRemove;
    if (index === undefined) return;
    appState.uploads.splice(Number(index), 1);
    renderUploads();
  });
  document.querySelectorAll('.tab-btn').forEach((button) => {
    button.addEventListener('click', () => setView(button.dataset.view));
  });
  document.querySelectorAll('[data-goto-view]').forEach((button) => {
    button.addEventListener('click', () => setView(button.dataset.gotoView));
  });
  document.addEventListener('change', (event) => {
    const input = event.target.closest('.chip-input');
    if (!input) return;
    input.closest('.chip')?.classList.toggle('is-checked', input.checked);
  });
  $('#taskList')?.addEventListener('click', (event) => {
    const row = event.target.closest('.task-row');
    if (!row) return;
    openTask(row.dataset.taskId);
  });
  $('#generateResultPanel')?.addEventListener('click', (event) => {
    const selectButton = event.target.closest('[data-select-generate-task]');
    if (selectButton?.dataset.selectGenerateTask) {
      appState.activeGenerateTaskId = selectButton.dataset.selectGenerateTask;
      renderGenerateResults();
      return;
    }
    const cancelButton = event.target.closest('[data-cancel-generate-task]');
    if (cancelButton) {
      cancelGenerateTask(cancelButton.dataset.cancelGenerateTask);
      return;
    }
    const openButton = event.target.closest('[data-open-generate-task]');
    if (openButton?.dataset.openGenerateTask) {
      openTask(openButton.dataset.openGenerateTask);
      return;
    }
    const clearButton = event.target.closest('[data-clear-generate-task]');
    if (clearButton?.dataset.clearGenerateTask) {
      clearGenerateResult(clearButton.dataset.clearGenerateTask);
      return;
    }
    const previewTrigger = event.target.closest(
      '.result-thumb[data-preview-endpoint], button[data-preview-endpoint]:not([data-download-only])',
    );
    if (previewTrigger && !previewTrigger.disabled && previewTrigger.dataset.previewEndpoint) {
      if (!previewTrigger.classList.contains('primary') || previewTrigger.classList.contains('result-thumb')) {
        openImagePreview(previewTrigger);
        return;
      }
    }
    const downloadButton = event.target.closest('button[data-download-endpoint]');
    if (downloadButton) {
      downloadImage(downloadButton.dataset.downloadEndpoint, downloadButton.dataset.downloadName);
    }
  });
  $('#detailPanel')?.addEventListener('click', (event) => {
    if (event.target.id === 'cancelTaskBtn') {
      cancelSelectedTask();
      return;
    }
    if (event.target.id === 'togglePromptBtn') {
      const button = event.target;
      const full = $('#detailPromptFull');
      const summary = $('#detailPromptSummary');
      if (!full) return;
      const expanded = button.dataset.expanded === '1';
      const nextExpanded = !expanded;
      full.hidden = !nextExpanded;
      if (summary) summary.hidden = nextExpanded;
      button.dataset.expanded = nextExpanded ? '1' : '0';
      button.textContent = nextExpanded ? t('detail.collapsePrompt') : t('detail.expandPrompt');
      if (appState.selectedTaskId) {
        appState.expandedPromptByTask[appState.selectedTaskId] = nextExpanded;
      }
      return;
    }
    const previewTrigger = event.target.closest(
      '.result-thumb[data-preview-endpoint], button[data-preview-endpoint]:not([data-download-only])',
    );
    if (previewTrigger && !previewTrigger.disabled && previewTrigger.dataset.previewEndpoint) {
      if (!previewTrigger.classList.contains('primary') || previewTrigger.classList.contains('result-thumb')) {
        openImagePreview(previewTrigger);
        return;
      }
    }
    const downloadButton = event.target.closest('button[data-download-endpoint]');
    if (downloadButton) {
      downloadImage(downloadButton.dataset.downloadEndpoint, downloadButton.dataset.downloadName);
    }
  });
  $('#imageLightbox')?.addEventListener('click', (event) => {
    if (event.target.closest('[data-lightbox-close]')) {
      closeLightbox();
    }
  });
  $('#lightboxDownloadBtn')?.addEventListener('click', () => {
    if (!appState.lightbox.downloadEndpoint) return;
    downloadImage(appState.lightbox.downloadEndpoint, appState.lightbox.downloadName);
  });
  $('#lightboxOpenTaskBtn')?.addEventListener('click', () => {
    if (!appState.lightbox.taskId) return;
    closeLightbox();
    openTask(appState.lightbox.taskId);
  });
  window.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && appState.lightbox.open) closeLightbox();
  });
  window.addEventListener('hashchange', () => {
    const view = window.location.hash.replace(/^#/, '') || 'overview';
    setView(view, { pushHash: false });
  });
}

async function refreshLocalizedUi() {
  await loadStrings();
  applyStaticText();
  renderState();
  renderTaskList();
  if (appState.currentView === 'tasks' && appState.selectedTask) {
    renderDetail(appState.selectedTask);
  } else if (appState.currentView === 'tasks' && appState.selectedTaskId) {
    await loadTaskDetail(appState.selectedTaskId, { silent: true });
  }
  if (appState.currentView === 'generate') {
    renderGenerateResults();
  }
  if (appState.currentView === 'gallery') {
    renderGallery();
  }
  if (appState.currentView === 'overview') {
    renderOverviewSummary();
  }
  if ($('#submitBtn')) $('#submitBtn').textContent = t('submit');
}

async function init() {
  try {
    appState.bridge = await getBridge();
    if (typeof appState.bridge.ready === 'function') {
      await appState.bridge.ready();
    }
  } catch (error) {
    showToast(error.message || 'Plugin bridge unavailable', true);
    return;
  }
  if (window.AstrBotPluginPage) {
    appState.bridge = window.AstrBotPluginPage;
  }
  let currentLocale = '';
  try {
    const context =
      (typeof appState.bridge.getContext === 'function'
        ? await appState.bridge.getContext()
        : null) || {};
    currentLocale = context.locale || '';
    applyTheme(context);
    if (typeof appState.bridge.onContext === 'function') {
      appState.bridge.onContext(async (nextContext) => {
        const contextValue = nextContext || {};
        applyTheme(contextValue);
        const nextLocale = contextValue.locale || '';
        if (nextLocale && nextLocale !== currentLocale) {
          currentLocale = nextLocale;
          await refreshLocalizedUi();
        }
      });
    }
  } catch {
    applyTheme({});
  }
  await loadStrings();
  applyStaticText();
  bindEvents();
  renderUploads();
  const initialView = window.location.hash.replace(/^#/, '') || 'overview';
  setView(initialView, { pushHash: false });
  await loadState();
  await loadTasks();
  renderGenerateResultEmpty();
  window.setInterval(() => {
    if (document.hidden) return;
    const hasActiveTask = appState.tasks.some((task) => task.active);
    if (hasActiveTask) loadTasks();
    if (
      appState.currentView === 'generate' &&
      appState.generateTasks.some((task) => task.active)
    ) {
      // Poll only while the current generate task is still running.
      loadGenerateResults({ silent: true });
    }
  }, 3000);
}

init().catch((error) => showToast(error.message || FALLBACK['error.generic'], true));
