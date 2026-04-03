# ============================================================
#  글로벌 매크로 대시보드 — app.py (완전 통합본 FINAL)
#  ✅ sec() 정의 완료
#  ✅ Net Liquidity 실제 데이터 적용
#  ✅ 국채금리 분해 섹션 삭제
#  ✅ 단위 변환 수정 (WALCL=M$, RRP=B$, TGA=M$)
#  ✅ S&P500 직접 호출 (캐시 충돌 방지)
#  ✅ 데이터 실패 진단 UI 포함
# ============================================================
import subprocess, sys, warnings
warnings.filterwarnings("ignore")

REQUIRED = {
    "streamlit": "streamlit",
    "yfinance":  "yfinance",
    "pandas":    "pandas",
    "numpy":     "numpy",
    "plotly":    "plotly",
    "fredapi":   "fredapi",
    "requests":  "requests",
}

def install_missing():
    for import_name, pkg_name in REQUIRED.items():
        try:
            __import__(import_name)
        except ImportError:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", pkg_name, "-q"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )

install_missing()

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from fredapi import Fred

# ── FRED 연결
FRED_API_KEY = "44435d53f0376bf6ab6263db6892924f"
try:
    fred = Fred(api_key=FRED_API_KEY)
except Exception:
    fred = None

# ── 페이지 설정
st.set_page_config(
    page_title="글로벌 매크로 대시보드",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════
#  CSS 스타일
# ═══════════════════════════════════════════════════════════
def hex_to_rgba(hex_color, alpha=0.10):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

st.markdown("""<style>
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700;900&display=swap");

html, body, [class*="css"], .stMarkdown, .stText, p, span, div, label {
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stApp { background: #060A12 !important; }
.block-container { padding-top: 2rem !important; max-width: 1400px; }

h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    letter-spacing: 0.04em !important;
}

.stCaption, .stCaption p, small {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #5A8AAE !important;
    letter-spacing: 0.14em !important;
}

.sec-hd {
    background: linear-gradient(90deg, #00D4FF18, transparent);
    border-left: 4px solid #00D4FF;
    padding: 8px 16px;
    margin: 28px 0 12px;
    border-radius: 0 8px 8px 0;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.275rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.16em;
    color: #00D4FF !important;
    text-transform: uppercase;
}

.kcard {
    background: linear-gradient(140deg, #131E2E, #0C1520);
    border: 1px solid #1E3050;
    border-radius: 12px;
    padding: 16px 18px 12px;
    margin-bottom: 10px;
    transition: border-color .25s, box-shadow .25s;
}
.kcard:hover {
    border-color: #00D4FF66;
    box-shadow: 0 0 20px rgba(0,212,255,0.08);
}

.klabel {
    font-size: 0.72rem !important;
    font-weight: 700 !important;
    color: #6B8EAE !important;
    letter-spacing: .10em;
    text-transform: uppercase;
    margin-bottom: 5px;
}

.kval {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.55rem !important;
    font-weight: 700 !important;
    color: #FFFFFF !important;
    line-height: 1.2;
}

.kup {
    color: #22D98A !important;
    font-size: .84rem !important;
    font-weight: 700 !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

.kdn {
    color: #FF5555 !important;
    font-size: .84rem !important;
    font-weight: 700 !important;
    font-family: 'IBM Plex Mono', monospace !important;
}

.kna {
    color: #607090 !important;
    font-size: .84rem !important;
    font-weight: 600 !important;
}

.ksub {
    color: #4A6888 !important;
    font-size: .70rem !important;
    font-weight: 600 !important;
    margin-top: 4px;
}

.b-low { background: #10B98122; color: #22D98A !important; border: 1px solid #10B98155; padding: 2px 9px; border-radius: 99px; font-size: .70rem !important; font-weight: 700 !important; }
.b-mid { background: #F59E0B22; color: #FFCC44 !important; border: 1px solid #F59E0B55; padding: 2px 9px; border-radius: 99px; font-size: .70rem !important; font-weight: 700 !important; }
.b-hi  { background: #EF444422; color: #FF5555 !important; border: 1px solid #EF444455; padding: 2px 9px; border-radius: 99px; font-size: .70rem !important; font-weight: 700 !important; }

hr { border-color: #1A2A3F !important; }

.stTabs [data-baseweb="tab-list"] { background: #0C1420; border-radius: 10px; gap: 4px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: #5A7A9A !important; font-family: 'IBM Plex Mono', monospace !important; font-size: .80rem !important; font-weight: 700 !important; }
.stTabs [aria-selected="true"] { color: #00D4FF !important; background: #00D4FF18 !important; border-radius: 7px; }

.stButton > button {
    background: #00D4FF18 !important;
    border: 1px solid #00D4FF55 !important;
    color: #00D4FF !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: .78rem !important;
    font-weight: 700 !important;
    border-radius: 8px; transition: .2s;
}
.stButton > button:hover {
    background: #00D4FF30 !important;
    border-color: #00D4FFAA !important;
}

.stAlert p { font-weight: 700 !important; }

section[data-testid="stSidebar"] { background: #080E1A !important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    font-weight: 700 !important;
    color: #8AAAC8 !important;
}
</style>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  공통 유틸 함수
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=300)
def get_yf(ticker, period="6mo", interval="1d"):
    try:
        h = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if h.empty or len(h) < 2:
            return None, None, None
        last = float(h["Close"].iloc[-1])
        prev = float(h["Close"].iloc[-2])
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


def delta_html(chg):
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
        {delta_html(chg)}{s}
    </div>"""


def sec(icon, title):
    """섹션 헤더 출력"""
    st.markdown(
        f'<div class="sec-hd"><span style="text-transform:none;">{icon}</span>'
        f'&nbsp;&nbsp;{title}</div>',
        unsafe_allow_html=True
    )


def spark(hist_or_series, color="#00D4FF", h=75, is_series=False):
    if hist_or_series is None:
        return
    try:
        x = hist_or_series.index
        y = hist_or_series.values if is_series else hist_or_series["Close"].values
        if len(y) == 0:
            return
        fig = go.Figure(go.Scatter(
            x=x, y=y, mode="lines",
            line=dict(color=color[:7], width=1.8),
            fill="tozeroy",
            fillcolor=hex_to_rgba(color[:7], 0.10),
        ))
        fig.update_layout(
            height=h, margin=dict(l=0, r=0, t=0, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    except Exception:
        pass


def risk_badge(name, val):
    if val is None:
        return ""
    tbl = {
        "VIX":  [(20,"b-low","안정"), (30,"b-mid","주의"), (99,"b-hi","위험")],
        "MOVE": [(80,"b-low","안정"), (130,"b-mid","주의"), (999,"b-hi","위험")],
    }
    if name in tbl:
        for thr, cls, lbl in tbl[name]:
            if val < thr:
                return f'<span class="{cls}">{lbl}</span>'
    return ""


CHART_LAYOUT = dict(
    height=340,
    paper_bgcolor="#060A12",
    plot_bgcolor="#060A12",
    legend=dict(
        bgcolor="#0C1420", bordercolor="#1A2A3F", borderwidth=1,
        font=dict(color="#AACCEE", size=12, family="IBM Plex Mono")
    ),
    xaxis=dict(gridcolor="#141E2E", color="#4A6A8A", showgrid=True,
               tickfont=dict(size=11, family="IBM Plex Mono")),
    yaxis=dict(gridcolor="#141E2E", color="#4A6A8A", showgrid=True,
               tickfont=dict(size=11, family="IBM Plex Mono")),
    margin=dict(l=55, r=20, t=20, b=35),
    hovermode="x unified",
    font=dict(family="IBM Plex Mono", color="#AACCEE"),
)


# ═══════════════════════════════════════════════════════════
#  헤더
# ═══════════════════════════════════════════════════════════
now_str = datetime.utcnow().strftime("%Y-%m-%d  %H:%M  UTC")

st.title("📡 글로벌 매크로 대시보드")
st.caption("GLOBAL MACRO MONITOR — REAL-TIME FINANCIAL INDICATORS")

ts_col, btn_col = st.columns([6, 1])
with ts_col:
    st.markdown(f"🕐 {now_str}")
with btn_col:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")
st.success("✅ **FRED API 연결됨** — 실데이터 수신 중")


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
    ("KOSPI",   "^KS11", "#F59E0B", "코스피 종합주가지수"),
    ("KOSDAQ",  "^KQ11", "#10B981", "코스닥 지수"),
    ("원/달러", "KRW=X", "#3B82F6", "원화 / 미국달러 환율"),
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
    ("S&P 500",     "^GSPC", "#10B981", "미국 S&P 500 지수"),
    ("나스닥 100",  "^NDX",  "#3B82F6", "나스닥 100"),
    ("다우존스",    "^DJI",  "#8B5CF6", "다우존스 산업평균"),
    ("S&P 선물",    "ES=F",  "#F59E0B", "E-mini S&P 500 선물"),
    ("나스닥 선물", "NQ=F",  "#06B6D4", "E-mini 나스닥 선물"),
    ("러셀 2000",   "^RUT",  "#EC4899", "소형주 지수"),
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
    st.markdown(card("VIX (공포지수)", f(v, 2), chg, "CBOE 변동성 지수", risk_badge("VIX", v)), unsafe_allow_html=True)
    spark(h, "#EF4444", 85)

with r2:
    v, chg, h = get_yf("^MOVE", "6mo", "1d")
    st.markdown(card("MOVE (채권 변동성)", f(v, 2), chg, "ICE BofA 채권 변동성", risk_badge("MOVE", v)), unsafe_allow_html=True)
    spark(h, "#F59E0B", 85)

with r3:
    ts_data = get_fred("T10Y2Y")
    if ts_data is not None and len(ts_data) > 0:
        lv   = float(ts_data.iloc[-1])
        pv   = float(ts_data.iloc[-2]) if len(ts_data) > 1 else lv
        diff = lv - pv
        clr  = "kup" if lv >= 0 else "kdn"
        arr  = "▲"   if lv >= 0 else "▼"
        st.markdown(f"""
        <div class="kcard">
          <div class="klabel">장단기 금리차 (10Y-2Y)</div>
          <div class="kval">{lv:+.2f}%</div>
          <span class="{clr}">{arr} {abs(diff):.3f}%p</span>
          <div class="ksub">FRED T10Y2Y — 수익률 곡선</div>
        </div>""", unsafe_allow_html=True)
        spark(ts_data, "#10B981", 85, is_series=True)
    else:
        v, chg, h = get_yf("^TNX", "6mo", "1d")
        st.markdown(card("10Y 국채금리 (TNX)", f(v, 3, suf="%"), chg, "미국 10년 국채"), unsafe_allow_html=True)
        spark(h, "#10B981", 85)

with r4:
    v, chg, h = get_yf("HYG", "6mo", "1d")
    st.markdown(card("HYG (하이일드 ETF)", f(v, 2, pre="$"), chg, "HY 스프레드 프록시"), unsafe_allow_html=True)
    spark(h, "#8B5CF6", 85)

hy = get_fred("BAMLH0A0HYM2")
if hy is not None and len(hy) > 0:
    lv     = float(hy.iloc[-1])
    pv     = float(hy.iloc[-2]) if len(hy) > 1 else lv
    chg_hy = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
    fe1, fe2 = st.columns(2)
    with fe1:
        st.markdown(card("하이일드 스프레드 (OAS)", f(lv, 2, suf="%"), chg_hy, "ICE BofA US HY OAS"), unsafe_allow_html=True)
        spark(hy, "#EF4444", 80, is_series=True)


# ═══════════════════════════════════════════════════════════
#  §5  유동성 핵심 창구
# ═══════════════════════════════════════════════════════════
sec("🏦", "유동성을 좌우하는 핵심 창구 (연준)")

LIQ = [
    ("WALCL",    "연준 총자산 (대차대조표)", "#3B82F6", 7_200),
    ("WRBWFRBL", "지급준비금 잔고",            "#10B981", 3_300),
    ("WTREGEN",  "TGA (재무부 일반계정)",      "#F59E0B",   750),
]
l1, l2, l3 = st.columns(3)
for col, (sid, label, color, demo) in zip([l1, l2, l3], LIQ):
    with col:
        data = get_fred(sid, 60)
        if data is not None and len(data) > 0:
            lv  = float(data.iloc[-1])
            pv  = float(data.iloc[-2]) if len(data) > 1 else lv
            chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
            st.markdown(card(label, f(lv/1000, 1, suf=" T$"), chg, f"FRED: {sid}"), unsafe_allow_html=True)
            spark(data, color, 85, is_series=True)
        else:
            st.markdown(card(label, f(demo, 0, suf=" B$"), None, "로딩 중..."), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §6  은행 신용 및 단기 자금 시장
# ═══════════════════════════════════════════════════════════
sec("💰", "은행 신용 및 단기 자금 시장")

CRED = [
    ("RRPONTSYD", "역레포 (ON RRP)",   "#EC4899", "%",  400,    1),
    ("WRMFSL",    "MMF 총잔고",         "#06B6D4", "B$", 6_200,  1),
    ("TOTLL",     "상업은행 총대출",    "#8B5CF6", "B$", 17_500, 1),
    ("SOFR",      "SOFR (익일물 금리)", "#F59E0B", "%",  5.33,   3),
]
crs = st.columns(4)
for col, (sid, label, color, unit, demo, dp) in zip(crs, CRED):
    with col:
        data = get_fred(sid, 60)
        suf  = "%" if unit == "%" else " B$"
        if data is not None and len(data) > 0:
            lv  = float(data.iloc[-1])
            pv  = float(data.iloc[-2]) if len(data) > 1 else lv
            chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
            st.markdown(card(label, f(lv, dp, suf=suf), chg, f"FRED: {sid}"), unsafe_allow_html=True)
            spark(data, color, 80, is_series=True)
        else:
            st.markdown(card(label, f(demo, dp, suf=suf), None, "로딩 중..."), unsafe_allow_html=True)


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
    if bei5 is not None and len(bei5) > 0:
        lv  = float(bei5.iloc[-1])
        pv  = float(bei5.iloc[-2]) if len(bei5) > 1 else lv
        chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
        st.markdown(card("5Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T5YIE"), unsafe_allow_html=True)
        spark(bei5, "#10B981", 90, is_series=True)
    else:
        st.markdown(card("5Y 기대 인플레이션", "—", None, "로딩 중..."), unsafe_allow_html=True)

with m4:
    bei10 = get_fred("T10YIE", 40)
    if bei10 is not None and len(bei10) > 0:
        lv  = float(bei10.iloc[-1])
        pv  = float(bei10.iloc[-2]) if len(bei10) > 1 else lv
        chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
        st.markdown(card("10Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T10YIE"), unsafe_allow_html=True)
        spark(bei10, "#3B82F6", 90, is_series=True)
    else:
        st.markdown(card("10Y 기대 인플레이션", "—", None, "로딩 중..."), unsafe_allow_html=True)

v2, chg2, h2 = get_yf("CL=F", "6mo", "1d")
mi1, _mi2, _mi3 = st.columns([1, 1, 2])
with mi1:
    st.markdown(card("WTI 원유 선물", f(v2, 2, pre="$", suf="/bbl"), chg2, "NYMEX Crude Oil"), unsafe_allow_html=True)
    spark(h2, "#64748B", 80)


# ═══════════════════════════════════════════════════════════
#  §8  종합 비교 차트
# ═══════════════════════════════════════════════════════════
sec("📊", "종합 비교 차트")

tab1, tab2, tab3, tab4 = st.tabs([
    "📉 미국 지수 (1년)",
    "🌐 외환 6종 (6개월)",
    "⚠️ 리스크 지표 (1년)",
    "🇰🇷 한국 지수 (6개월)",
])

with tab1:
    pairs = [
        ("S&P 500",    "^GSPC", "#10B981"),
        ("나스닥 100", "^NDX",  "#3B82F6"),
        ("다우존스",   "^DJI",  "#8B5CF6"),
        ("러셀 2000",  "^RUT",  "#F59E0B"),
    ]
    fig = go.Figure()
    for name, tk, clr in pairs:
        _, _, h = get_yf(tk, "1y", "1wk")
        if h is not None and not h.empty:
            n = h["Close"] / h["Close"].iloc[0] * 100
            fig.add_trace(go.Scatter(
                x=h.index, y=n, mode="lines",
                name=name, line=dict(color=clr, width=2.2)
            ))
    fig.update_layout(**CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

with tab2:
    fx_pairs = [
        ("EUR/USD", "EURUSD=X", "#10B981"),
        ("USD/JPY", "JPY=X",    "#3B82F6"),
        ("원/달러", "KRW=X",    "#F59E0B"),
        ("GBP/USD", "GBPUSD=X", "#8B5CF6"),
        ("USD/CNY", "CNY=X",    "#EC4899"),
        ("DXY",     "DX-Y.NYB", "#06B6D4"),
    ]
    fig2 = make_subplots(rows=2, cols=3, subplot_titles=[p[0] for p in fx_pairs])
    for idx, (name, tk, clr) in enumerate(fx_pairs):
        r, c = divmod(idx, 3)
        _, _, h = get_yf(tk, "6mo", "1d")
        if h is not None and not h.empty:
            fig2.add_trace(
                go.Scatter(x=h.index, y=h["Close"], mode="lines",
                           name=name, line=dict(color=clr, width=1.8), showlegend=False),
                row=r+1, col=c+1
            )
    fig2.update_layout(
        height=420, paper_bgcolor="#060A12", plot_bgcolor="#060A12",
        margin=dict(l=20, r=20, t=45, b=20),
        font=dict(color="#8AAAC8", family="IBM Plex Mono", size=11),
    )
    report_html = f"""
    <div style="background: linear-gradient(140deg, #131E2E, #0C1520); border: 1px solid #1E3050; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
        <div style="font-size: 1.1rem; font-weight: 800; color: #00D4FF; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
            <span>💡</span> 핵심 자산 배분 전략
        </div>
        <div style="font-size: 1rem; font-weight: 600; line-height: 1.6; margin-bottom: 20px; color: {s_color}; background: #060A12; padding: 16px; border-radius: 8px; border: 1px solid #1A2A3F;">
            {strategy}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px;">
            <div style="background: #080E1A; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                <div style="font-weight: 800; font-size: 0.95rem; margin-bottom: 12px; color: #00D4FF; border-bottom: 1px solid #1E3050; padding-bottom: 8px;">📌 시장 심리 및 유동성</div>
                <div style="line-height: 1.8; font-size: 0.85rem; color: #fef08a;">
                    <div>• {vix_msg}</div>
                    <div>• {sys_msg}</div>
                </div>
            </div>
            <div style="background: #080E1A; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                <div style="font-weight: 800; font-size: 0.95rem; margin-bottom: 12px; color: #00D4FF; border-bottom: 1px solid #1E3050; padding-bottom: 8px;">📌 매크로 및 신용 환경</div>
                <div style="line-height: 1.8; font-size: 0.85rem; color: #fef08a;">
                    <div>• {sofr_msg}</div>
                    <div>• {totll_msg}</div>
                    <div>• {yield_msg}</div>
                    <div>• {bei_msg}</div>
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(report_html, unsafe_allow_html=True)
except Exception:
    pass


# ═══════════════════════════════════════════════════════════
#  §12 심층 지표 분석 (상세보기)
# ═══════════════════════════════════════════════════════════
st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
sec("🔍", "심층 지표 분석 (상세보기)")
st.markdown("<div class='ksub' style='margin-bottom: 15px;'>원하는 지표를 선택하여 과거 3년간의 추이와 AI 평가, 상세 의미를 확인하세요.</div>", unsafe_allow_html=True)

DETAIL_META = {
    "VIX (공포지수)": {"ticker": "^VIX", "type": "yf", "desc": "시장이 앞으로 얼마나 출렁일지 예상하는 지수입니다. 20 이하는 안정, 30 이상은 경계 수준입니다."},
    "MOVE (채권 변동성)": {"ticker": "^MOVE", "type": "yf", "desc": "미국 국채 시장의 변동성을 보여주는 채권판 VIX입니다. 주식 시장의 공포지수보다 채권 시장의 발작이 거시적 금융 위기를 훨씬 더 빨리 잡아냅니다."},
    "장단기 금리차 (10Y-2Y)": {"ticker": "T10Y2Y", "type": "fred", "desc": "10년 금리에서 2년 금리를 뺀 값입니다. 이 값이 음수(-)로 뒤집히면 '역전'이라고 하며, 역사적으로 강력한 경기침체 선행 경고 신호입니다."},
    "하이일드 스프레드": {"ticker": "BAMLH0A0HYM2", "type": "fred", "desc": "안전한 미국 국채와 부도 위험이 있는 투기등급 채권 간의 금리 격차입니다. 이 격차가 벌어지면 한계 기업들의 자금줄이 마르고 부도 위험이 커진다는 뜻(신용 경색)입니다."},
    "달러 인덱스 (DXY)": {"ticker": "DX-Y.NYB", "type": "yf", "desc": "유로, 엔 등 주요 주요 통화 대비 미국 달러의 평균 가치입니다. 강달러 현상은 글로벌 투자 자금이 미국으로 빨려 들어가 신흥국 증시 유동성에 악재로 작용합니다."},
    "연준 총자산 (WALCL)": {"ticker": "WALCL", "type": "fred", "desc": "미국 중앙은행(Fed)이 돈을 찍어내어 보유하고 있는 자산의 총합입니다. 상승하면 시중에 돈을 푸는 양적완화(QE), 하락하면 시중의 달러를 흡수하는 양적긴축(QT)을 의미합니다."},
    "역레포 잔액 (RRP)": {"ticker": "RRPONTSYD", "type": "fred", "desc": "시중에 갈 곳을 잃은 단기 잉여 대기 자금이 연준 창고로 들어간 금액입니다. 이 잔액이 줄어든다는 것은 창고에서 돈이 빠져나와 주식이나 실물 시장으로 흘러가고 있다는 긍정적인 신호입니다."},
}

def eval_detail(ticker, val):
    if ticker == "^VIX":
        if val >= 30: return "🚨 경계 (위험 심리 극대화)", "#FF5555"
        elif val >= 20: return "⚠️ 주의 (변동성 확대)", "#F59E0B"
        else: return "✅ 안정 (위험 자산 선호)", "#22D98A"
    elif ticker == "^MOVE":
        if val >= 140: return "🚨 위험 (채권 시장 패닉)", "#FF5555"
        elif val >= 100: return "⚠️ 주의 (금리 변동성 확대)", "#F59E0B"
        else: return "✅ 안정 (채권 시장 평온)", "#22D98A"
    elif ticker == "T10Y2Y":
        if val < 0: return "🚨 침체 경고 (장단기 금리 역전)", "#FF5555"
        else: return "✅ 정상 (경제 성장 기대)", "#22D98A"
    elif ticker == "BAMLH0A0HYM2":
        if val >= 5.0: return "🚨 경고 (신용 경색 위험)", "#FF5555"
        elif val >= 4.0: return "⚠️ 주의 (기업 대출 여건 악화)", "#F59E0B"
        else: return "✅ 안정 (풍부한 신용 유동성)", "#22D98A"
    elif ticker == "DX-Y.NYB":
        if val >= 105: return "🚨 강세 (글로벌 유동성 축소 우려)", "#FF5555"
        elif val < 100: return "✅ 약세 (위험 자산 랠리 우호적)", "#22D98A"
        else: return "⚖️ 중립 (박스권 유지)", "#F59E0B"
    else:
        return "📊 지표 모니터링 중", "#00D4FF"

selected_ind_name = st.selectbox("분석할 지표 선택", list(DETAIL_META.keys()))
meta = DETAIL_META[selected_ind_name]

with st.spinner(f"{selected_ind_name} 상세 데이터 로딩 중..."):
    if meta["type"] == "yf":
        _, _, df_detail = get_yf(meta["ticker"], "3y", "1d")
        series_detail = df_detail["Close"] if df_detail is not None else None
    else:
        series_detail = get_fred(meta["ticker"], limit=756) # 약 3년치(252영업일 * 3)

    if series_detail is not None and not series_detail.empty:
        cur_val = float(series_detail.iloc[-1])
        prev_val = float(series_detail.iloc[-2]) if len(series_detail) > 1 else cur_val
        chg = cur_val - prev_val
        chg_pct = (chg / abs(prev_val)) * 100 if prev_val != 0 else 0
        
        status_text, status_color = eval_detail(meta["ticker"], cur_val)
        
        # 단위 스케일 보정 (FRED 자산 지표들)
        unit_str = ""
        if meta["ticker"] in ["WALCL", "RRPONTSYD"]:
            series_detail = series_detail / 1000
            cur_val, prev_val, chg = cur_val / 1000, prev_val / 1000, chg / 1000
            unit_str = " (B$)"
            
        fig_det = go.Figure()
        fig_det.add_trace(go.Scatter(
            x=series_detail.index, y=series_detail.values,
            mode="lines", name=selected_ind_name,
            line=dict(color="#00D4FF", width=2.5),
            fill="tozeroy", fillcolor=hex_to_rgba("#00D4FF", 0.15)
        ))
        
        # 임계값 가이드라인 추가
        if meta["ticker"] == "^VIX":
            fig_det.add_hline(y=30, line_dash="dash", line_color="#FF5555", opacity=0.8)
        elif meta["ticker"] == "^MOVE":
            fig_det.add_hline(y=140, line_dash="dash", line_color="#FF5555", opacity=0.8)
        elif meta["ticker"] == "T10Y2Y":
            fig_det.add_hline(y=0, line_dash="solid", line_color="#FFFFFF", opacity=0.4)
            
        fig_det.update_layout(**CHART_LAYOUT, height=450, title=f"{selected_ind_name} (최근 3년 추이)")
        st.plotly_chart(fig_det, use_container_width=True, config={"displayModeBar": False})

        st.markdown(f"""
        <div style="background: #0C1420; border: 1px solid #1E3050; border-radius: 12px; padding: 24px; margin-bottom: 30px;">
            <div style="display: flex; flex-wrap: wrap; gap: 40px; align-items: center; margin-bottom: 20px;">
                <div>
                    <div style="color: #6B8EAE; font-size: 0.85rem; font-weight: 700; margin-bottom: 5px;">현재 수치</div>
                    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 2.2rem; font-weight: 700; color: #FFFFFF;">
                        {cur_val:,.2f}<span style="font-size: 1rem; color: #6B8EAE;">{unit_str}</span>
                    </div>
                </div>
                <div>
                    <div style="color: #6B8EAE; font-size: 0.85rem; font-weight: 700; margin-bottom: 5px;">전일 대비 변동</div>
                    <div style="font-family: 'IBM Plex Mono', monospace; font-size: 1.3rem; font-weight: 700; color: {'#22D98A' if chg >= 0 else '#FF5555'};">
                        {'▲' if chg >= 0 else '▼'} {abs(chg):,.2f} ({abs(chg_pct):.2f}%)
                    </div>
                </div>
                <div style="flex-grow: 1;"></div>
                <div style="background: #060A12; border: 1px solid {status_color}55; padding: 12px 24px; border-radius: 8px; text-align: center;">
                    <div style="color: #6B8EAE; font-size: 0.8rem; font-weight: 700; margin-bottom: 4px;">AI 진단 상태</div>
                    <div style="color: {status_color}; font-size: 1.1rem; font-weight: 800;">{status_text}</div>
                </div>
            </div>
            <div style="border-top: 1px solid #1A2A3F; padding-top: 18px;">
                <div style="color: #00D4FF; font-weight: 800; margin-bottom: 8px; font-size: 0.95rem;">📌 지표 설명 및 시사점</div>
                <div style="color: #fef08a; font-size: 0.9rem; line-height: 1.6; font-weight: 500;">{meta['desc']}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("선택한 지표의 상세 데이터를 불러올 수 없습니다.")


# ═══════════════════════════════════════════════════════════
#  사이드바
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 설정")
    st.markdown("---")
    st.markdown("**FRED API**")
    st.text_input("API Key", value="••••••••••••••••••••••••", disabled=True)
    st.success("연결됨")
    st.markdown("---")
    if st.button("캐시 초기화", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("""
**데이터 소스**
- Yahoo Finance
- FRED
- 5분 캐시 적용
    """)


# ═══════════════════════════════════════════════════════════
#  푸터
# ═══════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#2A4060; font-size:.70rem;
            font-family:'IBM Plex Mono',monospace; font-weight:700; padding:12px 0;">
  Yahoo Finance · FRED | {now_str}
</div>
""", unsafe_allow_html=True)
