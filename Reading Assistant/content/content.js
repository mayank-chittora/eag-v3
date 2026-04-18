// content/content.js — Reading Assistant
// Detects text selection, shows an AI-powered speech-bubble tooltip.
// Shadow DOM (open mode) isolates styles and fixes event-retargeting issues.

(function () {
  'use strict';

  if (document.getElementById('ra-host')) return;

  // ─── Shadow DOM host ─────────────────────────────────────────────────────
  // Full-viewport size so that bottom/right CSS offsets on children resolve
  // against the viewport rather than a 0×0 box.
  // pointer-events:none passes all page interactions through.

  const host = document.createElement('div');
  host.id = 'ra-host';
  Object.assign(host.style, {
    position:      'fixed',
    top:           '0',
    left:          '0',
    width:         '100%',
    height:        '100%',
    zIndex:        '2147483647',
    pointerEvents: 'none'
  });
  document.documentElement.appendChild(host);

  const shadow = host.attachShadow({ mode: 'open' });

  const styleLink = document.createElement('link');
  styleLink.rel  = 'stylesheet';
  styleLink.href = chrome.runtime.getURL('content/content.css');
  shadow.appendChild(styleLink);

  // ─── Floating Action Button ───────────────────────────────────────────────
  // Inline styles applied immediately so layout is correct before CSS loads.

  const fab = document.createElement('div');
  fab.id    = 'ra-fab';
  fab.title = 'Reading Assistant';
  Object.assign(fab.style, {
    position:       'fixed',
    bottom:         '24px',
    right:          '24px',
    width:          '52px',
    height:         '52px',
    borderRadius:   '50%',
    background:     '#ffffff',
    boxShadow:      '0 4px 16px rgba(0,0,0,0.18), 0 1px 4px rgba(0,0,0,0.10)',
    display:        'flex',
    alignItems:     'center',
    justifyContent: 'center',
    pointerEvents:  'all',
    cursor:         'default',
    zIndex:         '2147483646'
  });
  // width/height attributes prevent the SVG from auto-sizing before CSS loads
  fab.innerHTML = `<svg width="26" height="26" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25"
      stroke="#4d90fe" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`;
  shadow.appendChild(fab);

  // ─── Speech Bubble Tooltip ────────────────────────────────────────────────
  // position:fixed set inline so placeTooltip works before CSS finishes loading.

  const tooltip = document.createElement('div');
  tooltip.id = 'ra-tooltip';
  tooltip.style.position = 'fixed';
  tooltip.style.display  = 'none';
  tooltip.innerHTML = `
    <button id="ra-close" aria-label="Close">✕</button>
    <div id="ra-header">
      <span id="ra-title">Reading Assistant</span>
    </div>
    <div id="ra-body">
      <div id="ra-loading">
        <div class="sk sk-full"></div>
        <div class="sk sk-3q"></div>
        <div class="sk sk-full"></div>
        <div class="sk sk-half"></div>
      </div>
      <ul id="ra-list"></ul>
      <div id="ra-error"></div>
    </div>
  `;
  shadow.appendChild(tooltip);

  // All visual styles set inline — bypasses async CSS load and cached stylesheets.
  Object.assign(tooltip.style, {
    background:   '#ffffff',
    border:       '1.5px solid #dde3ed',
    borderRadius: '20px',
    boxShadow:    '0 16px 48px rgba(0,0,0,0.20), 0 4px 16px rgba(0,0,0,0.12), 0 1px 4px rgba(0,0,0,0.08)',
    overflow:     'visible',
    fontFamily:   "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    fontSize:     '14px',
    color:        '#1a1a1a'
  });

  const _header = tooltip.querySelector('#ra-header');
  Object.assign(_header.style, {
    padding:      '12px 16px 10px',
    borderBottom: '1px solid #eef0f5',
    borderRadius: '20px 20px 0 0'
  });

  const _body = tooltip.querySelector('#ra-body');
  Object.assign(_body.style, {
    padding:      '14px 16px 16px',
    maxHeight:    'none',
    overflow:     'visible'
  });

  // Close button — absolutely positioned at top-right of the bubble.
  // #ra-tooltip is position:fixed which establishes the containing block.
  const _close = tooltip.querySelector('#ra-close');
  Object.assign(_close.style, {
    position:    'absolute',
    top:         '10px',
    right:       '12px',
    background:  'transparent',
    border:      'none',
    color:       '#9aa5b4',
    fontSize:    '15px',
    lineHeight:  '1',
    cursor:      'pointer',
    padding:     '2px 5px',
    borderRadius:'4px',
    pointerEvents:'all',
    zIndex:      '10'
  });
  _close.addEventListener('click', hideTooltip);

  // ─── State ────────────────────────────────────────────────────────────────

  let debounceTimer   = null;
  let dismissHandlers = null;

  // ─── Selection listener ───────────────────────────────────────────────────

  document.addEventListener('mouseup', (e) => {
    if (shadow.contains(e.target)) return;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(onSelectionEnd, 300);
  });

  function onSelectionEnd() {
    // Stop if the extension context was invalidated (e.g. after a reload).
    try { if (!chrome.runtime?.id) return; } catch (_) { return; }

    if (isFormField()) return;

    const sel  = window.getSelection();
    const text = sel && sel.toString().trim();

    if (!text || text.length < 2) { hideTooltip(); return; }

    let rect;
    try { rect = sel.getRangeAt(0).getBoundingClientRect(); } catch (_) { return; }
    if (!rect || (rect.width === 0 && rect.height === 0)) return;

    placeTooltip();
    setLoading();
    attachDismiss();

    try {
      chrome.runtime.sendMessage({ type: 'EXPLAIN_TEXT', payload: buildPayload(sel, text) }, (res) => {
        if (chrome.runtime.lastError || !res) { setError('Something went wrong. Please try again.'); return; }
        if (res.error) { setError(res.error); return; }
        setResults(res.bullets);
      });
    } catch (_) {
      hideTooltip(); // context invalidated mid-flight
    }
  }

  // ─── Positioning ──────────────────────────────────────────────────────────
  // Bubble always anchors above the FAB — tail points down toward the icon.

  function placeTooltip() {
    const FAB_SIZE   = 52;   // matches CSS width/height:52px
    const FAB_BOTTOM = 24;   // matches CSS bottom:24px
    const W = 340, GAP = 14, TOOLTIP_RIGHT = 12;

    tooltip.style.bottom = `${FAB_BOTTOM + FAB_SIZE + GAP}px`;
    tooltip.style.top    = '';
    tooltip.style.right  = `${TOOLTIP_RIGHT}px`;
    tooltip.style.left   = '';
    tooltip.style.width  = `${W}px`;

    // Tail offset from tooltip left edge aimed at FAB centre:
    //   FAB centre = (FAB_RIGHT + FAB_SIZE/2) = 50px from viewport right
    //   Tooltip right edge = TOOLTIP_RIGHT = 12px from viewport right
    //   tail-left = W − (FAB_centre_from_right − TOOLTIP_RIGHT) = 340 − 38 = 302px
    tooltip.style.setProperty('--tail-left', '302px');
    tooltip.classList.add('tail-down');
    tooltip.classList.remove('tail-up');

    tooltip.style.display = 'block';
  }

  // ─── UI states ────────────────────────────────────────────────────────────

  function setLoading() { show('ra-loading'); hide('ra-list'); hide('ra-error'); }

  function setResults(bullets) {
    const ul = shadow.getElementById('ra-list');
    ul.innerHTML = '';
    (bullets || []).forEach(b => {
      const li = document.createElement('li');
      li.textContent = b;
      ul.appendChild(li);
    });
    hide('ra-loading'); hide('ra-error'); show('ra-list');
  }

  function setError(msg) {
    shadow.getElementById('ra-error').textContent = msg;
    hide('ra-loading'); hide('ra-list'); show('ra-error');
  }

  function show(id) { shadow.getElementById(id).style.display = ''; }
  function hide(id) { shadow.getElementById(id).style.display = 'none'; }

  function hideTooltip() { tooltip.style.display = 'none'; cleanDismiss(); }

  // ─── Dismiss handlers ─────────────────────────────────────────────────────

  function attachDismiss() {
    cleanDismiss();
    const onKey  = (e) => { if (e.key === 'Escape') hideTooltip(); };
    const onDown = (e) => { if (!shadow.contains(e.target)) hideTooltip(); };
    document.addEventListener('keydown',   onKey);
    document.addEventListener('mousedown', onDown);
    dismissHandlers = { onKey, onDown };
  }

  function cleanDismiss() {
    if (!dismissHandlers) return;
    document.removeEventListener('keydown',   dismissHandlers.onKey);
    document.removeEventListener('mousedown', dismissHandlers.onDown);
    dismissHandlers = null;
  }

  // ─── Helpers ──────────────────────────────────────────────────────────────

  function buildPayload(sel, selectedText) {
    const words = selectedText.split(/\s+/).filter(Boolean).length;
    const selectionType =
      words <= 2  ? 'word_or_phrase'     :
      words <= 15 ? 'phrase_or_sentence' : 'paragraph';

    let node = sel.anchorNode;
    if (node?.nodeType === Node.TEXT_NODE) node = node.parentElement;
    const BLOCKS = ['P', 'DIV', 'ARTICLE', 'SECTION', 'LI', 'BLOCKQUOTE', 'TD', 'TH'];
    while (node && !BLOCKS.includes(node.tagName)) node = node.parentElement;

    const surroundingText = node
      ? (node.innerText || node.textContent || '').slice(0, 500).trim()
      : '';

    return { selectedText, surroundingText, selectionType };
  }

  function isFormField() {
    const a = document.activeElement;
    return a && (a.tagName === 'INPUT' || a.tagName === 'TEXTAREA' ||
                 a.tagName === 'SELECT' || a.isContentEditable);
  }

})();
