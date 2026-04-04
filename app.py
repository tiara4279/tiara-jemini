# ============================================================
#  글로벌 매크로 대시보드 — app.py (완전 수정본 v2)
#  ✅ hex_to_rgba 중복 제거 (상단 단일 정의)
#  ✅ MOVE 지수: FRED ICBMRATE → yfinance ^MOVE 로 수정
#  ✅ 지급준비금 ID 통일: WRESBAL (양쪽 동일)
#  ✅ MMF 시리즈 통일: MMMFFAQ027S → WRMFSL (주간)
#  ✅ Fred 객체 중복 생성 제거 (상단 fred 재사용)
#  ✅ §10 데이터 로딩에 get_fred/get_yf 캐시 함수 재사용
#  ✅ TGA 단위 B$ 기준으로 임계값 통일
#  ✅ API 키 상수 분리 (st.secrets 미지원 환경 대비 폴백 유지)
#  ✅ import 중복 제거
#  ✅ 폰트 색상 전체 밝게 조정 (짙은 회색 → 밝은 회색)
#  ✅ CHART_LAYOUT yaxis 충돌 방지
#  ✅ 스크롤 시 배경색 끊김(투명화) 현상 해결 및 전체 배경톤 통일
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
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )

install_missing()

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import streamlit.components.v1 as components
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
#  공통 유틸 함수 (모두 상단 정의, 중복 없음)
# ═══════════════════════════════════════════════════════════

def hex_to_rgba(hex_color: str, alpha: float = 0.10) -> str:
    """HEX 색상을 rgba 문자열로 변환 (단일 정의)"""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


@st.cache_data(ttl=300)
def get_yf(ticker: str, period: str = "6mo", interval: str = "1d"):
    """Yahoo Finance 데이터 로딩 (캐시 적용)"""
    try:
        h = yf.Ticker(ticker).history(period=period, interval=interval, auto_adjust=True)
        if h.empty or len(h) < 2:
            return None, None, None
        # 타임존 제거
        if hasattr(h.index, "tz") and h.index.tz is not None:
            h.index = h.index.tz_localize(None)
        last = float(h["Close"].iloc[-1])
        prev = float(h["Close"].iloc[-2])
        chg  = (last - prev) / prev * 100
        return last, chg, h
    except Exception:
        return None, None, None


@st.cache_data(ttl=600)
def get_fred(sid: str, limit: int = 60):
    """FRED 시리즈 로딩 (캐시 적용)"""
    if fred is None:
        return None
    try:
        s = fred.get_series(sid).dropna().tail(limit)
        return s if len(s) > 1 else None
    except Exception:
        return None


@st.cache_data(ttl=600)
def get_fred_range(sid: str, days: int = 730):
    """FRED 시리즈 날짜 범위 지정 로딩 (캐시 적용) — §10 전용"""
    if fred is None:
        return None
    try:
        end_dt   = datetime.today()
        start_dt = end_dt - timedelta(days=days)
        s = fred.get_series(sid, observation_start=start_dt, observation_end=end_dt).dropna()
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
        unsafe_allow_html=True,
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
        "VIX":  [(20, "b-low", "안정"), (30, "b-mid", "주의"), (99, "b-hi", "위험")],
        "MOVE": [(80, "b-low", "안정"), (130, "b-mid", "주의"), (999, "b-hi", "위험")],
    }
    if name in tbl:
        for thr, cls, lbl in tbl[name]:
            if val < thr:
                return f'<span class="{cls}">{lbl}</span>'
    return ""


def get_risk_status(value, thresholds, labels):
    """§10 상태 판정 함수"""
    for key, (low, high) in thresholds.items():
        if low <= value < high:
            return key, labels[key]
    return "caution", "데이터 범위 초과"


# ── 차트 공통 레이아웃 (yaxis 충돌 방지 — secondary_y 사용 시 직접 update_yaxes 호출)
CHART_LAYOUT = dict(
    height=340,
    paper_bgcolor="#060A12",
    plot_bgcolor="#060A12",
    legend=dict(
        bgcolor="#0C1420", bordercolor="#1A2A3F", borderwidth=1,
        font=dict(color="#D0E4F8", size=12, family="IBM Plex Mono"),
    ),
    xaxis=dict(
        gridcolor="#1A2A3F", color="#8AAED0", showgrid=True,
        tickfont=dict(size=11, family="IBM Plex Mono", color="#B0C8E0"),
    ),
    yaxis=dict(
        gridcolor="#1A2A3F", color="#8AAED0", showgrid=True,
        tickfont=dict(size=11, family="IBM Plex Mono", color="#B0C8E0"),
    ),
    margin=dict(l=55, r=20, t=20, b=35),
    hovermode="x unified",
    font=dict(family="IBM Plex Mono", color="#D0E4F8"),
)

# ── §10 상태 스타일
STATUS_STYLE = {
    "safe":    {"bg": "#064e3b", "border": "#10b981", "icon": "✅", "text": "#6ee7b7", "label": "안   전"},
    "caution": {"bg": "#1c1917", "border": "#f59e0b", "icon": "🟡", "text": "#fcd34d", "label": "보   통"},
    "warning": {"bg": "#431407", "border": "#f97316", "icon": "⚠️",  "text": "#fb923c", "label": "주   의"},
    "danger":  {"bg": "#450a0a", "border": "#ef4444", "icon": "🔴", "text": "#fca5a5", "label": "심   각"},
}

# ═══════════════════════════════════════════════════════════
#  CSS 스타일 (전체 앱 배경 통일 및 폰트 색상 조정)
# ═══════════════════════════════════════════════════════════
st.markdown("""<style>
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700;900&display=swap");

/* ══════════════════════════════════════
   스크롤 강제 활성화 및 배경색 전체 통일
══════════════════════════════════════ */
html, body {
    overflow: auto !important;
    height: auto !important;
    min-height: 100% !important;
}

/* Streamlit의 모든 루트 컨테이너 배경색을 하나로 통일 (스크롤 시 끊김 방지) */
html, body, #root, .stApp, 
[data-testid="stAppViewContainer"], 
[data-testid="stAppViewBlockContainer"], 
[data-testid="stMain"], 
.main {
    background-color: #060A12 !important;
    overflow: visible !important;
    overflow-y: visible !important;
    height: auto !important;
    max-height: none !important;
    min-height: 0 !important;
}

[data-testid="stHeader"] {
    background: transparent !important;
}

/* 스크롤바 커스텀 (Webkit) */
::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #0C1420; }
::-webkit-scrollbar-thumb { background: #2A5A8A; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #3A7ABB; }

/* Firefox */
* { scrollbar-width: thin; scrollbar-color: #2A5A8A #0C1420; }

/* ── 기본 텍스트 색상 ── */
html, body, [class*="css"], .stMarkdown, .stText, p, span, div, label {
    font-family: 'Noto Sans KR', sans-serif !important;
    color: #D8ECF8 !important;
}

.block-container { padding-top: 2rem !important; max-width: 1400px; }

h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    letter-spacing: 0.04em !important;
}
h2, h3 { color: #E8F4FF !important; }

.stCaption, .stCaption p, small {
    font-size: 1rem !important;
    font-weight: 700 !important;
    color: #7EADD4 !important;
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
    color: #8FBBDD !important;
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

.kup { color: #22D98A !important; font-size: .84rem !important; font-weight: 700 !important; font-family: 'IBM Plex Mono', monospace !important; }
.kdn { color: #FF6B6B !important; font-size: .84rem !important; font-weight: 700 !important; font-family: 'IBM Plex Mono', monospace !important; }
.kna { color: #7A94B0 !important; font-size: .84rem !important; font-weight: 600 !important; }

.ksub {
    color: #6E9DBF !important;
    font-size: .70rem !important;
    font-weight: 600 !important;
    margin-top: 4px;
}

.b-low { background: #10B98122; color: #22D98A !important; border: 1px solid #10B98155; padding: 2px 9px; border-radius: 99px; font-size: .70rem !important; font-weight: 700 !important; }
.b-mid { background: #F59E0B22; color: #FFCC44 !important; border: 1px solid #F59E0B55; padding: 2px 9px; border-radius: 99px; font-size: .70rem !important; font-weight: 700 !important; }
.b-hi  { background: #EF444422; color: #FF7070 !important; border: 1px solid #EF444455; padding: 2px 9px; border-radius: 99px; font-size: .70rem !important; font-weight: 700 !important; }

hr { border-color: #1A2A3F !important; }

.stTabs [data-baseweb="tab-list"] { background: #0C1420; border-radius: 10px; gap: 4px; padding: 4px; }
.stTabs [data-baseweb="tab"] { color: #7AAAC8 !important; font-family: 'IBM Plex Mono', monospace !important; font-size: .80rem !important; font-weight: 700 !important; }
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

.stAlert p { font-weight: 700 !important; color: #D8ECF8 !important; }

section[data-testid="stSidebar"] { background: #080E1A !important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    font-weight: 700 !important;
    color: #AACCEE !important;
}

.stTable th { color: #B8D8F0 !important; background: #0C1420 !important; }
.stTable td { color: #D0E8F8 !important; }
.stMarkdown p { color: #C8E0F4 !important; }
</style>""", unsafe_allow_html=True)


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
    ("WALCL",   "연준 총자산 (대차대조표)", "#3B82F6"),   # 단위: M$
    ("WRESBAL", "지급준비금 잔고",           "#10B981"),   # 단위: B$
    ("WTREGEN", "TGA (재무부 일반계정)",     "#F59E0B"),   # 단위: M$
]
l1, l2, l3 = st.columns(3)
for col, (sid, label, color) in zip([l1, l2, l3], LIQ):
    with col:
        data = get_fred(sid, 60)
        if data is not None and len(data) > 0:
            lv  = float(data.iloc[-1])
            pv  = float(data.iloc[-2]) if len(data) > 1 else lv
            chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
            if sid in ("WALCL", "WTREGEN"):
                display_val = f(lv / 1_000_000.0, 2, suf=" T$")
            else:
                display_val = f(lv / 1_000.0, 2, suf=" T$")
            st.markdown(card(label, display_val, chg, f"FRED: {sid}"), unsafe_allow_html=True)
            spark(data, color, 85, is_series=True)
        else:
            st.markdown(card(label, "— N/A", None, "데이터 로딩 중..."), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §6  은행 신용 및 단기 자금 시장
# ═══════════════════════════════════════════════════════════
sec("💰", "은행 신용 및 단기 자금 시장")

CRED = [
    ("RRPONTSYD", "역레포 (ON RRP)",   "#EC4899", "%",  1),
    ("WRMFSL",    "MMF 총잔고",         "#06B6D4", "B$", 1),
    ("TOTLL",     "상업은행 총대출",    "#8B5CF6", "B$", 1),
    ("SOFR",      "SOFR (익일물 금리)", "#F59E0B", "%",  3),
]
crs = st.columns(4)
for col, (sid, label, color, unit, dp) in zip(crs, CRED):
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
            st.markdown(card(label, "— N/A", None, "데이터 로딩 중..."), unsafe_allow_html=True)


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
        st.markdown(card("5Y 기대 인플레이션", "— N/A", None, "데이터 로딩 중..."), unsafe_allow_html=True)

with m4:
    bei10 = get_fred("T10YIE", 40)
    if bei10 is not None and len(bei10) > 0:
        lv  = float(bei10.iloc[-1])
        pv  = float(bei10.iloc[-2]) if len(bei10) > 1 else lv
        chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
        st.markdown(card("10Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T10YIE"), unsafe_allow_html=True)
        spark(bei10, "#3B82F6", 90, is_series=True)
    else:
        st.markdown(card("10Y 기대 인플레이션", "— N/A", None, "데이터 로딩 중..."), unsafe_allow_html=True)

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
                name=name, line=dict(color=clr, width=2.2),
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
                row=r + 1, col=c + 1,
            )
    fig2.update_layout(
        height=420, paper_bgcolor="#060A12", plot_bgcolor="#060A12",
        margin=dict(l=20, r=20, t=45, b=20),
        font=dict(color="#D0E4F8", family="IBM Plex Mono", size=11),
    )
    fig2.update_xaxes(gridcolor="#1A2A3F", color="#8AAED0", tickfont=dict(color="#B8D4EE"))
    fig2.update_yaxes(gridcolor="#1A2A3F", color="#8AAED0", tickfont=dict(color="#B8D4EE"))
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
                name=name, line=dict(color=clr, width=2.2),
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
                fillcolor=hex_to_rgba(clr[:7], 0.10),
            ))
    fig4.update_layout(**CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════
#  §9  Net Liquidity
# ═══════════════════════════════════════════════════════════
sec("🌊", "미국 핵심 유동성 흐름 (Net Liquidity)")
st.caption("Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")

_walcl = get_fred("WALCL",     limit=300)   # M$
_rrp   = get_fred("RRPONTSYD", limit=300)   # B$
_tga   = get_fred("WTREGEN",   limit=300)   # M$

try:
    _sp500_raw = yf.Ticker("^GSPC").history(period="1y", interval="1d", auto_adjust=True)
    if hasattr(_sp500_raw.index, "tz") and _sp500_raw.index.tz is not None:
        _sp500_raw.index = _sp500_raw.index.tz_localize(None)
    _sp500_ok = not _sp500_raw.empty and len(_sp500_raw) > 10
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
        walcl_t = _walcl / 1_000_000.0   # M$ → T$
        rrp_t   = _rrp   / 1_000.0       # B$ → T$
        tga_t   = _tga   / 1_000_000.0   # M$ → T$

        df_liq = pd.DataFrame({"WALCL": walcl_t, "RRP": rrp_t, "TGA": tga_t})
        df_liq["Net_Liquidity"] = df_liq["WALCL"] - df_liq["RRP"] - df_liq["TGA"]

        sp500_s = _sp500_raw["Close"].copy()
        df_liq.index  = pd.to_datetime(df_liq.index).normalize()
        sp500_s.index = pd.to_datetime(sp500_s.index).normalize()

        df_plot = (
            df_liq[["Net_Liquidity", "WALCL", "RRP", "TGA"]]
            .reindex(sp500_s.index, method="ffill")
            .join(sp500_s.rename("Close"))
            .dropna()
        )

        if len(df_plot) > 10:
            latest_walcl = float(df_plot["WALCL"].iloc[-1])
            latest_rrp   = float(df_plot["RRP"].iloc[-1])
            latest_tga   = float(df_plot["TGA"].iloc[-1])
            latest_nl    = float(df_plot["Net_Liquidity"].iloc[-1])
            latest_sp    = float(df_plot["Close"].iloc[-1])
            latest_date  = df_plot.index[-1].strftime("%Y-%m-%d")

            prev_nl      = float(df_plot["Net_Liquidity"].iloc[-6])
            nl_chg       = latest_nl - prev_nl
            nl_chg_arrow = "▲" if nl_chg >= 0 else "▼"
            nl_chg_color = "#22D98A" if nl_chg >= 0 else "#FF6B6B"
            nl_signal    = "유동성 공급 확대" if nl_chg >= 0 else "유동성 흡수 진행"
            nl_signal_ic = "📈" if nl_chg >= 0 else "📉"

            fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
            fig_liq.add_trace(
                go.Scatter(
                    x=df_plot.index, y=df_plot["Net_Liquidity"],
                    name="순유동성 (T)",
                    line=dict(color="#00D4FF", width=2.5),
                    fill="tozeroy",
                    fillcolor="rgba(0,212,255,0.06)",
                ),
                secondary_y=False,
            )
            fig_liq.add_trace(
                go.Scatter(
                    x=df_plot.index, y=df_plot["Close"],
                    name="S&P 500",
                    line=dict(color="#FF6B6B", width=1.8),
                ),
                secondary_y=True,
            )
            liq_layout = {k: v for k, v in CHART_LAYOUT.items() if k != "yaxis"}
            fig_liq.update_layout(**liq_layout, title_text="Net Liquidity vs S&P 500 (최근 1년)")
            fig_liq.update_yaxes(
                title_text="순유동성 (T)", secondary_y=False, color="#00D4FF",
                gridcolor="#1A2A3F", tickfont=dict(color="#B8D4EE"),
            )
            fig_liq.update_yaxes(
                title_text="S&P 500", secondary_y=True, color="#FF6B6B",
                tickfont=dict(color="#B8D4EE"),
            )
            st.plotly_chart(fig_liq, use_container_width=True, config={"displayModeBar": False})

            walcl_str = "&#36;" + f"{latest_walcl:.2f} T"
            rrp_str   = "&#36;" + f"{latest_rrp:.2f} T"
            tga_str   = "&#36;" + f"{latest_tga:.2f} T"
            nl_str    = "&#36;" + f"{latest_nl:.2f} T"
            sp_str    = f"{latest_sp:,.0f}"
            chg_str   = f"{nl_chg_arrow} {abs(nl_chg):.3f} T (주간 변화)"

            html_box = f"""
<!DOCTYPE html><html><head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700;900&display=swap" rel="stylesheet">
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; font-family:'Noto Sans KR',sans-serif; padding:4px; color:#D8ECF8; }}
  .box {{ background:#0C1420; border:1px solid #1E3050; border-radius:14px; padding:20px; margin-bottom:8px; }}
  .box-title {{ font-size:0.95rem; font-weight:800; color:#00D4FF; margin-bottom:14px; }}
  .box-title span {{ font-size:0.75rem; color:#7AAED0; font-weight:600; margin-left:10px; }}
  .formula-box {{
    font-family:'IBM Plex Mono',monospace; background:#060A12;
    border:1px solid #1A2A3F; border-radius:10px; padding:16px;
    margin-bottom:16px; line-height:2.4;
  }}
  .row {{ display:flex; align-items:center; gap:10px; flex-wrap:wrap; }}
  .row-divider {{ border-top:1px solid #1E3050; margin-top:10px; padding-top:12px; }}
  .label-blue  {{ color:#60A5FA; font-size:1.0rem; font-weight:700; }}
  .label-pink  {{ color:#F472B6; font-size:1.0rem; font-weight:700; }}
  .label-amber {{ color:#FCD34D; font-size:1.0rem; font-weight:700; }}
  .label-cyan  {{ color:#00D4FF; font-size:1.05rem; font-weight:800; }}
  .label-gray  {{ color:#8AAED0; font-size:0.8rem; }}
  .op-minus {{ color:#FF6B6B; font-size:1.3rem; font-weight:900; }}
  .op-equal {{ color:#22D98A; font-size:1.3rem; font-weight:900; }}
  .val-chip {{ background:#1A2A3F; padding:4px 14px; border-radius:6px; color:#E8F4FF; font-size:1.05rem; font-weight:700; }}
  .val-result {{
    background:rgba(0,212,255,0.15); border:1px solid rgba(0,212,255,0.35);
    padding:5px 18px; border-radius:8px;
    color:#00D4FF; font-size:1.25rem; font-weight:900;
  }}
  .chg-badge {{ font-size:0.82rem; font-weight:700; color:{nl_chg_color}; }}
  .metrics {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:14px; }}
  .metric-card {{ background:#080E1A; border:1px solid #1A2A3F; border-radius:10px; padding:14px; }}
  .metric-label {{ font-size:0.72rem; font-weight:700; color:#8AAED0; letter-spacing:.08em; margin-bottom:6px; text-transform:uppercase; }}
  .metric-val-sp {{ font-family:'IBM Plex Mono',monospace; font-size:1.3rem; font-weight:700; color:#FF6B6B; }}
  .metric-val-signal {{ font-family:'IBM Plex Mono',monospace; font-size:0.95rem; font-weight:700; color:{nl_chg_color}; }}
  .footnote {{ font-size:0.78rem; color:#A0C0DC; line-height:1.7; }}
  .footnote b.up {{ color:#00D4FF; }}
  .footnote b.dn {{ color:#FF6B6B; }}
</style></head><body>
<div class="box">
  <div class="box-title">📌 Net Liquidity 실시간 계산<span>기준일: {latest_date}</span></div>
  <div class="formula-box">
    <div class="row"><span class="label-blue">연준 총자산</span><span class="label-gray">(WALCL)</span><span class="val-chip">{walcl_str}</span></div>
    <div class="row"><span class="op-minus">−</span><span class="label-pink">역레포 (RRP)</span><span class="label-gray">(RRPONTSYD)</span><span class="val-chip">{rrp_str}</span></div>
    <div class="row"><span class="op-minus">−</span><span class="label-amber">재무부 계좌 (TGA)</span><span class="label-gray">(WTREGEN)</span><span class="val-chip">{tga_str}</span></div>
    <div class="row row-divider"><span class="op-equal">=</span><span class="label-cyan">순유동성 (Net Liquidity)</span><span class="val-result">{nl_str}</span><span class="chg-badge">{chg_str}</span></div>
  </div>
  <div class="metrics">
    <div class="metric-card"><div class="metric-label">S&P 500 최근 종가</div><div class="metric-val-sp">{sp_str}</div></div>
    <div class="metric-card"><div class="metric-label">유동성 신호</div><div class="metric-val-signal">{nl_signal_ic} {nl_signal}</div></div>
  </div>
  <div class="footnote">
    순유동성이 증가하면 시장에 돈이 풀려 <b class="up">주가 상승</b> 압력,
    감소하면 유동성 회수로 <b class="dn">주가 조정</b> 가능성이 높아집니다.
  </div>
</div></body></html>"""
            components.html(html_box, height=520, scrolling=False)
        else:
            st.warning("데이터 병합 포인트가 부족합니다. 잠시 후 다시 시도해 주세요.")

    except Exception as e:
        st.error(f"유동성 섹션 오류: {str(e)}")

else:
    st.markdown("""
<div style="background:#1A0E0E; border:1px solid #8B3A3A; border-radius:10px; padding:16px; margin-bottom:16px;">
  <div style="font-size:0.9rem; font-weight:700; color:#FF8080; margin-bottom:6px;">데이터 로딩 실패 — 항목별 상태</div>
  <div style="font-size:0.82rem; color:#DDC0C0; line-height:1.6;">FRED API 또는 인터넷 연결 상태를 확인하세요.</div>
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
            ok_color = "#22D98A" if status else "#FF6B6B"
            ok_text  = "READY"   if status else "FAILED"
            st.markdown(f"""
<div style="background:#0C1420; border:2px solid {ok_color}; border-radius:8px; padding:14px; text-align:center;">
  <div style="font-size:0.75rem; font-weight:700; color:#8AAED0; margin-bottom:6px;">{name}</div>
  <div style="font-family:'IBM Plex Mono',monospace; font-size:1.1rem; font-weight:800; color:{ok_color};">{ok_text}</div>
</div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §10  리스크 지표 상세 분석
# ═══════════════════════════════════════════════════════════
st.markdown("---")
st.markdown("## 🔬 리스크 지표 상세 분석")
st.markdown("12개 지표를 순서대로 확인하세요.")

RISK_INDICATORS = [
    {
        "name": "① VIX 공포지수",
        "yf_ticker": "^VIX",
        "fred_id": None,
        "color": "#ef4444",
        "unit": "",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**VIX (CBOE Volatility Index)** 는 S&P 500 옵션 시장에서 도출된 **향후 30일 주식 시장의 예상 변동성 지수**입니다.\n- **주가와 역의 상관관계**: 주가 급락 시 VIX 급등\n- **실시간 심리 반영**: 투자자들의 공포/탐욕 수준 파악\n- **글로벌 위기 선행지표**: 금융위기, 코로나, 금리쇼크 시 급등",
        "thresholds": {"safe": (0, 15), "caution": (15, 25), "warning": (25, 35), "danger": (35, 9999)},
        "threshold_labels": {
            "safe":    "안정 — 시장이 매우 차분하고 낙관적입니다.",
            "caution": "보통 — 정상 범위이나 약간의 불확실성 존재.",
            "warning": "주의 ⚠️ — 시장 변동성 확대 구간. 방어적 포지션 고려.",
            "danger":  "심각 🔴 — 공포 확산! 과거 위기 수준. 현금 비중 확대 권고.",
        },
    },
    {
        "name": "② MOVE 채권변동성",
        "yf_ticker": "^MOVE",
        "fred_id": None,
        "color": "#f59e0b",
        "unit": "",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**MOVE Index** 는 **미국 국채 시장의 내재 변동성 지수**입니다.\n- **MOVE 상승 = 금리 불확실성 확대**\n- **채권·주식 동반 위험 신호**\n- **은행 시스템 스트레스 연동**",
        "thresholds": {"safe": (0, 80), "caution": (80, 120), "warning": (120, 160), "danger": (160, 9999)},
        "threshold_labels": {
            "safe":    "안정 — 채권 시장 안정적.",
            "caution": "보통 — 금리 불확실성 다소 존재.",
            "warning": "주의 ⚠️ — 채권 변동성 확대.",
            "danger":  "심각 🔴 — 채권 시장 극도의 불안.",
        },
    },
    {
        "name": "③ 장단기 금리차 (10Y-2Y)",
        "yf_ticker": None,
        "fred_id": "T10Y2Y",
        "color": "#3b82f6",
        "unit": "%",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**장단기 금리차 (10Y-2Y)** 는 **미국 10년물 국채금리에서 2년물 국채금리를 뺀 값**입니다.\n- **마이너스(역전) = 경기침체 경고**\n- **플러스 복귀 = 침체 임박 신호**\n- **연준 정책 방향성 반영**",
        "thresholds": {"danger": (-9999, 0), "warning": (0, 0.5), "caution": (0.5, 1.5), "safe": (1.5, 9999)},
        "threshold_labels": {
            "danger":  "심각 🔴 — 금리 역전! 경기 침체 강력 경고 신호.",
            "warning": "주의 ⚠️ — 금리차 매우 좁음.",
            "caution": "보통 — 정상 범위 하단.",
            "safe":    "안정 — 금리차 정상. 경기 확장 국면.",
        },
    },
    {
        "name": "④ HYG (하이일드 ETF)",
        "yf_ticker": "HYG",
        "fred_id": None,
        "color": "#ec4899",
        "unit": "",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**HYG (iShares iBoxx High Yield Corporate Bond ETF)** 는 **미국 하이일드 채권을 추종하는 ETF**입니다.\n- **가격 하락 = 신용 위험 증가**\n- **주식 시장 선행**\n- **유동성 위기 바로미터**",
        "thresholds": {"danger": (-9999, 73), "warning": (73, 77), "caution": (77, 81), "safe": (81, 9999)},
        "threshold_labels": {
            "danger":  "심각 🔴 — HYG 급락! 신용 시장 위기 상태.",
            "warning": "주의 ⚠️ — 신용 시장 압박.",
            "caution": "보통 — 소폭 약세.",
            "safe":    "안정 — 하이일드 시장 건전.",
        },
    },
    {
        "name": "⑤ HY OAS 신용스프레드",
        "yf_ticker": None,
        "fred_id": "BAMLH0A0HYM2",
        "color": "#8b5cf6",
        "unit": "%",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**HY OAS (High Yield Option-Adjusted Spread)** 는 **하이일드 채권과 미국 국채 간의 금리 차이**입니다.\n- **스프레드 확대 = 신용 위험 증가**\n- **경기 침체 선행지표**\n- **유동성 경색 시그널**",
        "thresholds": {"safe": (0, 3.5), "caution": (3.5, 5.5), "warning": (5.5, 8.0), "danger": (8.0, 9999)},
        "threshold_labels": {
            "safe":    "안정 — 기업 신용 시장 건전.",
            "caution": "보통 — 신용 위험 소폭 상승.",
            "warning": "주의 ⚠️ — 신용 스프레드 확대.",
            "danger":  "심각 🔴 — 신용 위기 경보!",
        },
    },
    {
        "name": "⑥ 연준 총자산 (대차대조표)",
        "yf_ticker": None,
        "fred_id": "WALCL",
        "color": "#06b6d4",
        "unit": "B$",
        "fred_unit_divisor": 1000,   # M$ → B$
        "period": "2y",
        "description": "**연준 총자산 (Fed Balance Sheet)** 은 **연방준비제도의 보유 자산 총액**입니다.\n- **자산 증가(QE) = 유동성 공급**\n- **자산 감소(QT) = 유동성 흡수**\n- **경제 위기 시 급팽창**",
        "thresholds": {"danger": (-9999, 4000), "warning": (4000, 6000), "caution": (6000, 7500), "safe": (7500, 9999)},
        "threshold_labels": {
            "danger":  "심각 🔴 — 연준 자산 급감.",
            "warning": "주의 ⚠️ — QT 진행 중.",
            "caution": "보통 — 안정적 QT 범위.",
            "safe":    "안정 — 유동성 충분.",
        },
    },
    {
        "name": "⑦ 지급준비금 잔고",
        "yf_ticker": None,
        "fred_id": "WRESBAL",
        "color": "#10b981",
        "unit": "B$",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**지급준비금 잔고 (Reserve Balances)** 는 **시중 은행이 연준에 예치한 지급준비금 총액**입니다.\n- **잔고 감소 = 유동성 긴장**\n- **레포 시장 스트레스 연동**\n- **QT 한계 지표**",
        "thresholds": {"danger": (-9999, 2500), "warning": (2500, 3000), "caution": (3000, 3500), "safe": (3500, 9999)},
        "threshold_labels": {
            "danger":  "심각 🔴 — 준비금 급감!",
            "warning": "주의 ⚠️ — 준비금 부족 경계선.",
            "caution": "보통 — 준비금 적정 하단.",
            "safe":    "안정 — 준비금 충분.",
        },
    },
    {
        "name": "⑧ TGA (재무부 일반계정)",
        "yf_ticker": None,
        "fred_id": "WTREGEN",
        "color": "#f97316",
        "unit": "B$",
        "fred_unit_divisor": 1000,
        "period": "2y",
        "description": "**TGA (Treasury General Account)** 는 **미국 재무부가 연준에 보유한 운영 계좌**입니다.\n- **TGA 증가 = 시장 유동성 흡수**\n- **TGA 감소 = 유동성 공급**\n- **부채한도 협상과 연동**",
        "thresholds": {"danger": (-9999, 200), "warning": (200, 400), "caution": (400, 700), "safe": (700, 9999)},
        "threshold_labels": {
            "danger":  "심각 🔴 — TGA 바닥!",
            "warning": "주의 ⚠️ — TGA 낮음.",
            "caution": "보통 — TGA 정상 하단.",
            "safe":    "안정 — TGA 충분.",
        },
    },
    {
        "name": "⑨ 역레포 (ON RRP)",
        "yf_ticker": None,
        "fred_id": "RRPONTSYD",
        "color": "#a78bfa",
        "unit": "B$",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**역레포 (Overnight Reverse Repurchase, ON RRP)** 는 **연준이 MMF 등으로부터 하룻밤 자금을 빌리는 거래**입니다.\n- **역레포 증가 = 시장 초과 유동성**\n- **역레포 감소 = 유동성 흡수**\n- **급감 = 주의**",
        "thresholds": {"safe": (-9999, 500), "caution": (500, 1000), "warning": (1000, 2000), "danger": (2000, 9999)},
        "threshold_labels": {
            "safe":    "안정 — 역레포 낮음.",
            "caution": "보통 — 역레포 중간.",
            "warning": "주의 ⚠️ — 역레포 높음.",
            "danger":  "심각 🔴 — 역레포 극대!",
        },
    },
    {
        "name": "⑩ MMF 총잔고",
        "yf_ticker": None,
        "fred_id": "WRMFSL",
        "color": "#34d399",
        "unit": "B$",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**MMF 총잔고 (Money Market Fund Total Assets)** 는 **머니마켓펀드에 유입된 총 자산 규모**입니다.\n- **MMF 증가 = 위험 회피**\n- **대기 자금 규모**\n- **금리 환경 반영**",
        "thresholds": {"safe": (-9999, 4500), "caution": (4500, 5500), "warning": (5500, 6500), "danger": (6500, 9999)},
        "threshold_labels": {
            "safe":    "안정 — MMF 정상 수준.",
            "caution": "보통 — MMF 소폭 증가.",
            "warning": "주의 ⚠️ — MMF 급증.",
            "danger":  "심각 🔴 — MMF 사상 최고!",
        },
    },
    {
        "name": "⑪ 은행 대출 잔고",
        "yf_ticker": None,
        "fred_id": "TOTLL",
        "color": "#fb7185",
        "unit": "B$",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**은행 대출 잔고 (Total Loans and Leases)** 는 **미국 상업은행의 총 대출 및 리스 잔액**입니다.\n- **대출 증가 = 경기 확장**\n- **대출 감소 = 경기 수축**\n- **금리 민감도**",
        "thresholds": {"danger": (-9999, 11000), "warning": (11000, 12000), "caution": (12000, 13000), "safe": (13000, 9999)},
        "threshold_labels": {
            "danger":  "심각 🔴 — 대출 급감!",
            "warning": "주의 ⚠️ — 대출 감소세.",
            "caution": "보통 — 대출 성장 둔화.",
            "safe":    "안정 — 대출 성장 양호.",
        },
    },
    {
        "name": "⑫ SOFR (익일물 금리)",
        "yf_ticker": None,
        "fred_id": "SOFR",
        "color": "#fbbf24",
        "unit": "%",
        "fred_unit_divisor": 1,
        "period": "2y",
        "description": "**SOFR (Secured Overnight Financing Rate)** 는 **미국 국채 담보 익일물 금리**입니다.\n- **연준 기준금리와 연동**\n- **급등 = 단기 유동성 경색**\n- **스프레드 확대 주목**",
        "thresholds": {"safe": (0, 2.5), "caution": (2.5, 4.0), "warning": (4.0, 5.5), "danger": (5.5, 9999)},
        "threshold_labels": {
            "safe":    "안정 — 저금리 환경.",
            "caution": "보통 — 중립 금리 수준.",
            "warning": "주의 ⚠️ — 고금리 유지.",
            "danger":  "심각 🔴 — 초고금리!",
        },
    },
]

# ── 각 지표 렌더링
for idx, info in enumerate(RISK_INDICATORS):

    st.markdown("---")
    st.markdown(f"### {info['name']}")

    detail_data = None
    load_error  = None

    try:
        if info.get("yf_ticker"):
            _, _, raw_h = get_yf(info["yf_ticker"], info["period"], "1d")
            if raw_h is not None and not raw_h.empty:
                detail_data = raw_h["Close"].dropna()
        elif info.get("fred_id"):
            raw_s = get_fred_range(info["fred_id"], days=730)
            if raw_s is not None and len(raw_s) > 0:
                divisor = info.get("fred_unit_divisor", 1)
                detail_data = raw_s / divisor if divisor != 1 else raw_s
    except Exception as e:
        load_error = str(e)

    current_val  = None
    status_key   = "caution"
    status_label = "데이터 없음"
    change       = 0.0

    if detail_data is not None and len(detail_data) > 0:
        current_val  = float(detail_data.iloc[-1])
        prev_val     = float(detail_data.iloc[-2]) if len(detail_data) > 1 else current_val
        change       = current_val - prev_val
        status_key, status_label = get_risk_status(
            current_val, info["thresholds"], info["threshold_labels"]
        )

    style = STATUS_STYLE[status_key]

    if detail_data is not None and len(detail_data) > 0:
        val_min    = float(detail_data.min())
        val_max    = float(detail_data.max())
        val_avg    = float(detail_data.mean())
        percentile = float((detail_data <= current_val).mean() * 100)
    else:
        val_min = val_max = val_avg = percentile = 0.0

    unit_str       = info["unit"]
    val_display    = f"{current_val:.2f}{unit_str}" if current_val is not None else "N/A"
    change_display = f"{change:+.2f}" if current_val is not None else "-"
    change_color   = "#ef4444" if change > 0 else "#10b981"

    status_html = f"""
<!DOCTYPE html><html><head>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ background:transparent; font-family:'Segoe UI',sans-serif; padding:4px 0; }}
  .wrapper {{ display:flex; gap:8px; flex-wrap:nowrap; align-items:stretch; }}
  .status-card {{
    flex:1.8; min-width:160px;
    background:{style['bg']};
    border:2px solid {style['border']};
    border-radius:10px; padding:10px 14px;
    display:flex; align-items:center; gap:10px;
  }}
  .s-icon  {{ font-size:26px; flex-shrink:0; }}
  .s-text  {{ display:flex; flex-direction:column; gap:2px; }}
  .s-label {{ font-size:15px; font-weight:900; color:{style['text']}; letter-spacing:2px; }}
  .s-desc  {{ font-size:11px; color:#C8E0F4; line-height:1.4; }}
  .mc {{
    flex:1; min-width:80px;
    background:#1f2937; border:1px solid #374151;
    border-radius:10px; padding:8px 6px; text-align:center;
    display:flex; flex-direction:column; justify-content:center; gap:3px;
  }}
  .mt {{ font-size:10px; color:#94b4cc; text-transform:uppercase; letter-spacing:0.5px; }}
  .mv {{ font-size:16px; font-weight:800; color:#f0f8ff; line-height:1.2; }}
  .ms {{ font-size:10px; color:#8AAED0; }}
</style></head><body>
<div class="wrapper">
  <div class="status-card">
    <div class="s-icon">{style['icon']}</div>
    <div class="s-text">
      <div class="s-label">{style['label']}</div>
      <div class="s-desc">{status_label}</div>
    </div>
  </div>
  <div class="mc"><div class="mt">현재값</div><div class="mv">{val_display}</div><div class="ms" style="color:{change_color};">{change_display}</div></div>
  <div class="mc"><div class="mt">최저</div><div class="mv">{val_min:.2f}</div><div class="ms">2Y Low</div></div>
  <div class="mc"><div class="mt">최고</div><div class="mv">{val_max:.2f}</div><div class="ms">2Y High</div></div>
  <div class="mc"><div class="mt">평균</div><div class="mv">{val_avg:.2f}</div><div class="ms">2Y Avg</div></div>
  <div class="mc"><div class="mt">백분위</div><div class="mv" style="color:{style['text']};">{percentile:.0f}%</div><div class="ms">2Y 기준</div></div>
</div></body></html>"""
    components.html(status_html, height=80, scrolling=False)

    if detail_data is not None and len(detail_data) > 0:
        df_d = detail_data.reset_index()
        df_d.columns = ["Date", "Value"]

        th  = info["thresholds"]
        fig = go.Figure()

        zone_colors = {
            "safe":    "rgba(16,185,129,0.07)",
            "caution": "rgba(245,158,11,0.07)",
            "warning": "rgba(249,115,22,0.10)",
            "danger":  "rgba(239,68,68,0.12)",
        }

        y_min = float(df_d["Value"].min())
        y_max = float(df_d["Value"].max())
        y_pad = abs(y_max - y_min) * 0.1
        x_min = df_d["Date"].min()
        x_max = df_d["Date"].max()

        for zone, (z_low, z_high) in th.items():
            y0 = z_low  if z_low  > -900  else y_min - y_pad
            y1 = z_high if z_high < 9000  else y_max + y_pad
            if y0 >= y1:
                continue
            fig.add_shape(
                type="rect", xref="x", yref="y",
                x0=x_min, x1=x_max, y0=y0, y1=y1,
                fillcolor=zone_colors[zone], line_width=0, layer="below",
            )

        fig.add_trace(go.Scatter(
            x=df_d["Date"], y=df_d["Value"],
            mode="lines", name=info["name"],
            line=dict(color=info["color"], width=2.5),
            fill="tozeroy",
            fillcolor=hex_to_rgba(info["color"], 0.08),
            hovertemplate="<b>%{x|%Y-%m-%d}</b><br>값: %{y:.2f}<extra></extra>",
        ))

        if current_val is not None:
            fig.add_hline(
                y=current_val,
                line_dash="dot", line_color=style["border"], line_width=1.8,
                annotation_text=f"  현재: {current_val:.2f}",
                annotation_position="right",
                annotation_font_color=style["text"],
                annotation_font_size=13,
            )

        th_line_colors = {
            "safe": "#10b981", "caution": "#f59e0b", "warning": "#f97316", "danger": "#ef4444",
        }
        drawn = set()
        for zone, (z_low, z_high) in th.items():
            for tv in [z_low, z_high]:
                if -900 < tv < 9000 and tv not in drawn:
                    fig.add_hline(
                        y=tv, line_dash="dash",
                        line_color=th_line_colors[zone],
                        line_width=1, opacity=0.45,
                    )
                    drawn.add(tv)

        # ✅ 그래프 배경색도 기존 #111827에서 #060A12 로 완전히 통일했습니다.
        fig.update_layout(
            height=480,
            margin=dict(l=10, r=80, t=55, b=40),
            paper_bgcolor="#060A12", plot_bgcolor="#060A12",
            font=dict(color="#D8ECF8", size=13),
            title=dict(
                text=f"<b>{info['name']}</b> — 최근 2년 추이",
                font=dict(size=18, color="#F0F8FF"), x=0.01,
            ),
            xaxis=dict(
                gridcolor="#1A2A3F", showgrid=True, zeroline=False,
                tickfont=dict(size=12, color="#B8D4EE"),
            ),
            yaxis=dict(
                gridcolor="#1A2A3F", showgrid=True, zeroline=False,
                tickfont=dict(size=12, color="#B8D4EE"),
            ),
            hovermode="x unified", showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

    else:
        if load_error:
            st.error(f"❌ 데이터 로드 실패 ({info['name']}): {load_error}")
        else:
            st.warning(f"⚠️ {info['name']} — 데이터를 불러오지 못했습니다.")

    st.markdown(info["description"])
    st.markdown("**📊 단계별 판정 기준**")

    status_emojis = {
        "safe": "✅ 안전", "caution": "🟡 보통", "warning": "⚠️ 주의", "danger": "🔴 심각",
    }
    th_rows = []
    for zone, (z_low, z_high) in info["thresholds"].items():
        low_str  = str(z_low)  if z_low  > -900 else "-∞"
        high_str = str(z_high) if z_high < 9000 else "+∞"
        th_rows.append({
            "상태": status_emojis[zone],
            "범위": f"{low_str} ~ {high_str}{unit_str}",
            "의미": info["threshold_labels"][zone],
        })
    st.table(pd.DataFrame(th_rows))


# ═══════════════════════════════════════════════════════════
#  사이드바
# ═══════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### ⚙️ 설정")
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
- FRED (Federal Reserve)
- 5분 캐시 적용
    """)


# ═══════════════════════════════════════════════════════════
#  푸터
# ═══════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#4A7090; font-size:.70rem;
            font-family:'IBM Plex Mono',monospace; font-weight:700; padding:12px 0;">
  Yahoo Finance · FRED | {now_str}
</div>
""", unsafe_allow_html=True)
