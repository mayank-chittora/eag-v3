// popup/popup.js — Reading Assistant settings page
// Handles API key entry, model selection, validation, save, and load.

const keyInput      = document.getElementById('api-key-input');
const modelSelect   = document.getElementById('model-select');
const saveBtn       = document.getElementById('save-btn');
const statusMsg     = document.getElementById('status-msg');
const toggleBtn     = document.getElementById('toggle-visibility');

// ─── Load existing settings on popup open ────────────────────────────────────

chrome.storage.local.get(['geminiApiKey', 'geminiModel'], ({ geminiApiKey, geminiModel }) => {
  if (geminiApiKey) {
    keyInput.value = geminiApiKey;
    keyInput.type  = 'password';
  }
  if (geminiModel) {
    modelSelect.value = geminiModel;
  }
});

// ─── Toggle key visibility ────────────────────────────────────────────────────

toggleBtn.addEventListener('click', () => {
  keyInput.type = keyInput.type === 'password' ? 'text' : 'password';
});

// ─── Save settings ────────────────────────────────────────────────────────────

saveBtn.addEventListener('click', () => {
  const key = keyInput.value.trim();

  if (!key) {
    showStatus('Please enter your Gemini API key.', 'error');
    return;
  }

  if (key.length < 10) {
    showStatus('That key looks too short. Please paste your full Gemini API key.', 'error');
    return;
  }

  chrome.storage.local.set({ geminiApiKey: key, geminiModel: modelSelect.value }, () => {
    if (chrome.runtime.lastError) {
      showStatus('Failed to save settings. Please try again.', 'error');
      return;
    }
    showStatus('Settings saved! You can now use Reading Assistant.', 'success');
  });
});

// Allow saving with Enter key
keyInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') saveBtn.click();
});

// ─── Status message helper ────────────────────────────────────────────────────

function showStatus(message, type) {
  statusMsg.textContent = message;
  statusMsg.className   = `status status--${type}`;

  clearTimeout(showStatus._timer);
  showStatus._timer = setTimeout(() => {
    statusMsg.textContent = '';
    statusMsg.className   = 'status';
  }, 4000);
}
