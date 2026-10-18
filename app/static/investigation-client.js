/* Shared input resolution and streaming transport for landing and workspace. */
(() => {
  'use strict';
  window.SniffInvestigation = {
    async resolve(text, signal) {
      if (/\b(quantbase|paper\s+(?:vs|versus|and)|company\s+(?:brain|polic)|privacy\s+polic)\b/i.test(text)) return { status: 'question', question: text };
      const response = await fetch('/api/resolve?q=' + encodeURIComponent(text), { signal, credentials: 'same-origin' });
      const body = await response.json();
      if (!response.ok || body.status === 'error') throw new Error(body.message || body.error || 'Coin search is unavailable. Please try again.');
      return body;
    },
    async stream(mint, question, signal, onEvent) {
      const headers = { 'content-type': 'application/json', accept: 'text/event-stream' };
      try { const key = sessionStorage.getItem('sniff.claudeKey'); if (key) headers['x-anthropic-key'] = key; } catch {}
      const response = await fetch('/api/ask', { method: 'POST', headers, signal, credentials: 'same-origin', body: JSON.stringify({ mint, question }) });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || body.detail || 'The investigation could not start. Please try again.');
      }
      if (!response.body) throw new Error('The response stream is unavailable. Please try again.');
      const reader = response.body.getReader(), decoder = new TextDecoder();
      let buffer = '', done = false;
      const flush = () => {
        let boundary;
        while ((boundary = buffer.indexOf('\n\n')) !== -1) {
          const block = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2);
          const payload = block.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
          if (payload) { const event = JSON.parse(payload); if (event.type === 'done') done = true; onEvent(event); }
        }
      };
      try {
        for (;;) {
          const chunk = await reader.read();
          buffer += decoder.decode(chunk.value, { stream: !chunk.done }).replace(/\r\n/g, '\n');
          flush();
          if (chunk.done) break;
        }
        if (buffer.trim()) { buffer += '\n\n'; flush(); }
        if (!done) throw new Error('The connection ended early. Please try again.');
      } finally { reader.releaseLock(); }
    },
  };
})();
