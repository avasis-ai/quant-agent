'use strict';
(() => {
  const $ = id => document.getElementById(id);
  const page = document.body.dataset.page;
  const NS = 'http://www.w3.org/2000/svg';
  function el(tag, text, cls) { const n = document.createElement(tag); if(text !== undefined) n.textContent = text; if(cls) n.className = cls; return n; }
  function svg(tag, attrs) { const n = document.createElementNS(NS,tag); Object.entries(attrs).forEach(([k,v])=>n.setAttribute(k,v)); return n; }
  function date(at) { return at ? new Date(at*1000).toLocaleString(undefined,{dateStyle:'medium',timeStyle:'short'}) : 'Time not recorded'; }
  function status(text, error=false) { $('status').textContent=text; $('status').classList.toggle('error',error); }
  function sourceLink(url,text) { const a=el('a',text); try { const u=new URL(url); if(u.protocol==='https:') { a.href=u.href; a.target='_blank'; a.rel='noopener noreferrer'; } } catch{} return a; }
  async function fetchJSON(url, options={}) { const r=await fetch(url,{...options,headers:{'content-type':'application/json',...(options.headers||{})}}); const out=await r.json(); if(!r.ok) throw new Error(out.error||out.detail||'The request failed.'); return out; }

  function showGraph(graph, sources=[]) {
    const container=$('graph'); container.replaceChildren();
    container.scrollTo(0, 0);
    $('detail').replaceChildren(el('h2',page==='brain'?'Source details':'Evidence details'),el('p',page==='brain'?'Select a node to inspect its source or relationship.':'Select a node to see its finding, source and time.','meta'));
    const nodes=graph?.nodes||[], edges=graph?.edges||[];
    if(!nodes.length) { container.append(el('p','No graph evidence found for this query.','graph-empty')); return; }
    const lanes=page==='brain' ? [['Product','Feature','Policy','Decision','Finding','Metric','Entity'],['Section'],['Doc']] : [['Session','Coin','Wallet','Entity'],['Question'],['Evidence'],['Note']];
    const columns=lanes.map(labels=>nodes.filter(n=>labels.includes(n.label)));
    const other=nodes.filter(n=>!lanes.flat().includes(n.label)); if(other.length) columns.push(other);
    const used=columns.filter(c=>c.length), width=Math.max(660,used.length*220), height=Math.max(500,Math.max(...used.map(c=>c.length))*68+60);
    const canvas=svg('svg',{viewBox:`0 0 ${width} ${height}`,role:'group','aria-label':page==='brain'?'Public company knowledge graph':'Investigation memory graph'});
    canvas.style.width=width+'px'; canvas.style.height=height+'px'; const positions=new Map();
    const defs=svg('defs',{}), marker=svg('marker',{id:'graph-arrow',viewBox:'0 0 10 10',refX:9,refY:5,markerWidth:7,markerHeight:7,orient:'auto-start-reverse'});
    marker.append(svg('path',{d:'M 0 0 L 10 5 L 0 10 z',class:'graph-arrow'}));defs.append(marker);canvas.append(defs);
    used.forEach((column,ci)=>column.forEach((n,ri)=>positions.set(n.key,{x:ci*(width/used.length)+20,y:35+ri*((height-50)/column.length)})));
    const lineEls=[];
    function boundary(a,b){const dx=b.x-a.x,dy=b.y-a.y;const t=Math.min(dx?90/Math.abs(dx):Infinity,dy?24/Math.abs(dy):Infinity);return {x:a.x+90+dx*t,y:a.y+24+dy*t};}
    edges.forEach(edge=>{const a=positions.get(edge.src),b=positions.get(edge.dst);if(!a||!b||edge.src===edge.dst)return;const start=boundary(a,b),end=boundary(b,a);const line=svg('line',{x1:start.x,y1:start.y,x2:end.x,y2:end.y,class:'graph-edge','marker-end':'url(#graph-arrow)'});canvas.append(line);const label=svg('text',{x:(a.x+b.x)/2+90,y:(a.y+b.y)/2+16,'text-anchor':'middle',class:'edge-label'});label.textContent=edge.type;canvas.append(label);lineEls.push({edge,line,label});});
    const nodeEls=[];
    function inspect(n,g) {
      nodeEls.forEach(x=>{const active=x.n.key===n.key;x.g.classList.toggle('selected',active);x.g.setAttribute('aria-pressed',String(active));});
      lineEls.forEach(({edge,line,label})=>{const active=edge.src===n.key||edge.dst===n.key;line.classList.toggle('selected',active);label.style.opacity=active?'1':'0';});
      const panel=$('detail');panel.replaceChildren(el('h2',n.label),el('p',n.name||n.key));
      if(n.tool)panel.append(el('p','Tool: '+n.tool,'meta'));
      if(n.at)panel.append(el('p',date(n.at),'meta'));
      if(n.url)panel.append(sourceLink(n.url,'Open public source'));
      const source=sources.find(s=>'section:'+s.section_id===n.key);
      if(source){panel.append(el('p',source.section_title,'meta'),el('p','Fetched '+date(source.fetched_at),'meta'));const a=el('a','Read ['+source.id+'] below');a.href='#source-'+source.id;panel.append(a);}
      const connected=edges.filter(e=>e.src===n.key||e.dst===n.key);
      if(connected.length)panel.append(el('p',connected.length+' graph relationship'+(connected.length===1?'':'s'),'meta'),el('p',[...new Set(connected.map(e=>e.type))].join(' · '),'meta'));
    }
    nodes.forEach(n=>{const p=positions.get(n.key);if(!p)return;const g=svg('g',{transform:`translate(${p.x},${p.y})`,class:'graph-node',tabindex:'0',role:'button','aria-label':n.label+': '+(n.name||n.key)});const title=svg('title',{});title.textContent=n.name||n.key;g.append(title,svg('rect',{x:0,y:0,width:180,height:48,rx:4}));const kind=svg('text',{x:10,y:15,class:'node-kind'});kind.textContent=n.label;const text=svg('text',{x:10,y:34});const label=n.name||n.key;text.textContent=label.length>24?label.slice(0,23)+'…':label;g.append(kind,text);g.addEventListener('click',()=>inspect(n,g));g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();inspect(n,g);}});nodeEls.push({n,g});canvas.append(g);});
    container.append(canvas);
  }

  function renderMemory(data) {
    showGraph(data.graph);
    const target=$('findings');target.replaceChildren();
    (data.rows||[]).forEach(row=>{const article=el('article',undefined,'finding');article.append(el('h3',row.tool||'Investigation'),el('p',row.summary||'No public evidence was recorded for this investigation.'),el('p',date(row.at||row.asked_at)+(row.sessions?' · '+row.sessions+' anonymous session'+(row.sessions===1?'':'s'):''),'meta'));if(row.id)article.append(el('p','Memory evidence: '+row.id,'meta'));target.append(article);});
    (data.notes||[]).forEach(note=>{const article=el('article',undefined,'finding');article.append(el('h3','Agent note: '+note.by),el('p',note.text),el('p',date(note.at)+' · Unverified; self-declared agent label','meta'));if(note.evidence_ids?.length)article.append(el('p','Source evidence: '+note.evidence_ids.join(', '),'meta'));target.append(article);});
    if(!target.children.length)target.append(el('p','No investigations or notes found yet.','meta'));
    $('result-note').textContent=data.note||'';
    status((data.rows||[]).length+' findings'+((data.notes||[]).length?' and '+data.notes.length+' agent note'+(data.notes.length===1?'':'s'):'')+' recalled.');
  }
  function renderBrain(data) {
    showGraph(data.graph,data.sources);
    const answer=$('answer');answer.replaceChildren();answer.classList.remove('hidden');
    data.answer.split(/\n\s*\n/).forEach(text=>{const p=el('p');let last=0;for(const m of text.matchAll(/\[(B\d+)\]/g)){p.append(document.createTextNode(text.slice(last,m.index)));const a=el('a','['+m[1]+']');a.href='#source-'+m[1];p.append(a);last=m.index+m[0].length;}p.append(document.createTextNode(text.slice(last)));answer.append(p);});
    const target=$('sources');target.replaceChildren();
    (data.sources||[]).forEach(source=>{const article=el('article',undefined,'source');article.id='source-'+source.id;article.append(sourceLink(source.url,'['+source.id+'] '+source.title),el('p',source.section_title+' · Fetched '+date(source.fetched_at),'meta'),el('blockquote',source.excerpt));const details=el('details');details.append(el('summary','Read the source section'),el('pre',source.text));article.append(details);target.append(article);});
    if(!target.children.length)target.append(el('p','No matching public sources found.','meta'));
    $('result-note').textContent=data.note||'';
    status((data.sources||[]).length+' public source sections retrieved. Answers are source excerpts.');
  }
  async function run(ownSession=false) {
    const submit=$('submit');submit.disabled=true;status('Reading the '+(page==='brain'?'company knowledge':'investigation memory')+' graph…');
    try {
      let data;
      if(page==='brain')data=await fetchJSON('/api/brain/ask',{method:'POST',body:JSON.stringify({question:$('query').value.trim()})});
      else { const q=$('query').value.trim();const params=new URLSearchParams();if(!ownSession&&q){const scope=$('scope').value;if(scope==='session')params.set('session',q);else params.set('entity',q.includes(':')?q:(scope==='wallet'?'wallet:':'coin:')+q);}data=await fetchJSON('/api/memory?'+params); }
      if(page==='brain')renderBrain(data);else renderMemory(data);
    } catch(error) {status(error.message,true);}finally{submit.disabled=false;}
  }
  $('query-form').addEventListener('submit',e=>{e.preventDefault();run();});
  document.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>{$('query').value=b.dataset.question;run();}));
  if(page==='memory') {
    $('my-session').addEventListener('click',()=>run(true));
    $('scope').addEventListener('change',()=>{$('query').placeholder=$('scope').value==='session'?'32-character random session token':'Paste a Solana address';});
    const params=new URLSearchParams(location.search);const entity=params.get('entity')||params.get('mint');const session=params.get('session');
    if(entity||session){$('query').value=entity||session;$('scope').value=session?'session':entity.startsWith('wallet:')?'wallet':'entity';run();}
  }
})();
