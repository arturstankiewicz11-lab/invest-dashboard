import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import io
from datetime import datetime

st.set_page_config(
    page_title="Invest Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── DESIGN SYSTEM ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
    font-family: 'Inter', sans-serif !important;
    background-color: #07071a !important;
    color: #e2e8f0 !important;
}

[data-testid="stAppViewContainer"]::before {
    content: '';
    position: fixed;
    inset: 0;
    background-image: radial-gradient(rgba(99,102,241,0.07) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
    z-index: 0;
}

[data-testid="stMainBlockContainer"] { position: relative; z-index: 1; }

[data-testid="stSidebar"] {
    background: rgba(15,15,35,0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.06) !important;
    backdrop-filter: blur(20px);
}

/* Hide default streamlit elements */
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stDecoration"] { display: none; }

/* ── KPI CARDS ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 32px; }
.kpi {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px;
    padding: 24px;
    position: relative;
    overflow: hidden;
    transition: border-color .2s;
}
.kpi::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(99,102,241,0.5), transparent);
}
.kpi:hover { border-color: rgba(99,102,241,0.3); }
.kpi-icon { font-size: 22px; margin-bottom: 12px; }
.kpi-label { font-size: 11px; font-weight: 500; color: #64748b; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
.kpi-value { font-size: 28px; font-weight: 700; color: #f8fafc; letter-spacing: -0.5px; margin-bottom: 6px; }
.kpi-sub { font-size: 13px; font-weight: 500; }
.pos  { color: #10b981; }
.neg  { color: #ef4444; }
.neu  { color: #64748b; }

/* ── SECTION HEADER ── */
.section-header {
    display: flex; align-items: center; gap: 10px;
    margin: 32px 0 16px;
    font-size: 11px; font-weight: 600; color: #475569;
    text-transform: uppercase; letter-spacing: 2px;
}
.section-header::after {
    content: ''; flex: 1;
    height: 1px;
    background: linear-gradient(90deg, rgba(255,255,255,0.06), transparent);
}

/* ── ACTION CARDS ── */
.actions { display: flex; flex-direction: column; gap: 8px; margin-bottom: 8px; }
.action {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px; border-radius: 12px;
    font-size: 14px; font-weight: 500;
    border: 1px solid transparent;
}
.a-sell { background: rgba(239,68,68,0.08);  border-color: rgba(239,68,68,0.2);  color: #fca5a5; }
.a-buy  { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.2); color: #6ee7b7; }
.a-warn { background: rgba(245,158,11,0.08); border-color: rgba(245,158,11,0.2); color: #fcd34d; }
.action-ticker { font-weight: 700; font-size: 13px; }
.action-dot { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.dot-sell { background: #ef4444; box-shadow: 0 0 8px #ef4444; }
.dot-buy  { background: #10b981; box-shadow: 0 0 8px #10b981; }
.dot-warn { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }

/* ── POSITIONS TABLE ── */
.pos-table-wrap { overflow-x: auto; border-radius: 16px; border: 1px solid rgba(255,255,255,0.06); }
.pos-table {
    width: 100%; border-collapse: collapse;
    font-size: 13px; font-family: 'Inter', sans-serif;
}
.pos-table thead th {
    background: rgba(255,255,255,0.02);
    color: #475569; font-size: 10px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1.5px;
    padding: 14px 16px; text-align: left;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    white-space: nowrap;
}
.pos-table tbody tr {
    border-bottom: 1px solid rgba(255,255,255,0.03);
    transition: background .15s;
}
.pos-table tbody tr:last-child { border-bottom: none; }
.pos-table tbody tr:hover { background: rgba(255,255,255,0.03); }
.pos-table td { padding: 14px 16px; color: #cbd5e1; vertical-align: middle; white-space: nowrap; }
.t-ticker { font-weight: 700; font-size: 13px; color: #f1f5f9; letter-spacing: 0.3px; }
.t-name   { color: #94a3b8; font-size: 12px; max-width: 140px; overflow: hidden; text-overflow: ellipsis; }
.t-price  { font-weight: 600; color: #f1f5f9; font-size: 13px; }
.t-ccy    { color: #475569; font-size: 11px; }
.t-pos    { color: #10b981; font-weight: 600; }
.t-neg    { color: #ef4444; font-weight: 600; }
.t-neu    { color: #64748b; }
.t-fv     { color: #94a3b8; }

/* Row highlight by recommendation */
.row-buy  td:first-child { border-left: 3px solid #10b981; }
.row-sell td:first-child { border-left: 3px solid #ef4444; }
.row-reduce td:first-child { border-left: 3px solid #f59e0b; }
.row-hold td:first-child { border-left: 3px solid #334155; }

/* Badges */
.badge {
    display: inline-block; border-radius: 6px;
    padding: 3px 10px; font-size: 10px; font-weight: 700;
    letter-spacing: 0.8px; text-transform: uppercase;
}
.b-BUY    { background: rgba(16,185,129,0.15); color: #10b981; border: 1px solid rgba(16,185,129,0.3); }
.b-HOLD   { background: rgba(100,116,139,0.15); color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
.b-SELL   { background: rgba(239,68,68,0.15);  color: #ef4444;  border: 1px solid rgba(239,68,68,0.3); }
.b-REDUCE { background: rgba(245,158,11,0.15); color: #f59e0b;  border: 1px solid rgba(245,158,11,0.3); }

/* Demo banner */
.demo-banner {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px; padding: 14px 18px;
    font-size: 13px; color: #a5b4fc; margin-bottom: 24px;
    display: flex; align-items: center; gap: 10px;
}

/* ── DETAIL PAGE ── */
.detail-grid { display: grid; grid-template-columns: repeat(4,1fr); gap: 14px; margin-bottom: 28px; }
.dcard {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px; padding: 20px;
}
.dcard-label { font-size: 10px; font-weight: 600; color: #475569; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 8px; }
.dcard-value { font-size: 22px; font-weight: 700; color: #f8fafc; margin-bottom: 4px; }
.dcard-sub   { font-size: 12px; }

.thesis-card {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px; padding: 20px;
    line-height: 1.7; color: #94a3b8; font-size: 14px;
}
.breaker-card {
    background: rgba(239,68,68,0.05);
    border: 1px solid rgba(239,68,68,0.15);
    border-radius: 14px; padding: 18px; margin-top: 12px;
}
.risk-item {
    background: rgba(255,255,255,0.02);
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px; padding: 10px 14px;
    font-size: 13px; color: #94a3b8; margin-bottom: 8px;
}
.moat-card {
    background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.15);
    border-radius: 14px; padding: 18px; margin-top: 12px;
}

/* Sidebar nav */
.nav-item {
    display: flex; align-items: center; gap: 10px;
    padding: 10px 14px; border-radius: 10px;
    font-size: 13px; font-weight: 500; color: #64748b;
    cursor: pointer; margin-bottom: 4px;
    transition: all .15s;
}
</style>
""", unsafe_allow_html=True)

# ─── CONSTANTS ────────────────────────────────────────────────────────────────
SAMPLE_CSV = """Ticker,Nazwa,Ilosc,Srednia_cena,Waluta
MSFT,Microsoft,0,0,USD
ETL.PA,Eutelsat,0,0,EUR
RHM.DE,Rheinmetall,0,0,EUR
BTC-USD,Bitcoin,0,0,USD
PZU.WA,PZU,0,0,PLN
0700.HK,Tencent,0,0,HKD
CNDX.L,iShares Nasdaq 100,0,0,USD
SEMI.L,iShares Semiconductors,0,0,USD
RBOT.L,iShares Robotics,0,0,USD
HEAL.L,iShares Healthcare,0,0,USD
CSPX.L,iShares S&P 500,0,0,USD
EIMI.L,iShares Emerging Markets,0,0,USD
AGGG.L,iShares Bonds,0,0,USD"""

REC_ORDER  = {"SELL": 0, "REDUCE": 1, "BUY": 2, "HOLD": 3}
REC_DOT    = {"BUY": "dot-buy", "SELL": "dot-sell", "REDUCE": "dot-warn", "HOLD": "dot-warn"}
REC_ACTION = {"BUY": "a-buy", "SELL": "a-sell", "REDUCE": "a-warn", "HOLD": "a-warn"}
REC_ROW    = {"BUY": "row-buy", "SELL": "row-sell", "REDUCE": "row-reduce", "HOLD": "row-hold"}

# ─── DATA ─────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_portfolio():
    try:
        url = st.secrets["gsheets"]["portfolio_url"]
        return pd.read_csv(url), False
    except Exception:
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
    for ccy, sym in {"USD": "USDPLN=X", "EUR": "EURPLN=X", "HKD": "HKDPLN=X"}.items():
        try:
            rates[ccy] = float(yf.Ticker(sym).history(period="5d")["Close"].iloc[-1])
        except Exception:
            rates[ccy] = {"USD": 3.98, "EUR": 4.30, "HKD": 0.51}[ccy]
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
        t   = r["Ticker"]
        ccy = r["Waluta"]
        qty = float(r["Ilosc"])
        avg = float(r["Srednia_cena"])
        p   = prices.get(t, {})
        price = p.get("price")
        chg   = p.get("change_pct")
        rate  = fx.get(ccy, 1.0)
        rec   = recs.get(t, {})
        fv    = rec.get("fair_value")
        cur_val  = price * qty * rate if price and qty else None
        cost     = avg * qty * rate   if avg and qty else None
        pnl      = (cur_val - cost)   if cur_val and cost else None
        pnl_pct  = pnl / cost * 100   if pnl and cost and cost != 0 else None
        upside   = (fv - price) / price * 100 if fv and price else rec.get("upside_pct")
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
        line=dict(color="#6366f1", width=2.5),
        fill="tozeroy", fillcolor="rgba(99,102,241,0.06)",
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
        showlegend=False, margin=dict(l=0, r=50, t=8, b=0), height=300,
        xaxis=dict(showgrid=False, color="#334155", tickfont=dict(size=11)),
        yaxis=dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)",
                   color="#334155", tickfont=dict(size=11)),
        hovermode="x unified"
    )
    return fig

# ─── PAGE: OVERVIEW ───────────────────────────────────────────────────────────
def page_overview(pos, demo):
    if demo:
        st.markdown("""<div class="demo-banner">
        ⚙️ <b>Tryb demo</b> — live ceny i rekomendacje są aktywne.
        Skonfiguruj Google Sheets ze swoimi pozycjami żeby zobaczyć P&L.
        </div>""", unsafe_allow_html=True)

    total_val  = pos["Val_PLN"].sum() if pos["Val_PLN"].notna().any() else None
    total_cost = pos.apply(lambda r: r["Ilość"] * r["Avg"] * 1 if r["Ilość"] and r["Avg"] else 0, axis=1).sum()
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

    # Priority actions
    recs = load_recs()
    prio = [(t, r) for t, r in recs.items() if r.get("priority_action")]
    if prio:
        st.markdown('<div class="section-header">⚡ Priorytetowe działania</div>', unsafe_allow_html=True)
        html = '<div class="actions">'
        for t, r in sorted(prio, key=lambda x: REC_ORDER.get(x[1].get("recommendation","HOLD"), 3)):
            rec  = r.get("recommendation", "HOLD")
            ac   = REC_ACTION.get(rec, "a-warn")
            dot  = REC_DOT.get(rec, "dot-warn")
            html += f"""<div class="action {ac}">
                <div class="action-dot {dot}"></div>
                <span class="action-ticker">{t}</span>
                <span style="color:#64748b;font-size:12px">·</span>
                <span>{r['priority_action']}</span>
            </div>"""
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)

    # Positions table
    st.markdown('<div class="section-header">📊 Pozycje</div>', unsafe_allow_html=True)
    df = pos.sort_values("Rec_sort")

    rows_html = ""
    for _, r in df.iterrows():
        rec      = r["Rec"]
        row_cls  = REC_ROW.get(rec, "row-hold")
        price_s  = f'<span class="t-price">{r["Cena"]:.2f}</span> <span class="t-ccy">{r["Waluta"]}</span>' if r["Cena"] else "—"
        chg_s    = f'<span class="{pclass(r["Dzień%"])}">{fmt_pct(r["Dzień%"])}</span>' if r["Dzień%"] is not None else '<span class="t-neu">—</span>'
        val_s    = f'<span class="{pclass(r["Val_PLN"])}">{fmt_pln(r["Val_PLN"])}</span>' if r["Val_PLN"] else '<span class="t-neu">—</span>'
        pnl_s    = f'<span class="{pclass(r["PnL_PLN"])}">{fmt_pln(r["PnL_PLN"])}</span>' if r["PnL_PLN"] is not None else '<span class="t-neu">—</span>'
        pnlp_s   = f'<span class="{pclass(r["PnL%"])}">{fmt_pct(r["PnL%"])}</span>' if r["PnL%"] is not None else '<span class="t-neu">—</span>'
        fv_s     = f'<span class="t-fv">{r["FV"]:.0f} <span class="t-ccy">{r["FV_ccy"]}</span></span>' if r["FV"] else '<span class="t-neu">—</span>'
        up_s     = f'<span class="{pclass(r["Upside"])}">{fmt_pct(r["Upside"])}</span>' if r["Upside"] is not None else '<span class="t-neu">—</span>'
        badge    = f'<span class="badge b-{rec}">{rec}</span>' if rec != "—" else "—"
        rows_html += f"""<tr class="{row_cls}">
            <td><span class="t-ticker">{r['Ticker']}</span></td>
            <td><span class="t-name">{r['Nazwa']}</span></td>
            <td>{price_s}</td>
            <td>{chg_s}</td>
            <td>{val_s}</td>
            <td>{pnl_s}</td>
            <td>{pnlp_s}</td>
            <td>{fv_s}</td>
            <td>{up_s}</td>
            <td>{badge}</td>
        </tr>"""

    st.markdown(f"""
    <div class="pos-table-wrap">
    <table class="pos-table">
        <thead><tr>
            <th>Ticker</th><th>Nazwa</th><th>Cena</th><th>Dzień</th>
            <th>Wartość PLN</th><th>P&L</th><th>P&L%</th>
            <th>Fair Value</th><th>Upside</th><th>Rec</th>
        </tr></thead>
        <tbody>{rows_html}</tbody>
    </table>
    </div>
    """, unsafe_allow_html=True)

# ─── PAGE: DETAIL ─────────────────────────────────────────────────────────────
def page_detail(ticker, pos):
    recs = load_recs()
    rec  = recs.get(ticker, {})
    row  = pos[pos["Ticker"] == ticker].iloc[0] if not pos[pos["Ticker"] == ticker].empty else None

    recommendation = rec.get("recommendation", "—")
    fv   = rec.get("fair_value")
    fv_c = rec.get("fair_value_currency", "")
    ep   = rec.get("entry_point")

    price  = row["Cena"]  if row is not None else None
    ccy    = row["Waluta"] if row is not None else ""
    chg    = row["Dzień%"] if row is not None else None
    pnl    = row["PnL_PLN"] if row is not None else None
    pnl_p  = row["PnL%"]  if row is not None else None
    upside = (fv - price) / price * 100 if fv and price else rec.get("upside_pct")

    # Header
    badge_cls = {"BUY": "#10b981", "SELL": "#ef4444", "REDUCE": "#f59e0b", "HOLD": "#64748b"}.get(recommendation, "#64748b")
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:24px">
        <div>
            <div style="font-size:26px;font-weight:800;color:#f8fafc;letter-spacing:-0.5px">{rec.get('name', ticker)}</div>
            <div style="font-size:13px;color:#475569;margin-top:2px">{ticker} · {ccy}</div>
        </div>
        <div style="margin-left:auto">
            <span class="badge b-{recommendation}" style="font-size:13px;padding:6px 16px">{recommendation}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Detail cards
    ep_txt = f"{ep:.0f} {fv_c}" if ep else "Nie dotyczy"
    st.markdown(f"""
    <div class="detail-grid">
        <div class="dcard">
            <div class="dcard-label">Cena aktualna</div>
            <div class="dcard-value">{f"{price:.2f}" if price else "—"} <span style="font-size:14px;color:#475569">{ccy}</span></div>
            <div class="dcard-sub {kpiclass(chg)}">{fmt_pct(chg)} dziś</div>
        </div>
        <div class="dcard">
            <div class="dcard-label">Fair Value</div>
            <div class="dcard-value">{f"{fv:.0f}" if fv else "—"} <span style="font-size:14px;color:#475569">{fv_c}</span></div>
            <div class="dcard-sub {kpiclass(upside)}">{fmt_pct(upside)} upside</div>
        </div>
        <div class="dcard">
            <div class="dcard-label">Twój P&L</div>
            <div class="dcard-value {kpiclass(pnl)}">{fmt_pln(pnl)}</div>
            <div class="dcard-sub {kpiclass(pnl_p)}">{fmt_pct(pnl_p)}</div>
        </div>
        <div class="dcard">
            <div class="dcard-label">Entry Point</div>
            <div class="dcard-value" style="font-size:20px">{ep_txt}</div>
            <div class="dcard-sub neu">Margin of safety 20–30%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chart
    st.markdown('<div class="section-header">📉 Wykres ceny</div>', unsafe_allow_html=True)
    periods = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}
    sel = st.radio("", list(periods.keys()), horizontal=True, index=2, key="p_sel",
                   label_visibility="collapsed")
    fig = price_chart(ticker, periods[sel], ep, fv)
    if fig:
        st.plotly_chart(fig, width="stretch")
    else:
        st.info("Brak danych historycznych dla tego tickera.")

    # Thesis + risks
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown('<div class="section-header">💡 Teza inwestycyjna</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="thesis-card">{rec.get("thesis_full","Brak danych.")}</div>', unsafe_allow_html=True)
        tb = rec.get("thesis_breaker", "—")
        st.markdown(f"""
        <div class="breaker-card">
            <div style="font-size:10px;font-weight:600;color:#f87171;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:8px">⛔ Thesis Breaker — kiedy sprzedać</div>
            <div style="color:#fca5a5;font-size:14px;line-height:1.6">{tb}</div>
        </div>""", unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-header">⚠️ Ryzyka</div>', unsafe_allow_html=True)
        for risk in rec.get("risks", []):
            st.markdown(f'<div class="risk-item">· {risk}</div>', unsafe_allow_html=True)

        moat = rec.get("buffett_moat", "—")
        ne   = rec.get("next_earnings")
        upd  = rec.get("last_updated", "—")
        ne_html = f'<div style="margin-top:12px"><div style="font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:4px">Następny earnings</div><div style="color:#6366f1;font-size:14px;font-weight:600">{ne}</div></div>' if ne else ""
        st.markdown(f"""
        <div class="moat-card">
            <div style="font-size:10px;font-weight:600;color:#818cf8;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:6px">Buffett MOAT</div>
            <div style="color:#e0e7ff;font-size:16px;font-weight:700">🏰 {moat}</div>
            <div style="margin-top:12px;font-size:10px;font-weight:600;color:#475569;text-transform:uppercase;letter-spacing:1.5px">Analiza z dnia</div>
            <div style="color:#64748b;font-size:13px;margin-top:3px">{upd}</div>
            {ne_html}
        </div>""", unsafe_allow_html=True)

    prio = rec.get("priority_action")
    if prio:
        ac = REC_ACTION.get(recommendation, "a-warn")
        dot = REC_DOT.get(recommendation, "dot-warn")
        st.markdown(f"""
        <div class="action {ac}" style="margin-top:20px;font-size:15px">
            <div class="action-dot {dot}"></div>
            <b>Zalecane działanie:</b>&nbsp; {prio}
        </div>""", unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────────────────────────────────────
def main():
    df, demo = load_portfolio()
    fx       = get_fx()
    prices   = get_live_prices(tuple(df["Ticker"].tolist()))
    recs     = load_recs()
    pos      = build_positions(df, prices, fx, recs)

    with st.sidebar:
        st.markdown("""
        <div style="padding:8px 0 20px">
            <div style="font-size:18px;font-weight:800;color:#f1f5f9;letter-spacing:-0.3px">📈 Invest</div>
            <div style="font-size:11px;color:#475569;margin-top:2px">Dashboard</div>
        </div>
        """, unsafe_allow_html=True)

        options = ["📊 Overview"] + list(recs.keys())
        labels  = ["📊 Overview"] + [
            f"{'🟢' if recs[t].get('recommendation')=='BUY' else '🔴' if recs[t].get('recommendation')=='SELL' else '🟠' if recs[t].get('recommendation')=='REDUCE' else '⚪'} {t}"
            for t in recs if t in df["Ticker"].values
        ]
        page = st.radio("", labels, label_visibility="collapsed")

        st.markdown("---")
        st.markdown(f"""
        <div style="font-size:11px;color:#334155;line-height:2">
            <b style="color:#475569">Kursy FX</b><br>
            USD/PLN &nbsp; {fx.get('USD',0):.3f}<br>
            EUR/PLN &nbsp; {fx.get('EUR',0):.3f}<br>
            HKD/PLN &nbsp; {fx.get('HKD',0):.3f}
        </div>
        """, unsafe_allow_html=True)

    if page == "📊 Overview":
        page_overview(pos, demo)
    else:
        ticker = page.split(" ", 1)[1].strip()
        page_detail(ticker, pos)

if __name__ == "__main__" or True:
    main()
