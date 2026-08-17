/**
 * Socials OS Module - Frontend Controller (Facebook, Twitter/X & LinkedIn Management Suite)
 * Handles Facebook Page Publishing, Twitter/X Tweets, LinkedIn Thought Leadership, and Daily Automation.
 */

window.SocialsModule = (function () {
  let currentTab = 'facebook';
  let cachedFbPosts = [];
  let cachedTwPosts = [];
  let cachedLiPosts = [];
  let cachedGeneratedThread = [];
  let weeklyTopics = [];

  const FRESH_TOPICS_POOL = [
    "The Bootstrapped AI Stack: Scaling medical AI to 1,000 users with lightweight frameworks like Replit & Antigravity vs heavy AWS",
    "The 'Agentic AI' Shift: Moving past chatbots to autonomous multi-agent execution in 2026 without human supervision",
    "Zero-Cash Acquisitions: Partnering with existing supply chain operators for instant profitability without cash investment",
    "The 'Invisible AI' Trend: Embedding AI so deeply into business operations that customers never realize they use it",
    "The Meta SME AI Academy in Bangladesh: Scaling agriculture & garment sectors globally with practical AI tools",
    "The Rise of Local AI Engineering: DSi, SELISE, and Devnet shifting from outsourcing to complex GenAI models",
    "The 2026 AI Business Summit: DCCI pushing practical floor AI & digital sovereignty for local SMEs",
    "The Dual-Persona Architecture: Engineering AI that switches between brutal unfiltered truths and soft empathy",
    "The Synthetic Influencer Economy: AI creators landing real-world brand deals on TikTok & Facebook",
    "Human & AI Collaboration: Why the Half-Human + Half-AI model outperforms pure AI in 2026",
    "Unit Economics of Healthcare AI: Maintaining high margins with autonomous clinical diagnostics & workflows",
    "AI in Software Development Cycles: Shifting from syntax writing to managing autonomous agents that design and test"
  ];

  function init() {
    setupSidebarTabs();
    setupFacebookHub();
    setupTwitterHub();
    setupLinkedInHub();
    setupAutomationHub();
    checkAccountsStatus();
  }

  // ---------------------------------------------------------------------------
  // 1. Sidebar Tab Navigation
  // ---------------------------------------------------------------------------
  function setupSidebarTabs() {
    const tabs = document.querySelectorAll('[data-socials-tab]');
    tabs.forEach(tabBtn => {
      tabBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const tabTarget = tabBtn.getAttribute('data-socials-tab');
        switchSocialsTab(tabTarget);
      });
    });
  }

  function switchSocialsTab(tabName) {
    currentTab = tabName;

    // Update active styling
    document.querySelectorAll('[data-socials-tab]').forEach(btn => {
      const target = btn.getAttribute('data-socials-tab');
      if (target === tabName) {
        btn.classList.add('bg-cyan-500/10', 'text-cyan-400', 'border-cyan-500/40');
        btn.classList.remove('text-slate-400', 'border-transparent');
      } else {
        btn.classList.remove('bg-cyan-500/10', 'text-cyan-400', 'border-cyan-500/40');
        btn.classList.add('text-slate-400', 'border-transparent');
      }
    });

    // Toggle Tab Panels
    document.querySelectorAll('.socials-tab-panel').forEach(panel => {
      if (panel.id === `socials-panel-${tabName}`) {
        panel.classList.remove('hidden');
      } else {
        panel.classList.add('hidden');
      }
    });

    // Refresh active panel data
    if (tabName === 'facebook') loadPosts('facebook');
    if (tabName === 'twitter') loadPosts('twitter');
    if (tabName === 'linkedin') loadPosts('linkedin');
    if (tabName === 'automation') loadWeeklyTopics();
  }

  // ---------------------------------------------------------------------------
  // 2. Account Connection Health & Diagnostics
  // ---------------------------------------------------------------------------
  async function checkAccountsStatus() {
    try {
      const res = await fetch('/api/socials/accounts');
      const data = await res.json();

      // Facebook status update
      const fbProfile = data.facebook?.profile || {};
      const fbConnected = fbProfile.connected;
      const fbBadge = document.getElementById('fbLiveStatusBadge');
      const fbName = document.getElementById('fbPageName');
      const fbFollowers = document.getElementById('fbFollowersText');

      if (fbBadge && fbConnected) {
        fbBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
        fbBadge.innerHTML = '<i class="fas fa-check-circle mr-1"></i>Page Connected';
      } else if (fbBadge) {
        fbBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/30';
        fbBadge.innerHTML = '<i class="fas fa-key mr-1"></i>Token Loaded';
      }

      if (fbName && fbProfile.name) fbName.textContent = fbProfile.name;
      if (fbFollowers && fbProfile.followers_count !== undefined) {
        fbFollowers.textContent = `${fbProfile.followers_count} Followers • Category: ${fbProfile.category || 'Tech'}`;
      }

      // Twitter status update
      const twBadge = document.getElementById('twLiveStatusBadge');
      if (twBadge) {
        twBadge.className = 'text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/30';
        twBadge.innerHTML = '<i class="fas fa-check-circle mr-1"></i>API v2 Ready';
      }

    } catch (err) {
      console.warn('Accounts health check notice:', err);
    }
  }

  // ---------------------------------------------------------------------------
  // 3. Facebook Hub Controller
  // ---------------------------------------------------------------------------
  function setupFacebookHub() {
    const generateTodayBtn = document.getElementById('fbGenerateTodayBtn');
    const generateBtn = document.getElementById('fbGenerateBtn');
    const topicInput = document.getElementById('fbTopicInput');
    const contentEditor = document.getElementById('fbContentEditor');
    const publishGeneratedBtn = document.getElementById('fbPublishGeneratedBtn');
    const copyGeneratedBtn = document.getElementById('fbCopyGeneratedBtn');
    const wordCountBadge = document.getElementById('fbWordCountBadge');

    const feedContentEditor = document.getElementById('fbFeedContentEditor');
    const feedPublishBtn = document.getElementById('fbFeedPublishBtn');
    const feedCopyBtn = document.getElementById('fbFeedCopyBtn');
    const feedRefreshBtn = document.getElementById('fbFeedRefreshBtn');
    const feedWordCountBadge = document.getElementById('fbFeedWordCountBadge');
    const feedTopicLabel = document.getElementById('fbFeedTopicLabel');
    const feedStatusBadge = document.getElementById('fbFeedStatusBadge');

    // Quick topic filter pills
    document.querySelectorAll('[data-quick-topic-fb]').forEach(btn => {
      btn.addEventListener('click', () => {
        const topic = btn.getAttribute('data-quick-topic-fb');
        if (topicInput) {
          topicInput.value = topic;
          topicInput.focus();
        }
      });
    });

    // Word counter for AI Facebook Post Creator
    if (contentEditor && wordCountBadge) {
      contentEditor.addEventListener('input', () => {
        const words = contentEditor.value.trim().split(/\s+/).filter(Boolean).length;
        wordCountBadge.textContent = `${words} words`;
      });
    }

    // Word counter for Facebook Post Feed
    if (feedContentEditor && feedWordCountBadge) {
      feedContentEditor.addEventListener('input', () => {
        const words = feedContentEditor.value.trim().split(/\s+/).filter(Boolean).length;
        feedWordCountBadge.textContent = `${words} words`;
      });
    }

    // 1. "Generate Today's Post" button
    if (generateTodayBtn) {
      generateTodayBtn.addEventListener('click', async () => {
        generateTodayBtn.disabled = true;
        const originalHtml = generateTodayBtn.innerHTML;
        generateTodayBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Writing...';

        try {
          const weekday = new Date().toLocaleDateString('en-US', { weekday: 'long' });
          let todayTopic = `Autonomous AI Systems & Growth Strategy (${weekday})`;
          try {
            const topRes = await fetch('/api/socials/daily-topics');
            const topData = await topRes.json();
            const matching = (topData.topics || []).find(t => t.day_name.toLowerCase() === weekday.toLowerCase());
            if (matching && matching.topic) todayTopic = matching.topic;
          } catch (e) {
            console.warn('Could not fetch daily topics schedule:', e);
          }

          if (topicInput) topicInput.value = todayTopic;

          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'facebook', topic: todayTopic }),
          });
          const data = await res.json();

          if (data.success && contentEditor) {
            contentEditor.value = data.content;
            const words = data.content.trim().split(/\s+/).filter(Boolean).length;
            if (wordCountBadge) wordCountBadge.textContent = `${words} words`;
            const card = document.getElementById('fbGeneratedCard');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            window.showToast("Today's Facebook post generated! You can edit it below.", 'success');
          } else {
            window.showToast('Failed to generate today\'s post', 'error');
          }
        } catch (err) {
          window.showToast(`Generation error: ${err.message}`, 'error');
        } finally {
          generateTodayBtn.disabled = false;
          generateTodayBtn.innerHTML = originalHtml;
        }
      });
    }

    // 2. "Generate Facebook Post" from Search Bar
    if (generateBtn) {
      generateBtn.addEventListener('click', async () => {
        const topic = topicInput?.value.trim();
        if (!topic) {
          window.showToast('Please type a topic name into the box or click a filter pill', 'warning');
          if (topicInput) topicInput.focus();
          return;
        }

        generateBtn.disabled = true;
        const originalHtml = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Writing...';

        try {
          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'facebook', topic: topic }),
          });
          const data = await res.json();

          if (data.success && contentEditor) {
            contentEditor.value = data.content;
            const words = data.content.trim().split(/\s+/).filter(Boolean).length;
            if (wordCountBadge) wordCountBadge.textContent = `${words} words`;
            const card = document.getElementById('fbGeneratedCard');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            window.showToast('Facebook post generated! You can edit it freely before publishing.', 'success');
          } else {
            window.showToast('Failed to generate Facebook post', 'error');
          }
        } catch (err) {
          window.showToast(`Generation error: ${err.message}`, 'error');
        } finally {
          generateBtn.disabled = false;
          generateBtn.innerHTML = originalHtml;
        }
      });
    }

    // 3. AI Creator Option 1: "Publish Post"
    if (publishGeneratedBtn) {
      publishGeneratedBtn.addEventListener('click', async () => {
        const content = contentEditor?.value.trim();
        if (!content) {
          window.showToast('Post content is empty! Generate or write a post first.', 'warning');
          return;
        }

        publishGeneratedBtn.disabled = true;
        const originalHtml = publishGeneratedBtn.innerHTML;
        publishGeneratedBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Publishing...';

        try {
          const topic = topicInput?.value.trim() || 'Tech Innovation';
          const res = await fetch('/api/socials/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              platform: 'facebook',
              topic: topic,
              content: content,
              publish_now: true,
            }),
          });
          const data = await res.json();

          if (data.success) {
            window.showToast('Post published directly to Facebook Page!', 'success');
            loadPosts('facebook');
          } else {
            const msg = data.result?.error || data.error || 'Check Meta Page permissions';
            window.showToast(`Facebook response: ${msg}`, 'warning');
            loadPosts('facebook');
          }
        } catch (err) {
          window.showToast(`Publish error: ${err.message}`, 'error');
        } finally {
          publishGeneratedBtn.disabled = false;
          publishGeneratedBtn.innerHTML = originalHtml;
        }
      });
    }

    // 4. AI Creator Option 2: "Copy Post"
    if (copyGeneratedBtn) {
      copyGeneratedBtn.addEventListener('click', () => {
        const content = contentEditor?.value.trim();
        if (!content) {
          window.showToast('Post content is empty! Generate a post first.', 'warning');
          return;
        }
        navigator.clipboard.writeText(content);
        window.showToast('Post copied to clipboard! Ready to paste into Facebook.', 'success');
      });
    }

    // 5. Facebook Post Feed Option 1: "Publish to Page"
    if (feedPublishBtn) {
      feedPublishBtn.addEventListener('click', async () => {
        const content = feedContentEditor?.value.trim();
        if (!content) {
          window.showToast('Feed post content is empty!', 'warning');
          return;
        }

        feedPublishBtn.disabled = true;
        const originalHtml = feedPublishBtn.innerHTML;
        feedPublishBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Publishing...';

        try {
          const topic = feedTopicLabel?.textContent.trim() || 'Facebook Strategy';
          const res = await fetch('/api/socials/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              platform: 'facebook',
              topic: topic,
              content: content,
              publish_now: true,
            }),
          });
          const data = await res.json();

          if (data.success) {
            window.showToast('Feed post published to Facebook Page!', 'success');
            if (feedStatusBadge) {
              feedStatusBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
              feedStatusBadge.textContent = 'PUBLISHED';
            }
          } else {
            const msg = data.result?.error || data.error || 'Check Meta Page permissions';
            window.showToast(`Facebook response: ${msg}`, 'warning');
          }
        } catch (err) {
          window.showToast(`Publish error: ${err.message}`, 'error');
        } finally {
          feedPublishBtn.disabled = false;
          feedPublishBtn.innerHTML = originalHtml;
        }
      });
    }

    // 6. Facebook Post Feed Option 2: "Copy Post"
    if (feedCopyBtn) {
      feedCopyBtn.addEventListener('click', () => {
        const content = feedContentEditor?.value.trim();
        if (!content) {
          window.showToast('Feed post content is empty!', 'warning');
          return;
        }
        navigator.clipboard.writeText(content);
        window.showToast('Feed post copied to clipboard! Ready to paste into Facebook.', 'success');
      });
    }

    // 7. Facebook Post Feed Option 3: "Refresh Feed"
    if (feedRefreshBtn) {
      feedRefreshBtn.addEventListener('click', async () => {
        feedRefreshBtn.disabled = true;
        const originalHtml = feedRefreshBtn.innerHTML;
        feedRefreshBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Refreshing...';

        try {
          const randomTopic = FRESH_TOPICS_POOL[Math.floor(Math.random() * FRESH_TOPICS_POOL.length)];
          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'facebook', topic: randomTopic }),
          });
          const data = await res.json();

          if (data.success && feedContentEditor) {
            feedContentEditor.value = data.content;
            if (feedTopicLabel) feedTopicLabel.textContent = randomTopic;
            if (feedStatusBadge) {
              feedStatusBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
              feedStatusBadge.textContent = 'READY TO PUBLISH';
            }
            const words = data.content.trim().split(/\s+/).filter(Boolean).length;
            if (feedWordCountBadge) feedWordCountBadge.textContent = `${words} words`;
            window.showToast('Feed refreshed with new Facebook post! You can edit it directly.', 'success');
          } else {
            window.showToast('Failed to refresh feed post', 'error');
          }
        } catch (err) {
          window.showToast(`Refresh error: ${err.message}`, 'error');
        } finally {
          feedRefreshBtn.disabled = false;
          feedRefreshBtn.innerHTML = originalHtml;
        }
      });
    }

    loadPosts('facebook');
  }

  // ---------------------------------------------------------------------------
  // 4. Twitter Hub Controller
  // ---------------------------------------------------------------------------
  function setupTwitterHub() {
    const generateTodayBtn = document.getElementById('twGenerateTodayBtn');
    const generateBtn = document.getElementById('twGenerateBtn');
    const topicInput = document.getElementById('twTopicInput');
    const contentEditor = document.getElementById('twContentEditor');
    const publishGeneratedBtn = document.getElementById('twPublishGeneratedBtn');
    const copyGeneratedBtn = document.getElementById('twCopyGeneratedBtn');
    const charBadge = document.getElementById('twCharBadge');
    const threadContainer = document.getElementById('twThreadContainer');
    const threadList = document.getElementById('twThreadList');

    const feedContentEditor = document.getElementById('twFeedContentEditor');
    const feedPublishBtn = document.getElementById('twFeedPublishBtn');
    const feedCopyBtn = document.getElementById('twFeedCopyBtn');
    const feedRefreshBtn = document.getElementById('twFeedRefreshBtn');
    const feedCharBadge = document.getElementById('twFeedCharBadge');
    const feedTopicLabel = document.getElementById('twFeedTopicLabel');
    const feedStatusBadge = document.getElementById('twFeedStatusBadge');

    // Quick topic filter pills
    document.querySelectorAll('[data-quick-topic-tw]').forEach(btn => {
      btn.addEventListener('click', () => {
        const topic = btn.getAttribute('data-quick-topic-tw');
        if (topicInput) {
          topicInput.value = topic;
          topicInput.focus();
        }
      });
    });

    // 280-char counter with visual feedback (AI Creator)
    if (contentEditor && charBadge) {
      contentEditor.addEventListener('input', () => {
        const len = contentEditor.value.length;
        charBadge.textContent = `${len} / 280`;

        if (len > 280) {
          charBadge.className = 'font-bold mono-font px-2 py-0.5 rounded bg-red-950/80 border border-red-500 text-red-300 text-[11px]';
        } else if (len > 250) {
          charBadge.className = 'font-bold mono-font px-2 py-0.5 rounded bg-amber-950/80 border border-amber-500 text-amber-300 text-[11px]';
        } else {
          charBadge.className = 'font-bold mono-font px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400 text-[11px]';
        }
      });
    }

    // 280-char counter for Feed Tweet
    if (feedContentEditor && feedCharBadge) {
      feedContentEditor.addEventListener('input', () => {
        const len = feedContentEditor.value.length;
        feedCharBadge.textContent = `${len} / 280`;

        if (len > 280) {
          feedCharBadge.className = 'font-bold mono-font px-2 py-0.5 rounded bg-red-950/80 border border-red-500 text-red-300 text-[11px]';
        } else if (len > 250) {
          feedCharBadge.className = 'font-bold mono-font px-2 py-0.5 rounded bg-amber-950/80 border border-amber-500 text-amber-300 text-[11px]';
        } else {
          feedCharBadge.className = 'font-bold mono-font px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-cyan-400 text-[11px]';
        }
      });
    }

    // 1. "Generate Today's Tweet" button
    if (generateTodayBtn) {
      generateTodayBtn.addEventListener('click', async () => {
        generateTodayBtn.disabled = true;
        const originalHtml = generateTodayBtn.innerHTML;
        generateTodayBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Writing...';

        try {
          const weekday = new Date().toLocaleDateString('en-US', { weekday: 'long' });
          let todayTopic = `Why Simplicity Scales & Agentic AI in 2026 (${weekday})`;
          try {
            const topRes = await fetch('/api/socials/daily-topics');
            const topData = await topRes.json();
            const matching = (topData.topics || []).find(t => t.day_name.toLowerCase() === weekday.toLowerCase());
            if (matching && matching.topic) todayTopic = matching.topic;
          } catch (e) {
            console.warn('Could not fetch daily topics schedule:', e);
          }

          if (topicInput) topicInput.value = todayTopic;

          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'twitter', topic: todayTopic }),
          });
          const data = await res.json();

          if (data.success && contentEditor) {
            contentEditor.value = data.tweet;
            const len = data.tweet.length;
            if (charBadge) charBadge.textContent = `${len} / 280`;

            if (data.thread && data.thread.length > 0 && threadContainer && threadList) {
              cachedGeneratedThread = data.thread;
              threadContainer.classList.remove('hidden');
              threadList.innerHTML = data.thread.map((t, idx) => `
                <div class="p-2 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-2">
                  <span class="text-xs text-slate-300">${t}</span>
                  <button onclick="navigator.clipboard.writeText('${t.replace(/'/g, "\\'")}'); window.showToast('Part ${idx+1} copied!', 'info');" class="text-cyan-400 hover:text-cyan-300 text-[11px] shrink-0 p-1">
                    <i class="fas fa-copy"></i>
                  </button>
                </div>
              `).join('');
            } else if (threadContainer) {
              cachedGeneratedThread = [];
              threadContainer.classList.add('hidden');
            }

            const card = document.getElementById('twGeneratedCard');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            window.showToast("Today's Tweet generated! You can edit it below.", 'success');
          } else {
            window.showToast('Failed to generate today\'s tweet', 'error');
          }
        } catch (err) {
          window.showToast(`Generation error: ${err.message}`, 'error');
        } finally {
          generateTodayBtn.disabled = false;
          generateTodayBtn.innerHTML = originalHtml;
        }
      });
    }

    // 2. "Generate Tweet" from Search Bar
    if (generateBtn) {
      generateBtn.addEventListener('click', async () => {
        const topic = topicInput?.value.trim();
        if (!topic) {
          window.showToast('Please type a topic or click a filter pill', 'warning');
          if (topicInput) topicInput.focus();
          return;
        }

        generateBtn.disabled = true;
        const originalHtml = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Writing...';

        try {
          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'twitter', topic: topic }),
          });
          const data = await res.json();

          if (data.success && contentEditor) {
            contentEditor.value = data.tweet;
            const len = data.tweet.length;
            if (charBadge) charBadge.textContent = `${len} / 280`;

            if (data.thread && data.thread.length > 0 && threadContainer && threadList) {
              cachedGeneratedThread = data.thread;
              threadContainer.classList.remove('hidden');
              threadList.innerHTML = data.thread.map((t, idx) => `
                <div class="p-2 rounded-lg bg-slate-900/80 border border-slate-800 flex items-start justify-between gap-2">
                  <span class="text-xs text-slate-300">${t}</span>
                  <button onclick="navigator.clipboard.writeText('${t.replace(/'/g, "\\'")}'); window.showToast('Part ${idx+1} copied!', 'info');" class="text-cyan-400 hover:text-cyan-300 text-[11px] shrink-0 p-1">
                    <i class="fas fa-copy"></i>
                  </button>
                </div>
              `).join('');
            } else if (threadContainer) {
              cachedGeneratedThread = [];
              threadContainer.classList.add('hidden');
            }

            const card = document.getElementById('twGeneratedCard');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            window.showToast('Tweet generated under 280 characters!', 'success');
          } else {
            window.showToast('Failed to generate tweet', 'error');
          }
        } catch (err) {
          window.showToast(`Generation error: ${err.message}`, 'error');
        } finally {
          generateBtn.disabled = false;
          generateBtn.innerHTML = originalHtml;
        }
      });
    }

    // 3. AI Creator Option 1: "Publish Tweet"
    if (publishGeneratedBtn) {
      publishGeneratedBtn.addEventListener('click', async () => {
        const content = contentEditor?.value.trim();
        if (!content) {
          window.showToast('Tweet content is empty!', 'warning');
          return;
        }

        publishGeneratedBtn.disabled = true;
        const originalHtml = publishGeneratedBtn.innerHTML;
        publishGeneratedBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Publishing...';

        try {
          const topic = topicInput?.value.trim() || 'Tech Strategy';
          const res = await fetch('/api/socials/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              platform: 'twitter',
              topic: topic,
              content: content,
              thread: cachedGeneratedThread || [],
              publish_now: true,
            }),
          });
          const data = await res.json();

          if (data.success) {
            window.showToast('Tweet published live to Twitter / X!', 'success');
            loadPosts('twitter');
          } else {
            const msg = data.result?.error || data.error || 'Check Twitter API permissions';
            window.showToast(`Twitter response: ${msg}`, 'warning');
            loadPosts('twitter');
          }
        } catch (err) {
          window.showToast(`Publish error: ${err.message}`, 'error');
        } finally {
          publishGeneratedBtn.disabled = false;
          publishGeneratedBtn.innerHTML = originalHtml;
        }
      });
    }

    // 4. AI Creator Option 2: "Copy Tweet"
    if (copyGeneratedBtn) {
      copyGeneratedBtn.addEventListener('click', () => {
        const content = contentEditor?.value.trim();
        if (!content) {
          window.showToast('Tweet content is empty!', 'warning');
          return;
        }
        if (cachedGeneratedThread && cachedGeneratedThread.length > 0) {
          navigator.clipboard.writeText(cachedGeneratedThread.join('\n\n'));
          window.showToast('Full thread copied to clipboard! Ready to paste on X.', 'success');
        } else {
          navigator.clipboard.writeText(content);
          window.showToast('Tweet copied to clipboard! Ready to paste on X.', 'success');
        }
      });
    }

    // 5. Twitter Post Feed Option 1: "Publish to Twitter"
    if (feedPublishBtn) {
      feedPublishBtn.addEventListener('click', async () => {
        const content = feedContentEditor?.value.trim();
        if (!content) {
          window.showToast('Feed tweet content is empty!', 'warning');
          return;
        }

        feedPublishBtn.disabled = true;
        const originalHtml = feedPublishBtn.innerHTML;
        feedPublishBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Publishing...';

        try {
          const topic = feedTopicLabel?.textContent.trim() || 'Twitter Strategy';
          const res = await fetch('/api/socials/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              platform: 'twitter',
              topic: topic,
              content: content,
              publish_now: true,
            }),
          });
          const data = await res.json();

          if (data.success) {
            window.showToast('Feed tweet published to Twitter / X!', 'success');
            if (feedStatusBadge) {
              feedStatusBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
              feedStatusBadge.textContent = 'POSTED LIVE';
            }
          } else {
            const msg = data.result?.error || data.error || 'Check Twitter API permissions';
            window.showToast(`Twitter response: ${msg}`, 'warning');
          }
        } catch (err) {
          window.showToast(`Publish error: ${err.message}`, 'error');
        } finally {
          feedPublishBtn.disabled = false;
          feedPublishBtn.innerHTML = originalHtml;
        }
      });
    }

    // 6. Twitter Post Feed Option 2: "Copy Tweet"
    if (feedCopyBtn) {
      feedCopyBtn.addEventListener('click', () => {
        const content = feedContentEditor?.value.trim();
        if (!content) {
          window.showToast('Feed tweet content is empty!', 'warning');
          return;
        }
        navigator.clipboard.writeText(content);
        window.showToast('Tweet copied to clipboard! Ready to paste on X.', 'success');
      });
    }

    // 7. Twitter Post Feed Option 3: "Refresh Feed"
    if (feedRefreshBtn) {
      feedRefreshBtn.addEventListener('click', async () => {
        feedRefreshBtn.disabled = true;
        const originalHtml = feedRefreshBtn.innerHTML;
        feedRefreshBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Refreshing...';

        try {
          const randomTopic = FRESH_TOPICS_POOL[Math.floor(Math.random() * FRESH_TOPICS_POOL.length)];
          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'twitter', topic: randomTopic }),
          });
          const data = await res.json();

          if (data.success && feedContentEditor) {
            feedContentEditor.value = data.tweet;
            if (feedTopicLabel) feedTopicLabel.textContent = randomTopic;
            if (feedStatusBadge) {
              feedStatusBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
              feedStatusBadge.textContent = 'READY TO POST';
            }
            const len = data.tweet.length;
            if (feedCharBadge) feedCharBadge.textContent = `${len} / 280`;
            window.showToast('Feed refreshed with new tweet! You can edit it directly.', 'success');
          } else {
            window.showToast('Failed to refresh tweet', 'error');
          }
        } catch (err) {
          window.showToast(`Refresh error: ${err.message}`, 'error');
        } finally {
          feedRefreshBtn.disabled = false;
          feedRefreshBtn.innerHTML = originalHtml;
        }
      });
    }

    loadPosts('twitter');
  }

  // ---------------------------------------------------------------------------
  // 5. LinkedIn Hub Controller
  // ---------------------------------------------------------------------------
  function setupLinkedInHub() {
    const generateTodayBtn = document.getElementById('liGenerateTodayBtn');
    const generateBtn = document.getElementById('liGenerateBtn');
    const topicInput = document.getElementById('liTopicInput');
    const contentEditor = document.getElementById('liContentEditor');
    const publishGeneratedBtn = document.getElementById('liPublishGeneratedBtn');
    const copyGeneratedBtn = document.getElementById('liCopyGeneratedBtn');
    const wordCountBadge = document.getElementById('liWordCountBadge');

    const feedContentEditor = document.getElementById('liFeedContentEditor');
    const feedPublishBtn = document.getElementById('liFeedPublishBtn');
    const feedCopyBtn = document.getElementById('liFeedCopyBtn');
    const feedRefreshBtn = document.getElementById('liFeedRefreshBtn');
    const feedWordCountBadge = document.getElementById('liFeedWordCountBadge');
    const feedTopicLabel = document.getElementById('liFeedTopicLabel');
    const feedStatusBadge = document.getElementById('liFeedStatusBadge');

    // Quick topic filter pills
    document.querySelectorAll('[data-quick-topic-li]').forEach(btn => {
      btn.addEventListener('click', () => {
        const topic = btn.getAttribute('data-quick-topic-li');
        if (topicInput) {
          topicInput.value = topic;
          topicInput.focus();
        }
      });
    });

    // Word counter for AI LinkedIn Post Creator
    if (contentEditor && wordCountBadge) {
      contentEditor.addEventListener('input', () => {
        const words = contentEditor.value.trim().split(/\s+/).filter(Boolean).length;
        wordCountBadge.textContent = `${words} words`;
      });
    }

    // Word counter for LinkedIn Post Feed
    if (feedContentEditor && feedWordCountBadge) {
      feedContentEditor.addEventListener('input', () => {
        const words = feedContentEditor.value.trim().split(/\s+/).filter(Boolean).length;
        feedWordCountBadge.textContent = `${words} words`;
      });
    }

    // 1. "Generate Today's Post" button
    if (generateTodayBtn) {
      generateTodayBtn.addEventListener('click', async () => {
        generateTodayBtn.disabled = true;
        const originalHtml = generateTodayBtn.innerHTML;
        generateTodayBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Writing...';

        try {
          const weekday = new Date().toLocaleDateString('en-US', { weekday: 'long' });
          let todayTopic = `Bootstrapped Founder Playbook & AI Stack (${weekday})`;
          try {
            const topRes = await fetch('/api/socials/daily-topics');
            const topData = await topRes.json();
            const matching = (topData.topics || []).find(t => t.day_name.toLowerCase() === weekday.toLowerCase());
            if (matching && matching.topic) todayTopic = matching.topic;
          } catch (e) {
            console.warn('Could not fetch daily topics schedule:', e);
          }

          if (topicInput) topicInput.value = todayTopic;

          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'linkedin', topic: todayTopic }),
          });
          const data = await res.json();

          if (data.success && contentEditor) {
            contentEditor.value = data.content;
            const words = data.content.trim().split(/\s+/).filter(Boolean).length;
            if (wordCountBadge) wordCountBadge.textContent = `${words} words`;
            const card = document.getElementById('liGeneratedCard');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            window.showToast("Today's LinkedIn post generated! You can edit it below.", 'success');
          } else {
            window.showToast('Failed to generate LinkedIn post', 'error');
          }
        } catch (err) {
          window.showToast(`Generation error: ${err.message}`, 'error');
        } finally {
          generateTodayBtn.disabled = false;
          generateTodayBtn.innerHTML = originalHtml;
        }
      });
    }

    // 2. "Generate LinkedIn Post" from Search Bar
    if (generateBtn) {
      generateBtn.addEventListener('click', async () => {
        const topic = topicInput?.value.trim();
        if (!topic) {
          window.showToast('Please type a topic name into the box or click a filter pill', 'warning');
          if (topicInput) topicInput.focus();
          return;
        }

        generateBtn.disabled = true;
        const originalHtml = generateBtn.innerHTML;
        generateBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Writing...';

        try {
          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'linkedin', topic: topic }),
          });
          const data = await res.json();

          if (data.success && contentEditor) {
            contentEditor.value = data.content;
            const words = data.content.trim().split(/\s+/).filter(Boolean).length;
            if (wordCountBadge) wordCountBadge.textContent = `${words} words`;
            const card = document.getElementById('liGeneratedCard');
            if (card) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
            window.showToast('LinkedIn post generated with "...see more" & Dwell Time optimization!', 'success');
          } else {
            window.showToast('Failed to generate LinkedIn post', 'error');
          }
        } catch (err) {
          window.showToast(`Generation error: ${err.message}`, 'error');
        } finally {
          generateBtn.disabled = false;
          generateBtn.innerHTML = originalHtml;
        }
      });
    }

    // 3. AI Creator Option 1: "Publish Post"
    if (publishGeneratedBtn) {
      publishGeneratedBtn.addEventListener('click', async () => {
        const content = contentEditor?.value.trim();
        if (!content) {
          window.showToast('Post content is empty! Generate or write a post first.', 'warning');
          return;
        }

        publishGeneratedBtn.disabled = true;
        const originalHtml = publishGeneratedBtn.innerHTML;
        publishGeneratedBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Publishing...';

        try {
          const topic = topicInput?.value.trim() || 'LinkedIn Strategy';
          const res = await fetch('/api/socials/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              platform: 'linkedin',
              topic: topic,
              content: content,
              publish_now: true,
            }),
          });
          const data = await res.json();

          if (data.success) {
            navigator.clipboard.writeText(content);
            window.showToast('LinkedIn post saved & copied to clipboard! Ready to paste into LinkedIn.', 'success');
            loadPosts('linkedin');
          } else {
            window.showToast(`Response: ${data.detail || 'Could not save post'}`, 'warning');
            loadPosts('linkedin');
          }
        } catch (err) {
          window.showToast(`Publish error: ${err.message}`, 'error');
        } finally {
          publishGeneratedBtn.disabled = false;
          publishGeneratedBtn.innerHTML = originalHtml;
        }
      });
    }

    // 4. AI Creator Option 2: "Copy Post"
    if (copyGeneratedBtn) {
      copyGeneratedBtn.addEventListener('click', () => {
        const content = contentEditor?.value.trim();
        if (!content) {
          window.showToast('Post content is empty! Generate a post first.', 'warning');
          return;
        }
        navigator.clipboard.writeText(content);
        window.showToast('LinkedIn post copied to clipboard! Ready to paste into LinkedIn.', 'success');
      });
    }

    // 5. LinkedIn Post Feed Option 1: "Publish to LinkedIn"
    if (feedPublishBtn) {
      feedPublishBtn.addEventListener('click', async () => {
        const content = feedContentEditor?.value.trim();
        if (!content) {
          window.showToast('Feed post content is empty!', 'warning');
          return;
        }

        feedPublishBtn.disabled = true;
        const originalHtml = feedPublishBtn.innerHTML;
        feedPublishBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Publishing...';

        try {
          const topic = feedTopicLabel?.textContent.trim() || 'LinkedIn Strategy';
          const res = await fetch('/api/socials/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              platform: 'linkedin',
              topic: topic,
              content: content,
              publish_now: true,
            }),
          });
          const data = await res.json();

          if (data.success) {
            navigator.clipboard.writeText(content);
            window.showToast('Feed post saved & copied to clipboard! Ready to paste into LinkedIn.', 'success');
            if (feedStatusBadge) {
              feedStatusBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
              feedStatusBadge.textContent = 'READY / COPIED';
            }
          } else {
            window.showToast(`Response: ${data.detail || 'Could not save post'}`, 'warning');
          }
        } catch (err) {
          window.showToast(`Publish error: ${err.message}`, 'error');
        } finally {
          feedPublishBtn.disabled = false;
          feedPublishBtn.innerHTML = originalHtml;
        }
      });
    }

    // 6. LinkedIn Post Feed Option 2: "Copy Post"
    if (feedCopyBtn) {
      feedCopyBtn.addEventListener('click', () => {
        const content = feedContentEditor?.value.trim();
        if (!content) {
          window.showToast('Feed post content is empty!', 'warning');
          return;
        }
        navigator.clipboard.writeText(content);
        window.showToast('LinkedIn post copied to clipboard! Ready to paste into LinkedIn.', 'success');
      });
    }

    // 7. LinkedIn Post Feed Option 3: "Refresh Feed"
    if (feedRefreshBtn) {
      feedRefreshBtn.addEventListener('click', async () => {
        feedRefreshBtn.disabled = true;
        const originalHtml = feedRefreshBtn.innerHTML;
        feedRefreshBtn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Refreshing...';

        try {
          const randomTopic = FRESH_TOPICS_POOL[Math.floor(Math.random() * FRESH_TOPICS_POOL.length)];
          const res = await fetch('/api/socials/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ platform: 'linkedin', topic: randomTopic }),
          });
          const data = await res.json();

          if (data.success && feedContentEditor) {
            feedContentEditor.value = data.content;
            if (feedTopicLabel) feedTopicLabel.textContent = randomTopic;
            if (feedStatusBadge) {
              feedStatusBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
              feedStatusBadge.textContent = 'READY TO PUBLISH';
            }
            const words = data.content.trim().split(/\s+/).filter(Boolean).length;
            if (feedWordCountBadge) feedWordCountBadge.textContent = `${words} words`;
            window.showToast('Feed refreshed with new LinkedIn post! You can edit it directly.', 'success');
          } else {
            window.showToast('Failed to refresh LinkedIn post', 'error');
          }
        } catch (err) {
          window.showToast(`Refresh error: ${err.message}`, 'error');
        } finally {
          feedRefreshBtn.disabled = false;
          feedRefreshBtn.innerHTML = originalHtml;
        }
      });
    }

    loadPosts('linkedin');
  }

  // ---------------------------------------------------------------------------
  // 6. Posts Feed & Queue Loader (Facebook, Twitter, LinkedIn)
  // ---------------------------------------------------------------------------
  async function loadPosts(platform) {
    if (platform === 'facebook') {
      const feedEditor = document.getElementById('fbFeedContentEditor');
      const feedTopic = document.getElementById('fbFeedTopicLabel');
      const feedBadge = document.getElementById('fbFeedStatusBadge');
      const feedWordBadge = document.getElementById('fbFeedWordCountBadge');

      try {
        const res = await fetch('/api/socials/posts?platform=facebook');
        const data = await res.json();
        const posts = data.posts || [];
        cachedFbPosts = posts;

        if (posts.length > 0 && feedEditor) {
          const latest = posts[0];
          if (!feedEditor.value || feedEditor.value.trim() === '') {
            feedEditor.value = latest.content;
            if (feedTopic) feedTopic.textContent = latest.topic || latest.title || 'Facebook Post';
            if (feedBadge) {
              if (latest.status === 'published') {
                feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
                feedBadge.textContent = 'PUBLISHED';
              } else {
                feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
                feedBadge.textContent = 'READY TO PUBLISH';
              }
            }
            const words = latest.content.trim().split(/\s+/).filter(Boolean).length;
            if (feedWordBadge) feedWordBadge.textContent = `${words} words`;
          }
        } else if (feedEditor && (!feedEditor.value || feedEditor.value.trim() === '')) {
          const starterTopic = FRESH_TOPICS_POOL[0];
          feedEditor.value = `Most founders think scaling an AI app requires heavy, expensive cloud infrastructure.\n\nIn 2026, the game completely changed.\n\nHere is how bootstrapped teams are serving 1,000+ active doctors with virtually zero server overhead:\n\n• Micro-Agent Workflows: Offloading heavy reasoning to lightweight, autonomous edge agents.\n• Smart Local Caching: Eliminating 80% of repetitive LLM inference costs.\n• Streamlined UI: No clunky dashboards, just direct actionable answers in seconds.\n\nSimplicity always scales better than over-engineering.\n\nWhat is your biggest bottleneck when scaling AI workflows today? Let's discuss in the comments.`;
          if (feedTopic) feedTopic.textContent = starterTopic;
          if (feedBadge) {
            feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
            feedBadge.textContent = 'READY TO PUBLISH';
          }
          const words = feedEditor.value.trim().split(/\s+/).filter(Boolean).length;
          if (feedWordBadge) feedWordBadge.textContent = `${words} words`;
        }
      } catch (err) {
        console.warn('Could not load Facebook posts feed:', err);
      }
      return;
    }

    if (platform === 'twitter') {
      const feedEditor = document.getElementById('twFeedContentEditor');
      const feedTopic = document.getElementById('twFeedTopicLabel');
      const feedBadge = document.getElementById('twFeedStatusBadge');
      const feedCharBadge = document.getElementById('twFeedCharBadge');

      try {
        const res = await fetch('/api/socials/posts?platform=twitter');
        const data = await res.json();
        const posts = data.posts || [];
        cachedTwPosts = posts;

        if (posts.length > 0 && feedEditor) {
          const latest = posts[0];
          if (!feedEditor.value || feedEditor.value.trim() === '') {
            feedEditor.value = latest.content;
            if (feedTopic) feedTopic.textContent = latest.topic || latest.title || 'Twitter Post';
            if (feedBadge) {
              if (latest.status === 'published') {
                feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
                feedBadge.textContent = 'POSTED LIVE';
              } else {
                feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
                feedBadge.textContent = 'READY TO POST';
              }
            }
            const len = latest.content.length;
            if (feedCharBadge) feedCharBadge.textContent = `${len} / 280`;
          }
        } else if (feedEditor && (!feedEditor.value || feedEditor.value.trim() === '')) {
          const starterTopic = FRESH_TOPICS_POOL[0];
          feedEditor.value = `Why 2026 is moving past basic chatbots into autonomous multi-agent execution:\n\n• Chatbots wait for prompts\n• Agents proactively finish tasks\n• Multi-agent workflows eliminate human bottlenecks\n\nScale leverage, not team size. 🚀`;
          if (feedTopic) feedTopic.textContent = starterTopic;
          if (feedBadge) {
            feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
            feedBadge.textContent = 'READY TO POST';
          }
          const len = feedEditor.value.length;
          if (feedCharBadge) feedCharBadge.textContent = `${len} / 280`;
        }
      } catch (err) {
        console.warn('Could not load Twitter posts feed:', err);
      }
      return;
    }

    if (platform === 'linkedin') {
      const feedEditor = document.getElementById('liFeedContentEditor');
      const feedTopic = document.getElementById('liFeedTopicLabel');
      const feedBadge = document.getElementById('liFeedStatusBadge');
      const feedWordBadge = document.getElementById('liFeedWordCountBadge');

      try {
        const res = await fetch('/api/socials/posts?platform=linkedin');
        const data = await res.json();
        const posts = data.posts || [];
        cachedLiPosts = posts;

        if (posts.length > 0 && feedEditor) {
          const latest = posts[0];
          if (!feedEditor.value || feedEditor.value.trim() === '') {
            feedEditor.value = latest.content;
            if (feedTopic) feedTopic.textContent = latest.topic || latest.title || 'LinkedIn Post';
            if (feedBadge) {
              if (latest.status === 'published') {
                feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-emerald-500/20 text-emerald-300 border-emerald-500/30';
                feedBadge.textContent = 'PUBLISHED';
              } else {
                feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
                feedBadge.textContent = 'READY TO PUBLISH';
              }
            }
            const words = latest.content.trim().split(/\s+/).filter(Boolean).length;
            if (feedWordBadge) feedWordBadge.textContent = `${words} words`;
          }
        } else if (feedEditor && (!feedEditor.value || feedEditor.value.trim() === '')) {
          const starterTopic = FRESH_TOPICS_POOL[0];
          feedEditor.value = `Most founders believe that building a successful AI medical startup requires a $2M seed round and heavy AWS clusters.\n\nHere is how we proved them wrong.\n\n...\n\nBy leveraging lightweight orchestration and autonomous edge caching, we scaled to 1,000 active doctor accounts with under $100/mo in infrastructure.\n\n3 key rules that made this possible:\n1. Solve a repetitive daily workflow, not open-ended curiosity.\n2. Keep deterministic validations in code, and only use LLMs for semantic reasoning.\n3. Make your UI invisible—zero learning curve for busy clinicians.\n\nAre you building heavy or lightweight in 2026? Drop your thoughts below.`;
          if (feedTopic) feedTopic.textContent = starterTopic;
          if (feedBadge) {
            feedBadge.className = 'text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded-full border bg-cyan-500/20 text-cyan-300 border-cyan-500/30';
            feedBadge.textContent = 'READY TO PUBLISH';
          }
          const words = feedEditor.value.trim().split(/\s+/).filter(Boolean).length;
          if (feedWordBadge) feedWordBadge.textContent = `${words} words`;
        }
      } catch (err) {
        console.warn('Could not load LinkedIn posts feed:', err);
      }
      return;
    }
  }

  // ---------------------------------------------------------------------------
  // 7. Automation & Daily Scheduler Hub
  // ---------------------------------------------------------------------------
  function setupAutomationHub() {
    const triggerBtn = document.getElementById('triggerTodayBtn');
    if (triggerBtn) {
      triggerBtn.addEventListener('click', () => triggerDailyQuick());
    }
  }

  async function triggerDailyQuick() {
    try {
      window.showToast("Generating today's Facebook, Twitter & LinkedIn posts...", 'info');
      const res = await fetch('/api/socials/trigger-daily-cron', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_publish: false }),
      });
      const data = await res.json();

      if (data.success) {
        window.showToast(`Generated today's package on: "${data.topic}"`, 'success');
        loadPosts('facebook');
        loadPosts('twitter');
        loadPosts('linkedin');
      }
    } catch (err) {
      window.showToast(`Error: ${err.message}`, 'error');
    }
  }

  async function loadWeeklyTopics() {
    const container = document.getElementById('weeklyTopicsContainer');
    if (!container) return;

    try {
      const res = await fetch('/api/socials/daily-topics');
      const data = await res.json();
      weeklyTopics = data.topics || [];

      const currentDay = new Date().toLocaleDateString('en-US', { weekday: 'long' });

      container.innerHTML = weeklyTopics.map(t => {
        const isToday = t.day_name.toLowerCase() === currentDay.toLowerCase();
        return `
          <div class="p-3.5 rounded-xl border ${isToday ? 'bg-purple-950/40 border-purple-500/50 shadow-lg shadow-purple-500/10' : 'bg-slate-950/60 border-slate-800'} space-y-1.5">
            <div class="flex items-center justify-between">
              <span class="text-xs font-bold ${isToday ? 'text-purple-300' : 'text-slate-300'} flex items-center gap-1.5">
                ${t.day_name} ${isToday ? '<span class="text-[9px] px-1.5 py-0.2 rounded bg-purple-500/30 text-purple-200 border border-purple-500/40 font-bold uppercase">Today</span>' : ''}
              </span>
              <span class="text-[10px] text-slate-500">Autonomous Active</span>
            </div>
            <p class="text-xs text-slate-300 font-medium">${t.topic}</p>
          </div>
        `;
      }).join('');

    } catch (err) {
      container.innerHTML = `<div class="text-xs text-red-400">Error loading weekly schedule: ${err.message}</div>`;
    }
  }

  return {
    init,
    switchSocialsTab,
    checkAccountsStatus,
    loadPosts,
    triggerDailyQuick,
  };
})();
