# Briefing finale canonico

Circa 8–10 righe, italiano, niente newsletter completa. Usare i dati effettivi dell'edizione e gli esiti osservati, non un modello testuale con conteggi copiati.

```text
Personal News · <data>
<X> News · <Y> Radar · <N> NEW · <M> UPDATE · <F> Da non perdere
Da non perdere:
— <solo titolo 1, se presente>
— <solo titolo 2, se presente>
— <solo titolo 3, se presente>
Da sapere oggi: <soltanto se pertinente e non scaduto>
GitHub: <esito effettivo> · Pages: <esito effettivo>
<website_url>
```

- X+Y deve uguagliare N+M; featured appartiene a News. I conteggi sono del totale dell'edizione, non delle sole aggiunte nell'ultima run.
- Per un rerun aggiungere, se utile, “2 aggiunte in questa run” o “nessuna aggiunta; edizione invariata”, senza far sembrare che il sito contenga soltanto quelle due notizie.
- Non usare “rispetto a ieri” senza un confronto verificato. NEW significa mai fornito prima nell'archivio, non necessariamente pubblicato oggi.
- Zero novità in una nuova giornata: edizione vuota esplicita e messaggio breve. Zero novità in un rerun: preservare l'edizione già pubblicata.
- “GitHub aggiornato” richiede rilettura del commit; “Pages verificato” richiede contenuto live corrispondente e controlli osservati. In attesa del deploy scrivere “in pubblicazione”.
- Un problema di accesso alle fonti è una ricerca incompleta, non prova che non esistano notizie. Esplicitarlo.
- `tools/briefing.py` genera un testo di base con conteggi coerenti; gli esiti predefiniti sono “non verificato”.
- Non riportare un modello del task se i metadati non lo espongono.
