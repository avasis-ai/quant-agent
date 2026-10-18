(() => {
  'use strict';
  const visual = document.getElementById('hero-visual');
  const pause = document.getElementById('pause-graph');
  const traceButtons = [...document.querySelectorAll('[data-trace]')];
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let phase = 0, timer = null, manuallyPaused = false, inspecting = false;
  function setPhase(next) {
    phase = next;
    visual.dataset.phase = String(phase);
    traceButtons.forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.trace) === phase)));
  }
  function syncAnimation() {
    clearInterval(timer);
    const paused = manuallyPaused || motion.matches;
    pause.setAttribute('aria-pressed', String(paused));
    pause.disabled = motion.matches;
    pause.textContent = motion.matches ? 'Motion off' : paused ? 'Play' : 'Pause';
    if (!paused && !inspecting && !document.hidden) timer = setInterval(() => setPhase((phase + 1) % 3), 2400);
  }
  traceButtons.forEach(button => button.addEventListener('click', () => {
    manuallyPaused = true;
    setPhase(Number(button.dataset.trace));
    syncAnimation();
  }));
  pause.addEventListener('click', () => { manuallyPaused = !manuallyPaused; syncAnimation(); });
  motion.addEventListener('change', syncAnimation);
  visual.addEventListener('pointerenter', () => { inspecting = true; syncAnimation(); });
  visual.addEventListener('pointerleave', () => { inspecting = false; syncAnimation(); });
  visual.addEventListener('focusin', () => { inspecting = true; syncAnimation(); });
  visual.addEventListener('focusout', event => { if (!visual.contains(event.relatedTarget)) { inspecting = false; syncAnimation(); } });
  document.addEventListener('visibilitychange', syncAnimation);
  syncAnimation();

  // Snapshot metrics have a single source. Keep unavailable distinct from zero.
  fetch('/static/snapshot.json').then(response => {
    if (!response.ok) throw new Error('Snapshot unavailable');
    return response.json();
  }).then(snapshot => {
    document.querySelectorAll('[data-stat]').forEach(element => {
      const key = element.dataset.stat;
      element.textContent = key === 'links' ? (snapshot.links / 1e6).toFixed(1) + 'M' : snapshot[key].toLocaleString('en-US');
      if (key === 'links') element.title = snapshot.links.toLocaleString('en-US') + ' relationships';
    });
    const date = new Date(snapshot.recorded_through);
    document.getElementById('snapshot-date').textContent = 'Snapshot recorded through ' + date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' }) + ', ' + date.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', timeZone: 'UTC' }) + ' UTC.';
  }).catch(() => {
    document.querySelectorAll('[data-stat]').forEach(element => { element.textContent = 'Unavailable'; });
    document.getElementById('snapshot-date').textContent = 'Snapshot figures are unavailable. See the graph model on GitHub.';
  });

  document.querySelectorAll('[data-copy]').forEach(button => {
    button.addEventListener('click', async () => {
      const value = document.getElementById(button.dataset.copy).textContent;
      try {
        await navigator.clipboard.writeText(value);
        button.textContent = 'Copied';
      } catch {
        button.textContent = 'Select and copy the command above';
      }
      setTimeout(() => { button.textContent = 'Copy command'; }, 3000);
    });
  });
})();
