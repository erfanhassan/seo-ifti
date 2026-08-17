/**
 * GitHub Advocate Module - Frontend Controller
 * Preserves 100% of the repository checklist scanner, AI documentation generator,
 * commit applier, topics/description synchronizer, and v1.0.0 release creator.
 */

window.GitHubModule = (function () {
  let currentRepos = [];
  let pendingChanges = null;
  let activeTab = 'readme';

  function init() {
    loadUserProfile();
    loadRepositories();
  }

  async function loadUserProfile() {
    try {
      const res = await fetch('/api/user-profile');
      const data = await res.json();
      if (data.authenticated) {
        const profileEl = document.getElementById('ghUserProfileSection');
        if (profileEl) {
          profileEl.innerHTML = `
            <div class="flex items-center gap-3">
              <img src="${data.avatar_url}" alt="${data.login}" class="w-10 h-10 rounded-full border border-cyan-500/40">
              <div>
                <h4 class="text-sm font-bold text-slate-200">${data.name || data.login}</h4>
                <p class="text-xs text-slate-400">@${data.login} • ${data.public_repos} Public Repos</p>
              </div>
            </div>
          `;
        }
      }
    } catch (e) {
      console.warn('Profile load warning:', e);
    }
  }

  async function loadRepositories() {
    const tbody = document.getElementById('reposTableBody');
    if (!tbody) return;

    tbody.innerHTML = `
      <tr>
        <td colspan="5" class="text-center py-8 text-slate-400">
          <i class="fas fa-circle-notch fa-spin text-cyan-400 mr-2"></i> Scanning GitHub repositories & 8-point checklist...
        </td>
      </tr>
    `;

    try {
      const res = await fetch('/api/repos');
      const data = await res.json();
      currentRepos = data.repositories || [];

      if (currentRepos.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="5" class="text-center py-8 text-slate-500">
              No public repositories found.
            </td>
          </tr>
        `;
        return;
      }

      tbody.innerHTML = currentRepos.map(repo => {
        const status = repo.status || {};
        const score = status.score || 0;
        const color = score >= 7 ? 'text-emerald-400' : score >= 4 ? 'text-amber-400' : 'text-red-400';

        return `
          <tr class="border-b border-slate-800/60 hover:bg-slate-900/50 transition">
            <td class="py-3 px-4 font-semibold text-slate-200">
              <a href="${repo.html_url}" target="_blank" class="hover:text-cyan-400 transition flex items-center gap-1.5">
                <i class="fab fa-github text-slate-400"></i> ${repo.name}
              </a>
              <span class="text-[11px] text-slate-500 block font-normal">${repo.description || 'No description'}</span>
            </td>
            <td class="py-3 px-4 text-xs text-slate-400">${repo.language || 'Python'}</td>
            <td class="py-3 px-4">
              <div class="flex items-center gap-1">
                ${renderStatusBadge('README', status.has_readme)}
                ${renderStatusBadge('LICENSE', status.has_license)}
                ${renderStatusBadge('CONTRIB', status.has_contributing)}
                ${renderStatusBadge('CONDUCT', status.has_code_of_conduct)}
                ${renderStatusBadge('GITIGNORE', status.has_gitignore)}
                ${renderStatusBadge('ISSUES', status.has_issue_templates)}
                ${renderStatusBadge('PR', status.has_pr_template)}
                ${renderStatusBadge('TOPICS', status.has_topics)}
              </div>
            </td>
            <td class="py-3 px-4 text-sm font-bold ${color}">${score} / 8</td>
            <td class="py-3 px-4 text-right">
              <button onclick="window.GitHubModule.scanRepo('${repo.owner}', '${repo.name}')" class="px-3 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 text-xs font-bold border border-cyan-500/30 transition flex items-center gap-1.5 ml-auto">
                <i class="fas fa-wand-magic-sparkles text-[10px]"></i> Polish Repo
              </button>
            </td>
          </tr>
        `;
      }).join('');

    } catch (err) {
      tbody.innerHTML = `
        <tr>
          <td colspan="5" class="text-center py-8 text-red-400">
            Failed to load repositories: ${err.message}
          </td>
        </tr>
      `;
    }
  }

  function renderStatusBadge(label, passed) {
    return passed
      ? `<span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30" title="${label}: Present">✓</span>`
      : `<span class="px-1.5 py-0.5 rounded text-[9px] font-bold bg-slate-800 text-slate-500 border border-slate-700" title="${label}: Missing">✗</span>`;
  }

  async function scanRepo(owner, repo) {
    const modal = document.getElementById('ghChangesModal');
    if (!modal) return;

    modal.classList.remove('hidden');
    document.getElementById('ghModalTitle').textContent = `Polishing ${owner}/${repo}`;
    document.getElementById('ghModalBody').innerHTML = `
      <div class="py-16 text-center text-slate-400">
        <i class="fas fa-circle-notch fa-spin text-3xl text-cyan-400 mb-3"></i>
        <p class="font-medium text-slate-200">DeepSeek AI Open Source Architect is analyzing codebase manifests...</p>
        <p class="text-xs text-slate-500 mt-1">Generating killer README, MIT License, Contributing Guide, Issue Templates, and SEO topics.</p>
      </div>
    `;

    try {
      const res = await fetch(`/api/changes?owner=${owner}&repo=${repo}`);
      const data = await res.json();
      pendingChanges = data;
      renderChangesModalContent(data);
    } catch (err) {
      document.getElementById('ghModalBody').innerHTML = `
        <div class="py-12 text-center text-red-400">
          <p>Failed to generate changes: ${err.message}</p>
        </div>
      `;
    }
  }

  let currentActiveIndex = 0;

  function renderChangesModalContent(data) {
    const changes = data.changes || [];
    const topics = data.topics || [];
    const description = data.description || '';

    currentActiveIndex = 0;
    let activeChange = changes[0] || { content: '' };

    document.getElementById('ghModalBody').innerHTML = `
      <div class="space-y-4">
        <!-- Metadata Synced Preview -->
        <div class="bg-slate-950/60 rounded-xl p-3.5 border border-slate-800 text-xs space-y-3">
          <div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">Proposed About Description:</span>
              <button onclick="window.GitHubModule.copyField('ghEditDescription', 'Description')" class="text-cyan-400 hover:text-cyan-300 text-[11px] font-semibold flex items-center gap-1">
                <i class="fas fa-copy"></i> Copy
              </button>
            </div>
            <input type="text" id="ghEditDescription" value="${escapeQuotes(description)}" class="glass-input w-full px-3 py-2 rounded-lg text-xs mt-1">
          </div>
          <div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400 font-semibold uppercase tracking-wider text-[10px]">SEO Topics (Item #8 on Checklist):</span>
              <button onclick="window.GitHubModule.copyField('ghEditTopics', 'Topics')" class="text-cyan-400 hover:text-cyan-300 text-[11px] font-semibold flex items-center gap-1">
                <i class="fas fa-copy"></i> Copy Topics
              </button>
            </div>
            <input type="text" id="ghEditTopics" value="${topics.join(', ')}" class="glass-input w-full px-3 py-2 rounded-lg text-xs mt-1">
            <p class="text-[10px] text-slate-500 mt-1">
              <i class="fas fa-info-circle mr-0.5"></i>
              GitHub requires <strong>Administration (Read & Write)</strong> on Fine-Grained tokens to set topics via API. If restricted, you can 1-click copy them here and paste into your repo settings.
            </p>
          </div>
        </div>

        <!-- File Tabs -->
        <div class="flex flex-wrap gap-1.5 border-b border-slate-800 pb-2" id="ghFileTabs">
          ${changes.map((c, i) => `
            <button class="px-3 py-1 rounded-lg text-xs font-semibold ${i === 0 ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40' : 'text-slate-400 hover:text-slate-200'}" onclick="window.GitHubModule.selectChangeTab(${i})">
              ${c.path}
            </button>
          `).join('')}
        </div>

        <!-- Editor View -->
        <div>
          <textarea id="ghActiveFileContent" class="glass-input w-full h-72 rounded-xl p-4 font-mono text-xs leading-relaxed text-slate-200 resize-none">${escapeHtml(activeChange.content)}</textarea>
        </div>

        <!-- Release Checkbox -->
        <div class="flex items-center gap-2 pt-2">
          <input type="checkbox" id="ghCreateReleaseCheckbox" class="rounded bg-slate-900 border-slate-700 text-cyan-500 focus:ring-0">
          <label for="ghCreateReleaseCheckbox" class="text-xs text-slate-300">
            Publish official <strong>v1.0.0 Production Release</strong> with generated release notes
          </label>
        </div>
      </div>
    `;

    const editorEl = document.getElementById('ghActiveFileContent');
    if (editorEl) {
      editorEl.addEventListener('input', () => {
        if (pendingChanges && pendingChanges.changes[currentActiveIndex]) {
          pendingChanges.changes[currentActiveIndex].content = editorEl.value;
        }
      });
    }

    document.getElementById('ghApplyBtn').onclick = applyCurrentChanges;
  }

  function copyField(fieldId, label) {
    const input = document.getElementById(fieldId);
    if (!input || !input.value) return;
    navigator.clipboard.writeText(input.value);
    showToast(`${label} copied to clipboard!`, 'success');
  }

  function selectChangeTab(index) {
    if (!pendingChanges || !pendingChanges.changes[index]) return;
    
    // Save current editor content before switching
    const textarea = document.getElementById('ghActiveFileContent');
    if (textarea && pendingChanges.changes[currentActiveIndex]) {
      pendingChanges.changes[currentActiveIndex].content = textarea.value;
    }

    currentActiveIndex = index;
    const c = pendingChanges.changes[index];
    if (textarea) textarea.value = c.content;

    document.querySelectorAll('#ghFileTabs button').forEach((btn, i) => {
      if (i === index) {
        btn.className = 'px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500/20 text-cyan-300 border border-cyan-500/40';
      } else {
        btn.className = 'px-3 py-1 rounded-lg text-xs font-semibold text-slate-400 hover:text-slate-200';
      }
    });
  }

  async function applyCurrentChanges() {
    if (!pendingChanges) return;

    const [owner, repo] = pendingChanges.repo.split('/');
    const btn = document.getElementById('ghApplyBtn');
    btn.disabled = true;
    btn.innerHTML = `<i class="fas fa-circle-notch fa-spin mr-1.5"></i> Committing & Syncing...`;

    const description = document.getElementById('ghEditDescription').value;
    const topicsRaw = document.getElementById('ghEditTopics').value;
    const topics = topicsRaw.split(',').map(t => t.trim()).filter(Boolean);
    const createRelease = document.getElementById('ghCreateReleaseCheckbox').checked;

    try {
      const res = await fetch('/api/apply', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          owner,
          repo,
          changes: pendingChanges.changes,
          topics,
          description,
          create_release: createRelease,
          release_notes: pendingChanges.release_notes,
        }),
      });
      const data = await res.json();

      if (data.success) {
        const isRestricted = data.results?.metadata?.permission_restricted;
        if (isRestricted) {
          showToast(`Repository files committed! Note: To auto-sync Topics, enable 'Administration' on your GitHub token, or paste them into GitHub settings.`, 'warning');
        } else {
          showToast(`Successfully polished ${owner}/${repo}!`, 'success');
        }
        document.getElementById('ghChangesModal').classList.add('hidden');
        loadRepositories();
      } else {
        showToast('Failed to apply changes', 'error');
      }
    } catch (err) {
      showToast(`Apply error: ${err.message}`, 'error');
    } finally {
      btn.disabled = false;
      btn.innerHTML = `<i class="fas fa-check mr-1.5"></i> Apply & Push to GitHub`;
    }
  }

  function escapeQuotes(str) {
    return (str || '').replace(/"/g, '&quot;');
  }

  function escapeHtml(str) {
    return (str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  return {
    init,
    scanRepo,
    selectChangeTab,
    copyField,
  };
})();
