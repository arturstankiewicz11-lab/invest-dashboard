#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Walidator spójności wycen — egzekwuje zasady z CLAUDE.md (konstytucja, sekcja 2).

Użycie:  python3 tools/validate.py [TICKER]
         (bez argumentu: wszystkie tickery; exit code 1 gdy są błędy)

Sprawdza:
  E1  FV zgodne z modelem: stages → przeliczenie (logika identyczna z app.py
      compute_dcf_stages + TV + bridge) vs fair_value (±3% OK, 3-10% WARN, >10% ERROR);
      metody alternatywne/scenariuszowe: fair_value vs fair_value_computed/weighted
  E2  FV bez jakiegokolwiek modelu (dcf.stages / alt_valuation / scenarios) = ERROR
  E3  Schemat stages kompatybilny z aplikacją (rev_cagr_pct wymagane!)
  E4  Sanity: PV_TV < TV (sfabrykowany bridge = ERROR)
  E5  Wagi scenariuszy sumują się do 100%
  E6  BUY oparte na placeholderze fundamentals (source_file null) = ERROR
  W1  Entry ≈ 0.75 × FV (konwencja MoS 25%; odchylenie >10% = WARN)
  W2  thesis_breaker obecny przy każdej rekomendacji z FV
  W3  net_debt w dcf vs najnowsze fundamentals (>15% różnicy = WARN)
  W4  Daty w upcoming_events/next_earnings parsowalne (YYYY-MM-DD)
  W5  "ESTYMATA" w inputach przy rekomendacji BUY
  W6  last_updated starsze niż 90 dni = WARN (świeżość)
"""
import json, os, re, sys
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REC_PATH  = os.path.join(ROOT, "data", "recommendations.json")
FUND_DIR  = os.path.join(ROOT, "data", "fundamentals")

TOL_OK, TOL_WARN = 0.03, 0.10   # progi zgodności FV z modelem


def implied_fv_from_stages(dcf):
    """Replikacja logiki app.py: compute_dcf_stages + TV + bridge. Zwraca FV lub (None, powód)."""
    try:
        wacc = dcf["wacc_pct"] / 100.0
        g    = dcf["terminal_growth_pct"] / 100.0
        rev  = dcf.get("revenue_ttm_m") or dcf.get("revenue_base_fy2026e_m") or dcf.get("base_revenue_m")
        if rev is None:
            return None, "brak bazy revenue (revenue_ttm_m / revenue_base_fy2026e_m / base_revenue_m)"
        if wacc <= g:
            return None, f"WACC ({wacc:.1%}) <= g ({g:.1%}) — TV niepoliczalne"
        pv, year, last_fcf = 0.0, 0, 0.0
        for st in dcf["stages"]:
            m = re.search(r"(\d{4})[–\-](\d{4})", str(st.get("period", "")))
            n = st.get("n_years") or (int(m.group(2)) - int(m.group(1)) + 1 if m else 5)
            if "rev_cagr_pct" not in st:
                return None, "stage bez rev_cagr_pct (wymagane przez app.py)"
            cagr = st["rev_cagr_pct"] / 100.0
            full = all(k in st for k in ("ebit_margin_pct", "tax_pct", "capex_pct", "da_pct"))
            for _ in range(int(n)):
                year += 1
                rev *= (1 + cagr)
                if full:
                    fcf = (rev * st["ebit_margin_pct"] / 100.0 * (1 - st["tax_pct"] / 100.0)
                           + rev * st["da_pct"] / 100.0 - rev * st["capex_pct"] / 100.0)
                elif "fcf_margin_pct" in st:
                    fcf = rev * st["fcf_margin_pct"] / 100.0
                else:
                    return None, "stage bez kompletu EBIT/tax/capex/da ani fcf_margin_pct"
                pv += fcf / (1 + wacc) ** year
                last_fcf = fcf
        tv    = last_fcf * (1 + g) / (wacc - g)
        pv_tv = tv / (1 + wacc) ** year
        net_cash = -(dcf.get("net_debt_m") or 0) or dcf.get("net_cash_m", 0)
        shares = dcf.get("shares_m") or dcf.get("shares_diluted_m")
        if not shares:
            return None, "brak shares_m"
        fv = (pv + pv_tv + net_cash) / shares
        # udokumentowane aktywa nieoperacyjne (np. stake OpenAI w MSFT)
        stake = (dcf.get("openai_stake") or {}).get("per_share_after_tax_haircut")
        if stake:
            fv += stake
        return fv, None
    except Exception as e:
        return None, f"wyjątek przy przeliczaniu: {e}"


def latest_fundamentals(ticker):
    d = os.path.join(FUND_DIR, ticker)
    if not os.path.isdir(d):
        return None, None
    best, best_key = None, ""
    for f in os.listdir(d):
        if not f.endswith(".json"):
            continue
        try:
            data = json.load(open(os.path.join(d, f)))
        except Exception:
            continue
        key = str(data.get("period_end") or data.get("extracted") or "")
        if key >= best_key:
            best, best_key = data, key
    return best, best_key


def check_ticker(t, r):
    errors, warns = [], []
    fv  = r.get("fair_value")
    rec = r.get("recommendation", "")
    dcf = r.get("dcf") or {}

    # ETF/krypto: brak FV i brak modelu = tylko tracking, pomijamy
    if fv is None and not dcf:
        return [], [], "tracking-only (bez FV — OK dla ETF/krypto)"

    # W2: thesis breaker
    if fv is not None and not r.get("thesis_breaker"):
        errors.append("brak thesis_breaker (konstytucja pkt 8)")

    # E2/E1: model i zgodność FV
    has_stages = bool(dcf.get("stages"))
    alt = dcf.get("alt_valuation") or {}
    has_alt = bool(alt)
    has_scen = bool(dcf.get("scenarios"))
    mode = None
    if has_stages:
        mode = "DCF"
        implied, why = implied_fv_from_stages(dcf)
        if implied is None:
            errors.append(f"E3: model nieprzeliczalny — {why}")
        elif fv:
            diff = abs(implied - fv) / fv
            if diff > TOL_WARN:
                errors.append(f"E1: FV {fv} vs model {implied:.0f} (różnica {diff:.0%}) — model nie potwierdza FV")
            elif diff > TOL_OK:
                warns.append(f"FV {fv} vs model {implied:.0f} (różnica {diff:.1%})")
    elif has_alt or has_scen:
        mode = "ALT/SCEN"
        ref = (alt.get("fair_value_computed")
               or dcf.get("fair_value_weighted")
               or dcf.get("weighted_fv")
               or dcf.get("fair_value_computed"))
        if ref is None:
            errors.append("E2: metoda alternatywna bez fair_value_computed/weighted")
        elif fv:
            diff = abs(ref - fv) / fv
            if diff > TOL_WARN:
                errors.append(f"E1: FV {fv} vs metoda {ref} (różnica {diff:.0%})")
            elif diff > TOL_OK:
                warns.append(f"FV {fv} vs metoda {ref} (różnica {diff:.1%})")
    elif fv is not None:
        errors.append("E2: fair_value bez żadnego modelu (stages/alt_valuation/scenarios) — konstytucja pkt 2")

    # E4: sanity bridge
    tv_s, pv_tv_s = dcf.get("terminal_value_m"), dcf.get("pv_terminal_m")
    if tv_s and pv_tv_s and pv_tv_s >= tv_s:
        errors.append(f"E4: PV_TV ({pv_tv_s:,.0f}) >= TV ({tv_s:,.0f}) — matematycznie niemożliwe, bridge sfabrykowany")

    # E5: wagi scenariuszy (obsługa obu formatów: lista i dict)
    scen = dcf.get("scenarios") or (alt.get("scenarios") if has_alt else None)
    if scen:
        items = list(scen.values()) if isinstance(scen, dict) else scen
        s = sum(x.get("probability_pct", 0) for x in items if isinstance(x, dict))
        if abs(s - 100) > 0.5:
            errors.append(f"E5: wagi scenariuszy sumują się do {s}% (≠100%)")

    # W1: entry vs konwencja 0.75×FV
    ep = r.get("entry_point")
    if fv and ep:
        target = 0.75 * fv
        dev = abs(ep - target) / target
        if ep > fv:
            errors.append(f"entry {ep} > FV {fv} — odwrotność margin of safety")
        elif dev > 0.10:
            warns.append(f"entry {ep} vs konwencja 0.75×FV={target:.0f} (odchylenie {dev:.0%})")

    # E6/W5: placeholder fundamentals i ESTYMATY przy BUY
    fund, _ = latest_fundamentals(t)
    if rec == "BUY":
        if fund and fund.get("source_file") in (None, ""):
            errors.append("E6: BUY oparte na placeholderze fundamentals (source_file=null) — konstytucja pkt 5")
        blob = json.dumps(dcf, ensure_ascii=False)
        if "ESTYMATA" in blob.upper():
            warns.append("BUY z ESTYMATAMI w inputach modelu — do weryfikacji z dokumentów")

    # W3: net debt dcf vs fundamentals
    if fund and dcf.get("net_debt_m") is not None and fund.get("net_debt_m") is not None:
        a, b = dcf["net_debt_m"], fund["net_debt_m"]
        base = max(abs(a), abs(b))
        if base > 0 and abs(a - b) / base > 0.15:
            warns.append(f"net_debt dcf ({a:,.0f}) vs fundamentals ({b:,.0f}) — rozjazd >15% (różne daty bilansu?)")

    # W4: daty
    for ev in (r.get("upcoming_events") or []):
        try:
            datetime.strptime(str(ev.get("date", "")), "%Y-%m-%d")
        except ValueError:
            warns.append(f"upcoming_events: nieparsowalna data '{ev.get('date')}'")
    ne = r.get("next_earnings")
    if ne and "X" not in str(ne):
        try:
            datetime.strptime(str(ne), "%Y-%m-%d")
        except ValueError:
            warns.append(f"next_earnings nieparsowalne: '{ne}'")

    # W6: świeżość
    lu = r.get("last_updated")
    if lu and fv is not None:
        try:
            age = (date.today() - datetime.strptime(lu, "%Y-%m-%d").date()).days
            if age > 90:
                warns.append(f"analiza sprzed {age} dni — wymaga rewizji")
        except ValueError:
            warns.append(f"last_updated nieparsowalne: '{lu}'")

    return errors, warns, mode or "?"


def main():
    data = json.load(open(REC_PATH, encoding="utf-8"))
    only = sys.argv[1].upper() if len(sys.argv) > 1 else None
    n_err = n_warn = 0
    for t, r in data.items():
        if only and t.upper() != only:
            continue
        errors, warns, mode = check_ticker(t, r)
        n_err += len(errors); n_warn += len(warns)
        if errors:
            print(f"❌ {t} [{mode}]")
            for e in errors: print(f"     ERROR: {e}")
            for w in warns:  print(f"     warn:  {w}")
        elif warns:
            print(f"⚠️  {t} [{mode}]")
            for w in warns:  print(f"     warn:  {w}")
        else:
            print(f"✅ {t} [{mode}]")
    print(f"\n— Podsumowanie: {n_err} błędów, {n_warn} ostrzeżeń —")
    sys.exit(1 if n_err else 0)


if __name__ == "__main__":
    main()
