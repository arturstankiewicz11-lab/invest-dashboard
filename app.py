import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import json
import io
from datetime import datetime

# ─── PAGE CONFIG ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Invest Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── STYLES ──────────────────────────────────────────────────────────────────
st.markdown("""
<style>
[data-testid="stAppViewContainer"] { background-color: #0f0f1a; }
[data-testid="stSidebar"] { background-color: #13132a; border-right: 1px solid #2a2a4a; }
[data-testid="stSidebarNav"] { display: none; }

.kpi-card {
    background: linear-gradient(135deg, #1e1e3a 0%, #16213e 100%);
    border: 1px solid #2a2a4a;
    border-radius: 14px;
    padding: 22px 24px;
}
.kpi-label { color: #8888aa; font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 6px; }
.kpi-value { color: #ffffff; font-size: 26px; font-weight: 700; }
.kpi-sub-pos { color: #00d084; font-size: 13px; margin-top: 4px; }
.kpi-sub-neg { color: #ff4b4b; font-size: 13px; margin-top: 4px; }
.kpi-sub-neu { color: #8888aa; font-size: 13px; margin-top: 4px; }

.section-title {
    color: #8888aa;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin: 24px 0 12px 0;
    padding-bottom: 6px;
    border-bottom: 1px solid #2a2a4a;
}

.action-card {
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    font-size: 14px;
}
.action-sell { background: rgba(255,75,75,0.1); border-left: 3px solid #ff4b4b; }
.action-buy  { background: rgba(0,208,132,0.1); border-left: 3px solid #00d084; }
.action-info { background: rgba(255,215,0,0.08); border-left: 3px solid #ffd700; }

.rec-badge {
    display: inline-block;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.5px;
}
.rec-BUY    { background: rgba(0,208,132,0.15); color: #00d084; }
.rec-HOLD   { background: rgba(255,215,0,0.15);  color: #ffd700; }
.rec-SELL   { background: rgba(255,75,75,0.15);  color: #ff4b4b; }
.rec-REDUCE { background: rgba(255,140,0,0.15);  color: #ff8c00; }

.detail-card {
    background: #1a1a2e;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
}
.detail-label { color: #8888aa; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
.detail-value { color: #ffffff; font-size: 20px; font-weight: 600; margin-top: 4px; }

.demo-banner {
    background: rgba(0,217,255,0.08);
    border: 1px solid rgba(0,217,255,0.3);
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 20px;
    font-size: 13px;
    color: #00d9ff;
}
</style>
""", unsafe_allow_html=True)

# ─── SAMPLE DATA ─────────────────────────────────────────────────────────────
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

# ─── DATA LOADING ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=300)
def load_portfolio() -> tuple[pd.DataFrame, bool]:
    try:
        url = st.secrets["gsheets"]["portfolio_url"]
        df = pd.read_csv(url)
        return df, False
    except Exception:
        df = pd.read_csv(io.StringIO(SAMPLE_CSV))
        return df, True


@st.cache_data(ttl=300)
def get_live_prices(tickers: tuple) -> dict:
    result = {}
    for ticker in tickers:
        try:
            hist = yf.Ticker(ticker).history(period="5d", interval="1d")
            if len(hist) >= 2:
                prev  = float(hist["Close"].iloc[-2])
                curr  = float(hist["Close"].iloc[-1])
                chg   = (curr - prev) / prev * 100
            elif len(hist) == 1:
                curr, chg = float(hist["Close"].iloc[-1]), 0.0
            else:
                curr, chg = None, None
            result[ticker] = {"price": curr, "change_pct": chg}
        except Exception:
            result[ticker] = {"price": None, "change_pct": None}
    return result


@st.cache_data(ttl=1800)
def get_fx_rates() -> dict:
    pairs = {"USD": "USDPLN=X", "EUR": "EURPLN=X", "HKD": "HKDPLN=X"}
    fallback = {"USD": 3.98, "EUR": 4.30, "HKD": 0.51, "PLN": 1.0}
    rates = {"PLN": 1.0}
    for ccy, sym in pairs.items():
        try:
            hist = yf.Ticker(sym).history(period="5d")
            rates[ccy] = float(hist["Close"].iloc[-1])
        except Exception:
            rates[ccy] = fallback[ccy]
    return rates


@st.cache_data(ttl=3600)
def load_recommendations() -> dict:
    try:
        with open("data/recommendations.json", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


@st.cache_data(ttl=300)
def get_history(ticker: str, period: str) -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).history(period=period, interval="1d")
    except Exception:
        return pd.DataFrame()

# ─── HELPERS ─────────────────────────────────────────────────────────────────

REC_ORDER = {"SELL": 0, "REDUCE": 1, "BUY": 2, "HOLD": 3}
REC_EMOJI = {"BUY": "🟢", "HOLD": "🟡", "SELL": "🔴", "REDUCE": "🟠"}

def fmt_pln(val: float) -> str:
    if val is None:
        return "—"
    sign = "+" if val >= 0 else ""
    if abs(val) >= 1_000_000:
        return f"{sign}{val/1_000_000:.2f}M PLN"
    if abs(val) >= 1_000:
        return f"{sign}{val/1_000:.1f}k PLN"
    return f"{sign}{val:.0f} PLN"

def fmt_pct(val: float) -> str:
    if val is None:
        return "—"
    return f"{'+'if val>=0 else ''}{val:.1f}%"

def color_class(val: float) -> str:
    if val is None:
        return "kpi-sub-neu"
    return "kpi-sub-pos" if val >= 0 else "kpi-sub-neg"

def rec_badge(rec: str) -> str:
    return f'<span class="rec-badge rec-{rec}">{rec}</span>'


def build_positions(df: pd.DataFrame, prices: dict, fx: dict, recs: dict) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        ticker = row["Ticker"]
        ccy    = row["Waluta"]
        qty    = float(row["Ilosc"])
        avg    = float(row["Srednia_cena"])
        live   = prices.get(ticker, {})
        price  = live.get("price")
        chg    = live.get("change_pct")
        rate   = fx.get(ccy, 1.0)
        rec    = recs.get(ticker, {})

        cur_val_pln  = price * qty * rate if price and qty else None
        cost_pln     = avg   * qty * rate if avg and qty else None
        pnl_pln      = (cur_val_pln - cost_pln) if (cur_val_pln and cost_pln) else None
        pnl_pct      = (pnl_pln / cost_pln * 100) if (pnl_pln is not None and cost_pln and cost_pln != 0) else None

        fv       = rec.get("fair_value")
        fv_ccy   = rec.get("fair_value_currency", ccy)
        upside   = rec.get("upside_pct")
        if fv and price:
            fv_in_trade_ccy = fv if fv_ccy == ccy else fv  # same ccy assumed
            upside = (fv_in_trade_ccy - price) / price * 100

        rows.append({
            "Ticker":      ticker,
            "Nazwa":       row["Nazwa"],
            "Cena":        price,
            "Waluta":      ccy,
            "Dzień%":      chg,
            "Ilość":       qty,
            "Śr. zakup":   avg if avg else None,
            "Wartość PLN": cur_val_pln,
            "P&L PLN":     pnl_pln,
            "P&L%":        pnl_pct,
            "Fair Value":  fv,
            "FV Waluta":   fv_ccy,
            "Upside%":     upside,
            "Rec":         rec.get("recommendation", "—"),
            "Rec sort":    REC_ORDER.get(rec.get("recommendation", "HOLD"), 3),
        })
    return pd.DataFrame(rows)


# ─── CHART ───────────────────────────────────────────────────────────────────

def price_chart(ticker: str, period: str, entry: float | None, fv: float | None) -> go.Figure | None:
    hist = get_history(ticker, period)
    if hist.empty:
        return None

    prices_series = hist["Close"].astype(float)
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=hist.index,
        y=prices_series,
        mode="lines",
        name="Cena",
        line=dict(color="#00d9ff", width=2),
        fill="tozeroy",
        fillcolor="rgba(0,217,255,0.04)",
        hovertemplate="%{x|%d %b %Y}<br>%{y:.2f}<extra></extra>"
    ))

    if fv:
        fig.add_hline(
            y=fv, line_dash="dash", line_color="#ffd700", line_width=1.5,
            annotation_text=f"Fair Value {fv:.0f}",
            annotation_font_color="#ffd700", annotation_font_size=11,
            annotation_position="top right"
        )

    if entry:
        fig.add_hline(
            y=entry, line_dash="dot", line_color="#00d084", line_width=1.5,
            annotation_text=f"Entry {entry:.0f}",
            annotation_font_color="#00d084", annotation_font_size=11,
            annotation_position="bottom right"
        )

    fig.update_layout(
        plot_bgcolor="#0f0f1a",
        paper_bgcolor="#0f0f1a",
        font_color="#e0e0f0",
        showlegend=False,
        margin=dict(l=0, r=40, t=10, b=0),
        height=320,
        xaxis=dict(showgrid=False, color="#444466", tickfont_size=11),
        yaxis=dict(showgrid=True, gridcolor="#1e1e3a", color="#444466", tickfont_size=11),
        hovermode="x unified"
    )
    return fig


# ─── PAGES ───────────────────────────────────────────────────────────────────

def page_overview(pos: pd.DataFrame, demo: bool) -> None:
    if demo:
        st.markdown("""
        <div class="demo-banner">
        ⚙️ <b>Tryb demo</b> — widzisz strukturę portfela bez ilości i cen zakupu.
        Uzupełnij Google Sheets swoimi pozycjami (patrz README), a P&L pojawi się automatycznie.
        </div>
        """, unsafe_allow_html=True)

    # ── KPI ──
    total_val  = pos["Wartość PLN"].sum() if pos["Wartość PLN"].notna().any() else None
    total_pnl  = pos["P&L PLN"].sum()     if pos["P&L PLN"].notna().any()     else None
    total_cost = pos.apply(
        lambda r: r["Ilość"] * r["Śr. zakup"] if r["Ilość"] and r["Śr. zakup"] else 0, axis=1
    ).sum()
    pnl_pct    = (total_pnl / total_cost * 100) if (total_pnl and total_cost) else None
    day_pnl    = pos.apply(
        lambda r: (r["Cena"] * r["Ilość"] * r.get("_rate", 1)) * (r["Dzień%"] / 100)
        if (r["Cena"] and r["Ilość"] and r["Dzień%"]) else 0, axis=1
    ).sum()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        sub = fmt_pct(pnl_pct) if pnl_pct else "Uzupełnij pozycje"
        cls = color_class(pnl_pct)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Wartość portfela</div>
            <div class="kpi-value">{fmt_pln(total_val) if total_val else '—'}</div>
            <div class="{cls}">{sub}</div>
        </div>""", unsafe_allow_html=True)

    with c2:
        cls = color_class(total_pnl)
        sub = fmt_pct(pnl_pct) if pnl_pct else "—"
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Total P&L</div>
            <div class="kpi-value">{fmt_pln(total_pnl) if total_pnl else '—'}</div>
            <div class="{cls}">{sub}</div>
        </div>""", unsafe_allow_html=True)

    with c3:
        cls = color_class(day_pnl if day_pnl else None)
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Dzisiaj</div>
            <div class="kpi-value">{fmt_pln(day_pnl) if day_pnl else '—'}</div>
            <div class="{cls}">&nbsp;</div>
        </div>""", unsafe_allow_html=True)

    with c4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-label">Pozycji</div>
            <div class="kpi-value">{len(pos)}</div>
            <div class="kpi-sub-neu">Ostatnia aktualizacja: {datetime.now().strftime('%H:%M')}</div>
        </div>""", unsafe_allow_html=True)

    # ── PRIORITY ACTIONS ──
    recs_data = load_recommendations()
    actions = [(t, r) for t, r in recs_data.items() if r.get("priority_action")]

    if actions:
        st.markdown('<div class="section-title">Priorytetowe działania</div>', unsafe_allow_html=True)
        sells  = [(t, r) for t, r in actions if r["recommendation"] in ("SELL",)]
        buys   = [(t, r) for t, r in actions if r["recommendation"] == "BUY"]
        others = [(t, r) for t, r in actions if r["recommendation"] not in ("SELL", "BUY")]

        for t, r in sells:
            st.markdown(f'<div class="action-card action-sell">🔴 <b>{t}</b> — {r["priority_action"]}</div>', unsafe_allow_html=True)
        for t, r in buys:
            st.markdown(f'<div class="action-card action-buy">🟢 <b>{t}</b> — {r["priority_action"]}</div>', unsafe_allow_html=True)
        for t, r in others:
            st.markdown(f'<div class="action-card action-info">🟠 <b>{t}</b> — {r["priority_action"]}</div>', unsafe_allow_html=True)

    # ── POSITIONS TABLE ──
    st.markdown('<div class="section-title">Pozycje</div>', unsafe_allow_html=True)

    display = pos.sort_values("Rec sort").copy()

    def style_row(row):
        rec = row.get("Rec", "")
        colors = {"BUY": "#0d2b1a", "SELL": "#2b0d0d", "REDUCE": "#2b1a0d", "HOLD": ""}
        bg = colors.get(rec, "")
        return [f"background-color: {bg}" for _ in row]

    table_cols = ["Ticker", "Nazwa", "Cena", "Waluta", "Dzień%", "Wartość PLN", "P&L PLN", "P&L%", "Fair Value", "Upside%", "Rec"]
    display_table = display[table_cols].copy()

    # Format columns
    display_table["Cena"]        = display_table.apply(lambda r: f"{r['Cena']:.2f} {r['Waluta']}" if r['Cena'] else "—", axis=1)
    display_table["Dzień%"]      = display_table["Dzień%"].apply(lambda x: fmt_pct(x) if x else "—")
    display_table["Wartość PLN"] = display_table["Wartość PLN"].apply(lambda x: fmt_pln(x) if x else "—")
    display_table["P&L PLN"]     = display_table["P&L PLN"].apply(lambda x: fmt_pln(x) if x else "—")
    display_table["P&L%"]        = display_table["P&L%"].apply(lambda x: fmt_pct(x) if x else "—")
    display_table["Fair Value"]  = display_table.apply(
        lambda r: f"{r['Fair Value']:.0f} {display.loc[r.name, 'FV Waluta']}" if r['Fair Value'] else "—", axis=1)
    display_table["Upside%"]     = display_table["Upside%"].apply(lambda x: fmt_pct(x) if x else "—")
    display_table["Rec"]         = display_table["Rec"].apply(
        lambda x: f"{REC_EMOJI.get(x,'')} {x}" if x != "—" else "—")
    display_table = display_table.drop(columns=["Waluta"])

    st.dataframe(
        display_table,
        use_container_width=True,
        hide_index=True,
        height=500
    )


def page_detail(ticker: str, pos: pd.DataFrame) -> None:
    recs = load_recommendations()
    rec  = recs.get(ticker, {})
    row  = pos[pos["Ticker"] == ticker].iloc[0] if not pos[pos["Ticker"] == ticker].empty else None

    name = rec.get("name", ticker)
    recommendation = rec.get("recommendation", "—")
    fv   = rec.get("fair_value")
    fv_c = rec.get("fair_value_currency", "")
    ep   = rec.get("entry_point")
    upside = None

    price = row["Cena"] if row is not None else None
    if fv and price:
        upside = (fv - price) / price * 100

    # Header
    badge = REC_EMOJI.get(recommendation, "") + " " + recommendation
    st.markdown(f"## {name} &nbsp; `{ticker}`")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ccy = row["Waluta"] if row is not None else ""
        st.markdown(f"""
        <div class="detail-card">
            <div class="detail-label">Cena aktualna</div>
            <div class="detail-value">{f"{price:.2f} {ccy}" if price else "—"}</div>
            <div class="{color_class(row['Dzień%'] if row is not None else None)}">{fmt_pct(row['Dzień%'] if row is not None else None)} dziś</div>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="detail-card">
            <div class="detail-label">Fair Value</div>
            <div class="detail-value">{f"{fv:.0f} {fv_c}" if fv else "—"}</div>
            <div class="{color_class(upside)}">{fmt_pct(upside)} upside</div>
        </div>""", unsafe_allow_html=True)

    with col3:
        pnl = row["P&L PLN"] if row is not None else None
        pnl_pct = row["P&L%"] if row is not None else None
        st.markdown(f"""
        <div class="detail-card">
            <div class="detail-label">Twój P&L</div>
            <div class="detail-value">{fmt_pln(pnl)}</div>
            <div class="{color_class(pnl)}">{fmt_pct(pnl_pct)}</div>
        </div>""", unsafe_allow_html=True)

    with col4:
        ep_txt = f"{ep:.0f} {fv_c}" if ep else "Brak / nie dotyczy"
        st.markdown(f"""
        <div class="detail-card">
            <div class="detail-label">Entry Point</div>
            <div class="detail-value" style="font-size:18px">{ep_txt}</div>
            <div class="kpi-sub-neu">Rekomendacja: {badge}</div>
        </div>""", unsafe_allow_html=True)

    # Chart
    st.markdown('<div class="section-title">Wykres ceny</div>', unsafe_allow_html=True)
    period_map = {"1M": "1mo", "3M": "3mo", "6M": "6mo", "1Y": "1y"}
    sel = st.radio("Okres", list(period_map.keys()), horizontal=True, index=2, key="period_sel")
    fig = price_chart(ticker, period_map[sel], ep, fv)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nie udało się pobrać danych historycznych.")

    # Thesis
    col_a, col_b = st.columns([3, 2])
    with col_a:
        st.markdown('<div class="section-title">Teza inwestycyjna</div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="detail-card">{rec.get("thesis_full", "Brak danych.")}</div>""", unsafe_allow_html=True)

        tb = rec.get("thesis_breaker", "—")
        st.markdown(f"""
        <div class="detail-card" style="border-left: 3px solid #ff4b4b;">
            <div class="detail-label">Thesis Breaker — kiedy sprzedać</div>
            <div style="margin-top:8px; color:#ffcccc;">{tb}</div>
        </div>""", unsafe_allow_html=True)

    with col_b:
        st.markdown('<div class="section-title">Ryzyka</div>', unsafe_allow_html=True)
        risks = rec.get("risks", [])
        for risk in risks:
            st.markdown(f"""
            <div class="detail-card" style="padding: 10px 14px; margin-bottom: 6px;">
                ⚠️ {risk}
            </div>""", unsafe_allow_html=True)

        moat = rec.get("buffett_moat", "—")
        updated = rec.get("last_updated", "—")
        ne = rec.get("next_earnings")
        st.markdown(f"""
        <div class="detail-card" style="margin-top:8px;">
            <div class="detail-label">Buffett MOAT</div>
            <div style="color:#ffffff; margin: 6px 0 12px;">🏰 {moat}</div>
            <div class="detail-label">Analiza zaktualizowana</div>
            <div style="color:#8888aa; margin-top:4px;">{updated}</div>
            {'<div class="detail-label" style="margin-top:12px;">Następny earnings</div><div style="color:#00d9ff; margin-top:4px;">' + ne + '</div>' if ne else ''}
        </div>""", unsafe_allow_html=True)

    priority = rec.get("priority_action")
    if priority:
        rec_class = {"BUY": "action-buy", "SELL": "action-sell"}.get(recommendation, "action-info")
        st.markdown(f'<div class="action-card {rec_class}" style="margin-top:16px;">💡 <b>Zalecane działanie:</b> {priority}</div>', unsafe_allow_html=True)


# ─── MAIN ────────────────────────────────────────────────────────────────────

def main() -> None:
    portfolio_df, demo_mode = load_portfolio()
    fx = get_fx_rates()
    tickers = tuple(portfolio_df["Ticker"].tolist())
    prices  = get_live_prices(tickers)
    recs    = load_recommendations()

    # Add rate to df for day P&L calc
    portfolio_df["_rate"] = portfolio_df["Waluta"].map(fx).fillna(1.0)
    positions = build_positions(portfolio_df, prices, fx, recs)

    # ── SIDEBAR ──
    with st.sidebar:
        st.markdown("### 📈 Invest Dashboard")
        st.markdown("---")
        page = st.radio(
            "Widok",
            ["📊 Overview"] + [f"{REC_EMOJI.get(r.get('recommendation',''), '⚪')} {t}" for t, r in recs.items() if t in tickers],
            label_visibility="collapsed"
        )
        st.markdown("---")
        st.markdown(
            f"<div style='color:#444466; font-size:11px; padding:4px'>Kursy FX<br>"
            f"USD/PLN {fx.get('USD', 0):.3f} &nbsp; EUR/PLN {fx.get('EUR', 0):.3f}<br>"
            f"HKD/PLN {fx.get('HKD', 0):.3f}</div>",
            unsafe_allow_html=True
        )

    # ── ROUTING ──
    if page == "📊 Overview":
        page_overview(positions, demo_mode)
    else:
        ticker_selected = page.split(" ", 1)[1].strip()
        page_detail(ticker_selected, positions)


if __name__ == "__main__" or True:
    main()
