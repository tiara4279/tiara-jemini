# ============================================================
#  글로벌 매크로 대시보드 — app.py (완전 통합본)
#  처음 실행 시 자동으로 필요한 패키지를 설치합니다.
# ============================================================
import subprocess, sys, os

# ── 자동 패키지 설치 ─────────────────────────────────────────
REQUIRED = [
    "streamlit",
    "yfinance",
    "pandas",
    "numpy",
    "plotly",
    "fredapi",
    "pandas-datareader",
    "requests",
]

def install_missing():
    for pkg in REQUIRED:
        try:
            __import__(pkg.replace("-", "_").split(">=")[0])
        except ImportError:
            print(f"📦 설치 중: {pkg}")
            subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "-q"])

install_missing()

# ── 이하 메인 앱 ─────────────────────────────────────────────
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# ── FRED API (선택) ──────────────────────────────────────────
FRED_API_KEY = os.getenv("FRED_API_KEY", "")
try:
    from fredapi import Fred
    fred = Fred(api_key=FRED_API_KEY) if FRED_API_KEY else None
except Exception:
    fred = None

# ── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="글로벌 매크로 대시보드",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── 스타일 ────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;600&family=Noto+Sans+KR:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stApp {
    background: #060A12;
}
.block-container {
    padding-top: 1.2rem !important;
    max-width: 1400px;
}

/* ── 헤더 ── */
.main-title {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.7rem;
    font-weight: 600;
    color: #E2E8F0;
    letter-spacing: 0.04em;
}
.main-sub {
    font-size: 0.73rem;
    color: #3D526E;
    letter-spacing: 0.1em;
    margin-top: 2px;
}
.ts {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: #2A3A52;
    text-align: right;
}

/* ── 섹션 라벨 ── */
.sec-hd {
    background: linear-gradient(90deg,#00D4FF12,transparent);
    border-left: 3px solid #00D4FF;
    padding: 6px 14px;
    margin: 28px 0 10px;
    border-radius: 0 6px 6px 0;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    letter-spacing: 0.14em;
    color: #00D4FF;
    text-transform: uppercase;
}

/* ── 지표 카드 ── */
.kcard {
    background: linear-gradient(140deg,#111827,#0C1420);
    border: 1px solid #1A2A3F;
    border-radius: 10px;
    padding: 14px 16px 10px;
    margin-bottom: 10px;
    transition: border-color .25s;
}
.kcard:hover { border-color: #00D4FF44; }
.klabel {
    font-size: 0.68rem;
    color: #4B6280;
    letter-spacing: .09em;
    text-transform: uppercase;
    margin-bottom: 3px;
}
.kval {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 1.42rem;
    font-weight: 600;
    color: #DDE6F0;
    line-height: 1.15;
}
.kup   { color: #10B981; font-size: .78rem; font-family: 'IBM Plex Mono'; }
.kdn   { color: #EF4444; font-size: .78rem; font-family: 'IBM Plex Mono'; }
.kna   { color: #475569; font-size: .78rem; font-family: 'IBM Plex Mono'; }
.ksub  { color: #2E3F55; font-size: .66rem; margin-top: 2px; }

/* ── 배지 ── */
.b-low  { background:#10B98118; color:#10B981; border:1px solid #10B98138;
           padding:1px 7px; border-radius:99px; font-size:.65rem; }
.b-mid  { background:#F59E0B18; color:#F59E0B; border:1px solid #F59E0B38;
           padding:1px 7px; border-radius:99px; font-size:.65rem; }
.b-hi   { background:#EF444418; color:#EF4444; border:1px solid #EF444438;
           padding:1px 7px; border-radius:99px; font-size:.65rem; }

hr { border-color:#151F2E !important; }

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] { background: #0C1420; border-radius:8px; gap:4px; }
.stTabs [data-baseweb="tab"] {
    color:#4B6280; font-family:'IBM Plex Mono',monospace; font-size:.75rem;
}
.stTabs [aria-selected="true"] { color:#00D4FF !important; background:#00D4FF12 !important; border-radius:6px; }

/* ── 버튼 ── */
.stButton>button {
    background:#00D4FF14; border:1px solid #00D4FF40; color:#00D4FF;
    font-family:'IBM Plex Mono',monospace; font-size:.75rem;
    border-radius:6px; transition:.2s;
}
.stButton>button:hover { background:#00D4FF28; border-color:#00D4FF80; }
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  공통 유틸
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_yf(ticker, period="6mo", interval="1d"):
    try:
        h = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if h.empty:
            return None, None, None
        last = float(h["Close"].iloc[-1])
        prev = float(h["Close"].iloc[-2]) if len(h) >= 2 else last
        chg  = (last - prev) / prev * 100
        return last, chg, h
    except Exception:
        return None, None, None

@st.cache_data(ttl=600)
def get_fred(sid, limit=60):
    if fred is None:
        return None
    try:
        s = fred.get_series(sid).dropna().tail(limit)
        return s if len(s) > 1 else None
    except Exception:
        return None

def f(v, d=2, pre="", suf=""):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "N/A"
    return f"{pre}{v:,.{d}f}{suf}"

def delta(chg):
    if chg is None:
        return '<span class="kna">— N/A</span>'
    a = "▲" if chg >= 0 else "▼"
    c = "kup" if chg >= 0 else "kdn"
    return f'<span class="{c}">{a} {abs(chg):.3f}%</span>'

def card(label, val_str, chg=None, sub="", badge=""):
    b = f" &nbsp;{badge}" if badge else ""
    s = f'<div class="ksub">{sub}</div>' if sub else ""
    return f"""
    <div class="kcard">
        <div class="klabel">{label}</div>
        <div class="kval">{val_str}{b}</div>
        {delta(chg)} {s}
    </div>"""

def sec(icon, title):
    st.markdown(f'<div class="sec-hd">{icon}&nbsp;&nbsp;{title}</div>', unsafe_allow_html=True)

def spark(hist, color="#00D4FF", h=75):
    if hist is None or hist.empty:
        return
    fig = go.Figure(go.Scatter(
        x=hist.index, y=hist["Close"], mode="lines",
        line=dict(color=color, width=1.6),
        fill="tozeroy", fillcolor=color[:7] + "14",
    ))
    fig.update_layout(
        height=h, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def spark_fred(series, color="#00D4FF", h=75):
    if series is None:
        return
    fig = go.Figure(go.Scatter(
        x=series.index, y=series.values, mode="lines",
        line=dict(color=color, width=1.6),
        fill="tozeroy", fillcolor=color[:7] + "14",
    ))
    fig.update_layout(
        height=h, margin=dict(l=0,r=0,t=0,b=0),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False), yaxis=dict(visible=False), showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

def risk_badge(name, val):
    if val is None:
        return ""
    tbl = {"VIX": [(20,"b-low","안정"), (30,"b-mid","주의"), (99,"b-hi","위험")],
           "MOVE":[(80,"b-low","안정"),(130,"b-mid","주의"),(999,"b-hi","위험")]}
    if name in tbl:
        for thr, cls, lbl in tbl[name]:
            if val < thr:
                return f'<span class="{cls}">{lbl}</span>'
    return ""


# ═══════════════════════════════════════════════════════════
#  헤더
# ═══════════════════════════════════════════════════════════

now_str = datetime.utcnow().strftime("%Y-%m-%d  %H:%M  UTC")
hc1, hc2 = st.columns([4, 1])
with hc1:
    st.markdown('<div class="main-title">📡 글로벌 매크로 대시보드</div>', unsafe_allow_html=True)
    st.markdown('<div class="main-sub">GLOBAL MACRO MONITOR — REAL-TIME FINANCIAL INDICATORS</div>', unsafe_allow_html=True)
with hc2:
    st.markdown(f'<div class="ts" style="padding-top:14px">🕐 {now_str}</div>', unsafe_allow_html=True)
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear(); st.rerun()

st.markdown("---")

# FRED 미설정 안내
if not FRED_API_KEY:
    st.info(
        "ℹ️ **FRED API 키**가 없으면 연준·유동성 지표는 데모값으로 표시됩니다.  \n"
        "무료 발급 → [fred.stlouisfed.org](https://fred.stlouisfed.org/docs/api/api_key.html)  \n"
        "발급 후 터미널에서: `set FRED_API_KEY=발급키` (윈도우) 또는 `export FRED_API_KEY=발급키` (맥/리눅스)"
    )


# ═══════════════════════════════════════════════════════════
#  §1  세계 외환 지표
# ═══════════════════════════════════════════════════════════

sec("🌐", "세계 외환 지표")

FX = [
    ("EUR/USD",  "EURUSD=X", "#10B981", "유로 / 달러"),
    ("USD/JPY",  "JPY=X",    "#3B82F6", "달러 / 엔"),
    ("USD/CNY",  "CNY=X",    "#F59E0B", "달러 / 위안"),
    ("GBP/USD",  "GBPUSD=X", "#8B5CF6", "파운드 / 달러"),
    ("USD/CHF",  "CHF=X",    "#EC4899", "달러 / 스위스프랑"),
    ("AUD/USD",  "AUDUSD=X", "#06B6D4", "호주달러 / 달러"),
]

cols = st.columns(6)
for col, (name, tk, color, desc) in zip(cols, FX):
    with col:
        v, chg, h = get_yf(tk, "1mo", "1d")
        st.markdown(card(name, f(v, 4), chg, desc), unsafe_allow_html=True)
        spark(h, color, 65)


# ═══════════════════════════════════════════════════════════
#  §2  한국 경제 지표
# ═══════════════════════════════════════════════════════════

sec("🇰🇷", "한국 경제 지표")

KR = [
    ("KOSPI",   "^KS11",  "#F59E0B", "코스피 종합주가지수"),
    ("KOSDAQ",  "^KQ11",  "#10B981", "코스닥 지수"),
    ("원/달러", "KRW=X",  "#3B82F6", "원화 / 미국달러 환율"),
]

cols = st.columns(3)
for col, (name, tk, color, desc) in zip(cols, KR):
    with col:
        v, chg, h = get_yf(tk, "3mo", "1d")
        st.markdown(card(name, f(v, 2), chg, desc), unsafe_allow_html=True)
        spark(h, color, 100)


# ═══════════════════════════════════════════════════════════
#  §3  미국 지수 및 선물
# ═══════════════════════════════════════════════════════════

sec("🇺🇸", "미국 지수 및 선물")

US = [
    ("S&P 500",    "^GSPC",  "#10B981", "미국 S&P 500 지수"),
    ("나스닥 100", "^NDX",   "#3B82F6", "나스닥 100"),
    ("다우존스",   "^DJI",   "#8B5CF6", "다우존스 산업평균"),
    ("S&P 선물",   "ES=F",   "#F59E0B", "E-mini S&P 500 선물"),
    ("나스닥 선물","NQ=F",   "#06B6D4", "E-mini 나스닥 선물"),
    ("러셀 2000",  "^RUT",   "#EC4899", "소형주 지수"),
]

c1, c2, c3 = st.columns(3)
for i, (name, tk, color, desc) in enumerate(US):
    with [c1, c2, c3][i % 3]:
        v, chg, h = get_yf(tk, "3mo", "1d")
        st.markdown(card(name, f(v, 2), chg, desc), unsafe_allow_html=True)
        spark(h, color, 85)


# ═══════════════════════════════════════════════════════════
#  §4  시장 리스크 및 스트레스 지표
# ═══════════════════════════════════════════════════════════

sec("⚠️", "시장 리스크 및 스트레스 지표")

r1, r2, r3, r4 = st.columns(4)

with r1:
    v, chg, h = get_yf("^VIX", "6mo", "1d")
    st.markdown(card("VIX (공포지수)", f(v, 2), chg,
                     "CBOE 변동성 지수", risk_badge("VIX", v)), unsafe_allow_html=True)
    spark(h, "#EF4444", 85)

with r2:
    v, chg, h = get_yf("^MOVE", "6mo", "1d")
    st.markdown(card("MOVE (채권 변동성)", f(v, 2), chg,
                     "ICE BofA 채권 변동성", risk_badge("MOVE", v)), unsafe_allow_html=True)
    spark(h, "#F59E0B", 85)

with r3:
    # 장단기 금리차: FRED 우선, 없으면 TNX로 대체
    ts = get_fred("T10Y2Y")
    if ts is not None:
        lv = float(ts.iloc[-1]); pv = float(ts.iloc[-2])
        chg_ts = lv - pv
        clr = "kup" if lv >= 0 else "kdn"
        arr = "▲" if lv >= 0 else "▼"
        st.markdown(f"""
        <div class="kcard">
            <div class="klabel">장단기 금리차 (10Y-2Y)</div>
            <div class="kval">{lv:+.2f}%</div>
            <span class="{clr}">{arr} {abs(chg_ts):.3f}%p</span>
            <div class="ksub">FRED T10Y2Y — 수익률 곡선</div>
        </div>""", unsafe_allow_html=True)
        spark_fred(ts, "#10B981", 85)
    else:
        v, chg, h = get_yf("^TNX", "6mo", "1d")
        st.markdown(card("10Y 국채금리", f(v, 3, suf="%"), chg, "미국 10년 국채"), unsafe_allow_html=True)
        spark(h, "#10B981", 85)

with r4:
    v, chg, h = get_yf("HYG", "6mo", "1d")
    st.markdown(card("HYG (하이일드 ETF)", f(v, 2, pre="$"), chg,
                     "HY 스프레드 프록시"), unsafe_allow_html=True)
    spark(h, "#8B5CF6", 85)

# FRED 하이일드 스프레드 실데이터
hy = get_fred("BAMLH0A0HYM2")
if hy is not None:
    lv = float(hy.iloc[-1]); pv = float(hy.iloc[-2])
    chg_hy = (lv - pv) / pv * 100
    fe1, fe2 = st.columns(2)
    with fe1:
        st.markdown(card("하이일드 스프레드 (OAS)", f(lv, 2, suf="%"), chg_hy,
                         "ICE BofA US HY OAS — FRED"), unsafe_allow_html=True)
        spark_fred(hy, "#EF4444", 80)


# ═══════════════════════════════════════════════════════════
#  §5  유동성 핵심 창구
# ═══════════════════════════════════════════════════════════

sec("🏦", "유동성을 좌우하는 핵심 창구 (연준)")

LIQ = [
    ("WALCL",    "연준 총자산 (대차대조표)", "#3B82F6", 7_200),
    ("WRBWFRBL", "지급준비금 잔고",          "#10B981", 3_300),
    ("WTREGEN",  "TGA (재무부 일반계정)",    "#F59E0B",   750),
]

l1, l2, l3 = st.columns(3)
for col, (sid, label, color, demo) in zip([l1, l2, l3], LIQ):
    with col:
        data = get_fred(sid, 60)
        if data is not None:
            lv = float(data.iloc[-1]); pv = float(data.iloc[-2])
            chg = (lv - pv) / pv * 100
            st.markdown(card(label, f(lv, 1, suf=" B$"), chg, f"FRED: {sid}"), unsafe_allow_html=True)
            spark_fred(data, color, 85)
        else:
            st.markdown(card(label, f(demo, 0, suf=" B$"), None,
                             f"⚠️ FRED 키 필요 | 데모값"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §6  은행 신용 및 단기 자금 시장
# ═══════════════════════════════════════════════════════════

sec("💰", "은행 신용 및 단기 자금 시장")

CRED = [
    ("RRPONTSYD", "역레포 (ON RRP)",    "#EC4899", "%",  400,   2),
    ("WRMFSL",    "MMF 총잔고",          "#06B6D4", "B$", 6_200, 1),
    ("TOTLL",     "상업은행 총대출",     "#8B5CF6", "B$", 17_500,1),
    ("SOFR",      "SOFR (익일물 금리)",  "#F59E0B", "%",  5.33,  3),
]

crs = st.columns(4)
for col, (sid, label, color, unit, demo, dp) in zip(crs, CRED):
    with col:
        data = get_fred(sid, 60)
        suf = "%" if unit == "%" else " B$"
        if data is not None:
            lv = float(data.iloc[-1]); pv = float(data.iloc[-2])
            chg = (lv - pv) / pv * 100 if pv else 0
            st.markdown(card(label, f(lv, dp, suf=suf), chg, f"FRED: {sid}"), unsafe_allow_html=True)
            spark_fred(data, color, 80)
        else:
            st.markdown(card(label, f(demo, dp, suf=suf), None,
                             "⚠️ FRED 키 필요 | 데모값"), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §7  인플레이션 및 글로벌 매크로
# ═══════════════════════════════════════════════════════════

sec("📈", "인플레이션 및 글로벌 매크로")

m1, m2, m3, m4 = st.columns(4)

with m1:
    v, chg, h = get_yf("DX-Y.NYB", "6mo", "1d")
    st.markdown(card("DXY (달러 인덱스)", f(v, 3), chg, "ICE US Dollar Index"), unsafe_allow_html=True)
    spark(h, "#F59E0B", 90)

with m2:
    v, chg, h = get_yf("GC=F", "6mo", "1d")
    st.markdown(card("금 선물", f(v, 2, pre="$"), chg, "COMEX Gold $/oz"), unsafe_allow_html=True)
    spark(h, "#FBBF24", 90)

with m3:
    bei5 = get_fred("T5YIE", 40)
    if bei5 is not None:
        lv = float(bei5.iloc[-1]); pv = float(bei5.iloc[-2])
        chg = (lv - pv) / pv * 100
        st.markdown(card("5Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T5YIE BEI"), unsafe_allow_html=True)
        spark_fred(bei5, "#10B981", 90)
    else:
        st.markdown(card("5Y 기대 인플레이션", "2.30%", None, "⚠️ FRED 키 필요"), unsafe_allow_html=True)

with m4:
    bei10 = get_fred("T10YIE", 40)
    if bei10 is not None:
        lv = float(bei10.iloc[-1]); pv = float(bei10.iloc[-2])
        chg = (lv - pv) / pv * 100
        st.markdown(card("10Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T10YIE BEI"), unsafe_allow_html=True)
        spark_fred(bei10, "#3B82F6", 90)
    else:
        st.markdown(card("10Y 기대 인플레이션", "2.28%", None, "⚠️ FRED 키 필요"), unsafe_allow_html=True)

# WTI
v2, chg2, h2 = get_yf("CL=F", "6mo", "1d")
mi1, mi2, _ = st.columns([1, 1, 2])
with mi1:
    st.markdown(card("WTI 원유 선물", f(v2, 2, pre="$", suf="/bbl"), chg2, "NYMEX Crude Oil"), unsafe_allow_html=True)
    spark(h2, "#64748B", 80)


# ═══════════════════════════════════════════════════════════
#  §8  종합 비교 차트 탭
# ═══════════════════════════════════════════════════════════

sec("📊", "종합 비교 차트")

tab1, tab2, tab3, tab4 = st.tabs([
    "📉 미국 지수 (1년)", "🌐 외환 6종 (6개월)",
    "⚠️ 리스크 지표 (1년)", "🇰🇷 한국 지수 (6개월)"
])

CHART_LAYOUT = dict(
    height=340, paper_bgcolor="#060A12", plot_bgcolor="#060A12",
    legend=dict(bgcolor="#0C1420", bordercolor="#1A2A3F", borderwidth=1,
                font=dict(color="#94A3B8", size=11)),
    xaxis=dict(gridcolor="#141E2E", color="#3D526E", showgrid=True),
    yaxis=dict(gridcolor="#141E2E", color="#3D526E", showgrid=True),
    margin=dict(l=50, r=20, t=20, b=30), hovermode="x unified",
    font=dict(family="IBM Plex Mono"),
)

with tab1:
    pairs = [("S&P 500","^GSPC","#10B981"), ("나스닥 100","^NDX","#3B82F6"),
             ("다우존스","^DJI","#8B5CF6"),  ("러셀 2000","^RUT","#F59E0B")]
    fig = go.Figure()
    for name, tk, clr in pairs:
        _, _, h = get_yf(tk, "1y", "1wk")
        if h is not None and not h.empty:
            n = h["Close"] / h["Close"].iloc[0] * 100
            fig.add_trace(go.Scatter(x=h.index, y=n, mode="lines",
                                     name=name, line=dict(color=clr, width=2)))
    fig.update_layout(**CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with tab2:
    fx_pairs = [("EUR/USD","EURUSD=X","#10B981"), ("USD/JPY","JPY=X","#3B82F6"),
                ("원/달러","KRW=X","#F59E0B"),    ("GBP/USD","GBPUSD=X","#8B5CF6"),
                ("USD/CNY","CNY=X","#EC4899"),    ("DXY","DX-Y.NYB","#06B6D4")]
    fig2 = make_subplots(rows=2, cols=3, subplot_titles=[p[0] for p in fx_pairs])
    for idx, (name, tk, clr) in enumerate(fx_pairs):
        r, c = divmod(idx, 3)
        _, _, h = get_yf(tk, "6mo", "1d")
        if h is not None and not h.empty:
            fig2.add_trace(go.Scatter(x=h.index, y=h["Close"], mode="lines",
                                      name=name, line=dict(color=clr, width=1.5),
                                      showlegend=False), row=r+1, col=c+1)
    fig2.update_layout(height=400, paper_bgcolor="#060A12", plot_bgcolor="#060A12",
                       margin=dict(l=20,r=20,t=40,b=20),
                       font=dict(color="#3D526E", family="IBM Plex Mono"))
    fig2.update_xaxes(gridcolor="#141E2E", color="#3D526E")
    fig2.update_yaxes(gridcolor="#141E2E", color="#3D526E")
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

with tab3:
    risk_pairs = [("VIX","^VIX","#EF4444"), ("MOVE","^MOVE","#F59E0B"), ("HYG","HYG","#8B5CF6")]
    fig3 = go.Figure()
    for name, tk, clr in risk_pairs:
        _, _, h = get_yf(tk, "1y", "1wk")
        if h is not None and not h.empty:
            n = h["Close"] / h["Close"].iloc[0] * 100
            fig3.add_trace(go.Scatter(x=h.index, y=n, mode="lines",
                                      name=name, line=dict(color=clr, width=2)))
    fig3.update_layout(**CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with tab4:
    kr_pairs = [("KOSPI","^KS11","#F59E0B"), ("KOSDAQ","^KQ11","#10B981")]
    fig4 = go.Figure()
    for name, tk, clr in kr_pairs:
        _, _, h = get_yf(tk, "6mo", "1d")
        if h is not None and not h.empty:
            n = h["Close"] / h["Close"].iloc[0] * 100
            fig4.add_trace(go.Scatter(x=h.index, y=n, mode="lines",
                                      name=name, line=dict(color=clr, width=2),
                                      fill="tozeroy", fillcolor=clr + "12"))
    fig4.update_layout(**CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════
#  사이드바 — 빠른 설정
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.markdown("---")
    st.markdown("**FRED API 키 입력**")
    api_input = st.text_input("API Key", value=FRED_API_KEY,
                              type="password", placeholder="여기에 붙여넣기")
    if api_input and api_input != FRED_API_KEY:
        os.environ["FRED_API_KEY"] = api_input
        st.success("✅ 키 적용! 새로고침 하세요.")
    st.markdown("---")
    st.markdown("**캐시 설정**")
    st.caption("데이터는 5분마다 자동 갱신됩니다.")
    if st.button("🗑️ 캐시 초기화", use_container_width=True):
        st.cache_data.clear(); st.rerun()
    st.markdown("---")
    st.markdown("**데이터 소스**")
    st.markdown("""
    - 📈 Yahoo Finance
    - 🏛️ FRED (St. Louis Fed)
    - ⏱ 갱신: 5분
    """)
    st.markdown("---")
    st.caption(f"🕐 {now_str}")


# ─── 푸터 ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:#1E2D40;font-size:.65rem;
     font-family:'IBM Plex Mono',monospace;padding:10px 0">
    📡 데이터 소스: Yahoo Finance · FRED (St. Louis Fed) &nbsp;|&nbsp;
    ⏱ 캐시: 5분 갱신 &nbsp;|&nbsp; 🕐 {now_str}
</div>
""", unsafe_allow_html=True)
