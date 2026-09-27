/* Personal News. The UI is stable; editions are plain, versioned JSON. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const storeKey = 'personal-news.v1';
  const fallback = {version:1,theme:'auto',compact:false,images:true,read:[],saved:[]};
  const allowedTheme = ['auto','light','dark'];
  const normalize = s => String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
  const validId = s => typeof s === 'string' && /^[a-z0-9][a-z0-9-]{0,159}$/.test(s);
  const datePattern = /^\d{4}-\d{2}-\d{2}$/;
  const editionKey = e => e.id || e.edition_id || e.date;
  function cleanPrefs(p) {
    if (!p || p.version !== 1 || !allowedTheme.includes(p.theme) || typeof p.compact !== 'boolean' || typeof p.images !== 'boolean') throw Error('Formato preferenze non valido.');
    for (const key of ['read','saved']) if (!Array.isArray(p[key]) || p[key].length > 20000 || !p[key].every(validId)) throw Error('Elenco preferenze non valido.');
    return {version:1,theme:p.theme,compact:p.compact,images:p.images,read:[...new Set(p.read)],saved:[...new Set(p.saved)]};
  }
  let prefs;
  try { prefs = cleanPrefs(JSON.parse(localStorage.getItem(storeKey))); } catch { prefs = {...fallback}; }
  const state = {manifest:null,categories:[],day:null,date:null,mode:'edition',category:'all',q:'',unread:false,saved:false,limit:24,read:new Set(prefs.read),bookmarks:new Set(prefs.saved),cache:new Map(),search:null,searchPromise:null,route:0,render:0,visible:[]};
  let toastTimer, storageWarned = false;
  function toast(message) { $('toast').textContent = message; $('toast').hidden = false; clearTimeout(toastTimer); toastTimer = setTimeout(() => $('toast').hidden = true,4200); }
  function persist() {
    prefs.read = [...state.read]; prefs.saved = [...state.bookmarks];
    try { localStorage.setItem(storeKey,JSON.stringify(prefs)); }
    catch { if (!storageWarned) {storageWarned = true;toast('Salvataggio locale non disponibile: le scelte restano solo in questa sessione.');} }
  }
  function node(tag,cls,text) { const n = document.createElement(tag); if (cls) n.className = cls; if (text !== undefined) n.textContent = text; return n; }
  function https(url) { try { const u = new URL(url); return u.protocol === 'https:' && !u.username && !u.password ? u.href : null; } catch { return null; } }
  function link(url,text,cls) { const n = node('a',cls,text); const safe = https(url); if (safe) n.href = safe; n.target = '_blank';n.rel = 'noopener noreferrer';return n; }
  function fmt(date,options={day:'numeric',month:'long'}) { return new Intl.DateTimeFormat('it-IT',{...options,timeZone:'Europe/Rome'}).format(new Date(/^\d{4}-\d{2}-\d{2}(-initial)?$/.test(date) ? `${date.slice(0,10)}T12:00:00+02:00` : date)); }
  function today() { return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Rome',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date()); }
  function category(id) { return state.categories.find(c=>c.id===id) || {id,label:id,symbol:'↗'}; }
  function color(n,id) { if (state.categories.some(c=>c.id===id)) n.style.setProperty('--cat',`var(--${id})`); }
  async function fetchJson(path) {
    if (location.protocol === 'file:') throw Error('Apri il sito con un server locale: python -m http.server 8000 --directory docs. Poi visita http://localhost:8000.');
    const response = await fetch(path,{cache:'no-store',credentials:'same-origin'});
    if (!response.ok) throw Error(`Impossibile caricare ${path} (HTTP ${response.status}). Riprova dopo aver verificato la connessione.`);
    try {return await response.json();} catch {throw Error(`Il file ${path} non contiene JSON valido.`);}
  }
  function checkManifest(m) {
    if (!m || m.version !== 1 || !Array.isArray(m.editions)) throw Error('Indice delle edizioni non valido.');
    const keys = m.editions.map(editionKey);
    if (new Set(keys).size !== keys.length || !m.editions.every(e=>datePattern.test(e.date))) throw Error('Date non valide nell’indice.');
    for (const e of m.editions) {
      const initial = e.kind === 'bootstrap' && editionKey(e) === `${e.date}-initial`;
      if (editionKey(e) !== e.date && !initial) throw Error('Identificatore edizione non valido.');
      if (e.path !== `data/${initial?'initial':'daily'}/${e.date}.json`) throw Error('Percorso edizione non valido.');
    }
    m.editions.sort((a,b)=>(b.generated_at||b.date).localeCompare(a.generated_at||a.date));
    if (keys.length && m.latest !== editionKey(m.editions[0])) throw Error('L’ultima edizione non coincide con l’indice.');
    return m;
  }
  function getDay(date) {
    if (!state.cache.has(date)) {
      const entry = state.manifest.editions.find(e=>editionKey(e)===date);
      if (!entry) return Promise.reject(Error('Edizione non presente nell’archivio.'));
      const promise = fetchJson(entry.path).then(d=>{
        if (d.version!==1 || d.date!==entry.date || editionKey(d)!==date || !Array.isArray(d.items) || !d.items.every(i=>validId(i.id)&&validId(i.event_id)&&Array.isArray(i.sources)&&i.sources.length)) throw Error('Dati dell’edizione non validi.');
        return d;
      }).catch(e=>{state.cache.delete(date);throw e;});
      state.cache.set(date,promise);
    }
    return state.cache.get(date);
  }
  function getSearch() {
    if (!state.searchPromise) state.searchPromise = fetchJson('data/search.json').then(d=>{
      if (d.version!==1 || !Array.isArray(d.items)) throw Error('Indice di ricerca non valido.');
      state.search=d.items;return d.items;
    }).catch(e=>{state.searchPromise=null;throw e;});
    return state.searchPromise;
  }
  function applyPrefs() {
    const dark = prefs.theme === 'dark' || (prefs.theme === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches);
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    document.querySelector('meta[name="theme-color"]').content = dark ? '#10171c' : '#f5f6f8';
    document.body.classList.toggle('compact',prefs.compact);document.body.classList.toggle('no-images',!prefs.images);
    $('density').setAttribute('aria-pressed',String(prefs.compact));$('theme-select').value = prefs.theme;$('images').checked=prefs.images;
    $('theme').title = `Tema: ${prefs.theme === 'auto' ? 'automatico' : dark ? 'scuro' : 'chiaro'}. Cambia tema`;
    $('theme').setAttribute('aria-label',$('theme').title);
  }
  function error(message) { $('error').textContent=message;$('error').hidden=false; }
  function clearFilters() {state.category='all';state.q='';state.unread=false;state.saved=false;state.limit=24;$('search').value='';}
  function syncControls() {
    $('scope').value=state.mode;$('search').value=state.q;
    $('unread').setAttribute('aria-pressed',String(state.unread));$('saved').setAttribute('aria-pressed',String(state.saved));
    $('saved-total').textContent=state.bookmarks.size;
    for (const [id,active] of [['nav-latest',state.mode==='edition' && state.date===state.manifest.latest],['nav-saved',state.saved],['mobile-latest',state.mode==='edition' && state.date===state.manifest.latest],['mobile-saved',state.saved]]) $(id).classList.toggle('active',active);
  }
  function writeURL(replace=true) {
    const u=new URL(location.href);u.search='';
    if (state.date !== state.manifest.latest) u.searchParams.set('date',state.date);
    if (state.mode==='archive') u.searchParams.set('scope','archive');
    if (state.q) u.searchParams.set('q',state.q);
    if (state.category!=='all') u.searchParams.set('category',state.category);
    if (state.saved) u.searchParams.set('saved','1');
    if (state.unread) u.searchParams.set('unread','1');
    history[replace?'replaceState':'pushState']({},'',u);
  }
  async function navigate(date,{url=true,reset=true}={}) {
    const ticket=++state.route;++state.render;state.visible=[];$('cards').setAttribute('aria-busy','true');
    try {
      const day=await getDay(date);if(ticket!==state.route)return;
      state.day=day;state.date=date;if(reset){clearFilters();state.mode='edition';}
      $('error').hidden=true;if(url){const u=new URL(location.href);u.hash='';history.pushState({},'',u);writeURL(true);}
      renderHeader();renderCategories();syncControls();renderHighlights();await renderCards();
      if(url)window.scrollTo({top:0,behavior:'instant'});
      const target=location.hash.slice(1);if(validId(target))requestAnimationFrame(()=>document.getElementById(target)?.scrollIntoView({block:'center'}));
    } catch(e) {if(ticket===state.route){error(e.message);$('cards').setAttribute('aria-busy','false');}}
  }
  async function readRoute() {
    const u=new URL(location.href);const requested=u.searchParams.get('date');
    const known=state.manifest.editions.some(e=>editionKey(e)===requested);
    state.mode=u.searchParams.get('scope')==='archive'?'archive':'edition';state.q=u.searchParams.get('q')||'';
    state.category=state.categories.some(c=>c.id===u.searchParams.get('category'))?u.searchParams.get('category'):'all';
    state.saved=u.searchParams.get('saved')==='1';state.unread=u.searchParams.get('unread')==='1';state.limit=24;
    let target = known?requested:state.manifest.latest;
    const article = u.hash.slice(1);
    if (validId(article)) {
      const selected = await getDay(target);
      if (!selected.items.some(i=>i.id===article)) {
        const indexed = (await getSearch()).find(i=>i.id===article);
        if (indexed) target=indexed.edition;
      }
    }
    await navigate(target,{url:false,reset:false});
    if(requested&&!known)toast('Questa data non è in archivio: è stata aperta l’ultima edizione.');
  }
  function renderHeader() {
    const d=state.day, all=state.manifest.editions, i=all.findIndex(e=>editionKey(e)===state.date), isLatest=state.date===state.manifest.latest;
    $('date-label').textContent=fmt(d.date,{day:'numeric',month:'long',year:'numeric'})+(d.kind==='bootstrap'?' · iniziale':'');
    $('latest-label').textContent=fmt(state.manifest.latest,{day:'numeric',month:'long',year:'numeric'});
    $('archive-total').textContent=all.length;$('edition-number').textContent=String(all.length-i).padStart(2,'0');$('stamp-date').textContent=fmt(d.date,{day:'2-digit',month:'short',year:'numeric'});
    $('edition-label').textContent=isLatest?'LA TUA RASSEGNA PERSONALE':'DAL TUO ARCHIVIO';
    $('headline').replaceChildren(document.createTextNode(isLatest?'Le cose che contano':'Una giornata da ritrovare'),node('span','','.'));
    $('subtitle').textContent=d.summary;
    const notes=[];
    if(!isLatest)notes.push(`Stai leggendo l’edizione del ${fmt(d.date,{day:'numeric',month:'long',year:'numeric'})}. Il pulsante “Ultime news” resta sempre disponibile.`);
    if(d.kind==='bootstrap')notes.push('Edizione iniziale: selezione retrospettiva di articoli verificati. Non è una rassegna delle ultime 24 ore né uno storico di newsletter già inviate.');
    if(isLatest && d.date<today())notes.push(`Nessuna edizione più recente caricata: l’ultima disponibile è del ${fmt(d.date)}.`);
    if(d.note)notes.push(d.note);
    $('edition-notice').hidden=!notes.length;$('edition-notice').textContent=notes.join(' ');
    $('prev').disabled=i===all.length-1;$('next').disabled=i===0;
    $('prev').title=$('prev').disabled?'Non ci sono edizioni precedenti':'Edizione precedente';$('next').title=$('next').disabled?'Sei sull’ultima edizione':'Edizione successiva';
    const metrics=$('metrics');metrics.replaceChildren();
    const words=d.items.reduce((sum,n)=>sum+(n.summary+' '+n.why_you_care).split(/\s+/).length,0);
    for (const [value,label] of [[d.items.length,'notizie selezionate'],[d.items.filter(n=>n.featured).length,'da non perdere'],[Math.max(1,Math.ceil(words/180)),'min di lettura']]) {const x=node('span');x.append(node('strong','',value),document.createTextNode(label));metrics.append(x);}
    metrics.append(node('span','updated',`Edizione creata ${fmt(d.generated_at,{day:'numeric',month:'short',hour:'2-digit',minute:'2-digit'})}`));
    $('footer-meta').textContent=`${all.length} edizion${all.length===1?'e':'i'} in archivio · Preferenze in questo browser`;
    document.title=`Personal News — ${fmt(d.date,{day:'numeric',month:'long',year:'numeric'})}`;
  }
  function renderCategories() {
    for(const id of ['rail-categories','chips']) {
      const wrap=$(id);wrap.replaceChildren();const cats=id==='chips'?[{id:'all',label:'Tutte'},...state.categories]:state.categories;
      for(const c of cats) {
        const button=node('button',id==='chips'?'chip':'category-link');button.type='button';button.classList.toggle('active',state.category===c.id);button.setAttribute('aria-pressed',String(state.category===c.id));color(button,c.id);
        if(c.id!=='all')button.append(node('span','cat-dot'));
        button.append(document.createTextNode(c.label));
        if(id==='chips'&&state.mode==='edition')button.append(node('span','count',c.id==='all'?state.day.items.length:state.day.items.filter(i=>i.category===c.id).length));
        button.title=c.description||'Tutte le categorie';button.onclick=()=>{state.category=c.id;filtersChanged();$('feed').scrollIntoView();};wrap.append(button);
      }
    }
  }
  function articleImage(url,alt,onError) {const img=node('img');img.loading='lazy';img.decoding='async';img.referrerPolicy='no-referrer';img.alt=alt||'';img.onerror=()=>{img.remove();onError?.();};img.src=url;return img;}
  function openImage(image) {
    if (!https(image?.url)) return;
    $('full-image').src=image.url;$('full-image').alt=image.alt||'';
    $('image-caption').textContent=[image.alt,image.credit].filter(Boolean).join(' · ');
    $('image-source').href=https(image.source_url)||image.url;
    $('image-dialog').showModal();
  }
  function renderHighlights() {
    const items=state.day.items.filter(i=>i.featured).slice(0,3);$('highlights').hidden=!items.length || state.mode==='archive';const grid=$('highlight-grid');grid.replaceChildren();
    if(!items.length)return;
    const first=items[0],lead=node('article','lead');
    if(prefs.images && https(first.image?.url))lead.append(articleImage(first.image.url,first.image.alt));
    lead.append(node('span','lead-tag',`${category(first.category).label} · In evidenza`));
    const title=node('h3'),a=node('a','',first.title);a.href=`#${first.id}`;a.onclick=()=>showArticle(first.id);title.append(a);lead.append(title,node('span','lead-source',`${first.sources[0].name} · ${first.published_date?fmt(first.published_date):'Data non dichiarata'}`));
    const cta=node('a','lead-cta','↗');cta.href=`#${first.id}`;cta.setAttribute('aria-label',`Leggi la scheda: ${first.title}`);cta.onclick=()=>showArticle(first.id);lead.append(cta);grid.append(lead);
    const side=node('div','highlight-side');items.slice(1).forEach((item,index)=>{const n=node('article','highlight-small');color(n,item.category);const body=node('div');body.append(node('span','mini-category',category(item.category).label));const h=node('h3'),l=node('a','',item.title);l.href=`#${item.id}`;l.onclick=()=>showArticle(item.id);h.append(l);body.append(h,node('span','muted',`${item.sources[0].name} · ${item.published_date?fmt(item.published_date):'Data non dichiarata'}`));n.append(node('span','highlight-number',String(index+2).padStart(2,'0')),body);side.append(n);});if(items.length>1)grid.append(side);
  }
  function showArticle(id) {clearFilters();state.mode='edition';syncControls();renderCategories();writeURL();renderCards().then(()=>document.getElementById(id)?.scrollIntoView({block:'center'}));}
  function matches(i) {
    if(state.category!=='all'&&i.category!==state.category)return false;
    if(state.unread&&state.read.has(i.id))return false;if(state.saved&&!state.bookmarks.has(i.id))return false;
    return !state.q||normalize(i.search_text||[i.title,i.summary,i.why_you_care,...(i.tags||[]),...(i.sources||[]).map(s=>s.name)].join(' ')).includes(normalize(state.q));
  }
  async function renderCards() {
    const ticket=++state.render;$('cards').setAttribute('aria-busy','true');$('read-all').disabled=true;state.visible=[];
    try {
      let rows, total;
      if(state.mode==='archive') {
        const indexed=(await getSearch()).filter(matches);total=indexed.length;const page=indexed.slice(0,state.limit);
        const dates=[...new Set(page.map(i=>i.edition))];const days=await Promise.all(dates.map(getDay));
        const byId=new Map(days.flatMap(d=>d.items.map(i=>[i.id,{...i,edition:editionKey(d)}])));rows=page.map(i=>byId.get(i.id)).filter(Boolean);
        if(rows.length!==page.length)throw Error('L’indice di ricerca non è allineato alle edizioni. Esegui tools/news.py rebuild.');
      } else {const all=state.day.items.filter(matches);total=all.length;rows=all.slice(0,state.limit).map(i=>({...i,edition:editionKey(state.day)}));}
      if(ticket!==state.render)return;
      $('error').hidden=true;state.visible=rows;$('cards').replaceChildren(...rows.map(createCard));$('cards').setAttribute('aria-busy','false');$('read-all').disabled=!rows.length;
      $('result-count').textContent=`${rows.length}${total>rows.length?' di '+total:''} notizi${rows.length===1?'a':'e'}`;
      $('feed-heading').textContent=state.mode==='archive'?(state.saved?'Le tue notizie salvate':'Cerca nel tuo archivio'):(state.date===state.manifest.latest?'News recenti':'News di questa edizione');
      $('empty').hidden=rows.length>0;$('empty-title').textContent=state.saved?'Nessuna notizia salvata con questi filtri.':'Nessuna notizia da mostrare.';
      $('empty-copy').textContent=state.mode==='edition'&&!state.day.items.length?'Questa edizione non contiene novità sufficientemente rilevanti. Puoi consultare l’archivio.':'Prova un’altra ricerca o azzera i filtri. I preferiti si salvano con la stella sulle card.';
      $('more').hidden=rows.length>=total;$('highlights').hidden=state.mode==='archive'||!state.day.items.some(i=>i.featured);
    } catch(e) {if(ticket===state.render){error(e.message);$('cards').setAttribute('aria-busy','false');}}
  }
  function createCard(item) {
    const n=$('card-template').content.firstElementChild.cloneNode(true);n.id=item.id;n.dataset.id=item.id;color(n,item.category);n.classList.toggle('is-read',state.read.has(item.id));
    n.querySelector('.placeholder-label').textContent=category(item.category).label;n.querySelector('.placeholder-symbol').textContent=category(item.category).symbol||'↗';
    const img=n.querySelector('.article-image');
    if(prefs.images&&https(item.image?.url)){
      img.alt=item.image.alt||'';
      n.querySelector('.media-credit').textContent=item.image.credit||'';
      const zoom=node('button','image-expand','⛶');zoom.type='button';zoom.title='Visualizza immagine completa';zoom.setAttribute('aria-label','Visualizza immagine completa');
      zoom.onclick=()=>openImage(item.image);
      n.querySelector('.card-media').append(zoom);
      img.onerror=()=>{img.remove();zoom.remove();n.querySelector('.media-credit').textContent='';};
      img.src=item.image.url;
    }else img.remove();
    const meta=n.querySelector('.card-kicker');meta.append(node('span','card-category',category(item.category).label),node('span',`badge${item.status==='UPDATE'?' update':''}`,item.status==='UPDATE'?'Aggiornamento':'Nuova'),node('span','',item.published_date?`Fonte · ${fmt(item.published_date,{day:'numeric',month:'short',year:'numeric'})}`:'Fonte · data non dichiarata'));
    if(state.mode==='archive')meta.append(node('span','',`Edizione · ${fmt(item.edition,{day:'numeric',month:'short',year:'numeric'})}`));
    n.querySelector('.card-title').textContent=item.title;n.querySelector('.card-summary').textContent=item.summary;n.querySelector('.why p').textContent=item.why_you_care;
    if(item.status==='UPDATE'){const delta=n.querySelector('.delta');delta.hidden=false;delta.textContent=`Cosa cambia: ${item.delta}`;if(item.previous){const l=node('a','', ' Vedi la notizia precedente →');l.href=`?date=${encodeURIComponent(item.previous.date)}#${encodeURIComponent(item.previous.id)}`;delta.append(l);}}
    const sources=n.querySelector('.source-content');
    for(const source of item.sources){const p=node('p');p.append(link(source.url,source.name));p.append(document.createTextNode(` · ${{official:'Fonte ufficiale',research:'Ricerca',reputable:'Testata',community:'Community'}[source.type]||'Fonte'}`));sources.append(p);}
    if(item.event_date && item.event_date!==item.published_date)sources.append(node('p','',`Data dell’evento: ${fmt(item.event_date,{day:'numeric',month:'long',year:'numeric'})}`));
    sources.append(node('p','',`Fonti consultate il ${fmt(item.verified_at,{day:'numeric',month:'long',year:'numeric'})}. Sintesi originale, non copia dell’articolo.`));
    if(item.image?.source_url){const p=node('p');p.append(link(item.image.source_url,'Provenienza immagine'));p.append(document.createTextNode(` · ${item.image.credit||'Diritti del rispettivo titolare'}`));sources.append(p);}
    const tags=node('div');(item.tags||[]).forEach(t=>tags.append(node('span','tag',t)));sources.append(tags);
    const open=n.querySelector('.source-link');open.href=https(item.sources[0].url)||'#';
    const read=n.querySelector('.read-button'),save=n.querySelector('.save-button');
    const refresh=()=>{const r=state.read.has(item.id),s=state.bookmarks.has(item.id);n.classList.toggle('is-read',r);read.setAttribute('aria-pressed',String(r));read.setAttribute('aria-label',r?'Segna come non letto':'Segna come letto');read.title=read.getAttribute('aria-label');save.setAttribute('aria-pressed',String(s));save.textContent=s?'★':'☆';save.setAttribute('aria-label',s?'Rimuovi dai salvati':'Salva notizia');save.title=save.getAttribute('aria-label');$('saved-total').textContent=state.bookmarks.size;};refresh();
    read.onclick=()=>{state.read.has(item.id)?state.read.delete(item.id):state.read.add(item.id);persist();refresh();if(state.unread)renderCards();};
    save.onclick=()=>{state.bookmarks.has(item.id)?state.bookmarks.delete(item.id):state.bookmarks.add(item.id);persist();refresh();if(state.saved)renderCards();};
    open.onclick=()=>{state.read.add(item.id);persist();refresh();if(state.unread)renderCards();};
    n.querySelector('.share-button').onclick=async()=>{const u=new URL(location.href);u.search='';u.searchParams.set('date',item.edition);u.hash=item.id;try{await navigator.clipboard.writeText(u.href);toast('Link alla notizia copiato.');}catch{toast('Copia il link dalla finestra che si apre.');window.prompt('Link permanente alla notizia',u.href);}};
    return n;
  }
  function filtersChanged() {if(!state.day)return;state.limit=24;syncControls();renderCategories();writeURL();renderCards();}
  function openArchive() {if(!state.manifest)return;renderArchive();$('archive-dialog').showModal();}
  function renderArchive() {
    const month=$('archive-month').value;const entries=state.manifest.editions.filter(d=>!month||d.date.startsWith(month));$('archive-list').replaceChildren();
    for(const e of entries){const b=node('button',`archive-item${editionKey(e)===state.date?' current':''}`);b.type='button';const text=node('span');text.append(node('strong','',fmt(e.date,{weekday:'long',day:'numeric',month:'long',year:'numeric'})),node('small','',e.title));b.append(text,node('span','counter',`${e.count} news`));b.onclick=()=>{$('archive-dialog').close();navigate(editionKey(e));};$('archive-list').append(b);}
    $('archive-help').textContent=entries.length?`${entries.length} edizion${entries.length===1?'e disponibile':'i disponibili'}. Non vengono create giornate fittizie per riempire lo storico.`:'Nessuna edizione in questo mese.';
  }
  function latest() {if(state.manifest?.latest){$('new-edition').hidden=true;navigate(state.manifest.latest);}}
  function saved() {if(!state.day)return;state.mode='archive';clearFilters();state.saved=true;filtersChanged();$('feed').scrollIntoView();}
  function adjacent(direction) {if(!state.day)return;const i=state.manifest.editions.findIndex(e=>editionKey(e)===state.date);const next=state.manifest.editions[i+direction];if(next)navigate(editionKey(next));}
  async function checkFreshness() {
    if(document.hidden||!state.manifest)return;
    try {const m=checkManifest(await fetchJson('data/index.json'));if(m.updated_at!==state.manifest.updated_at){state.manifest=m;state.cache.clear();state.search=null;state.searchPromise=null;$('new-edition').hidden=false;$('latest-label').textContent=fmt(m.latest,{day:'numeric',month:'long',year:'numeric'});}}catch{/* Keep the current edition on transient network errors. */}
  }
  function bind() {
    for(const id of ['nav-latest','latest-button','mobile-latest','refresh-latest'])$(id).onclick=latest;
    for(const id of ['nav-archive','date-open','mobile-archive'])$(id).onclick=openArchive;
    for(const id of ['nav-saved','mobile-saved'])$(id).onclick=saved;
    for(const id of ['settings-open','mobile-settings'])$(id).onclick=()=>$('settings-dialog').showModal();
    document.querySelectorAll('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());
    document.querySelectorAll('dialog').forEach(d=>d.addEventListener('click',e=>{if(e.target===d){const r=d.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)d.close();}}));
    $('prev').onclick=()=>adjacent(1);$('next').onclick=()=>adjacent(-1);$('archive-month').oninput=renderArchive;
    $('search').oninput=()=>{state.q=$('search').value;filtersChanged();};$('scope').onchange=()=>{state.mode=$('scope').value;filtersChanged();};
    $('unread').onclick=()=>{state.unread=!state.unread;filtersChanged();};$('saved').onclick=()=>{state.saved=!state.saved;filtersChanged();};
    for(const id of ['reset','empty-reset'])$(id).onclick=()=>{clearFilters();filtersChanged();};
    $('read-all').onclick=()=>{state.visible.forEach(i=>state.read.add(i.id));persist();renderCards();toast('Le notizie visibili sono segnate come lette.');};
    $('more').onclick=()=>{state.limit+=24;renderCards();};$('back-top').onclick=()=>window.scrollTo({top:0,behavior:'smooth'});
    $('density').onclick=()=>{prefs.compact=!prefs.compact;persist();applyPrefs();};
    $('theme').onclick=()=>{prefs.theme=allowedTheme[(allowedTheme.indexOf(prefs.theme)+1)%allowedTheme.length];persist();applyPrefs();};
    $('theme-select').onchange=()=>{prefs.theme=$('theme-select').value;persist();applyPrefs();};$('images').onchange=()=>{prefs.images=$('images').checked;persist();applyPrefs();if(state.day){renderHighlights();renderCards();}};
    matchMedia('(prefers-color-scheme: dark)').addEventListener('change',applyPrefs);
    $('export').onclick=()=>{const blob=new Blob([JSON.stringify({...prefs,read:[...state.read],saved:[...state.bookmarks]},null,2)],{type:'application/json'});const u=URL.createObjectURL(blob),a=node('a');a.href=u;a.download='personal-news-preferenze.json';a.click();setTimeout(()=>URL.revokeObjectURL(u),1000);};
    $('import').onclick=()=>$('import-file').click();$('import-file').onchange=async e=>{const file=e.target.files[0];if(!file)return;try{if(file.size>3000000)throw Error('File troppo grande.');const imported=cleanPrefs(JSON.parse(await file.text()));prefs={...imported};state.read=new Set([...state.read,...imported.read]);state.bookmarks=new Set([...state.bookmarks,...imported.saved]);persist();applyPrefs();if(state.day){syncControls();renderHighlights();renderCards();}toast('Preferenze importate; letti e salvati uniti a quelli presenti.');}catch(err){toast(err.message);}finally{e.target.value='';}};
    window.addEventListener('popstate',()=>{if(state.manifest)readRoute();});
    document.addEventListener('visibilitychange',checkFreshness);setInterval(checkFreshness,300000);
    document.addEventListener('keydown',e=>{if(e.ctrlKey||e.metaKey||e.altKey||e.shiftKey||document.querySelector('dialog[open]')||e.target.closest('input,textarea,select,button,a,summary,[contenteditable="true"]'))return;if(e.key==='/'){e.preventDefault();$('search').focus();}else if(e.key==='ArrowLeft'){e.preventDefault();adjacent(1);}else if(e.key==='ArrowRight'){e.preventDefault();adjacent(-1);}});
  }
  async function init() {
    applyPrefs();bind();
    try {const [manifest,cats]=await Promise.all([fetchJson('data/index.json'),fetchJson('data/categories.json')]);state.manifest=checkManifest(manifest);if(cats.version!==1||!Array.isArray(cats.categories))throw Error('Categorie non valide.');state.categories=cats.categories;if(!manifest.editions.length){$('subtitle').textContent='La prima edizione non è ancora disponibile.';$('cards').setAttribute('aria-busy','false');return;}await readRoute();}
    catch(e){error(e.message);$('subtitle').textContent='Caricamento non riuscito. Nessuna notizia viene inventata o sostituita.';$('cards').setAttribute('aria-busy','false');}
  }
  init();
})();
