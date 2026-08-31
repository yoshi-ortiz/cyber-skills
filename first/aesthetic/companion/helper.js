(function() {
  const MIN_RECONNECT_MS = 500;
  const MAX_RECONNECT_MS = 30000;
  const TOMBSTONE_AFTER_MS = 15000;

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
  function splitStatusParts(raw) {
    const value = String(raw || '').trim();
    const match = value.match(/^((?:\p{Regional_Indicator}{2})|(?:\p{Extended_Pictographic}(?:\uFE0E|\uFE0F)?(?:\u200D\p{Extended_Pictographic}(?:\uFE0E|\uFE0F)?)*))\s*/u);
    return match ? { icon: match[1], text: value.slice(match[0].length) }
      : { icon: '', text: value };
  }
  function agentIdentity(label, app, model, url, kind) {
    let agentApp = String(app || '').trim();
    let agentModel = String(model || '').trim();
    const fallback = String(label || '').trim();
    if (!agentApp && fallback.includes('|')) {
      const parts = fallback.split('|').map(value => value.trim()).filter(Boolean);
      agentApp = parts[0] || '';
      agentModel = parts.slice(1).join(' ');
    }
    if (!agentApp && !agentModel) agentApp = fallback || 'Cyber Yoshi';
    return {
      app: agentApp,
      model: agentModel,
      url: String(url || '').trim(),
      kind: String(kind || '').trim() || 'Agent companion'
    };
  }
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      nextReconnectDelay, rankIsOn, starsForEvent, splitStatusParts, agentIdentity,
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
    const label = el.querySelector('[data-connection-text]');
    if (label) label.textContent = text;
    el.style.setProperty('--status-color', color);
  }

  function wireAgentHeader() {
    const host = document.querySelector('[data-agent-state]');
    const header = document.querySelector('[data-companion-header]');
    if (!host || !header) return;
    const identity = agentIdentity(
      host.getAttribute('data-agent-label'),
      host.getAttribute('data-agent-app'),
      host.getAttribute('data-agent-model'),
      host.getAttribute('data-agent-url'),
      host.getAttribute('data-companion-kind')
    );
    header.querySelector('[data-companion-kind]').textContent = identity.kind;
    header.querySelector('[data-agent-app]').textContent = identity.app;
    header.querySelector('[data-agent-model]').textContent = identity.model;
    const link = header.querySelector('[data-agent-link]');
    if (identity.url) {
      link.href = identity.url;
      link.removeAttribute('aria-disabled');
    } else {
      link.removeAttribute('href');
      link.setAttribute('aria-disabled', 'true');
    }
  }

  function connect() {
    if (reconnectTimer) { clearTimeout(reconnectTimer); reconnectTimer = null; }
    setStatus(everConnected ? 'reconnecting' : 'connecting');
    ws = new WebSocket(websocketUrl());

    ws.onopen = () => {
      everConnected = true;
      disconnectedSince = null;
      reconnectDelay = MIN_RECONNECT_MS;
      setStatus('connected');
      eventQueue.forEach(e => ws.send(JSON.stringify(e)));
      eventQueue = [];
    };

    ws.onmessage = (msg) => {
      let data;
      try { data = JSON.parse(msg.data); } catch (e) { return; }
      if (data.type === 'reload') window.location.reload();
      if (data.type === 'dh-agent') {
        const status = splitStatusParts(data.text);
        data.icon = status.icon;
        data.text = status.text;
        window.__dhLastAgent = data;
        window.dispatchEvent(new CustomEvent('dh-agent', { detail: data }));
      }
    };

    ws.onclose = () => {
      ws = null;
      if (disconnectedSince === null) disconnectedSince = Date.now();
      if (Date.now() - disconnectedSince >= TOMBSTONE_AFTER_MS) {
        setStatus('disconnected');
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

  wireAgentHeader();
  connect();
})();
