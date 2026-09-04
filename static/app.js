const form = document.querySelector('#agentForm');
const input = document.querySelector('#agentInput');
const resultArea = document.querySelector('#resultArea');
const traceList = document.querySelector('#traceList');
const historyList = document.querySelector('#historyList');
const toolCount = document.querySelector('#toolCount');
const specimenId = document.querySelector('#specimenId');
const specimenTime = document.querySelector('#specimenTime');
const runButton = form.querySelector('.run-button');
const serviceDot = document.querySelector('#serviceDot');
const serviceText = document.querySelector('#serviceText');
const loginText = document.querySelector('#loginText');
const toolCatalog = document.querySelector('#toolCatalog');
const toolWorkbench = document.querySelector('#toolWorkbench');
const toolForm = document.querySelector('#toolForm');
const toolFields = document.querySelector('#toolFields');
const toolTitle = document.querySelector('#toolTitle');
const toolMachineName = document.querySelector('#toolMachineName');
const toolDescription = document.querySelector('#toolDescription');
const toolRiskBadge = document.querySelector('#toolRiskBadge');
const confirmRow = document.querySelector('#confirmRow');
const confirmTool = document.querySelector('#confirmTool');
const confirmCopy = document.querySelector('#confirmCopy');
const executeTool = document.querySelector('#executeTool');
const toolFormHint = document.querySelector('#toolFormHint');
const preflightPanel = document.querySelector('#preflightPanel');
const preflightButton = document.querySelector('#preflightButton');
const preflightResult = document.querySelector('#preflightResult');

let sequence = 0;
let currentTool = null;
let currentFilter = 'all';
let currentRewrite = null;
let tools = [];
const history = [];

const FIELD_LABELS = {
  title: '标题', content: '正文', images: '图片路径或链接', tags: '话题标签',
  schedule_at: '定时发布时间', is_original: '声明原创', visibility: '可见范围',
  products: '商品关键词', video: '视频绝对路径', keyword: '搜索关键词', filters: '筛选条件',
  feed_id: '笔记 ID', xsec_token: '访问令牌', load_all_comments: '加载全部评论',
  limit: '数量上限', click_more_replies: '展开二级回复', reply_limit: '回复数量阈值',
  scroll_speed: '滚动速度', user_id: '用户 ID', tab: '分区 / Tab',
  comment_id: '评论 ID', unlike: '取消点赞', unfavorite: '取消收藏'
};

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  })[char]);
}

function timeLabel(date = new Date()) {
  return new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit' }).format(date);
}

function setTrace(stage, title, detail) {
  const labels = [
    ['服务握手', '本地服务已连接'],
    ['工具执行', '等待选择或解析任务'],
    ['样本归档', '真实返回会写入工作台']
  ];
  traceList.innerHTML = labels.map((item, index) => {
    const state = index < stage ? 'is-done' : index === stage ? 'is-active' : '';
    const copy = index === stage ? [title, detail] : item;
    return `<li class="trace-item ${state}"><span class="trace-node"></span><div><b>${escapeHtml(copy[0])}</b><small>${escapeHtml(copy[1])}</small></div></li>`;
  }).join('');
}

function renderLoading(message) {
  resultArea.classList.remove('has-result');
  resultArea.innerHTML = `<div class="loading-state"><div><div class="scanner"></div><strong>Agent 正在执行</strong><p>${escapeHtml(message)}</p></div></div>`;
}

function renderResult(payload, query) {
  const result = payload.result || {};
  const text = result.text || '工具调用完成，但没有返回文本。';
  const images = (result.images || []).map((src, index) => `<img class="result-image" src="${src}" alt="工具返回图片 ${index + 1}">`).join('');
  const raw = result.data?.length
    ? `<details class="raw-data"><summary>查看结构化原始数据</summary><pre>${escapeHtml(JSON.stringify(result.data, null, 2))}</pre></details>`
    : '';
  const risk = payload.risk && payload.risk !== 'read'
    ? `<span class="result-risk">${payload.risk === 'write' ? '已确认写操作' : '已确认副作用'}</span>`
    : '';
  resultArea.classList.add('has-result');
  resultArea.innerHTML = `<div class="result-block"><div class="result-meta"><span>${escapeHtml(payload.activity || '工具结果')}</span><span>实时返回</span>${risk}</div><h1>${escapeHtml(payload.activity)}</h1><p class="result-text">${escapeHtml(text)}</p>${images}${raw}</div>`;
  addHistory(query, payload.activity);
}

function renderError(message) {
  resultArea.classList.remove('has-result');
  resultArea.innerHTML = `<div class="error-state"><span class="error-stamp">COLLECTION FAILED</span><h1>这次没有执行成功</h1><p>${escapeHtml(message)}</p></div>`;
}

function addHistory(query, activity) {
  history.unshift({ query, activity, time: timeLabel() });
  sequence += 1;
  specimenId.textContent = `XHS—${String(sequence).padStart(3, '0')}`;
  specimenTime.textContent = `归档 ${timeLabel()}`;
  historyList.innerHTML = history.slice(0, 7).map(item => `<li><strong>${escapeHtml(item.activity)}</strong><span>${escapeHtml(item.query)}</span><time>${item.time}</time></li>`).join('');
}

function errorMessage(payload, fallback) {
  if (typeof payload?.detail === 'string') return payload.detail;
  if (payload?.detail?.message) return payload.detail.message;
  return fallback;
}

function renderPreflightResult(result, source) {
  const sourceLabel = source === 'checker' ? '内容检查器' : '规则包词表';
  currentRewrite = {
    title: result.optimizedTitle || '',
    content: result.optimizedContent || ''
  };
  preflightResult.className = `preflight-result ${result.hasSensitive ? 'is-risk' : 'is-pass'}`;
  const rewriteBlock = currentRewrite.title || currentRewrite.content
    ? `<div class="rewrite-card">
        <div class="rewrite-head">
          <strong>改写稿</strong>
          <button type="button" class="apply-rewrite" id="applyRewrite">填入改写稿</button>
        </div>
        ${currentRewrite.title ? `<label>标题</label><pre>${escapeHtml(currentRewrite.title)}</pre>` : ''}
        ${currentRewrite.content ? `<label>正文</label><pre>${escapeHtml(currentRewrite.content)}</pre>` : ''}
      </div>`
    : '';
  if (!result.hasSensitive) {
    preflightResult.innerHTML = `${sourceLabel}通过：标题和正文未发现明显敏感词。${rewriteBlock}`;
    return;
  }
  const summary = result.summary ? `<p class="preflight-summary">${escapeHtml(result.summary)}</p>` : '';
  const rows = result.words.slice(0, 8).map(item => {
    const suggestions = Array.isArray(item.suggestion) && item.suggestion.length
      ? ` 建议：<em>${escapeHtml(item.suggestion.slice(0, 4).join(' / '))}</em>`
      : '';
    return `<li><b>${escapeHtml(item.level || '提示')}</b> ${escapeHtml(item.keyword)} <span>${escapeHtml(item.category)}</span>${suggestions}</li>`;
  }).join('');
  preflightResult.innerHTML = `${sourceLabel}发现 ${result.wordCount} 个风险词。高危 ${result.stats.high} / 中危 ${result.stats.mid} / 低危 ${result.stats.low} / 提示 ${result.stats.tip}${summary}<ul>${rows}</ul>${rewriteBlock}`;
}

async function runAgent(message) {
  runButton.disabled = true;
  input.disabled = true;
  renderLoading(message);
  setTrace(1, '任务解析', message);
  try {
    const response = await fetch('/api/agent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(errorMessage(payload, 'Agent 调用失败'));
    setTrace(2, '样本归档', `${payload.tool} 已返回`);
    renderResult(payload, message);
  } catch (error) {
    setTrace(1, '执行失败', error.message);
    renderError(error.message);
  } finally {
    runButton.disabled = false;
    input.disabled = false;
    input.focus();
  }
}

function resolveSchema(schema, root) {
  if (!schema?.$ref?.startsWith('#/$defs/')) return schema || {};
  return root.$defs?.[schema.$ref.split('/').pop()] || schema;
}

function schemaType(schema) {
  if (Array.isArray(schema.type)) {
    return schema.type.find(type => type !== 'null') || schema.type[0] || 'string';
  }
  return schema.type || (schema.properties ? 'object' : 'string');
}

function fieldMarkup(name, rawSchema, required, rootSchema) {
  const schema = resolveSchema(rawSchema, rootSchema);
  const type = schemaType(schema);
  const label = FIELD_LABELS[name] || name;
  const requiredMark = required ? '<em>必填</em>' : '';
  const description = escapeHtml(schema.description || '可选参数');
  const common = `name="${escapeHtml(name)}" data-argument="${escapeHtml(name)}" data-field-type="${escapeHtml(type)}" data-required="${required}"`;

  if (Array.isArray(schema.enum)) {
    const options = schema.enum.map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('');
    return `<label class="tool-field"><span>${escapeHtml(label)}${requiredMark}</span><select ${common}><option value="">请选择</option>${options}</select><small>${description}</small></label>`;
  }
  if (type === 'boolean') {
    return `<label class="tool-field"><span>${escapeHtml(label)}${requiredMark}</span><span class="boolean-field"><input type="checkbox" ${common}>启用</span><small>${description}</small></label>`;
  }
  if (type === 'array') {
    return `<label class="tool-field is-wide"><span>${escapeHtml(label)}${requiredMark}</span><textarea ${common} placeholder="每行一个值，也可填写 JSON 数组"></textarea><small>${description}</small></label>`;
  }
  if (type === 'object') {
    return `<label class="tool-field is-wide"><span>${escapeHtml(label)}${requiredMark}</span><textarea ${common} placeholder='例如：{"sort_by":"最新"}'></textarea><small>${description}；请填写 JSON 对象。</small></label>`;
  }
  if (type === 'integer' || type === 'number') {
    return `<label class="tool-field"><span>${escapeHtml(label)}${requiredMark}</span><input type="number" ${common}><small>${description}</small></label>`;
  }
  if (name === 'content') {
    return `<label class="tool-field is-wide"><span>${escapeHtml(label)}${requiredMark}</span><textarea ${common}></textarea><small>${description}</small></label>`;
  }
  return `<label class="tool-field"><span>${escapeHtml(label)}${requiredMark}</span><input type="text" ${common}><small>${description}</small></label>`;
}

function renderCatalog() {
  const visible = tools.filter(tool => {
    if (currentFilter === 'read') return tool.risk === 'read';
    if (currentFilter === 'guarded') return tool.risk !== 'read';
    return true;
  });
  toolCatalog.innerHTML = visible.map(tool => `
    <button class="tool-entry ${currentTool?.name === tool.name ? 'is-active' : ''}" type="button" data-tool="${escapeHtml(tool.name)}" title="${escapeHtml(tool.description)}">
      <span class="tool-entry-code">T${String(tool.index).padStart(2, '0')}</span>
      <span class="tool-entry-copy"><strong>${escapeHtml(tool.label)}</strong><small>${escapeHtml(tool.riskLabel)}</small></span>
      <span class="risk-dot ${escapeHtml(tool.risk)}" aria-label="${escapeHtml(tool.riskLabel)}"></span>
    </button>`).join('');
}

function openTool(tool) {
  currentTool = tool;
  renderCatalog();
  toolWorkbench.hidden = false;
  toolTitle.textContent = tool.label;
  toolMachineName.textContent = `工具 ${String(tool.index).padStart(2, '0')}`;
  toolDescription.textContent = tool.description;
  toolRiskBadge.textContent = tool.riskLabel;
  toolRiskBadge.className = tool.risk;
  executeTool.classList.toggle('guarded', tool.risk !== 'read');
  executeTool.textContent = tool.risk === 'read' ? '执行工具' : '确认并执行';
  confirmTool.checked = false;
  confirmRow.hidden = tool.risk === 'read';
  confirmCopy.textContent = tool.risk === 'side_effect'
    ? '我知道读取通知列表会清除所选分区的未读标记，并确认继续。'
    : '我已检查参数，并确认这项操作会改变账号、内容或本地登录状态。';
  preflightPanel.hidden = tool.name !== 'publish_content';
  currentRewrite = null;
  preflightResult.className = 'preflight-result';
  preflightResult.textContent = '检测标题和正文，通过后再手动发布。';
  const schema = tool.inputSchema || {};
  const properties = schema.properties || {};
  const required = new Set(schema.required || []);
  toolFields.innerHTML = Object.keys(properties).length
    ? Object.entries(properties).map(([name, field]) => fieldMarkup(name, field, required.has(name), schema)).join('')
    : '<p class="no-parameters">这个工具不需要参数，可以直接执行。</p>';
  toolFormHint.textContent = '参数表单按当前工具说明生成。';
  toolWorkbench.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

async function runPreflightCheck() {
  if (!currentTool || currentTool.name !== 'publish_content') return;
  const title = toolForm.querySelector('[name="title"]')?.value.trim() || '';
  const content = toolForm.querySelector('[name="content"]')?.value.trim() || '';
  if (!title && !content) {
    preflightResult.className = 'preflight-result is-risk';
    preflightResult.textContent = '请先填写标题或正文，再做发布前检测。';
    return;
  }

  preflightButton.disabled = true;
  preflightResult.className = 'preflight-result';
  preflightResult.textContent = '正在检测标题和正文...';
  try {
    const response = await fetch('/api/sensitive-check', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title, content, ner: true })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(errorMessage(payload, '发布前检测失败'));
    renderPreflightResult(payload.result, payload.source);
  } catch (error) {
    preflightResult.className = 'preflight-result is-risk';
    preflightResult.textContent = error.message;
  } finally {
    preflightButton.disabled = false;
  }
}

function parseField(element) {
  const type = element.dataset.fieldType;
  const required = element.dataset.required === 'true';
  if (type === 'boolean') return { present: required || element.checked, value: element.checked };
  const raw = element.value.trim();
  if (!raw) {
    if (required) throw new Error(`${FIELD_LABELS[element.name] || element.name} 为必填参数`);
    return { present: false };
  }
  if (type === 'integer') return { present: true, value: Number.parseInt(raw, 10) };
  if (type === 'number') return { present: true, value: Number(raw) };
  if (type === 'object') {
    try { return { present: true, value: JSON.parse(raw) }; }
    catch { throw new Error(`${FIELD_LABELS[element.name] || element.name} 必须是合法 JSON 对象`); }
  }
  if (type === 'array') {
    if (raw.startsWith('[')) {
      try {
        const value = JSON.parse(raw);
        if (!Array.isArray(value)) throw new Error();
        return { present: true, value };
      } catch { throw new Error(`${FIELD_LABELS[element.name] || element.name} 必须是 JSON 数组或逐行列表`); }
    }
    return { present: true, value: raw.split(/[\n,，]+/).map(value => value.trim()).filter(Boolean) };
  }
  return { present: true, value: raw };
}

function collectArguments() {
  const argumentsObject = {};
  toolForm.querySelectorAll('[data-argument]').forEach(element => {
    const parsed = parseField(element);
    if (parsed.present) argumentsObject[element.name] = parsed.value;
  });
  return argumentsObject;
}

async function invokeCurrentTool(event) {
  event.preventDefault();
  if (!currentTool) return;
  if (currentTool.risk !== 'read' && !confirmTool.checked) {
    toolFormHint.textContent = '请先勾选确认项；页面不会替你执行写操作。';
    confirmTool.focus();
    return;
  }

  let args;
  try { args = collectArguments(); }
  catch (error) {
    toolFormHint.textContent = error.message;
    return;
  }

  executeTool.disabled = true;
  renderLoading(currentTool.label);
  setTrace(1, '工具执行', currentTool.label);
  try {
    const response = await fetch(`/api/tools/${encodeURIComponent(currentTool.name)}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ arguments: args, confirm: currentTool.risk !== 'read' && confirmTool.checked })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(errorMessage(payload, '工具执行失败'));
    setTrace(2, '样本归档', `${currentTool.label} 已返回`);
    renderResult(payload, currentTool.name);
    toolFormHint.textContent = '执行完成，真实返回已写入下方样本纸。';
  } catch (error) {
    setTrace(1, '执行失败', error.message);
    renderError(error.message);
    toolFormHint.textContent = error.message;
  } finally {
    executeTool.disabled = false;
  }
}

async function loadTools() {
  try {
    const response = await fetch('/api/tools');
    const payload = await response.json();
    if (!response.ok) throw new Error(errorMessage(payload, '工具清单读取失败'));
    tools = payload.tools || [];
    toolCount.textContent = String(payload.count || tools.length).padStart(2, '0');
    renderCatalog();
  } catch (error) {
    toolCatalog.innerHTML = `<p class="catalog-error">${escapeHtml(error.message)}。确认本地服务已启动后刷新页面。</p>`;
  }
}

form.addEventListener('submit', event => {
  event.preventDefault();
  const message = input.value.trim();
  if (!message) return;
  runAgent(message);
});

toolForm.addEventListener('submit', invokeCurrentTool);
preflightButton.addEventListener('click', runPreflightCheck);

document.addEventListener('click', event => {
  const applyRewrite = event.target.closest('#applyRewrite');
  if (applyRewrite && currentRewrite) {
    const titleInput = toolForm.querySelector('[name="title"]');
    const contentInput = toolForm.querySelector('[name="content"]');
    if (titleInput && currentRewrite.title) titleInput.value = currentRewrite.title;
    if (contentInput && currentRewrite.content) contentInput.value = currentRewrite.content;
    applyRewrite.textContent = '已填入';
    return;
  }
  const toolButton = event.target.closest('[data-tool]');
  if (toolButton) {
    const tool = tools.find(item => item.name === toolButton.dataset.tool);
    if (tool) openTool(tool);
    return;
  }
  const promptButton = event.target.closest('[data-prompt]');
  if (!promptButton) return;
  const prompt = promptButton.dataset.prompt;
  input.value = prompt;
  runAgent(prompt);
});

document.querySelectorAll('[data-tool-filter]').forEach(button => {
  button.addEventListener('click', () => {
    currentFilter = button.dataset.toolFilter;
    document.querySelectorAll('[data-tool-filter]').forEach(item => item.classList.toggle('is-active', item === button));
    renderCatalog();
  });
});

document.querySelector('#closeTool').addEventListener('click', () => {
  toolWorkbench.hidden = true;
  currentTool = null;
  renderCatalog();
});

document.querySelector('#clearHistory').addEventListener('click', () => {
  history.length = 0;
  historyList.innerHTML = '<li class="history-empty">还没有采集记录</li>';
});

async function checkStatus() {
  try {
    const response = await fetch('/api/status');
    const payload = await response.json();
    const online = payload.service === 'online';
    serviceDot.className = `status-dot ${online ? 'online' : 'offline'}`;
    serviceText.textContent = online ? '服务在线' : '服务离线';
    const loginSummary = (payload.login?.text || '登录状态未知').split('\n')[0].replace(/^[✅❌]\s*/, '');
    loginText.textContent = online ? loginSummary : '请启动本地服务';
    setTrace(online ? 1 : 0, online ? '等待任务' : '服务离线', online ? '18 个工具已接入' : '请先启动本地服务');
  } catch {
    serviceDot.className = 'status-dot offline';
    serviceText.textContent = '页面服务异常';
    loginText.textContent = '请刷新重试';
  }
}

checkStatus();
loadTools();
