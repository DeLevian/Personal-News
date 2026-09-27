"""One-time checked transformation of the existing UI. Removed before merge."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def patch():
 p=ROOT/'docs/assets/app.js';s=p.read_text()
 if 'const sectionOf =' in s:return
 def rep(a,b):
  nonlocal s
  if a not in s: raise RuntimeError('Expected UI anchor missing: '+a[:100])
  s=s.replace(a,b)
 rep("const editionKey = e => e.id || e.edition_id || e.date;", "const editionKey = e => e.id || e.edition_id || e.date;\n  const sectionOf = i => i.section || 'main';\n  const itemCounts = items => ({main:items.filter(i=>sectionOf(i)==='main').length,radar:items.filter(i=>sectionOf(i)==='radar').length,new:items.filter(i=>i.status==='NEW').length,update:items.filter(i=>i.status==='UPDATE').length,featured:items.filter(i=>i.featured).length});")
 rep("category:'all',q:''", "category:'all',section:'all',q:''")
 rep("m.version !== 1", "![1,2].includes(m.version)")
 rep("d.version!==1", "![1,2].includes(d.version)")
 rep("cats.version!==1", "![1,2].includes(cats.version)")
 rep("function clearFilters() {state.category='all';", "function clearFilters() {state.section='all';state.category='all';")
 rep("$('scope').value=state.mode;$('search').value=state.q;", "$('scope').value=state.mode;$('search').value=state.q;\n    document.querySelectorAll('[data-section-filter]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sectionFilter===state.section)));")
 rep("if (state.q) u.searchParams.set('q',state.q);", "if (state.q) u.searchParams.set('q',state.q);\n    if (state.section!=='all') u.searchParams.set('section',state.section);")
 rep("state.saved=u.searchParams.get('saved')==='1';", "state.section=['main','radar'].includes(u.searchParams.get('section'))?u.searchParams.get('section'):'all';\n    state.saved=u.searchParams.get('saved')==='1';")
 rep("renderHeader();renderCategories();syncControls();renderHighlights();await renderCards();", "renderHeader();renderAttention();renderCategories();syncControls();renderHighlights();await renderCards();")
 old="for (const [value,label] of [[d.items.length,'notizie selezionate'],[d.items.filter(n=>n.featured).length,'da non perdere'],[Math.max(1,Math.ceil(words/180)),'min di lettura']])"
 rep(old,"const c=itemCounts(d.items);\n    for (const [value,label] of [[c.main,'News'],[c.radar,'Radar'],[c.new,'NEW'],[c.update,'UPDATE'],[c.featured,'da non perdere']])")
 rep("m.editions.sort((a,b)=>(b.generated_at||b.date).localeCompare(a.generated_at||a.date));", "m.editions.sort((a,b)=>new Date(b.generated_at||b.date)-new Date(a.generated_at||a.date));")
 attention="""
  function renderAttention() {
    const box=$('attention-today'),a=state.day?.attention_today;box.replaceChildren();
    if(!a){box.hidden=true;return;}
    const now=Date.now(), current=state.day.date===today()&&now>=Date.parse(a.valid_from)&&now<Date.parse(a.expires_at);
    const archived=state.date!==state.manifest.latest||state.day.date!==today();
    box.hidden=!current&&!archived;if(box.hidden)return;
    box.append(node('span','eyebrow',current?'DA SAPERE OGGI':'DA SAPERE ALLORA · ARCHIVIO'),node('p','',a.text));
    const detail=node('p','muted',`Scadenza: ${fmt(a.expires_at,{day:'numeric',month:'long',hour:'2-digit',minute:'2-digit'})} · Europe/Rome`);
    box.append(detail,link(a.source_url,'Verifica alla fonte ↗','source-link'));
  }
"""
 rep("  function renderCategories() {",attention+"\n  function renderCategories() {")
 rep("state.day.items.filter(i=>i.featured)","state.day.items.filter(i=>i.featured&&sectionOf(i)==='main')")
 rep("  function matches(i) {", "  function matches(i) {\n    if(state.section!=='all'&&sectionOf(i)!==state.section)return false;")
 rep("state.visible=rows;$('cards').replaceChildren(...rows.map(createCard));", "state.visible=rows;const mainRows=rows.filter(i=>sectionOf(i)==='main'),radarRows=rows.filter(i=>sectionOf(i)==='radar');\n      $('cards').replaceChildren(...mainRows.map(createCard));$('radar-cards').replaceChildren(...radarRows.map(createCard));\n      $('main-group').hidden=state.section==='radar'||(state.section==='all'&&!mainRows.length);\n      $('radar-group').hidden=state.section==='main';\n      $('radar-empty').hidden=radarRows.length>0;\n      $('radar-count').textContent=radarRows.length+' Radar';")
 rep("n.id=item.id;n.dataset.id=item.id;color(n,item.category);", "n.id=item.id;n.dataset.id=item.id;n.dataset.section=sectionOf(item);n.classList.toggle('radar-card',sectionOf(item)==='radar');color(n,item.category);")
 rep("const meta=n.querySelector('.card-kicker');meta.append", "const meta=n.querySelector('.card-kicker');if(sectionOf(item)==='radar')meta.append(node('span','badge radar-badge','Radar'));meta.append")
 rep("`${e.count} news`", "`${e.counts?.main??e.count} News · ${e.counts?.radar??0} Radar`")
 rep("    $('prev').onclick=()=>adjacent(1);", "    document.querySelectorAll('[data-section-filter]').forEach(b=>b.onclick=()=>{state.section=b.dataset.sectionFilter;filtersChanged();});\n    $('prev').onclick=()=>adjacent(1);")
 rep("setInterval(checkFreshness,300000);", "setInterval(checkFreshness,300000);setInterval(()=>{if(state.day)renderAttention();},60000);")
 rep("    await navigate(target,{url:false,reset:false});", "    if(validId(article)){clearFilters();state.mode='edition';}\n    await navigate(target,{url:false,reset:false});")
 rep("state.day.items.some(i=>i.featured)", "state.day.items.some(i=>i.featured&&sectionOf(i)==='main')")
 rep("document.querySelectorAll('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());", "document.querySelectorAll('.close-dialog').forEach(b=>b.onclick=()=>b.closest('dialog').close());\n    $('image-dialog').addEventListener('close',()=>{$('full-image').removeAttribute('src');});")
 p.write_text(s)
 p=ROOT/'docs/index.html';h=p.read_text()
 h=h.replace('20260927b','20260927v2')
 h=h.replace('<script src="assets/app.js?v=20260927v2" defer></script>', '<link rel="stylesheet" href="assets/v2.css?v=20260927v2">\n  <script src="assets/app.js?v=20260927v2" defer></script>')
 h=h.replace('<section id="highlights"', '<section id="attention-today" class="attention-box" aria-label="Da sapere oggi" hidden></section>\n      <section id="highlights"')
 h=h.replace('<div class="chips" id="chips"', '<div class="section-filters" role="group" aria-label="Tipo di contenuto"><button type="button" class="pill" data-section-filter="all" aria-pressed="true">Tutto</button><button type="button" class="pill" data-section-filter="main" aria-pressed="false">News</button><button type="button" class="pill" data-section-filter="radar" aria-pressed="false">Radar</button></div>\n          <div class="chips" id="chips"')
 h=h.replace('<div id="cards" class="cards" aria-busy="true"></div>', '<div id="main-group"><h3 class="group-label">News principali</h3><div id="cards" class="cards" aria-busy="true"></div></div><section id="radar-group" aria-labelledby="radar-heading"><div class="section-head"><div><p class="eyebrow">SCOPERTE DA TENERE D’OCCHIO</p><h2 id="radar-heading">Radar</h2></div><span id="radar-count" class="muted"></span></div><p class="radar-intro">Segnalazioni verificate degli ultimi 7 giorni, non necessariamente uscite oggi.</p><div id="radar-cards" class="radar-cards"></div><p id="radar-empty" class="muted">Nessun elemento Radar in questa edizione o con questi filtri.</p></section>')
 h=h.replace('“Nuova” significa nuova nel tuo archivio', 'News e Radar condividono ricerca, salvati e storico. “Nuova” significa nuova nel tuo archivio')
 p.write_text(h)
if __name__=='__main__':patch()
