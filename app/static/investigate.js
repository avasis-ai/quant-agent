(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
  const short = value => value && value.length > 14 ? value.slice(0, 4) + '…' + value.slice(-4) : (value || '');
  const MINT = /^[1-9A-HJ-NP-Za-km-z]{32,44}$/;
  const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;
  const DEFAULT_QUESTION = 'Who is behind this coin?';
  const date = timestamp => timestamp ? new Date(timestamp * 1000).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' }) : 'Not recorded';
  const visitorKey = () => { try { return sessionStorage.getItem('sniff.claudeKey') || ''; } catch { return ''; } };
  const coinLegend = document.querySelector('.legend').innerHTML;
  const coinPolicy = document.querySelector('.map-policy').textContent;
  const coinGraphLabel = $('graph').getAttribute('aria-label');
  const plainExcerpt = text => text.replace(/^\s*(?:#{1,6}\s+|[-*]\s+)/gm, '').replace(/\*\*|__/g, '').replace(/`([^`]+)`/g, '$1');
  const STEP = {
    search_coins: 'Looking up the coin', coin_dossier: 'Checking the creator and funders',
    funding_trail: 'Following the funding trail', siblings: 'Checking the funder’s other creators',
    shared_snipers: 'Comparing early buyers', shared_handles: 'Looking for reused socials',
    ring: 'Inspecting the funding ring', connect: 'Finding a connecting path', top_operators: 'Finding the busiest operators',
    brain_ask: 'Retrieving public source sections',
  };
  let graph, request = null, run = 0, selectedMint = null, cardEvidence = [], agentEvidence = [], currentMint = null;
  let searchRows = [], searchIndex = -1, searchTimer, searchRequest, hasVerdict = false;
  let dossierMint = null, brainGraph = null, brainSources = [];

  function address(value, kind = 'account') {
    return `<a class="addr" href="https://solscan.io/${kind}/${encodeURIComponent(value || '')}" target="_blank" rel="noopener noreferrer">${esc(short(value))}<span class="sr-only"> on Solscan (opens in a new tab)</span></a>`;
  }
  function citation(id, label) {
    return id ? `<button type="button" class="ev" data-e="${esc(id)}" aria-label="Show ${id.startsWith('c') ? 'dossier evidence ' + esc(id.slice(1)) : 'evidence ' + esc(id)}" aria-pressed="false">${esc(label || '[' + id + ']')}</button>` : '';
  }
  function cardCitation(id) { return citation(id ? 'c' + id : null, '↗'); }
  function sourceLink(url, label) {
    try {
      const parsed = new URL(url);
      if (parsed.protocol === 'https:') return `<a href="${esc(parsed.href)}" target="_blank" rel="noopener noreferrer">${esc(label)}</a>`;
    } catch {}
    return esc(label);
  }

  function graphSelection(selection) {
    document.querySelectorAll('.ev').forEach(button => {
      const active = selection.type === 'evidence' && button.dataset.e === selection.id;
      button.classList.toggle('on', active);
      button.setAttribute('aria-pressed', String(active));
    });
    if (selection.type === 'clear') {
      $('evline').textContent = 'Select a node or an evidence tag to follow a connection.';
    } else if (selection.type === 'evidence') {
      const label = selection.id.startsWith('c') ? 'Dossier' : `[${selection.id}]`;
      $('evline').innerHTML = `<b>${esc(label)}</b> ${esc(selection.item.summary)}`;
    } else {
      const node = selection.node;
      if (brainGraph) $('evline').innerHTML = `<b>${esc(node.label)}</b> · ${esc(node.name || node.key)}${node.url ? ' · ' + sourceLink(node.url, 'Open public source') : ''}${node.citation ? ' · ' + citation(node.citation) : ''}`;
      else if (selection.kind === 'hub') $('evline').innerHTML = '<b>Hub · dead end.</b> This exchange-like wallet paid more than 200 wallets. Sniff does not connect creators through it.';
      else if (selection.kind === 'coin') $('evline').innerHTML = `<b>${esc(node.name || short(node.mint))}</b> · ${node.graduated ? 'Graduated' : 'Did not graduate'} · ${address(node.mint, 'token')}`;
      else if (selection.kind === 'ring') $('evline').innerHTML = `<b>Funding ring</b> · ${esc(node.creators)} creators · ${esc(node.coins)} coins · ${esc(node.graduations)} graduated`;
      else if (selection.kind === 'handle') $('evline').textContent = `${node.handle || ''} on ${node.platform || 'social / website'} · used by ${node.coins ?? '?'} coins`;
      else if (selection.kind === 'group') $('evline').textContent = selection.label.replace('\n', ' · ') + '. This is a group total, not an individual wallet.';
      else $('evline').innerHTML = `<b>Wallet</b> · ${address(node.addr)}${node.launches != null ? ` · ${esc(node.launches)} launches · ${esc(node.graduations ?? 0)} graduated` : ''}`;
    }
  }
  function initGraph() {
    if (!graph) graph = new window.SniffGraph($('graph'), graphSelection);
    return graph;
  }
  function refreshGraph() {
    // Each API response has its own E1… sequence. Prefix the fixed dossier ids.
    const items = [...agentEvidence, ...cardEvidence];
    $('map-title').textContent = brainGraph ? 'Public source graph' : 'The connection map';
    $('graph').setAttribute('aria-label', brainGraph ? 'Public source graph. Arrow keys pan, plus and minus zoom. Use B citations or Graph details to inspect sources.' : coinGraphLabel);
    if (brainGraph) {
      document.querySelector('.legend').textContent = [...new Set(brainGraph.nodes.map(node => node.label))].join(' · ');
      document.querySelector('.map-policy').textContent = 'MENTIONS connects literal source anchors; PART_OF connects sections to documents.';
    } else {
      document.querySelector('.legend').innerHTML = coinLegend;
      document.querySelector('.map-policy').textContent = coinPolicy;
    }
    initGraph().setEvidence(items, currentMint ? 'coin:' + currentMint : null, brainGraph);
    const count = graph.cy?.nodes().length || 0;
    syncViewport();
    $('graph-count').textContent = count ? `${count} nodes · ${graph.cy.edges().length} links` : 'No connections returned';
    $('graph-empty').hidden = Boolean(count);
    if (!count) {
      $('graph-empty').querySelector('h3').textContent = graph.cy ? 'No recorded connections.' : 'The map is unavailable.';
      $('graph-empty').querySelector('p').textContent = graph.cy ? 'No links were returned for this question. Try a recorded example or a different coin.' : 'The answer and evidence are still available. Reload the page to try the map again.';
    }
    $('graph-details').hidden = !count;
    $('graph-loading').hidden = true;
    $('node-list').innerHTML = [...graph.nodes.entries()].map(([key, node]) => `<button type="button" data-node="${esc(key)}">${esc(node.label)} · ${esc(graph.label(node))}</button>`).join('');
    $('source-details').hidden = !items.length;
    $('evidence-count').textContent = String(items.length);
    $('evidence-list').innerHTML = brainGraph ? brainSources.map(source => `<article class="brain-source" id="source-${esc(source.id)}" tabindex="-1"><h3>${sourceLink(source.url, '[' + source.id + '] ' + source.title)}</h3><p class="meta">${esc(source.section_title)} · Fetched ${esc(date(source.fetched_at))}</p><blockquote>${esc(plainExcerpt(source.excerpt))}</blockquote><details><summary>Read the source section</summary><pre>${esc(source.text)}</pre></details><button type="button" data-source="${esc(source.id)}">Show ${esc(source.id)} on the graph</button></article>`).join('') : items.map(item => `<button type="button" data-source="${esc(item.id)}"><strong>${esc(item.id.startsWith('c') ? 'Dossier' : item.id)}</strong>${esc(item.summary)}</button>`).join('');
    graphSelection({ type: 'clear' });
  }
  function showEvidence(id) {
    graph?.highlight(id);
    if (id.startsWith('B')) {
      $('source-details').open = true;
      const source = $('source-' + id);
      if (source) {
        source.querySelector('details').open = true;
        source.focus({ preventScroll: true });
        source.scrollIntoView({ behavior: reduce() ? 'auto' : 'smooth', block: 'start' });
        return;
      }
    }
    if (innerWidth <= 768) $('results').scrollIntoView({ behavior: reduce() ? 'auto' : 'smooth', block: 'start' });
  }
  function syncViewport() {
    const count = graph?.cy?.nodes().length || 0;
    const zoom = graph?.cy?.zoom() || 1;
    $('zoom-in').disabled = !count || zoom >= graph.cy.maxZoom() - .001;
    $('zoom-out').disabled = !count || zoom <= graph.cy.minZoom() + .001;
    $('reset').disabled = !count;
    $('zoom-value').textContent = count ? Math.round(zoom * 100) + '%' : '…';
  }

  function renderCard(response) {
    const dossier = response.coin_dossier || {};
    if (dossier.error) return `<p class="note err">${esc(dossier.error)}</p>`;
    if (!dossier.found) return `<p class="note">${esc(dossier.note || 'This coin is not in the snapshot. Try one of the example investigations above.')}</p>`;
    const coin = dossier.coin, creator = dossier.creator, funders = dossier.funders || [], ring = dossier.ring;
    const sibling = response.siblings?.rows?.[0];
    const handles = response.shared_handles?.rows || [];
    const payers = funders.filter(funder => funder.label !== 'Hub');
    const hub = funders.find(funder => funder.label === 'Hub');
    const payer = payers.length ? payers.map(funder => `${address(funder.addr)} ${cardCitation(funder.evidence)}`).join('<br>') : hub ? `Hub · dead end ${cardCitation(hub.evidence)}` : 'No funder recorded';
    const base = response.base ? `${(response.base.rate * 100).toFixed(1)}% of launches in this snapshot graduated.` : '';
    return `<div class="coinhead"><div class="coin-name">${esc(coin.name || short(coin.mint))}${coin.symbol ? `<span class="coin-symbol">$${esc(coin.symbol)}</span>` : ''}</div><span class="tag ${coin.graduated ? 'grad' : ''}"><i aria-hidden="true"></i>${coin.graduated ? 'Graduated' : 'Did not graduate'}</span>${address(coin.mint, 'token')}</div>
      <dl class="dossier-facts">
        <div><dt>Creator history</dt><dd><strong>${esc(dossier.creator_other_coins)} other launches</strong> ${cardCitation(dossier.evidence?.[0])}<span class="detail">${esc(dossier.creator_other_graduated)} graduated · ${esc(short(creator?.addr))}</span></dd></div>
        <div><dt>Funded by</dt><dd>${payer}<span class="detail">${payers[0]?.sol != null ? Number(payers[0].sol).toFixed(4) + ' SOL recorded' : hub ? 'Never traversed to link creators' : 'Missing coverage is possible'}</span></dd></div>
        <div><dt>Same funder</dt><dd><strong>${sibling ? esc(sibling.creators) + ' other creators' : 'None found'}</strong> ${cardCitation(sibling?.evidence)}<span class="detail">${sibling ? `${esc(sibling.coins)} launches · ${esc(sibling.graduated)} graduated` : 'In the recorded funding data'}</span></dd></div>
        <div><dt>Funding ring</dt><dd><strong>${ring ? esc(ring.creators) + ' creators' : 'No ring found'}</strong> ${cardCitation(ring?.evidence)}<span class="detail">${ring ? `${esc(ring.coins)} coins · ${esc(ring.graduations)} graduated` : 'Hubs excluded from rings'}</span></dd></div>
      </dl>
      <details class="full-dossier"><summary>Full dossier & socials</summary><dl class="full-facts"><div><dt>Launched</dt><dd>${esc(date(coin.created_at))} <span class="mut">UTC</span></dd></div><div><dt>Creator</dt><dd>${creator?.addr ? address(creator.addr) : 'Not recorded'}</dd></div><div><dt>Socials</dt><dd>${handles.length ? handles.slice(0, 3).map(handle => `${esc(handle.platform === 'twitter' ? 'X' : handle.platform)} · ${esc(handle.handle)} · ${esc(handle.other_coins)} other coins ${cardCitation(handle.evidence)}`).join('<br>') : 'No reused socials found in this snapshot.'}</dd></div><div><dt>Mint</dt><dd class="mono">${esc(coin.mint)}</dd></div></dl><p class="dossier-context">${esc(base)} History, not a prediction.</p></details>`;
  }

  async function loadDossier(mint, token, signal) {
    dossierMint = mint;
    $('cardPanel').hidden = false;
    $('card').innerHTML = '<div class="dossier-loading" aria-label="Loading coin dossier"><span></span><span></span><span></span><span></span></div>';
    try {
      const response = await fetch('/api/dossier?mint=' + encodeURIComponent(mint), { signal, credentials: 'same-origin' });
      const result = await response.json();
      if (!response.ok) throw new Error(result.error || 'The dossier could not load. Try again.');
      if (token !== run) return;
      $('card').innerHTML = renderCard(result);
      cardEvidence = (result.evidence || []).map(item => ({ ...item, id: 'c' + item.id }));
      refreshGraph();
      if (result.coin_dossier?.coin) {
        $('coin').value = result.coin_dossier.coin.name || mint;
        selectedMint = mint;
        document.title = `${result.coin_dossier.coin.name || short(mint)} · Sniff investigation`;
      }
    } catch (error) {
      if (signal.aborted || token !== run) return;
      $('card').innerHTML = `<p class="note err">${esc(error.message)}</p>`;
    }
  }

  function stepRow(text, state, ms) {
    const row = document.createElement('li');
    row.className = state;
    row.innerHTML = `<span class="d" aria-hidden="true"></span><span>${esc(text)}</span><span class="ms">${ms != null ? esc(ms) + ' ms' : state === 'run' ? 'Running' : ''}</span>`;
    $('steps').append(row);
    return row;
  }
  function busy(value) {
    $('go').disabled = value;
    $('go').innerHTML = value ? 'Investigating…' : 'Investigate <span class="arrow" aria-hidden="true">↗</span>';
    $('go').setAttribute('aria-busy', String(value));
    document.querySelectorAll('.chip').forEach(button => { button.disabled = value; });
  }
  function verdict(event) {
    hasVerdict = true;
    if (event.mode === 'brain') {
      brainGraph = event.graph || { nodes: [], edges: [] };
      brainSources = event.sources || [];
      refreshGraph();
      $('note').textContent = '';
    }
    const available = new Set(agentEvidence.map(item => item.id));
    // Escape before inserting markup; unrecognized tags are plain text.
    const answer = event.mode === 'brain' ? plainExcerpt(event.text || '') : event.text || '';
    const text = esc(answer.replace(/(\[[EB]\d+\][.!?]?)\s+(?=[A-Z])/g, '$1\n\n').replace(/\s+(For context:)/g, '\n\n$1'))
      .replace(/\[([EB]\d+)\]/g, (tag, id) => available.has(id) ? citation(id) : tag);
    $('verdict').innerHTML = text.split(/\n{2,}/).map(paragraph => `<p${paragraph.startsWith('For context:') ? ' class="answer-context"' : ''}>` + paragraph.replace(/\n/g, '<br>') + '</p>').join('');
    $('mode').textContent = event.mode === 'brain' ? 'Public source excerpts' : event.mode === 'agent' ? 'Written by Claude from graph evidence' : 'Fixed dossier · direct graph checks';
    $('answer-status').textContent = 'Evidence ready';
    $('answer-actions').hidden = false;
  }

  async function investigate(mint, question = '', updateUrl = true) {
    request?.abort();
    request = new AbortController();
    const { signal } = request;
    const token = ++run;
    document.body.classList.add('has-investigation');
    currentMint = mint;
    question = question.trim() || DEFAULT_QUESTION;
    agentEvidence = []; cardEvidence = []; dossierMint = null; hasVerdict = false; brainGraph = null; brainSources = [];
    closeSuggestions();
    if (updateUrl) {
      const parameters = new URLSearchParams();
      if (mint) parameters.set('mint', mint);
      if (question !== DEFAULT_QUESTION || !mint) parameters.set('q', question);
      history.replaceState(null, '', '/app?' + parameters.toString());
    }
    $('answer-empty').hidden = true;
    $('graph-empty').hidden = true;
    $('graph-loading').hidden = false;
    $('graph-count').textContent = 'Following the evidence';
    $('cardPanel').hidden = !mint;
    $('steps').replaceChildren();
    $('step-details').hidden = false; $('step-details').open = true;
    $('source-details').hidden = true; $('graph-details').hidden = true;
    $('step-count').textContent = '';
    $('verdict').innerHTML = '<span class="wait">Tracing creators, funding and connected launches…</span>';
    $('note').textContent = ''; $('note').className = 'note';
    $('mode').textContent = '';
    $('answer-status').textContent = 'Investigating';
    $('answer-actions').hidden = true;
    graph?.cy?.elements().remove();
    ['zoom-in', 'zoom-out', 'reset'].forEach(id => { $(id).disabled = true; });
    graphSelection({ type: 'clear' });
    busy(true);
    if (mint) loadDossier(mint, token, signal);
    let pending = stepRow('Starting the investigation', 'run');
    let completedSteps = 0, doneEvent = false;
    const headers = { 'content-type': 'application/json', accept: 'text/event-stream' };
    const key = visitorKey();
    if (key) headers['x-anthropic-key'] = key;
    const onEvent = event => {
      if (token !== run) return;
      if (event.type === 'start') {
        pending.remove();
        pending = stepRow(event.mode === 'brain' ? 'Finding public company sources' : event.mode === 'agent' ? 'Claude is planning the graph queries' : 'Running the fixed graph checks', 'run');
        if (event.mode === 'dossier') $('note').innerHTML = 'Using the fixed dossier. Add a Claude key in <a href="/settings">Settings</a> for a written answer.';
      } else if (event.type === 'step') {
        pending.remove();
        stepRow(STEP[event.tool] || event.tool, event.ok ? 'ok' : 'bad', event.ms);
        completedSteps++;
        $('step-count').textContent = String(completedSteps);
        pending = stepRow('Following the next connection', 'run');
        if (!currentMint && event.input?.mint && MINT.test(event.input.mint)) {
          currentMint = event.input.mint;
          if (dossierMint !== currentMint) loadDossier(currentMint, token, signal);
        }
      } else if (event.type === 'notice') {
        $('note').textContent = event.text;
      } else if (event.type === 'evidence') {
        agentEvidence = event.items || [];
        refreshGraph();
      } else if (event.type === 'verdict') {
        pending.remove();
        verdict(event);
      } else if (event.type === 'done') {
        doneEvent = true;
        pending.remove();
        stepRow('Investigation complete', 'ok', event.ms);
        $('step-count').textContent = `${completedSteps} checks`;
        $('step-details').open = false;
      }
    };
    try {
      const response = await fetch('/api/ask', { method: 'POST', headers, signal, credentials: 'same-origin', body: JSON.stringify({ question, mint: mint || null }) });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || 'Sniff could not answer right now. Please try again.');
      }
      if (!response.body) throw new Error('The response stream is unavailable. Please try again.');
      const reader = response.body.getReader(), decoder = new TextDecoder();
      let buffer = '';
      const flush = () => {
        let boundary;
        while ((boundary = buffer.indexOf('\n\n')) !== -1) {
          const chunk = buffer.slice(0, boundary); buffer = buffer.slice(boundary + 2);
          const payload = chunk.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
          if (payload) onEvent(JSON.parse(payload));
        }
      };
      for (;;) {
        const { value, done } = await reader.read();
        if (signal.aborted || token !== run) { await reader.cancel(); return; }
        if (done) { buffer = (buffer + decoder.decode()).replace(/\r\n/g, '\n'); if (buffer.trim()) buffer += '\n\n'; flush(); break; }
        buffer = (buffer + decoder.decode(value, { stream: true })).replace(/\r\n/g, '\n');
        flush();
      }
      if (!hasVerdict || !doneEvent) throw new Error('The investigation stream ended early. Please try again.');
    } catch (error) {
      if (signal.aborted || token !== run) return;
      pending.remove();
      if (!hasVerdict) $('verdict').textContent = '';
      $('note').className = 'note err';
      $('note').textContent = error.message || 'The investigation could not complete. Please try again.';
      $('answer-status').textContent = 'Could not complete';
      stepRow('Investigation interrupted', 'bad');
    } finally {
      if (token === run) { busy(false); $('graph-loading').hidden = true; }
    }
  }

  function closeSuggestions() {
    clearTimeout(searchTimer);
    searchRequest?.abort();
    $('sugg').hidden = true;
    $('coin').setAttribute('aria-expanded', 'false');
    $('coin').removeAttribute('aria-activedescendant');
  }
  function showSuggestions(rows, message) {
    searchRows = rows; searchIndex = -1;
    $('sugg').innerHTML = rows.length ? rows.map((coin, index) => `<button type="button" role="option" id="suggestion-${index}" aria-selected="false" tabindex="-1" data-index="${index}"><span class="nm">${esc(coin.name || short(coin.mint))} ${coin.symbol ? `<span class="meta">$${esc(coin.symbol)}</span>` : ''}</span><span class="meta">${coin.graduated ? 'Graduated' : esc(date(coin.created_at))} · ${esc(short(coin.mint))}</span></button>`).join('') : `<p class="search-message">${esc(message || 'No matching coins in this snapshot. Paste the full mint address or try an example.')}</p>`;
    $('sugg').hidden = false;
    $('coin').setAttribute('aria-expanded', 'true');
  }
  function choose(coin) {
    selectedMint = coin.mint;
    $('coin').value = coin.name || coin.mint;
    closeSuggestions();
    $('q').focus();
  }
  $('coin').addEventListener('input', () => {
    $('coin').removeAttribute('aria-invalid');
    selectedMint = null; searchRows = []; searchIndex = -1;
    closeSuggestions(); clearTimeout(searchTimer); searchRequest?.abort();
    const query = $('coin').value.trim();
    if (query.length < 2 || MINT.test(query)) return;
    searchTimer = setTimeout(async () => {
      searchRequest = new AbortController();
      try {
        const response = await fetch('/api/search?q=' + encodeURIComponent(query), { signal: searchRequest.signal, credentials: 'same-origin' });
        const body = await response.json();
        if ($('coin').value.trim() !== query) return;
        if (!response.ok) throw new Error(body.error || 'Coin search is unavailable. You can still paste an address.');
        showSuggestions(body.rows || []);
      } catch (error) {
        if (error.name !== 'AbortError' && $('coin').value.trim() === query) showSuggestions([], error.message);
      }
    }, 220);
  });
  $('coin').addEventListener('keydown', event => {
    if ($('sugg').hidden) return;
    if ((event.key === 'ArrowDown' || event.key === 'ArrowUp') && searchRows.length) {
      event.preventDefault();
      searchIndex = (searchIndex + (event.key === 'ArrowDown' ? 1 : -1) + searchRows.length) % searchRows.length;
      $('sugg').querySelectorAll('button').forEach((button, index) => {
        button.classList.toggle('sel', index === searchIndex);
        button.setAttribute('aria-selected', String(index === searchIndex));
      });
      const active = $('suggestion-' + searchIndex);
      $('coin').setAttribute('aria-activedescendant', active.id);
      active.scrollIntoView({ block: 'nearest' });
    } else if (event.key === 'Enter' && searchIndex >= 0) {
      event.preventDefault(); choose(searchRows[searchIndex]);
    } else if (event.key === 'Escape' || event.key === 'Tab') closeSuggestions();
  });
  $('sugg').addEventListener('click', event => {
    const button = event.target.closest('[data-index]');
    if (button) choose(searchRows[Number(button.dataset.index)]);
  });
  async function resolveAndInvestigate(input, question = '', updateUrl = true) {
    request?.abort();
    request = new AbortController();
    const signal = request.signal;
    busy(true);
    $('note').textContent = 'Looking up the coin…';
    try {
      const result = await window.SniffInvestigation.resolve(input || question, signal);
      if (signal.aborted) return;
      if (result.status === 'missing') {
        selectedMint = null;
        $('coin').value = input;
        $('coin').setAttribute('aria-invalid', 'true');
        $('note').textContent = result.message + ' Choose METHU, Subprime Cat, Women in Finance or Higher above.';
        $('note').className = 'note err';
        $('cardPanel').hidden = true;
        $('verdict').replaceChildren();
        graph?.cy?.elements().remove();
        return;
      }
      selectedMint = result.coin?.mint || null;
      $('coin').value = result.coin?.name || '';
      const resolvedQuestion = question || result.question || DEFAULT_QUESTION;
      $('q').value = resolvedQuestion === DEFAULT_QUESTION ? '' : resolvedQuestion;
      await investigate(selectedMint, resolvedQuestion, updateUrl);
      if (result.note) $('note').textContent = result.note;
    } catch (error) {
      if (!signal.aborted) { $('note').textContent = error.message; $('note').className = 'note err'; }
    } finally { if (!signal.aborted) busy(false); }
  }
  $('form').addEventListener('submit', event => {
    event.preventDefault();
    if ($('go').disabled) return;
    const input = $('coin').value.trim(), question = $('q').value.trim();
    if (!input && !question) { $('coin').focus(); return; }
    const mint = selectedMint || (MINT.test(input) ? input : null);
    if (mint) investigate(mint, question);
    else resolveAndInvestigate(input, question);
  });
  function example(mint, name) { selectedMint = mint; $('coin').value = name; investigate(mint, $('q').value); }
  $('chips').addEventListener('click', event => {
    const button = event.target.closest('[data-mint]');
    if (button && !button.disabled) example(button.dataset.mint, button.querySelector('b').textContent);
  });
  $('empty-example').addEventListener('click', () => example('3LaVxn1Pp5gDjJZgGrpbQ8gRKj7GxgPE8cjF62Svpump', 'METHU'));
  document.addEventListener('click', event => {
    const citationButton = event.target.closest('[data-e], [data-source]');
    if (citationButton) showEvidence(citationButton.dataset.e || citationButton.dataset.source);
    if (!event.target.closest('.coin-field')) closeSuggestions();
  });
  $('node-list').addEventListener('click', event => {
    const button = event.target.closest('[data-node]');
    if (button && graph?.cy) graph.selectNode(graph.cy.getElementById(button.dataset.node));
  });
  $('zoom-in').addEventListener('click', () => graph?.zoom(1.25));
  $('graph').addEventListener('graphzoom', syncViewport);
  $('zoom-out').addEventListener('click', () => graph?.zoom(.8));
  $('reset').addEventListener('click', () => { graph?.clear(); graph?.fit(); });
  $('copy-link').addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(location.href); $('copy-link').textContent = 'Link copied'; }
    catch { $('copy-link').textContent = 'Copy the address from your browser'; }
    setTimeout(() => { $('copy-link').textContent = 'Copy investigation link ↗'; }, 3000);
  });
  const parameters = new URLSearchParams(location.search);
  fetch('/static/snapshot.json').then(response => {
    if (!response.ok) throw new Error('Snapshot unavailable');
    return response.json();
  }).then(snapshot => {
    document.querySelector('.workspace-snapshot>span:last-child').textContent = 'Snapshot · ' + new Date(snapshot.recorded_through).toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' });
  }).catch(() => { document.querySelector('.workspace-snapshot>span:last-child').textContent = 'Snapshot date unavailable'; });
  const mint = parameters.get('mint'), question = parameters.get('q')?.slice(0, 500) || '';
  if (mint && MINT.test(mint)) {
    selectedMint = mint; $('coin').value = mint; $('q').value = question; investigate(mint, question, false);
  } else if (question) {
    resolveAndInvestigate(question, '', false);
  } else if (mint) {
    $('coin').value = mint; $('coin').setAttribute('aria-invalid', 'true');
    $('note').textContent = 'That address is not a valid Solana mint. Enter a coin name or a full mint address above.';
    $('note').className = 'note err';
  }
})();
