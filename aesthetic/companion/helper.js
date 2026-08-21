(function() {
  const MIN_RECONNECT_MS = 500;
  const MAX_RECONNECT_MS = 30000;
  const TOMBSTONE_AFTER_MS = 15000; // show the "paused" overlay after this long disconnected

  // Pure: next backoff delay (doubles, capped). Exported for unit tests.
  function nextReconnectDelay(current, max) {
    return Math.min(current * 2, max);
  }

  // Zero is a separate worst-score control, not the first lit star.
  function rankIsOn(rank, stars) {
    return rank === 0 ? stars === 0 : rank > 0 && rank <= stars;
  }
  function starsForEvent(raw, scored) {
    const stars = parseInt(raw, 10);
    return scored === 'yes' && Number.isInteger(stars) && stars >= 0 && stars <= 5
      ? stars : null;
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      nextReconnectDelay, rankIsOn, starsForEvent,
      MIN_RECONNECT_MS, MAX_RECONNECT_MS, TOMBSTONE_AFTER_MS
    };
  }

  // Everything below is browser-only; bail out when loaded in Node (tests).
  if (typeof window === 'undefined') return;

  let ws = null;
  let eventQueue = [];
  let reconnectDelay = MIN_RECONNECT_MS;
  let reconnectTimer = null;
  let disconnectedSince = null;
  let everConnected = false;
  let tombstoneShown = false;

  function sessionKey() {
    try {
      return window.sessionStorage && window.sessionStorage.getItem('brainstorm-session-key');
    } catch (e) {}
    return null;
  }

  function websocketUrl() {
    const key = sessionKey();
    return 'ws://' + window.location.host + (key ? '/?key=' + encodeURIComponent(key) : '');
  }

  function reloadAfterRecovery() {
    const key = sessionKey();
    if (key) {
      window.location.replace('/?key=' + encodeURIComponent(key));
    } else {
      window.location.reload();
    }
  }

  // Reflect connection state in the frame's status pill (absent on full-doc screens).
  function setStatus(state) {
    const el = document.querySelector('.status');
    if (!el) return;
    const map = {
      connecting:   ['Connecting…',   'var(--text-tertiary)'],
      connected:    ['Connected',     'var(--success)'],
      reconnecting: ['Reconnecting…', 'var(--warning)'],
      disconnected: ['Disconnected',  'var(--error)']
    };
    const [text, color] = map[state] || map.disconnected;
    el.textContent = text;
    el.style.setProperty('--status-color', color);
  }

  // Self-styled so it works on framed and full-document screens alike.
  function showTombstone() {
    if (tombstoneShown) return;
    tombstoneShown = true;
    const el = document.createElement('div');
    el.id = 'bs-tombstone';
    el.style.cssText = 'position:fixed;inset:0;z-index:99999;display:flex;' +
      'align-items:center;justify-content:center;padding:2rem;text-align:center;' +
      'background:rgba(20,20,22,0.92);color:#f5f5f7;font-family:system-ui,sans-serif';
    el.innerHTML = '<div style="max-width:480px">' +
      '<h2 style="margin:0 0 .5rem;font-weight:600">Companion paused</h2>' +
      '<p style="margin:0;opacity:.85">This brainstorm companion has stopped. ' +
      'Ask your coding agent to bring it back — this page reconnects automatically.</p></div>';
    if (document.body) document.body.appendChild(el);
  }

  function connect() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    setStatus(everConnected ? 'reconnecting' : 'connecting');
    ws = new WebSocket(websocketUrl());

    ws.onopen = () => {
      const recovered = tombstoneShown;
      everConnected = true;
      disconnectedSince = null;
      reconnectDelay = MIN_RECONNECT_MS;
      tombstoneShown = false;
      setStatus('connected');
      eventQueue.forEach(e => ws.send(JSON.stringify(e)));
      eventQueue = [];
      // Recovered from a tombstoned outage (e.g. the server restarted on the same
      // port) — reload through the keyed bootstrap when possible so the cookie is
      // refreshed before the visible URL returns to bare /.
      if (recovered) reloadAfterRecovery();
    };

    ws.onmessage = (msg) => {
      let data;
      try { data = JSON.parse(msg.data); } catch (e) { return; }
      if (data.type === 'reload') window.location.reload();
      if (data.type === 'dh-agent') {
        window.__dhLastAgent = data;
        window.dispatchEvent(new CustomEvent('dh-agent', { detail: data }));
      }
    };

    ws.onclose = () => {
      ws = null;
      if (disconnectedSince === null) disconnectedSince = Date.now();
      if (Date.now() - disconnectedSince >= TOMBSTONE_AFTER_MS) {
        setStatus('disconnected');
        showTombstone();
      } else {
        setStatus('reconnecting');
      }
      reconnectTimer = setTimeout(connect, reconnectDelay);
      reconnectDelay = nextReconnectDelay(reconnectDelay, MAX_RECONNECT_MS);
    };

    // Let onclose own reconnection so we don't schedule it twice.
    ws.onerror = () => { try { ws.close(); } catch (e) {} };
  }

  function sendEvent(event) {
    event.timestamp = Date.now();
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(event));
    } else {
      eventQueue.push(event);
    }
  }

  function rgbToHex(value) {
    const channels = String(value).match(/[\d.]+/g);
    if (!channels || channels.length < 3) return null;
    return '#' + channels.slice(0, 3).map(n =>
      Math.max(0, Math.min(255, Math.round(Number(n)))).toString(16).padStart(2, '0')
    ).join('');
  }

  function articleTheme() {
    const art = document.querySelector('.dh-art');
    if (!art) return null;
    const style = getComputedStyle(art);
    const accent = style.getPropertyValue('--dh-accent').trim();
    return {
      bg: rgbToHex(style.backgroundColor),
      ink: rgbToHex(style.color),
      accent: /^#[0-9a-f]{6}$/i.test(accent) ? accent : '#d9482a',
      font: style.fontFamily
    };
  }

  function applyFrameTheme(elements) {
    if (!elements) return;
    const root = document.documentElement.style;
    root.setProperty('--bg-primary', elements.bg);
    root.setProperty('--bg-secondary', elements.bg);
    root.setProperty('--text-primary', elements.ink);
    root.setProperty('--text-secondary', elements.ink);
    root.setProperty('--accent', elements.accent);
    root.setProperty('--selected-border', elements.accent);
    document.body.style.fontFamily = elements.font;
  }

  function selectedTheme(spec) {
    return (spec.themes || []).find(theme => theme.id === spec.selected) || null;
  }

  async function themeRequest(payload) {
    const response = await fetch('/theme', {
      method: payload ? 'POST' : 'GET',
      headers: payload ? { 'Content-Type': 'application/json' } : {},
      body: payload ? JSON.stringify(payload) : undefined
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'Theme request failed');
    return data;
  }

  function wireThemeSettings() {
    const settings = document.querySelector('[data-theme-settings]');
    if (!settings) return;
    const follow = settings.querySelector('[data-follow-art-direction]');
    const message = settings.querySelector('[data-theme-message]');
    let spec = null;
    const say = text => { message.textContent = text; };
    themeRequest().then(value => {
      spec = value;
      follow.checked = Boolean(spec.followArtDirection);
      const selected = selectedTheme(spec);
      if (follow.checked && selected) applyFrameTheme(selected.elements);
    }).catch(error => say(error.message));
    follow.addEventListener('change', async () => {
      try {
        spec = await themeRequest({ action: 'follow', enabled: follow.checked });
        if (follow.checked) {
          const candidate = articleTheme();
          const selected = selectedTheme(spec);
          applyFrameTheme(candidate || (selected && selected.elements));
        } else {
          window.location.reload();
        }
        say(follow.checked ? 'Companion follows the art direction' : 'Companion uses its safe theme');
      } catch (error) { follow.checked = !follow.checked; say(error.message); }
    });
    settings.querySelectorAll('[data-theme-save]').forEach(button => {
      button.addEventListener('click', async () => {
        const mode = button.dataset.themeSave;
        const candidate = articleTheme();
        if (!candidate) { say('No article theme is available'); return; }
        let id = spec && spec.selected || 'art-direction';
        let name = id;
        if (mode === 'new') {
          name = window.prompt('Theme name', 'Art direction') || '';
          if (!name.trim()) return;
          id = name.toLowerCase().replace(/[^a-z0-9._-]+/g, '-').replace(/^-|-$/g, '');
        }
        try {
          spec = await themeRequest({ action: 'save', mode, id, name, elements: candidate });
          const selected = selectedTheme(spec);
          if (follow.checked && selected) applyFrameTheme(selected.elements);
          const issues = selected && selected.issues || [];
          say(issues.length
            ? 'Saved with safe fallback for: ' + issues.map(issue => issue.element).join(', ')
            : 'Theme saved to the project');
        } catch (error) { say(error.message); }
      });
    });
  }

  // Capture clicks on choice elements
  document.addEventListener('click', (e) => {
    const target = e.target.closest('[data-choice]');
    if (!target) return;

    sendEvent({
      type: 'click',
      text: target.textContent.trim(),
      choice: target.dataset.choice,
      element: target.dataset.element || null,
      stars: starsOf(target),
      id: target.id || null
    });

  });

  // Star rank: 1-5, set by the user, never inferred by the agent.
  function starsOf(el) {
    const holder = el.closest('[data-stars]');
    return holder ? starsForEvent(holder.dataset.stars, holder.dataset.scored) : null;
  }

  // Click a [data-rank] control to set the standing of its design element.
  document.addEventListener('click', (e) => {
    const star = e.target.closest('[data-rank]');
    if (!star) return;
    const holder = star.closest('[data-element]');
    if (!holder) return;
    const stars = parseInt(star.dataset.rank, 10);
    if (!Number.isInteger(stars) || stars < 0 || stars > 5) return;
    e.stopPropagation();
    holder.dataset.stars = String(stars);
    holder.dataset.scored = 'yes';
    holder.querySelectorAll('[data-rank]').forEach((s) => {
      s.classList.toggle('on', rankIsOn(parseInt(s.dataset.rank, 10), stars));
    });
    sendEvent({
      type: 'rank',
      element: holder.dataset.element,
      choice: holder.dataset.choice || holder.dataset.element,
      stars: stars,
      text: holder.dataset.label || null,
      timestamp: Date.now()
    });
  });

  // Click a [data-sentiment] control to like or dislike its design element.
  // Direction only: strength stays with the star rank.
  document.addEventListener('click', (e) => {
    const mood = e.target.closest('[data-sentiment]');
    if (!mood) return;
    const holder = mood.closest('[data-element]');
    if (!holder) return;
    const sentiment = mood.dataset.sentiment;
    if (sentiment !== 'like' && sentiment !== 'dislike') return;
    e.stopPropagation();
    const already = mood.classList.contains('on');
    holder.querySelectorAll('[data-sentiment]').forEach((s) => s.classList.remove('on'));
    if (!already) mood.classList.add('on');
    const stars = starsOf(holder);
    sendEvent({
      type: 'sentiment',
      element: holder.dataset.element,
      choice: holder.dataset.choice || holder.dataset.element,
      sentiment: already ? null : sentiment,
      stars: stars === null ? undefined : stars,
      text: holder.dataset.label || null,
      timestamp: Date.now()
    });
  });

  // Click [data-reset] to clear a rating. "I have not judged this" is a real
  // state; without it, toggling a control off was purely cosmetic.
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-reset]');
    if (!btn) return;
    const holder = btn.closest('[data-element]');
    if (!holder) return;
    e.stopPropagation();
    holder.dataset.stars = '0';
    holder.dataset.scored = 'no';
    holder.querySelectorAll('[data-rank],[data-sentiment],[data-verdict]')
      .forEach((n) => n.classList.remove('on'));
    sendEvent({ type: 'reset', element: holder.dataset.element,
                choice: holder.dataset.element, reset: true, timestamp: Date.now() });
  });

  // Click a [data-verdict] control to approve or reject outright. Explicit,
  // so nobody has to infer a verdict from a sentence.
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-verdict]');
    if (!btn) return;
    const holder = btn.closest('[data-element]');
    if (!holder) return;
    const verdict = btn.dataset.verdict;
    if (verdict !== 'approved' && verdict !== 'rejected' && verdict !== 'reviewed') return;
    e.stopPropagation();
    // `reviewed` is a toggleable status, not a one-way lock.
    const wasOn = btn.classList.contains('on');
    holder.querySelectorAll('[data-verdict]').forEach((b) => b.classList.remove('on'));
    if (!wasOn) btn.classList.add('on');
    const stars = starsOf(holder);
    sendEvent({
      type: 'verdict',
      element: holder.dataset.element,
      choice: holder.dataset.choice || holder.dataset.element,
      verdict: wasOn ? 'proposed' : verdict,
      stars: stars === null ? undefined : stars,
      text: holder.dataset.label || null,
      timestamp: Date.now()
    });
  });

  // Prove the page is wired. A file:// tab never runs this, so its controls
  // stay visibly dead instead of swallowing clicks in silence.
  document.documentElement.setAttribute('data-dh-live', 'yes');

  // Frame UI: selection tracking
  window.selectedChoice = null;

  window.toggleSelect = function(el) {
    const container = el.closest('.options') || el.closest('.cards');
    const multi = container && container.dataset.multiselect !== undefined;
    if (container && !multi) {
      container.querySelectorAll('.option, .card').forEach(o => o.classList.remove('selected'));
    }
    if (multi) {
      el.classList.toggle('selected');
    } else {
      el.classList.add('selected');
    }
    window.selectedChoice = el.dataset.choice;
  };

  // Expose API for explicit use
  window.brainstorm = {
    send: sendEvent,
    choice: (value, metadata = {}) => sendEvent({ type: 'choice', value, ...metadata }),
    rank: (element, stars, metadata = {}) =>
      sendEvent({ type: 'rank', element, choice: element, stars, ...metadata })
  };

  wireThemeSettings();
  connect();
})();
