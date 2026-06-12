---
name: audyt
description: Pełny audyt wszystkich wycen w systemie — walidator + ceny live + spójność rekomendacji z cenami + świeżość analiz + nadchodzące wydarzenia. Użyj gdy użytkownik chce przegląd stanu wycen, sprawdzenie spójności, albo pyta "co wymaga uwagi". Read-only: niczego nie zmienia.
---

# /audyt — przegląd stanu wszystkich wycen

Audyt jest READ-ONLY: raportuje, niczego nie zmienia. Propozycje napraw wymagają osobnej
decyzji użytkownika (konstytucja pkt 1 w CLAUDE.md).

## Kroki

1. **Walidator**: `python3 tools/validate.py` — pełny przebieg. Zbierz błędy i ostrzeżenia.

2. **Ceny live**: pobierz przez yfinance (`fast_info.last_price`) dla wszystkich tickerów
   z `fair_value` w recommendations.json + wszystkich pozycji portfela.

3. **Spójność cena ↔ rekomendacja ↔ entry**, per ticker:
   - BUY z ceną ≤ entry → "BUY aktywny" (OK, wyróżnij jako okazję)
   - BUY z ceną > FV → ❌ niespójność (kupowanie powyżej wartości)
   - HOLD/pozycja z ceną > 1.3×FV → ⚠️ rozważ propozycję REDUCE (tylko propozycja!)
   - Pozycja z P&L < −20% → sprawdź thesis breaker (czy któryś warunek blisko aktywacji)

4. **Świeżość**: `last_updated` > 60 dni przy aktywnej pozycji → do rewizji;
   eventy w `upcoming_events` w ciągu 14 dni → wyróżnij ("decyzja zbliża się").

5. **Placeholdery**: fundamentals z `source_file: null` → lista "do zastąpienia raportem".

## Format wyniku

Jedna tabela zbiorcza: Ticker | Rec | Cena | FV | Entry | Status (✅/⚠️/❌ + powód).
Potem trzy krótkie listy: (1) wymaga działania teraz, (2) do rewizji przy earnings,
(3) backlog znany. Liczby z narzędzi, nie z pamięci (konstytucja pkt 3).
