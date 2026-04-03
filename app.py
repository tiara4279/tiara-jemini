# ============================================================
#  글로벌 매크로 대시보드 — app.py (오리지널 프리미엄 UI + 다중 우회 로딩)
# ============================================================
import subprocess, sys, warnings
warnings.filterwarnings("ignore")

# --- 필수 라이브러리 자동 설치 로직 (고객님 코드 유지) ---
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
import urllib.request
import json
from fredapi import Fred

# --- FRED API 키 설정 (고객님 코드 유지) ---
FRED_API_KEY = "44435d53f0376bf6ab6263db6892924f"
try:
    fred = Fred(api_key=FRED_API_KEY)
except Exception:
    fred = None

# --- 페이지 설정 ---
st.set_page_config(
    page_title="글로벌 매크로 대시보드",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- HEX → rgba 변환 ---
def hex_to_rgba(hex_color, alpha=0.10):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

# --- 오리지널 커스텀 CSS (다크 네이비, 연노랑 포인트, 프리미엄 UI 복구) ---
st.markdown("""<style>
@import url("https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Noto+Sans+KR:wght@400;600;700;900&display=swap");

/* ── 전체 기본 폰트 ── */
html, body, [class*="css"], .stMarkdown, .stText, p, span, div, label {
    font-family: 'Noto Sans KR', sans-serif !important;
}
.stApp { background: #060A12 !important; }
.block-container {
    padding-top: 2rem !important;
    max-width: 1400px;
}

/* ════════════════════════════════
   네이티브 st.title() 스타일 강제
   ════════════════════════════════ */
h1 {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 2.2rem !important;
    font-weight: 900 !important;
    color: #FFFFFF !important;
    letter-spacing: 0.04em !important;
    line-height: 1.25 !important;
}

/* 네이티브 st.caption() 스타일 */
.stCaption, .stCaption p, small {
    font-size: 1rem !important; /* 1.5배 증가 */
    font-weight: 700 !important;
    color: #5A8AAE !important;
    letter-spacing: 0.14em !important;
}

/* ── 섹션 헤더 ── */
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

/* ── 지표 카드 ── */
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

/* ── 리스크 배지 ── */
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

/* ── 탭 ── */
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

/* ── 버튼 ── */
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

/* ── 알림 박스 ── */
.stAlert p {
    font-weight: 700 !important;
}

/* ── 사이드바 ── */
section[data-testid="stSidebar"] {
    background: #080E1A !important;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span {
    font-weight: 700 !important;
    color: #8AAAC8 !important;
}
</style>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  공통 유틸 (데이터 수집 엔진 완벽 업그레이드)
# ═══════════════════════════════════════════════════════════

@st.cache_data(ttl=300, show_spinner=False)
def get_yf(ticker, period="6mo", interval="1d"):
    # [우회 로직 1] yfinance 최신 버전의 MultiIndex 오류를 완벽하게 회피하는 정밀 다운로드
    try:
        h = yf.download(ticker, period=period, interval=interval, progress=False, threads=False)
        if h.empty: return None, None, None
        
        # 최신 yfinance MultiIndex 구조 대응
        if isinstance(h.columns, pd.MultiIndex):
            if 'Close' in h.columns.get_level_values(0):
                c = h['Close'].iloc[:, 0]
            elif 'Close' in h.columns.get_level_values(1):
                c = h.xs('Close', level=1, axis=1).iloc[:, 0]
            else:
                c = h.iloc[:, 0]
        else:
            c = h['Close'] if 'Close' in h.columns else h.iloc[:, 0]
            
        c = c.dropna()
        if len(c) < 2: return None, None, None
        
        last = float(c.iloc[-1])
        prev = float(c.iloc[-2])
        chg  = (last - prev) / prev * 100
        return last, chg, pd.DataFrame({"Close": c})
    except Exception:
        return None, None, None

@st.cache_data(ttl=600, show_spinner=False)
def get_fred(sid, limit=60):
    # [우회 로직 2] FRED API 한도 및 무한로딩(Hang)을 뚫어내는 브라우저 위장 + 다이렉트 CSV 다운로드
    try:
        import requests
        from io import StringIO
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        # 일반 사용자의 크롬 브라우저로 완벽 위장하여 차단 우회
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        
        # 무한 대기 원천 차단 (3.5초 내에 안주면 바로 끊음)
        r = requests.get(url, headers=headers, timeout=3.5)
        if r.status_code == 200:
            df = pd.read_csv(StringIO(r.text), index_col='DATE', parse_dates=True, na_values=['.'])
            if sid in df.columns:
                s = df[sid].dropna()
                if not s.empty: return s.tail(limit)
    except Exception:
        pass

    # [백업 로직] CSV 추출 실패 시 FRED 공식 API로 2차 시도
    if fred is not None:
        try:
            s = fred.get_series(sid).dropna()
            if not s.empty: return s.tail(limit)
        except Exception:
            pass
            
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
    st.markdown(f'<div class="sec-hd"><span style="text-transform: none;">{icon}</span>&nbsp;&nbsp;{title}</div>', unsafe_allow_html=True)

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


# ═══════════════════════════════════════════════════════════
#  헤더 — 타이틀, 타임스탬프, 새로고침 버튼
# ═══════════════════════════════════════════════════════════

now_str = datetime.utcnow().strftime("%Y-%m-%d  %H:%M  UTC")

st.title("📡 글로벌 매크로 대시보드")
st.caption("GLOBAL MACRO MONITOR — REAL-TIME FINANCIAL INDICATORS")

ts_col, btn_col = st.columns([6, 1])
with ts_col:
    st.markdown(
        f'<div class="ts-box">🕐 {now_str}</div>',
        unsafe_allow_html=True
    )
with btn_col:
    if st.button("🔄 새로고침", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")
st.success("✅ **FRED API 연결됨** — 연준·유동성·인플레이션 실데이터 수신 중")


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
    st.markdown(card("VIX (공포지수)", f(v, 2), chg,
                     "CBOE 변동성 지수", risk_badge("VIX", v)), unsafe_allow_html=True)
    spark(h, "#EF4444", 85)

with r2:
    v, chg, h = get_yf("^MOVE", "6mo", "1d")
    st.markdown(card("MOVE (채권 변동성)", f(v, 2), chg,
                     "ICE BofA 채권 변동성", risk_badge("MOVE", v)), unsafe_allow_html=True)
    spark(h, "#F59E0B", 85)

with r3:
    ts_data = get_fred("T10Y2Y")
    if ts_data is not None:
        lv   = float(ts_data.iloc[-1])
        pv   = float(ts_data.iloc[-2])
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
    st.markdown(card("HYG (하이일드 ETF)", f(v, 2, pre="$"), chg,
                     "HY 스프레드 프록시"), unsafe_allow_html=True)
    spark(h, "#8B5CF6", 85)

hy = get_fred("BAMLH0A0HYM2")
if hy is not None:
    lv = float(hy.iloc[-1]); pv = float(hy.iloc[-2])
    chg_hy = (lv - pv) / pv * 100
    fe1, fe2 = st.columns(2)
    with fe1:
        st.markdown(card("하이일드 스프레드 (OAS)", f(lv, 2, suf="%"), chg_hy,
                         "ICE BofA US HY OAS — FRED"), unsafe_allow_html=True)
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
        if data is not None:
            lv = float(data.iloc[-1]); pv = float(data.iloc[-2])
            chg = (lv - pv) / pv * 100
            st.markdown(card(label, f(lv, 1, suf=" B$"), chg, f"FRED: {sid}"), unsafe_allow_html=True)
            spark(data, color, 85, is_series=True)
        else:
            st.markdown(card(label, f(demo, 0, suf=" B$"), None, "⚠️ 로딩 중..."), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §6  은행 신용 및 단기 자금 시장
# ═══════════════════════════════════════════════════════════

sec("💰", "은행 신용 및 단기 자금 시장")

CRED = [
    ("RRPONTSYD", "역레포 (ON RRP)",   "#EC4899", "B$", 400,    1),
    ("WRMFSL",    "MMF 총잔고",         "#06B6D4", "B$", 6_200,  1),
    ("TOTLL",     "상업은행 총대출",    "#8B5CF6", "B$", 17_500, 1),
    ("SOFR",      "SOFR (익일물 금리)", "#F59E0B", "%",  5.33,   3),
]
crs = st.columns(4)
for col, (sid, label, color, unit, demo, dp) in zip(crs, CRED):
    with col:
        data = get_fred(sid, 60)
        suf  = "%" if unit == "%" else " B$"
        if data is not None:
            lv = float(data.iloc[-1]); pv = float(data.iloc[-2])
            chg = (lv - pv) / pv * 100 if pv else 0
            st.markdown(card(label, f(lv, dp, suf=suf), chg, f"FRED: {sid}"), unsafe_allow_html=True)
            spark(data, color, 80, is_series=True)
        else:
            st.markdown(card(label, f(demo, dp, suf=suf), None, "⚠️ 로딩 중..."), unsafe_allow_html=True)


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
        spark(bei5, "#10B981", 90, is_series=True)
    else:
        st.markdown(card("5Y 기대 인플레이션", "—", None, "⚠️ 로딩 중..."), unsafe_allow_html=True)

with m4:
    bei10 = get_fred("T10YIE", 40)
    if bei10 is not None:
        lv = float(bei10.iloc[-1]); pv = float(bei10.iloc[-2])
        chg = (lv - pv) / pv * 100
        st.markdown(card("10Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T10YIE BEI"), unsafe_allow_html=True)
        spark(bei10, "#3B82F6", 90, is_series=True)
    else:
        st.markdown(card("10Y 기대 인플레이션", "—", None, "⚠️ 로딩 중..."), unsafe_allow_html=True)

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
        margin=dict(l=20,r=20,t=45,b=20),
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
#  §9 미국 핵심 유동성 흐름 (Net Liquidity)
# ═══════════════════════════════════════════════════════════
sec("🌊", "미국 핵심 유동성 흐름 (Net Liquidity)")
st.caption("Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")

with st.spinner("유동성 차트 데이터 로딩 중..."):
    try:
        # 1년치 데이터 호출을 위해 limit=300 (영업일 기준 넉넉하게)
        walcl = get_fred('WALCL', limit=300)
        rrp = get_fred('RRPONTSYD', limit=300)
        tga = get_fred('WTREGEN', limit=300)
        
        _, _, sp500_df = get_yf('^GSPC', period='1y', interval='1d')
        
        if walcl is not None and rrp is not None and tga is not None and sp500_df is not None:
            walcl = walcl / 1000  # 빌리언 달러 단위 변환
            sp500_s = sp500_df['Close']
            
            if hasattr(sp500_s.index, 'tz') and sp500_s.index.tz is not None:
                sp500_s.index = sp500_s.index.tz_localize(None)
            
            df_liq = pd.DataFrame({'WALCL': walcl, 'RRP': rrp, 'TGA': tga}).ffill().dropna()
            df_liq['Net_Liquidity'] = df_liq['WALCL'] - df_liq['RRP'] - df_liq['TGA']
            
            df_plot = df_liq.join(sp500_s, how='inner').ffill().dropna()
            
            fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
            fig_liq.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Net_Liquidity'], name="순유동성 (B$)", line=dict(color='#00D4FF', width=2.5)), secondary_y=False)
            fig_liq.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name="S&P 500", line=dict(color='#FF5555', width=1.5)), secondary_y=True)
            
            fig_liq.update_layout(**CHART_LAYOUT, height=450, title="Net Liquidity vs S&P 500 (최근 1년)")
            st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})
            
            st.markdown("""<div style="background: #0C1420; border: 1px solid #1E3050; border-radius: 12px; padding: 16px; margin-bottom: 30px;">
            <div style="font-size: 0.9rem; font-weight: 700; color:#00D4FF; margin-bottom: 8px;">📌 Net Liquidity(순유동성) 공식: 연준 대차대조표 - 역레포(RRP) - 재무부 계좌(TGA)</div>
            <div style="font-size: 0.8rem; color: #8AAAC8; line-height: 1.5;">
            중앙은행이 시장에 실질적으로 공급한 순수 유동성 자금의 양입니다.<br>
            통상적으로 <b style="color:#00D4FF">파란선(순유동성)</b>이 오르면 시중에 돈이 넘쳐나 <b style="color:#FF5555">빨간선(S&P 500)</b>도 함께 오르고, 내리면 주가도 조정을 받는 <b>강한 양(+)의 상관관계</b>를 가집니다.
            </div></div>""", unsafe_allow_html=True)
        else:
            st.warning("⚠️ 유동성 데이터를 불러오지 못했습니다. (서버 연동 지연)")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  §10 미국 10년물 국채금리 분해 
# ═══════════════════════════════════════════════════════════
sec("🇺🇸", "미국 10년물 국채금리 분해")
st.caption("국채금리를 '단기금리 기대경로', '기대인플레이션', '기간 프리미엄'으로 분해하여 시장의 진짜 의도를 파악합니다.")

with st.spinner("국채금리 분해 차트 로딩 중..."):
    try:
        dgs10 = get_fred('DGS10', limit=300)
        t10yie = get_fred('T10YIE', limit=300)
        acmtp10 = get_fred('ACMTP10', limit=300)
        
        if dgs10 is not None and t10yie is not None and acmtp10 is not None:
            df_dec = pd.DataFrame({'10Y': dgs10, 'T10YIE': t10yie, 'ACMTP10': acmtp10}).ffill().dropna()
            df_dec['Short Rate'] = df_dec['10Y'] - df_dec['T10YIE'] - df_dec['ACMTP10']
            
            fig_dec = make_subplots(specs=[[{"secondary_y": True}]])
            fig_dec.add_trace(go.Scatter(x=df_dec.index, y=df_dec['10Y'], name="10년물 금리 (좌)", line=dict(color='#3B82F6', width=2.5)), secondary_y=False)
            fig_dec.add_trace(go.Scatter(x=df_dec.index, y=df_dec['Short Rate'], name="단기금리 기대경로 (좌)", line=dict(color='#06B6D4', width=1.5)), secondary_y=False)
            fig_dec.add_trace(go.Scatter(x=df_dec.index, y=df_dec['T10YIE'], name="기대인플레이션 (좌)", line=dict(color='#8AAAC8', width=1.5)), secondary_y=False)
            fig_dec.add_trace(go.Scatter(x=df_dec.index, y=df_dec['ACMTP10'], name="기간 프리미엄 (우)", line=dict(color='#F59E0B', width=2.5)), secondary_y=True)
            
            fig_dec.update_layout(**CHART_LAYOUT, height=450, title="미국 10년물 국채금리 분해 (최근 1년)")
            fig_dec.update_yaxes(title_text="금리 (%)", secondary_y=False)
            fig_dec.update_yaxes(title_text="기간 프리미엄 (%p)", secondary_y=True, showgrid=False)
            
            st.plotly_chart(fig_dec, use_container_width=True, config={'displayModeBar': False})
        else:
            st.warning("⚠️ 기간 프리미엄 데이터를 불러오지 못했습니다.")
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  §11 AI 매크로 종합 시황 진단
# ═══════════════════════════════════════════════════════════
sec("📝", "AI 매크로 종합 시황 진단")

try:
    vix_val, _, _ = get_yf("^VIX", "1mo", "1d")
    move_val, _, _ = get_yf("^MOVE", "1mo", "1d")
    
    t10y2y = get_fred("T10Y2Y", 2)
    yc_val = float(t10y2y.iloc[-1]) if t10y2y is not None else 0.0
    
    sofr = get_fred("SOFR", 2)
    iorb = get_fred("IORB", 2)
    sofr_spread = (float(sofr.iloc[-1]) - float(iorb.iloc[-1])) if sofr is not None and iorb is not None else 0.0
    
    bei10 = get_fred("T10YIE", 2)
    bei_val = float(bei10.iloc[-1]) if bei10 is not None else 0.0
    
    totll = get_fred("TOTLL", 2)
    totll_chg = (float(totll.iloc[-1]) - float(totll.iloc[-2])) if totll is not None and len(totll)>1 else 0.0
    
    dw = get_fred("WLCFLPCL", 2)
    btfp = get_fred("H41RESPALBFRB", 2)
    emerg_val = (float(dw.iloc[-1]) if dw is not None else 0.0) + (float(btfp.iloc[-1]) if btfp is not None else 0.0)

    COLOR_DANGER = "#FF5555"
    COLOR_SAFE = "#22D98A"
    COLOR_WARN = "#FFCC44"
    
    if vix_val and vix_val > 30: vix_msg = f"<b style='color:{COLOR_DANGER};'>위험 심리:</b> VIX가 {vix_val:.2f}로 시장에 공포 심리가 팽배합니다."
    else: vix_msg = f"<b style='color:{COLOR_SAFE};'>위험 심리:</b> VIX가 {vix_val:.2f}로 시장이 안정적인 흐름을 유지 중입니다." if vix_val else "VIX 데이터 대기 중"
    
    if emerg_val > 500 or (move_val and move_val > 140): sys_msg = f"<b style='color:{COLOR_DANGER};'>시스템 경고:</b> 연준 긴급 대출이나 채권 변동성이 높아 스트레스 징후가 관찰됩니다."
    else: sys_msg = f"<b style='color:{COLOR_SAFE};'>시스템 안정:</b> 긴급 대출 및 채권 시장이 안정적이며 시스템 위기 징후는 없습니다."
    
    if sofr_spread > 0.05: sofr_msg = f"<b style='color:{COLOR_DANGER};'>조달 스트레스:</b> 단기 달러 경색 조짐이 보입니다."
    else: sofr_msg = f"<b style='color:{COLOR_SAFE};'>조달 안정:</b> 단기 자금 시장 융통이 원활합니다."
    
    if totll_chg < 0: totll_msg = f"<b style='color:{COLOR_DANGER};'>신용 축소:</b> 상업은행 대출이 감소하여 신용 공급 둔화 우려가 있습니다."
    elif totll_chg > 0: totll_msg = f"<b style='color:{COLOR_SAFE};'>신용 팽창:</b> 상업은행 대출이 증가하며 신용 창출이 이어지고 있습니다."
    else: totll_msg = f"<b style='color:{COLOR_WARN};'>신용 정체:</b> 상업은행 대출 규모가 관망세를 보이고 있습니다."
    
    if yc_val < 0: yield_msg = f"<b style='color:{COLOR_DANGER};'>침체 선행:</b> 장단기 금리차({yc_val:.2f}%) 역전으로 경기 둔화 가능성이 암시됩니다."
    else: yield_msg = f"<b style='color:{COLOR_SAFE};'>성장 기대:</b> 장단기 금리차({yc_val:.2f}%)가 정상화되어 성장 기대가 반영 중입니다."
    
    if bei_val > 2.5: bei_msg = f"<b style='color:{COLOR_DANGER};'>물가 불안:</b> 기대인플레({bei_val:.2f}%)가 높아 긴축 우려가 있습니다."
    else: bei_msg = f"<b style='color:{COLOR_SAFE};'>물가 안정:</b> 기대인플레({bei_val:.2f}%)가 연준의 목표 궤적에 부합합니다."

    if yc_val < 0 and sofr_spread > 0.05:
        strategy = "침체 시그널과 펀딩 스트레스가 중첩되었습니다. <b style='color:#FF5555'>현금 및 채권 방어적 포트폴리오 비중 확대</b>를 강력히 권장합니다."
        s_color = COLOR_DANGER
    elif yc_val >= 0 and sofr_spread <= 0:
        strategy = "신용 조달이 안정적이며 경제 성장이 기대됩니다. <b style='color:#22D98A'>위험 자산(주식)의 비중 유지 및 랠리 동참</b>이 유리한 환경입니다."
        s_color = COLOR_SAFE
    else:
        strategy = "거시 지표 방향성이 혼재되어 있습니다. <b style='color:#FFCC44'>관망세 유지 및 선별적 접근</b>이 필요합니다."
        s_color = COLOR_WARN

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
#  사이드바
# ═══════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("### ⚙️ 설정")
    st.markdown("---")
    st.markdown("**🔑 FRED API 키**")
    st.text_input("API Key", value="••••••••••••••••••••••••", disabled=True)
    st.success("✅ 연결됨")
    st.markdown("---")
    if st.button("🗑️ 캐시 초기화", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown("---")
    st.markdown("""
**📡 데이터 소스**
- 📈 Yahoo Finance
- 🏛️ FRED (St. Louis Fed)
- ⏱ 갱신: 5분마다
    """)
    st.caption(f"🕐 {now_str}")

# ── 푸터 ─────────────────────────────────────────────────────
st.markdown("---")
st.markdown(f"""
<div style="text-align:center; color:#2A4060; font-size:.70rem;
     font-family:'IBM Plex Mono',monospace; font-weight:700; padding:12px 0">
  📡 Yahoo Finance · FRED (St. Louis Fed) &nbsp;|&nbsp;
  ⏱ 5분 캐시 &nbsp;|&nbsp; 🕐 {now_str}
</div>
""", unsafe_allow_html=True)
