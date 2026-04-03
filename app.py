# ============================================================
#  글로벌 매크로 대시보드 — app.py (최종 버전)
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

/* ── 상세 패널 ── */
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
    <div class="kcard" onclick="document.getElementById('{label}').click()">
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
#  상세 패널 렌더링 함수
# ═══════════════════════════════════════════════════════════

def render_detail_panel(indicator_key):
    """선택된 지표에 대한 상세 패널 렌더링"""

    # ── 지표별 메타데이터 정의 ──
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
        },
        "WRMFSL": {
            "title": "MMF 총잔고",
            "subtitle": "FRED WRMFSL · Money Market Fund Total Assets",
            "color": "#06B6D4",
            "fred_id": "WRMFSL",
            "is_fred": True,
            "what": "머니마켓펀드(MMF)에 쌓인 총 자금입니다. 불확실성이 클수록 투자자들이 MMF로 피신합니다. MMF 잔고가 사상 최고치라면 '현금 대기 중' 상태로, 향후 증
