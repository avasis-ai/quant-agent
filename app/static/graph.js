/* Shared evidence renderer. Graph objects come only from the read-only tools. */
(() => {
  'use strict';
  const short = value => value && value.length > 14 ? `${value.slice(0, 4)}…${value.slice(-4)}` : (value || '');
  const cut = (value, max = 26) => value.length > max ? value.slice(0, max - 1) + '…' : value;
  const kinds = { Coin: 'coin', Wallet: 'wallet', Hub: 'hub', Handle: 'handle', Ring: 'ring',
    Doc: 'doc', Section: 'section', Product: 'entity', Feature: 'entity', Policy: 'entity',
    Decision: 'entity', Finding: 'entity', Metric: 'entity', Entity: 'entity' };
  const reduced = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  class SniffGraph {
    constructor(container, onSelect = () => {}) {
      this.container = container;
      this.onSelect = onSelect;
      this.evidence = [];
      this.nodes = new Map();
      if (!window.cytoscape) {
        container.innerHTML = '<p class="graph-unavailable">The graph renderer could not load. You can still read the evidence and answer.</p>';
        return;
      }
      this.cy = cytoscape({
        container, minZoom: .02, maxZoom: 1.2,
        boxSelectionEnabled: false, selectionType: 'single',
        style: [
          { selector: 'node', style: {
            label: 'data(label)', color: '#e8e4e2', 'font-family': 'Host Grotesk, sans-serif', 'font-size': 12,
            'font-weight': 400, 'text-valign': 'bottom', 'text-margin-y': 10,
            'text-wrap': 'wrap', 'text-max-width': 150, 'text-outline-width': 3, 'text-outline-color': '#191619',
            'background-color': '#342a29', 'border-width': 1.5, 'border-color': '#a99a94', width: 28, height: 28,
            'overlay-opacity': 0,
          } },
          { selector: 'node[kind="coin"]', style: {
            shape: 'round-rectangle', 'background-color': '#3d2821', 'border-color': '#ffac83', width: 32, height: 32,
            'background-image': 'data(image)', 'background-width': '75%', 'background-height': '75%',
          } },
          { selector: 'node[kind="coin"][grad="yes"]', style: { 'background-color': '#24362b', 'border-color': '#91c9a5' } },
          { selector: 'node[kind="hub"]', style: {
            shape: 'hexagon', 'background-color': '#272326', 'border-style': 'dashed', 'border-color': '#aaa09d',
            width: 38, height: 38, color: '#bababa',
          } },
          { selector: 'node[kind="handle"]', style: { shape: 'diamond', width: 34, height: 34, 'background-color': '#322a2d' } },
          { selector: 'node[kind="ring"]', style: {
            shape: 'ellipse', width: 48, height: 48, 'border-width': 5, 'border-color': '#9e6448',
            'background-color': '#241c1b', 'background-opacity': .8,
          } },
          { selector: 'node[kind="group"]', style: {
            shape: 'round-rectangle', width: 58, height: 38, 'border-style': 'dotted',
            'background-color': '#2b2526', 'border-color': '#a99a94',
          } },
          { selector: 'node[kind="doc"], node[kind="section"]', style: {
            shape: 'round-rectangle', width: 38, height: 30, 'border-color': '#ffac83',
          } },
          { selector: 'node.focus', style: {
            width: 42, height: 42, 'border-width': 2, 'border-color': '#ff6d29',
            'background-color': '#67311e', 'font-size': 14, 'font-weight': 600, color: '#ffffff',
            'underlay-color': '#ff6d29', 'underlay-padding': 12, 'underlay-opacity': .07, 'underlay-shape': 'ellipse',
          } },
          { selector: 'edge', style: {
            width: 1.3, 'line-color': '#72605a', 'target-arrow-color': '#72605a',
            'target-arrow-shape': 'triangle', 'arrow-scale': .75, 'curve-style': 'bezier',
            label: 'data(label)', 'font-size': 10, 'font-family': 'Geist Mono, monospace', color: '#bababa',
            'text-rotation': 'autorotate', 'text-background-color': '#191619',
            'text-background-opacity': 1, 'text-background-padding': 4, 'text-margin-y': -3,
            'overlay-opacity': 0,
          } },
          { selector: 'edge[type="FUNDED"]', style: { 'line-color': '#aa7a63', 'target-arrow-color': '#aa7a63', width: 1.8 } },
          { selector: 'edge[type="LINKS"], edge[type="SHARED"]', style: { 'line-style': 'dashed', 'target-arrow-shape': 'none' } },
          { selector: 'edge[type="IN_RING"]', style: { 'line-style': 'dotted', 'target-arrow-shape': 'none', 'line-color': '#9e6448' } },
          { selector: 'edge.hub-edge', style: { 'line-style': 'dashed' } },
          { selector: '.dim', style: { opacity: .13 } },
          { selector: 'node.hi', style: {
            'border-color': '#ff9a6b', 'border-width': 2.5, color: '#ffffff', 'z-index': 10,
            'underlay-color': '#ff6d29', 'underlay-padding': 12, 'underlay-opacity': .12, 'underlay-shape': 'ellipse',
          } },
          { selector: 'edge.hi', style: {
            'line-color': '#ff9a6b', 'target-arrow-color': '#ff9a6b', width: 2.5,
            color: '#ffcfb6', 'z-index': 10, 'underlay-color': '#ff6d29', 'underlay-padding': 4, 'underlay-opacity': .08,
          } },
        ],
      });
      this.cy.on('tap', 'node', event => this.selectNode(event.target));
      this.cy.on('tap', event => { if (event.target === this.cy) this.clear(); });
      this.cy.on('mouseover', 'node', () => { container.style.cursor = 'pointer'; });
      this.cy.on('mouseout', 'node', () => { container.style.cursor = 'grab'; });
      this.cy.on('zoom', () => container.dispatchEvent(new CustomEvent('graphzoom', { detail: this.cy.zoom() })));
      container.addEventListener('keydown', event => {
        const moves = { ArrowLeft: [40, 0], ArrowRight: [-40, 0], ArrowUp: [0, 40], ArrowDown: [0, -40] };
        if (moves[event.key]) { event.preventDefault(); const [x, y] = moves[event.key]; this.cy.panBy({ x, y }); }
        if (event.key === '+' || event.key === '=') { event.preventDefault(); this.zoom(1.25); }
        if (event.key === '-') { event.preventDefault(); this.zoom(.8); }
      });
      this.observer = new ResizeObserver(() => {
        this.cy.resize();
        if (this.cy.nodes().length && !this.active) this.arrange(false);
      });
      this.observer.observe(container);
    }

    label(node) {
      if (node.label === 'Coin') return cut(node.name || short(node.mint));
      if (node.label === 'Hub') return `Hub · dead end\n${short(node.addr)}`;
      if (node.label === 'Handle') return cut(`${node.platform === 'twitter' ? 'X' : (node.platform || 'Social')} · ${node.handle || ''}`);
      if (node.label === 'Ring') return `Funding ring\n${node.creators ?? '?'} creators`;
      if (['doc', 'section', 'entity'].includes(kinds[node.label])) return cut(node.name || node.key);
      return short(node.addr || node.key);
    }

    setEvidence(items, focusKey, extraGraph = null) {
      this.evidence = items || [];
      if (!this.cy) return;
      this.layout?.stop();
      const data = new Map(), edges = new Map();
      this.nodes.clear();
      const addNode = (node, eid) => {
        if (!node.key) return;
        const merged = { ...this.nodes.get(node.key), ...Object.fromEntries(Object.entries(node).filter(([, v]) => v != null)) };
        this.nodes.set(node.key, merged);
        const previous = data.get(node.key);
        data.set(node.key, {
          id: node.key, kind: node._kind || kinds[merged.label] || 'wallet',
          label: node._label || this.label(merged), grad: merged.graduated ? 'yes' : 'no',
          image: merged.label === 'Coin' ? 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(`<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32"><text x="16" y="22" text-anchor="middle" fill="#ffcfb6" font-size="19" font-family="Arial">${(merged.symbol || merged.name || 'C').charAt(0).replace(/[<>&"']/g, '')}</text></svg>`) : 'none',
          ev: [...(previous?.ev || []), eid],
        });
      };
      const addEdge = (edge, eid) => {
        const id = `${edge.type}|${edge.src}|${edge.dst}`;
        let label = edge.label || '';
        if (extraGraph && !label) label = edge.type;
        if (edge.type === 'FUNDED' && !label) label = edge.sol != null ? `${Number(edge.sol).toFixed(3)} SOL` : 'funded';
        if (edge.type === 'CREATED') label = 'created';
        if (edge.type === 'LINKS') label = 'uses';
        edges.set(id, { id, source: edge.src, target: edge.dst, type: edge.type, label, ev: [...(edges.get(id)?.ev || []), eid] });
      };
      for (const item of this.evidence) {
        // A negative lookup includes the requested mint as an evidence anchor.
        // It is not a recorded Coin and must not be drawn as one.
        if (item.tool === 'coin_dossier' && /coin is not in the graph/i.test(item.summary)) continue;
        for (const node of item.nodes || []) addNode(node, item.id);
        for (const edge of item.edges || []) addEdge(edge, item.id);
        // The siblings tool returns an aggregate, not individual wallet edges.
        // Its separate group node is explicitly labelled as an aggregate.
        if (item.tool === 'siblings' && item.nodes?.length >= 2) {
          const match = /paid (\d+) other creators: (\d+) coins, (\d+) graduated/.exec(item.summary);
          if (match) {
            const funder = item.nodes[0];
            const key = `group:${funder.key}`;
            addNode({ key, label: 'Group', _kind: 'group', _label: `${match[1]} other creators\n${match[2]} coins · aggregate` }, item.id);
            addEdge({ type: 'FUNDED', src: funder.key, dst: key, label: 'also funded' }, item.id);
          }
        }
        if (item.tool === 'shared_snipers' && item.nodes?.length >= 2 && !item.edges?.length) {
          addEdge({ type: 'SHARED', src: item.nodes[0].key, dst: item.nodes[1].key, label: 'shared early buyers' }, item.id);
        }
      }
      // The brain verdict includes the complete retrieved neighbourhood, beyond
      // the section/document pair in each individual citation's evidence.
      for (const node of extraGraph?.nodes || []) addNode(node, node.citation || null);
      for (const edge of extraGraph?.edges || []) {
        const source = this.evidence.find(item => item.nodes?.some(node => node.key === edge.src));
        addEdge(edge, source?.id || null);
      }
      const elements = [...data.values()].map(node => ({ data: node, classes: node.id === focusKey ? 'focus' : '' }));
      for (const edge of edges.values()) {
        if (data.has(edge.source) && data.has(edge.target)) elements.push({ data: edge, classes: data.get(edge.source).kind === 'hub' ? 'hub-edge' : '' });
      }
      for (const node of elements.filter(element => element.data.kind === 'wallet')) {
        const outgoing = [...edges.values()].filter(edge => edge.source === node.data.id);
        const role = outgoing.some(edge => edge.type === 'CREATED') ? 'Creator' : outgoing.some(edge => edge.type === 'FUNDED') ? 'Funder' : 'Wallet';
        node.data.label = role + '\n' + node.data.label;
      }
      this.cy.batch(() => {
        this.cy.elements().remove();
        this.cy.add(elements);
        this.cy.nodes().forEach((node, index) => {
          const angle = index * 2.399963;
          node.position({ x: Math.cos(angle) * (100 + index * 12), y: Math.sin(angle) * (100 + index * 12) });
        });
      });
      this.active = null;
      this.cy.resize();
      this.arrange();
    }

    arrange(animate = true) {
      if (!this.cy?.nodes().length) return;
      this.layout?.stop();
      const primary = new Set();
      const focus = this.cy.nodes('.focus');
      const ancestors = focus.toArray();
      while (ancestors.length) {
        const node = ancestors.shift();
        if (primary.has(node.id())) continue;
        primary.add(node.id());
        node.incomers('edge[type="FUNDED"], edge[type="CREATED"]').sources().forEach(parent => ancestors.push(parent));
      }
      let roots = this.cy.nodes().filter(node => node.incomers('edge').empty()).toArray();
      if (!roots.length) roots = [focus[0] || this.cy.nodes().sort((a, b) => b.degree() - a.degree())[0]];
      const ranks = new Map(roots.map(node => [node.id(), 0])), queue = [...roots];
      while (queue.length) {
        const node = queue.shift();
        node.outgoers('edge').targets().forEach(child => {
          if (ranks.has(child.id())) return;
          ranks.set(child.id(), ranks.get(node.id()) + 1); queue.push(child);
        });
      }
      const columns = new Map();
      this.cy.nodes().forEach(node => {
        const rank = ranks.get(node.id()) ?? 0;
        if (!columns.has(rank)) columns.set(rank, []);
        columns.get(rank).push(node);
      });
      const vertical = this.container.clientWidth < 540;
      const positions = new Map();
      for (const [rank, nodes] of columns) {
        nodes.sort((a, b) => Number(primary.has(b.id())) - Number(primary.has(a.id())) || b.degree() - a.degree() || a.id().localeCompare(b.id()));
        nodes.forEach((node, index) => {
          const offset = index === 0 ? 0 : Math.ceil(index / 2) * (index % 2 ? -1 : 1) * 100;
          const depth = rank * (vertical ? 150 : 200);
          positions.set(node.id(), vertical ? { x: offset, y: depth } : { x: depth, y: offset });
        });
      }
      // Explicit, deterministic columns keep short evidence paths readable.
      // Using label-aware automatic breadth-first spacing made small graphs tiny.
      this.layout = this.cy.layout({ name: 'preset', positions: node => positions.get(node.id()),
        fit: true, padding: vertical ? 30 : 48, animate: animate && !reduced(),
        animationDuration: 500, animationEasing: 'ease-out-cubic',
        // Final label bounds are available after the nodes finish moving.
        // Fit again so initial load and container resizes include every label.
        stop: () => this.cy.fit(undefined, 52) });
      this.layout.run();
    }

    highlight(id, move = true) {
      const item = this.evidence.find(item => item.id === id);
      if (!item || !this.cy) return;
      this.active = id;
      const selection = this.cy.elements().filter(element => (element.data('ev') || []).includes(id));
      this.cy.elements().removeClass('hi').addClass('dim');
      selection.removeClass('dim').addClass('hi');
      selection.connectedNodes().removeClass('dim');
      if (move && selection.length) {
        this.cy.stop();
        this.cy.animate({ fit: { eles: selection.union(selection.connectedNodes()), padding: 90 } }, { duration: reduced() ? 0 : 300 });
      }
      this.onSelect({ type: 'evidence', id, item });
    }

    selectNode(node) {
      this.active = node.id();
      this.cy.elements().removeClass('dim hi');
      node.addClass('hi');
      this.onSelect({ type: 'node', id: node.id(), node: this.nodes.get(node.id()) || {}, kind: node.data('kind'), label: node.data('label') });
    }

    clear() {
      if (!this.cy) return;
      this.active = null;
      this.cy.elements().removeClass('dim hi');
      this.onSelect({ type: 'clear' });
    }

    fit(animate = true) {
      if (!this.cy || !this.cy.nodes().length) return;
      this.cy.stop();
      if (animate && !reduced()) this.cy.animate({ fit: { padding: 52 } }, { duration: 300 });
      else this.cy.fit(undefined, 52);
    }

    zoom(factor) {
      if (!this.cy) return;
      this.cy.zoom({ level: this.cy.zoom() * factor, renderedPosition: { x: this.cy.width() / 2, y: this.cy.height() / 2 } });
    }
  }
  window.SniffGraph = SniffGraph;
})();
