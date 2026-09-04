const form = document.querySelector('#draftForm');
const coverWall = document.querySelector('#coverWall');
const titlePicks = document.querySelector('#titlePicks');
const bodyCopy = document.querySelector('#bodyCopy');
const tagList = document.querySelector('#tagList');
const sourceNote = document.querySelector('#sourceNote');
const copyDraft = document.querySelector('#copyDraft');
const downloadCover = document.querySelector('#downloadCover');
const runButton = form.querySelector('.run-button');

let draft = null;
let pickedTitle = '';
let pickedCover = null;

function escapeHtml(value = '') {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}

function renderTitles(titles) {
  titlePicks.innerHTML = titles.map(title => `
    <button type="button" data-title="${escapeHtml(title)}" class="${title === pickedTitle ? 'is-picked' : ''}">${escapeHtml(title)}</button>
  `).join('');
}

function renderCovers(covers) {
  coverWall.innerHTML = covers.map(cover => `
    <article class="cover-card ${pickedCover?.id === cover.id ? 'is-picked' : ''}">
      <button type="button" data-cover="${escapeHtml(cover.id)}">
        <img src="${cover.dataUrl}" alt="${escapeHtml(cover.label)}封面">
        <span>${escapeHtml(cover.label)}</span>
      </button>
    </article>
  `).join('');
}

function renderTags(tags) {
  tagList.textContent = tags.map(tag => `#${tag}`).join('  ');
}

function enableExport(on) {
  copyDraft.disabled = !on;
  downloadCover.disabled = !on || !pickedCover;
}

async function generateDraft(event) {
  event.preventDefault();
  runButton.disabled = true;
  sourceNote.textContent = '正在出标题、正文和封面…';
  try {
    const response = await fetch('/api/draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: form.topic.value.trim(),
        points: form.points.value,
        audience: form.audience.value.trim(),
        title: pickedTitle
      })
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || '生成失败');
    draft = payload;
    pickedTitle = payload.title;
    pickedCover = payload.covers[0] || null;
    bodyCopy.value = payload.body;
    renderTitles(payload.titles);
    renderCovers(payload.covers);
    renderTags(payload.tags);
    enableExport(true);
    sourceNote.textContent = payload.source === 'model' ? '这次用了本地/接口模型。' : '这次是规则模板。封面为本地排版，导出后去专业号后台发布。';
  } catch (error) {
    sourceNote.textContent = error.message;
  } finally {
    runButton.disabled = false;
  }
}

async function refreshCovers(title) {
  pickedTitle = title;
  renderTitles(draft.titles);
  sourceNote.textContent = '按新标题重排封面…';
  const response = await fetch('/api/draft/covers', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      topic: form.topic.value.trim() || '主题',
      title
    })
  });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload.detail || '封面更新失败');
  draft.covers = payload.covers;
  pickedCover = payload.covers.find(item => item.id === pickedCover?.id) || payload.covers[0];
  renderCovers(payload.covers);
  enableExport(true);
  sourceNote.textContent = '封面已按所选标题更新。';
}

form.addEventListener('submit', generateDraft);

titlePicks.addEventListener('click', async event => {
  const button = event.target.closest('[data-title]');
  if (!button || !draft) return;
  try {
    await refreshCovers(button.dataset.title);
  } catch (error) {
    sourceNote.textContent = error.message;
  }
});

coverWall.addEventListener('click', event => {
  const button = event.target.closest('[data-cover]');
  if (!button || !draft) return;
  pickedCover = draft.covers.find(item => item.id === button.dataset.cover) || pickedCover;
  renderCovers(draft.covers);
  enableExport(true);
});

copyDraft.addEventListener('click', async () => {
  if (!draft) return;
  const text = [pickedTitle, '', bodyCopy.value, '', tagList.textContent].join('\n');
  await navigator.clipboard.writeText(text);
  sourceNote.textContent = '标题、正文和标签已复制。去专业号后台粘贴即可。';
});

downloadCover.addEventListener('click', () => {
  if (!pickedCover) return;
  const link = document.createElement('a');
  link.href = pickedCover.dataUrl;
  link.download = `${pickedTitle || 'cover'}-${pickedCover.id}.png`;
  link.click();
});
