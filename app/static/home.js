(() => {
  'use strict';
  const visual = document.getElementById('hero-visual');
  const pause = document.getElementById('pause-graph');
  const traceButtons = [...document.querySelectorAll('[data-trace]')];
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  // Cache geometry once. Each frame only paints SVG attributes: no layout reads.
  const svg = visual.querySelector('.lineage-visual');
  const ns = 'http://www.w3.org/2000/svg';
  const clamp = value => Math.max(0, Math.min(1, value));
  const ease = value => value * value * (3 - 2 * value);
  const branches = [...svg.querySelectorAll('.aggregate-branches path')];
  const edges = [
    { path: svg.querySelector('.edge-creator'), start: 650, duration: 1150 },
    { path: svg.querySelector('.edge-funder'), start: 1950, duration: 1150 },
    ...branches.map((path, index) => ({ path, start: 3350 + index * 230, duration: 850 })),
    { path: svg.querySelector('.edge-hub'), start: 7550, duration: 1000 }
  ];
  const sparks = document.createElementNS(ns, 'g');
  sparks.setAttribute('class', 'graph-sparks');
  sparks.setAttribute('aria-hidden', 'true');
  svg.append(sparks);
  edges.forEach(edge => {
    edge.length = edge.path.getTotalLength();
    edge.path.classList.add('staged-edge');
    edge.path.style.strokeDasharray = String(edge.length);
    edge.particles = [0, 1, 2].map(index => {
      const dot = document.createElementNS(ns, 'circle');
      dot.setAttribute('r', index ? '1.6' : '3');
      sparks.append(dot);
      return dot;
    });
  });
  const nodes = [
    { element: svg.querySelector('.coin-node'), start: 0 },
    { element: svg.querySelector('.creator-node'), start: 1800 },
    { element: svg.querySelector('.funder-node'), start: 3100 },
    { element: svg.querySelector('.hub-node'), start: 8550 }
  ];
  // Match the schematic ring nodes to their incoming edge, including mid-path forks.
  svg.querySelectorAll('.aggregate-nodes > *').forEach(element => {
    const x = Number(element.getAttribute('cx') ?? element.getAttribute('x')) + (element.tagName === 'rect' ? Number(element.getAttribute('width')) / 2 : 0);
    const y = Number(element.getAttribute('cy') ?? element.getAttribute('y')) + (element.tagName === 'rect' ? Number(element.getAttribute('height')) / 2 : 0);
    let arrival = 7300;
    edges.slice(2, -1).forEach(edge => {
      for (let step = 0; step <= 60; step++) {
        const point = edge.path.getPointAtLength(edge.length * step / 60);
        if (Math.hypot(point.x - x, point.y - y) < 10) arrival = Math.min(arrival, edge.start + edge.duration * step / 60);
      }
    });
    nodes.push({ element, start: arrival });
  });
  let elapsed = 0, previous = null, frame = null, inView = false, manuallyPaused = false;
  const end = 9300;
  function paint(time) {
    edges.forEach(edge => {
      const progress = ease(clamp((time - edge.start) / edge.duration));
      edge.path.style.strokeDashoffset = String(edge.length * (1 - progress));
      edge.path.style.opacity = progress ? '1' : '0';
      edge.path.style.filter = progress > 0 && progress < 1 ? 'drop-shadow(0 0 3px rgba(255,109,41,.65))' : 'none';
      edge.particles.forEach((dot, index) => {
        const trail = progress - index * .045;
        const active = progress > 0 && progress < 1 && trail > 0;
        dot.style.opacity = active ? String(1 - index * .3) : '0';
        if (active) {
          const point = edge.path.getPointAtLength(edge.length * trail);
          dot.setAttribute('cx', point.x);
          dot.setAttribute('cy', point.y);
        }
      });
    });
    nodes.forEach(({ element, start }) => {
      const reached = ease(clamp((time - start) / 450));
      element.style.setProperty('--reached', reached);
      const halo = element.querySelector('.node-halo');
      if (halo) {
        const pulse = clamp((time - start) / 850);
        halo.style.opacity = String(reached * (.1 + .22 * Math.sin(pulse * Math.PI)));
        halo.setAttribute('transform', `translate(${halo.getAttribute('cx')} ${halo.getAttribute('cy')}) scale(${1 + .22 * Math.sin(pulse * Math.PI)}) translate(${-halo.getAttribute('cx')} ${-halo.getAttribute('cy')})`);
      }
    });
    svg.querySelectorAll('.svg-edge').forEach((label, index) => {
      label.style.opacity = String(ease(clamp((time - (index ? 1800 : 3100)) / 450)));
    });
    svg.querySelector('.ring-outline').style.opacity = String(.15 + .35 * ease(clamp((time - 3350) / 4000)));
    svg.querySelector('.graph-annotation').parentElement.style.opacity = String(ease(clamp((time - 7200) / 700)));
    visual.dataset.phase = time < 1800 ? '2' : time < 3100 ? '1' : '0';
    traceButtons.forEach(button => button.setAttribute('aria-pressed', String(Number(button.dataset.trace) === (time < 1800 ? 0 : time < 3100 ? 1 : 2))));
  }
  function tick(now) {
    if (previous !== null) elapsed = Math.min(end, elapsed + now - previous);
    previous = now;
    paint(elapsed);
    if (elapsed < end) frame = requestAnimationFrame(tick);
    else { frame = null; syncAnimation(); }
  }
  function syncAnimation() {
    cancelAnimationFrame(frame);
    frame = null;
    previous = null;
    const paused = manuallyPaused || motion.matches;
    pause.setAttribute('aria-pressed', String(paused));
    pause.disabled = motion.matches;
    pause.textContent = motion.matches ? 'Motion off' : elapsed >= end ? 'Replay' : paused ? 'Play' : 'Pause';
    visual.dataset.animation = motion.matches || elapsed >= end ? 'complete' : paused ? 'paused' : inView ? 'playing' : 'waiting';
    if (motion.matches) paint(end);
    else if (!paused && inView && !document.hidden && elapsed < end) frame = requestAnimationFrame(tick);
  }
  traceButtons.forEach(button => button.addEventListener('click', () => {
    manuallyPaused = true;
    elapsed = [600, 1900, 3300][Number(button.dataset.trace)];
    paint(elapsed);
    syncAnimation();
  }));
  pause.addEventListener('click', () => {
    if (elapsed >= end) { elapsed = 0; manuallyPaused = false; paint(0); }
    else manuallyPaused = !manuallyPaused;
    syncAnimation();
  });
  motion.addEventListener('change', () => { paint(motion.matches ? end : elapsed); syncAnimation(); });
  document.addEventListener('visibilitychange', syncAnimation);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => {
      inView = entries[0].isIntersecting;
      syncAnimation();
    }, { threshold: .3 }).observe(visual);
  } else inView = true;
  visual.classList.add('graph-staged');
  paint(motion.matches ? end : 0);
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

// Progressive enhancement: the story reads in full without JavaScript or motion.
(() => {
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  const sections = [...document.querySelectorAll('[data-reveal]')];
  const observer = 'IntersectionObserver' in window ? new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.remove('reveal-pending');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: .08 }) : null;
  if (observer && !motion.matches) sections.forEach(section => {
    section.classList.add('reveal-pending');
    observer.observe(section);
  });
  motion.addEventListener('change', () => {
    if (motion.matches) {
      observer?.disconnect();
      sections.forEach(section => section.classList.remove('reveal-pending'));
    }
  });
  document.querySelectorAll('.story-art img').forEach(img => {
    const ready = () => { if (img.naturalWidth) img.classList.add('is-ready'); };
    img.addEventListener('load', ready);
    img.addEventListener('error', () => img.classList.remove('is-ready'));
    ready();
  });

  const trigger = document.getElementById('watch-demo');
  const dialog = document.getElementById('demo-dialog');
  const player = document.getElementById('demo-player');
  if (!trigger || !dialog?.showModal || !player) return;
  trigger.addEventListener('click', event => {
    event.preventDefault();
    const frame = document.createElement('iframe');
    frame.src = 'https://www.youtube-nocookie.com/embed/fz89p-YZS6o?autoplay=1';
    frame.title = 'Sniff by QuantBase · Graph Hacks demo';
    frame.allow = 'autoplay; encrypted-media; picture-in-picture; fullscreen';
    player.replaceChildren(frame);
    dialog.showModal();
  });
  document.getElementById('close-demo').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => {
    if (event.target === dialog) {
      const bounds = dialog.getBoundingClientRect();
      if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) dialog.close();
    }
  });
  dialog.addEventListener('close', () => {
    player.replaceChildren();
    trigger.focus({ preventScroll: true });
  });
})();

(() => {
  const flow = document.getElementById('hero-flow');
  const button = document.getElementById('pause-flow');
  if (!flow || !button) return;
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  flow.querySelectorAll('.flow-trace-branch').forEach((path, index) => {
    path.style.animationDelay = `${index * .15}s`;
  });
  flow.querySelectorAll('.flow-node-branch .flow-node-light').forEach((node, index) => {
    node.style.animationDelay = `${index * .15}s`;
  });
  let paused = false;
  const sync = () => {
    const stop = paused || motion.matches || document.hidden;
    flow.dataset.flow = stop ? 'paused' : 'playing';
    button.textContent = motion.matches ? 'Motion off' : paused ? 'Play animation' : 'Pause animation';
    button.setAttribute('aria-pressed', String(paused || motion.matches));
    button.disabled = motion.matches;
  };
  button.addEventListener('click', () => { paused = !paused; sync(); });
  motion.addEventListener('change', sync);
  document.addEventListener('visibilitychange', sync);
  sync();
})();
