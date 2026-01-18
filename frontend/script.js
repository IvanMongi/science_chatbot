// DOM Elements
const chatEl = document.getElementById('chat');
const formEl = document.getElementById('chat-form');
const inputEl = document.getElementById('input');
const sendBtn = document.getElementById('send');
const suggestionsEl = document.getElementById('suggestions');
const modeToggleEl = document.getElementById('mode-toggle');
const modeLabelEl = document.getElementById('mode-label');

// State
let useAgent = true;

// Configuration
const CONFIG = {
  apiBaseUrl: 'http://127.0.0.1:8000',
  suggestedPrompts: [
    'What evidence supports dark matter?',
    'Explain the Krebs cycle and its key steps.',
    'What are the differences between CRISPR-Cas9 and base editing?',
    'Summarize the original transformers paper (2017).'
  ]
};

/**
 * Add a message to the chat display
 * @param {string} role - 'user' or 'bot'
 * @param {string} text - Message content
 */
function addMessage(role, text) {
  const container = document.createElement('div');
  container.className = 'message';

  const avatar = document.createElement('div');
  avatar.className = `avatar ${role === 'user' ? 'user' : 'bot'}`;
  avatar.textContent = role === 'user' ? 'You' : 'AI';

  const content = document.createElement('div');
  const meta = document.createElement('div');
  meta.className = 'meta';
  meta.textContent = role === 'user' ? 'User' : (useAgent ? 'Assistant' : 'Assistant (echo)');

  const bubble = document.createElement('div');
  bubble.className = 'bubble';

  // Render markdown for bot messages
  if (role === 'bot') {
    if (typeof marked !== 'undefined' && marked.parse) {
      bubble.innerHTML = marked.parse(text);
    } else {
      bubble.textContent = text;
    }
  } else {
    bubble.textContent = text;
  }

  content.appendChild(meta);
  content.appendChild(bubble);
  container.appendChild(avatar);
  container.appendChild(content);

  chatEl.appendChild(container);
  chatEl.scrollTop = chatEl.scrollHeight;
}

/**
 * Render empty state when no messages exist
 */
function renderEmptyState() {
  if (chatEl.childElementCount === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty';
    empty.textContent = 'Ask your first scientific question or try an example.';
    chatEl.appendChild(empty);
  }
}

/**
 * Remove empty state when first message arrives
 */
function clearEmptyState() {
  if (chatEl.firstChild && chatEl.firstChild.classList.contains('empty')) {
    chatEl.removeChild(chatEl.firstChild);
  }
}

/**
 * Send a message to the backend
 * @param {string} text - User message
 */
async function sendMessage(text) {
  clearEmptyState();
  addMessage('user', text);
  setLoading(true);

  try {
    const res = await fetch(`${CONFIG.apiBaseUrl}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text, use_agent: useAgent })
    });

    if (!res.ok) {
      throw new Error('Server error');
    }

    const data = await res.json();
    addMessage('bot', data.reply ?? 'No response');
  } catch (err) {
    addMessage('bot', 'Could not connect to the backend. Make sure it is running.');
    console.error('Chat error:', err);
  } finally {
    setLoading(false);
  }
}

/**
 * Update UI loading state
 * @param {boolean} isLoading - Whether loading or not
 */
function setLoading(isLoading) {
  sendBtn.disabled = isLoading;
  inputEl.disabled = isLoading;
  sendBtn.textContent = isLoading ? 'Sending...' : 'Send';
}

/**
 * Toggle between agent mode and echo mode
 */
function toggleMode() {
  useAgent = !useAgent;
  modeToggleEl.classList.toggle('active', useAgent);
  modeLabelEl.textContent = useAgent ? 'Agent Mode' : 'Echo Mode';
}

/**
 * Render suggested prompt pills
 */
function renderPrompts() {
  CONFIG.suggestedPrompts.forEach((prompt) => {
    const pill = document.createElement('button');
    pill.type = 'button';
    pill.className = 'pill';
    pill.textContent = prompt;
    pill.addEventListener('click', () => {
      inputEl.value = prompt;
      inputEl.focus();
    });
    suggestionsEl.appendChild(pill);
  });
}

/**
 * Initialize event listeners
 */
function initializeEventListeners() {
  formEl.addEventListener('submit', (e) => {
    e.preventDefault();
    const text = inputEl.value.trim();
    if (!text) return;
    inputEl.value = '';
    sendMessage(text);
  });

  modeToggleEl.addEventListener('click', toggleMode);
}

/**
 * Initialize the application
 */
function initialize() {
  // Set up initial UI state
  modeToggleEl.classList.add('active');
  modeLabelEl.textContent = 'Agent Mode';

  // Render UI
  renderEmptyState();
  renderPrompts();

  // Set up event listeners
  initializeEventListeners();
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', initialize);
