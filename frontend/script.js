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
let currentThreadId = null;
let threads = [];

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
 * Fetch and display all threads
 */
async function loadThreads() {
  try {
    const res = await fetch(`${CONFIG.apiBaseUrl}/api/threads`);
    const data = await res.json();
    threads = data.threads || [];
    renderThreadsSidebar();
  } catch (err) {
    console.error('Error loading threads:', err);
  }
}

/**
 * Render threads in sidebar
 */
function renderThreadsSidebar() {
  const sidebar = document.getElementById('threads-sidebar');
  if (!sidebar) return;
  
  sidebar.innerHTML = '<h3>Conversations</h3><button id="new-chat-btn" class="new-chat">+ New Chat</button>';
  
  threads.forEach(thread => {
    const item = document.createElement('div');
    item.className = `thread-item ${thread.thread_id === currentThreadId ? 'active' : ''}`;
    item.innerHTML = `
      <div class="thread-content">
        <div class="thread-title">${thread.title}</div>
        <div class="thread-preview">${thread.preview}</div>
      </div>
      <button class="thread-delete" data-thread-id="${thread.thread_id}">×</button>
    `;
    
    item.querySelector('.thread-content').addEventListener('click', () => {
      loadThread(thread.thread_id);
    });
    
    item.querySelector('.thread-delete').addEventListener('click', (e) => {
      e.stopPropagation();
      deleteThread(thread.thread_id);
    });
    
    sidebar.appendChild(item);
  });
  
  document.getElementById('new-chat-btn').addEventListener('click', startNewChat);
}

/**
 * Load a specific thread
 */
async function loadThread(threadId) {
  currentThreadId = threadId;
  chatEl.innerHTML = '';
  renderThreadsSidebar();
}

/**
 * Start a new chat
 */
function startNewChat() {
  currentThreadId = null;
  chatEl.innerHTML = '';
  renderEmptyState();
  renderThreadsSidebar();
  inputEl.focus();
}

/**
 * Delete a thread
 */
async function deleteThread(threadId) {
  if (!confirm('Delete this conversation?')) return;
  
  try {
    const res = await fetch(`${CONFIG.apiBaseUrl}/api/threads/${threadId}`, {
      method: 'DELETE'
    });
    
    if (res.ok) {
      threads = threads.filter(t => t.thread_id !== threadId);
      if (currentThreadId === threadId) {
        startNewChat();
      }
      renderThreadsSidebar();
    }
  } catch (err) {
    console.error('Error deleting thread:', err);
  }
}

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
      body: JSON.stringify({
        message: text,
        thread_id: currentThreadId,
        use_agent: useAgent
      })
    });

    if (!res.ok) {
      throw new Error('Server error');
    }

    const data = await res.json();
    addMessage('bot', data.reply ?? 'No response');

    // Update current thread if this was a new chat
    if (data.thread_id && !currentThreadId) {
      currentThreadId = data.thread_id;
    }

    // Refresh thread list and UI
    await loadThreads();
  } catch (err) {
    addMessage('bot', 'Could not connect to the backend. Make sure it is running.');
    console.error('Chat error:', err);
  } finally {
    setLoading(false);
  }
}

/**
 * Load all threads from backend
 */
async function loadThreads() {
  try {
    const res = await fetch(`${CONFIG.apiBaseUrl}/api/threads`);
    if (!res.ok) throw new Error('Failed to load threads');
    
    const data = await res.json();
    threads = data.threads || [];
    renderThreadsSidebar();
  } catch (err) {
    console.error('Error loading threads:', err);
  }
}

/**
 * Edit a thread name
 * @param {string} threadId - Thread ID to edit
 * @param {string} currentTitle - Current thread title
 */
async function editThreadName(threadId, currentTitle) {
  const newTitle = prompt('Enter new chat name:', currentTitle);
  
  if (newTitle === null) return; // User cancelled
  if (newTitle.trim() === '') {
    alert('Chat name cannot be empty');
    return;
  }

  try {
    const res = await fetch(`${CONFIG.apiBaseUrl}/api/threads/${threadId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle.trim() })
    });

    if (!res.ok) throw new Error('Failed to update thread name');

    const data = await res.json();
    if (data.success) {
      // Update local thread data
      const thread = threads.find(t => t.thread_id === threadId);
      if (thread) {
        thread.title = newTitle.trim();
      }
      renderThreadsSidebar();
    } else {
      alert('Failed to update chat name');
    }
  } catch (err) {
    console.error('Error editing thread name:', err);
    alert('Could not update chat name');
  }
}

/**
 * Render threads in sidebar
 */
function renderThreadsSidebar() {
  const sidebarEl = document.getElementById('threads-sidebar');
  const threadList = sidebarEl.querySelector('.thread-list') || (() => {
    const list = document.createElement('div');
    list.className = 'thread-list';
    sidebarEl.appendChild(list);
    return list;
  })();

  threadList.innerHTML = '';

  threads.forEach(thread => {
    const item = document.createElement('div');
    item.className = `thread-item ${thread.thread_id === currentThreadId ? 'active' : ''}`;
    
    const content = document.createElement('div');
    content.className = 'thread-content';
    content.addEventListener('click', () => loadThread(thread.thread_id));
    
    const title = document.createElement('div');
    title.className = 'thread-title';
    title.textContent = thread.title || 'Untitled';
    
    const preview = document.createElement('div');
    preview.className = 'thread-preview';
    preview.textContent = thread.preview || 'No messages';
    
    content.appendChild(title);
    content.appendChild(preview);
    
    const actions = document.createElement('div');
    actions.className = 'thread-actions';
    
    const editBtn = document.createElement('button');
    editBtn.className = 'thread-edit';
    editBtn.textContent = '✎';
    editBtn.title = 'Edit chat name';
    editBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      editThreadName(thread.thread_id, thread.title);
    });
    
    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'thread-delete';
    deleteBtn.textContent = '✕';
    deleteBtn.title = 'Delete conversation';
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteThread(thread.thread_id);
    });
    
    actions.appendChild(editBtn);
    actions.appendChild(deleteBtn);
    
    item.appendChild(content);
    item.appendChild(actions);
    threadList.appendChild(item);
  });
}

/**
 * Load a specific thread
 * @param {string} threadId - Thread ID to load
 */
async function loadThread(threadId) {
  currentThreadId = threadId;
  chatEl.innerHTML = '';
  renderThreadsSidebar();
  
  // Fetch and display previous messages for this thread
  try {
    const res = await fetch(`${CONFIG.apiBaseUrl}/api/threads/${threadId}/messages`);
    if (!res.ok) {
      throw new Error('Failed to load messages');
    }
    
    const data = await res.json();
    const messages = data.messages || [];
    
    if (messages.length === 0) {
      renderEmptyState();
    } else {
      // Display all previous messages
      messages.forEach(msg => {
        addMessage(msg.role === 'user' ? 'user' : 'bot', msg.content);
      });
    }
  } catch (err) {
    console.error('Error loading thread messages:', err);
    addMessage('bot', 'Could not load previous messages.');
  }
}

/**
 * Start a new chat
 */
function startNewChat() {
  currentThreadId = null;
  chatEl.innerHTML = '';
  renderEmptyState();
  renderThreadsSidebar();
}

/**
 * Delete a thread
 * @param {string} threadId - Thread ID to delete
 */
async function deleteThread(threadId) {
  if (!confirm('Delete this conversation?')) return;

  try {
    const res = await fetch(`${CONFIG.apiBaseUrl}/api/threads/${threadId}`, {
      method: 'DELETE'
    });

    if (!res.ok) throw new Error('Failed to delete thread');

    if (currentThreadId === threadId) {
      startNewChat();
    } else {
      await loadThreads();
    }
  } catch (err) {
    console.error('Error deleting thread:', err);
    alert('Failed to delete conversation');
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

  // Set up new chat button
  const sidebarEl = document.getElementById('threads-sidebar');
  const newChatBtn = document.createElement('button');
  newChatBtn.className = 'new-chat';
  newChatBtn.textContent = '+ New Chat';
  newChatBtn.addEventListener('click', startNewChat);
  
  // Insert at top of sidebar
  sidebarEl.insertBefore(newChatBtn, sidebarEl.firstChild);
}

/**
 * Initialize the application
 */
async function initialize() {
  // Set up initial UI state
  modeToggleEl.classList.add('active');
  modeLabelEl.textContent = 'Agent Mode';

  // Load existing threads
  await loadThreads();

  // Render UI
  renderEmptyState();
  renderPrompts();

  // Set up event listeners
  initializeEventListeners();
}

// Start the app when DOM is ready
document.addEventListener('DOMContentLoaded', initialize);
