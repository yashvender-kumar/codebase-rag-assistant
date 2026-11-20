const API_BASE = "http://127.0.0.1:8000";
const knownFiles = new Set();
let isRepoIndexed = false;

function renderFileList(files) {
  if (!files || files.length === 0) return;
  const listEl = document.getElementById("indexedFilesList");
  listEl.innerHTML = "";

  files.forEach(filePath => {
    const item = document.createElement("div");
    item.className = "file-item";
    item.onclick = () => askAboutFile(filePath);
    item.innerHTML = `
      <svg class="file-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14 2 14 8 20 8"/>
      </svg>
      <span>${escapeHtml(filePath)}</span>
    `;
    listEl.appendChild(item);
  });
}

function askAboutFile(filePath) {
  if (!isRepoIndexed) {
    alert("Please index a repository first.");
    return;
  }
  const input = document.getElementById("questionInput");
  input.value = `Explain what ${filePath} does and its key functions.`;
  input.focus();
}

function triggerSuggested(text) {
  if (!isRepoIndexed) {
    alert("Please paste a GitHub repository URL and click 'Index Repo' first!");
    document.getElementById("repoUrl").focus();
    return;
  }
  const input = document.getElementById("questionInput");
  input.value = text;
  sendMessage(new Event("submit"));
}

function clearMessages() {
  document.getElementById("messagesArea").innerHTML = "";
}

async function indexRepository() {
  const repoInput = document.getElementById("repoUrl");
  const repoUrl = repoInput.value.trim().replace(/\s+/g, "");
  repoInput.value = repoUrl;

  if (!repoUrl) {
    alert("Please enter a GitHub repository URL (e.g., https://github.com/owner/repo).");
    return;
  }

  const btn = document.getElementById("indexBtn");
  btn.disabled = true;
  btn.textContent = "Indexing...";

  try {
    const res = await fetch(`${API_BASE}/ingest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Ingestion failed");

    isRepoIndexed = true;
    document.getElementById("filesProcessedVal").textContent = data.files_processed ?? 0;
    document.getElementById("chunksIndexedVal").textContent = data.chunks_indexed ?? 0;

    // Enable chat input after successful indexing
    const qInput = document.getElementById("questionInput");
    const sendBtn = document.getElementById("sendBtn");
    qInput.disabled = false;
    sendBtn.disabled = false;
    qInput.placeholder = "Ask anything about this repository...";

    if (Array.isArray(data.files) && data.files.length > 0) {
      knownFiles.clear();
      data.files.forEach(f => knownFiles.add(f));
      renderFileList(Array.from(knownFiles));
    }

    const area = document.getElementById("messagesArea");
    area.innerHTML = "";
    const toast = document.createElement("div");
    toast.className = "status-toast";
    toast.innerHTML = `Indexed <strong>${escapeHtml(repoUrl)}</strong> (${data.files_processed} files, ${data.chunks_indexed} chunks). Ask your questions below!`;
    area.appendChild(toast);
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Index Repo";
  }
}

function addUserBubble(text) {
  const area = document.getElementById("messagesArea");
  const row = document.createElement("div");
  row.className = "msg-user-row";
  row.innerHTML = `
    <div class="msg-user-bubble">${escapeHtml(text)}</div>
    <div class="user-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
        <path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/>
      </svg>
    </div>
  `;
  area.appendChild(row);
  area.scrollTop = area.scrollHeight;
}

function addAiBubble(markdownAnswer, sources) {
  const area = document.getElementById("messagesArea");
  const row = document.createElement("div");
  row.className = "msg-ai-row";

  const rawHtml = marked.parse(markdownAnswer);
  const tempDiv = document.createElement("div");
  tempDiv.innerHTML = rawHtml;

  tempDiv.querySelectorAll("pre").forEach(pre => {
    const wrapper = document.createElement("div");
    wrapper.className = "code-wrapper";

    const copyBtn = document.createElement("button");
    copyBtn.className = "copy-code-btn";
    copyBtn.type = "button";
    copyBtn.innerHTML = `
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
      <span>Copy</span>
    `;
    copyBtn.onclick = () => {
      const codeText = pre.innerText;
      navigator.clipboard.writeText(codeText);
      copyBtn.querySelector("span").textContent = "Copied!";
      setTimeout(() => (copyBtn.querySelector("span").textContent = "Copy"), 1500);
    };

    pre.parentNode.insertBefore(wrapper, pre);
    wrapper.appendChild(copyBtn);
    wrapper.appendChild(pre);

    const codeEl = pre.querySelector("code");
    if (codeEl) hljs.highlightElement(codeEl);
  });

  let sourcesHtml = "";
  if (Array.isArray(sources) && sources.length > 0) {
    sources.forEach(s => knownFiles.add(s));
    renderFileList(Array.from(knownFiles));

    sourcesHtml = `
      <div class="sources-row">
        ${sources.map(src => `
          <span class="source-pill">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
              <polyline points="14 2 14 8 20 8"/>
            </svg>
            ${escapeHtml(src)}
          </span>
        `).join("")}
      </div>
    `;
  }

  row.innerHTML = `
    <div class="ai-avatar">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 2a4 4 0 0 1 4 4v2h2a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-8a2 2 0 0 1 2-2h2V6a4 4 0 0 1 4-4z"/>
        <circle cx="9" cy="14" r="1"/><circle cx="15" cy="14" r="1"/>
      </svg>
    </div>
    <div class="msg-ai-content">
      ${tempDiv.innerHTML}
      ${sourcesHtml}
    </div>
  `;

  area.appendChild(row);
  area.scrollTop = area.scrollHeight;
}

async function sendMessage(e) {
  e.preventDefault();
  const repoUrl = document.getElementById("repoUrl").value.trim();
  const input = document.getElementById("questionInput");
  const question = input.value.trim();
  if (!repoUrl || !question) return;

  addUserBubble(question);
  input.value = "";

  const sendBtn = document.getElementById("sendBtn");
  sendBtn.disabled = true;

  const area = document.getElementById("messagesArea");
  const typing = document.createElement("div");
  typing.className = "status-toast";
  typing.textContent = "Analyzing repository...";
  area.appendChild(typing);
  area.scrollTop = area.scrollHeight;

  try {
    const res = await fetch(`${API_BASE}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ repo_url: repoUrl, question })
    });
    const data = await res.json();
    typing.remove();

    if (!res.ok) throw new Error(data.detail || "Failed to fetch answer");
    addAiBubble(data.answer, data.sources);
  } catch (err) {
    typing.remove();
    addAiBubble(`**Error:** ${err.message}`, []);
  } finally {
    sendBtn.disabled = false;
  }
}

function escapeHtml(str) {
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}