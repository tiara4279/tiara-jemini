# ============================================================
#  글로벌 매크로 대시보드 — app.py (완성본)
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
    max-width: 1400px;
}
h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    letter-spacing: 0.04em !important;
    line-height: 1.25 !important;
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
    cursor: pointer;
}
.kcard:hover {
    border-color: #00D4FF66;
    box-shadow: 0 0 20px rgba(0,212,255,0.08);
}
.kcard-active {
    background: linear-gradient(140deg, #131E2E, #0C1520);
    border: 1px solid #00D4FFAA !important;
    border-radius: 12px;
    padding: 16px 18px 12px;
    margin-bottom: 10px;
    box-shadow: 0 0 24px rgba(0,212,255,0.18) !important;
    cursor: pointer;
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
.b-low {
    background: #10B98122; color: #22D98A !important;
    border: 1px solid #10B98155;
    padding: 2px 9px; border-radius: 99px;
    font-size: .70rem !important; font-weight: 700 !important;
}
.b-mid {
    background: #F59E0B22; color: #FFCC44 !important;
    border: 1px solid #F59E0B55;
    padding: 2px 9px; border-radius: 99px;
    font-size: .70rem !important; font-weight: 700 !important;
}
.b-hi {
    background: #EF444422; color: #FF5555 !important;
    border: 1px solid #EF444455;
    padding: 2px 9px; border-radius: 99px;
    font-size: .70rem !important; font-weight: 700 !important;
}
hr { border-color: #1A2A3F !important; }
.stTabs [data-baseweb="tab-list"] {
    background: #0C1420; border-radius: 10px; gap: 4px; padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    color: #5A7A9A !important;
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: .80rem !important;
    font-weight: 700 !important;
}
.stTabs [aria-selected="true"] {
    color: #00D4FF !important;
    background: #00D4FF18 !important;
    border-radius: 7px;
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
.stAlert p { font-weight: 700 !important; }
section[data-testid="stSidebar"] { background: #080E1A !important; }
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    font-weight: 700 !important;
    color: #8AAAC8 !important;
}
.detail-panel {
    background: linear-gradient(160deg, #0D1828, #080E1A);
    border: 1px solid #00D4FF33;
    border-radius: 16px;
    padding: 28px 32px;
    margin: 20px 0;
    box-shadow: 0 0 40px rgba(0,212,255,0.06);
}
.detail-title {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 1.5rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    letter-spacing: 0.06em;
    margin-bottom: 4px;
}
.detail-subtitle {
    font-size: 0.85rem !important;
    color: #4A6888 !important;
    font-weight: 600 !important;
    margin-bottom: 20px;
    letter-spacing: 0.08em;
}
.detail-val-box {
    background: #131E2E;
    border: 1px solid #1E3050;
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 12px;
}
.detail-val-label {
    font-size: 0.70rem !important;
    font-weight: 700 !important;
    color: #4A6888 !important;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}
.detail-val-num {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    line-height: 1.2;
}
.level-card {
    border-radius: 10px;
    padding: 12px 16px;
    margin-bottom: 8px;
    border: 1px solid;
}
.level-low  { background: #10B98115; border-color: #10B98133; }
.level-mid  { background: #F59E0B15; border-color: #F59E0B33; }
.level-hi   { background: #EF444415; border-color: #EF444433; }
.level-crit { background: #9333EA15; border-color: #9333EA33; }
.level-title {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.88rem !important;
    font-weight: 700 !important;
    margin-bottom: 4px;
}
.level-desc {
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    color: #7A9ABE !important;
    line-height: 1.5;
}
.outlook-box {
    background: linear-gradient(135deg, #0F1F35, #0A1525);
    border: 1px solid #00D4FF22;
    border-radius: 12px;
    padding: 20px 24px;
    margin-top: 16px;
}
.outlook-title {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.9rem !important;
    font-weight: 700 !important;
    color: #00D4FF !important;
    letter-spacing: 0.12em;
    margin-bottom: 10px;
}
.outlook-text {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #AACCEE !important;
    line-height: 1.75;
}
.click-hint {
    font-size: 0.72rem !important;
    color: #2A4060 !important;
    font-weight: 600 !important;
    text-align: center;
    padding: 4px 0 0 0;
    font-family: 'IBM Plex Mono', monospace !important;
}
</style>
""", unsafe_allow_html=True)


# ── 세션 스테이트 초기화 ──────────────────────────────────────
if "selected_indicator" not in st.session_state:
    st.session_state.selected_indicator = None


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

DETAIL_CHART_LAYOUT = dict(
    height=380,
    paper_bgcolor="#0D1828",
    plot_bgcolor="#0D1828",
    legend=dict(
        bgcolor="#0C1420", bordercolor="#1A2A3F", borderwidth=1,
        font=dict(color="#AACCEE", size=12, family="IBM Plex Mono")
    ),
    xaxis=dict(gridcolor="#1A2A3E", color="#4A6A8A", showgrid=True,
               tickfont=dict(size=11, family="IBM Plex Mono")),
    yaxis=dict(gridcolor="#1A2A3E", color="#4A6A8A", showgrid=True,
               tickfont=dict(size=11, family="IBM Plex Mono")),
    margin=dict(l=60, r=20, t=30, b=40),
    hovermode="x unified",
    font=dict(family="IBM Plex Mono", color="#AACCEE"),
)


# ═══════════════════════════════════════════════════════════
#  지표 메타데이터 전체 정의
# ═══════════════════════════════════════════════════════════

META = {
    "VIX": {
        "title": "VIX — 공포 지수 (변동성 지수)",
        "subtitle": "CBOE Volatility Index · S&P 500 옵션 내재 변동성 기반",
        "color": "#EF4444",
        "ticker": "^VIX",
        "is_fred": False,
        "period": "1y",
        "what": "VIX는 S&P 500 지수 옵션의 내재 변동성을 기반으로 산출되며, 향후 30일간 시장이 얼마나 흔들릴지를 나타냅니다. '공포지수'라고도 불리며, 투자자들의 불안감을 수치화한 것입니다.",
        "levels": [
            ("20 미만 — 안정", "시장이 조용하고 투자자들이 편안한 상태. 위험 자산 선호.", "#22D98A", "level-low"),
            ("20~30 — 주의", "불확실성이 커지는 구간. 변동성이 높아질 수 있어 조심할 필요가 있어요.", "#FFCC44", "level-mid"),
            ("30 이상 — 경계", "투자자들이 겁먹은 상태. 과거 주요 시장 충격 때 항상 이 구간을 넘었어요.", "#FF5555", "level-hi"),
            ("40 이상 — 위기", "금융위기 수준의 패닉. 2008년 금융위기 때 89까지, 2020년 코로나 충격 때 85까지.", "#FF5555", "level-crit"),
        ],
        "yline": 20,
        "yline_label": "경계선 20",
        "outlook": "VIX가 20을 넘으면 단기 변동성 확대를 대비하고, 30을 넘으면 방어적 포지션을 고려하세요. 반대로 VIX 고점에서의 매수는 역사적으로 높은 수익률을 기록했습니다.",
    },
    "MOVE": {
        "title": "MOVE — 채권 변동성 지수",
        "subtitle": "ICE BofA MOVE Index · 미국 국채 옵션 내재 변동성",
        "color": "#F59E0B",
        "ticker": "^MOVE",
        "is_fred": False,
        "period": "1y",
        "what": "MOVE 지수는 미국 국채 시장의 변동성을 측정합니다. VIX가 주식 시장의 공포를 나타낸다면, MOVE는 채권 시장의 불안을 나타냅니다. 금리 정책 불확실성이 높을수록 MOVE는 급등합니다.",
        "levels": [
            ("80 미만 — 안정", "채권 시장이 안정적. 금리 방향성에 대한 합의가 형성된 상태.", "#22D98A", "level-low"),
            ("80~130 — 주의", "금리 불확실성 증가. 연준 정책 전환 기대나 인플레이션 우려 구간.", "#FFCC44", "level-mid"),
            ("130 이상 — 경계", "채권 시장 큰 혼란. 금리 급변, 국채 발행 우려 등 시스템 리스크 신호.", "#FF8844", "level-hi"),
            ("160 이상 — 위기", "2022년 영국 길트 위기(180↑), 2020년 코로나 초기(160↑) 수준.", "#FF5555", "level-crit"),
        ],
        "yline": 80,
        "yline_label": "경계선 80",
        "outlook": "MOVE와 VIX가 동시에 급등하면 주식·채권 동반 하락의 위험 신호입니다. MOVE 단독 급등은 금리 정책 불확실성이 주된 원인일 가능성이 높습니다.",
    },
    "T10Y2Y": {
        "title": "장단기 금리차 (10Y - 2Y)",
        "subtitle": "FRED T10Y2Y · 미국 국채 10년물 - 2년물 스프레드",
        "color": "#10B981",
        "fred_id": "T10Y2Y",
        "is_fred": True,
        "what": "10년 국채 금리에서 2년 국채 금리를 뺀 값입니다. 정상적인 경제에서는 양수(+)이며, 음수(-)가 되면 '장단기 금리 역전'이라고 해서 경기침체 선행지표로 해석됩니다.",
        "levels": [
            ("+0.5% 이상 — 정상", "경제가 건전하게 성장 중. 장기 금리가 단기보다 높은 정상 구조.", "#22D98A", "level-low"),
            ("0 ~ +0.5% — 주의", "수익률 곡선 평탄화. 성장 둔화 또는 금리 정점 신호일 수 있음.", "#FFCC44", "level-mid"),
            ("0 ~ -0.5% — 경계 (역전)", "장단기 역전. 과거 12~18개월 내 경기침체가 뒤따른 경우가 많음.", "#FF8844", "level-hi"),
            ("-0.5% 이하 — 심각한 역전", "깊은 역전. 1980년 이후 모든 경기침체 전에 이 구간 진입.", "#FF5555", "level-crit"),
        ],
        "yline": 0,
        "yline_label": "역전 기준선 0",
        "outlook": "역전 상태에서 정상화(스티프닝)가 시작될 때 오히려 경기침체가 임박했다는 신호일 수 있습니다. 역전 해소 시점을 주의 깊게 모니터링하세요.",
    },
    "HYG": {
        "title": "HYG — 하이일드 채권 ETF",
        "subtitle": "iShares iBoxx HY Corporate Bond ETF · 고수익 회사채",
        "color": "#8B5CF6",
        "ticker": "HYG",
        "is_fred": False,
        "period": "1y",
        "what": "HYG는 신용등급이 낮은(BB 이하) 회사채에 투자하는 ETF입니다. 경제가 좋을 때 오르고 신용 위기 때 폭락합니다. HYG 하락은 기업 신용 스트레스, 경기침체 우려의 신호입니다.",
        "levels": [
            ("$80 이상 — 안정", "신용 시장 안정. 기업 디폴트 위험이 낮고 투자자 신뢰 유지.", "#22D98A", "level-low"),
            ("$75~$80 — 주의", "신용 스프레드 확대 시작. 경기 불확실성 또는 금리 상승 압박.", "#FFCC44", "level-mid"),
            ("$70~$75 — 경계", "신용 위기 진입. 기업 자금 조달 어려움 및 디폴트 위험 증가.", "#FF8844", "level-hi"),
            ("$70 미만 — 위기", "2020년 코로나 충격 때 $68까지 급락. 신용 시장 붕괴 수준.", "#FF5555", "level-crit"),
        ],
        "yline": 80,
        "yline_label": "주의선 $80",
        "outlook": "HYG와 S&P 500의 동조화가 깨질 때 주의하세요. 주식이 오르는데 HYG가 하락한다면 신용 시장이 먼저 위험을 감지하고 있는 신호입니다.",
    },
    "HY_OAS": {
        "title": "하이일드 스프레드 (OAS)",
        "subtitle": "ICE BofA US HY OAS · FRED BAMLH0A0HYM2",
        "color": "#EF4444",
        "fred_id": "BAMLH0A0HYM2",
        "is_fred": True,
        "what": "하이일드 채권이 미국 국채 대비 얼마나 높은 금리를 요구하는지를 나타냅니다(%). 스프레드가 넓어질수록 투자자들이 기업 부도 위험을 크게 본다는 의미입니다.",
        "levels": [
            ("3% 미만 — 안정", "신용 시장 낙관. 기업 신용도 안정, 자금 조달 용이.", "#22D98A", "level-low"),
            ("3~5% — 주의", "스프레드 확대. 경기 불확실성 또는 특정 섹터 리스크 증가.", "#FFCC44", "level-mid"),
            ("5~8% — 경계", "신용 우려 심화. 경기침체 진입 가능성 높아지는 구간.", "#FF8844", "level-hi"),
            ("8% 이상 — 위기", "2009년 금융위기 때 22%까지. 2020년 코로나 때 11%까지.", "#FF5555", "level-crit"),
        ],
        "yline": 5,
        "yline_label": "경계선 5%",
        "outlook": "하이일드 스프레드는 경기침체의 선행지표입니다. 스프레드가 빠르게 확대되면 기업 신용 환경 악화를 의미하며, 주식 시장 하락이 뒤따를 가능성이 높습니다.",
    },
    "WALCL": {
        "title": "연준 총자산 (대차대조표)",
        "subtitle": "FRED WALCL · Federal Reserve Total Assets",
        "color": "#3B82F6",
        "fred_id": "WALCL",
        "is_fred": True,
        "what": "연준(미국 중앙은행)이 보유한 총자산 규모입니다. 양적완화(QE) 시 자산이 급증하고, 양적긴축(QT) 시 감소합니다. 시중 유동성의 핵심 지표로, 이 숫자가 크면 돈이 많이 풀린 상태입니다.",
        "levels": [
            ("9조 달러 이상 — 완화 기조", "풍부한 유동성. 주식·부동산 등 위험 자산에 유리한 환경.", "#22D98A", "level-low"),
            ("7~9조 달러 — 중립", "QT 진행 중이나 완만한 감소. 시장에 미치는 직접적 영향 제한적.", "#FFCC44", "level-mid"),
            ("5~7조 달러 — 긴축", "유동성 회수 본격화. 금융 시스템 스트레스 주의 필요.", "#FF8844", "level-hi"),
            ("5조 달러 미만 — 과도 긴축", "2020년 이전 수준. 급격한 긴축으로 시장 충격 가능성.", "#FF5555", "level-crit"),
        ],
        "yline": None,
        "outlook": "연준 대차대조표 축소(QT) 속도가 빨라지면 시장 유동성이 감소합니다. 준비금 잔고와 함께 모니터링하여 QT 한계점을 파악하는 것이 중요합니다.",
    },
    "WRBWFRBL": {
        "title": "지급준비금 잔고",
        "subtitle": "FRED WRBWFRBL · Reserve Balances with Federal Reserve Banks",
        "color": "#10B981",
        "fred_id": "WRBWFRBL",
        "is_fred": True,
        "what": "은행들이 연준에 예치한 준비금 총액입니다. 이 금액이 많을수록 은행 시스템이 여유 자금을 충분히 보유하고 있으며, 너무 줄어들면 은행 간 자금 경색(2019년 레포 위기처럼)이 발생할 수 있습니다.",
        "levels": [
            ("3조 달러 이상 — 풍부", "은행 시스템 유동성 충분. 단기 자금 시장 안정.", "#22D98A", "level-low"),
            ("2~3조 달러 — 적정", "적정 수준의 준비금. 연준 QT 지속 가능 구간.", "#FFCC44", "level-mid"),
            ("1~2조 달러 — 주의", "준비금 감소로 단기 금리 급등 가능성. 2019년 레포 위기 전조.", "#FF8844", "level-hi"),
            ("1조 달러 미만 — 위험", "은행 간 자금 부족. 연준 긴급 개입 가능성 높음.", "#FF5555", "level-crit"),
        ],
        "yline": None,
        "outlook": "준비금이 2조 달러 아래로 내려가면 QT 속도 조절을 고려해야 합니다. 2019년 9월 레포 시장 위기가 준비금 부족에서 비롯되었다는 점을 기억하세요.",
    },
    "WTREGEN": {
        "title": "TGA — 재무부 일반계정",
        "subtitle": "FRED WTREGEN · U.S. Treasury General Account",
        "color": "#F59E0B",
        "fred_id": "WTREGEN",
        "is_fred": True,
        "what": "미국 재무부가 연준에 보유한 당좌예금 계좌입니다. TGA가 줄면(재무부 지출↑) 시중에 달러가 풀려 유동성이 증가하고, TGA가 늘면(세금 수입↑) 유동성이 흡수됩니다.",
        "levels": [
            ("7,000억 달러 이상 — 풍부", "재무부 여력 충분. 향후 지출 시 시중 유동성 공급 기대.", "#22D98A", "level-low"),
            ("3,000~7,000억 달러 — 적정", "정상 운영 수준. 시장에 미치는 직접적 영향 제한적.", "#FFCC44", "level-mid"),
            ("1,000~3,000억 달러 — 주의", "부채한도 협상 등 정치적 리스크 구간. 유동성 변동성 증가.", "#FF8844", "level-hi"),
            ("1,000억 달러 미만 — 위험", "디폴트 위험 수준. 부채한도 위기 직전 패턴.", "#FF5555", "level-crit"),
        ],
        "yline": None,
        "outlook": "부채한도 협상 시즌에 TGA가 급격히 소진되면 단기적으로 유동성이 공급되어 주가에 긍정적일 수 있지만, 이후 TGA 재충전 시 유동성 흡수가 나타납니다.",
    },
    "RRPONTSYD": {
        "title": "역레포 (ON RRP)",
        "subtitle": "FRED RRPONTSYD · Overnight Reverse Repurchase Agreements",
        "color": "#EC4899",
        "fred_id": "RRPONTSYD",
        "is_fred": True,
        "what": "MMF 등 금융기관이 연준에 하루짜리로 돈을 맡기는 규모입니다. 역레포가 많다는 것은 시중에 갈 곳 없는 돈이 넘쳐난다는 의미(유동성 과잉). 역레포가 줄면 그 돈이 다른 곳으로 이동하고 있다는 뜻입니다.",
        "levels": [
            ("2조 달러 이상 — 유동성 과잉", "시중 자금이 넘쳐남. MMF로 몰린 현금 대기 중.", "#22D98A", "level-low"),
            ("5,000억~2조 달러 — 정상화", "과잉 유동성 서서히 흡수 중. QT 효과 나타나는 구간.", "#FFCC44", "level-mid"),
            ("1,000~5,000억 달러 — 감소", "역레포 거의 소진. 준비금 감소 시작, 단기 금리 압력 가능.", "#FF8844", "level-hi"),
            ("1,000억 달러 미만 — 고갈", "역레포 완전 소진. 준비금만 남아 QT 지속 시 리스크 증가.", "#FF5555", "level-crit"),
        ],
        "yline": None,
        "outlook": "역레포 잔고가 빠르게 소진될수록 QT의 시장 영향이 본격화됩니다. 역레포 잔고가 0에 가까워지면 연준이 QT를 중단하거나 속도를 줄일 가능성이 높아집니다.",
    },
    "WRMFSL": {
        "title": "MMF 총잔고",
        "subtitle": "FRED WRMFSL · Money Market Fund Total Assets",
        "color": "#06B6D4",
        "fred_id": "WRMFSL",
        "is_fred": True,
        "what": "머니마켓펀드(MMF)에 쌓인 총 자금입니다. 불확실성이 클수록 투자자들이 MMF로 피신합니다. MMF 잔고가 사상 최고치라면 '현금 대기 중' 상태로, 향후 증시 유입 기대감이 큽니다.",
        "levels": [
            ("5조 달러 이상 — 현금 과잉", "대규모 현금 대기. 불확실성 해소 시 증시 급등 연료.", "#22D98A", "level-low"),
            ("4~5조 달러 — 정상", "적정 수준의 MMF 자금. 현금 선호도 보통.", "#FFCC44", "level-mid"),
            ("3~4조 달러 — 감소", "MMF 자금이 다른 자산으로 이동 중. 위험 선호 증가.", "#22D98A", "level-low"),
            ("3조 달러 미만 — 저수준", "현금 비중 낮음. 시장이 이미 충분히 낙관적인 상태.", "#FFCC44", "level-mid"),
        ],
        "yline": None,
        "outlook": "MMF 잔고 사상 최고치는 역설적으로 강세장의 신호일 수 있습니다. 이 자금이 증시로 이동하기 시작하면 강력한 상승 동력이 됩니다.",
    },
}


# ═══════════════════════════════════════════════════════════
#  상세 패널 렌더링 함수
# ═══════════════════════════════════════════════════════════

def render_detail_panel(indicator_key):
    if indicator_key not in META:
        return
    m = META[indicator_key]
    color = m["color"]

    # 데이터 가져오기
    if m["is_fred"]:
        series = get_fred(m["fred_id"], limit=120)
        if series is not None and len(series) > 0:
            last_val = float(series.iloc[-1])
            prev_val = float(series.iloc[-2]) if len(series) > 1 else last_val
            chg_pct  = (last_val - prev_val) / abs(prev_val) * 100 if prev_val != 0 else 0
        else:
            last_val, chg_pct, series = None, None, None
        hist = None
    else:
        last_val, chg_pct, hist = get_yf(m["ticker"], period=m.get("period","1y"))
        series = None

    # ── 패널 헤더 ──
    st.markdown(f"""
    <div class="detail-panel">
        <div class="detail-title">{m['title']}</div>
        <div class="detail-subtitle">{m['subtitle']}</div>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 2])

    with col_l:
        # 현재값 박스
        val_display = f"{last_val:,.2f}" if last_val is not None else "N/A"
        chg_display = f"{'▲' if chg_pct and chg_pct >= 0 else '▼'} {abs(chg_pct):.3f}%" if chg_pct is not None else "N/A"
        chg_color   = "#22D98A" if chg_pct and chg_pct >= 0 else "#FF5555"

        st.markdown(f"""
        <div class="detail-val-box">
            <div class="detail-val-label">현재 값</div>
            <div class="detail-val-num" style="color:{color};">{val_display}</div>
            <div style="color:{chg_color}; font-family:'IBM Plex Mono'; font-weight:700; font-size:.9rem; margin-top:4px;">{chg_display}</div>
        </div>
        """, unsafe_allow_html=True)

        # 이 지표란?
        st.markdown(f"""
        <div style="background:#0A1525; border:1px solid #1A2A3F; border-radius:10px; padding:14px 16px; margin-bottom:12px;">
            <div style="font-family:'IBM Plex Mono'; font-size:.75rem; font-weight:700; color:#00D4FF; letter-spacing:.1em; margin-bottom:8px;">📖 이 지표란?</div>
            <div style="font-size:.80rem; color:#8AAAC8; line-height:1.75; font-weight:500;">{m['what']}</div>
        </div>
        """, unsafe_allow_html=True)

        # 레벨 가이드
        st.markdown("""
        <div style="font-family:'IBM Plex Mono'; font-size:.75rem; font-weight:700; color:#5A7A9A; letter-spacing:.1em; margin-bottom:8px;">📊 레벨 가이드</div>
        """, unsafe_allow_html=True)

        for lvl_title, lvl_desc, lvl_color, lvl_class in m["levels"]:
            st.markdown(f"""
            <div class="level-card {lvl_class}">
                <div class="level-title" style="color:{lvl_color};">{lvl_title}</div>
                <div class="level-desc">{lvl_desc}</div>
            </div>
            """, unsafe_allow_html=True)

        # 투자 시사점
        if "outlook" in m:
            st.markdown(f"""
            <div class="outlook-box">
                <div class="outlook-title">💡 투자 시사점</div>
                <div class="outlook-text">{m['outlook']}</div>
            </div>
            """, unsafe_allow_html=True)

    with col_r:
        # 차트
        data_available = (hist is not None and not hist.empty) or (series is not None and len(series) > 0)

        if data_available:
            fig = go.Figure()

            if m["is_fred"] and series is not None:
                fig.add_trace(go.Scatter(
                    x=series.index, y=series.values,
                    mode="lines", name=indicator_key,
                    line=dict(color=color, width=2),
                    fill="tozeroy",
                    fillcolor=hex_to_rgba(color, 0.08),
                ))
            elif hist is not None:
                fig.add_trace(go.Scatter(
                    x=hist.index, y=hist["Close"].values,
                    mode="lines", name=indicator_key,
                    line=dict(color=color, width=2),
                    fill="tozeroy",
                    fillcolor=hex_to_rgba(color, 0.08),
                ))

            # 기준선 추가
            if m.get("yline") is not None:
                fig.add_hline(
                    y=m["yline"],
                    line_dash="dash",
                    line_color="#FF555566",
                    line_width=1.5,
                    annotation_text=m.get("yline_label", ""),
                    annotation_font_color="#FF5555",
                    annotation_font_size=11,
                )

            layout = dict(DETAIL_CHART_LAYOUT)
            layout["title"] = dict(
                text=f"{indicator_key} — 1년 추이",
                font=dict(size=13, color="#5A7A9A", family="IBM Plex Mono"),
                x=0.02,
            )
            fig.update_layout(**layout)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("차트 데이터를 불러오는 중이거나 데이터가 없습니다.")

    # 닫기 버튼
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("✕ 닫기", key=f"close_{indicator_key}"):
        st.session_state.selected_indicator = None
        st.rerun()


# ═══════════════════════════════════════════════════════════
#  헤더
# ═══════════════════════════════════════════════════════════

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
st.markdown(f"""
<div style="display:flex; align-items:baseline; gap:18px; flex-wrap:wrap; margin-bottom:4px;">
  <h1>📡 글로벌 매크로 대시보드</h1>
</div>
""", unsafe_allow_html=True)
st.caption(f"GLOBAL MACRO DASHBOARD  ·  {now}  ·  실시간 데이터")

# 새로고침 버튼
col_ref, _ = st.columns([1,11])
with col_ref:
    if st.button("↺ 새로고침"):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")


# ═══════════════════════════════════════════════════════════
#  탭 구성
# ═══════════════════════════════════════════════════════════

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 시장 개요",
    "⚡ 리스크 지표",
    "💵 유동성 & 연준",
    "📈 주요 자산",
    "🌐 글로벌 경제",
])


# ═══════════════════════════════════════════════════════════
#  TAB 1 — 시장 개요
# ═══════════════════════════════════════════════════════════

with tab1:

    sec("📊", "주요 지수")
    indices = [
        ("S&P 500",  "^GSPC",  "#00D4FF"),
        ("NASDAQ",   "^IXIC",  "#8B5CF6"),
        ("DOW JONES","^DJI",   "#10B981"),
        ("RUSSELL 2K","^RUT",  "#F59E0B"),
        ("KOSPI",    "^KS11",  "#EC4899"),
        ("닛케이 225","^N225",  "#3B82F6"),
    ]
    cols = st.columns(len(indices))
    for i, (name, ticker, color) in enumerate(indices):
        with cols[i]:
            val, chg, hist = get_yf(ticker)
            st.markdown(card(name, f(val, 0), chg), unsafe_allow_html=True)
            spark(hist, color)

    sec("🛢️", "원자재 & 에너지")
    comms = [
        ("WTI 원유",   "CL=F",  "#F59E0B"),
        ("브렌트 원유", "BZ=F",  "#EF4444"),
        ("천연가스",   "NG=F",  "#10B981"),
        ("금",         "GC=F",  "#FFCC44"),
        ("은",         "SI=F",  "#AACCEE"),
        ("구리",       "HG=F",  "#EC4899"),
    ]
    cols = st.columns(len(comms))
    for i, (name, ticker, color) in enumerate(comms):
        with cols[i]:
            val, chg, hist = get_yf(ticker)
            st.markdown(card(name, f(val, 2), chg), unsafe_allow_html=True)
            spark(hist, color)

    sec("💱", "주요 환율")
    fx = [
        ("USD/KRW", "USDKRW=X", "#00D4FF"),
        ("EUR/USD", "EURUSD=X", "#10B981"),
        ("USD/JPY", "USDJPY=X", "#F59E0B"),
        ("GBP/USD", "GBPUSD=X", "#8B5CF6"),
        ("USD/CNY", "USDCNY=X", "#EF4444"),
        ("DXY 달러", "DX-Y.NYB","#EC4899"),
    ]
    cols = st.columns(len(fx))
    for i, (name, ticker, color) in enumerate(fx):
        with cols[i]:
            val, chg, hist = get_yf(ticker)
            st.markdown(card(name, f(val, 2), chg), unsafe_allow_html=True)
            spark(hist, color)

    sec("₿", "암호화폐")
    crypto = [
        ("비트코인",  "BTC-USD", "#F59E0B"),
        ("이더리움",  "ETH-USD", "#8B5CF6"),
        ("BNB",       "BNB-USD", "#FFCC44"),
        ("솔라나",    "SOL-USD", "#10B981"),
        ("XRP",       "XRP-USD", "#3B82F6"),
    ]
    cols = st.columns(len(crypto))
    for i, (name, ticker, color) in enumerate(crypto):
        with cols[i]:
            val, chg, hist = get_yf(ticker)
            st.markdown(card(name, f"${f(val,0)}", chg), unsafe_allow_html=True)
            spark(hist, color)


# ═══════════════════════════════════════════════════════════
#  TAB 2 — 리스크 지표
# ═══════════════════════════════════════════════════════════

with tab2:

    sec("⚡", "변동성 지표")
    vix_val,  vix_chg,  vix_h  = get_yf("^VIX",  period="1y")
    move_val, move_chg, move_h = get_yf("^MOVE", period="1y")

    col1, col2 = st.columns(2)
    with col1:
        badge = risk_badge("VIX", vix_val)
        st.markdown(card("VIX  공포지수", f(vix_val,2), vix_chg, badge=badge), unsafe_allow_html=True)
        spark(vix_h, "#EF4444")
        if st.button("VIX 상세 보기 →", key="btn_VIX"):
            st.session_state.selected_indicator = "VIX"
            st.rerun()
    with col2:
        badge = risk_badge("MOVE", move_val)
        st.markdown(card("MOVE  채권변동성", f(move_val,2), move_chg, badge=badge), unsafe_allow_html=True)
        spark(move_h, "#F59E0B")
        if st.button("MOVE 상세 보기 →", key="btn_MOVE"):
            st.session_state.selected_indicator = "MOVE"
            st.rerun()

    # 상세 패널 표시 (VIX / MOVE)
    if st.session_state.selected_indicator in ["VIX","MOVE"]:
        render_detail_panel(st.session_state.selected_indicator)

    st.markdown("---")

    sec("📉", "신용 스프레드")
    hyg_val,  hyg_chg,  hyg_h  = get_yf("HYG", period="1y")
    lqd_val,  lqd_chg,  lqd_h  = get_yf("LQD", period="1y")
    hy_series = get_fred("BAMLH0A0HYM2", 120)
    ig_series = get_fred("BAMLC0A0CM",   120)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card("HYG  하이일드ETF", f"${f(hyg_val,2)}", hyg_chg), unsafe_allow_html=True)
        spark(hyg_h, "#8B5CF6")
        if st.button("HYG 상세 보기 →", key="btn_HYG"):
            st.session_state.selected_indicator = "HYG"
            st.rerun()
    with c2:
        st.markdown(card("LQD  투자등급ETF", f"${f(lqd_val,2)}", lqd_chg), unsafe_allow_html=True)
        spark(lqd_h, "#3B82F6")
    with c3:
        hy_last = float(hy_series.iloc[-1]) if hy_series is not None else None
        hy_prev = float(hy_series.iloc[-2]) if hy_series is not None and len(hy_series) > 1 else None
        hy_chg  = (hy_last - hy_prev) / abs(hy_prev) * 100 if hy_last and hy_prev else None
        st.markdown(card("HY OAS  스프레드", f(hy_last,2,suf="%"), hy_chg), unsafe_allow_html=True)
        spark(hy_series, "#EF4444", is_series=True)
        if st.button("HY OAS 상세 보기 →", key="btn_HY_OAS"):
            st.session_state.selected_indicator = "HY_OAS"
            st.rerun()
    with c4:
        ig_last = float(ig_series.iloc[-1]) if ig_series is not None else None
        ig_prev = float(ig_series.iloc[-2]) if ig_series is not None and len(ig_series) > 1 else None
        ig_chg  = (ig_last - ig_prev) / abs(ig_prev) * 100 if ig_last and ig_prev else None
        st.markdown(card("IG OAS  투자등급", f(ig_last,2,suf="%"), ig_chg), unsafe_allow_html=True)
        spark(ig_series, "#10B981", is_series=True)

    # 상세 패널 (HYG / HY_OAS)
    if st.session_state.selected_indicator in ["HYG","HY_OAS"]:
        render_detail_panel(st.session_state.selected_indicator)

    st.markdown("---")

    sec("📐", "금리 & 수익률 곡선")
    t10_val, t10_chg, t10_h = get_yf("^TNX", period="1y")
    t2_val,  t2_chg,  t2_h  = get_yf("^IRX", period="1y")
    t30_val, t30_chg, t30_h = get_yf("^TYX", period="1y")
    t10y2y_s = get_fred("T10Y2Y", 120)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(card("미국 10Y 국채", f(t10_val,3,suf="%"), t10_chg), unsafe_allow_html=True)
        spark(t10_h, "#00D4FF")
    with c2:
        st.markdown(card("미국 2Y 국채", f(t2_val,3,suf="%"), t2_chg), unsafe_allow_html=True)
        spark(t2_h, "#8B5CF6")
    with c3:
        st.markdown(card("미국 30Y 국채", f(t30_val,3,suf="%"), t30_chg), unsafe_allow_html=True)
        spark(t30_h, "#F59E0B")
    with c4:
        sp_last = float(t10y2y_s.iloc[-1]) if t10y2y_s is not None else None
        sp_prev = float(t10y2y_s.iloc[-2]) if t10y2y_s is not None and len(t10y2y_s) > 1 else None
        sp_chg  = (sp_last - sp_prev) if sp_last and sp_prev else None
        inv     = "🔴역전" if sp_last and sp_last < 0 else "🟢정상"
        st.markdown(card("장단기금리차 10Y-2Y", f(sp_last,3,suf="%"), sub=inv), unsafe_allow_html=True)
        spark(t10y2y_s, "#10B981", is_series=True)
        if st.button("금리차 상세 보기 →", key="btn_T10Y2Y"):
            st.session_state.selected_indicator = "T10Y2Y"
            st.rerun()

    # 상세 패널
    if st.session_state.selected_indicator == "T10Y2Y":
        render_detail_panel("T10Y2Y")

    # 수익률 곡선 차트
    st.markdown("---")
    sec("📈", "수익률 곡선 (현재 vs 1년전)")
    maturities = ["1M","3M","6M","1Y","2Y","3Y","5Y","7Y","10Y","20Y","30Y"]
    tickers_yc  = ["^IRX","^IRX","^IRX","^FVX","^IRX","^FVX","^FVX","^TNX","^TNX","^TYX","^TYX"]
    # 실제 미국채 수익률 — yfinance 직접 조회
    yc_tickers = {
        "1M":"^IRX","3M":"^IRX","6M":"^IRX","1Y":"^FVX",
        "2Y":"^IRX","5Y":"^FVX","10Y":"^TNX","30Y":"^TYX"
    }
    yc_data = {}
    for mat, tk in yc_tickers.items():
        v, _, h2 = get_yf(tk, period="1y")
        if v:
            yc_data[mat] = {"now": v, "prev": float(h2["Close"].iloc[0]) if h2 is not None and not h2.empty else v}

    if yc_data:
        mats_plot = list(yc_data.keys())
        now_vals  = [yc_data[m]["now"]  for m in mats_plot]
        prev_vals = [yc_data[m]["prev"] for m in mats_plot]
        fig_yc = go.Figure()
        fig_yc.add_trace(go.Scatter(x=mats_plot, y=now_vals,  mode="lines+markers",
                                    name="현재", line=dict(color="#00D4FF", width=2.5),
                                    marker=dict(size=8)))
        fig_yc.add_trace(go.Scatter(x=mats_plot, y=prev_vals, mode="lines+markers",
                                    name="1년전", line=dict(color="#FF5555", width=1.5, dash="dot"),
                                    marker=dict(size=6)))
        layout_yc = dict(CHART_LAYOUT)
        layout_yc["height"] = 280
        fig_yc.update_layout(**layout_yc)
        st.plotly_chart(fig_yc, use_container_width=True, config={"displayModeBar":False})


# ═══════════════════════════════════════════════════════════
#  TAB 3 — 유동성 & 연준
# ═══════════════════════════════════════════════════════════

with tab3:

    sec("🏦", "연준 대차대조표")
    walcl_s    = get_fred("WALCL",     60)
    wrbwfrbl_s = get_fred("WRBWFRBL",  60)
    wtregen_s  = get_fred("WTREGEN",   60)
    rrp_s      = get_fred("RRPONTSYD", 60)
    wrmfsl_s   = get_fred("WRMFSL",    60)

    def fred_last(s):
        if s is not None and len(s) > 0:
            v = float(s.iloc[-1])
            p = float(s.iloc[-2]) if len(s) > 1 else v
            c = (v - p) / abs(p) * 100 if p != 0 else 0
            return v, c
        return None, None

    walcl_v,    walcl_c    = fred_last(walcl_s)
    wrbwfrbl_v, wrbwfrbl_c = fred_last(wrbwfrbl_s)
    wtregen_v,  wtregen_c  = fred_last(wtregen_s)
    rrp_v,      rrp_c      = fred_last(rrp_s)
    wrmfsl_v,   wrmfsl_c   = fred_last(wrmfsl_s)

    c1, c2, c3 = st.columns(3)
    with c1:
        display_v = f"${walcl_v/1e6:,.2f}T" if walcl_v else "N/A"
        st.markdown(card("연준 총자산 (WALCL)", display_v, walcl_c,
                         sub="단위: 백만 달러"), unsafe_allow_html=True)
        spark(walcl_s, "#3B82F6", is_series=True)
        if st.button("연준 총자산 상세 →", key="btn_WALCL"):
            st.session_state.selected_indicator = "WALCL"
            st.rerun()
    with c2:
        display_v = f"${wrbwfrbl_v/1e6:,.2f}T" if wrbwfrbl_v else "N/A"
        st.markdown(card("지급준비금 (WRBWFRBL)", display_v, wrbwfrbl_c,
                         sub="단위: 백만 달러"), unsafe_allow_html=True)
        spark(wrbwfrbl_s, "#10B981", is_series=True)
        if st.button("준비금 상세 →", key="btn_WRBWFRBL"):
            st.session_state.selected_indicator = "WRBWFRBL"
            st.rerun()
    with c3:
        display_v = f"${wtregen_v/1e3:,.1f}B" if wtregen_v else "N/A"
        st.markdown(card("TGA 재무부계정 (WTREGEN)", display_v, wtregen_c,
                         sub="단위: 백만 달러"), unsafe_allow_html=True)
        spark(wtregen_s, "#F59E0B", is_series=True)
        if st.button("TGA 상세 →", key="btn_WTREGEN"):
            st.session_state.selected_indicator = "WTREGEN"
            st.rerun()

    # 상세 패널
    if st.session_state.selected_indicator in ["WALCL","WRBWFRBL","WTREGEN"]:
        render_detail_panel(st.session_state.selected_indicator)

    st.markdown("---")

    c1, c2 = st.columns(2)
    with c1:
        display_v = f"${rrp_v/1e3:,.1f}B" if rrp_v else "N/A"
        st.markdown(card("역레포 (ON RRP)", display_v, rrp_c,
                         sub="단위: 백만 달러"), unsafe_allow_html=True)
        spark(rrp_s, "#EC4899", is_series=True)
        if st.button("역레포 상세 →", key="btn_RRPONTSYD"):
            st.session_state.selected_indicator = "RRPONTSYD"
            st.rerun()
    with c2:
        display_v = f"${wrmfsl_v/1e6:,.2f}T" if wrmfsl_v else "N/A"
        st.markdown(card("MMF 총잔고 (WRMFSL)", display_v, wrmfsl_c,
                         sub="단위: 백만 달러"), unsafe_allow_html=True)
        spark(wrmfsl_s, "#06B6D4", is_series=True)
        if st.button("MMF 상세 →", key="btn_WRMFSL"):
            st.session_state.selected_indicator = "WRMFSL"
            st.rerun()

    # 상세 패널
    if st.session_state.selected_indicator in ["RRPONTSYD","WRMFSL"]:
        render_detail_panel(st.session_state.selected_indicator)

    # ── 연준 유동성 통합 차트 ──
    st.markdown("---")
    sec("📊", "연준 유동성 구성 차트")
    if walcl_s is not None and wrbwfrbl_s is not None:
        fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
        if walcl_s is not None:
            fig_liq.add_trace(go.Scatter(
                x=walcl_s.index, y=walcl_s.values,
                name="연준 총자산", line=dict(color="#3B82F6", width=2.5)
            ), secondary_y=False)
        if wrbwfrbl_s is not None:
            fig_liq.add_trace(go.Scatter(
                x=wrbwfrbl_s.index, y=wrbwfrbl_s.values,
                name="지급준비금", line=dict(color="#10B981", width=2)
            ), secondary_y=False)
        if rrp_s is not None:
            fig_liq.add_trace(go.Scatter(
                x=rrp_s.index, y=rrp_s.values,
                name="역레포(RRP)", line=dict(color="#EC4899", width=1.8, dash="dot")
            ), secondary_y=True)
        layout_liq = dict(CHART_LAYOUT)
        layout_liq["height"] = 360
        fig_liq.update_layout(**layout_liq)
        fig_liq.update_yaxes(title_text="백만 달러 (총자산/준비금)", secondary_y=False,
                             tickfont=dict(size=10, family="IBM Plex Mono"), color="#4A6A8A")
        fig_liq.update_yaxes(title_text="백만 달러 (역레포)", secondary_y=True,
                             tickfont=dict(size=10, family="IBM Plex Mono"), color="#EC4899")
        st.plotly_chart(fig_liq, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("FRED 데이터를 불러오는 중입니다...")


# ═══════════════════════════════════════════════════════════
#  TAB 4 — 주요 자산
# ═══════════════════════════════════════════════════════════

with tab4:

    sec("🏦", "미국 섹터 ETF")
    sector_etfs = [
        ("기술",    "XLK", "#8B5CF6"),
        ("금융",    "XLF", "#3B82F6"),
        ("에너지",  "XLE", "#F59E0B"),
        ("헬스케어","XLV", "#10B981"),
        ("필수소비","XLP", "#EC4899"),
        ("유틸리티","XLU", "#06B6D4"),
        ("산업재",  "XLI", "#EF4444"),
        ("부동산",  "XLRE","#22D98A"),
    ]
    cols = st.columns(4)
    for i, (name, ticker, color) in enumerate(sector_etfs):
        with cols[i % 4]:
            val, chg, hist = get_yf(ticker)
            st.markdown(card(f"{name} ({ticker})", f"${f(val,2)}", chg), unsafe_allow_html=True)
            spark(hist, color)

    st.markdown("---")
    sec("🌍", "글로벌 ETF")
    global_etfs = [
        ("미국 S&P", "SPY",  "#00D4FF"),
        ("신흥국",   "EEM",  "#F59E0B"),
        ("유럽",     "VGK",  "#10B981"),
        ("중국",     "FXI",  "#EF4444"),
        ("일본",     "EWJ",  "#8B5CF6"),
        ("한국",     "EWY",  "#EC4899"),
        ("인도",     "INDA", "#22D98A"),
        ("브라질",   "EWZ",  "#3B82F6"),
    ]
    cols = st.columns(4)
    for i, (name, ticker, color) in enumerate(global_etfs):
        with cols[i % 4]:
            val, chg, hist = get_yf(ticker)
            st.markdown(card(f"{name} ({ticker})", f"${f(val,2)}", chg), unsafe_allow_html=True)
            spark(hist, color)

    st.markdown("---")

    # 주요 자산 6개월 성과 비교 차트
    sec("📈", "주요 자산 6개월 성과 비교")
    perf_tickers = {
        "S&P 500":  "^GSPC",
        "금":       "GC=F",
        "10Y 국채": "^TNX",
        "HYG":      "HYG",
        "달러지수": "DX-Y.NYB",
        "BTC":      "BTC-USD",
    }
    perf_colors = ["#00D4FF","#FFCC44","#10B981","#8B5CF6","#EF4444","#F59E0B"]

    fig_perf = go.Figure()
    for (name, ticker), color in zip(perf_tickers.items(), perf_colors):
        _, _, hist = get_yf(ticker, period="6mo")
        if hist is not None and not hist.empty:
            base = hist["Close"].iloc[0]
            norm = (hist["Close"] / base - 1) * 100
            fig_perf.add_trace(go.Scatter(
                x=hist.index, y=norm.values,
                mode="lines", name=name,
                line=dict(color=color, width=2),
            ))

    fig_perf.add_hline(y=0, line_dash="dash", line_color="#2A3A4F", line_width=1)
    layout_perf = dict(CHART_LAYOUT)
    layout_perf["height"] = 380
    layout_perf["yaxis"] = dict(
        gridcolor="#141E2E", color="#4A6A8A", showgrid=True,
        tickfont=dict(size=11, family="IBM Plex Mono"),
        ticksuffix="%"
    )
    fig_perf.update_layout(**layout_perf)
    st.plotly_chart(fig_perf, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════
#  TAB 5 — 글로벌 경제
# ═══════════════════════════════════════════════════════════

with tab5:

    sec("📉", "미국 경제지표 (FRED)")

    fred_indicators = [
        ("UNRATE",    "실업률",         "%",  "#EF4444", 24),
        ("CPIAUCSL",  "CPI (소비자물가)","",  "#F59E0B", 24),
        ("PCEPI",     "PCE 물가지수",   "",   "#EC4899", 24),
        ("FEDFUNDS",  "연방기금금리",   "%",  "#00D4FF", 24),
        ("GDPC1",     "실질 GDP",       "B$", "#10B981", 20),
        ("INDPRO",    "산업생산지수",   "",   "#8B5CF6", 24),
        ("RSXFS",     "소매판매",       "M$", "#3B82F6", 24),
        ("UMCSENT",   "미시간 소비심리","",   "#22D98A", 24),
    ]

    cols = st.columns(4)
    for i, (sid, name, suf, color, limit) in enumerate(fred_indicators):
        with cols[i % 4]:
            s = get_fred(sid, limit)
            if s is not None and len(s) > 0:
                last_v = float(s.iloc[-1])
                prev_v = float(s.iloc[-2]) if len(s) > 1 else last_v
                chg_v  = (last_v - prev_v) / abs(prev_v) * 100 if prev_v != 0 else 0
                st.markdown(card(name, f(last_v, 2, suf=suf), chg_v), unsafe_allow_html=True)
                spark(s, color, is_series=True)
            else:
                st.markdown(card(name, "N/A"), unsafe_allow_html=True)

    st.markdown("---")
    sec("🌍", "주요 중앙은행 정책금리")

    cb_rates = {
        "미국 (연준)":  ("FEDFUNDS", "#00D4FF"),
        "유로존 (ECB)": ("ECBDFR",   "#10B981"),
    }
    c1, c2 = st.columns(2)
    cols_cb = [c1, c2]
    for i, (name, (sid, color)) in enumerate(cb_rates.items()):
        with cols_cb[i]:
            s = get_fred(sid, 60)
            if s is not None:
                last_v = float(s.iloc[-1])
                prev_v = float(s.iloc[-2]) if len(s) > 1 else last_v
                chg_v  = last_v - prev_v
                st.markdown(card(name, f"{last_v:.2f}%"), unsafe_allow_html=True)
                spark(s, color, is_series=True)
            else:
                st.markdown(card(name, "N/A"), unsafe_allow_html=True)

    st.markdown("---")
    sec("📊", "미국 경기 사이클 차트 (실업률 vs 금리)")
    unrate_s  = get_fred("UNRATE",   60)
    fedfunds_s= get_fred("FEDFUNDS", 60)
    cpi_s     = get_fred("CPIAUCSL", 60)

    if unrate_s is not None and fedfunds_s is not None:
        fig_cycle = make_subplots(specs=[[{"secondary_y": True}]])
        fig_cycle.add_trace(go.Scatter(
            x=fedfunds_s.index, y=fedfunds_s.values,
            name="연방기금금리", line=dict(color="#00D4FF", width=2.5)
        ), secondary_y=False)
        fig_cycle.add_trace(go.Scatter(
            x=unrate_s.index, y=unrate_s.values,
            name="실업률", line=dict(color="#EF4444", width=2)
        ), secondary_y=True)
        if cpi_s is not None:
            fig_cycle.add_trace(go.Scatter(
                x=cpi_s.index, y=cpi_s.pct_change(12)*100,
                name="CPI YoY%", line=dict(color="#F59E0B", width=1.8, dash="dot")
            ), secondary_y=True)
        layout_cycle = dict(CHART_LAYOUT)
        layout_cycle["height"] = 360
        fig_cycle.update_layout(**layout_cycle)
        fig_cycle.update_yaxes(
            title_text="금리 (%)", secondary_y=False,
            tickfont=dict(size=10, family="IBM Plex Mono"), color="#00D4FF"
        )
        fig_cycle.update_yaxes(
            title_text="실업률 / CPI (%)", secondary_y=True,
            tickfont=dict(size=10, family="IBM Plex Mono"), color="#EF4444"
        )
        st.plotly_chart(fig_cycle, use_container_width=True, config={"displayModeBar": False})
    else:
        st.info("FRED 데이터를 불러오는 중...")

    # 푸터
    st.markdown("---")
    st.markdown("""
    <div style="text-align:center; padding:20px 0; color:#2A3A4F; font-family:'IBM Plex Mono'; font-size:.72rem; font-weight:600; letter-spacing:.08em;">
        데이터 소스: Yahoo Finance · FRED (Federal Reserve Economic Data) · ICE BofA<br>
        본 대시보드는 정보 제공 목적이며 투자 조언이 아닙니다.<br>
        © 2025 글로벌 매크로 대시보드
    </div>
    """, unsafe_allow_html=True)
