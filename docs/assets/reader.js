/* Full-screen Italian reading view. UI only; never scrape or translate in the browser. */
(() => {
  'use strict';
  const validId = value => typeof value === 'string' && /^[a-z0-9][a-z0-9-]{0,159}$/.test(value);
  const node = (tag, cls, text) => {
    const element = document.createElement(tag);
    if (cls) element.className = cls;
    if (text !== undefined) element.textContent = text;
    return element;
  };
  const safeURL = value => {
    try {
      const u = new URL(value);
      return u.protocol === 'https:' && !u.username && !u.password ? u.href : null;
    } catch { return null; }
  };
  function externalLink(source, label) {
    const a = node('a', 'reader-source', label || source.name);
    const href = safeURL(source.url);
    if (href) a.href = href;
    a.target = '_blank'; a.rel = 'noopener noreferrer'; a.referrerPolicy = 'no-referrer';
    return a;
  }
  function checkBody(body, item) {
    if (!body || body.version !== 1 || body.item_id !== item.id || body.language !== 'it' || body.editorial_mode !== 'original') throw Error('Articolo non valido.');
    if (!Array.isArray(body.sources) || !body.sources.length || !body.sources.every(s => s && typeof s.name === 'string' && safeURL(s.url))) throw Error('Fonti dell’articolo non valide.');
    const urls = new Set(body.sources.map(s => s.url));
    if (!Array.isArray(body.sections) || body.sections.length < 2 || !body.sections.every(s => s && typeof s.heading === 'string' && Array.isArray(s.paragraphs) && s.paragraphs.length && s.paragraphs.every(p => typeof p === 'string') && Array.isArray(s.source_urls) && s.source_urls.length && s.source_urls.every(u => urls.has(u)))) throw Error('Testo dell’articolo non valido.');
    return body;
  }

  window.PersonalNewsReader = {
    create(hooks) {
      const dialog = node('dialog', 'reader-dialog'); dialog.id = 'reader-dialog';
      dialog.setAttribute('aria-labelledby', 'reader-title');
      const toolbar = node('div', 'reader-toolbar');
      const back = node('button', 'reader-back', '← Notizie'); back.type = 'button'; back.id = 'reader-back';
      back.setAttribute('aria-label', 'Torna alle notizie'); back.onclick = hooks.requestClose;
      const label = node('span', 'reader-brand', 'personal news.');
      const theme = node('button', 'icon-button', '◐'); theme.type = 'button';
      theme.setAttribute('aria-label', 'Cambia tema'); theme.onclick = hooks.changeTheme;
      toolbar.append(back, label, theme);
      const paper = node('article', 'reader-paper');
      const kicker = node('p', 'eyebrow'); kicker.id = 'reader-kicker';
      const title = node('h2', 'reader-title'); title.id = 'reader-title'; title.tabIndex = -1;
      const meta = node('p', 'reader-meta'); meta.id = 'reader-meta';
      const actions = node('div', 'reader-actions');
      const read = node('button', 'pill'); read.id = 'reader-read'; read.type = 'button';
      const save = node('button', 'pill'); save.id = 'reader-save'; save.type = 'button';
      const share = node('button', 'pill', 'Condividi link'); share.id = 'reader-share'; share.type = 'button';
      actions.append(read, save, share);
      const imageBox = node('figure', 'reader-image');
      const summary = node('p', 'reader-summary');
      const status = node('p', 'reader-notice'); status.id = 'reader-status'; status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite');
      const retry = node('button', 'pill', 'Riprova a caricare il testo'); retry.type = 'button'; retry.id = 'reader-retry'; retry.hidden = true;
      const bodyBox = node('div', 'reader-body'); bodyBox.id = 'reader-body';
      const why = node('section', 'reader-why');
      const sourcesBox = node('section', 'reader-sources'); sourcesBox.id = 'reader-sources';
      const footer = node('p', 'reader-editorial'); footer.textContent = 'Testo originale in italiano basato sulle fonti citate. Non è una traduzione integrale né una copia dell’articolo della fonte.';
      paper.append(kicker, title, meta, actions, imageBox, summary, status, retry, bodyBox, why, sourcesBox, footer);
      dialog.append(toolbar, paper); document.body.append(dialog);
      let current = null, sequence = 0, controller = null;
      let scrollBefore = 0;

      function setStatus(kind, message) {
        dialog.dataset.contentStatus = kind;
        status.textContent = message;
      }
      function flags() {
        if (!current) return;
        const f = hooks.flags(current.id);
        read.textContent = f.read ? '✓ Letta · segna non letta' : '✓ Segna come letta';
        save.textContent = f.saved ? '★ Salvata' : '☆ Salva';
        read.setAttribute('aria-pressed', String(f.read)); save.setAttribute('aria-pressed', String(f.saved));
        read.setAttribute('aria-label', f.read ? 'Segna come non letto' : 'Segna come letto');
        save.setAttribute('aria-label', f.saved ? 'Rimuovi dai salvati' : 'Salva notizia');
      }
      function renderSources(sources) {
        sourcesBox.replaceChildren(node('h3', '', 'Fonti e approfondimenti originali'));
        const list = node('ol');
        for (const source of sources) {
          const li = node('li'); li.append(externalLink(source)); list.append(li);
        }
        sourcesBox.append(list);
      }
      async function json(path, signal) {
        const response = await fetch(path, {cache: 'no-store', credentials: 'same-origin', signal});
        if (!response.ok) throw Error(`HTTP ${response.status}`);
        return response.json();
      }
      async function loadBody() {
        if (!current) return;
        const item = current, ticket = ++sequence;
        controller?.abort(); controller = new AbortController();
        const signal = controller.signal;
        bodyBox.replaceChildren(); retry.hidden = true; bodyBox.setAttribute('aria-busy', 'true');
        setStatus('loading', 'Caricamento dell’articolo in italiano…');
        try {
          const index = await json('data/article-index.json', signal);
          if (ticket !== sequence || !dialog.open) return;
          if (index.version !== 1 || !Array.isArray(index.items)) throw Error('Indice articoli non valido.');
          const entry = index.items.find(i => i.item_id === item.id);
          if (!entry) throw Error('Articolo non indicizzato.');
          if (entry.status === 'legacy_summary') {
            setStatus('legacy-summary', 'Questa scheda storica contiene solo la sintesi in italiano. L’approfondimento completo non è ancora disponibile.');
            footer.hidden = true;
            return;
          }
          const expected = `data/articles/${item.id}.json`;
          if (entry.status !== 'full' || entry.path !== expected) throw Error('Percorso articolo non valido.');
          const body = checkBody(await json(expected, signal), item);
          if (ticket !== sequence || !dialog.open) return;
          for (const part of body.sections) {
            const section = node('section', 'reader-section'); section.append(node('h3', '', part.heading));
            part.paragraphs.forEach(p => section.append(node('p', '', p)));
            const citations = node('p', 'reader-citations', 'Fonti: ');
            part.source_urls.forEach((url, n) => {
              const i = body.sources.findIndex(s => s.url === url);
              if (n) citations.append(document.createTextNode(' · '));
              citations.append(externalLink(body.sources[i], `[${i + 1}]`));
            });
            section.append(citations); bodyBox.append(section);
          }
          renderSources(body.sources);
          const words = body.sections.reduce((n, s) => n + s.paragraphs.join(' ').trim().split(/\s+/).length, 0);
          setStatus('full', `Articolo in italiano · ${Math.max(1, Math.ceil(words / 200))} min di lettura`);
          footer.hidden = false;
        } catch (error) {
          if (ticket !== sequence || error.name === 'AbortError' || !dialog.open) return;
          setStatus('error', 'Il testo completo non è stato caricato. Qui resta la sintesi: riprova oppure consulta le fonti.');
          retry.hidden = false; footer.hidden = true;
        } finally {
          if (ticket === sequence) bodyBox.setAttribute('aria-busy', 'false');
        }
      }
      read.onclick = () => { if (current) { hooks.toggleRead(current.id); flags(); } };
      save.onclick = () => { if (current) { hooks.toggleSaved(current.id); flags(); } };
      share.onclick = () => { if (current) hooks.share(current); };
      retry.onclick = loadBody;
      dialog.addEventListener('cancel', event => { event.preventDefault(); hooks.requestClose(); });
      return {
        isOpen: () => dialog.open,
        itemId: () => current?.id,
        refresh: flags,
        open(item) {
          if (!validId(item?.id)) return;
          current = item; dialog.dataset.itemId = item.id;
          title.textContent = item.title;
          kicker.textContent = `${item.section === 'radar' ? 'RADAR' : 'NEWS'} · LETTURA IN ITALIANO`;
          meta.textContent = `Fonte · ${hooks.publicationLabel(item)}${item.published_at ? ' · Europe/Rome' : ' · orario non dichiarato'}`;
          summary.textContent = item.summary;
          why.replaceChildren(node('h3', '', 'Perché conta'), node('p', '', item.why_you_care));
          if (item.status === 'UPDATE') why.append(node('h3', '', 'Cosa cambia rispetto al precedente'), node('p', '', item.delta));
          imageBox.replaceChildren(); imageBox.hidden = true;
          if (hooks.imagesEnabled() && safeURL(item.image?.url)) {
            const zoom = node('button', 'reader-zoom'); zoom.type = 'button'; zoom.setAttribute('aria-label', 'Visualizza immagine completa');
            const img = node('img'); img.alt = item.image.alt || ''; img.referrerPolicy = 'no-referrer'; img.decoding = 'async';
            img.onerror = () => { if (current?.id === item.id) imageBox.hidden = true; };
            img.src = item.image.url; zoom.append(img); zoom.onclick = () => hooks.openImage(item.image);
            imageBox.append(zoom, node('figcaption', '', item.image.credit || '')); imageBox.hidden = false;
          }
          renderSources(item.sources); footer.hidden = true; flags();
          if (!dialog.open) { scrollBefore = window.scrollY; dialog.showModal(); }
          document.body.classList.add('reader-open');
          dialog.scrollTop = 0; title.focus({preventScroll: true});
          loadBody();
        },
        close() {
          ++sequence; controller?.abort(); current = null;
          if (dialog.open) dialog.close();
          document.body.classList.remove('reader-open');
          window.scrollTo({top: scrollBefore, behavior: 'instant'});
        }
      };
    }
  };
})();
