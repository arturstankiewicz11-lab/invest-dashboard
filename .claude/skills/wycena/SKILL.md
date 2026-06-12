---
name: wycena
description: Pełna wycena spółki od zera lub pełna rewizja — DCF/metoda alternatywna ze scenariuszami, checklisty Buffetta, profil CEO, mapa konkurencji, zapis do systemu. Użyj gdy użytkownik prosi o analizę/wycenę/DCF spółki ("zrób wycenę X", "przeanalizuj X", "DCF dla X") — inicjacja nowego tickera lub pełna rewizja istniejącego.
---

# /wycena [TICKER] — pełna analiza i wycena

Realizuje protokoły z CLAUDE.md (sekcje 4-7) + konstytucję (sekcja 2). Wynik: kompletny
wpis w recommendations.json + rekomendacja w formacie z sekcji 8.

## Kolejność kroków

1. **Dane źródłowe** (konstytucja pkt 3-6):
   - fundamentals z raportów (`data/fundamentals/`, brak → najpierw /nowy-raport)
   - **foldery badawcze `data/<SEKTOR>/`** (AI, Quantum...) — `ls data/*/`, przeczytaj
     wszystko co dotyczy tickera/sektora (raporty branżowe użytkownika)
   - cena live, market cap, shares — yfinance (NIE z pamięci; cross-check shares vs raport!)
   - fakty rynkowe — web z regułą 2 źródeł; transkrypcje calli (cytat+kontekst+wpływ, sekcja 7)
   - Morningstar FV/moat jako referencja, gdy użytkownik poda lub publicznie dostępne

2. **Wybór metody** (sekcja 5): DCF gdy FCF dodatnie/przewidywalne; inaczej EV/Revenue,
   EV/EBITDA lub scenariusze. Uzasadnij wybór w `method_reason`.

3. **Wycena** (sekcja 4): Krok 0 segmenty (blended CAGR/EBIT z pokazanym działaniem) →
   A-E → **Krok F scenariusze Bear/Base/Bull** (jawne zmiany założeń z uzasadnieniem
   biznesowym, wagi=100%). `fair_value` = Base. Każdy input z `source`+datą.

4. **Checklisty jakościowe** (sekcja 6):
   - Buffett Tenets: ✅/⚠️/❌ × 4 grupy → wniosek o wielkości pozycji i wymaganym MoS
   - `ceo_profile`: CV, głód (archetyp Zuckerberg/Bezos), ekspertyza domenowa, skin in the
     game, werdykt GŁODNY/SYTY × EKSPERT/MENEDŻER
   - `competitive_landscape`: per segment, baza z sekcji Competition 10-K/S-1

5. **Entry i thesis breaker**: entry = 0,75 × FV_base (MoS 30%+ przy wielu ❌ z tenets);
   thesis breaker = konkretne, mierzalne warunki. Przy INICJACJI nowego tickera zapisz
   komplet; przy REWIZJI istniejącego — zmiany rec/entry/breaker tylko jako propozycja
   czekająca na akceptację (pkt 1).

6. **Zapis i kontrola**: pełny wpis do recommendations.json (dcf z wszystkimi polami,
   events — wpis inicjacji/rewizji, upcoming_events — earnings i katalizatory do
   kalendarza) → `python3 tools/validate.py [TICKER]` musi przejść bez ERRORów →
   **agent-weryfikator** (subagent `weryfikator` z TICKEREM; werdykt NIEZGODNA blokuje
   publikację — napraw findings i powtórz) → commit + push → odśwież kartę.

7. **Output dla użytkownika**: format rekomendacji z CLAUDE.md sekcja 8 (teza, tenets,
   CEO, konkurencja, DCF z tabelą, entry, ryzyka, geopolityka, pozycja portfelowa).
   Lead z wnioskiem: FV vs cena vs entry.
