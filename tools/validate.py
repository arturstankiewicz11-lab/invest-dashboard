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
  W7  Scenariusze Bear/Base/Bull obowiązkowe przy każdym DCF (Krok F, od 12.06.2026)
  W8  Wyprowadzenie parametrów WACC/g/CAGR ze źródłami (od 13.06.2026)
  W9  Renderowalność modelu w zakładce DCF (stages/alt/scenarios/catalyst; od 13.06.2026)
  W10 Moonshot bez tam_analysis (dyscyplina upside; od 13.06.2026)
  W14 świeże IPO bez ryzyka lock-up (nawis podażowy; od 13.06.2026)
  W13 shares dcf vs fundamentals (anty podwójne-liczenie; od 13.06.2026)
  W12 TAM deklaruje jedną shares_used (anty-mix current/forward; od 13.06.2026)
  W11 Pułapka tagu HTML ('<' + litera w tekście psuje render; od 13.06.2026)
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

    # E5 + W7: scenariusze (obsługa obu formatów: lista i dict)
    scen = dcf.get("scenarios") or (alt.get("scenarios") if has_alt else None)
    if scen:
        items = list(scen.values()) if isinstance(scen, dict) else scen
        s = sum(x.get("probability_pct", 0) for x in items if isinstance(x, dict))
        if abs(s - 100) > 0.5:
            errors.append(f"E5: wagi scenariuszy sumują się do {s}% (≠100%)")
        if len(items) < 3:
            warns.append(f"W7: tylko {len(items)} scenariusze — wymagane min. Bear/Base/Bull (Krok F)")
    elif mode == "DCF":
        # W7: scenariusze Bear/Base/Bull obowiązkowe przy DCF (Krok F, zasada z 2026-06-12)
        warns.append("W7: brak scenariuszy Bear/Base/Bull (Krok F protokołu DCF, wymagane od 12.06.2026)")

    # W13: shares w dcf vs fundamentals (3. raz blad liczby akcji: RHM/CBRS/QNT). Zasada 2026-06-13.
    # Dozwolony rozjazd tylko z nota 'forward'/'diluted' (legit forward-dilution moonshota, np. IONQ).
    dcf_sh = dcf.get("shares_m") or dcf.get("shares_diluted_m")
    fund_t, _ = latest_fundamentals(t)
    if dcf_sh and fund_t:
        fsh = fund_t.get("shares_diluted_m") or (fund_t.get("balance_sheet", {}) or {}).get("shares_diluted_m")
        if fsh and abs(dcf_sh - fsh) / fsh > 0.05:
            blob = (json.dumps(dcf.get("wacc_inputs", {}), ensure_ascii=False)
                    + json.dumps(dcf.get("tam_analysis", {}), ensure_ascii=False)
                    + json.dumps(dcf.get("alt_valuation", {}), ensure_ascii=False)).lower()
            if "forward" not in blob:
                errors.append(f"W13: shares dcf {dcf_sh}M vs fundamentals {fsh}M (>5%) bez noty 'forward diluted' "
                              f"— sprawdź podwójne liczenie (wzorzec RHM/CBRS/QNT)")

    # W12: TAM musi deklarować JEDNĄ liczbę akcji (shares_used) — zapobiega mieszaniu
    # current vs forward-diluted między bridge_cases (bug IONQ 373 vs 420). Zasada 2026-06-13.
    ta12 = dcf.get("tam_analysis")
    if ta12 and ta12.get("bridge_cases"):
        su = ta12.get("shares_used")
        if su is None:
            errors.append("W12: tam_analysis bez 'shares_used' — zadeklaruj jedną liczbę akcji dla wszystkich bridge_cases")
        else:
            canon12 = dcf.get("shares_m") or dcf.get("shares_diluted_m")
            if canon12 and abs(su - canon12) / canon12 > 0.10 and "forward" not in str(ta12.get("note_shares","")).lower():
                warns.append(f"W12: tam shares_used {su}M vs model {canon12:.0f}M (>10%) bez noty 'forward diluted'")

    # W11: pułapka tagu HTML — '<' + litera/slash/! w polach tekstowych psuje render
    # (browser parsuje jako tag; np. '<rok' -> InvalidCharacterError). '<' + cyfra/spacja jest OK.
    import re as _re11
    def _scan_html(o, p=""):
        out=[]
        if isinstance(o,dict):
            for k,vv in o.items(): out+=_scan_html(vv,p+"."+k)
        elif isinstance(o,list):
            for i,vv in enumerate(o): out+=_scan_html(vv,f"{p}[{i}]")
        elif isinstance(o,str):
            if _re11.search(r"<[a-zA-Z/!]", o): out.append(p)
        return out
    bad = _scan_html(r)
    if bad:
        errors.append(f"W11: pułapka tagu HTML ('<' + litera) w polach {bad[:3]} — psuje render (InvalidCharacterError); użyj 'poniżej'/'mniej niż' albo &lt;")

    # W9: renderowalność — czy app pokaże model w zakładce DCF (zasada z 2026-06-13).
    # tab_dcf renderuje, gdy istnieje: stages | alt_valuation | scenarios | catalyst_sensitivity.
    # Model "istnieje" dla walidatora (E1/E2) ≠ "app go wyrenderuje" — to był bug LEU.
    if fv is not None and dcf and not (has_stages or has_alt or has_scen
                                       or dcf.get("catalyst_sensitivity")):
        errors.append("W9: model nierenderowalny — fair_value jest, ale brak stages/alt_valuation/"
                      "scenarios/catalyst (zakładka DCF pokaże 'Brak modelu')")

    # W10: moonshot powinien mieć tam_analysis (dyscyplina upside, zasada z 2026-06-13)
    if r.get("position_type") == "moonshot" and fv is not None and not dcf.get("tam_analysis"):
        warns.append("W10: moonshot bez tam_analysis (warstwa dyscypliny upside — TAM x udział x marża)")

    # W14: świeże IPO musi ujmować ryzyko lock-up (luka wykryta 2026-06-13: XE/QNT bez nawisu).
    # Sygnał WŁASNEGO świeżego IPO = data dzienna przy IPO ("IPO 27.04", "po IPO (21.05.2026)").
    # Wzmianki cudze/historyczne ("IPO OpenAI $1", "od IPO" o zwrocie od 1997) nie mają dd.mm —
    # nie łapane. Gdy jest taki własny-IPO sygnał, wymagaj wzmianki "lock-up" gdzieś w rekomendacji.
    import re as _re14
    _blob = json.dumps(r, ensure_ascii=False)
    if _re14.search(r"IPO\b[^.\n]{0,10}\d{1,2}[.\-/]\d{1,2}", _blob, _re14.I) \
            and not _re14.search(r"lock[\s\-]?up", _blob, _re14.I):
        warns.append("W14: spółka po świeżym IPO bez ryzyka lock-up — dodaj nawis podażowy "
                     "(data ~180 dni od IPO + skala zablokowane vs float) do upcoming_events/risks")

    # W8: wyprowadzenie parametrów DCF ze źródłami (zasada z 2026-06-13)
    if mode == "DCF":
        wi = dcf.get("wacc_inputs") or {}
        if not wi:
            warns.append("W8: brak wacc_inputs — wyprowadzenie WACC obowiązkowe")
        else:
            miss = [k for k in ("rf_pct", "beta", "erp_pct") if k not in wi]
            if miss:
                warns.append(f"W8: wacc_inputs bez pól {miss}")
        if not dcf.get("terminal_growth_rationale"):
            warns.append("W8: brak terminal_growth_rationale (kotwica + wrażliwość ±0.5pp)")
        no_note = [s.get("period", "?") for s in (dcf.get("stages") or []) if not s.get("note")]
        if no_note and not dcf.get("cagr_context"):
            warns.append(f"W8: stages bez uzasadnienia CAGR w note: {no_note}")

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
