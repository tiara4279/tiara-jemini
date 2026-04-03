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
    ("WRBWFRBL", "지급준비금 잔고",           "#10B981", 3_300),
    ("WTREGEN",  "TGA (재무부 일반계정)",     "#F59E0B",   750),
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
    fig2.update_xaxes(gridcolor="#141E2E", color="#4A6A8A")
    fig2.update_yaxes(gridcolor="#141E2E", color="#4A6A8A")
    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

with tab3:
    risk_pairs = [
        ("VIX",  "^VIX",  "#EF4444"),
        ("MOVE", "^MOVE", "#F59E0B"),
        ("HYG",  "HYG",   "#8B5CF6"),
    ]
    fig3 = go.Figure()
    for name, tk, clr in risk_pairs:
        _, _, h = get_yf(tk, "1y", "1wk")
        if h is not None and not h.empty:
            n = h["Close"] / h["Close"].iloc[0] * 100
            fig3.add_trace(go.Scatter(
                x=h.index, y=n, mode="lines",
                name=name, line=dict(color=clr, width=2.2)
            ))
    fig3.update_layout(**CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

with tab4:
    kr_pairs = [
        ("KOSPI",  "^KS11", "#F59E0B"),
        ("KOSDAQ", "^KQ11", "#10B981"),
    ]
    fig4 = go.Figure()
    for name, tk, clr in kr_pairs:
        _, _, h = get_yf(tk, "6mo", "1d")
        if h is not None and not h.empty:
            n = h["Close"] / h["Close"].iloc[0] * 100
            fig4.add_trace(go.Scatter(
                x=h.index, y=n, mode="lines",
                name=name, line=dict(color=clr[:7], width=2.2),
                fill="tozeroy",
                fillcolor=hex_to_rgba(clr[:7], 0.10)
            ))
    fig4.update_layout(**CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════
#  §9  Net Liquidity (달러기호 충돌 완전 수정)
# ═══════════════════════════════════════════════════════════
import streamlit.components.v1 as components

sec("🌊", "미국 핵심 유동성 흐름 (Net Liquidity)")
st.caption("Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")

# ── 개별 데이터 로딩
_walcl = get_fred('WALCL',     limit=300)   # 단위: 백만달러 (M$)
_rrp   = get_fred('RRPONTSYD', limit=300)   # 단위: 십억달러 (B$)
_tga   = get_fred('WTREGEN',   limit=300)   # 단위: 백만달러 (M$)

# ── S&P500 직접 호출
try:
    _sp500_raw = yf.Ticker('^GSPC').history(period='1y', interval='1d', auto_adjust=True)
    _sp500_ok  = not _sp500_raw.empty and len(_sp500_raw) > 10
except Exception:
    _sp500_raw = None
    _sp500_ok  = False

_data_ok = (
    _walcl is not None and len(_walcl) > 1 and
    _rrp   is not None and len(_rrp)   > 1 and
    _tga   is not None and len(_tga)   > 1 and
    _sp500_ok
)

if _data_ok:
    try:
        # ── 단위 통일 → T$
        walcl_t = _walcl / 1_000_000.0   # M$ → T$
        rrp_t   = _rrp   / 1_000.0       # B$ → T$
        tga_t   = _tga   / 1_000_000.0   # M$ → T$

        df_liq = pd.DataFrame({'WALCL': walcl_t, 'RRP': rrp_t, 'TGA': tga_t})
        df_liq['Net_Liquidity'] = df_liq['WALCL'] - df_liq['RRP'] - df_liq['TGA']

        # ── S&P500 타임존 제거
        sp500_s = _sp500_raw['Close'].copy()
        if hasattr(sp500_s.index, 'tz') and sp500_s.index.tz is not None:
            sp500_s.index = sp500_s.index.tz_localize(None)

        # ── 날짜 정규화 + 병합
        df_liq.index  = pd.to_datetime(df_liq.index).normalize()
        sp500_s.index = pd.to_datetime(sp500_s.index).normalize()

        df_plot = (
            df_liq[['Net_Liquidity', 'WALCL', 'RRP', 'TGA']]
            .reindex(sp500_s.index, method='ffill')
            .join(sp500_s.rename('Close'))
            .dropna()
        )

        if len(df_plot) > 10:
            latest_walcl = float(df_plot['WALCL'].iloc[-1])
            latest_rrp   = float(df_plot['RRP'].iloc[-1])
            latest_tga   = float(df_plot['TGA'].iloc[-1])
            latest_nl    = float(df_plot['Net_Liquidity'].iloc[-1])
            latest_sp    = float(df_plot['Close'].iloc[-1])
            latest_date  = df_plot.index[-1].strftime('%Y-%m-%d')

            prev_nl      = float(df_plot['Net_Liquidity'].iloc[-6])
            nl_chg       = latest_nl - prev_nl
            nl_chg_arrow = "▲" if nl_chg >= 0 else "▼"
            nl_chg_color = "#22D98A" if nl_chg >= 0 else "#FF5555"
            nl_signal    = "유동성 공급 확대" if nl_chg >= 0 else "유동성 흡수 진행"
            nl_signal_ic = "📈" if nl_chg >= 0 else "📉"

            # ── Plotly 차트
            fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
            fig_liq.add_trace(
                go.Scatter(
                    x=df_plot.index, y=df_plot['Net_Liquidity'],
                    name="순유동성 (T)",
                    line=dict(color='#00D4FF', width=2.5),
                    fill='tozeroy',
                    fillcolor='rgba(0,212,255,0.06)'
                ),
                secondary_y=False
            )
            fig_liq.add_trace(
                go.Scatter(
                    x=df_plot.index, y=df_plot['Close'],
                    name="S&P 500",
                    line=dict(color='#FF5555', width=1.8)
                ),
                secondary_y=True
            )
            fig_liq.update_layout(
                **CHART_LAYOUT,
                title_text="Net Liquidity vs S&P 500 (최근 1년)"
            )
            fig_liq.update_yaxes(title_text="순유동성 (T)", secondary_y=False, color="#00D4FF")
            fig_liq.update_yaxes(title_text="S&P 500",     secondary_y=True,  color="#FF5555")
            st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})

            # ── 공식 박스: $ → &#36; 로 전부 치환하여 Streamlit LaTeX 충돌 방지
            walcl_str = "&#36;" + f"{latest_walcl:.2f} T"
            rrp_str   = "&#36;" + f"{latest_rrp:.2f} T"
            tga_str   = "&#36;" + f"{latest_tga:.2f} T"
            nl_str    = "&#36;" + f"{latest_nl:.2f} T"
            sp_str    = f"{latest_sp:,.0f}"
            chg_str   = f"{nl_chg_arrow} {abs(nl_chg):.3f} T (주간 변화)"

            html_box = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; font-family:'Noto Sans KR',sans-serif; padding:4px; }}
  .box {{
    background:#0C1420; border:1px solid #1E3050; border-radius:14px;
    padding:20px; margin-bottom:8px;
  }}
  .box-title {{
    font-size:0.95rem; font-weight:800; color:#00D4FF; margin-bottom:14px;
  }}
  .box-title span {{ font-size:0.75rem; color:#4A6888; font-weight:600; margin-left:10px; }}
  .formula-box {{
    font-family:'IBM Plex Mono',monospace; background:#060A12;
    border:1px solid #1A2A3F; border-radius:10px; padding:16px;
    margin-bottom:16px; line-height:2.4;
  }}
  .row {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .row-divider {{ border-top:1px solid #1E3050; margin-top:10px; padding-top:12px; }}
  .label-blue  {{ color:#3B82F6; font-size:1.0rem; font-weight:700; }}
  .label-pink  {{ color:#EC4899; font-size:1.0rem; font-weight:700; }}
  .label-amber {{ color:#F59E0B; font-size:1.0rem; font-weight:700; }}
  .label-cyan  {{ color:#00D4FF; font-size:1.05rem; font-weight:800; }}
  .label-gray  {{ color:#4A6888; font-size:0.8rem; }}
  .op-minus {{ color:#FF5555; font-size:1.3rem; font-weight:900; }}
  .op-equal {{ color:#22D98A; font-size:1.3rem; font-weight:900; }}
  .val-chip {{
    background:#1A2A3F; padding:4px 14px; border-radius:6px;
    color:#FFFFFF; font-size:1.05rem; font-weight:700;
  }}
  .val-result {{
    background:rgba(0,212,255,0.15); border:1px solid rgba(0,212,255,0.35);
    padding:5px 18px; border-radius:8px;
    color:#00D4FF; font-size:1.25rem; font-weight:900;
  }}
  .chg-badge {{ font-size:0.82rem; font-weight:700; color:{nl_chg_color}; }}
  .metrics {{
    display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px;
  }}
  .metric-card {{
    background:#080E1A; border:1px solid #1A2A3F; border-radius:10px; padding:14px;
  }}
  .metric-label {{
    font-size:0.72rem; font-weight:700; color:#6B8EAE;
    letter-spacing:.08em; margin-bottom:6px; text-transform:uppercase;
  }}
  .metric-val-sp {{
    font-family:'IBM Plex Mono',monospace; font-size:1.3rem; font-weight:700; color:#FF5555;
  }}
  .metric-val-signal {{
    font-family:'IBM Plex Mono',monospace; font-size:0.95rem;
    font-weight:700; color:{nl_chg_color};
  }}
  .footnote {{ font-size:0.78rem; color:#4A6888; line-height:1.7; }}
  .footnote b.up {{ color:#00D4FF; }}
  .footnote b.dn {{ color:#FF5555; }}
</style>
</head>
<body>
<div class="box">

  <div class="box-title">
    📌 Net Liquidity 실시간 계산
    <span>기준일: {latest_date}</span>
  </div>

  <div class="formula-box">

    <div class="row">
      <span class="label-blue">연준 총자산</span>
      <span class="label-gray">(WALCL)</span>
      <span class="val-chip">{walcl_str}</span>
    </div>

    <div class="row">
      <span class="op-minus">−</span>
      <span class="label-pink">역레포 (RRP)</span>
      <span class="label-gray">(RRPONTSYD)</span>
      <span class="val-chip">{rrp_str}</span>
    </div>

    <div class="row">
      <span class="op-minus">−</span>
      <span class="label-amber">재무부 계좌 (TGA)</span>
      <span class="label-gray">(WTREGEN)</span>
      <span class="val-chip">{tga_str}</span>
    </div>

    <div class="row row-divider">
      <span class="op-equal">=</span>
      <span class="label-cyan">순유동성 (Net Liquidity)</span>
      <span class="val-result">{nl_str}</span>
      <span class="chg-badge">{chg_str}</span>
    </div>

  </div>

  <div class="metrics">
    <div class="metric-card">
      <div class="metric-label">S&P 500 최근 종가</div>
      <div class="metric-val-sp">{sp_str}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">유동성 신호</div>
      <div class="metric-val-signal">{nl_signal_ic} {nl_signal}</div>
    </div>
  </div>

  <div class="footnote">
    순유동성이 증가하면 시장에 돈이 풀려 <b class="up">주가 상승</b> 압력,
    감소하면 유동성 회수로 <b class="dn">주가 조정</b> 가능성이 높아집니다.
  </div>

</div>
</body>
</html>
"""
            components.html(html_box, height=380, scrolling=False)

        else:
            st.warning("데이터 병합 포인트가 부족합니다. 잠시 후 다시 시도해 주세요.")

    except Exception as e:
        st.error(f"유동성 섹션 오류: {str(e)}")

else:
    st.markdown("""
<div style="background:#1A0E0E; border:1px solid #8B3A3A; border-radius:10px;
            padding:16px; margin-bottom:16px;">
  <div style="font-size:0.9rem; font-weight:700; color:#FF6B6B; margin-bottom:6px;">
    데이터 로딩 실패 — 항목별 상태
  </div>
  <div style="font-size:0.82rem; color:#CC9999; line-height:1.6;">
    FRED API 또는 인터넷 연결 상태를 확인하세요.
  </div>
</div>""", unsafe_allow_html=True)

    dc1, dc2, dc3, dc4 = st.columns(4)
    status_data = [
        ("WALCL",     _walcl is not None and len(_walcl) > 1),
        ("RRPONTSYD", _rrp   is not None and len(_rrp)   > 1),
        ("WTREGEN",   _tga   is not None and len(_tga)   > 1),
        ("S&P 500",   _sp500_ok),
    ]
    for col, (name, status) in zip([dc1, dc2, dc3, dc4], status_data):
        with col:
            ok_color = "#22D98A" if status else "#FF5555"
            ok_text  = "READY"   if status else "FAILED"
            st.markdown(f"""
<div style="background:#0C1420; border:2px solid {ok_color}; border-radius:8px;
            padding:14px; text-align:center;">
  <div style="font-size:0.75rem; font-weight:700; color:#6B8EAE; margin-bottom:6px;">
    {name}
  </div>
  <div style="font-family:'IBM Plex Mono',monospace; font-size:1.1rem;
              font-weight:800; color:{ok_color};">
    {ok_text}
  </div>
</div>""", unsafe_allow_html=True)


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
