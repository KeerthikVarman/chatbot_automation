/* AI Workflow Builder - UI/UX Pro Max Interactive Frontend Client */

let conversationId = 'session_' + Math.random().toString(36).substring(2, 10);
let currentWorkflowSpec = null;

// Initialize Mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  themeVariables: {
    primaryColor: '#7C3AED',
    primaryTextColor: '#F8FAFC',
    primaryBorderColor: '#6366F1',
    lineColor: '#06B6D4',
    secondaryColor: '#1E293B',
    tertiaryColor: '#0F172A'
  }
});

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('session-display').textContent = `Session: ${conversationId}`;

  // Attach Event Listeners
  document.getElementById('chat-form').addEventListener('submit', handleFormSubmit);
  document.getElementById('btn-reset').addEventListener('click', resetSession);
  document.getElementById('btn-export').addEventListener('click', exportWorkflowJson);

  // Preset Cards
  document.querySelectorAll('.preset-card').forEach(card => {
    card.addEventListener('click', () => {
      const prompt = card.getAttribute('data-prompt');
      if (prompt) {
        resetSession();
        sendMessage(prompt);
      }
    });
  });

  // Suggestion Chips
  document.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      const text = chip.getAttribute('data-text');
      const input = document.getElementById('user-input');
      input.value = text;
      input.focus();
    });
  });
});

function resetSession() {
  conversationId = 'session_' + Math.random().toString(36).substring(2, 10);
  currentWorkflowSpec = null;
  document.getElementById('session-display').textContent = `Session: ${conversationId}`;
  document.getElementById('btn-export').style.display = 'none';

  // Reset Chat
  const chatMessages = document.getElementById('chat-messages');
  chatMessages.innerHTML = `
    <div class="chat-bubble assistant">
      <div class="chat-avatar">⚡</div>
      <div class="chat-content">
        <strong>Session reset!</strong> Describe your automation goal in plain English to start a new workflow session.
      </div>
    </div>
  `;

  // Reset Inspector
  document.getElementById('readiness-pct').textContent = '0%';
  document.getElementById('progress-fill').style.width = '0%';
  document.getElementById('wf-type').textContent = 'Not determined';
  document.getElementById('req-badges').innerHTML = '<span style="font-size: 0.8rem; color: var(--text-dim);">Awaiting prompt...</span>';
  document.getElementById('param-table').innerHTML = '<tbody><tr><td colspan="2" style="color: var(--text-dim); text-align: center;">No parameters collected yet.</td></tr></tbody>';
  document.getElementById('miss-badges').innerHTML = '<span style="font-size: 0.8rem; color: var(--text-dim);">None</span>';
  document.getElementById('dag-container').innerHTML = '<span style="color: var(--text-dim); font-size: 0.85rem;">Generated DAG workflow diagram will render here when ready.</span>';
  document.getElementById('status-badge').className = 'badge badge-col';
  document.getElementById('status-badge').innerHTML = '&bull; Ready';
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const inputEl = document.getElementById('user-input');
  const message = inputEl.value.trim();
  if (!message) return;

  inputEl.value = '';
  await sendMessage(message);
}

async function sendMessage(message) {
  appendUserMessage(message);
  showTypingIndicator();

  try {
    const response = await fetch('/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        conversation_id: conversationId,
        message: message
      })
    });

    removeTypingIndicator();

    if (!response.ok) {
      const err = await response.json();
      appendAssistantMessage(`⚠️ Error processing request: ${err.detail || 'Server error'}`);
      return;
    }

    const data = await response.json();
    appendAssistantMessage(data.message);
    updateInspector(data);

  } catch (err) {
    removeTypingIndicator();
    appendAssistantMessage(`⚠️ Network error: Could not connect to API server. ${err.message}`);
  }
}

function appendUserMessage(text) {
  const chatMessages = document.getElementById('chat-messages');
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble user';
  bubble.innerHTML = `
    <div class="chat-avatar">👤</div>
    <div class="chat-content">${escapeHtml(text)}</div>
  `;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendAssistantMessage(text) {
  const chatMessages = document.getElementById('chat-messages');
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble assistant';
  bubble.innerHTML = `
    <div class="chat-avatar">⚡</div>
    <div class="chat-content">${escapeHtml(text)}</div>
  `;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function showTypingIndicator() {
  const chatMessages = document.getElementById('chat-messages');
  const bubble = document.createElement('div');
  bubble.className = 'chat-bubble assistant';
  bubble.id = 'typing-bubble';
  bubble.innerHTML = `
    <div class="chat-avatar">⚡</div>
    <div class="chat-content">
      <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
      </div>
    </div>
  `;
  chatMessages.appendChild(bubble);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function removeTypingIndicator() {
  const el = document.getElementById('typing-bubble');
  if (el) el.remove();
}

function updateInspector(data) {
  const ready = data.workflow_ready;
  
  // Status Badge
  const statusBadge = document.getElementById('status-badge');
  if (ready) {
    statusBadge.className = 'badge badge-col';
    statusBadge.innerHTML = '⚡ Workflow Ready';
    document.getElementById('btn-export').style.display = 'inline-flex';
  } else {
    statusBadge.className = 'badge badge-miss';
    statusBadge.innerHTML = '❓ Clarification Required';
  }

  // Progress Bar
  const missingCount = (data.missing_information || []).length + (data.ambiguities || []).length;
  const collectedCount = Object.keys(data.collected_information || {}).length;
  const total = collectedCount + missingCount;
  let pct = 0;
  if (ready) {
    pct = 100;
  } else if (total > 0) {
    pct = Math.min(90, Math.round((collectedCount / total) * 100));
  } else if (collectedCount > 0) {
    pct = 50;
  }

  document.getElementById('readiness-pct').textContent = `${pct}%`;
  document.getElementById('progress-fill').style.width = `${pct}%`;

  // Collected Information Table
  const paramTable = document.getElementById('param-table');
  const collected = data.collected_information || {};
  const keys = Object.keys(collected);

  if (keys.length > 0) {
    let rowsHtml = '<tbody>';
    for (const k of keys) {
      rowsHtml += `
        <tr>
          <td class="key">${escapeHtml(k)}</td>
          <td class="val">${escapeHtml(String(collected[k]))}</td>
        </tr>
      `;
    }
    rowsHtml += '</tbody>';
    paramTable.innerHTML = rowsHtml;
  } else {
    paramTable.innerHTML = '<tbody><tr><td colspan="2" style="color: var(--text-dim); text-align: center;">No parameters collected yet.</td></tr></tbody>';
  }

  // Missing Badges
  const missContainer = document.getElementById('miss-badges');
  const missingList = data.missing_information || [];
  const ambigList = data.ambiguities || [];

  if (missingList.length > 0 || ambigList.length > 0) {
    let badgesHtml = '';
    missingList.forEach(m => {
      badgesHtml += `<span class="badge badge-miss">❓ ${escapeHtml(m)}</span>`;
    });
    ambigList.forEach(a => {
      badgesHtml += `<span class="badge badge-miss">⚠️ ${escapeHtml(a)}</span>`;
    });
    missContainer.innerHTML = badgesHtml;
  } else {
    missContainer.innerHTML = '<span style="font-size: 0.8rem; color: var(--success);">&check; None</span>';
  }

  // Render Workflow DAG if available
  if (data.workflow) {
    currentWorkflowSpec = data.workflow;
    document.getElementById('wf-type').textContent = data.workflow.name || 'Custom Workflow';
    renderMermaidDag(data.workflow);
  }
}

function renderMermaidDag(workflow) {
  const container = document.getElementById('dag-container');
  const nodes = workflow.nodes || [];
  const edges = workflow.edges || [];

  let mermaidStr = 'graph LR\n';
  nodes.forEach(n => {
    const id = n.id.replace(/-/g, '_');
    const name = n.name || id;
    const type = (n.type || 'NODE').toUpperCase();
    mermaidStr += `    ${id}["<b>${escapeHtml(name)}</b><br/><code>[${type}]</code>"]\n`;
  });

  edges.forEach(e => {
    const src = e.source.replace(/-/g, '_');
    const tgt = e.target.replace(/-/g, '_');
    mermaidStr += `    ${src} --> ${tgt}\n`;
  });

  const dagId = 'dag_' + Math.random().toString(36).substring(2, 8);
  container.innerHTML = `<div class="mermaid" id="${dagId}">${mermaidStr}</div>`;
  
  try {
    mermaid.run({ nodes: [document.getElementById(dagId)] });
  } catch (e) {
    console.error('Mermaid render error:', e);
  }
}

function exportWorkflowJson() {
  if (!currentWorkflowSpec) return;
  const jsonStr = JSON.stringify(currentWorkflowSpec, null, 2);
  const blob = new Blob([jsonStr], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${(currentWorkflowSpec.name || 'workflow').toLowerCase().replace(/\s+/g, '_')}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
