(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const KEY = 'sniff.claudeKey';
  const storage = {
    get() { try { return sessionStorage.getItem(KEY) || ''; } catch { return ''; } },
    set(key) { try { sessionStorage.setItem(KEY, key); return true; } catch { return false; } },
    clear() { try { sessionStorage.removeItem(KEY); } catch {} },
  };
  let status = { admin: false, owner: { active: false } }, statusAvailable = false;
  const message = (id, text, state = '') => { $(id).textContent = text; $(id).className = 'msg ' + state; };
  const busy = (id, value, label) => {
    $(id).disabled = value;
    $(id).setAttribute('aria-busy', String(value));
    $(id).textContent = value ? 'Checking…' : label;
  };
  function stateText(id, title, detail) {
    const strong = document.createElement('b'), meta = document.createElement('span');
    strong.textContent = title; meta.className = 'meta'; meta.textContent = detail;
    $(id).replaceChildren(strong, meta);
  }
  async function call(path, { method = 'GET', body, key } = {}) {
    const headers = { 'content-type': 'application/json' };
    if (key) headers['x-anthropic-key'] = key;
    const response = await fetch(path, { method, headers, credentials: 'same-origin', ...(body ? { body: JSON.stringify(body) } : {}) });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || 'The request failed. Please try again.');
    return result;
  }
  function renderVisitor() {
    const mine = storage.get();
    $('youState').classList.toggle('on', Boolean(mine || status.owner.active));
    if (mine) stateText('youText', 'Using your key', '…' + mine.slice(-4) + ' · this tab session only');
    else if (status.owner.active) stateText('youText', 'Using Sniff’s shared key', (status.owner.model || 'Claude') + ' · shared hourly allowance');
    else if (statusAvailable) stateText('youText', 'Fixed dossier available', 'Add a key for answers written by Claude.');
    else stateText('youText', 'Connection status unavailable', 'You can still validate your own key below.');
    $('youForm').classList.toggle('hidden', Boolean(mine));
    $('youActions').classList.toggle('hidden', !mine);
  }
  function renderOwner() {
    const owner = status.owner;
    $('lock').classList.toggle('hidden', status.admin);
    $('manage').classList.toggle('hidden', !status.admin);
    $('ownState').classList.toggle('on', Boolean(owner.active));
    stateText('ownText', owner.active ? 'Active · ' + (owner.last4 || '') : 'No shared key', owner.active ? (owner.model || 'Claude') : 'Visitors can use a fixed dossier or their own key.');
    $('ownRemove').classList.toggle('hidden', !owner.active);
    $('ownTest').classList.toggle('hidden', !owner.active);
    $('ownSave').textContent = owner.active ? 'Replace key' : 'Activate key';
    if (status.admin) {
      $('owner').classList.remove('hidden'); $('ownerOpen').classList.add('hidden');
      $('ownerOpen').setAttribute('aria-expanded', 'true');
    }
  }
  async function refresh() {
    try { status = await call('/api/settings/status'); statusAvailable = true; }
    catch (error) { statusAvailable = false; message('youMsg', error.message, 'err'); }
    renderVisitor(); renderOwner();
  }
  $('youSave').addEventListener('click', async () => {
    const key = $('youKey').value.trim();
    if (!key) { message('youMsg', 'Enter your Anthropic API key first.', 'err'); $('youKey').focus(); return; }
    busy('youSave', true, 'Use my key');
    $('youKey').removeAttribute('aria-invalid');
    try {
      const result = await call('/api/settings/visitor-check', { method: 'POST', key });
      if (!storage.set(key)) throw new Error('This browser blocked tab storage. Allow session storage and try again.');
      $('youKey').value = '';
      message('youMsg', 'Your key works. Sniff will use ' + result.model + '.', 'ok');
    } catch (error) { $('youKey').setAttribute('aria-invalid', 'true'); message('youMsg', error.message, 'err'); }
    busy('youSave', false, 'Use my key'); renderVisitor();
  });
  $('youKey').addEventListener('keydown', event => { if (event.key === 'Enter') $('youSave').click(); });
  $('youForget').addEventListener('click', () => { storage.clear(); message('youMsg', 'Your key was removed from this tab.'); renderVisitor(); });
  $('youTest').addEventListener('click', async () => {
    busy('youTest', true, 'Test connection');
    try { const result = await call('/api/ai/ping', { method: 'POST', key: storage.get() }); message('youMsg', `${result.reply} (${result.model})`, 'ok'); }
    catch (error) { message('youMsg', error.message, 'err'); }
    busy('youTest', false, 'Test connection');
  });
  $('ownerOpen').addEventListener('click', () => {
    $('owner').classList.remove('hidden'); $('ownerOpen').classList.add('hidden');
    $('ownerOpen').setAttribute('aria-expanded', 'true'); $('pass').focus();
  });
  $('unlock').addEventListener('click', async () => {
    const passcode = $('pass').value;
    if (!passcode) { message('ownMsg', 'Enter the owner passcode first.', 'err'); $('pass').focus(); return; }
    busy('unlock', true, 'Unlock settings');
    try {
      await call('/api/settings/login', { method: 'POST', body: { passcode } });
      $('pass').value = ''; message('ownMsg', ''); await refresh();
    } catch (error) { message('ownMsg', error.message, 'err'); }
    busy('unlock', false, 'Unlock settings');
  });
  $('pass').addEventListener('keydown', event => { if (event.key === 'Enter') $('unlock').click(); });
  $('ownSave').addEventListener('click', async () => {
    const key = $('ownKey').value.trim();
    if (!key) { message('ownMsg', 'Enter an Anthropic API key first.', 'err'); $('ownKey').focus(); return; }
    busy('ownSave', true, 'Activate key');
    try {
      const result = await call('/api/settings/owner-key', { method: 'POST', body: { key } });
      $('ownKey').value = ''; status.owner = result.owner;
      message('ownMsg', 'Shared key activated. Visitors will use ' + result.owner.model + '.', 'ok');
    } catch (error) { message('ownMsg', error.message, 'err'); }
    busy('ownSave', false, 'Activate key'); renderOwner(); renderVisitor();
  });
  $('ownKey').addEventListener('keydown', event => { if (event.key === 'Enter') $('ownSave').click(); });
  $('ownRemove').addEventListener('click', async () => {
    busy('ownRemove', true, 'Remove key');
    try { const result = await call('/api/settings/owner-key', { method: 'DELETE' }); status.owner = result.owner; message('ownMsg', 'Shared key removed from the server.'); }
    catch (error) { message('ownMsg', error.message, 'err'); }
    busy('ownRemove', false, 'Remove key'); renderOwner(); renderVisitor();
  });
  $('ownTest').addEventListener('click', async () => {
    busy('ownTest', true, 'Test connection');
    try { const result = await call('/api/ai/ping', { method: 'POST' }); message('ownMsg', `${result.reply} (${result.model})`, 'ok'); }
    catch (error) { message('ownMsg', error.message, 'err'); }
    busy('ownTest', false, 'Test connection');
  });
  $('logout').addEventListener('click', async () => {
    busy('logout', true, 'Lock settings');
    try { await call('/api/settings/logout', { method: 'POST' }); status.admin = false; renderOwner(); message('ownMsg', 'Settings locked.'); $('pass').focus(); }
    catch (error) { message('ownMsg', error.message, 'err'); }
    busy('logout', false, 'Lock settings');
  });
  refresh();
})();
