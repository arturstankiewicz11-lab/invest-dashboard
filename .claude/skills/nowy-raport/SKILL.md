---
name: nowy-raport
description: Przetworzenie nowego raportu finansowego spółki (10-K/10-Q/S-1/raport roczny) — ekstrakcja do fundamentals, porównanie z poprzednim okresem, propozycja rewizji DCF. Użyj gdy użytkownik mówi "nowy raport [TICKER]", "wrzuciłem raport [TICKER]" lub wrzucił PDF do data/reports/.
---

# /nowy-raport [TICKER] — przetworzenie raportu finansowego

Realizuje workflow z CLAUDE.md sekcja 3, z twardymi zasadami z konstytucji (sekcja 2).

## Kroki

1. **Znajdź dokument**: najnowszy PDF w `data/reports/[TICKER]/`. Brak lub tylko cover page
   (sprawdź: `pdftotext | wc -l` — podejrzanie mało tekstu = niekompletny plik!) → zaproponuj
   pobranie pełnego z SEC EDGAR (CIK przez full-text search) lub IR spółki; zapisz do reports/.

2. **Ekstrakcja** — TYLKO liczby wprost z dokumentu (konstytucja pkt 2-4):
   revenue (Q/FY!), EBIT i operating result (raporty EU rozróżniają — zapisz oba),
   D&A i CapEx (z cash flow statement, nie szacuj), FCF jeśli podany,
   **net debt pełny stack**: dług + current portion + finance leases (operating leases NIE —
   czynsz już w EBIT), shares diluted, guidance, segmenty (do Kroku 0), sekcja
   Competition (do competitive_landscape), koncentracja klientów.
   Czego nie ma → "brak w raporcie".

3. **Zapisz fundamentals**: `data/fundamentals/[TICKER]/[PERIOD].json` (format: CLAUDE.md
   sekcja 8) — z `source_file` wskazującym PDF i dosłownymi cytatami w `notes` przy
   kluczowych faktach.

4. **Porównaj z poprzednim okresem**: revenue YoY/QoQ (trajektoria segmentów!), marża,
   dług, guidance. Pokaż tabelą.

5. **Propozycja rewizji DCF** (gdy dane vs założenia modelu różnią się >10%):
   policz pełnym protokołem (CLAUDE.md sekcja 4, kroki 0-F) — NIGDY widełki przed
   wyliczeniem. Zmiany `fair_value` + `dcf` zapisuj; zmiany `recommendation` /
   `entry_point` / `thesis_breaker` TYLKO proponuj i czekaj na akceptację (pkt 1).

6. **Walidacja + push**: `python3 tools/validate.py [TICKER]` — ERRORy napraw przed pushem.
   Jeśli rewizja zmieniła FV/model → uruchom agenta `weryfikator` (werdykt NIEZGODNA
   blokuje). Potem commit + push (pkt 9). Przypomnij o odświeżeniu karty aplikacji.
