# Architektura systemu — przewodnik top-down

> Ostatnia aktualizacja: 2026-06-12. Po każdej zmianie struktury aktualizować ten plik.

## 1. Obraz całości — 4 warstwy

```
┌─ WARSTWA 1: ZASADY ────────────────────────────────────────────┐
│  CLAUDE.md — zasady wyceny, protokoły, format rekomendacji     │
└────────────────────────────┬───────────────────────────────────┘
                             ↓ (Claude stosuje przy każdej analizie)
┌─ WARSTWA 2: DANE ──────────────────────────────────────────────┐
│  data/reports/        ← PDF-y raportów (źródła prawdy)         │
│  data/fundamentals/   ← liczby wyciągnięte z raportów          │
│  data/recommendations.json ← wyceny, rekomendacje, DCF         │
│  data/watchlist.json  ← obserwowane spółki                     │
│  Google Sheets „Akcje" ← portfel (transakcje Bought/Sold)      │
└────────────────────────────┬───────────────────────────────────┘
                             ↓ (app czyta przy każdym odświeżeniu)
┌─ WARSTWA 3: SILNIK (app.py, jeden plik ~2450 linii) ───────────┐
│  ładowanie danych → ceny live (Yahoo) → kalkulator DCF →       │
│  budowa pozycji portfela                                       │
└────────────────────────────┬───────────────────────────────────┘
                             ↓
┌─ WARSTWA 4: PREZENTACJA (app.py, Streamlit Cloud) ─────────────┐
│  Overview · strony spółek (Wykres/DCF/Działania/Teza) ·        │
│  Watchlista · Chat AI                                          │
└────────────────────────────────────────────────────────────────┘
```

Przepływ zmiany: **edycja pliku → git push → Streamlit Cloud przebudowuje (1-2 min) → ODŚWIEŻ KARTĘ przeglądarki** (stara karta ma martwy WebSocket i nie reaguje).

---

## 2. ZASADY WYCENY — gdzie są i jak zmienić

**Plik: `CLAUDE.md`** (245 linii) — jedyne miejsce z zasadami. Sekcje:

CLAUDE.md (po reorganizacji 12.06.2026, ~230 linii) ma 8 sekcji w logicznej kolejności:

| Sekcja | Co reguluje |
|--------|-------------|
| `1. Rola i profil inwestora` | 6 elementów rekomendacji; kapitał 1 mln PLN, cały świat, 10-50x |
| `2. Zasady twarde (konstytucja)` | **10 punktów**: zakaz zmian rec/entry/breaker bez zgody, FV tylko z wyliczenia, liczby tylko z narzędzi, "nie wiem" obowiązkowe, source+data (ESTYMATY blokują BUY), reguła 2 źródeł, konwencje (FV=base, entry=0.75×FV, etapy 5+5), entry+breaker zawsze, auto-push, rewizja=teza |
| `3. Workflow: nowy raport` | 5 kroków po "nowy raport TICKER"; pełny stack net debt (lekcja AMZN) |
| `4. Protokół DCF` | Krok 0 (segmenty, blended CAGR) + kroki A-E; sanity PV_TV<TV (lekcja RHM) |
| `5. Metody alternatywne` | EV/Revenue, EV/EBITDA, scenariusze — kiedy i jak |
| `6. Checklisty jakościowe` | Buffett Tenets (✅/⚠️/❌ → wielkość pozycji), profil CEO (głód/ekspertyza, werdykt 2×2), mapa konkurencji per segment |
| `7. Źródła danych i transkrypcje` | hierarchia źródeł, cytat+kontekst+wpływ na wycenę |
| `8. Formaty danych` | fundamentals JSON, alt_valuation, szablon rekomendacji |

**Jak zmienić zasadę:** edytuj CLAUDE.md (sam lub powiedz mi) → commit. Od następnej rozmowy stosuję nową wersję. Przykład: chcesz MoS 30% zamiast 25% → zmień pkt 7 konstytucji i powiedz mi, żebym przeliczył entry pointy.

---

## 3. DANE — co gdzie leży i kto to pisze

### `data/recommendations.json` — serce systemu (~92 KB)
Jeden klucz = jeden ticker. Pola każdego tickera:

| Pole | Co zawiera | Gdzie widać w aplikacji |
|------|-----------|------------------------|
| `recommendation` | BUY/HOLD/REDUCE/SELL | wszędzie (kolory, sortowanie, alerty) |
| `fair_value`, `entry_point` | wycena i cena wejścia | tabela pozycji, karty, wykres (linie FV/entry), chipy priorytetów |
| `thesis_short/full` | teza | zakładka Teza, karty |
| `thesis_breaker` | warunki wyjścia | zakładka Działania ("Kiedy wychodzić") |
| `risks`, `buffett_moat` | ryzyka, fosa | zakładka Teza |
| `dcf` | **pełny model wyceny** (szczegóły niżej) | zakładka DCF |
| `events` | historia decyzji i rewizji | zakładka Działania (oś czasu) |
| `upcoming_events`, `next_earnings` | przyszłe daty | kalendarz na Overview |
| `priority_action` | ręczny tekst akcji | sekcja "Priorytetowe działania" (Overview) |

Kto pisze: **Claude podczas analiz** (przez skrypty Pythona, nie ręcznie w edytorze). Ty możesz edytować bezpośrednio — po pushu aplikacja to pokaże.

### `data/fundamentals/TICKER/OKRES.json`
Liczby wyciągnięte **wprost z raportów** (revenue, EBIT, D&A, CapEx, net debt, akcje). Każdy plik ma `source_file` wskazujący PDF. ⚠️ Pliki z `source_file: null` to placeholdery — ich liczby są niezweryfikowane (tak powstał błąd RHM: akcje 83M zamiast 46.5M).

### `data/reports/TICKER/*.pdf`
Źródłowe dokumenty (10-K, 10-Q, S-1, raporty roczne). Wrzucasz Ty albo ściągam ja (SEC EDGAR / IR spółki). To są "dowody" — każda liczba w fundamentals powinna stąd pochodzić.

### `data/watchlist.json`
Obserwowane spółki w koszykach sektorowych (Space/AI/Energy/Quantum/...). Edytowalne też z poziomu aplikacji (strona Watchlista).

### Google Sheets „Akcje"
Portfel: kolumny Nazwa, Ticker, Sector, **Status (Bought/Sold)**, Where, Instrument, Waluta, Volume, Price, Date. Aplikacja: sumuje Bought minus Sold per ticker; pozycja w całości sprzedana znika; średnia cena tylko z zakupów. Odświeżanie: cache 5 min.

---

## 4. WYLICZENIA — gdzie są i jak je samemu zweryfikować

### Gdzie mieszka kalkulator
`app.py`, funkcja **`compute_dcf_stages()`** (sekcja `# ─── DCF CALCULATOR ───`, ~linia 612). Przy **każdym otwarciu zakładki DCF** aplikacja liczy od zera, rok po roku:
```
Revenue(n) = Revenue(n−1) × (1+CAGR)
FCF(n) = Revenue(n) × [EBIT% × (1−tax%) + D&A% − CapEx%]
PV(n) = FCF(n) / (1+WACC)^n
```
z założeń zapisanych w `dcf.stages` w recommendations.json. Czyli: **zakładka DCF nie pokazuje zapamiętanych liczb — pokazuje przeliczenie na żywo z założeń.** Jeśli zmienisz założenie w JSON, tabela się zmieni.

### Jak zweryfikować wycenę samemu (3 poziomy szczegółowości)
1. **W aplikacji**: strona spółki → zakładka DCF → masz: założenia (WACC, g, baza), wyprowadzenie WACC (CAPM), marże FCF per etap, tabelę rok-po-roku z PV, Terminal Value ze wzorem, bridge do ceny akcji, udział TV w EV. Sekcja "Analiza scenariuszowa" (rozwijana) — warianty z założeniami.
2. **W JSON**: `data/recommendations.json` → ticker → `dcf` — wszystkie założenia z uzasadnieniami w polach `note`, źródła danych bilansowych w `balance_sheet_inputs`.
3. **Od źródła**: `dcf.note` → `fundamentals/TICKER` → `source_file` → PDF w `reports/`. Każda liczba powinna mieć tę ścieżkę. (Tam gdzie jej nie ma, jest oznaczenie ESTYMATA.)

### Czego jeszcze brakuje (znane luki)
- Brak automatycznego walidatora: zapisane `fair_value` może rozjechać się z tym, co implikują założenia (przypadki RHM/ETL/IONQ z audytu 12.06). Plan: `tools/validate.py` — patrz sekcja 7.

---

## 5. WYGLĄD I UKŁAD APLIKACJI — mapa app.py

| Sekcja (komentarz w kodzie) | Linie (≈) | Co tu jest |
|------------------------------|-----------|-----------|
| `DESIGN SYSTEM` | 19–268 | **cały wygląd**: kolory (ACCENT zielony #00d9a3, tło, karty), fonty, style tabel, chipów, zakładek (CSS) |
| `CONSTANTS` | 269–283 | mapowanie rekomendacji na kolory/emoji, przykładowy portfel |
| `PORTFOLIO NORMALIZATION` | 284–373 | czytanie arkusza Akcje: tickery, waluty, **logika Bought/Sold** |
| `DATA LOADING` | 374–512 | Google Sheets URL, ceny Yahoo (cache 5 min), FX, recommendations.json (cache po mtime), watchlista |
| `HELPERS` | 513–571 | formatowanie liczb, budowa wierszy pozycji (jakie kolumny ma tabela) |
| `CHART` | 572–611 | wykres ceny z liniami FV (bursztyn) i entry |
| `DCF CALCULATOR` | 612–1207 | **silnik wyliczeń** + rendering zakładki DCF + scenariusze + metody alternatywne |
| `TAB: DZIAŁANIA` | 1208–1312 | karta rekomendacji, "kiedy kupować/wychodzić", oś czasu eventów |
| `PAGE: OVERVIEW` | 1313–1511 | KPI portfela, **priorytety z chipami live**, **kalendarz wydarzeń**, tabela pozycji |
| `PAGE: DETAIL` | 1512–1679 | strona spółki: nagłówek, metryki, 4 zakładki |
| `CHAT...` | 1680–2163 | doradca AI w aplikacji + zapis historii |
| `PAGE: WATCHLISTA` | 2164–2260 | koszyki sektorowe, dodawanie/usuwanie |
| `MAIN` | 2261–2450 | nawigacja, panel FX, przycisk Odśwież, **alerty BUY** (cena ≤ entry), routing stron |

**Jak zmienić wygląd:** wszystko w sekcji DESIGN SYSTEM (np. kolor akcentu = stała `ACCENT`). **Jak zmienić co się wyświetla:** znajdź sekcję z tabeli wyżej, powiedz mi co zmienić.

---

## 6. ZASADY ODŚWIEŻANIA DANYCH

| Co | Jak często |
|----|-----------|
| Ceny akcji, FX | co 5 min (cache), przycisk "Odśwież dane" wymusza |
| Portfel (Sheets) | co 5 min |
| Rekomendacje/wyceny | natychmiast po git push + redeploy (**wymaga odświeżenia karty!**) |
| Chipy priorytetów, kalendarz, alerty | liczone przy każdym renderze z powyższych |

---

## 7. PLAN WZMOCNIENIA (uzgodniony kierunek, status)

1. ⬜ `tools/validate.py` + schemat JSON — automatyczne sprawdzanie: FV zgodne z założeniami, entry = 25% MoS, wagi scenariuszy = 100%, brak placeholderów przy BUY, PV_TV < TV
2. ⬜ Skill `/audyt` — przegląd wszystkich wycen jedną komendą
3. ⬜ Skille `/nowy-raport`, `/wycena` — sformalizowane protokoły z CLAUDE.md
4. ⬜ Agent-weryfikator — niezależne przeliczenie każdej nowej wyceny
5. ⬜ Dopisanie do CLAUDE.md konwencji z sekcji 2 (FV=base, 5+5 lat, entry=0.75×FV)
