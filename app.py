import streamlit as st
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
.pos-table {{ width: 100%; border-collapse: collapse; font-size: 13px; font-family: 'Inter', sans-serif; }}
.pos-table thead th {{
    background: rgba(255,255,255,0.02); color: #475569;
    font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;
    padding: 14px 16px; text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.06); white-space: nowrap;
}}
.pos-table tbody tr {{ border-bottom: 1px solid rgba(255,255,255,0.03); transition: background .15s; }}
.pos-table tbody tr:last-child {{ border-bottom: none; }}
.pos-table tbody tr:hover {{ background: rgba(255,255,255,0.025); }}
.pos-table td {{ padding: 14px 16px; color: #cbd5e1; vertical-align: middle; white-space: nowrap; }}
.t-ticker {{ font-weight: 700; font-size: 13px; color: #f1f5f9; letter-spacing: 0.3px; }}
.t-name   {{ color: #94a3b8; font-size: 12px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; }}
.t-price  {{ font-weight: 600; color: #f1f5f9; font-size: 13px; }}
.t-ccy    {{ color: #475569; font-size: 11px; }}
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
}
CCY_MAP = {
    "dolar": "USD", "dollar": "USD", "usd": "USD",
    "euro": "EUR", "eur": "EUR",
    "pln": "PLN", "zł": "PLN", "hkd": "HKD",
    "gbp": "GBP", "funt": "GBP", "pound": "GBP",
}

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
        if cl == "nazwa":    rename[col] = "Nazwa"
        elif cl == "ticker": rename[col] = "Ticker_raw"
        elif cl == "waluta": rename[col] = "Waluta"
        elif cl == "volume": rename[col] = "Ilosc"
        elif cl == "price":  rename[col] = "Srednia_cena"
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
    df = df[df["Ticker"].notna() & (df["Ticker"] != "") & (df["Ilosc"] > 0)].copy()
    rows = []
    for (ticker, ccy), g in df.groupby(["Ticker", "Waluta"]):
        vol  = g["Ilosc"].sum()
        wavg = (g["Ilosc"] * g["Srednia_cena"]).sum() / vol if vol > 0 else 0
        rows.append({"Ticker": ticker, "Nazwa": g["Nazwa"].iloc[0],
                     "Ilosc": vol, "Srednia_cena": wavg, "Waluta": ccy})
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
    result = {}
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period="5d")
            if len(hist) >= 2:
                prev, curr = float(hist["Close"].iloc[-2]), float(hist["Close"].iloc[-1])
                result[ticker] = {"price": curr, "change_pct": (curr - prev) / prev * 100}
            elif len(hist) == 1:
                result[ticker] = {"price": float(hist["Close"].iloc[-1]), "change_pct": 0.0}
            else:
                result[ticker] = {"price": None, "change_pct": None}
        except Exception:
            result[ticker] = {"price": None, "change_pct": None}
    return result

@st.cache_data(ttl=1800)
def get_fx() -> dict:
    rates = {"PLN": 1.0}
    for ccy, sym in {"USD": "USDPLN=X", "EUR": "EURPLN=X", "HKD": "HKDPLN=X", "GBP": "GBPPLN=X"}.items():
        try:
            rates[ccy] = float(yf.Ticker(sym).history(period="5d")["Close"].iloc[-1])
        except Exception:
            rates[ccy] = {"USD": 3.98, "EUR": 4.30, "HKD": 0.51, "GBP": 5.05}[ccy]
    return rates

@st.cache_data(ttl=3600)
def load_recs() -> dict:
    try:
        with open("data/recommendations.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

@st.cache_data(ttl=300)
def get_history(ticker: str, period: str) -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).history(period=period)
    except Exception:
        return pd.DataFrame()

# ─── HELPERS ──────────────────────────────────────────────────────────────────
def fmt_pln(v):
    if v is None: return "—"
    s = "+" if v >= 0 else ""
    if abs(v) >= 1_000_000: return f"{s}{v/1_000_000:.2f}M PLN"
    if abs(v) >= 1_000:     return f"{s}{v/1_000:.1f}k PLN"
    return f"{s}{v:.0f} PLN"

def fmt_m(v):
    if v is None: return "—"
    if abs(v) >= 1_000_000: return f"${v/1_000_000:.1f}T"
    if abs(v) >= 1_000:     return f"${v/1_000:.1f}B"
    return f"${v:.0f}M"

def fmt_pct(v):
    if v is None: return "—"
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
        rate = fx.get(ccy, 1.0); rec = recs.get(t, {}); fv = rec.get("fair_value")
        cur_val = price * qty * rate if price and qty else None
        cost    = avg * qty * rate   if avg and qty else None
        pnl     = (cur_val - cost)   if cur_val is not None and cost is not None else None
        pnl_pct = pnl / cost * 100   if pnl is not None and cost and cost != 0 else None
        upside  = (fv - price) / price * 100 if fv and price else rec.get("upside_pct")
        rows.append({
            "Ticker": t, "Nazwa": r["Nazwa"], "Cena": price, "Waluta": ccy,
            "Dzień%": chg, "Ilość": qty, "Avg": avg,
            "Val_PLN": cur_val, "PnL_PLN": pnl, "PnL%": pnl_pct,
            "FV": fv, "FV_ccy": rec.get("fair_value_currency", ccy),
            "Upside": upside, "Rec": rec.get("recommendation", "—"),
            "Rec_sort": REC_ORDER.get(rec.get("recommendation", "HOLD"), 3),
        })
    return pd.DataFrame(rows)

# ─── CHART ────────────────────────────────────────────────────────────────────
def price_chart(ticker, period, entry, fv):
    hist = get_history(ticker, period)
    if hist.empty: return None
    closes = hist["Close"].astype(float)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=hist.index, y=closes, mode="lines", name="Cena",
        line=dict(color=ACCENT, width=2.5),
        fill="tozeroy", fillcolor="rgba(0,217,163,0.05)",
        hovertemplate="%{x|%d %b %Y}  <b>%{y:.2f}</b><extra></extra>"
    ))
    if fv:
        fig.add_hline(y=fv, line_dash="dash", line_color="rgba(245,158,11,0.7)", line_width=1.5,
                      annotation_text=f"Fair Value  {fv:.0f}",
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
                   color="#334155", tickfont=dict(size=11)),
        hovermode="x unified"
    )
    return fig

# ─── DCF CALCULATOR ───────────────────────────────────────────────────────────
def compute_dcf_stages(dcf: dict):
    """Returns list of dicts with computed yearly FCF per stage."""
    wacc   = dcf["wacc_pct"] / 100
    rev    = dcf["revenue_ttm_m"]
    stages = dcf["stages"]
    rows   = []
    year   = 0
    for stage in stages:
        years_range = stage["period"]
        n_years     = 5
        cagr        = stage["rev_cagr_pct"] / 100
        ebit_m      = stage["ebit_margin_pct"] / 100
        tax         = stage["tax_pct"] / 100
        capex_pct   = stage["capex_pct"] / 100
        da_pct      = stage["da_pct"] / 100
        for i in range(1, n_years + 1):
            year += 1
            rev = rev * (1 + cagr)
            ebit = rev * ebit_m
            nopat = ebit * (1 - tax)
            da = rev * da_pct
            capex = rev * capex_pct
            fcf = nopat + da - capex
            pv = fcf / ((1 + wacc) ** year)
            rows.append({
                "Rok": year,
                "Okres": years_range,
                "Przychody": rev,
                "EBIT": ebit,
                "NOPAT": nopat,
                "D&A": da,
                "CapEx": capex,
                "FCF": fcf,
                "PV_FCF": pv,
            })
    return rows, rev, year

def tab_dcf(rec: dict):
    dcf = rec.get("dcf")
    if not dcf:
        st.markdown("""
        <div style="padding:40px;text-align:center;color:#475569">
            <div style="font-size:32px;margin-bottom:12px">📐</div>
            <div style="font-size:15px">Brak modelu DCF dla tego aktywa.</div>
            <div style="font-size:13px;margin-top:6px;color:#334155">Krypto i ETF-y nie mają przepływów gotówkowych do dyskontowania.</div>
        </div>""", unsafe_allow_html=True)
        return

    wacc = dcf["wacc_pct"] / 100
    tg   = dcf["terminal_growth_pct"] / 100

    # ── Key Assumptions
    st.markdown('<div class="sh">⚙️ Założenia modelu</div>', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    assumptions = [
        (col1, "WACC", f"{dcf['wacc_pct']}%", "Stopa dyskontowa"),
        (col2, "Terminal Growth", f"{dcf['terminal_growth_pct']}%", "Wzrost w nieskończoność"),
        (col3, "Revenue TTM", fmt_m(dcf['revenue_ttm_m']), "Bazowe przychody"),
        (col4, "Liczba akcji", f"{dcf['shares_m']/1000:.1f}B" if dcf['shares_m'] >= 1000 else f"{dcf['shares_m']}M", "Akcji w obrocie"),
    ]
    for col, label, val, sub in assumptions:
        with col:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{val}</div>
                <div class="metric-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    # ── Stage breakdown table
    st.markdown('<div class="sh">📊 Projekcja przepływów gotówkowych</div>', unsafe_allow_html=True)
    rows, final_rev, total_years = compute_dcf_stages(dcf)

    header = "<tr><th>Rok</th><th>Okres</th><th>Przychody</th><th>EBIT</th><th>NOPAT</th><th>+D&A</th><th>–CapEx</th><th>FCF</th><th>PV(FCF)</th></tr>"
    body = ""
    pv_sum = 0
    for r in rows:
        pv_sum += r["PV_FCF"]
        body += f"""<tr>
            <td>{r['Rok']}</td><td>{r['Okres']}</td>
            <td>{fmt_m(r['Przychody'])}</td><td>{fmt_m(r['EBIT'])}</td>
            <td>{fmt_m(r['NOPAT'])}</td><td>{fmt_m(r['D&A'])}</td>
            <td>{fmt_m(r['CapEx'])}</td><td>{fmt_m(r['FCF'])}</td>
            <td style="color:#00d9a3">{fmt_m(r['PV_FCF'])}</td>
        </tr>"""

    last_fcf = rows[-1]["FCF"]
    tv  = last_fcf * (1 + tg) / (wacc - tg)
    pv_tv = tv / ((1 + wacc) ** total_years)

    body += f"""<tr class="total">
        <td colspan="8" style="color:#64748b;font-size:11px">Suma PV przepływów (rok 1–{total_years})</td>
        <td>{fmt_m(pv_sum)}</td>
    </tr>"""

    st.markdown(f"""
    <div style="overflow-x:auto;border-radius:14px;border:1px solid {BORDER}">
    <table class="dcf-table"><thead>{header}</thead><tbody>{body}</tbody></table>
    </div>""", unsafe_allow_html=True)

    # ── Bridge to fair value — all values from stored JSON for consistency
    st.markdown('<div class="sh">🌉 Od wartości przedsiębiorstwa do ceny akcji</div>', unsafe_allow_html=True)
    pv_fcf_display     = dcf.get("pv_fcf_m", pv_sum)
    pv_terminal_display = dcf.get("pv_terminal_m", round(pv_tv))
    ev     = dcf.get("enterprise_value_m", pv_fcf_display + pv_terminal_display)
    eq_val = ev - dcf.get("net_debt_m", 0)

    net_debt = dcf.get("net_debt_m", 0)
    nd_label = "– Dług netto" if net_debt > 0 else "+ Gotówka netto"
    nd_val   = -net_debt if net_debt > 0 else abs(net_debt)

    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown(f"""
        <div class="dcf-bridge">
            <div class="dcf-row">
                <span class="dcf-row-label">PV wolnych przepływów gotówkowych (10 lat)</span>
                <span class="dcf-row-value">{fmt_m(pv_fcf_display)}</span>
            </div>
            <div class="dcf-row">
                <span class="dcf-row-label">+ PV wartości terminalnej (wzrost {dcf['terminal_growth_pct']}% ∞)</span>
                <span class="dcf-row-value">{fmt_m(pv_terminal_display)}</span>
            </div>
            <div class="dcf-row" style="border-top:1px solid rgba(255,255,255,0.08);padding-top:12px;margin-top:4px">
                <span class="dcf-row-label" style="font-weight:600;color:#e2e8f0">= Wartość przedsiębiorstwa (EV)</span>
                <span class="dcf-row-value" style="font-size:15px">{fmt_m(ev)}</span>
            </div>
            <div class="dcf-row">
                <span class="dcf-row-label">{nd_label}</span>
                <span class="dcf-row-value" style="color:#10b981">{fmt_m(nd_val)}</span>
            </div>
            <div class="dcf-row" style="border-top:1px solid rgba(255,255,255,0.08);padding-top:12px;margin-top:4px">
                <span class="dcf-row-label" style="font-weight:600;color:#e2e8f0">= Wartość kapitału własnego</span>
                <span class="dcf-row-value" style="font-size:15px">{fmt_m(eq_val)}</span>
            </div>
            <div class="dcf-row">
                <span class="dcf-row-label">÷ Liczba akcji</span>
                <span class="dcf-row-value">{dcf['shares_m']}M</span>
            </div>
            <div class="dcf-row" style="border-top:1px solid rgba(0,217,163,0.25);padding-top:14px;margin-top:4px">
                <span class="dcf-row-label" style="font-weight:700;color:#00d9a3;font-size:14px">= Fair Value na akcję</span>
                <span class="dcf-row-total">{dcf.get('fair_value','—')} {rec.get('fair_value_currency','')}</span>
            </div>
        </div>""", unsafe_allow_html=True)

    with col_b:
        tv_share = pv_terminal_display / (pv_fcf_display + pv_terminal_display) * 100 if (pv_fcf_display + pv_terminal_display) > 0 else 0
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
    prio_html = f'<div style="margin-top:10px;font-size:14px;color:{c};line-height:1.6">{prio}</div>' if prio else ""

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
                <span>{tb}</span>
            </div>
            {"<div class='trigger-item ti-sell'><span class='ti-icon'>📊</span><span>Fair Value rewizja w dół powyżej -20% — czas na wyjście</span></div>" if fv else ""}
            {"<div class='trigger-item ti-sell'><span class='ti-icon'>🎯</span><span>Cena osiąga Fair Value " + str(fv) + " " + rec.get('fair_value_currency','') + " — realizuj zysk lub redukuj pozycję</span></div>" if fv else ""}
        </div>""", unsafe_allow_html=True)

    with col_r:
        # ── Events timeline
        events = rec.get("events", [])
        st.markdown('<div class="sh">📅 Ostatnie wydarzenia</div>', unsafe_allow_html=True)
        if events:
            html = ""
            for i, ev in enumerate(events):
                impact = ev.get("impact", "neutral")
                dot_cls = "ev-pos" if impact == "positive" else "ev-neg" if impact == "negative" else "ev-neu"
                line = '<div class="event-line"></div>' if i < len(events) - 1 else ""
                html += f"""
                <div class="event-item">
                    <div class="event-dot-wrap">
                        <div class="event-dot {dot_cls}"></div>
                        {line}
                    </div>
                    <div class="event-body">
                        <div class="event-date">{ev.get('date','—')}</div>
                        <div class="event-text">{ev.get('event','')}</div>
                        <div class="event-fv">→ FV: {ev.get('fv_note','')}</div>
                    </div>
                </div>"""
            st.markdown(f'<div style="padding:4px 0">{html}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#475569;font-size:13px;padding:20px 0">Brak wydarzeń do wyświetlenia.</div>', unsafe_allow_html=True)

# ─── PAGE: OVERVIEW ───────────────────────────────────────────────────────────
def page_overview(pos, demo):
    if demo:
        st.markdown("""<div class="demo-banner">
        ⚙️ <b>Tryb demo</b> — live ceny i rekomendacje są aktywne.
        Skonfiguruj Google Sheets ze swoimi pozycjami żeby zobaczyć P&L.
        </div>""", unsafe_allow_html=True)

    total_val  = pos["Val_PLN"].sum() if pos["Val_PLN"].notna().any() else None
    total_cost = pos.apply(lambda r: r["Ilość"] * r["Avg"] if r["Ilość"] and r["Avg"] else 0, axis=1).sum()
    total_pnl  = pos["PnL_PLN"].sum() if pos["PnL_PLN"].notna().any() else None
    pnl_pct    = (total_pnl / total_cost * 100) if total_pnl and total_cost else None
    n_pos      = len(pos)

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

    recs = load_recs()
    prio = [(t, r) for t, r in recs.items() if r.get("priority_action")]
    if prio:
        st.markdown('<div class="sh">⚡ Priorytetowe działania</div>', unsafe_allow_html=True)
        html = '<div class="actions">'
        for t, r in sorted(prio, key=lambda x: REC_ORDER.get(x[1].get("recommendation","HOLD"), 3)):
            rec = r.get("recommendation", "HOLD")
            ac  = REC_ACTION.get(rec, "a-neu")
            dot = REC_DOT.get(rec, "dot-neu")
            html += f"""<div class="action {ac}">
                <div class="action-dot {dot}"></div>
                <span class="action-ticker">{t}</span>
                <span style="color:#475569;font-size:12px">·</span>
                <span>{r['priority_action']}</span>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    st.markdown('<div class="sh">📊 Pozycje</div>', unsafe_allow_html=True)
    df = pos.sort_values("Rec_sort")
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
        pnlp_s  = f'<span class="{pclass(r["PnL%"])}">{fmt_pct(r["PnL%"])}</span>' if r["PnL%"] is not None else '<span class="t-neu">—</span>'
        fv_s    = f'<span class="t-fv">{r["FV"]:.0f} <span class="t-ccy">{r["FV_ccy"]}</span></span>' if r["FV"] else '<span class="t-neu">—</span>'
        up_s    = f'<span class="{pclass(r["Upside"])}">{fmt_pct(r["Upside"])}</span>' if r["Upside"] is not None else '<span class="t-neu">—</span>'
        badge   = f'<span class="badge b-{rec}">{rec}</span>' if rec != "—" else "—"
        rows_html += f"""<tr class="{row_cls}">
            <td><span class="t-ticker">{r['Ticker']}</span></td>
            <td><span class="t-name">{r['Nazwa']}</span></td>
            <td>{qty_s}</td><td>{avg_s}</td>
            <td>{price_s}</td><td>{chg_s}</td>
            <td>{val_s}</td><td>{pnl_s}</td><td>{pnlp_s}</td>
            <td>{fv_s}</td><td>{up_s}</td><td>{badge}</td>
        </tr>"""

    st.markdown(f"""
    <div class="pos-table-wrap">
    <table class="pos-table">
        <thead><tr>
            <th>Ticker</th><th>Nazwa</th><th>Ilość</th><th>Śr. cena</th>
            <th>Cena</th><th>Dzień</th>
            <th>Wartość PLN</th><th>P&L</th><th>P&L%</th>
            <th>Fair Value</th><th>Upside</th><th>Rec</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>""", unsafe_allow_html=True)

# ─── PAGE: DETAIL ─────────────────────────────────────────────────────────────
def page_detail(ticker, pos, prices):
    recs = load_recs()
    rec  = recs.get(ticker, {})
    rec["_ticker"] = ticker
    row  = pos[pos["Ticker"] == ticker]
    row  = row.iloc[0] if not row.empty else None

    recommendation = rec.get("recommendation", "—")
    fv   = rec.get("fair_value")
    fv_c = rec.get("fair_value_currency", "")
    ep   = rec.get("entry_point")

    price  = row["Cena"]   if row is not None else prices.get(ticker, {}).get("price")
    ccy    = row["Waluta"] if row is not None else fv_c
    chg    = row["Dzień%"] if row is not None else None
    pnl    = row["PnL_PLN"] if row is not None else None
    pnl_p  = row["PnL%"]  if row is not None else None
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
            <div class="dcard-label">Twój P&L</div>
            <div class="dcard-value {kpiclass(pnl)}">{fmt_pln(pnl)}</div>
            <div class="dcard-sub {kpiclass(pnl_p)}">{fmt_pct(pnl_p)}</div>
        </div>
        <div class="dcard">
            <div class="dcard-label">Punkt wejścia</div>
            <div class="dcard-value" style="font-size:20px">{ep_txt}</div>
            <div class="dcard-sub neu">Margin of safety 20–30%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Tabs
    t_wykres, t_dcf, t_actions, t_teza = st.tabs(["📈 Wykres", "📐 DCF", "⚡ Działania", "💡 Teza"])

    with t_wykres:
        periods = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y", "3Y": "3y"}
        sel = st.radio("Okres", list(periods.keys()), horizontal=True, index=2,
                       key=f"p_{ticker}", label_visibility="collapsed")
        fig = price_chart(ticker, periods[sel], ep, fv)
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
            st.markdown(f'<div class="thesis-card">{rec.get("thesis_full","Brak danych.")}</div>', unsafe_allow_html=True)
            tb = rec.get("thesis_breaker", "—")
            st.markdown(f"""
            <div class="breaker-card">
                <div style="font-size:10px;font-weight:600;color:#f87171;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px">⛔ Thesis Breaker — kiedy sprzedać</div>
                <div style="color:#fca5a5;font-size:14px;line-height:1.65">{tb}</div>
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

# ─── PAGE: CHAT ───────────────────────────────────────────────────────────────
def build_system_prompt(pos, recs, prices, fx):
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
    return f"""Jesteś profesjonalnym doradcą inwestycyjnym. Analizujesz spółki moonshot (AI, Energy/fusion/SMR, Space).
Masz dostęp do narzędzia web_search — używaj go zawsze gdy pytanie dotyczy aktualnych wydarzeń, newsów, wyników finansowych lub cen.

PROFIL INWESTORA:
- Horyzont: 1–3 lata | Kapitał: 50k–250k PLN | Ryzyko: wysoka tolerancja, szuka 10–50x
- Giełdy: globalny mandat (US, EU, PL) | Narzędzia: Morningstar, DCF

AKTUALNY PORTFEL (live ceny z yfinance):
{chr(10).join(portfolio_lines) if portfolio_lines else 'Brak danych'}

REKOMENDACJE I FAIR VALUES:
{chr(10).join(rec_lines)}

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
- Dzisiejsza data: {datetime.now().strftime('%Y-%m-%d')}"""

SEARCH_TOOL = {
    "name": "web_search",
    "description": "Wyszukuje aktualne informacje w internecie. Używaj dla newsów, wyników finansowych, aktualnych cen, wydarzeń rynkowych.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Zapytanie wyszukiwania po angielsku dla lepszych wyników finansowych"
            }
        },
        "required": ["query"]
    }
}

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

def render_chat(pos, recs, prices, fx, current_ticker=None):
    try:
        api_key = st.secrets["anthropic"]["api_key"]
    except Exception:
        return
    try:
        tavily_key = st.secrets["tavily"]["api_key"]
    except Exception:
        tavily_key = None

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # Show history in expander
    if st.session_state.chat_messages:
        label = f"💬 Rozmowa ({len(st.session_state.chat_messages)} wiad.)"
        with st.expander(label, expanded=True):
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])
            if st.button("🗑️ Wyczyść", type="secondary", key="clear_chat"):
                st.session_state.chat_messages = []
                st.rerun()

    # Always-visible input at bottom
    ticker_hint = f"{current_ticker} — " if current_ticker else ""
    prompt = st.chat_input(f"💬 {ticker_hint}zapytaj o wycenę, newsy, strategię...")

    if prompt:
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.expander("💬 Rozmowa", expanded=True):
            for msg in st.session_state.chat_messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

            with st.chat_message("assistant"):
                placeholder = st.empty()
                try:
                    client   = anthropic.Anthropic(api_key=api_key)
                    # Inject current ticker context
                    extra = f"\nUżytkownik aktualnie przegląda: {current_ticker}" if current_ticker else ""
                    system   = build_system_prompt(pos, recs, prices, fx) + extra
                    messages = [{"role": m["role"], "content": m["content"]}
                                for m in st.session_state.chat_messages]

                    for _ in range(5):
                        placeholder.markdown("🔍 Analizuję...")
                        response = client.messages.create(
                            model="claude-opus-4-7",
                            max_tokens=4096,
                            system=system,
                            tools=[SEARCH_TOOL],
                            messages=messages,
                        )

                        if response.stop_reason == "tool_use":
                            tool_results = []
                            for block in response.content:
                                if block.type == "tool_use" and block.name == "web_search":
                                    query = block.input.get("query", "")
                                    placeholder.markdown(f"🔍 Szukam: *{query}*...")
                                    result = do_search(query, tavily_key) if tavily_key else "[Web search niedostępny]"
                                    tool_results.append({
                                        "type": "tool_result",
                                        "tool_use_id": block.id,
                                        "content": result,
                                    })
                            messages.append({"role": "assistant", "content": response.content})
                            messages.append({"role": "user", "content": tool_results})
                        else:
                            answer = next((b.text for b in response.content if hasattr(b, "text")), "")
                            placeholder.markdown(answer)
                            st.session_state.chat_messages.append({"role": "assistant", "content": answer})
                            break

                except Exception as e:
                    placeholder.error(f"Błąd: {e}")

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    df, demo = load_portfolio()
    fx       = get_fx()
    recs     = load_recs()
    all_tickers = list(set(df["Ticker"].tolist()) | set(recs.keys()))
    prices   = get_live_prices(tuple(all_tickers))
    pos      = build_positions(df, prices, fx, recs)

    # ── Top navigation bar
    nav_col, fx_col = st.columns([3, 1])

    with nav_col:
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;padding:4px 0 16px">
            <span style="font-size:20px;font-weight:800;color:#f1f5f9;letter-spacing:-0.3px">📈 Invest Dashboard</span>
        </div>""", unsafe_allow_html=True)

        labels = ["📊 Overview"]
        keys   = ["__overview__"]
        for t, r in recs.items():
            emoji = REC_EMOJI.get(r.get("recommendation"), "⚪")
            labels.append(f"{emoji} {t}")
            keys.append(t)

        sel = st.selectbox("Wybierz widok", labels, label_visibility="collapsed")
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

    st.markdown("<hr style='border:none;border-top:1px solid rgba(255,255,255,0.06);margin:0 0 20px'>",
                unsafe_allow_html=True)

    if page_key == "__overview__":
        page_overview(pos, demo)
        render_chat(pos, recs, prices, fx)
    else:
        page_detail(page_key, pos, prices)
        render_chat(pos, recs, prices, fx, current_ticker=page_key)

if __name__ == "__main__" or True:
    main()
