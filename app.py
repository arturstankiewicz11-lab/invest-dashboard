import streamlit as st
import streamlit.components.v1 as components
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import io
import math
from datetime import datetime
import anthropic

st.set_page_config(
    page_title="Invest Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── DESIGN SYSTEM ───────────────────────────────────────────────────────────
ACCENT  = "#00d9a3"   # Revolut green
BG      = "#0d0e1c"
CARD    = "rgba(255,255,255,0.03)"
BORDER  = "rgba(255,255,255,0.07)"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

html, body, [data-testid="stAppViewContainer"] {{
    font-family: 'Inter', sans-serif !important;
    background-color: {BG} !important;
    color: #e2e8f0 !important;
}}

[data-testid="stAppViewContainer"]::before {{
    content: '';
    position: fixed; inset: 0;
    background-image: radial-gradient(rgba(0,217,163,0.05) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none; z-index: 0;
}}
[data-testid="stMainBlockContainer"] {{ position: relative; z-index: 1; }}

[data-testid="stSidebar"] {{
    background: rgba(10,11,25,0.97) !important;
    border-right: 1px solid rgba(255,255,255,0.05) !important;
    backdrop-filter: blur(20px);
}}

#MainMenu, footer {{ visibility: hidden; }}
header {{ visibility: hidden; height: 0 !important; min-height: 0 !important; }}
[data-testid="stDecoration"] {{ display: none; }}
[data-testid="stSidebarCollapsedControl"] {{ visibility: visible !important; height: auto !important; }}

/* ── TABS ── */
[data-testid="stTabs"] > div:first-child {{
    border-bottom: 1px solid rgba(255,255,255,0.07) !important;
    gap: 4px;
}}
button[data-baseweb="tab"] {{
    background: transparent !important;
    color: #64748b !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    font-family: 'Inter', sans-serif !important;
    border: none !important;
    border-radius: 8px 8px 0 0 !important;
    padding: 10px 20px !important;
    transition: all .15s;
}}
button[data-baseweb="tab"]:hover {{ color: #e2e8f0 !important; }}
button[data-baseweb="tab"][aria-selected="true"] {{
    color: {ACCENT} !important;
    border-bottom: 2px solid {ACCENT} !important;
    background: rgba(0,217,163,0.04) !important;
}}

/* ── KPI CARDS ── */
.kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }}
.kpi {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 16px; padding: 24px;
    position: relative; overflow: hidden; transition: border-color .2s;
}}
.kpi::before {{
    content: ''; position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0,217,163,0.4), transparent);
}}
.kpi:hover {{ border-color: rgba(0,217,163,0.25); }}
.kpi-icon {{ font-size: 22px; margin-bottom: 12px; }}
.kpi-label {{ font-size: 11px; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }}
.kpi-value {{ font-size: 28px; font-weight: 700; color: #f8fafc; letter-spacing: -0.5px; margin-bottom: 6px; }}
.kpi-sub {{ font-size: 13px; font-weight: 500; }}
.pos {{ color: #10b981; }} .neg {{ color: #ef4444; }} .neu {{ color: #64748b; }}

/* ── SECTION HEADER ── */
.sh {{
    display: flex; align-items: center; gap: 10px;
    margin: 28px 0 14px;
    font-size: 10px; font-weight: 600; color: #475569;
    text-transform: uppercase; letter-spacing: 2px;
}}
.sh::after {{ content: ''; flex: 1; height: 1px; background: linear-gradient(90deg, rgba(255,255,255,0.06), transparent); }}

/* ── BADGES ── */
.badge {{
    display: inline-block; border-radius: 6px;
    padding: 3px 10px; font-size: 10px; font-weight: 700;
    letter-spacing: 0.8px; text-transform: uppercase;
}}
.b-BUY    {{ background: rgba(16,185,129,0.15);  color: #10b981; border: 1px solid rgba(16,185,129,0.3); }}
.b-HOLD   {{ background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }}
.b-SELL   {{ background: rgba(239,68,68,0.15);   color: #ef4444; border: 1px solid rgba(239,68,68,0.3); }}
.b-REDUCE {{ background: rgba(245,158,11,0.15);  color: #f59e0b; border: 1px solid rgba(245,158,11,0.3); }}

/* ── ACTION CARDS ── */
.actions {{ display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }}
.action {{
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px; border-radius: 12px;
    font-size: 14px; font-weight: 500; border: 1px solid transparent;
}}
.a-sell {{ background: rgba(239,68,68,0.08);  border-color: rgba(239,68,68,0.2);  color: #fca5a5; }}
.a-buy  {{ background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.2); color: #6ee7b7; }}
.a-warn {{ background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.2); color: #fcd34d; }}
.a-neu  {{ background: rgba(100,116,139,0.08); border-color: rgba(100,116,139,0.2); color: #94a3b8; }}
.action-ticker {{ font-weight: 700; font-size: 13px; }}
.action-dot {{ width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }}
.dot-sell {{ background: #ef4444; box-shadow: 0 0 8px #ef4444; }}
.dot-buy  {{ background: #10b981; box-shadow: 0 0 8px #10b981; }}
.dot-warn {{ background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }}
.dot-neu  {{ background: #64748b; }}

/* ── POSITIONS TABLE ── */
.pos-table-wrap {{ overflow-x: auto; border-radius: 16px; border: 1px solid {BORDER}; }}
.pos-table {{ width: 100%; border-collapse: collapse; font-size: 11px; font-family: 'Inter', sans-serif; table-layout: fixed; }}
.pos-table thead th {{
    background: rgba(255,255,255,0.02); color: #475569;
    font-size: 9px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px;
    padding: 8px 8px; text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.06); white-space: nowrap;
}}
.pos-table tbody tr {{ border-bottom: 1px solid rgba(255,255,255,0.03); transition: background .15s; }}
.pos-table tbody tr:last-child {{ border-bottom: none; }}
.pos-table tbody tr:hover {{ background: rgba(255,255,255,0.025); }}
.pos-table td {{ padding: 7px 8px; color: #cbd5e1; vertical-align: middle; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.t-ticker {{ font-weight: 700; font-size: 12px; color: #f1f5f9; letter-spacing: 0.3px; }}
.t-name   {{ color: #94a3b8; font-size: 11px; max-width: 100px; overflow: hidden; text-overflow: ellipsis; display: block; }}
.t-price  {{ font-weight: 600; color: #f1f5f9; font-size: 11px; }}
.t-ccy    {{ color: #475569; font-size: 10px; }}
.t-pos    {{ color: #10b981; font-weight: 600; }} .t-neg {{ color: #ef4444; font-weight: 600; }}
.t-neu    {{ color: #64748b; }} .t-fv {{ color: #94a3b8; }}
.row-buy    td:first-child {{ border-left: 3px solid #10b981; }}
.row-sell   td:first-child {{ border-left: 3px solid #ef4444; }}
.row-reduce td:first-child {{ border-left: 3px solid #f59e0b; }}
.row-hold   td:first-child {{ border-left: 3px solid #334155; }}

/* ── DETAIL CARDS ── */
.detail-grid {{ display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 28px; }}
.dcard {{
    background: {CARD}; border: 1px solid {BORDER};
    border-radius: 14px; padding: 20px;
}}
.dcard-label {{ font-size: 10px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }}
.dcard-value {{ font-size: 22px; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }}
.dcard-sub   {{ font-size: 12px; }}

/* ── DCF TABLE ── */
.dcf-table {{ width: 100%; border-collapse: collapse; font-size: 12px; font-family: 'Inter', sans-serif; }}
.dcf-table th {{
    background: rgba(0,217,163,0.05); color: #00d9a3;
    font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.2px;
    padding: 10px 14px; text-align: right; border-bottom: 1px solid rgba(0,217,163,0.15);
}}
.dcf-table th:first-child {{ text-align: left; }}
.dcf-table td {{
    padding: 10px 14px; color: #94a3b8; text-align: right;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}}
.dcf-table td:first-child {{ color: #e2e8f0; font-weight: 500; text-align: left; }}
.dcf-table tr:last-child td {{ border-bottom: none; }}
.dcf-table tr:hover td {{ background: rgba(255,255,255,0.02); }}
.dcf-table .total td {{ color: #00d9a3 !important; font-weight: 700; border-top: 1px solid rgba(0,217,163,0.2); }}

.dcf-bridge {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
    padding: 20px; margin-top: 16px;
}}
.dcf-row {{
    display: flex; justify-content: space-between; align-items: center;
    padding: 8px 0; border-bottom: 1px solid rgba(255,255,255,0.04);
    font-size: 13px;
}}
.dcf-row:last-child {{ border-bottom: none; }}
.dcf-row-label {{ color: #94a3b8; }}
.dcf-row-value {{ color: #e2e8f0; font-weight: 600; }}
.dcf-row-total {{ color: #00d9a3; font-size: 16px; font-weight: 700; }}

.metric-card {{
    background: rgba(0,217,163,0.05);
    border: 1px solid rgba(0,217,163,0.15);
    border-radius: 12px; padding: 16px 20px;
    display: flex; flex-direction: column; gap: 4px;
}}
.metric-label {{ font-size: 10px; font-weight: 600; color: #00d9a3; text-transform: uppercase; letter-spacing: 1.2px; }}
.metric-value {{ font-size: 20px; font-weight: 700; color: #f8fafc; }}
.metric-sub {{ font-size: 11px; color: #64748b; }}

/* ── EVENTS TIMELINE ── */
.event-item {{
    display: flex; gap: 16px; padding: 14px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}}
.event-item:last-child {{ border-bottom: none; }}
.event-dot-wrap {{ display: flex; flex-direction: column; align-items: center; gap: 0; padding-top: 3px; }}
.event-dot {{ width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }}
.event-line {{ width: 1px; flex: 1; background: rgba(255,255,255,0.06); min-height: 20px; margin-top: 4px; }}
.ev-pos {{ background: #10b981; box-shadow: 0 0 6px rgba(16,185,129,0.5); }}
.ev-neg {{ background: #ef4444; box-shadow: 0 0 6px rgba(239,68,68,0.5); }}
.ev-neu {{ background: #64748b; }}
.event-body {{ flex: 1; }}
.event-date {{ font-size: 11px; color: #475569; font-weight: 600; margin-bottom: 3px; }}
.event-text {{ font-size: 13px; color: #cbd5e1; line-height: 1.5; margin-bottom: 6px; }}
.event-fv   {{ font-size: 12px; color: #64748b; background: rgba(255,255,255,0.03); padding: 6px 10px; border-radius: 6px; border-left: 2px solid rgba(255,255,255,0.1); }}

/* ── THESIS ── */
.thesis-card {{
    background: {CARD}; border: 1px solid {BORDER};
    border-radius: 14px; padding: 20px; line-height: 1.75;
    color: #94a3b8; font-size: 14px;
}}
.breaker-card {{
    background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.15);
    border-radius: 14px; padding: 18px; margin-top: 12px;
}}
.moat-card {{
    background: rgba(0,217,163,0.04); border: 1px solid rgba(0,217,163,0.12);
    border-radius: 14px; padding: 18px; margin-top: 12px;
}}
.risk-item {{
    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px; padding: 10px 14px; font-size: 13px; color: #94a3b8; margin-bottom: 8px;
}}

/* ── TRIGGER CARD ── */
.trigger-section {{ margin-bottom: 20px; }}
.trigger-header {{ font-size: 10px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }}
.trigger-item {{
    display: flex; align-items: flex-start; gap: 10px;
    padding: 10px 14px; border-radius: 10px; margin-bottom: 6px; font-size: 13px;
}}
.ti-buy  {{ background: rgba(16,185,129,0.06);  border: 1px solid rgba(16,185,129,0.15); color: #6ee7b7; }}
.ti-sell {{ background: rgba(239,68,68,0.06);   border: 1px solid rgba(239,68,68,0.15);  color: #fca5a5; }}
.ti-hold {{ background: rgba(100,116,139,0.06); border: 1px solid rgba(100,116,139,0.15); color: #94a3b8; }}
.ti-icon {{ font-size: 14px; margin-top: 1px; flex-shrink: 0; }}

/* Demo banner */
.demo-banner {{
    background: rgba(0,217,163,0.06); border: 1px solid rgba(0,217,163,0.2);
    border-radius: 12px; padding: 14px 18px; font-size: 13px; color: #5eead4;
    margin-bottom: 24px; display: flex; align-items: center; gap: 10px;
}}
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
SAMPLE_CSV = """Ticker,Nazwa,Ilosc,Srednia_cena,Waluta
MSFT,Microsoft,0,0,USD
ETL.PA,Eutelsat,0,0,EUR
RHM.DE,Rheinmetall,0,0,EUR
BTC-USD,Bitcoin,0,0,USD
PZU.WA,PZU,0,0,PLN
0700.HK,Tencent,0,0,HKD"""

REC_ORDER  = {"SELL": 0, "REDUCE": 1, "BUY": 2, "HOLD": 3}
REC_DOT    = {"BUY": "dot-buy", "SELL": "dot-sell", "REDUCE": "dot-warn", "HOLD": "dot-neu"}
REC_ACTION = {"BUY": "a-buy",   "SELL": "a-sell",   "REDUCE": "a-warn",   "HOLD": "a-neu"}
REC_ROW    = {"BUY": "row-buy", "SELL": "row-sell",  "REDUCE": "row-reduce","HOLD": "row-hold"}
REC_EMOJI  = {"BUY": "🟢", "SELL": "🔴", "REDUCE": "🟠", "HOLD": "⚪"}

# ─── PORTFOLIO NORMALIZATION ──────────────────────────────────────────────────
NAME_TO_TICKER = {
    "nvidia": "NVDA", "microsoft": "MSFT", "eutelsat": "ETL.PA",
    "rheinmetal": "RHM.DE", "rheinmetall": "RHM.DE",
    "btc": "BTC-USD", "eth": "ETH-USD", "ethereum": "ETH-USD",
    "pzu": "PZU.WA", "tencent": "0700.HK",
}
ETF_MAP = {
    "SXRV": "SXRV.DE", "SECO": "SEMI.L", "2B76": "2B76.DE",
    "2B78": "2B78.DE", "SXR8": "SXR8.DE", "IS3N": "IS3N.DE", "EUNA": "EUNA.DE",
    "ETL": "ETL.PA", "RHM": "RHM.DE", "PZU": "PZU.WA",
    "ORA": "ORA.PA",
    "BTC": "BTC-USD", "ETH": "ETH-USD", "700": "0700.HK",
}
CCY_MAP = {
    "dolar": "USD", "dollar": "USD", "usd": "USD",
    "euro": "EUR", "eur": "EUR",
    "pln": "PLN", "zł": "PLN", "hkd": "HKD",
    "gbp": "GBP", "funt": "GBP", "pound": "GBP",
    "dolar hk": "HKD", "hk": "HKD",
}

def _e(s):
    """Escape HTML special characters in text content."""
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

def to_float(v):
    s = str(v).strip().replace("\xa0", "").replace(" ", "")
    if "," in s and "." in s:
        s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except Exception:
        return 0.0

def normalize_portfolio(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        cl = col.strip().lower()
        if cl == "nazwa":      rename[col] = "Nazwa"
        elif cl == "ticker":   rename[col] = "Ticker_raw"
        elif cl == "waluta":   rename[col] = "Waluta"
        elif cl == "volume":   rename[col] = "Ilosc"
        elif cl == "price":    rename[col] = "Srednia_cena"
        elif cl == "instrument": rename[col] = "Instrument"
        elif cl == "status":   rename[col] = "Status"
    df = df.rename(columns=rename)

    def resolve_ticker(row):
        raw = str(row.get("Ticker_raw", "")).strip()
        if raw and raw.lower() not in ("nan", ""):
            return ETF_MAP.get(raw, raw)
        name = str(row.get("Nazwa", "")).strip().lower()
        for key, val in NAME_TO_TICKER.items():
            if key in name:
                return val
        return ""

    df["Ticker"] = df.apply(resolve_ticker, axis=1)
    df["Waluta"] = df["Waluta"].apply(
        lambda x: CCY_MAP.get(str(x).strip().lower(), str(x).strip().upper()))
    df["Ilosc"]        = df["Ilosc"].apply(to_float)
    df["Srednia_cena"] = df["Srednia_cena"].apply(to_float)
    # Status: Bought = pozycja kupiona, Sold = sprzedana (odejmowana od wolumenu).
    # Brak kolumny lub pusta wartość traktowane jak Bought (kompatybilność wstecz).
    if "Status" in df.columns:
        df["Status"] = df["Status"].apply(
            lambda x: "Sold" if str(x).strip().lower() == "sold" else "Bought")
    else:
        df["Status"] = "Bought"
    df = df[df["Ticker"].notna() & (df["Ticker"] != "") & (df["Ilosc"] > 0)].copy()
    INSTR_SORT = {"Shares": 0, "ETF": 1, "Crypto": 2}
    rows = []
    for (ticker, ccy), g in df.groupby(["Ticker", "Waluta"]):
        bought = g[g["Status"] == "Bought"]
        sold   = g[g["Status"] == "Sold"]
        vol    = bought["Ilosc"].sum() - sold["Ilosc"].sum()
        if vol <= 0:
            continue  # pozycja w całości sprzedana — nie pokazuj w aplikacji
        bvol  = bought["Ilosc"].sum()
        wavg  = (bought["Ilosc"] * bought["Srednia_cena"]).sum() / bvol if bvol > 0 else 0
        instr = g["Instrument"].iloc[0] if "Instrument" in g.columns else "Shares"
        rows.append({"Ticker": ticker, "Nazwa": g["Nazwa"].iloc[0],
                     "Ilosc": vol, "Srednia_cena": wavg, "Waluta": ccy,
                     "Instrument": instr,
                     "Instr_sort": INSTR_SORT.get(instr, 1)})
    return pd.DataFrame(rows)

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1TpTWtiHNK5brEKr0EJHMr8lumDNDviOGpEiJ-bpVAlA/export?format=csv&gid=0"

@st.cache_data(ttl=300)
def load_portfolio():
    try:
        url = st.secrets.get("gsheets", {}).get("portfolio_url", SHEETS_URL)
    except Exception:
        url = SHEETS_URL
    try:
        raw = pd.read_csv(url)
        return normalize_portfolio(raw), False
    except Exception as e:
        st.warning(f"⚠️ Błąd ładowania danych: {e}")
        return pd.read_csv(io.StringIO(SAMPLE_CSV)), True

@st.cache_data(ttl=300)
def get_live_prices(tickers: tuple) -> dict:
    result = {t: {"price": None, "change_pct": None} for t in tickers}
    if not tickers:
        return result
    # fast_info gives the latest traded price (intraday), not just yesterday's close
    for ticker in tickers:
        try:
            fi = yf.Ticker(ticker).fast_info
            curr = float(fi.last_price)
            prev = float(fi.previous_close)
            if not math.isnan(curr):
                chg = (curr - prev) / prev * 100 if prev and not math.isnan(prev) else 0.0
                result[ticker] = {"price": curr, "change_pct": chg}
        except Exception:
            pass
    # fallback to daily download for any ticker that fast_info couldn't resolve
    missing = [t for t in tickers if result[t]["price"] is None]
    if missing:
        try:
            raw = yf.download(missing, period="10d", auto_adjust=True,
                              progress=False, threads=True)
            if isinstance(raw.columns, pd.MultiIndex):
                close_df = raw["Close"]
            else:
                close_df = raw[["Close"]].rename(columns={"Close": missing[0]})
            for ticker in missing:
                try:
                    close = close_df[ticker].dropna() if ticker in close_df.columns else pd.Series(dtype=float)
                    if len(close) >= 2:
                        prev, curr = float(close.iloc[-2]), float(close.iloc[-1])
                        result[ticker] = {"price": curr, "change_pct": (curr - prev) / prev * 100}
                    elif len(close) == 1:
                        result[ticker] = {"price": float(close.iloc[0]), "change_pct": 0.0}
                except Exception:
                    pass
        except Exception:
            pass
    # NaN guard
    for t, p in result.items():
        if isinstance(p["price"], float) and math.isnan(p["price"]):
            result[t]["price"] = None
        if isinstance(p.get("change_pct"), float) and math.isnan(p["change_pct"]):
            result[t]["change_pct"] = None
    return result

@st.cache_data(ttl=1800)
def get_fx() -> dict:
    rates  = {"PLN": 1.0}
    fallback = {"USD": 3.63, "EUR": 4.25, "HKD": 0.46, "GBP": 4.90}
    symbols  = {"USD": "USDPLN=X", "EUR": "EURPLN=X", "HKD": "HKDPLN=X", "GBP": "GBPPLN=X"}
    try:
        raw = yf.download(list(symbols.values()), period="5d", auto_adjust=True,
                          progress=False, threads=True)
        close_df = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw[["Close"]]
        for ccy, sym in symbols.items():
            try:
                col = close_df[sym].dropna()
                rates[ccy] = float(col.iloc[-1]) if not col.empty else fallback[ccy]
            except Exception:
                rates[ccy] = fallback[ccy]
    except Exception:
        rates.update(fallback)
    return rates

@st.cache_data(ttl=3600)
def get_market_caps(tickers: tuple) -> dict:
    from concurrent.futures import ThreadPoolExecutor, as_completed
    result = {t: None for t in tickers}
    if not tickers:
        return result
    def _fetch(t):
        try:
            mc = yf.Ticker(t).fast_info.market_cap
            return t, (mc if mc and not math.isnan(float(mc)) else None)
        except Exception:
            return t, None
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(_fetch, t): t for t in tickers}
        for fut in as_completed(futures, timeout=25):
            try:
                t, mc = fut.result(timeout=5)
                result[t] = mc
            except Exception:
                pass
    return result

@st.cache_data
def load_recs(_mtime: float = 0) -> dict:
    try:
        with open("data/recommendations.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _recs_mtime() -> float:
    try:
        return os.path.getmtime("data/recommendations.json")
    except Exception:
        return 0.0

WATCHLIST_SECTORS = ["Space", "Defence", "AI", "Energy", "Quantum", "Robots", "Health"]
SECTOR_EMOJI = {"Space": "🚀", "Defence": "🛡️", "AI": "🤖", "Energy": "⚡", "Quantum": "⚛️", "Robots": "🦾", "Health": "🏥"}
GH_WATCHLIST_PATH = "data/watchlist.json"

@st.cache_data(ttl=300)
def load_watchlist() -> dict:
    try:
        with open("data/watchlist.json", encoding="utf-8") as f:
            data = json.load(f)
            for s in WATCHLIST_SECTORS:
                data.setdefault(s, [])
            return data
    except Exception:
        return {s: [] for s in WATCHLIST_SECTORS}

@st.cache_data(ttl=300)
def get_history(ticker: str, period: str, interval: str = "1d") -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).history(period=period, interval=interval)
    except Exception:
        return pd.DataFrame()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_pln(v):
    if v is None or (isinstance(v, float) and math.isnan(v)): return "—"
    s = "+" if v >= 0 else ""
    if abs(v) >= 1_000_000: return f"{s}{v/1_000_000:.2f}M PLN"
    if abs(v) >= 1_000:     return f"{s}{v/1_000:.1f}k PLN"
    return f"{s}{v:.0f} PLN"

def fmt_m(v):
    if v is None: return "—"
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.1f}T"
    if abs(v) >= 1_000:     return f"${v/1_000:.1f}B"
    return f"${v:.0f}M"

def fmt_cap(v):
    if v is None or (isinstance(v, float) and math.isnan(v)): return "—"
    if v >= 1_000_000_000_000: return f"${v/1_000_000_000_000:.2f}T"
    if v >= 1_000_000_000:     return f"${v/1_000_000_000:.1f}B"
    if v >= 1_000_000:         return f"${v/1_000_000:.0f}M"
    return f"${v:.0f}"

def fmt_pct(v):
    if v is None or (isinstance(v, float) and math.isnan(v)): return "—"
    return f"{'+'if v>=0 else ''}{v:.1f}%"

def pclass(v):
    if v is None: return "t-neu"
    return "t-pos" if v >= 0 else "t-neg"

def kpiclass(v):
    if v is None: return "neu"
    return "pos" if v >= 0 else "neg"

def build_positions(df, prices, fx, recs):
    rows = []
    for _, r in df.iterrows():
        t   = r["Ticker"]; ccy = r["Waluta"]; qty = float(r["Ilosc"]); avg = float(r["Srednia_cena"])
        p   = prices.get(t, {}); price = p.get("price"); chg = p.get("change_pct")
        if isinstance(price, float) and math.isnan(price): price = None
        if isinstance(chg,   float) and math.isnan(chg):   chg   = None
        rate = fx.get(ccy, 1.0); rec = recs.get(t, {}); fv = rec.get("fair_value")
        cur_val = price * qty * rate if price is not None and qty else None
        cost    = avg * qty * rate   if avg is not None and qty else None  # avg=0 valid (free shares)
        pnl     = (cur_val - cost)   if cur_val is not None and cost is not None else None
        pnl_pct = pnl / cost * 100   if pnl is not None and cost else None  # cost=0 → pnl_pct=None (∞)
        upside  = (fv - price) / price * 100 if fv and price else rec.get("upside_pct")
        rows.append({
            "Ticker": t, "Nazwa": r["Nazwa"], "Cena": price, "Waluta": ccy,
            "Dzień%": chg, "Ilość": qty, "Avg": avg,
            "Val_PLN": cur_val, "Cost_PLN": cost, "PnL_PLN": pnl, "PnL%": pnl_pct,
            "FV": fv, "FV_ccy": rec.get("fair_value_currency", ccy),
            "Entry": rec.get("entry_point"),
            "Thesis_breaker": rec.get("thesis_breaker", ""),
            "Upside": upside, "Rec": rec.get("recommendation", "—"),
            "Rec_sort": REC_ORDER.get(rec.get("recommendation", "HOLD"), 3),
            "Instr_sort": r.get("Instr_sort", 1),
        })
    return pd.DataFrame(rows)

# ─── CHART ────────────────────────────────────────────────────────────────────
def price_chart(ticker, period, entry, fv, interval="1d"):
    hist = get_history(ticker, period, interval)
    if hist.empty: return None
    closes = hist["Close"].dropna().astype(float)
    if closes.empty: return None

    y_min = closes.min(); y_max = closes.max()
    pad   = (y_max - y_min) * 0.08 or y_min * 0.02
    y_lo  = y_min - pad;  y_hi = y_max + pad

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=closes, mode="lines", name="Cena",
        line=dict(color=ACCENT, width=2),
        fill="tozeroy", fillcolor="rgba(0,217,163,0.06)",
        hovertemplate="%{x|%d %b %Y}  <b>%{y:.2f}</b><extra></extra>"
    ))
    if fv:
        fig.add_hline(y=fv, line_dash="dash", line_color="rgba(245,158,11,0.7)", line_width=1.5,
                      annotation_text=f"FV  {fv:.0f}",
                      annotation_font=dict(color="#f59e0b", size=11),
                      annotation_position="top right")
    if entry:
        fig.add_hline(y=entry, line_dash="dot", line_color="rgba(16,185,129,0.7)", line_width=1.5,
                      annotation_text=f"Entry  {entry:.0f}",
                      annotation_font=dict(color="#10b981", size=11),
                      annotation_position="bottom right")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#94a3b8"),
        showlegend=False, margin=dict(l=0, r=60, t=8, b=0), height=320,
        xaxis=dict(showgrid=False, color="#334155", tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                   color="#334155", tickfont=dict(size=11),
                   range=[y_lo, y_hi]),
        hovermode="x unified"
    )
    return fig

# ─── DCF CALCULATOR ───────────────────────────────────────────────────────────
def compute_dcf_stages(dcf: dict):
    """Returns list of dicts with computed yearly FCF per stage.
    Supports two stage formats:
      Standard: ebit_margin_pct + tax_pct + capex_pct + da_pct
      Direct:   fcf_margin_pct  (pre-revenue / scenario models)
    n_years is parsed from the period string ("2026–2030" → 5, "2026-2028" → 3).
    """
    import re as _re
    wacc   = dcf["wacc_pct"] / 100
    rev    = dcf.get("revenue_ttm_m") or dcf.get("revenue_base_fy2026e_m")
    if rev is None:
        return [], 0, 0
    stages = dcf["stages"]
    rows   = []
    year   = 0
    for stage in stages:
        years_range = stage["period"]
        m = _re.search(r'(\d{4})[–\-](\d{4})', years_range)
        n_years = stage.get("n_years") or (int(m.group(2)) - int(m.group(1)) + 1 if m else 5)
        cagr    = stage["rev_cagr_pct"] / 100
        has_components = all(k in stage for k in ["ebit_margin_pct", "tax_pct", "capex_pct", "da_pct"])
        direct  = "fcf_margin_pct" in stage and not has_components
        if not direct:
            ebit_m    = stage["ebit_margin_pct"] / 100
            tax       = stage["tax_pct"] / 100
            capex_pct = stage["capex_pct"] / 100
            da_pct    = stage["da_pct"] / 100
        else:
            fcf_pct   = stage["fcf_margin_pct"] / 100
        for _ in range(n_years):
            year += 1
            rev = rev * (1 + cagr)
            if not direct:
                ebit  = rev * ebit_m
                nopat = ebit * (1 - tax)
                da    = rev * da_pct
                capex = rev * capex_pct
                fcf   = nopat + da - capex
                rows.append({"Rok": year, "Okres": years_range,
                              "Przychody": rev, "EBIT": ebit, "NOPAT": nopat,
                              "D&A": da, "CapEx": capex, "FCF": fcf,
                              "PV_FCF": fcf / ((1 + wacc) ** year), "direct": False})
            else:
                fcf = rev * fcf_pct
                rows.append({"Rok": year, "Okres": years_range,
                              "Przychody": rev, "EBIT": None, "NOPAT": None,
                              "D&A": None, "CapEx": None, "FCF": fcf,
                              "PV_FCF": fcf / ((1 + wacc) ** year),
                              "direct": True, "fcm": stage["fcf_margin_pct"]})
    return rows, rev, year

def _render_alt_valuation(alt: dict, fv_currency: str):
    """Renders step-by-step alternative valuation (EV/Revenue, EV/EBITDA, Scenario etc.)"""
    MONO = "font-family:'Courier New',monospace;font-size:12px;background:rgba(0,0,0,0.25);border-radius:8px;padding:14px 18px;line-height:1.9;color:#94a3b8;border:1px solid rgba(255,255,255,0.06)"
    HL   = "color:#00d9a3;font-weight:700"
    HLW  = "color:#e2e8f0;font-weight:600"

    method = alt.get("method", "Metoda alternatywna")
    reason = alt.get("method_reason", "")
    inputs = alt.get("inputs", [])
    steps  = alt.get("steps", [])
    fv_alt = alt.get("fair_value_computed")

    st.markdown(f'<div class="sh">📐 Metoda wyceny: {method}</div>', unsafe_allow_html=True)

    if reason:
        st.markdown(f"""
        <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:8px;padding:10px 14px;font-size:12px;color:#94a3b8;margin-bottom:8px">
        <b style="color:#f59e0b">Dlaczego nie DCF:</b> {reason}
        </div>""", unsafe_allow_html=True)

    # Inputs table
    if inputs:
        st.markdown('<div class="sh">📋 Dane wsadowe (źródło każdej liczby)</div>', unsafe_allow_html=True)
        rows_html = ""
        for inp in inputs:
            name   = inp.get("name", "")
            value  = inp.get("value", "")
            source = inp.get("source", "—")
            rows_html += f"""<tr>
                <td>{name}</td>
                <td style="color:#e2e8f0;font-weight:600">{value}</td>
                <td style="color:#475569;font-size:11px">{source}</td>
            </tr>"""
        st.markdown(f"""
        <div style="overflow-x:auto;border-radius:10px;border:1px solid rgba(255,255,255,0.06)">
        <table class="dcf-table">
          <thead><tr><th style="text-align:left">Parametr</th><th>Wartość</th><th style="text-align:left">Źródło</th></tr></thead>
          <tbody>{rows_html}</tbody>
        </table>
        </div>""", unsafe_allow_html=True)

    # Steps
    if steps:
        st.markdown('<div class="sh">🧮 Wyliczenie krok po kroku</div>', unsafe_allow_html=True)
        steps_html = "<br>".join(
            f'<b style="color:#64748b">Krok {i+1}:</b>&nbsp; {s}' for i, s in enumerate(steps)
        )
        result_html = ""
        if fv_alt is not None:
            result_html = f'<br><br><b style="{HL}">= Fair Value: {fv_alt:.2f} {fv_currency}</b>'
        st.markdown(f'<div style="{MONO}">{steps_html}{result_html}</div>', unsafe_allow_html=True)

    # Bridge card
    if fv_alt is not None:
        stored_fv = None  # passed from caller via alt block itself
        col_res, _ = st.columns([1, 2])
        with col_res:
            st.markdown(f"""
            <div style="background:rgba(0,217,163,0.06);border:1px solid rgba(0,217,163,0.2);border-radius:10px;padding:16px 20px;margin-top:8px">
                <div style="font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">Fair Value ({method})</div>
                <div style="font-size:28px;font-weight:700;color:#00d9a3">{fv_alt:.2f} {fv_currency}</div>
            </div>""", unsafe_allow_html=True)


def _render_dcf_scenarios(scenarios: list, dcf: dict, rec: dict):
    """Renders scenario analysis section inside an expander in the DCF tab."""
    weighted   = dcf.get("fair_value_weighted")
    formula    = dcf.get("fair_value_weighted_formula", "")
    currency   = rec.get("fair_value_currency", "USD")
    max_fv     = max(s["fair_value"] for s in scenarios)

    with st.expander("📊 Analiza scenariuszowa", expanded=False):
        st.markdown(
            '<div style="font-size:11px;color:#64748b;margin-bottom:16px">'
            'Bazowy DCF (powyżej) to <b style="color:#e2e8f0">Base case</b>. '
            'Tabela poniżej pokazuje pełne spektrum wyników przy różnych założeniach makro i operacyjnych.'
            '</div>', unsafe_allow_html=True)

        # ── Scenario cards
        cols = st.columns(len(scenarios))
        for col, sc in zip(cols, scenarios):
            c     = sc["color"]
            prob  = sc["probability_pct"]
            fv    = sc["fair_value"]
            bar_w = int(fv / max_fv * 100)
            a     = sc["assumptions"]
            with col:
                st.markdown(f"""
                <div style="background:rgba(255,255,255,0.04);border:1px solid #{c}44;border-radius:12px;padding:14px 12px">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
                        <span style="font-size:11px;font-weight:700;color:#{c};text-transform:uppercase;letter-spacing:1px">{sc['name']}</span>
                        <span style="font-size:10px;color:#475569;background:rgba(255,255,255,0.06);border-radius:4px;padding:2px 6px">{prob}%</span>
                    </div>
                    <div style="font-size:22px;font-weight:700;color:#{c};margin-bottom:2px">${fv}</div>
                    <div style="font-size:10px;color:#475569;margin-bottom:10px">{currency}</div>
                    <div style="background:rgba(255,255,255,0.06);border-radius:3px;height:4px;margin-bottom:12px">
                        <div style="background:#{c};width:{bar_w}%;height:100%;border-radius:3px"></div>
                    </div>
                    <div style="font-size:10px;color:#64748b;line-height:1.7">
                        <div>CAGR S1 &nbsp;<b style="color:#94a3b8">{a['stage1_cagr_pct']}%</b></div>
                        <div>CAGR S2 &nbsp;<b style="color:#94a3b8">{a['stage2_cagr_pct']}%</b></div>
                        <div>EBIT &nbsp;&nbsp;&nbsp;<b style="color:#94a3b8">{a['ebit_margin_pct']}%</b></div>
                        <div>WACC &nbsp;&nbsp;&nbsp;<b style="color:#94a3b8">{a['wacc_pct']}%</b></div>
                        <div>g &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<b style="color:#94a3b8">{a['terminal_g_pct']}%</b></div>
                    </div>
                    <div style="margin-top:10px;font-size:10px;color:#475569;line-height:1.5;border-top:1px solid rgba(255,255,255,0.05);padding-top:8px">{sc['description']}</div>
                </div>""", unsafe_allow_html=True)

        # ── Weighted FV
        if weighted:
            st.markdown(f"""
            <div style="margin-top:20px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);
                        border-radius:10px;padding:16px 20px;display:flex;justify-content:space-between;align-items:center">
                <div>
                    <div style="font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:4px">
                        Fair Value Ważone Scenariuszowo
                    </div>
                    <div style="font-size:11px;color:#64748b;font-family:'Courier New',monospace">{formula}</div>
                </div>
                <div style="text-align:right">
                    <div style="font-size:28px;font-weight:700;color:#e2e8f0">${weighted}</div>
                    <div style="font-size:10px;color:#475569">{currency} · prob-weighted</div>
                </div>
            </div>""", unsafe_allow_html=True)

        # ── Assumptions table (jeden string — Streamlit domyka tagi per st.markdown!)
        rows_html = ""
        for sc in scenarios:
            a = sc["assumptions"]
            c = sc["color"]
            rows_html += f"""<tr style="border-bottom:1px solid rgba(255,255,255,0.04)">
              <td style="padding:7px 6px;color:#{c};font-weight:600">{sc['name']}</td>
              <td style="padding:7px 6px;color:#64748b;text-align:center">{sc['probability_pct']}%</td>
              <td style="padding:7px 6px;color:#94a3b8;text-align:right">{a['stage1_cagr_pct']}%</td>
              <td style="padding:7px 6px;color:#94a3b8;text-align:right">{a['stage2_cagr_pct']}%</td>
              <td style="padding:7px 6px;color:#94a3b8;text-align:right">{a['ebit_margin_pct']}%</td>
              <td style="padding:7px 6px;color:#94a3b8;text-align:right">{a['fcf_margin_s1_pct']}%</td>
              <td style="padding:7px 6px;color:#94a3b8;text-align:right">{a['wacc_pct']}%</td>
              <td style="padding:7px 6px;color:#94a3b8;text-align:right">{a['terminal_g_pct']}%</td>
              <td style="padding:7px 6px;color:#{c};font-weight:700;text-align:right">${sc['fair_value']}</td>
            </tr>"""
        st.markdown(f"""
        <div style="margin-top:20px;overflow-x:auto">
        <table style="width:100%;border-collapse:collapse;font-size:11px;font-family:'Inter',sans-serif">
          <thead>
            <tr style="border-bottom:1px solid rgba(255,255,255,0.08)">
              <th style="text-align:left;padding:8px 6px;color:#475569;font-weight:600">Scenariusz</th>
              <th style="text-align:center;padding:8px 6px;color:#475569">Prob.</th>
              <th style="text-align:right;padding:8px 6px;color:#475569">CAGR S1</th>
              <th style="text-align:right;padding:8px 6px;color:#475569">CAGR S2</th>
              <th style="text-align:right;padding:8px 6px;color:#475569">EBIT</th>
              <th style="text-align:right;padding:8px 6px;color:#475569">FCF S1</th>
              <th style="text-align:right;padding:8px 6px;color:#475569">WACC</th>
              <th style="text-align:right;padding:8px 6px;color:#475569">g</th>
              <th style="text-align:right;padding:8px 6px;color:#475569;font-weight:600">FV</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        </div>""", unsafe_allow_html=True)

        # ── Risk per scenario (również jeden string)
        risks_html = "".join(
            f"""<div style="background:rgba(255,255,255,0.03);border-left:2px solid #{sc['color']};
                 border-radius:0 6px 6px 0;padding:6px 10px;font-size:10px;color:#64748b;flex:1;min-width:180px">
                 <b style="color:#{sc['color']}">{sc['name']} risk:</b> {_e(sc.get('key_risk','—'))}</div>"""
            for sc in scenarios)
        st.markdown(f'<div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">{risks_html}</div>',
                    unsafe_allow_html=True)


def tab_dcf(rec: dict):
    dcf = rec.get("dcf")
    alt = dcf.get("alt_valuation") if dcf else None
    fv_currency = rec.get("fair_value_currency", "")

    if not dcf:
        st.markdown("""
        <div style="padding:40px;text-align:center;color:#475569">
            <div style="font-size:32px;margin-bottom:12px">📐</div>
            <div style="font-size:15px">Brak modelu DCF dla tego aktywa.</div>
            <div style="font-size:13px;margin-top:6px;color:#334155">Krypto i ETF-y nie mają przepływów gotówkowych do dyskontowania.</div>
        </div>""", unsafe_allow_html=True)
        return

    # If no DCF stages but alt_valuation exists — show alternative method (+ scenarios if present)
    has_stages = bool(dcf.get("stages"))
    if not has_stages:
        if alt:
            _render_alt_valuation(alt, fv_currency)
            if dcf.get("scenarios"):
                _render_dcf_scenarios(dcf["scenarios"], dcf, rec)
        else:
            st.markdown("""
            <div style="padding:40px;text-align:center;color:#475569">
                <div style="font-size:32px;margin-bottom:12px">📐</div>
                <div style="font-size:15px">Brak modelu DCF dla tego aktywa.</div>
                <div style="font-size:13px;margin-top:6px;color:#334155">Krypto i ETF-y nie mają przepływów gotówkowych do dyskontowania.</div>
            </div>""", unsafe_allow_html=True)
        return

    wacc       = dcf["wacc_pct"] / 100
    tg         = dcf["terminal_growth_pct"] / 100
    fv_currency = rec.get("fair_value_currency", "")
    rev_ttm    = dcf.get("revenue_ttm_m")
    rev_fy26e  = dcf.get("revenue_base_fy2026e_m")
    rev_base   = rev_ttm or rev_fy26e
    rev_label  = "Revenue TTM" if rev_ttm else "Revenue FY2026E"
    shares_m   = dcf.get("shares_m", 1)

    MONO = "font-family:'Courier New',monospace;font-size:12px;background:rgba(0,0,0,0.25);border-radius:8px;padding:14px 18px;line-height:1.9;color:#94a3b8;border:1px solid rgba(255,255,255,0.06)"
    HL   = "color:#00d9a3;font-weight:700"
    HLW  = "color:#e2e8f0;font-weight:600"

    # ── Summary metrics
    st.markdown('<div class="sh">⚙️ Założenia modelu</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    for col, label, val, sub in [
        (col1, "WACC",           f"{dcf['wacc_pct']}%",  "Stopa dyskontowa"),
        (col2, "Terminal Growth",f"{dcf['terminal_growth_pct']}%", "Wzrost w nieskończoność"),
        (col3, rev_label,        fmt_m(rev_base) if rev_base else "—", "Bazowe przychody"),
        (col4, "Liczba akcji",   f"{shares_m/1000:.1f}B" if shares_m >= 1000 else f"{shares_m}M", "Akcji w obrocie"),
    ]:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # ── KROK 0: Base Revenue Breakdown (optional — present for forward-estimate bases)
    base_bd = dcf.get("base_breakdown")
    if base_bd:
        ttm_note = base_bd.get("ttm_note", "")
        items    = base_bd.get("items", [])
        st.markdown('<div class="sh">🏗️ Krok 0 — Baza przychodów (skąd pochodzi liczba bazowa)</div>', unsafe_allow_html=True)
        if ttm_note:
            st.markdown(f"""
            <div style="background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:8px;padding:10px 14px;font-size:12px;color:#94a3b8;margin-bottom:8px">
            <b style="color:#f59e0b">Dlaczego nie TTM:</b> {ttm_note}
            </div>""", unsafe_allow_html=True)
        if items:
            rows_html = "".join(
                f"""<tr>
                    <td style="color:#e2e8f0;font-weight:{'700' if 'RAZEM' in item.get('segment','') else '400'}">{item.get('segment','')}</td>
                    <td style="color:#00d9a3;text-align:right">{fmt_m(item['revenue_m']) if item.get('revenue_m') else '—'}</td>
                    <td style="color:#{'10b981' if item.get('yoy_pct') and item['yoy_pct']>0 else '94a3b8'};text-align:right">
                        {'+'+str(round(item['yoy_pct'],1))+'%' if item.get('yoy_pct') is not None else '—'}
                    </td>
                    <td style="color:#64748b;font-size:11px">{item.get('note','')}</td>
                </tr>"""
                for item in items
            )
            st.markdown(f"""
            <div style="overflow-x:auto;border-radius:12px;border:1px solid rgba(255,255,255,0.06);margin-bottom:8px">
            <table style="width:100%;border-collapse:collapse;font-family:'Courier New',monospace;font-size:12px">
            <thead><tr style="border-bottom:1px solid rgba(255,255,255,0.1)">
                <th style="color:#475569;text-align:left;padding:8px 12px">Segment</th>
                <th style="color:#475569;text-align:right;padding:8px 12px">Revenue FY2026E</th>
                <th style="color:#475569;text-align:right;padding:8px 12px">YoY</th>
                <th style="color:#475569;text-align:left;padding:8px 12px">Uzasadnienie</th>
            </tr></thead>
            <tbody style="color:#94a3b8">
            {rows_html}
            </tbody></table></div>""", unsafe_allow_html=True)

    # ── KROK 1: WACC
    st.markdown('<div class="sh">📐 Krok 1 — Stopa dyskontowa (WACC)</div>', unsafe_allow_html=True)
    wi = dcf.get("wacc_inputs")
    if wi:
        rf     = wi.get("rf_pct", 0)
        beta   = wi.get("beta", 1.0)
        erp    = wi.get("erp_pct", 5.0)
        rd     = wi.get("rd_pct", 4.0)
        mcap   = wi.get("market_cap_m", 0)
        d_wi   = wi.get("debt_m", 0)
        tax_wi = wi.get("tax_pct", 19.0)
        V      = mcap + d_wi
        E_w    = mcap / V * 100 if V > 0 else 100.0
        D_w    = d_wi  / V * 100 if V > 0 else 0.0
        Re     = rf + beta * erp
        Rd_at  = rd * (1 - tax_wi / 100)
        wacc_r = E_w / 100 * Re / 100 + D_w / 100 * Rd_at / 100
        st.markdown(f"""<div style="{MONO}">
<b style="{HLW}">WACC = E/V &times; Re + D/V &times; Rd &times; (1&minus;tax)</b><br><br>
<b style="color:#64748b">Koszt kapitału własnego (CAPM):</b><br>
&nbsp;&nbsp;Re = Rf + &beta; &times; ERP<br>
&nbsp;&nbsp;Re = {rf}% + {beta} &times; {erp}%<br>
&nbsp;&nbsp;Re = {rf}% + {beta*erp:.1f}%<br>
&nbsp;&nbsp;<b style="{HLW}">Re = {Re:.1f}%</b><br><br>
<b style="color:#64748b">Koszt długu po podatku:</b><br>
&nbsp;&nbsp;Rd &times; (1&minus;tax) = {rd}% &times; (1&minus;{tax_wi}%) = <b style="{HLW}">{Rd_at:.2f}%</b><br><br>
<b style="color:#64748b">Wagi kapitału (E = market cap, D = dług księgowy):</b><br>
&nbsp;&nbsp;E/V = {fmt_m(mcap)} / {fmt_m(V)} = {E_w:.1f}%<br>
&nbsp;&nbsp;D/V = {fmt_m(d_wi)} / {fmt_m(V)} = {D_w:.1f}% &nbsp;<span style="color:#475569;font-size:11px">(dług pomijalny)</span><br><br>
<b style="color:#64748b">WACC:</b><br>
&nbsp;&nbsp;= {E_w:.1f}% &times; {Re:.1f}% + {D_w:.1f}% &times; {Rd_at:.2f}%<br>
&nbsp;&nbsp;= {E_w/100*Re/100*100:.2f}% + {D_w/100*Rd_at/100*100:.3f}%<br>
&nbsp;&nbsp;<b style="{HL}">= {wacc_r*100:.2f}% &asymp; {dcf['wacc_pct']}%</b>
</div>""", unsafe_allow_html=True)
        # Źródła i uzasadnienia składowych WACC (note, full_wacc_calc, *_source)
        wi_extra = ""
        for key, label in [("note", "Uzasadnienie / źródła"),
                           ("full_wacc_calc", "Pełny WACC z długiem"),
                           ("rf_source", "Źródło Rf"), ("beta_source", "Źródło bety"),
                           ("erp_source", "Źródło ERP")]:
            if wi.get(key):
                wi_extra += (f'<div style="margin-top:8px"><b style="color:#475569;font-size:10px;'
                             f'text-transform:uppercase;letter-spacing:1px">{label}</b><br>'
                             f'<span style="color:#64748b;font-size:11.5px;line-height:1.6">{_e(wi[key])}</span></div>')
        if wi_extra:
            st.markdown(f'<div style="background:rgba(255,255,255,0.02);border-radius:8px;'
                        f'padding:10px 16px;margin-top:8px">{wi_extra}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div style="{MONO}">WACC = <b style="{HL}">{dcf["wacc_pct"]}%</b> (założenie — brak danych CAPM w modelu)</div>', unsafe_allow_html=True)

    # ── KROK 2 + KROK 3 (side by side)
    col_tg, col_nd = st.columns(2)
    with col_tg:
        st.markdown('<div class="sh">📈 Krok 2 — Terminal Growth (g)</div>', unsafe_allow_html=True)
        tg_note = dcf.get("terminal_growth_rationale", "")
        note_html = f'<br><span style="color:#475569;font-size:11px">{tg_note}</span>' if tg_note else ""
        st.markdown(f"""<div style="{MONO}">
<b style="color:#64748b">Ograniczenie górne:</b><br>
&nbsp;&nbsp;g &le; nominalny PKB = inflacja + realny PKB<br>
&nbsp;&nbsp;g &le; ~2.5% + 1.5% = ~4.0%<br><br>
<b style="color:#64748b">Przyjęte:</b><br>
&nbsp;&nbsp;<b style="{HL}">g = {dcf['terminal_growth_pct']}%</b> (poniżej nominalnego PKB){note_html}
</div>""", unsafe_allow_html=True)

    with col_nd:
        st.markdown('<div class="sh">💰 Krok 3 — Net Cash / Net Debt</div>', unsafe_allow_html=True)
        bs = dcf.get("balance_sheet_inputs") or {}
        net_debt_val = dcf.get("net_debt_m", -dcf.get("net_cash_m", 0))
        # Tolerancja na warianty nazw pól w modelach
        cash_bs = (bs.get("cash_and_st_investments_m") or bs.get("cash_and_st_securities_m")
                   or ((bs.get("cash_m") or 0) + (bs.get("marketable_securities_m") or 0)
                       + (bs.get("marketable_debt_m") or 0)) or None)
        debt_bs = (bs.get("total_debt_m") or bs.get("debt_m")
                   or bs.get("lt_debt_book_value_m") or bs.get("debt_gross_m"))
        bs_note = bs.get("note", "")
        note_html = (f'<br><span style="color:#475569;font-size:11px">{_e(bs_note)}</span>'
                     if bs_note else "")
        if cash_bs and debt_bs is not None:
            net_bs  = cash_bs - debt_bs
            col_net = "#10b981" if net_bs > 0 else "#ef4444"
            bridge_hint = ("net cash &rarr; w kroku Bridge DODAJEMY do EV (Equity = EV + net cash)"
                           if net_bs > 0 else
                           "net debt &rarr; w kroku Bridge ODEJMUJEMY od EV (Equity = EV − net debt)")
            st.markdown(f"""<div style="{MONO}">
Net Cash = Gotówka &minus; Dług (brutto)<br>
&nbsp;&nbsp;= {fmt_m(cash_bs)} &minus; {fmt_m(debt_bs)}<br>
&nbsp;&nbsp;<b style="color:{col_net}">= {fmt_m(net_bs)}</b><br><br>
<span style="color:#475569;font-size:11px">{bridge_hint}</span>{note_html}
</div>""", unsafe_allow_html=True)
        else:
            # Brak składowych w modelu — pokaż wartość używaną w Bridge, bez fabrykowania 0−0
            net_cash_direct = (bs.get("net_cash_m") or bs.get("net_liquidity_m")
                               or bs.get("net_cash_conservative_m") or -net_debt_val)
            sign = "net cash (dodajemy do EV)" if net_cash_direct > 0 else "net debt (odejmujemy od EV)"
            col  = "#10b981" if net_cash_direct > 0 else "#ef4444"
            st.markdown(f"""<div style="{MONO}">
Net cash/debt (wartość używana w Bridge) = <b style="color:{col}">{fmt_m(net_cash_direct)}</b><br>
<span style="color:#475569;font-size:11px">{sign} — brak rozbicia gotówka/dług w modelu{(' · ' + _e(bs_note)) if bs_note else ''}</span>
</div>""", unsafe_allow_html=True)

    # ── KROK 4: FCF Margin derivation
    st.markdown('<div class="sh">🧮 Krok 4 — Marże FCF (wyprowadzenie ze wzoru)</div>', unsafe_allow_html=True)
    fcm_parts = []
    for i, stage in enumerate(dcf.get("stages", [])):
        has_comp = all(k in stage for k in ["ebit_margin_pct", "tax_pct", "capex_pct", "da_pct"])
        if has_comp:
            ebit_s  = stage["ebit_margin_pct"]
            tax_s   = stage["tax_pct"]
            capex_s = stage["capex_pct"]
            da_s    = stage["da_pct"]
            nopat_s = ebit_s * (1 - tax_s / 100)
            fcm_s   = nopat_s + da_s - capex_s
            stored  = stage.get("fcf_margin_pct")
            check   = f' &nbsp;<span style="color:#475569;font-size:11px">(zapisane: {stored}%)</span>' if stored else ""
            fcm_parts.append(
                f'<b style="{HLW}">Stage {i+1} ({stage["period"]}, CAGR {stage["rev_cagr_pct"]}%):</b><br>'
                f'FCF_margin = EBIT% &times; (1&minus;tax%) + D&amp;A% &minus; CapEx%<br>'
                f'&nbsp;&nbsp;= {ebit_s}% &times; (1&minus;{tax_s}%) + {da_s}% &minus; {capex_s}%<br>'
                f'&nbsp;&nbsp;= {ebit_s}% &times; {100-tax_s:.0f}% + {da_s}% &minus; {capex_s}%<br>'
                f'&nbsp;&nbsp;= NOPAT {nopat_s:.2f}% + D&amp;A {da_s}% &minus; CapEx {capex_s}%<br>'
                f'&nbsp;&nbsp;<b style="{HL}">= {fcm_s:.2f}%</b>{check}'
                + (f'<br><span style="color:#475569;font-size:11px">↳ {_e(stage["note"])}</span>' if stage.get("note") else "")
            )
        elif "fcf_margin_pct" in stage:
            fcm_parts.append(
                f'<b style="{HLW}">Stage {i+1} ({stage["period"]}, CAGR {stage["rev_cagr_pct"]}%) — FCF Margin bezpośrednia:</b><br>'
                f'FCF_margin = <b style="{HL}">{stage["fcf_margin_pct"]}%</b> &nbsp;'
                f'<span style="color:#475569;font-size:11px">(brak składowych — użyto wprost)</span>'
            )
    st.markdown(f'<div style="{MONO}">{"<br><br>".join(fcm_parts)}</div>', unsafe_allow_html=True)

    # ── KROK 4b: CAGR Context (optional — backlog / growth driver justification)
    cagr_ctx = dcf.get("cagr_context")
    if cagr_ctx:
        st.markdown('<div class="sh">📡 Krok 4b — Uzasadnienie CAGR (dlaczego te stawki wzrostu)</div>', unsafe_allow_html=True)
        for stage_key in sorted(cagr_ctx.keys()):
            stg = cagr_ctx[stage_key]
            headline  = stg.get("headline", "")
            cagr_val  = stg.get("cagr_pct", "?")
            period    = stg.get("period", "")
            bullet_items = stg.get("items", [])
            bullets_html = "".join(f'<br>&nbsp;&nbsp;• {item}' for item in bullet_items)
            st.markdown(f"""<div style="{MONO}">
<b style="{HLW}">{stage_key.upper()} — {period} — CAGR <span style="color:#00d9a3">{cagr_val}%</span></b><br>
<b style="color:#f59e0b">{headline}</b>{bullets_html}
</div>""", unsafe_allow_html=True)

    # ── KROKI 5-6: Projection table
    wacc_label = dcf['wacc_pct']
    st.markdown(f'<div class="sh">📊 Kroki 5–6 — Przychody, FCF i dyskontowanie (WACC={wacc_label}%)</div>', unsafe_allow_html=True)
    rows, final_rev, total_years = compute_dcf_stages(dcf)
    if not rows:
        st.warning("Brak `revenue_ttm_m` lub `revenue_base_fy2026e_m` w modelu DCF — nie można obliczyć projekcji.")
        return

    is_direct = any(r.get("direct") for r in rows)
    if is_direct:
        header = "<tr><th>Rok</th><th>Okres</th><th>Przychody</th><th>FCF Margin</th><th>FCF</th><th>PV(FCF)</th></tr>"
    else:
        header = "<tr><th>Rok</th><th>Okres</th><th>Przychody</th><th>EBIT</th><th>NOPAT</th><th>+D&A</th><th>–CapEx</th><th>FCF</th><th>PV(FCF)</th></tr>"
    body = ""
    pv_sum = 0
    for r in rows:
        pv_sum += r["PV_FCF"]
        fcf_color = "#ef4444" if r["FCF"] < 0 else "inherit"
        pv_color  = "#ef4444" if r["PV_FCF"] < 0 else "#00d9a3"
        if is_direct:
            fcm = r.get("fcm", "?")
            fcm_color = "#ef4444" if isinstance(fcm, (int, float)) and fcm < 0 else "#10b981"
            body += f"""<tr>
                <td>{r['Rok']}</td><td>{r['Okres']}</td>
                <td>{fmt_m(r['Przychody'])}</td>
                <td style="color:{fcm_color}">{fcm}%</td>
                <td style="color:{fcf_color}">{fmt_m(r['FCF'])}</td>
                <td style="color:{pv_color}">{fmt_m(r['PV_FCF'])}</td>
            </tr>"""
        else:
            body += f"""<tr>
                <td>{r['Rok']}</td><td>{r['Okres']}</td>
                <td>{fmt_m(r['Przychody'])}</td><td>{fmt_m(r['EBIT'])}</td>
                <td>{fmt_m(r['NOPAT'])}</td><td>{fmt_m(r['D&A'])}</td>
                <td>{fmt_m(r['CapEx'])}</td>
                <td style="color:{fcf_color}">{fmt_m(r['FCF'])}</td>
                <td style="color:{pv_color}">{fmt_m(r['PV_FCF'])}</td>
            </tr>"""

    colspan = "5" if is_direct else "8"
    body += f"""<tr class="total">
        <td colspan="{colspan}" style="color:#64748b;font-size:11px">Suma PV przepływów (rok 1–{total_years})</td>
        <td style="color:{'#ef4444' if pv_sum < 0 else '#00d9a3'}">{fmt_m(pv_sum)}</td>
    </tr>"""

    last_fcf = rows[-1]["FCF"]
    tv    = last_fcf * (1 + tg) / (wacc - tg)
    pv_tv = tv / ((1 + wacc) ** total_years)

    st.markdown(f"""
    <div style="overflow-x:auto;border-radius:14px;border:1px solid {BORDER}">
    <table class="dcf-table"><thead>{header}</thead><tbody>{body}</tbody></table>
    </div>""", unsafe_allow_html=True)

    # ── KROKI 7-8: Terminal Value + Bridge
    st.markdown('<div class="sh">🌉 Kroki 7–8 — Terminal Value i bridge do ceny akcji</div>', unsafe_allow_html=True)

    net_debt     = dcf.get("net_debt_m", -dcf.get("net_cash_m", 0))
    shares       = dcf.get("shares_m", 1)
    ev_computed  = pv_sum + pv_tv
    eq_computed  = ev_computed - net_debt
    fv_computed  = eq_computed / shares
    nd_label     = "– Dług netto" if net_debt > 0 else "+ Gotówka netto"
    nd_color     = "#ef4444" if net_debt > 0 else "#10b981"
    stored_fv    = rec.get("fair_value")
    divergence_pct = abs(fv_computed - stored_fv) / max(abs(stored_fv), 0.01) * 100 if stored_fv else 0

    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown(f"""
        <div class="dcf-bridge">
            <div class="dcf-row">
                <span class="dcf-row-label">PV wolnych przepływów gotówkowych (lata 1–{total_years})</span>
                <span class="dcf-row-value">{fmt_m(pv_sum)}</span>
            </div>
            <div class="dcf-row" style="flex-direction:column;align-items:flex-start;gap:4px">
                <div style="display:flex;justify-content:space-between;width:100%">
                    <span class="dcf-row-label">+ PV wartości terminalnej</span>
                    <span class="dcf-row-value">{fmt_m(pv_tv)}</span>
                </div>
                <div style="font-size:11px;color:#475569;font-family:monospace;padding:6px 10px;background:rgba(0,0,0,0.2);border-radius:6px;width:100%;box-sizing:border-box">
                  TV = FCF<sub>{total_years}</sub> &times; (1+g) / (WACC&minus;g) = {fmt_m(last_fcf)} &times; {1+tg:.3f} / ({wacc:.3f}&minus;{tg:.3f}) = <b style="color:#94a3b8">{fmt_m(tv)}</b><br>
                  PV = TV / (1+WACC)<sup>{total_years}</sup> = {fmt_m(tv)} / {(1+wacc)**total_years:.4f} = <b style="color:#00d9a3">{fmt_m(pv_tv)}</b>
                </div>
            </div>
            <div class="dcf-row" style="border-top:1px solid rgba(255,255,255,0.08);padding-top:12px;margin-top:4px">
                <span class="dcf-row-label" style="font-weight:600;color:#e2e8f0">= Wartość przedsiębiorstwa (EV)</span>
                <span class="dcf-row-value" style="font-size:15px">{fmt_m(ev_computed)}</span>
            </div>
            <div class="dcf-row">
                <span class="dcf-row-label">{nd_label}</span>
                <span class="dcf-row-value" style="color:{nd_color}">{fmt_m(abs(net_debt))}</span>
            </div>
            <div class="dcf-row" style="border-top:1px solid rgba(255,255,255,0.08);padding-top:12px;margin-top:4px">
                <span class="dcf-row-label" style="font-weight:600;color:#e2e8f0">= Wartość kapitału własnego</span>
                <span class="dcf-row-value" style="font-size:15px">{fmt_m(eq_computed)}</span>
            </div>
            <div class="dcf-row">
                <span class="dcf-row-label">÷ Liczba akcji</span>
                <span class="dcf-row-value">{shares}M</span>
            </div>
            <div class="dcf-row" style="border-top:1px solid rgba(0,217,163,0.25);padding-top:14px;margin-top:4px">
                <span class="dcf-row-label" style="font-weight:700;color:#00d9a3;font-size:14px">= Fair Value DCF (z modelu)</span>
                <span class="dcf-row-total">{fv_computed:.2f} {fv_currency}</span>
            </div>
        </div>""", unsafe_allow_html=True)

        if stored_fv and divergence_pct > 10:
            valuation_method = dcf.get("valuation_method", "inna metoda wyceny")
            direction = "wyżej" if stored_fv > fv_computed else "niżej"
            st.warning(
                f"**Rozbieżność {divergence_pct:.0f}%** — model DCF daje **{fv_computed:.2f} {fv_currency}**, "
                f"ale zapisana FV w nagłówku to **{stored_fv} {fv_currency}** ({direction}). "
                f"Powód: _{valuation_method}_. Liczby powyżej to wynik czysto matematyczny z założeń — "
                f"sprawdź czy założenia są aktualne przed użyciem."
            )

    with col_b:
        tv_share = pv_tv / (pv_sum + pv_tv) * 100 if (pv_sum + pv_tv) > 0 else 0
        st.markdown(f"""
        <div style="background:{CARD};border:1px solid {BORDER};border-radius:14px;padding:20px">
            <div style="font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:16px">Struktura wartości</div>
            <div style="margin-bottom:12px">
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                    <span style="color:#94a3b8">PV FCF (10 lat)</span>
                    <span style="color:#e2e8f0">{100-tv_share:.0f}%</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:6px">
                    <div style="background:{ACCENT};width:{100-tv_share:.0f}%;height:100%;border-radius:4px"></div>
                </div>
            </div>
            <div>
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px">
                    <span style="color:#94a3b8">PV Terminal Value</span>
                    <span style="color:#e2e8f0">{tv_share:.0f}%</span>
                </div>
                <div style="background:rgba(255,255,255,0.06);border-radius:4px;height:6px">
                    <div style="background:#f59e0b;width:{tv_share:.0f}%;height:100%;border-radius:4px"></div>
                </div>
            </div>
            <div style="margin-top:20px;padding-top:16px;border-top:1px solid rgba(255,255,255,0.06)">
                <div style="font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">Uwagi analityczne</div>
                <div style="font-size:12px;color:#64748b;line-height:1.6">{dcf.get('notes','—')}</div>
            </div>
        </div>""", unsafe_allow_html=True)

    # If alt_valuation exists alongside DCF — show it as a secondary section
    if alt:
        st.markdown('<div style="margin-top:24px;border-top:1px solid rgba(255,255,255,0.06);padding-top:8px"></div>', unsafe_allow_html=True)
        _render_alt_valuation(alt, fv_currency)

    # Scenario analysis (optional)
    scenarios = dcf.get("scenarios")
    if scenarios:
        _render_dcf_scenarios(scenarios, dcf, rec)

# ─── TAB: DZIAŁANIA ───────────────────────────────────────────────────────────
def tab_actions(rec: dict, row, prices: dict):
    recommendation = rec.get("recommendation", "HOLD")
    fv  = rec.get("fair_value")
    ep  = rec.get("entry_point")
    ticker = rec.get("_ticker", "")
    price = prices.get(ticker, {}).get("price")

    # ── Big recommendation card
    colors = {"BUY": ("#10b981","rgba(16,185,129,0.08)","rgba(16,185,129,0.25)"),
              "SELL": ("#ef4444","rgba(239,68,68,0.08)","rgba(239,68,68,0.25)"),
              "REDUCE": ("#f59e0b","rgba(245,158,11,0.08)","rgba(245,158,11,0.25)"),
              "HOLD": ("#94a3b8","rgba(100,116,139,0.08)","rgba(100,116,139,0.2)")}
    c, bg, bd = colors.get(recommendation, colors["HOLD"])

    prio = rec.get("priority_action", "")
    prio_html = f'<div style="margin-top:10px;font-size:14px;color:{c};line-height:1.6">{_e(prio)}</div>' if prio else ""

    st.markdown(f"""
    <div style="background:{bg};border:1px solid {bd};border-radius:16px;padding:24px 28px;margin-bottom:24px">
        <div style="display:flex;align-items:center;gap:16px">
            <div style="background:{c};border-radius:12px;width:48px;height:48px;display:flex;align-items:center;justify-content:center;font-size:22px;flex-shrink:0">
                {"📈" if recommendation=="BUY" else "📉" if recommendation=="SELL" else "⚖️" if recommendation=="REDUCE" else "⏸"}
            </div>
            <div>
                <div style="font-size:11px;font-weight:600;color:{c};text-transform:uppercase;letter-spacing:1.5px;opacity:0.8">Aktualna rekomendacja</div>
                <div style="font-size:28px;font-weight:800;color:{c};letter-spacing:-0.5px">{recommendation}</div>
            </div>
            {"<div style='margin-left:auto;text-align:right'><div style='font-size:11px;color:#475569;margin-bottom:2px'>Aktualna cena</div><div style='font-size:20px;font-weight:700;color:#f8fafc'>" + f"{price:.2f}" + "</div></div>" if price else ""}
        </div>
        {prio_html}
    </div>""", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1])

    with col_l:
        # ── Buy/Add triggers
        st.markdown('<div class="sh">🟢 Kiedy dokupować</div>', unsafe_allow_html=True)
        if ep and fv:
            margin = (fv - ep) / fv * 100 if fv else 0
            st.markdown(f"""
            <div class="trigger-section">
                <div class="trigger-item ti-buy">
                    <span class="ti-icon">🎯</span>
                    <span>Wejście przy <b>{ep:.0f} {rec.get('fair_value_currency','')}</b> — {margin:.0f}% margin of safety do FV {fv:.0f}</span>
                </div>
                <div class="trigger-item ti-buy">
                    <span class="ti-icon">📉</span>
                    <span>Korekta <b>-15%</b> od aktualnej ceny to okazja do uzupełnienia</span>
                </div>
                {"<div class='trigger-item ti-buy'><span class='ti-icon'>📰</span><span>Negatywne wydarzenie niezwiązane z fundamentami (sentiment-driven selloff)</span></div>" if recommendation in ("BUY","HOLD") else ""}
            </div>""", unsafe_allow_html=True)
        elif recommendation == "BUY":
            st.markdown(f"""
            <div class="trigger-section">
                <div class="trigger-item ti-buy">
                    <span class="ti-icon">✅</span>
                    <span>Aktualna cena to dobry entry — poniżej fair value</span>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="trigger-section">
                <div class="trigger-item ti-hold">
                    <span class="ti-icon">⏳</span>
                    <span>Czekaj na korektę — obecna cena nieoptymalna</span>
                </div>
            </div>""", unsafe_allow_html=True)

        # ── Thesis breaker / Sell triggers
        st.markdown('<div class="sh">🔴 Kiedy sprzedawać</div>', unsafe_allow_html=True)
        tb = rec.get("thesis_breaker", "—")
        st.markdown(f"""
        <div class="trigger-section">
            <div class="trigger-item ti-sell">
                <span class="ti-icon">⛔</span>
                <span>{_e(tb)}</span>
            </div>
            {"<div class='trigger-item ti-sell'><span class='ti-icon'>📊</span><span>Fair Value rewizja w dół powyżej -20% — czas na wyjście</span></div>" if fv else ""}
            {"<div class='trigger-item ti-sell'><span class='ti-icon'>🎯</span><span>Cena osiąga Fair Value " + str(fv) + " " + rec.get('fair_value_currency','') + " — realizuj zysk lub redukuj pozycję</span></div>" if fv else ""}
        </div>""", unsafe_allow_html=True)

    with col_r:
        # ── Events timeline
        events = rec.get("events", [])
        st.markdown('<div class="sh">📅 Ostatnie wydarzenia</div>', unsafe_allow_html=True)
        if events:
            for i, ev in enumerate(events):
                impact  = ev.get("impact", "neutral")
                dot_cls = "ev-pos" if impact == "positive" else "ev-neg" if impact == "negative" else "ev-neu"
                border  = "border-bottom:1px solid rgba(255,255,255,0.04);" if i < len(events) - 1 else ""
                st.markdown(f"""
                <div style="display:flex;gap:16px;padding:14px 0;{border}">
                    <div style="display:flex;flex-direction:column;align-items:center;gap:0;padding-top:3px">
                        <div class="event-dot {dot_cls}"></div>
                    </div>
                    <div style="flex:1">
                        <div class="event-date">{_e(ev.get('date','—'))}</div>
                        <div class="event-text">{_e(ev.get('event',''))}</div>
                        <div class="event-fv">&#8594; FV: {_e(ev.get('fv_note',''))}</div>
                    </div>
                </div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#475569;font-size:13px;padding:20px 0">Brak wydarzeń do wyświetlenia.</div>', unsafe_allow_html=True)

# ─── PAGE: OVERVIEW ───────────────────────────────────────────────────────────
def page_overview(pos, demo, recs, mkt_cap=None, prices=None):
    if demo:
        st.markdown("""<div class="demo-banner">
        ⚙️ <b>Tryb demo</b> — live ceny i rekomendacje są aktywne.
        Skonfiguruj Google Sheets ze swoimi pozycjami żeby zobaczyć P&L.
        </div>""", unsafe_allow_html=True)

    # Only include positions where we have a live price (Val_PLN not None)
    priced      = pos[pos["Val_PLN"].notna()]
    total_val   = priced["Val_PLN"].sum()  or None
    total_cost  = priced["Cost_PLN"].sum() or None
    total_pnl   = priced["PnL_PLN"].sum()  or None
    pnl_pct     = (total_pnl / total_cost * 100) if total_pnl is not None and total_cost else None
    n_pos       = len(pos)

    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-icon">💼</div>
            <div class="kpi-label">Wartość portfela</div>
            <div class="kpi-value">{fmt_pln(total_val) if total_val else '—'}</div>
            <div class="kpi-sub {kpiclass(pnl_pct)}">{fmt_pct(pnl_pct) if pnl_pct else 'Uzupełnij pozycje'}</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon">📈</div>
            <div class="kpi-label">Total P&L</div>
            <div class="kpi-value {kpiclass(total_pnl)}">{fmt_pln(total_pnl) if total_pnl else '—'}</div>
            <div class="kpi-sub {kpiclass(pnl_pct)}">{fmt_pct(pnl_pct) if pnl_pct else '—'}</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon">🕐</div>
            <div class="kpi-label">Ostatnia aktualizacja</div>
            <div class="kpi-value" style="font-size:22px">{datetime.now().strftime('%H:%M')}</div>
            <div class="kpi-sub neu">{datetime.now().strftime('%d %b %Y')}</div>
        </div>
        <div class="kpi">
            <div class="kpi-icon">🎯</div>
            <div class="kpi-label">Pozycji</div>
            <div class="kpi-value">{n_pos}</div>
            <div class="kpi-sub neu">aktywnych</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Priority actions (manual text + live context z cen Yahoo)
    # Reguła widoczności: ticker w portfelu LUB rekomendacja BUY.
    # Pozycje zamknięte / czysto obserwacyjne (HOLD bez pozycji) nie zaśmiecają overview.
    pos_by_ticker = {row["Ticker"]: row for _, row in pos.iterrows()}
    prio = []
    for t, r in recs.items():
        if not r.get("priority_action"):
            continue
        in_pf = t in pos_by_ticker
        if not in_pf and r.get("recommendation") != "BUY":
            continue
        prio.append((t, r, in_pf))
    if prio:
        st.markdown('<div class="sh">⚡ Priorytetowe działania</div>', unsafe_allow_html=True)
        html = '<div class="actions">'
        for t, r, in_pf in sorted(prio, key=lambda x: REC_ORDER.get(x[1].get("recommendation","HOLD"), 3)):
            rec = r.get("recommendation", "HOLD")
            ac  = REC_ACTION.get(rec, "a-neu")
            dot = REC_DOT.get(rec, "dot-neu")
            # chipy liczone na żywo przy każdym renderze — teksty piszemy bez cen
            price = (prices or {}).get(t, {}).get("price")
            if price is None and in_pf:
                price = pos_by_ticker[t]["Cena"]
            entry = r.get("entry_point")
            fv    = r.get("fair_value")
            chips = []
            if in_pf:
                chips.append((f"{pos_by_ticker[t]['Ilość']:g} szt.", "#64748b"))
            if price is not None:
                chips.append((f"cena {price:,.2f}", "#94a3b8"))
                if entry:
                    if price <= entry:
                        chips.append((f"&#10003; poniżej entry {entry:,.0f}", "#10b981"))
                    else:
                        chips.append((f"entry {entry:,.0f} ({(price-entry)/entry*100:+.0f}% powyżej)", "#f59e0b"))
                if fv:
                    up = (fv - price) / price * 100
                    chips.append((f"FV {fv:,.0f} ({up:+.0f}%)", "#00d9a3" if up >= 0 else "#ef4444"))
            chips_html = "".join(
                f'<span style="background:rgba(255,255,255,0.05);border-radius:5px;'
                f'padding:2px 8px;font-size:11px;color:{c};white-space:nowrap">{txt}</span>'
                for txt, c in chips)
            html += f"""<div class="action {ac}" style="flex-wrap:wrap;row-gap:6px">
                <div class="action-dot {dot}"></div>
                <span class="action-ticker">{t}</span>
                <span style="color:#475569;font-size:12px">·</span>
                <span>{_e(r['priority_action'])}</span>
                <span style="display:inline-flex;gap:6px;flex-wrap:wrap;margin-left:auto">{chips_html}</span>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # ── Kalendarz wydarzeń (next_earnings + upcoming_events z recommendations.json)
    PL_M = {1:"sty",2:"lut",3:"mar",4:"kwi",5:"maj",6:"cze",7:"lip",8:"sie",9:"wrz",10:"paź",11:"lis",12:"gru"}
    today = datetime.now().date()
    cal = []
    for t, r in recs.items():
        in_pf = t in pos_by_ticker
        if not in_pf and r.get("recommendation") != "BUY":
            continue  # ta sama reguła co priorytety: portfel lub aktywne BUY
        ne = r.get("next_earnings")
        if ne and "X" not in str(ne):
            try:
                d = datetime.strptime(str(ne), "%Y-%m-%d").date()
                if d >= today:
                    cal.append((d, t, "Earnings", "earnings"))
            except Exception:
                pass
        for ev in r.get("upcoming_events") or []:
            try:
                d = datetime.strptime(str(ev.get("date", "")), "%Y-%m-%d").date()
            except Exception:
                continue
            if d >= today:
                cal.append((d, t, ev.get("event", ""), ev.get("type", "catalyst")))
    if cal:
        cal.sort(key=lambda x: x[0])
        st.markdown('<div class="sh">📅 Kalendarz wydarzeń</div>', unsafe_allow_html=True)
        html = '<div style="display:flex;flex-direction:column;gap:8px">'
        for d, t, txt, typ in cal[:12]:
            days = (d - today).days
            when = "DZIŚ" if days == 0 else "jutro" if days == 1 else f"za {days} dni"
            urg  = "#ef4444" if days <= 3 else "#f59e0b" if days <= 14 else "#64748b"
            icon = "📊" if typ == "earnings" else "⚡"
            html += f"""<div style="display:flex;align-items:center;gap:14px;background:rgba(255,255,255,0.03);
                        border:1px solid rgba(255,255,255,0.06);border-left:2px solid {urg};
                        border-radius:10px;padding:10px 16px;flex-wrap:wrap">
                <div style="font-family:'Courier New',monospace;font-size:12px;color:#94a3b8;min-width:90px">{d.day} {PL_M[d.month]} {d.year}</div>
                <span style="background:rgba(255,255,255,0.06);border-radius:5px;padding:2px 8px;font-size:11px;color:{urg};white-space:nowrap;min-width:60px;text-align:center">{when}</span>
                <span style="font-size:13px">{icon}</span>
                <span style="font-weight:700;font-size:13px;color:#e2e8f0;min-width:56px">{t}</span>
                <span style="font-size:12px;color:#94a3b8;flex:1">{_e(txt)}</span>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="sh">📊 Pozycje</div>', unsafe_allow_html=True)
    df = pos.sort_values("Val_PLN", ascending=False, na_position="last")
    rows_html = ""
    for _, r in df.iterrows():
        rec     = r["Rec"]
        row_cls = REC_ROW.get(rec, "row-hold")
        qty_s   = f'<span style="color:#e2e8f0">{r["Ilość"]:.4f}'.rstrip('0').rstrip('.') + '</span>'
        avg_s   = f'<span style="color:#94a3b8">{r["Avg"]:.2f} <span class="t-ccy">{r["Waluta"]}</span></span>' if r["Avg"] else "—"
        price_s = f'<span class="t-price">{r["Cena"]:.2f}</span> <span class="t-ccy">{r["Waluta"]}</span>' if r["Cena"] else "—"
        chg_s   = f'<span class="{pclass(r["Dzień%"])}">{fmt_pct(r["Dzień%"])}</span>' if r["Dzień%"] is not None else '<span class="t-neu">—</span>'
        val_s   = f'<span class="{pclass(r["Val_PLN"])}">{fmt_pln(r["Val_PLN"])}</span>' if r["Val_PLN"] else '<span class="t-neu">—</span>'
        pnl_s   = f'<span class="{pclass(r["PnL_PLN"])}">{fmt_pln(r["PnL_PLN"])}</span>' if r["PnL_PLN"] is not None else '<span class="t-neu">—</span>'
        # P&L combined
        if r["PnL_PLN"] is not None and r["PnL%"] is not None:
            pnl_combined = f'<span class="{pclass(r["PnL_PLN"])}">{fmt_pln(r["PnL_PLN"])}</span><br><span class="{pclass(r["PnL%"])}" style="font-size:10px">{fmt_pct(r["PnL%"])}</span>'
        else:
            pnl_combined = '<span class="t-neu">—</span>'

        fv_s    = f'<span class="t-fv">{r["FV"]:.0f} <span class="t-ccy">{r["FV_ccy"]}</span></span>' if r["FV"] else '<span class="t-neu">—</span>'
        up_s    = f'<span class="{pclass(r["Upside"])}">{fmt_pct(r["Upside"])}</span>' if r["Upside"] is not None else '<span class="t-neu">—</span>'
        badge   = f'<span class="badge b-{rec}">{rec}</span>' if rec != "—" else "—"
        entry_s = f'<span style="color:#10b981;font-weight:600;font-size:11px">{r["Entry"]:.0f}</span> <span class="t-ccy">{r["FV_ccy"]}</span>' if r["Entry"] else '<span class="t-neu">—</span>'
        tb      = str(r["Thesis_breaker"]).replace('"', '&quot;').replace('<', '&lt;').replace('>', '&gt;')
        if rec == "SELL":
            exit_s = '<span style="color:#ef4444;font-weight:600">Sprzedaj</span>'
        elif tb and tb != "None":
            short_tb = (tb[:32] + "…") if len(tb) > 32 else tb
            exit_s = f'<span style="font-size:10px;color:#64748b">{short_tb}</span>'
        else:
            exit_s = '<span class="t-neu">—</span>'

        mc_val = (mkt_cap or {}).get(r['Ticker'])
        mc_s   = f'<span style="color:#64748b;font-size:10px">{fmt_cap(mc_val)}</span>' if mc_val else '<span class="t-neu">—</span>'
        rows_html += f"""<tr class="{row_cls}">
            <td><span class="t-ticker">{r['Ticker']}</span></td>
            <td><span class="t-name">{r['Nazwa']}</span></td>
            <td>{qty_s}</td><td>{avg_s}</td>
            <td>{price_s}</td><td>{chg_s}</td><td>{mc_s}</td>
            <td>{val_s}</td><td style="white-space:normal;line-height:1.4">{pnl_combined}</td>
            <td>{entry_s}</td><td>{fv_s}</td><td>{up_s}</td>
            <td style="max-width:140px;white-space:normal;line-height:1.4">{exit_s}</td>
            <td>{badge}</td>
        </tr>"""

    st.markdown(f"""
    <div class="pos-table-wrap">
    <table class="pos-table">
        <thead><tr>
            <th>Ticker</th><th>Nazwa</th><th>Szt.</th><th>Śr. cena</th>
            <th>Cena</th><th>Dzień%</th><th>Mkt Cap</th>
            <th>Wartość</th><th>P&amp;L</th>
            <th>Entry</th><th>FV</th><th>Upside</th>
            <th>Wyjście</th><th>Rec</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)

# ─── PAGE: DETAIL ─────────────────────────────────────────────────────────────
def page_detail(ticker, pos, prices, recs):
    rec  = recs.get(ticker, {})
    rec["_ticker"] = ticker
    row  = pos[pos["Ticker"] == ticker]
    row  = row.iloc[0] if not row.empty else None

    recommendation = rec.get("recommendation", "—")
    fv   = rec.get("fair_value")
    fv_c = rec.get("fair_value_currency", "")
    ep   = rec.get("entry_point")

    price  = row["Cena"]    if row is not None else prices.get(ticker, {}).get("price")
    ccy    = row["Waluta"]  if row is not None else fv_c
    chg    = row["Dzień%"]  if row is not None else None
    pnl    = row["PnL_PLN"] if row is not None else None
    pnl_p  = row["PnL%"]   if row is not None else None
    val    = row["Val_PLN"] if row is not None else None
    upside = (fv - price) / price * 100 if fv and price else rec.get("upside_pct")

    # ── Header
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div>
            <div style="font-size:28px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px">{rec.get('name', ticker)}</div>
            <div style="font-size:13px;color:#475569;margin-top:3px">{ticker} · {ccy}</div>
        </div>
        <div style="margin-left:auto;display:flex;align-items:center;gap:12px">
            <span class="badge b-{recommendation}" style="font-size:12px;padding:5px 14px">{recommendation}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── KPI row
    ep_txt = f"{ep:.0f} {fv_c}" if ep else "—"
    st.markdown(f"""
    <div class="detail-grid">
        <div class="dcard">
            <div class="dcard-label">Cena aktualna</div>
            <div class="dcard-value">{f"{price:.2f}" if price else "—"} <span style="font-size:14px;color:#475569">{ccy}</span></div>
            <div class="dcard-sub {kpiclass(chg)}">{fmt_pct(chg)} dziś</div>
        </div>
        <div class="dcard">
            <div class="dcard-label">Fair Value (DCF)</div>
            <div class="dcard-value">{f"{fv:.0f}" if fv else "—"} <span style="font-size:14px;color:#475569">{fv_c}</span></div>
            <div class="dcard-sub {kpiclass(upside)}">{fmt_pct(upside)} upside</div>
        </div>
        <div class="dcard">
            <div class="dcard-label">Wartość pozycji</div>
            <div class="dcard-value">{fmt_pln(val) if val else '—'}</div>
            <div class="dcard-sub {kpiclass(pnl)}">{fmt_pln(pnl)} ({fmt_pct(pnl_p)})</div>
        </div>
        <div class="dcard">
            <div class="dcard-label">Punkt wejścia</div>
            <div class="dcard-value" style="font-size:20px">{ep_txt}</div>
            <div class="dcard-sub neu">Margin of safety 20–30%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Entry / Exit bar — always visible
    tb = rec.get("thesis_breaker", "")
    if recommendation == "SELL":
        entry_html = '<span style="color:#ef4444;font-size:15px;font-weight:700">Sprzedaj — nie dokupuj</span>'
        exit_html  = '<span style="color:#ef4444;font-size:15px;font-weight:700">Wyjdź z pozycji natychmiast</span>'
    else:
        ep_color   = "#10b981" if ep and price and price <= ep * 1.05 else "#f59e0b"
        entry_html = f'<span style="color:{ep_color};font-size:16px;font-weight:700">{ep_txt}</span><span style="color:#475569;font-size:12px;margin-left:8px">rekomendowany entry z 20–30% MoS</span>' if ep else '<span style="color:#475569">Brak konkretnego entry — obserwuj</span>'

        # Drabinka wyjścia (konstytucja pkt 7) — standard sekcji "Kiedy wychodzić"
        ptype  = rec.get("position_type")
        dcf_d  = rec.get("dcf") or {}
        wfv    = dcf_d.get("fair_value_weighted") or dcf_d.get("weighted_fv")
        scen_d = dcf_d.get("scenarios") or (dcf_d.get("alt_valuation") or {}).get("scenarios")
        bull_fv = None
        if scen_d:
            items = list(scen_d.values()) if isinstance(scen_d, dict) else scen_d
            fvs = [s.get("fair_value") or s.get("fv_per_share")
                   for s in items if isinstance(s, dict)]
            fvs = [v for v in fvs if v]
            bull_fv = max(fvs) if fvs else None
        rungs = []   # (próg, etykieta, akcja, czy_trigger)
        if ptype == "compounder":
            if fv:      rungs.append((fv,      f"FV base {fv:.0f} {fv_c}",   "nie sprzedajemy — compounder, FV rośnie z czasem", False))
            if bull_fv: rungs.append((bull_fv, f"&gt; bull {bull_fv:.0f} {fv_c}", "obowiązkowa decyzja: REDUCE albo rewizja scenariuszy", True))
        elif ptype == "moonshot":
            if fv:      rungs.append((fv,      f"&ge; base {fv:.0f} {fv_c}",     "trim 25–33% — odzyskaj koszt", True))
            if wfv:     rungs.append((wfv,     f"&ge; weighted {wfv:.0f} {fv_c}", "trim do ~50% pozycji", True))
            if bull_fv: rungs.append((bull_fv, f"&ge; bull {bull_fv:.0f} {fv_c}", "redukcja do rdzenia ~25% (rdzeń trzyma ogon)", True))
        if rungs:
            rows = ""
            for thr, lbl, act, is_trig in rungs:
                hit   = price is not None and thr and price >= thr and is_trig
                col   = "#f59e0b" if hit else ("#94a3b8" if is_trig else "#475569")
                badge = (' <span style="background:rgba(245,158,11,0.15);color:#f59e0b;border-radius:4px;'
                         'padding:1px 6px;font-size:10px;font-weight:700">AKTYWNY</span>') if hit else ""
                mark  = "🔔" if hit else ("·" if is_trig else "—")
                rows += (f'<div style="display:flex;gap:8px;font-size:12.5px;margin-top:5px;align-items:baseline">'
                         f'<span style="width:16px">{mark}</span>'
                         f'<span style="color:{col};font-weight:600;min-width:160px">{lbl}</span>'
                         f'<span style="color:#64748b">{act}{badge}</span></div>')
            t_lbl = "COMPOUNDER" if ptype == "compounder" else "MOONSHOT"
            exit_html = (f'<div style="font-size:10px;color:#475569;letter-spacing:0.5px">Drabinka wyjścia · {t_lbl}'
                         + (f' · cena {price:.2f} {fv_c}' if price else '') + '</div>' + rows)
        elif fv:
            exit_html = f'<span style="color:#f59e0b;font-size:16px;font-weight:700">{fv:.0f} {fv_c}</span><span style="color:#475569;font-size:12px;margin-left:8px">brak position_type — drabinka po klasyfikacji</span>'
        else:
            exit_html = '<span style="color:#475569;font-size:13px">Brak ceny docelowej — patrz thesis breaker poniżej</span>'

    tb_html = f'<div style="margin-top:10px;padding-top:10px;border-top:1px solid rgba(239,68,68,0.15);font-size:13px;color:#fca5a5"><span style="color:#ef4444;font-weight:600;margin-right:8px">⛔ Thesis Breaker:</span>{_e(tb)}</div>' if tb else ""

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:20px">
        <div style="background:rgba(16,185,129,0.05);border:1px solid rgba(16,185,129,0.15);border-radius:14px;padding:16px 20px">
            <div style="font-size:10px;font-weight:600;color:#10b981;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px">🟢 Kiedy wchodzić</div>
            {entry_html}
        </div>
        <div style="background:rgba(239,68,68,0.05);border:1px solid rgba(239,68,68,0.15);border-radius:14px;padding:16px 20px">
            <div style="font-size:10px;font-weight:600;color:#ef4444;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px">🔴 Kiedy wychodzić</div>
            {exit_html}
            {tb_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs
    t_wykres, t_dcf, t_actions, t_teza = st.tabs(["📈 Wykres", "📐 DCF", "⚡ Działania", "💡 Teza"])

    with t_wykres:
        # (okres, interwał) — granularność dobrana automatycznie do zakresu
        periods = {"1M": ("1mo", "1d"), "3M": ("3mo", "1d"), "6M": ("6mo", "1d"),
                   "1Y": ("1y", "1d"), "3Y": ("3y", "1wk")}
        sel = st.radio("Okres", list(periods.keys()), horizontal=True, index=2,
                       key=f"p_{ticker}", label_visibility="collapsed")
        per, itv = periods[sel]
        fig = price_chart(ticker, per, ep, fv, itv)
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.info("Brak danych historycznych dla tego tickera.")

        # Key metrics inline under chart
        if price and fv:
            dist_to_fv = (fv - price) / price * 100
            dist_to_ep = (price - ep) / ep * 100 if ep else None
            col1, col2, col3 = st.columns(3)
            with col1:
                cl = "pos" if dist_to_fv > 0 else "neg"
                st.markdown(f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:16px;text-align:center">
                    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px">Dystans do FV</div>
                    <div style="font-size:20px;font-weight:700" class="{cl}">{fmt_pct(dist_to_fv)}</div>
                </div>""", unsafe_allow_html=True)
            with col2:
                if ep:
                    above = price > ep
                    cl2 = "neg" if above else "pos"
                    label = "powyżej entry" if above else "poniżej entry"
                    st.markdown(f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:16px;text-align:center">
                        <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px">vs Entry Point</div>
                        <div style="font-size:20px;font-weight:700" class="{cl2}">{fmt_pct(dist_to_ep)} {label}</div>
                    </div>""", unsafe_allow_html=True)
            with col3:
                upd = rec.get("last_updated", "—")
                st.markdown(f"""<div style="background:{CARD};border:1px solid {BORDER};border-radius:12px;padding:16px;text-align:center">
                    <div style="font-size:10px;color:#475569;text-transform:uppercase;letter-spacing:1.2px;margin-bottom:6px">Analiza z dnia</div>
                    <div style="font-size:16px;font-weight:700;color:#f8fafc">{upd}</div>
                </div>""", unsafe_allow_html=True)

    with t_dcf:
        tab_dcf(rec)

    with t_actions:
        tab_actions(rec, row, prices)

    with t_teza:
        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.markdown('<div class="sh">💡 Teza inwestycyjna</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="thesis-card">{_e(rec.get("thesis_full","Brak danych."))}</div>', unsafe_allow_html=True)
            tb = rec.get("thesis_breaker", "—")
            st.markdown(f"""
            <div class="breaker-card">
                <div style="font-size:10px;font-weight:600;color:#f87171;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px">⛔ Thesis Breaker — kiedy sprzedać</div>
                <div style="color:#fca5a5;font-size:14px;line-height:1.65">{_e(tb)}</div>
            </div>""", unsafe_allow_html=True)

        with col_r:
            st.markdown('<div class="sh">⚠️ Ryzyka</div>', unsafe_allow_html=True)
            for risk in rec.get("risks", []):
                st.markdown(f'<div class="risk-item">· {risk}</div>', unsafe_allow_html=True)

            moat = rec.get("buffett_moat", "—")
            ne   = rec.get("next_earnings")
            upd  = rec.get("last_updated", "—")
            ne_html = f'<div style="margin-top:12px"><div style="font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px">Następny earnings</div><div style="color:{ACCENT};font-size:14px;font-weight:600">{ne}</div></div>' if ne else ""
            st.markdown(f"""
            <div class="moat-card">
                <div style="font-size:10px;font-weight:600;color:#00d9a3;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">Buffett MOAT</div>
                <div style="color:#e0e7ff;font-size:16px;font-weight:700">🏰 {moat}</div>
                <div style="margin-top:12px;font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px">Analiza z dnia</div>
                <div style="color:#64748b;font-size:13px;margin-top:3px">{upd}</div>
                {ne_html}
            </div>""", unsafe_allow_html=True)

        # ── Profil CEO (gdy istnieje w danych)
        ceo = rec.get("ceo_profile")
        if ceo:
            verdict = ceo.get("verdict", "")
            v_up = verdict.upper()
            vc = "#10b981" if ("GLODNY" in v_up or "GŁODNY" in v_up) and ("EKSPERT" in v_up) \
                 else "#ef4444" if "SYTY" in v_up else "#f59e0b"
            rows = ""
            for key, label in [("background", "Kim jest"), ("hunger", "Głód"),
                               ("domain_expertise", "Ekspertyza domenowa"),
                               ("track_record", "Track record"),
                               ("skin_in_the_game", "Skin in the game"),
                               ("capital_allocation", "Alokacja kapitału"),
                               ("red_flags", "Czerwone flagi")]:
                val = ceo.get(key)
                if val:
                    warn_style = "color:#f59e0b" if "BRAK POTWIERDZENIA" in str(val).upper() else "color:#94a3b8"
                    rows += (f'<div style="margin-bottom:10px"><div style="font-size:10px;font-weight:600;'
                             f'color:#475569;text-transform:uppercase;letter-spacing:1.2px">{label}</div>'
                             f'<div style="{warn_style};font-size:12.5px;line-height:1.6">{_e(val)}</div></div>')
            st.markdown(f"""
            <div style="margin-top:20px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-radius:14px;padding:18px 22px">
                <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:14px">
                    <div><span style="font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px">👤 Profil CEO</span>
                    <div style="color:#e2e8f0;font-size:16px;font-weight:700;margin-top:2px">{_e(ceo.get('name','—'))}
                    <span style="color:#475569;font-size:12px;font-weight:400"> · CEO od {_e(ceo.get('ceo_since','—'))}</span></div></div>
                    <span style="background:{vc}22;border:1px solid {vc}55;color:{vc};border-radius:8px;padding:4px 12px;font-size:12px;font-weight:700">{_e(verdict)}</span>
                </div>
                {rows}
            </div>""", unsafe_allow_html=True)

        # ── Mapa konkurencji (gdy istnieje)
        comp = rec.get("competitive_landscape")
        if comp:
            st.markdown('<div class="sh" style="margin-top:20px">⚔️ Mapa konkurencji</div>', unsafe_allow_html=True)
            t_colors = {"wysokie": "#ef4444", "średnie": "#f59e0b", "srednie": "#f59e0b", "niskie": "#64748b"}
            html = '<div style="display:flex;flex-direction:column;gap:8px">'
            for c in comp:
                tc = t_colors.get(str(c.get("threat", "")).lower(), "#64748b")
                tick = f' <span style="color:#475569;font-size:11px">({_e(c["ticker"])})</span>' if c.get("ticker") else \
                       ' <span style="color:#475569;font-size:11px">(prywatna)</span>'
                html += f"""<div style="background:rgba(255,255,255,0.03);border-left:2px solid {tc};
                            border-radius:0 10px 10px 0;padding:10px 16px">
                    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:6px">
                        <span style="color:#e2e8f0;font-weight:700;font-size:13px">{_e(c.get('name','—'))}{tick}</span>
                        <span style="color:{tc};font-size:11px;font-weight:700;text-transform:uppercase">zagrożenie: {_e(c.get('threat','—'))}</span>
                    </div>
                    <div style="color:#94a3b8;font-size:12px;margin-top:3px">{_e(c.get('segment',''))}</div>
                    <div style="color:#64748b;font-size:11.5px;margin-top:3px">{_e(c.get('note',''))}
                        <span style="color:#334155"> · źródło: {_e(c.get('source','—'))}</span></div>
                </div>"""
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)

        # ── Buffett Tenets checklist (gdy istnieje)
        tenets = rec.get("buffett_tenets")
        if tenets:
            st.markdown('<div class="sh" style="margin-top:20px">📋 Buffett Tenets</div>', unsafe_allow_html=True)
            LABELS = {"business_simple": "Biznes prosty i zrozumiały", "business_consistent_history": "Spójna historia operacyjna",
                      "business_longterm_prospects": "Perspektywy długoterminowe", "mgmt_rational": "Management racjonalny",
                      "mgmt_candid": "Szczerość wobec akcjonariuszy", "mgmt_institutional_imperative": "Odporność na imperatyw instytucjonalny",
                      "fin_roe": "ROE (nie EPS)", "fin_margins": "Wysokie marże", "fin_dollar_test": "Test $1 za $1",
                      "fin_owner_earnings": "Owner earnings"}
            MARK = {"OK": ("✅", "#10b981"), "UWAGA": ("⚠️", "#f59e0b")}
            html = '<div style="display:flex;flex-direction:column;gap:6px">'
            for key, item in tenets.items():
                if key == "wniosek" or not isinstance(item, dict):
                    continue
                mark, mc = MARK.get(str(item.get("ocena", "")).upper(), ("❌", "#ef4444"))
                html += f"""<div style="display:flex;gap:10px;align-items:baseline;background:rgba(255,255,255,0.02);
                            border-radius:8px;padding:7px 12px">
                    <span style="font-size:13px">{mark}</span>
                    <span style="color:#e2e8f0;font-size:12.5px;font-weight:600;min-width:230px">{LABELS.get(key, key)}</span>
                    <span style="color:#64748b;font-size:12px">{_e(item.get('uzasadnienie',''))}</span>
                </div>"""
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
            if tenets.get("wniosek"):
                st.markdown(f"""<div style="margin-top:10px;background:rgba(0,217,163,0.06);border:1px solid rgba(0,217,163,0.2);
                    border-radius:10px;padding:10px 16px;font-size:12.5px;color:#94a3b8">
                    <b style="color:#00d9a3">Wniosek dla pozycji:</b> {_e(tenets['wniosek'])}</div>""", unsafe_allow_html=True)

# ─── CHAT HISTORY PERSISTENCE ────────────────────────────────────────────────
CHAT_HISTORY_FILE = "data/chat_history.json"
CHAT_CONTEXT_LIMIT = 20  # max messages sent to API (saves tokens)

def _gist_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}

def _load_all_chat(token: str = None, gist_id: str = None) -> dict:
    """Load full chat history dict {context: [messages]} from Gist or local file."""
    import requests as _req
    if token and gist_id:
        try:
            r = _req.get(f"https://api.github.com/gists/{gist_id}",
                         headers=_gist_headers(token), timeout=6)
            if r.status_code == 200:
                raw = r.json().get("files", {}).get("chat_history.json", {}).get("content", "{}")
                data = json.loads(raw)
                if isinstance(data, list):        # migrate old format
                    return {"overview": data}
                return data if isinstance(data, dict) else {}
        except Exception:
            pass
    try:
        with open(CHAT_HISTORY_FILE, encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {"overview": data}
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def load_chat_history(token: str = None, gist_id: str = None, context: str = "overview") -> list:
    if "_all_chat" not in st.session_state:
        st.session_state["_all_chat"] = _load_all_chat(token, gist_id)
    return st.session_state["_all_chat"].get(context, [])

def save_chat_history(messages: list, token: str = None, gist_id: str = None, context: str = "overview"):
    import requests as _req
    if "_all_chat" not in st.session_state:
        st.session_state["_all_chat"] = {}
    st.session_state["_all_chat"][context] = messages
    payload = json.dumps(st.session_state["_all_chat"], ensure_ascii=False, indent=2)
    if token and gist_id:
        try:
            _req.patch(f"https://api.github.com/gists/{gist_id}",
                       headers=_gist_headers(token),
                       json={"files": {"chat_history.json": {"content": payload}}},
                       timeout=6)
        except Exception:
            pass
    try:
        with open(CHAT_HISTORY_FILE, "w", encoding="utf-8") as f:
            f.write(payload)
    except Exception:
        pass

# ─── PAGE: CHAT ───────────────────────────────────────────────────────────────
def build_system_prompt(pos, recs, prices, fx, watchlist=None):
    portfolio_lines = []
    for _, r in pos.iterrows():
        price = r["Cena"]
        pnl   = r["PnL_PLN"]
        portfolio_lines.append(
            f"- {r['Ticker']} ({r['Nazwa']}): {r['Ilość']} szt., avg {r['Avg']:.2f} {r['Waluta']}, "
            f"cena {f'{price:.2f}' if price else 'N/A'}, P&L {f'{pnl:+.0f} PLN' if pnl else 'N/A'}"
        )
    rec_lines = []
    for t, rec in recs.items():
        fv  = rec.get("fair_value")
        cur = prices.get(t, {}).get("price")
        upside = f"{(fv-cur)/cur*100:+.0f}%" if fv and cur else "N/A"
        rec_lines.append(
            f"- {t}: {rec.get('recommendation','?')} | FV {fv} {rec.get('fair_value_currency','')} | "
            f"upside {upside} | {rec.get('thesis_short','')}"
        )
    watch_section = ""
    if watchlist:
        watch_lines = []
        for sector, stocks in watchlist.items():
            if stocks:
                names = ", ".join(f"{s['ticker']} ({s.get('name','')})" for s in stocks)
                watch_lines.append(f"  {sector}: {names}")
        if watch_lines:
            watch_section = "\nWATCHLISTA (obserwowane, nie w portfelu):\n" + "\n".join(watch_lines)
    return f"""Jesteś profesjonalnym doradcą inwestycyjnym. Analizujesz spółki moonshot (AI, Energy/fusion/SMR, Space).
Masz dostęp do narzędzi web_search, add_to_watchlist, remove_from_watchlist, update_recommendation.

PROFIL INWESTORA:
- Horyzont: 1–3 lata | Kapitał: 50k–250k PLN | Ryzyko: wysoka tolerancja, szuka 10–50x
- Giełdy: globalny mandat (US, EU, PL) | Narzędzia: Morningstar, DCF

AKTUALNY PORTFEL (live ceny z yfinance):
{chr(10).join(portfolio_lines) if portfolio_lines else 'Brak danych'}

REKOMENDACJE I FAIR VALUES:
{chr(10).join(rec_lines)}{watch_section}

FX: USD/PLN {fx.get('USD',0):.3f} | EUR/PLN {fx.get('EUR',0):.3f} | HKD/PLN {fx.get('HKD',0):.3f}

ZASADY ODPOWIEDZI:
- Używaj web_search dla aktualnych danych — zawsze szukaj przed odpowiedzią na pytania o spółki
- Odpowiedzi muszą być SZCZEGÓŁOWE i ANALITYCZNE — nie dawaj ogólników
- Przy każdej wycenie podaj: konkretny WACC, growth rate, fair value, entry point, margin of safety %
- Zawsze oceniaj przez pryzmat Buffett tenets: moat (wide/narrow/none), management quality, business simplicity
- Wskaż top 3 ryzyka z konkretnym wpływem na wycenę (np. "ryzyko X obniża FV o ~15%")
- Uwzględnij czynnik geopolityczny — jak napięcia geopolityczne wpływają na tezę
- Zawsze podaj rekomendację: BUY/HOLD/SELL/REDUCE z konkretnym entry pointem i thesis breakerem
- Porównaj z danymi portfela użytkownika gdy relevant (ma pozycję? jaki P&L?)
- Odpowiadaj po polsku, w formacie markdown z nagłówkami
- Dzisiejsza data: {datetime.now().strftime('%Y-%m-%d')}

WATCHLISTA — zasady:
- Dodaj spółkę: add_to_watchlist gdy użytkownik prosi "dodaj X do watchlisty" lub podobnie
- Usuń spółkę: remove_from_watchlist gdy użytkownik prosi "usuń X z watchlisty"
- Sektory: {', '.join(WATCHLIST_SECTORS)}

REKOMENDACJE (update_recommendation):
- Działa dla KAŻDEGO tickera — zarówno z portfela jak i z watchlisty (tworzy nowy wpis jeśli nie istnieje)
- Gdy użytkownik prosi o "zapisz analizę", "dodaj rekomendację", "zapisz wyniki" → użyj tego narzędzia
- Zapisuj wszystkie dostępne pola: name, fair_value, fair_value_currency, entry_point, thesis_short, thesis_full, thesis_breaker, buffett_moat, risks (oddzielone |), event_text
- Przed zapisem ZAWSZE podsumuj kluczowe liczby (FV, entry, rec) i poczekaj na potwierdzenie
- Po aktualizacji poinformuj użytkownika że dashboard odświeży się za ~1 minutę"""

SEARCH_TOOL = {
    "name": "web_search",
    "description": "Wyszukuje aktualne informacje w internecie. Używaj dla newsów, wyników finansowych, aktualnych cen, wydarzeń rynkowych.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Zapytanie wyszukiwania po angielsku dla lepszych wyników finansowych"}
        },
        "required": ["query"]
    }
}

UPDATE_REC_TOOL = {
    "name": "update_recommendation",
    "description": "Tworzy lub aktualizuje pełną rekomendację spółki na dashboardzie (działa też dla spółek z watchlisty, nie tylko portfela). UŻYWAJ gdy użytkownik prosi o zapisanie analizy lub WYRAŹNIE potwierdza zmianę.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker":             {"type": "string", "description": "Ticker np. RKLB, MSFT, RHM.DE"},
            "recommendation":     {"type": "string", "enum": ["BUY","HOLD","SELL","REDUCE"]},
            "name":               {"type": "string", "description": "Pełna nazwa spółki"},
            "fair_value":         {"type": "number", "description": "Fair value na akcję z DCF"},
            "fair_value_currency":{"type": "string", "description": "Waluta fair value np. USD, EUR, PLN"},
            "entry_point":        {"type": "number", "description": "Rekomendowana cena wejścia (z margin of safety)"},
            "thesis_short":       {"type": "string", "description": "Teza inwestycyjna — 1 zdanie"},
            "thesis_full":        {"type": "string", "description": "Pełna teza inwestycyjna — 3-5 zdań z kluczowymi argumentami"},
            "thesis_breaker":     {"type": "string", "description": "Kiedy sprzedać — konkretny warunek łamania tezy"},
            "buffett_moat":       {"type": "string", "description": "Ocena moat: wide/narrow/none + krótkie uzasadnienie"},
            "risks":              {"type": "string", "description": "Top 3 ryzyka oddzielone znakiem | np. 'Ryzyko A | Ryzyko B | Ryzyko C'"},
            "priority_action":    {"type": "string", "description": "Priorytetowe działanie widoczne na overview (puste = brak)"},
            "event_text":         {"type": "string", "description": "Opis analizy/zmiany — pojawi się w timeline wydarzeń"}
        },
        "required": ["ticker", "recommendation"]
    }
}

ADD_WATCHLIST_TOOL = {
    "name": "add_to_watchlist",
    "description": "Dodaje spółkę do listy obserwowanych. Używaj gdy użytkownik prosi o dodanie do watchlisty.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker":  {"type": "string", "description": "Ticker spółki np. RKLB, IONQ, PLTR"},
            "name":    {"type": "string", "description": "Pełna nazwa spółki"},
            "sector":  {"type": "string", "enum": ["Space", "Defence", "AI", "Energy", "Quantum", "Robots", "Health"]},
            "note":    {"type": "string", "description": "Krótka notatka dlaczego obserwujemy (1-2 zdania)"}
        },
        "required": ["ticker", "name", "sector"]
    }
}

REMOVE_WATCHLIST_TOOL = {
    "name": "remove_from_watchlist",
    "description": "Usuwa spółkę z listy obserwowanych.",
    "input_schema": {
        "type": "object",
        "properties": {
            "ticker": {"type": "string", "description": "Ticker spółki do usunięcia"}
        },
        "required": ["ticker"]
    }
}

GH_REPO = "arturstankiewicz11-lab/invest-dashboard"
GH_REC_PATH = "data/recommendations.json"

def do_update_recommendation(inputs: dict, gh_token: str) -> str:
    import requests as _req, base64 as _b64
    api = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_REC_PATH}"
    hdrs = {"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"}

    r = _req.get(api, headers=hdrs, timeout=10)
    if r.status_code != 200:
        return f"Błąd pobierania pliku z GitHub: {r.status_code}"

    sha     = r.json()["sha"]
    current = json.loads(_b64.b64decode(r.json()["content"]).decode())
    ticker  = inputs["ticker"]

    # Allow creating new entries (e.g. for watchlist stocks)
    if ticker not in current:
        current[ticker] = {"events": []}

    rec = current[ticker]
    rec["recommendation"] = inputs["recommendation"]
    rec["last_updated"]   = datetime.now().strftime("%Y-%m-%d")
    if inputs.get("name"):                        rec["name"]               = inputs["name"]
    if inputs.get("fair_value")      is not None: rec["fair_value"]         = inputs["fair_value"]
    if inputs.get("fair_value_currency"):         rec["fair_value_currency"]= inputs["fair_value_currency"]
    if inputs.get("entry_point")     is not None: rec["entry_point"]        = inputs["entry_point"]
    if inputs.get("thesis_short"):                rec["thesis_short"]       = inputs["thesis_short"]
    if inputs.get("thesis_full"):                 rec["thesis_full"]        = inputs["thesis_full"]
    if inputs.get("thesis_breaker"):              rec["thesis_breaker"]     = inputs["thesis_breaker"]
    if inputs.get("buffett_moat"):                rec["buffett_moat"]       = inputs["buffett_moat"]
    if inputs.get("risks"):
        rec["risks"] = [r.strip() for r in inputs["risks"].split("|") if r.strip()]
    if "priority_action" in inputs:               rec["priority_action"]    = inputs.get("priority_action") or None

    if inputs.get("event_text"):
        rec.setdefault("events", []).insert(0, {
            "date":   datetime.now().strftime("%Y-%m-%d"),
            "event":  inputs["event_text"],
            "impact": "neutral",
            "fv_note": f"Rekomendacja zmieniona na {inputs['recommendation']}."
        })

    new_content = _b64.b64encode(json.dumps(current, ensure_ascii=False, indent=2).encode()).decode()
    put = _req.put(api, headers=hdrs, json={
        "message": f"chore: update {ticker} → {inputs['recommendation']} via chat",
        "content": new_content,
        "sha": sha
    }, timeout=10)

    if put.status_code in (200, 201):
        try:
            with open("data/recommendations.json", "w", encoding="utf-8") as _f:
                json.dump(current, _f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        load_recs.clear()
        return f"✅ Rekomendacja **{ticker}** zaktualizowana na **{inputs['recommendation']}**."
    return f"Błąd zapisu do GitHub: {put.status_code} — {put.text[:300]}"

def do_add_to_watchlist(inputs: dict, gh_token: str) -> str:
    import requests as _req, base64 as _b64
    api  = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_WATCHLIST_PATH}"
    hdrs = {"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"}
    r = _req.get(api, headers=hdrs, timeout=10)
    if r.status_code != 200:
        return f"Błąd pobierania watchlisty z GitHub: {r.status_code}"
    sha     = r.json()["sha"]
    current = json.loads(_b64.b64decode(r.json()["content"]).decode())
    ticker  = inputs["ticker"].strip().upper()
    sector  = inputs["sector"]
    if sector not in WATCHLIST_SECTORS:
        return f"Nieznany sektor: {sector}. Dostępne: {', '.join(WATCHLIST_SECTORS)}"
    for s in WATCHLIST_SECTORS:
        for item in current.get(s, []):
            if item.get("ticker", "").upper() == ticker:
                return f"Ticker {ticker} już jest na watchliście (sektor: {s})"
    current.setdefault(sector, []).append({
        "ticker": ticker, "name": inputs.get("name", ticker),
        "note": inputs.get("note", ""), "added": datetime.now().strftime("%Y-%m-%d")
    })
    new_content = _b64.b64encode(json.dumps(current, ensure_ascii=False, indent=2).encode()).decode()
    put = _req.put(api, headers=hdrs, json={
        "message": f"chore: add {ticker} to watchlist ({sector})",
        "content": new_content, "sha": sha
    }, timeout=10)
    if put.status_code in (200, 201):
        try:
            with open("data/watchlist.json", "w", encoding="utf-8") as _f:
                json.dump(current, _f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        load_watchlist.clear()
        st.session_state["_watchlist_dirty"] = True
        return f"✅ **{ticker}** ({inputs.get('name', ticker)}) dodany do watchlisty, sektor: **{sector}**."
    return f"Błąd zapisu do GitHub: {put.status_code}"

def do_remove_from_watchlist(inputs: dict, gh_token: str) -> str:
    import requests as _req, base64 as _b64
    api  = f"https://api.github.com/repos/{GH_REPO}/contents/{GH_WATCHLIST_PATH}"
    hdrs = {"Authorization": f"Bearer {gh_token}", "Accept": "application/vnd.github+json"}
    r = _req.get(api, headers=hdrs, timeout=10)
    if r.status_code != 200:
        return f"Błąd pobierania watchlisty: {r.status_code}"
    sha     = r.json()["sha"]
    current = json.loads(_b64.b64decode(r.json()["content"]).decode())
    ticker  = inputs["ticker"].strip().upper()
    removed = False
    for s in WATCHLIST_SECTORS:
        before = len(current.get(s, []))
        current[s] = [i for i in current.get(s, []) if i.get("ticker", "").upper() != ticker]
        if len(current[s]) < before:
            removed = True
    if not removed:
        return f"Ticker {ticker} nie znaleziono na watchliście."
    new_content = _b64.b64encode(json.dumps(current, ensure_ascii=False, indent=2).encode()).decode()
    put = _req.put(api, headers=hdrs, json={
        "message": f"chore: remove {ticker} from watchlist",
        "content": new_content, "sha": sha
    }, timeout=10)
    if put.status_code in (200, 201):
        try:
            with open("data/watchlist.json", "w", encoding="utf-8") as _f:
                json.dump(current, _f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        load_watchlist.clear()
        st.session_state["_watchlist_dirty"] = True
        return f"✅ **{ticker}** usunięty z watchlisty."
    return f"Błąd zapisu do GitHub: {put.status_code}"

def do_search(query: str, tavily_key: str) -> str:
    try:
        from tavily import TavilyClient
        client  = TavilyClient(api_key=tavily_key)
        results = client.search(query=query, max_results=5, search_depth="basic")
        lines   = []
        for r in results.get("results", []):
            lines.append(f"**{r.get('title','')}** ({r.get('url','')})\n{r.get('content','')[:400]}")
        return "\n\n---\n\n".join(lines) if lines else "Brak wyników."
    except Exception as e:
        return f"[Web search niedostępny: {e}] Odpowiadam na podstawie wiedzy."

def render_chat(pos, recs, prices, fx, current_ticker=None, watchlist=None):
    try:
        api_key = st.secrets["anthropic"]["api_key"]
    except Exception:
        return
    try:
        tavily_key = st.secrets["tavily"]["api_key"]
    except Exception:
        tavily_key = None
    try:
        gh_token  = st.secrets["github"]["token"]
        gh_gist   = st.secrets["github"]["gist_id"]
    except Exception:
        gh_token = gh_gist = None

    context  = current_ticker if current_ticker else "overview"
    sess_key = f"chat_{context}"

    if sess_key not in st.session_state:
        st.session_state[sess_key] = load_chat_history(gh_token, gh_gist, context)

    msgs = st.session_state[sess_key]

    # Collapsed history — doesn't trigger page scroll on load
    if msgs:
        ctx_label = current_ticker if current_ticker else "Dashboard"
        storage = "☁️" if gh_token else "💾"
        with st.expander(f"💬 Historia {ctx_label} ({len(msgs)} wiad.)", expanded=False):
            for msg in msgs:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            col_clear, col_info = st.columns([1, 3])
            with col_clear:
                if st.button("🗑️ Wyczyść", type="secondary", key=f"clear_{context}"):
                    st.session_state[sess_key] = []
                    save_chat_history([], gh_token, gh_gist, context)
                    st.rerun()
            with col_info:
                st.markdown(f'<span style="font-size:11px;color:#475569">{storage} · {len(msgs)} wiad.</span>', unsafe_allow_html=True)

    # Chat input
    ticker_hint = f"{current_ticker} — " if current_ticker else ""
    prompt = st.chat_input(f"💬 {ticker_hint}zapytaj o wycenę, newsy, strategię...")

    if prompt:
        msgs.append({"role": "user", "content": prompt})
        save_chat_history(msgs, gh_token, gh_gist, context)

        # Render only new exchange inline — no full history re-render, no expander
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            placeholder = st.empty()
            try:
                client   = anthropic.Anthropic(api_key=api_key)
                extra = f"\nUżytkownik aktualnie przegląda: {current_ticker}" if current_ticker else ""
                system   = build_system_prompt(pos, recs, prices, fx, watchlist) + extra
                all_msgs = st.session_state[sess_key]
                ctx_msgs = all_msgs[-CHAT_CONTEXT_LIMIT:] if len(all_msgs) > CHAT_CONTEXT_LIMIT else all_msgs
                messages = [{"role": m["role"], "content": m["content"]} for m in ctx_msgs]

                tools = [SEARCH_TOOL]
                if gh_token:
                    tools += [UPDATE_REC_TOOL, ADD_WATCHLIST_TOOL, REMOVE_WATCHLIST_TOOL]

                import time as _time
                PRICE_IN  = 15.0 / 1_000_000
                PRICE_OUT = 75.0 / 1_000_000
                total_in = total_out = 0

                answered = False
                for _ in range(8):
                    placeholder.markdown("🔍 Analizuję...")
                    response = None
                    for attempt in range(3):
                        try:
                            response = client.messages.create(
                                model="claude-opus-4-7",
                                max_tokens=4096,
                                system=system,
                                tools=tools,
                                messages=messages,
                            )
                            break
                        except Exception as api_err:
                            if attempt < 2 and "overloaded" in str(api_err).lower():
                                placeholder.markdown(f"⏳ Serwer przeciążony, ponawianie za {5*(attempt+1)}s...")
                                _time.sleep(5 * (attempt + 1))
                            else:
                                raise
                    if response is None:
                        placeholder.error("❌ Serwer nie odpowiedział po 3 próbach. Spróbuj ponownie.")
                        break

                    total_in  += getattr(response.usage, "input_tokens",  0)
                    total_out += getattr(response.usage, "output_tokens", 0)

                    if response.stop_reason == "tool_use":
                        tool_results = []
                        for block in response.content:
                            if block.type != "tool_use":
                                continue
                            if block.name == "web_search":
                                query = block.input.get("query", "")
                                placeholder.markdown(f"🔍 Szukam: *{query}*...")
                                result = do_search(query, tavily_key) if tavily_key else "[Web search niedostępny]"
                            elif block.name == "update_recommendation":
                                ticker_u = block.input.get("ticker", "?")
                                rec_u    = block.input.get("recommendation", "?")
                                placeholder.markdown(f"💾 Aktualizuję rekomendację **{ticker_u}** → **{rec_u}**...")
                                result = do_update_recommendation(block.input, gh_token) if gh_token else "Brak tokenu GitHub."
                            elif block.name == "add_to_watchlist":
                                t_w = block.input.get("ticker", "?")
                                s_w = block.input.get("sector", "?")
                                placeholder.markdown(f"👁️ Dodaję **{t_w}** do watchlisty ({s_w})...")
                                result = do_add_to_watchlist(block.input, gh_token) if gh_token else "Brak tokenu GitHub."
                            elif block.name == "remove_from_watchlist":
                                t_w = block.input.get("ticker", "?")
                                placeholder.markdown(f"🗑️ Usuwam **{t_w}** z watchlisty...")
                                result = do_remove_from_watchlist(block.input, gh_token) if gh_token else "Brak tokenu GitHub."
                            else:
                                result = "Nieznane narzędzie."
                            tool_results.append({
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": result,
                            })
                        messages.append({"role": "assistant", "content": response.content})
                        messages.append({"role": "user", "content": tool_results})
                    else:
                        answer = next((b.text for b in response.content if hasattr(b, "text")), "")
                        if not answer:
                            answer = "✅ Gotowe."
                        cost = total_in * PRICE_IN + total_out * PRICE_OUT
                        usage_line = (
                            f'\n\n<div style="margin-top:10px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.05);'
                            f'font-size:10px;color:#334155;display:flex;gap:12px">'
                            f'<span>⬆️ {total_in:,} in</span>'
                            f'<span>⬇️ {total_out:,} out</span>'
                            f'<span style="color:#475569">~${cost:.3f}</span>'
                            f'</div>'
                        )
                        placeholder.markdown(answer + usage_line, unsafe_allow_html=True)
                        msgs.append({"role": "assistant", "content": answer})
                        save_chat_history(msgs, gh_token, gh_gist, context)
                        answered = True
                        break

                if not answered and response is not None:
                    placeholder.error("❌ Asystent nie zwrócił odpowiedzi tekstowej. Spróbuj inaczej sformułować pytanie.")

            except Exception as e:
                placeholder.error(f"❌ Błąd: {e}")

# ─── PAGE: WATCHLISTA ────────────────────────────────────────────────────────
def page_watchlist(watchlist, prices, recs, pos, labels, keys, mkt_cap=None):
    total = sum(len(v) for v in watchlist.values())
    active_sectors = len([s for s in watchlist if watchlist[s]])

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid rgba(255,255,255,0.06)">
        <div>
            <div style="font-size:28px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px">👁️ Lista Obserwowanych</div>
            <div style="font-size:13px;color:#475569;margin-top:3px">{total} spółek · {active_sectors} aktywnych sektorów</div>
        </div>
        <div style="margin-left:auto;font-size:12px;color:#334155;line-height:1.8">
            Dodaj przez chat: <span style="color:#00d9a3">"Dodaj RKLB Rocket Lab do watchlisty, sektor Space"</span><br>
            Usuń przez chat: <span style="color:#ef4444">"Usuń RKLB z watchlisty"</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # Sector overview chips
    chips_html = '<div style="display:flex;flex-wrap:wrap;gap:10px;margin-bottom:28px">'
    for s in WATCHLIST_SECTORS:
        count = len(watchlist.get(s, []))
        alpha = "1" if count else "0.35"
        chips_html += f'<div style="opacity:{alpha};background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.08);border-radius:20px;padding:6px 14px;font-size:12px;font-weight:600;color:#94a3b8">{SECTOR_EMOJI[s]} {s} <span style="color:#f8fafc;margin-left:4px">{count}</span></div>'
    chips_html += '</div>'
    st.markdown(chips_html, unsafe_allow_html=True)

    for sector in WATCHLIST_SECTORS:
        stocks = watchlist.get(sector, [])
        st.markdown(f'<div class="sh">{SECTOR_EMOJI[sector]} {sector}</div>', unsafe_allow_html=True)

        if not stocks:
            st.markdown(f'<div style="color:#334155;font-size:13px;padding:10px 0 18px">Brak spółek. Dodaj przez chat np. "Dodaj IONQ do watchlisty, sektor {sector}"</div>', unsafe_allow_html=True)
            continue

        rows_html = ""
        for stock in stocks:
            t    = stock["ticker"]
            name = stock.get("name", t)
            note = stock.get("note", "")
            added = stock.get("added", "")

            pd_  = prices.get(t, {})
            price = pd_.get("price")
            chg   = pd_.get("change_pct")
            rec_d = recs.get(t, {})
            fv    = rec_d.get("fair_value")
            fv_c  = rec_d.get("fair_value_currency", "")
            ep    = rec_d.get("entry_point")
            recommendation = rec_d.get("recommendation", "")
            upside = (fv - price) / price * 100 if fv and price else rec_d.get("upside_pct")
            in_port = not pos[pos["Ticker"] == t].empty

            mc_val  = (mkt_cap or {}).get(t)
            price_s = f'<span class="t-price">{price:.2f}</span> <span class="t-ccy">{fv_c}</span>' if price else '<span class="t-neu">—</span>'
            chg_s   = f'<span class="{pclass(chg)}">{fmt_pct(chg)}</span>' if chg is not None else '<span class="t-neu">—</span>'
            mc_s    = f'<span style="color:#64748b;font-size:10px">{fmt_cap(mc_val)}</span>' if mc_val else '<span class="t-neu">—</span>'
            fv_s    = f'<span class="t-fv">{fv:.0f} <span class="t-ccy">{fv_c}</span></span>' if fv else '<span class="t-neu">—</span>'
            ep_s    = f'<span style="color:#10b981;font-weight:600">{ep:.0f}</span> <span class="t-ccy">{fv_c}</span>' if ep else '<span class="t-neu">—</span>'
            up_s    = f'<span class="{pclass(upside)}">{fmt_pct(upside)}</span>' if upside is not None else '<span class="t-neu">—</span>'
            badge   = f'<span class="badge b-{recommendation}">{recommendation}</span>' if recommendation else '<span style="color:#334155;font-size:11px">brak analizy</span>'
            port_tag = ' <span style="font-size:9px;background:rgba(0,217,163,0.1);color:#00d9a3;border:1px solid rgba(0,217,163,0.2);border-radius:4px;padding:1px 5px">portfel</span>' if in_port else ""
            rows_html += f"""<tr>
                <td><span class="t-ticker">{_e(t)}</span>{port_tag}</td>
                <td><span class="t-name" style="max-width:130px">{_e(name)}</span></td>
                <td>{price_s}</td><td>{chg_s}</td><td>{mc_s}</td><td>{fv_s}</td>
                <td>{ep_s}</td><td>{up_s}</td><td>{badge}</td>
                <td style="max-width:180px;white-space:normal;font-size:11px;color:#64748b">{_e(note)}</td>
                <td style="color:#475569;font-size:10px">{_e(added)}</td>
            </tr>"""

        st.markdown(f"""
        <div class="pos-table-wrap">
        <table class="pos-table">
            <thead><tr>
                <th>Ticker</th><th>Nazwa</th><th>Cena</th><th>Dzień%</th><th>Mkt Cap</th>
                <th>FV</th><th>Entry</th><th>Upside</th><th>Rec</th>
                <th>Notatka</th><th>Dodano</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
        </table>
        </div>""", unsafe_allow_html=True)

        # Navigation buttons to detail pages
        n = len(stocks)
        ncols = min(n, 5)
        btn_cols = st.columns(ncols)
        for i, stock in enumerate(stocks):
            t = stock["ticker"]
            rec_d = recs.get(t, {})
            emoji_r = REC_EMOJI.get(rec_d.get("recommendation", ""), "⚪") if rec_d else "👁"
            with btn_cols[i % ncols]:
                if st.button(f"{emoji_r} {t} →", key=f"wl_goto_{t}", use_container_width=True):
                    st.session_state["_nav_goto"] = t
                    st.rerun()

        st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    # One-time JS on session start: scroll to top + block Streamlit's 'C' cache shortcut
    if "scroll_reset" not in st.session_state:
        st.session_state["scroll_reset"] = True
        components.html("""<script>
var p = window.parent;
setTimeout(function(){ p.scrollTo({top:0,behavior:"instant"}); }, 300);
p.document.addEventListener('keydown', function(e){
    if(e.key.toLowerCase()==='c' && (e.metaKey||e.ctrlKey)){
        e.stopImmediatePropagation();
    }
}, true);
</script>""", height=1)

    df, demo = load_portfolio()
    fx        = get_fx()
    recs      = load_recs(_mtime=_recs_mtime())
    watchlist = load_watchlist()

    # Collect all tickers: portfolio + recs + watchlist
    wl_tickers = {s["ticker"] for stocks in watchlist.values() for s in stocks}
    all_tickers = list(set(df["Ticker"].tolist()) | set(recs.keys()) | wl_tickers)
    prices  = get_live_prices(tuple(all_tickers))
    mkt_cap = get_market_caps(tuple(all_tickers))
    pos     = build_positions(df, prices, fx, recs)

    # ── Top navigation bar
    nav_col, fx_col = st.columns([3, 1])

    with nav_col:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 16px">
            <span style="font-size:20px;font-weight:800;color:#f1f5f9;letter-spacing:-0.3px">📈 Invest Dashboard</span>
        </div>""", unsafe_allow_html=True)

        labels = ["📊 Overview", "👁️ Watchlista"]
        keys   = ["__overview__", "__watchlist__"]
        # Tabs: portfolio positions first, then watchlist-only tickers
        port_tickers = list(pos["Ticker"]) if not pos.empty else []
        seen = set()
        for t in port_tickers:
            if t in seen: continue
            seen.add(t)
            r = recs.get(t, {})
            emoji = REC_EMOJI.get(r.get("recommendation"), "⚪")
            labels.append(f"{emoji} {t}")
            keys.append(t)
        for t in sorted(wl_tickers):
            if t in seen: continue
            seen.add(t)
            r = recs.get(t, {})
            emoji = REC_EMOJI.get(r.get("recommendation"), "👁")
            labels.append(f"{emoji} {t}")
            keys.append(t)

        # Apply programmatic navigation BEFORE rendering the selectbox
        if "_nav_goto" in st.session_state:
            goto = st.session_state.pop("_nav_goto")
            if goto in keys:
                st.session_state["nav_sel"] = labels[keys.index(goto)]

        sel = st.selectbox("Wybierz widok", labels, label_visibility="collapsed", key="nav_sel")
        page_key = keys[labels.index(sel)]

    with fx_col:
        st.markdown(f"""
        <div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);
             border-radius:12px;padding:12px 16px;margin-top:4px;font-size:11px;line-height:2;color:#64748b">
            <span style="color:#475569;font-weight:600">FX</span><br>
            USD/PLN <span style="color:#94a3b8;float:right">{fx.get('USD',0):.3f}</span><br>
            EUR/PLN <span style="color:#94a3b8;float:right">{fx.get('EUR',0):.3f}</span><br>
            GBP/PLN <span style="color:#94a3b8;float:right">{fx.get('GBP',0):.3f}</span><br>
            HKD/PLN <span style="color:#94a3b8;float:right">{fx.get('HKD',0):.3f}</span>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔄 Odśwież dane", use_container_width=True, key="btn_refresh"):
            load_portfolio.clear()
            get_live_prices.clear()
            get_fx.clear()
            get_market_caps.clear()
            load_recs.clear()
            load_watchlist.clear()
            st.rerun()

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:0 0 20px'>",
                unsafe_allow_html=True)

    # ── Price alerts: BUY zone (price <= entry) and BUY above entry but below FV
    alerts      = []   # price <= entry_point  → urgent
    buy_above   = []   # price > entry but < FV → informational
    for t, rec in recs.items():
        ep   = rec.get("entry_point")
        p    = prices.get(t, {}).get("price")
        r    = rec.get("recommendation", "")
        fv   = rec.get("fair_value")
        fv_c = rec.get("fair_value_currency", "USD")
        if r != "BUY" or not p:
            continue
        upside = (fv - p) / p * 100 if fv and p else None
        if ep and p <= ep:
            alerts.append((t, rec.get("name", t), p, ep, upside, fv, fv_c))
        elif fv and p < fv:
            buy_above.append((t, rec.get("name", t), p, ep, upside, fv, fv_c))

    # ── DCF stale (>90 days) and upcoming earnings alerts
    today = datetime.now().date()
    dcf_stale, earnings_due = [], []
    for t, rec in recs.items():
        lu = rec.get("last_updated")
        ne = rec.get("next_earnings")
        if lu:
            try:
                days_old = (today - datetime.strptime(lu, "%Y-%m-%d").date()).days
                if days_old > 90:
                    dcf_stale.append((t, rec.get("name", t), days_old))
            except Exception:
                pass
        if ne:
            try:
                days_to = (datetime.strptime(ne, "%Y-%m-%d").date() - today).days
                if 0 <= days_to <= 14:
                    earnings_due.append((t, rec.get("name", t), ne, days_to))
            except Exception:
                pass

    reminders_html = ""
    for t, name, days in dcf_stale:
        reminders_html += f"""<div style="background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.25);
            border-radius:10px;padding:10px 16px;font-size:12px;color:#94a3b8;display:flex;gap:10px;align-items:center">
            <span style="font-size:16px">📅</span>
            <span>DCF <b style="color:#fbbf24">{t}</b> — analiza sprzed <b>{days} dni</b>. Rozważ rewizję.</span>
        </div>"""
    for t, name, ne, days in earnings_due:
        label = "DZIŚ" if days == 0 else f"za {days} dni"
        reminders_html += f"""<div style="background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.25);
            border-radius:10px;padding:10px 16px;font-size:12px;color:#94a3b8;display:flex;gap:10px;align-items:center">
            <span style="font-size:16px">📢</span>
            <span>Earnings <b style="color:#818cf8">{t}</b> — {ne} ({label}). Sprawdź czy teza aktualna.</span>
        </div>"""
    # Alerty i banery BUY tylko na Overview — strony spółek zaczynają się od własnych danych
    if reminders_html and page_key == "__overview__":
        st.markdown(f'<div style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px">{reminders_html}</div>',
                    unsafe_allow_html=True)

    all_buys = sorted(alerts, key=lambda x: -(x[4] or 0)) + sorted(buy_above, key=lambda x: -(x[4] or 0))
    if all_buys and page_key == "__overview__":
        html = '<div style="display:flex;flex-direction:column;gap:10px;margin-bottom:24px">'
        for t, name, p, ep, upside, fv, fv_c in all_buys:
            up_s     = f"+{upside:.0f}%" if upside else ""
            in_zone  = ep and p <= ep
            bg       = "rgba(16,185,129,0.08)" if in_zone else "rgba(16,185,129,0.03)"
            border   = "1.5px solid rgba(16,185,129,0.5)" if in_zone else "1px solid rgba(16,185,129,0.2)"
            icon     = "🚨" if in_zone else "🟢"
            zone_lbl = "W strefie zakupu" if in_zone else "Powyżej entry"
            zone_sub = "cena ≤ entry — margin of safety" if in_zone else f"cena powyżej entry {ep:.0f} {fv_c}" if ep else "nadal upside do FV"
            price_detail = f"Cena <b style='color:#f1f5f9'>{p:.2f} {fv_c}</b> · Entry <b style='color:#10b981'>{ep:.0f} {fv_c}</b>" if ep else f"Cena <b style='color:#f1f5f9'>{p:.2f} {fv_c}</b>"
            html += f"""
            <div style="background:{bg};border:{border};border-radius:14px;padding:16px 20px;
                        display:flex;align-items:center;gap:16px;flex-wrap:wrap">
                <div style="font-size:26px">{icon}</div>
                <div style="flex:1;min-width:200px">
                    <div style="font-size:16px;font-weight:800;color:#10b981;letter-spacing:-0.3px">
                        KUPUJ {t} — {name}
                    </div>
                    <div style="font-size:12px;color:#94a3b8;margin-top:3px">
                        {price_detail}
                        {"&nbsp;·&nbsp;FV <b style='color:#00d9a3'>" + str(fv) + " " + fv_c + "</b> <b style='color:#10b981'>" + up_s + "</b>" if fv else ""}
                    </div>
                </div>
                <div style="font-size:11px;color:#475569;text-align:right">
                    {zone_lbl}<br><span style="color:#334155">{zone_sub}</span>
                </div>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    if page_key == "__overview__":
        page_overview(pos, demo, recs, mkt_cap, prices)
        render_chat(pos, recs, prices, fx, watchlist=watchlist)
    elif page_key == "__watchlist__":
        page_watchlist(watchlist, prices, recs, pos, labels, keys, mkt_cap)
        render_chat(pos, recs, prices, fx, current_ticker=None, watchlist=watchlist)
    else:
        page_detail(page_key, pos, prices, recs)
        render_chat(pos, recs, prices, fx, current_ticker=page_key, watchlist=watchlist)

if __name__ == "__main__" or True:
    main()
    if st.session_state.pop("_watchlist_dirty", False):
        st.rerun()
