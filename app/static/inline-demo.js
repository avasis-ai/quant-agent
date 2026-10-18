/* Landing-page investigation. Same graph, streaming endpoint, keys and caps as /app. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  const short = value => value ? value.slice(0, 4) + '…' + value.slice(-4) : 'Not recorded';
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const DEFAULT = 'Who is behind this coin?';
  const STEP = { search_coins: 'Find the coin', coin_dossier: 'Inspect creator and funders', siblings: 'Check connected launches', shared_handles: 'Compare reused socials', shared_snipers: 'Compare early buyers', funding_trail: 'Trace the funding trail', ring: 'Inspect the funding ring', connect: 'Find a connecting path', memory_recall: 'Recall recorded evidence', brain_ask: 'Retrieve public sources' };
  let request, serial = 0, graph, coin = null, agentEvidence = [], dossierEvidence = [], brainGraph = null, lastInput = '';
  let matchingCoins = [], currentQuestion = DEFAULT;
  const allEvidence = () => [...agentEvidence, ...dossierEvidence];
  const citation = (id, label = '[' + id + ']') => `<button class="inline-citation" type="button" data-inline-e="${esc(id)}" aria-pressed="false" aria-label="Inspect evidence ${esc(id)}">${esc(label)}</button>`;

  function select(selection) {
    document.querySelectorAll('[data-inline-e]').forEach(button => {
      const active = selection.type === 'evidence' && button.dataset.inlineE === selection.id;
      button.setAttribute('aria-pressed', String(active));
    });
    if (selection.type === 'evidence') $('inline-selection').textContent = `[${selection.id}] ${selection.item.summary}`;
    else if (selection.type === 'node') $('inline-selection').textContent = selection.kind === 'hub' ? 'Hub · dead end. This exchange-like funder never links creators together.' : (selection.label || selection.node.name || '') + (selection.node.addr ? ' · ' + selection.node.addr : '');
    else $('inline-selection').textContent = 'Select an evidence tag or a node to inspect its source.';
  }
  function refreshGraph() {
    if (!graph) graph = new window.SniffGraph($('inline-graph'), select, { compact: true });
    const items = allEvidence();
    // Keep the first path compact; every original result remains in evidence below.
    const focus = coin ? 'coin:' + coin.mint : null;
    const primary = new Set(focus ? [focus] : []);
    for (const item of items) for (const edge of item.edges || []) {
      if (edge.type === 'CREATED' && edge.dst === focus) primary.add(edge.src);
    }
    for (const item of items) for (const edge of item.edges || []) {
      if (edge.type === 'FUNDED' && primary.has(edge.dst)) primary.add(edge.src);
      if (edge.type === 'IN_RING' && primary.has(edge.src)) primary.add(edge.dst);
    }
    const compact = brainGraph ? items : items.map(item => ({ ...item, nodes: (item.nodes || []).filter(node => primary.has(node.key)), edges: (item.edges || []).filter(edge => primary.has(edge.src) && primary.has(edge.dst)) }));
    graph.setEvidence(compact, focus, brainGraph);
    $('inline-sources').hidden = !items.length;
    $('inline-source-count').textContent = String(items.length);
    $('inline-source-list').innerHTML = items.map(item => `<button type="button" data-inline-e="${esc(item.id)}" aria-pressed="false"><strong>${esc(item.id)}</strong><span>${esc(item.summary)}</span></button>`).join('');
    if (!graph.cy?.nodes().length) $('inline-selection').textContent = 'No recorded connections returned. The answer and source evidence remain available.';
  }
  function showDossier(body) {
    const d = body.coin_dossier;
    if (!d?.found) throw new Error(d?.error || 'Not in our snapshot (ends 14 Oct 2026). Try one of the recorded coins.');
    coin = d.coin;
    const funder = d.funders?.[0];
    const fact = (label, text, id) => `<div><dt>${esc(label)}</dt><dd>${esc(text)} ${id ? citation('d' + id, '↗') : ''}</dd></div>`;
    $('inline-dossier').innerHTML = `<div class="inline-coin"><strong>${esc(coin.name || short(coin.mint))}</strong><span>${esc(coin.symbol ? '$' + coin.symbol : '')} · <span class="${coin.graduated ? 'inline-graduated' : ''}">${coin.graduated ? 'Graduated' : 'Did not graduate'}</span></span><a href="https://solscan.io/token/${encodeURIComponent(coin.mint)}" target="_blank" rel="noopener noreferrer" aria-label="View ${esc(coin.name)} mint on Solscan (opens in a new tab)">${esc(short(coin.mint))} ↗</a></div><dl>${fact('Creator history', d.creator_other_coins + ' other launches', d.evidence?.[0])}${fact('Funder', funder?.label === 'Hub' ? 'Hub · dead end' : funder ? short(funder.addr) : 'Not recorded', funder?.evidence)}${fact('Funding ring', d.ring ? d.ring.creators + ' creators · ' + d.ring.coins + ' coins' : 'No ring recorded', d.ring?.evidence)}</dl>`;
    dossierEvidence = (body.evidence || []).map(item => ({ ...item, id: 'd' + item.id }));
    $('inline-dossier').hidden = false;
    $('inline-title').textContent = coin.name || 'Coin investigation';
    refreshGraph();
  }
  function step(text, ok = true, ms) {
    const row = document.createElement('li');
    row.className = ok ? 'inline-step-ok' : 'inline-step-bad';
    row.innerHTML = `<span>${esc(text)}</span><span>${ms == null ? '' : esc(ms) + ' ms'}</span>`;
    $('inline-steps').append(row);
    $('inline-step-count').textContent = String($('inline-steps').children.length);
  }
  function setLink(mint, question) {
    const params = new URLSearchParams();
    if (mint) params.set('mint', mint);
    if (question) params.set('q', question);
    $('inline-full').href = '/app?' + params;
    $('inline-full').hidden = false;
  }
  async function run(input, knownMint = null, questionOverride = null, matches = []) {
    request?.abort();
    request = new AbortController();
    const { signal } = request;
    const token = ++serial;
    lastInput = input;
    coin = null; agentEvidence = []; dossierEvidence = []; brainGraph = null;
    document.body.classList.add('inline-active');
    $('inline-demo').hidden = false;
    $('inline-body').hidden = true;
    $('inline-full').hidden = true;
    $('inline-retry').hidden = true;
    $('inline-dossier').hidden = true;
    $('inline-sources').hidden = true;
    $('inline-matches').hidden = true;
    $('inline-title').textContent = 'Following the trail.';
    $('inline-status').textContent = 'Looking up the coin…';
    $('inline-status').classList.remove('inline-error');
    $('inline-answer').textContent = 'Tracing the creator, funding and connected launches…';
    $('inline-mode').textContent = '';
    $('inline-steps').replaceChildren();
    $('inline-step-count').textContent = '';
    $('inline-step-details').open = true;
    graph?.cy?.elements().remove();
    $('inline-fit').disabled = true;
    const submit = $('inline-form').querySelector('button');
    submit.disabled = true;
    submit.setAttribute('aria-busy', 'true');
    document.querySelectorAll('[data-inline-mint]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.inlineMint === knownMint)));
    $('inline-title').focus({ preventScroll: true });
    $('inline-demo').scrollIntoView({ behavior: reduced() ? 'auto' : 'smooth', block: 'start' });
    try {
      const resolved = knownMint ? { status: 'found', coin: { mint: knownMint }, question: questionOverride || DEFAULT, rows: matches } : await window.SniffInvestigation.resolve(input, signal);
      if (signal.aborted || token !== serial) return;
      if (resolved.status === 'missing') throw new Error(resolved.message);
      if (!resolved.coin && !/\b(quantbase|company|privacy|paper)\b/i.test(input)) throw new Error('Name a coin or paste its mint to start a new trail. Our snapshot ends 14 Oct 2026.');
      coin = resolved.coin || null;
      const question = resolved.question || DEFAULT;
      currentQuestion = question;
      matchingCoins = resolved.rows || [];
      if (matchingCoins.length > 1) {
        $('inline-match-select').innerHTML = matchingCoins.map(row => `<option value="${esc(row.mint)}"${row.mint === coin?.mint ? ' selected' : ''}>${esc(row.name)} · ${esc(short(row.mint))}${row.graduated ? ' · graduated' : ''}</option>`).join('');
        $('inline-matches').hidden = false;
      }
      $('inline-body').hidden = false;
      if (coin) {
        const response = await fetch('/api/dossier?mint=' + encodeURIComponent(coin.mint), { signal, credentials: 'same-origin' });
        const body = await response.json();
        if (!response.ok) throw new Error(body.error || 'The dossier could not load. Please try again.');
        if (signal.aborted || token !== serial) return;
        showDossier(body);
      }
      setLink(coin?.mint, question);
      $('inline-status').textContent = resolved.note || 'The dossier is ready. Following the evidence…';
      let hasVerdict = false;
      await window.SniffInvestigation.stream(coin?.mint || null, question, signal, event => {
        if (signal.aborted || token !== serial) return;
        if (event.type === 'start') {
          $('inline-status').textContent = event.mode === 'agent' ? 'Claude is investigating the recorded graph…' : event.mode === 'brain' ? 'Retrieving public sources…' : 'Running the recorded graph checks…';
        } else if (event.type === 'step') {
          step(STEP[event.tool] || event.tool.replaceAll('_', ' '), event.ok, event.ms);
        } else if (event.type === 'notice') {
          $('inline-status').textContent = event.text;
        } else if (event.type === 'evidence') {
          agentEvidence = event.items || [];
          refreshGraph();
        } else if (event.type === 'verdict') {
          hasVerdict = true;
          if (event.graph) { brainGraph = event.graph; refreshGraph(); }
          const ids = new Set(agentEvidence.map(item => item.id));
          $('inline-answer').innerHTML = esc(event.text || 'No answer was returned. Try a different question.').replace(/\[([EB]\d+)\]/g, (tag, id) => ids.has(id) ? citation(id) : tag).split(/\n{2,}/).map(p => '<p>' + p.replace(/\n/g, '<br>') + '</p>').join('');
          $('inline-mode').textContent = event.mode === 'agent' ? 'Written by Claude from graph evidence' : event.mode === 'brain' ? 'Public source excerpts' : 'Recorded graph dossier · AI is unavailable for this run';
        } else if (event.type === 'done') {
          step('Investigation complete', true, event.ms);
          $('inline-step-details').open = false;
          $('inline-status').textContent = 'Evidence ready · Snapshot ends 14 Oct 2026' + (resolved.note ? ' · ' + resolved.note : '');
        }
      });
      if (!hasVerdict) throw new Error('The stream returned no answer. Please try again.');
    } catch (error) {
      if (signal.aborted || token !== serial) return;
      $('inline-status').textContent = error.message;
      $('inline-status').classList.add('inline-error');
      $('inline-retry').hidden = false;
      if (!$('inline-dossier').hidden) $('inline-answer').textContent = 'The answer could not finish. You can inspect the recorded dossier and evidence, or try again.';
    } finally {
      if (token === serial) {
        submit.disabled = false;
        submit.setAttribute('aria-busy', 'false');
        $('inline-fit').disabled = !graph?.cy?.nodes().length;
      }
    }
  }
  $('inline-form').addEventListener('submit', event => {
    event.preventDefault();
    const input = $('home-question').value.trim();
    if (input) run(input);
  });
  document.addEventListener('click', event => {
    const example = event.target.closest('[data-inline-mint]');
    if (example) { $('home-question').value = example.textContent.trim(); run(example.textContent.trim(), example.dataset.inlineMint); }
    const button = event.target.closest('[data-inline-e]');
    if (button) {
      graph?.highlight(button.dataset.inlineE, false);
      // Also expose evidence whose nodes were omitted from the compact path.
      const item = allEvidence().find(item => item.id === button.dataset.inlineE);
      if (item) select({ type: 'evidence', id: item.id, item });
      $('inline-selection').scrollIntoView({ behavior: reduced() ? 'auto' : 'smooth', block: 'nearest' });
    }
  });
  $('inline-fit').addEventListener('click', () => { graph?.clear(); graph?.fit(); });
  $('inline-again').addEventListener('click', () => run(lastInput));
  $('inline-match-select').addEventListener('change', event => run(lastInput, event.target.value, currentQuestion, matchingCoins));
})();
