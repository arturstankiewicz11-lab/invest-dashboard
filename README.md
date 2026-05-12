# Invest Dashboard

Personalny dashboard inwestycyjny z live cenami, P&L i rekomendacjami.

## Setup (jednorazowy, ~15 minut)

### Krok 1 — GitHub

1. Wejdź na github.com → zaloguj się
2. Kliknij **"New repository"** → nazwa: `invest-dashboard` → **Public** → Create
3. Pobierz i zainstaluj [GitHub Desktop](https://desktop.github.com/) (najprostszy sposób)
4. W GitHub Desktop: File → Clone Repository → wybierz `invest-dashboard`
5. Skopiuj wszystkie pliki z tego folderu do sklonowanego repozytorium
6. GitHub Desktop: "Commit to main" → "Push origin"

### Krok 2 — Google Sheets (Twoje pozycje)

1. Otwórz [ten link](https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms/copy) lub stwórz nowy arkusz
2. Wypełnij kolumny: `Ticker | Nazwa | Ilosc | Srednia_cena | Waluta`
   - Przykład wiersza: `MSFT | Microsoft | 10 | 380.00 | USD`
3. Plik → **Udostępnij** → Każdy z linkiem może **wyświetlać**
4. Plik → Pobierz → Wartości rozdzielone przecinkami (.csv) — **NIE** — zamiast tego:
5. Z paska adresu skopiuj ID arkusza (część między `/d/` a `/edit`)
6. Zbuduj URL: `https://docs.google.com/spreadsheets/d/TWOJE_ID/export?format=csv&gid=0`

### Krok 3 — Streamlit Cloud

1. Wejdź na [share.streamlit.io](https://share.streamlit.io)
2. Zaloguj się przez GitHub
3. **New app** → wybierz repozytorium `invest-dashboard` → Branch: `main` → File: `app.py`
4. **Advanced settings** → Secrets → wklej:

```toml
[gsheets]
portfolio_url = "https://docs.google.com/spreadsheets/d/TWOJE_ID/export?format=csv&gid=0"
```

5. **Deploy** → za 2-3 minuty masz link działający na każdym urządzeniu!

---

## Struktura kolumn Google Sheets

| Kolumna | Opis | Przykład |
|---|---|---|
| Ticker | Symbol giełdowy (yfinance format) | MSFT, RHM.DE, BTC-USD, PZU.WA, 0700.HK |
| Nazwa | Twoja nazwa | Microsoft |
| Ilosc | Liczba akcji/jednostek | 10 |
| Srednia_cena | Średnia cena zakupu (w walucie z kolumny Waluta) | 380.50 |
| Waluta | Waluta zakupu | USD, EUR, PLN, HKD |

## Aktualizowanie rekomendacji

Plik `data/recommendations.json` jest aktualizowany przez Claude przy każdej analizie.
Po aktualizacji: commit → push na GitHub → Streamlit automatycznie odświeży.

## Lokalne uruchomienie (opcjonalne)

```bash
pip install -r requirements.txt
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# uzupełnij secrets.toml swoim URL
streamlit run app.py
```
