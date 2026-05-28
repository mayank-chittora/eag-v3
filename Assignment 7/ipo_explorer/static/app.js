/* IPO RAG — 3-stage chatbot app.js
 * State machine: WELCOME → INDEXING → CHAT
 * Query SSE uses fetch() + ReadableStream (EventSource is GET-only).
 */

'use strict';

// ── State machine ────────────────────────────────────────────────────────────
const STAGES = {
  WELCOME: 'stage-welcome',
  SETUP: 'stage-setup',
  CHAT: 'stage-chat',
};

let currentStage = 'WELCOME';
let corpusStats = { companies: 0, chunks: 0 };
let sessionId = 'session-' + Math.random().toString(36).slice(2, 10);
let isQuerying = false;

function goTo(stage) {
  document.querySelectorAll('.stage').forEach(s => s.classList.remove('active'));
  document.getElementById(STAGES[stage]).classList.add('active');
  currentStage = stage;
}

// ── Stage 1 → 2 ──────────────────────────────────────────────────────────────
document.getElementById('btn-start').addEventListener('click', () => goTo('SETUP'));

// ── Stage 2: Indexing ─────────────────────────────────────────────────────────
document.getElementById('btn-index').addEventListener('click', startIndexing);

async function startIndexing() {
  const startYear = parseInt(document.getElementById('start-year').value, 10);
  const endYear = parseInt(document.getElementById('end-year').value, 10);
  if (isNaN(startYear) || isNaN(endYear) || startYear > endYear) {
    alert('Invalid year range');
    return;
  }

  const btn = document.getElementById('btn-index');
  btn.disabled = true;
  btn.textContent = 'Indexing…';

  let res;
  try {
    res = await fetch('/api/index', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ start_year: startYear, end_year: endYear }),
    });
  } catch (e) {
    alert('Server error: ' + e.message);
    btn.disabled = false;
    btn.textContent = 'Index IPOs';
    return;
  }

  const data = await res.json();

  if (data.cached) {
    // Already indexed — flash notice and go to chat
    const notice = document.getElementById('cached-notice');
    notice.textContent = `✓ Cached index found — ${data.ipo_count} companies already indexed`;
    notice.classList.add('visible');
    await loadCorpusStats();
    setTimeout(() => transitionToChat(), 1500);
    return;
  }

  // Show progress
  const progressSection = document.getElementById('progress-section');
  progressSection.classList.add('visible');
  const progressBar = document.getElementById('progress-bar');
  const progressCount = document.getElementById('progress-count');
  const progressTicker = document.getElementById('progress-ticker');
  const statsCard = document.getElementById('stats-card');

  let totalCount = data.ipo_count;
  progressCount.textContent = `0 / ${totalCount}`;

  const es = new EventSource(`/api/index/${data.job_id}/stream`);

  es.onmessage = (e) => {
    const ev = JSON.parse(e.data);

    if (ev.event === 'progress') {
      const pct = Math.round((ev.company_done / ev.company_total) * 100);
      progressBar.style.width = pct + '%';
      progressCount.textContent = `${ev.company_done} / ${ev.company_total}`;
      progressTicker.innerHTML =
        `Indexing: <span class="ticker-company">${ev.company}</span>` +
        ` (${ev.chunks_written} chunks)`;
    }

    if (ev.event === 'stats') {
      document.getElementById('stat-companies').textContent = ev.companies_indexed;
      document.getElementById('stat-pages').textContent = ev.pages_fetched;
      document.getElementById('stat-chunks').textContent = ev.total_chunks;
      statsCard.classList.add('visible');
      progressTicker.textContent = 'All companies indexed ✓';
      progressBar.style.width = '100%';
      corpusStats = { companies: ev.companies_indexed, chunks: ev.total_chunks };
    }

    if (ev.event === 'done') {
      es.close();
      setTimeout(() => transitionToChat(), 1400);
    }

    if (ev.event === 'error') {
      progressTicker.innerHTML = `<span style="color:var(--red)">Error: ${ev.message}</span>`;
    }
  };

  es.onerror = () => {
    progressTicker.innerHTML = `<span style="color:var(--red)">Connection lost</span>`;
    es.close();
  };
}

async function loadCorpusStats() {
  try {
    const r = await fetch('/api/state');
    const d = await r.json();
    corpusStats = { companies: d.companies, chunks: d.chunks };
  } catch (_) {}
}

function transitionToChat() {
  updateCorpusHeader();
  goTo('CHAT');
}

function updateCorpusHeader() {
  const badge = document.getElementById('corpus-badge');
  const statsBar = document.getElementById('corpus-stats-bar');
  badge.textContent = `${corpusStats.companies} companies indexed`;
  statsBar.innerHTML =
    `<strong>${corpusStats.companies}</strong> companies · <strong>${corpusStats.chunks}</strong> chunks`;
}

// ── Stage 3: Chat ─────────────────────────────────────────────────────────────

// Chip clicks
document.querySelectorAll('.chip').forEach(chip => {
  chip.addEventListener('click', () => {
    const q = chip.dataset.q;
    if (q && !isQuerying) sendQuery(q);
  });
});

// Textarea: Enter sends, Shift+Enter inserts newline
const chatInput = document.getElementById('chat-input');
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    submitQuery();
  }
});
chatInput.addEventListener('input', () => {
  chatInput.style.height = 'auto';
  chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
});

document.getElementById('send-btn').addEventListener('click', submitQuery);

function submitQuery() {
  const q = chatInput.value.trim();
  if (!q || isQuerying) return;
  chatInput.value = '';
  chatInput.style.height = 'auto';
  sendQuery(q);
}

function hideChips() {
  const bar = document.getElementById('chip-bar');
  if (bar) bar.style.display = 'none';
}

async function sendQuery(query) {
  hideChips();
  isQuerying = true;
  setInputEnabled(false);
  clearError();

  // User bubble
  appendMessage('user', query);

  // Thinking container (will fill with iterations)
  const thinkingBlock = document.createElement('div');
  thinkingBlock.className = 'thinking-block';

  const agentRow = appendAgentRow();
  agentRow.querySelector('.msg-body').appendChild(thinkingBlock);

  // Answer bubble placeholder (appended after iterations)
  let answerBubble = null;

  // Parse SSE from a POST response
  let res;
  try {
    res = await fetch('/api/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId }),
    });
  } catch (e) {
    showError('Network error: ' + e.message);
    isQuerying = false;
    setInputEnabled(true);
    return;
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  // Iteration tracking
  const iterCards = {}; // iter number → {card, bodyEl, data}

  function getOrCreateIterCard(iter) {
    if (iterCards[iter]) return iterCards[iter];
    const card = document.createElement('div');
    card.className = 'iter-card';

    const header = document.createElement('div');
    header.className = 'iter-header';
    header.innerHTML = `
      <span class="iter-num">Iteration ${iter}</span>
      <span class="iter-badge running"><span class="spinner"></span></span>
      <span class="iter-summary"></span>
      <span class="iter-chevron">▶</span>
    `;
    header.addEventListener('click', () => card.classList.toggle('open'));

    const body = document.createElement('div');
    body.className = 'iter-body';

    card.appendChild(header);
    card.appendChild(body);
    thinkingBlock.appendChild(card);

    iterCards[iter] = { card, header, body, data: {} };
    scrollToBottom();
    return iterCards[iter];
  }

  function setIterBadge(ic, kind) {
    const badge = ic.header.querySelector('.iter-badge');
    badge.className = 'iter-badge ' + kind;
    if (kind === 'running') {
      badge.innerHTML = '<span class="spinner"></span>';
    } else if (kind === 'tool') {
      badge.textContent = 'tool call';
    } else if (kind === 'answer') {
      badge.textContent = 'answer';
    }
  }

  function renderIterBody(ic) {
    const d = ic.data;
    const b = ic.body;
    b.innerHTML = '';

    if (d.memory) {
      const row = makeIterRow('Memory', `${d.memory.hits} hits`);
      if (d.memory.descriptors && d.memory.descriptors.length > 0) {
        const ul = document.createElement('ul');
        ul.style.cssText = 'list-style:none;margin-top:0.25rem;display:flex;flex-direction:column;gap:0.15rem';
        d.memory.descriptors.forEach(desc => {
          const li = document.createElement('li');
          li.style.cssText = 'font-size:0.75rem;color:var(--text-dim)';
          li.textContent = '· ' + desc;
          ul.appendChild(li);
        });
        row.querySelector('.iter-row-val').appendChild(ul);
      }
      b.appendChild(row);
    }

    if (d.perception) {
      const ul = document.createElement('ul');
      ul.className = 'goal-list';
      d.perception.goals.forEach(g => {
        const li = document.createElement('li');
        li.className = 'goal-item' + (g.done ? ' done' : '');
        li.innerHTML = `<span class="goal-icon">${g.done ? '✓' : '○'}</span>
          <span class="goal-text">${escHtml(g.text)}</span>`;
        ul.appendChild(li);
      });
      const row = makeIterRow('Goals', '');
      row.querySelector('.iter-row-val').innerHTML = '';
      row.querySelector('.iter-row-val').appendChild(ul);
      b.appendChild(row);
    }

    if (d.decision) {
      if (d.decision.kind === 'tool_call') {
        b.appendChild(makeIterRow('Decision', `<code>${escHtml(d.decision.detail)}</code>`));
      } else {
        b.appendChild(makeIterRow('Decision', 'Generating answer…'));
      }
    }

    if (d.action) {
      let val = `<code>${escHtml(d.action.tool)}</code> → `;
      val += escHtml((d.action.result_preview || '').slice(0, 200));
      if (d.action.artifact_id) val += ` <em>(artifact: ${d.action.artifact_id})</em>`;
      b.appendChild(makeIterRow('Action', val));
    }

    if (d.memory_write) {
      b.appendChild(makeIterRow('Memory', 'Written to vector index ✓'));
    }
  }

  function makeIterRow(label, html) {
    const row = document.createElement('div');
    row.className = 'iter-row';
    row.innerHTML = `<span class="iter-row-label">${label}</span><span class="iter-row-val">${html}</span>`;
    return row;
  }

  // Read SSE stream
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop();

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue;
      let ev;
      try { ev = JSON.parse(line.slice(6)); } catch (_) { continue; }

      const iter = ev.iter;

      if (ev.event === 'memory' && iter) {
        const ic = getOrCreateIterCard(iter);
        ic.data.memory = ev;
        renderIterBody(ic);
        ic.header.querySelector('.iter-summary').textContent =
          `Memory: ${ev.hits} hits`;
      }

      if (ev.event === 'perception' && iter) {
        const ic = getOrCreateIterCard(iter);
        ic.data.perception = ev;
        const pending = ev.goals.filter(g => !g.done);
        ic.header.querySelector('.iter-summary').textContent =
          pending.length ? pending[0].text.slice(0, 60) : 'All done';
        renderIterBody(ic);
      }

      if (ev.event === 'decision' && iter) {
        const ic = getOrCreateIterCard(iter);
        ic.data.decision = ev;
        setIterBadge(ic, ev.kind === 'tool_call' ? 'tool' : 'answer');
        ic.header.querySelector('.iter-summary').textContent =
          ev.kind === 'tool_call' ? ev.detail.slice(0, 60) : 'Generating answer…';
        renderIterBody(ic);
      }

      if (ev.event === 'action' && iter) {
        const ic = getOrCreateIterCard(iter);
        ic.data.action = ev;
        renderIterBody(ic);
      }

      if (ev.event === 'memory_write' && iter) {
        const ic = iterCards[iter];
        if (ic) {
          ic.data.memory_write = true;
          setIterBadge(ic, ic.data.decision?.kind === 'answer' ? 'answer' : 'tool');
          renderIterBody(ic);
        }
      }

      if (ev.event === 'done') {
        // Collapse all iteration cards
        Object.values(iterCards).forEach(ic => ic.card.classList.remove('open'));

        // Show final answer
        if (ev.answer) {
          const bubble = document.createElement('div');
          bubble.className = 'bubble';
          bubble.innerHTML = formatAnswer(ev.answer);
          agentRow.querySelector('.msg-body').appendChild(bubble);
        }
        scrollToBottom();
      }

      if (ev.event === 'error') {
        showError(ev.message || 'Agent error');
      }
    }
  }

  isQuerying = false;
  setInputEnabled(true);
}

// ── Helpers ──────────────────────────────────────────────────────────────────

function appendMessage(role, text) {
  const messages = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = `msg-row ${role}`;
  const initial = role === 'user' ? 'U' : '🤖';
  row.innerHTML = `
    <div class="msg-avatar">${initial}</div>
    <div class="msg-body">
      <div class="bubble">${formatAnswer(text)}</div>
    </div>
  `;
  messages.appendChild(row);
  scrollToBottom();
  return row;
}

function appendAgentRow() {
  const messages = document.getElementById('chat-messages');
  const row = document.createElement('div');
  row.className = 'msg-row agent';
  row.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-body"></div>
  `;
  messages.appendChild(row);
  scrollToBottom();
  return row;
}

function scrollToBottom() {
  const el = document.getElementById('chat-messages');
  el.scrollTop = el.scrollHeight;
}

function setInputEnabled(enabled) {
  document.getElementById('chat-input').disabled = !enabled;
  document.getElementById('send-btn').disabled = !enabled;
}

function showError(msg) {
  const b = document.getElementById('error-banner');
  b.textContent = '⚠ ' + msg;
  b.classList.add('visible');
}

function clearError() {
  document.getElementById('error-banner').classList.remove('visible');
}

function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatAnswer(text) {
  // Markdown: code blocks, inline code, bold, italic, bullet lists, newlines
  let s = escHtml(text);

  // Fenced code blocks
  s = s.replace(/```[\w]*\n([\s\S]*?)```/g, (_, code) =>
    `<pre class="code-block"><code>${code.trimEnd()}</code></pre>`);

  // Inline code
  s = s.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  // Bold / italic
  s = s.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  s = s.replace(/\*(.+?)\*/g, '<em>$1</em>');

  // Bullet lists (lines starting with - or •)
  s = s.replace(/((?:^|\n)[•\-] .+)+/g, match => {
    const items = match.trim().split('\n').map(l =>
      `<li>${l.replace(/^[•\-]\s*/, '')}</li>`).join('');
    return `<ul class="answer-list">${items}</ul>`;
  });

  // Newlines → <br> (but not inside pre blocks)
  s = s.replace(/(?<!<\/pre>)\n/g, '<br>');

  return s;
}

// ── Init: check if corpus already indexed ────────────────────────────────────
(async () => {
  try {
    const r = await fetch('/api/state');
    const d = await r.json();
    if (d.indexed) {
      corpusStats = { companies: d.companies, chunks: d.chunks };
    }
  } catch (_) {}
})();
