const indexPageBtn = document.getElementById('log-page-btn');
const summarizeBtn = document.getElementById('summarize-btn');
const queryInput = document.getElementById('ask-input');
const userQueryBtn = document.getElementById('ask-btn');
const resultsDiv = document.getElementById('results');
const backendStatus = document.getElementById('backend-status');
const statsSection = document.getElementById('stats-section');
const statsContent = document.getElementById('stats-content');
const indexedPagesList = document.getElementById('indexed-pages-list');
const settingsForm = document.getElementById('options-form');
const backendUrlInput = document.getElementById('backend-url');
const saveSettings = document.getElementById('save-status');

const BACKEND_BASE = 'http://127.0.0.1:8000';

async function getCurrentTabUrl() {
  return new Promise((resolve) => {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      resolve(tabs[0].url);
    });
  });
}

async function checkBackendStatus() {
  try {
    const res = await fetch(`${BACKEND_BASE}/health`);
    if (res.ok) {
      backendStatus.classList.add('online');
      backendStatus.classList.remove('offline');
      backendStatus.title = 'Backend Online';
    } else {
      throw new Error();
    }
  } catch {
    backendStatus.classList.remove('online');
    backendStatus.classList.add('offline');
    backendStatus.title = 'Backend Offline';
  }
}

indexPageBtn.addEventListener('click', async () => {
  const url = await getCurrentTabUrl();
  indexPageBtn.classList.add('loading');
  indexPageBtn.disabled = true;
  fetch(`${BACKEND_BASE}/indexed-pages`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  })
    .then(res => res.json())
    .then(data => {
      indexPageBtn.classList.remove('loading');
      indexPageBtn.disabled = false;
      resultsDiv.textContent = 'Page indexed.';
      listIndexedPages();
    })
    .catch(() => {
      indexPageBtn.classList.remove('loading');
      indexPageBtn.disabled = false;
      resultsDiv.textContent = 'Error indexing page.';
    });
});


summarizeBtn.addEventListener('click', async () => {
  const url = await getCurrentTabUrl();
  summarizeBtn.classList.add('loading');
  summarizeBtn.disabled = true;
  fetch(`${BACKEND_BASE}/summaries`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  })
    .then(res => res.json())
    .then(data => {
      summarizeBtn.classList.remove('loading');
      summarizeBtn.disabled = false;
      let summary = data.summary;
      if (summary) {
        const match = summary.match(/{[\s\S]*}/);
        if (match) {
          try {
            const parsed = JSON.parse(match[0]);
            resultsDiv.innerHTML = parsed.answer.replace(/\n/g, '<br>');
          } catch {
            resultsDiv.textContent = summary;
          }
        } else {
          resultsDiv.textContent = summary;
        }
      } else {
        resultsDiv.textContent = data.error || 'No summary.';
      }
    })
    .catch(() => {
      summarizeBtn.classList.remove('loading');
      summarizeBtn.disabled = false;
      resultsDiv.textContent = 'Error summarizing page.';
    });
});

function renderResults(data) {
  if (!data) return resultsDiv.textContent = '';
  if (data.answer) {
    resultsDiv.innerHTML = `<div style="margin-bottom:10px;">${data.answer.replace(/\n/g, '<br>')}</div>`;
  }
  if (data.found_answer && Array.isArray(data.source_urls) && data.source_urls.length > 0) {
    data.source_urls.forEach(url => {
      const info = document.createElement('div');
      info.style.fontSize = '0.97em';
      info.style.margin = '7px 0 0 0';
      info.innerHTML = `From: <a href='${url}' target='_blank' rel='noopener noreferrer' style='color:#1b6ec2;text-decoration:underline;'>${url}</a>`;
      resultsDiv.appendChild(info);
    });
  }
}

userQueryBtn.addEventListener('click', async () => {
  const url = await getCurrentTabUrl();
  const query = queryInput.value.trim();
  if (!query) return;
  userQueryBtn.classList.add('loading');
  userQueryBtn.disabled = true;
  fetch(`${BACKEND_BASE}/queries`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({query, k: 5})
  })
    .then(res => res.json())
    .then(data => {
      userQueryBtn.classList.remove('loading');
      userQueryBtn.disabled = false;
      renderResults(data);
    })
    .catch(() => {
      userQueryBtn.classList.remove('loading');
      userQueryBtn.disabled = false;
      resultsDiv.textContent = 'Error querying.';
    });
});

async function listIndexedPages() {
  indexedPagesList.innerHTML = '<div>Loading...</div>';
  fetch(`${BACKEND_BASE}/indexed-pages`)
    .then(res => res.json())
    .then(data => {
      indexedPagesList.innerHTML = '';
      (data.urls || []).forEach(url => {
        const div = document.createElement('div');
        div.className = 'item';
        let displayText;
        try {
          const u = new URL(url);
          displayText = u.hostname + u.pathname;
          if (displayText.length > 40) {
            displayText = displayText.slice(0, 37) + '...';
          }
        } catch {
          displayText = url;
        }
        const a = document.createElement('a');
        a.href = url;
        a.textContent = displayText;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
        a.style.color = '#1b6ec2';
        a.style.textDecoration = 'underline';
        a.style.flex = '1';
        a.style.fontSize = '0.9em';
        a.style.whiteSpace = 'nowrap';
        a.style.overflow = 'hidden';
        a.style.textOverflow = 'ellipsis';
        a.title = url;
        div.appendChild(a);
        const delBtn = document.createElement('button');
        delBtn.className = 'ui icon button';
        delBtn.innerHTML = '<i class="trash icon"></i>';
        delBtn.title = 'Delete from index';
        delBtn.setAttribute('aria-label', `Delete ${url} from index`);
        delBtn.onclick = () => deletePage(url);
        div.appendChild(delBtn);
        indexedPagesList.appendChild(div);
      });
      if ((data.urls || []).length === 0) {
        indexedPagesList.innerHTML = '<div>No pages indexed.</div>';
      }
    });
}

async function deletePage(url) {
  fetch(`${BACKEND_BASE}/delete-indexed-pages`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({url})
  })
    .then(res => res.json())
    .then(data => {
      listIndexedPages();
      resultsDiv.textContent = `Deleted: ${url}`;
    });
}

function loadStats() {
  fetch(`${BACKEND_BASE}/index-stats`)
    .then(res => res.json())
    .then(data => {
      statsContent.innerHTML = `
        <div style="padding:10px 0;">
          <table class="ui compact table">
            <tr>
              <td style="font-weight:500;">Pages Indexed: Number of unique web pages stored.</td>
              <td style="color:#1b6ec2;font-weight:600;text-align:right;">${data.num_pages ?? '-'}</td>
            </tr>
            <tr>
              <td style="font-weight:500;">Total Chunks: Number of text sections split and embedded.</td>
              <td style="color:#1b6ec2;font-weight:600;text-align:right;">${data.num_chunks ?? '-'}</td>
            </tr>
            <tr>
              <td style="font-weight:500;">Vector Dimensions: Size of each embedding vector.</td>
              <td style="color:#1b6ec2;font-weight:600;text-align:right;">${data.embedding_dim ?? '-'}</td>
            </tr>
            <tr>
              <td style="font-weight:500;">FAISS Index Type: Algorithm used for fast search.</td>
              <td style="color:#1b6ec2;font-weight:600;text-align:right;">${data.faiss_index_type ?? '-'}</td>
            </tr>
          </table>
        </div>
      `;
    });
}

// Options form handling
settingsForm.addEventListener('submit', (e) => {
  e.preventDefault();
  const saveBtn = settingsForm.querySelector('button[type="submit"]');
  saveBtn.classList.add('loading');
  saveBtn.disabled = true;
  const url = backendUrlInput.value.trim();
  chrome.storage.sync.set({ backendUrl: url }, () => {
    saveSettings.classList.remove('hidden');
    saveSettings.textContent = 'Saved!';
    saveBtn.classList.remove('loading');
    saveBtn.disabled = false;
    setTimeout(() => {
      saveSettings.classList.add('hidden');
      saveSettings.textContent = '';
    }, 2000);
  });
});

// Load saved backend URL
chrome.storage.sync.get(['backendUrl'], (data) => {
  if (data.backendUrl) backendUrlInput.value = data.backendUrl;
});

// Auto-expand textarea
queryInput.addEventListener('input', function() {
  this.style.height = 'auto';
  this.style.height = (this.scrollHeight + 2) + 'px';
});

// Initialize Semantic UI components
document.addEventListener('DOMContentLoaded', () => {
  try {
    $('.ui.tabular.menu .item').tab({
      onVisible: function(tabPath) {
        console.log(`Switched to tab: ${tabPath}`);
        if (tabPath === 'stats') {
          loadStats();
        }
      }
    });
    $('.ui.accordion').accordion();
    $('.ui.modal').modal();
    checkBackendStatus();
    listIndexedPages();
  } catch (error) {
    console.error('Error initializing UI components:', error);
  }
});