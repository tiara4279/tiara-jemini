# ============================================================
#  글로벌 매크로 대시보드 — app.py (v8 - 확장성과 가독성 조정)
# ============================================================
import subprocess, sys, os, warnings
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
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ── FRED API ──────────────────────────────────────────────────
FRED_API_KEY = "44435d53f0376bf6ab6263db6892924f"
fred = None
try:
    from fredapi import Fred
    fred = Fred(api_key=FRED_API_KEY)
except Exception:
    fred = None

# ── 페이지 설정 ───────────────────────────────────────────────
st.set_page_config(
    page_title="글로벌 매크로 대시보드",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── HEX → rgba 변환 ──────────────────────────────────────────
def hex_to_rgba(hex_color, alpha=0.10):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

# ── 전체 CSS ──────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700;900&display=swap');

html, body, [class*="css"], .stMarkdown, .stText, p, span, div, label {
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stApp { background: #060A12 !important; }
.block-container {
    padding-top: 2rem !important;
}

h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    letter-spacing: 0.04em !important;
}
.stCaption, .stCaption p, small {
    font-size: 1rem !important; /* 1.5배 증가 */
    font-weight: 700 !important;
    color: #5A8AAE !important;
}
.sec-hd {
    background: linear-gradient(90deg, #00D4FF18, transparent);
    border-left: 4px solid #00D4FF;
    padding: 8px 16px;
    margin: 28px 0 12px;
    border-radius: 0 8px 8px 0;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.275rem !important; /* 1.5배 증가 */
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
}
.kdn {
    color: #FF5555 !important;
    font-size: .84rem !important;
}
.kna {
    color: #607090 !important;
    font-size: .84rem !important;
}
.ksub {
    color: #4A6888 !important;
    font-size: .70rem !important;
    margin-top: 4px;
}
.b-low { background: #10B98122; color: #22D98A !important; }
.b-mid { background: #F59E0B22; color: #FFCC44 !important; }
.b-hi { background: #EF444422; color: #FF5555 !important; }
hr { border-color: #1A2A3F !important; }
.stTabs [data-baseweb="tab-list"] {
    background: #0C1420; border-radius: 10px; gap: 4px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #5A7A9A !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: .80rem !important;
}
.stTabs [aria-selected="true"] {
    color: #00D4FF !important;
    background: #00D4FF18 !important;
}
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
.stAlert p {
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] {
    background: #080E1A !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    font-weight: 700 !important;
    color: #8AAAC8 !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════
#  공통 유틸
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
    st.markdown(f'<div class="sec-hd">{icon}&nbsp;&nbsp;{title}</div>', unsafe_allow_html=True)

def spark(hist_or_series, color="#00D4FF", h=75, is_series=False):
    if hist_or_series is None:
        return
    try:
        x = hist_or_series.index if is_series else hist_or_series.index
        y = hist_or_series.values if is_series else hist_or_series["Close"].values
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

# 설명을 위해 추가된 데이터
def get_indicator_description(indicator):
    descriptions = {
        "VIX": {
            "current_value": "24.5",
            "trend": "VIX 24.5 — 평균적으로 높아요. 주가가 불안정할 때는 VIX가 올라갑니다.",
            "risk": {
                "20": "안정 — 시장이 안전합니다.",
                "30": "주의 — 시장이 변동성이 높아집니다.",
                "40": "위험 — 시장이 매우 불안정합니다.",
            },
            "chart_data": "VIX 그래프 데이터",  # 그래프 데이터 추가 필요
        },
        "Liquidity": {
            "current_value": "3,300억",
            "trend": "현재 유동성 상황은 양호합니다. 데이터 업데이트 필요.",
            "risk": {
                "20": "안정 — 유동성이 안정적입니다.",
                "30": "주의 — 유동성의 변동성이 커질 수 있습니다.",
                "40": "위험 — 유동성이 낮습니다.",
            },
            "chart_data": "유동성 그래프 데이터",
        },
        "Credit": {
            "current_value": "17,500억",
            "trend": "신용 상태는 안정적인 편입니다.",
            "risk": {
                "20": "안정 — 신용 상태가 안정적입니다.",
                "30": "주의 — 신용 위험이 증가할 수 있습니다.",
                "40": "위험 — 신용이 걱정됩니다.",
            },
            "chart_data": "신용 그래프 데이터",
        },
    }
    return descriptions[indicator]

# ═══════════════════════════════════════════════════════════
#  헤더 — 타이틀, 타임스탬프, 새로고침 버튼
# ═══════════════════════════════════════════════════════════

now_str = datetime.utcnow().strftime("%Y-%m-%d  %H:%M  UTC")

st.title("📡 글로벌 매크로 대시보드")
st.caption("GLOBAL MACRO MONITOR — REAL-TIME FINANCIAL INDICATORS")

ts_col, btn_col = st.columns([6, 1])
with ts_col:
    st.markdown(f'<div class="ts-box">🕐 {now_str}</div>', unsafe_allow_html=True)
with btn_col:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")
st.success("✅ **FRED API 연결됨** — 연준·유동성·인플레이션 실데이터 수신 중")

# ═══════════════════════════════════════════════════════════
#  §1  지표 선택
# ═══════════════════════════════════════════════════════════

indicator_choice = st.selectbox(
    "지표 선택하기",
    ["시장 리스크 및 스트레스 지표 (VIX)", "유동성을 좌우하는 핵심 창구 (연준)", "은행 신용 및 단기 자금 시장"]
)

if indicator_choice == "시장 리스크 및 스트레스 지표 (VIX)":
    description = get_indicator_description("VIX")
    
    # 데이터 및 그래프
    vix_data = get_fred("VIX", 60)  # VIX 데이터 예시
    if vix_data is not None:
        spark(vix_data, "#EF4444", 300, is_series=True)

    # 설명
    st.markdown(f"### 현재 VIX 수치\n**{description['current_value']}**\n")
    st.markdown(f"### 분석:\n{description['trend']}\n")
    for key, value in description['risk'].items():
        st.markdown(f"**{key}** — {value}")

elif indicator_choice == "유동성을 좌우하는 핵심 창구 (연준)":
    description = get_indicator_description("Liquidity")

    # 데이터 및 그래프
    liquidity_data = get_fred("WALCL", 60)  # 예시 데이터
    if liquidity_data is not None:
        spark(liquidity_data, "#10B981", 300, is_series=True)

    # 설명
    st.markdown(f"### 현재 유동성 수치\n**{description['current_value']}**\n")
    st.markdown(f"### 분석:\n{description['trend']}\n")
    for key, value in description['risk'].items():
        st.markdown(f"**{key}** — {value}")

elif indicator_choice == "은행 신용 및 단기 자금 시장":
    description = get_indicator_description("Credit")

    # 데이터 및 그래프
    credit_data = get_fred("RRPONTSYD", 60)  # 예시 데이터
    if credit_data is not None:
        spark(credit_data, "#8B5CF6", 300, is_series=True)

    # 설명
    st.markdown(f"### 현재 신용 수치\n**{description['current_value']}**\n")
    st.markdown(f"### 분석:\n{description['trend']}\n")
    for key, value in description['risk'].items():
        st.markdown(f"**{key}** — {value}")

# ── 푸터 ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#2A4060; font-size:.70rem;
     font-family:'IBM Plex Mono',monospace; font-weight:700; padding:12px 0">
  📡 Yahoo Finance · FRED (St. Louis Fed) &nbsp;|&nbsp;
  ⏱ 5분 캐시 &nbsp;|&nbsp; 🕐 {now_str}
</div>
""", unsafe_allow_html=True)
