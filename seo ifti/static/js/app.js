/**
 * Main Application Orchestrator & View Switcher
 * Manages Top Nav Bar (GitHub, Socials) and Global Toast/Modal UI.
 */

const AppState = {
  currentView: 'socials',
};

document.addEventListener('DOMContentLoaded', () => {
  initTopNav();
  initGlobalModals();

  // Check URL hash or default to 'socials'
  const hash = window.location.hash.replace('#', '');
  if (['github', 'socials'].includes(hash)) {
    switchView(hash);
  } else {
    switchView('socials');
  }
});

function initTopNav() {
  const navBtns = document.querySelectorAll('[data-view-target]');
  navBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
      const targetView = btn.getAttribute('data-view-target');
      switchView(targetView);
    });
  });
}

function switchView(viewName) {
  AppState.currentView = viewName;
  window.location.hash = viewName;

  // Update Nav Button active styling
  document.querySelectorAll('[data-view-target]').forEach(btn => {
    const target = btn.getAttribute('data-view-target');
    if (target === viewName) {
      btn.classList.add('bg-slate-800', 'text-cyan-400', 'border-cyan-500/30');
      btn.classList.remove('text-slate-400', 'border-transparent');
    } else {
      btn.classList.remove('bg-slate-800', 'text-cyan-400', 'border-cyan-500/30');
      btn.classList.add('text-slate-400', 'border-transparent');
    }
  });

  // Toggle View Containers
  document.querySelectorAll('.app-view-container').forEach(viewEl => {
    if (viewEl.id === `view-${viewName}`) {
      viewEl.classList.remove('hidden');
    } else {
      viewEl.classList.add('hidden');
    }
  });

  // Trigger view-specific loaders
  if (viewName === 'socials' && window.SocialsModule) {
    window.SocialsModule.init();
  } else if (viewName === 'github' && window.GitHubModule) {
    window.GitHubModule.init();
  }
}

// Global Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  const colors = {
    success: 'border-emerald-500/40 bg-emerald-950/80 text-emerald-200',
    error: 'border-red-500/40 bg-red-950/80 text-red-200',
    info: 'border-cyan-500/40 bg-cyan-950/80 text-cyan-200',
    warning: 'border-amber-500/40 bg-amber-950/80 text-amber-200'
  };

  const icons = {
    success: 'fa-check-circle text-emerald-400',
    error: 'fa-exclamation-circle text-red-400',
    info: 'fa-info-circle text-cyan-400',
    warning: 'fa-triangle-exclamation text-amber-400'
  };

  toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-lg shadow-xl text-sm transition-all duration-300 transform translate-y-2 opacity-0 ${colors[type] || colors.info}`;
  toast.innerHTML = `
    <i class="fas ${icons[type] || icons.info}"></i>
    <span class="font-medium">${message}</span>
  `;

  container.appendChild(toast);

  // Animate in
  requestAnimationFrame(() => {
    toast.classList.remove('translate-y-2', 'opacity-0');
  });

  setTimeout(() => {
    toast.classList.add('translate-y-2', 'opacity-0');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function initGlobalModals() {
  document.querySelectorAll('[data-close-modal]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.add('hidden'));
    });
  });

  // Close on ESC
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      document.querySelectorAll('.modal-overlay').forEach(m => m.classList.add('hidden'));
    }
  });
}

window.showToast = showToast;
