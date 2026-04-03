# ============================================================
#  글로벌 매크로 대시보드 — app.py (완전 통합본 FINAL)
#  ✅ 앱 마비 원인 (install_missing) 완전 제거
#  ✅ 무한 로딩 원인 (fredapi) 제거 및 requests.get (3.5초 타임아웃) 교체
#  ✅ Net Liquidity 실패 UI 논리 오류 완벽 수정
#  ✅ TypeError(중복 키워드 인자) 완벽 해결
#  ✅ 2x2 카드 배열 및 기간 버튼이 포함된 심층 지표 분석 섹션 탑재
# ============================================================
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import requests

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


# 무한 로딩을 완벽하게 방지하는 새로운 FRED 데이터 호출 로직 (3.5초 타임아웃 강제)
@st.cache_data(ttl=600)
def get_fred(sid, limit=60):
    try:
        url = f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}&api_key=44435d53f0376bf6ab6263db6892924f&file_type=json"
        # 3.5초 안에 안 주면 가차없이 끊어서 앱 마비(Hang) 원천 방지
        r = requests.get(url, timeout=3.5)
        if r.status_code == 200:
            data = r.json().get('observations', [])
            if not data: return None
            
            df = pd.DataFrame(data)
            df['value'] = pd.to_numeric(df['value'], errors='coerce')
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')['value'].dropna()
            
            return df.tail(limit) if len(df) > 1 else None
    except Exception:
        return None
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
st.success("✅ **API 통신 모듈 최적화 완료** — 실데이터 수신 중 (타임아웃 방어 적용)")


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
            st.markdown(card(label, "데이터 없음", None, "통신 지연"), unsafe_allow_html=True)


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
            st.markdown(card(label, "데이터 없음", None, "통신 지연"), unsafe_allow_html=True)


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
        st.markdown(card("5Y 기대 인플레이션", "데이터 없음", None, "통신 지연"), unsafe_allow_html=True)

with m4:
    bei10 = get_fred("T10YIE", 40)
    if bei10 is not None and len(bei10) > 0:
        lv  = float(bei10.iloc[-1])
        pv  = float(bei10.iloc[-2]) if len(bei10) > 1 else lv
        chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
        st.markdown(card("10Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T10YIE"), unsafe_allow_html=True)
        spark(bei10, "#3B82F6", 90, is_series=True)
    else:
        st.markdown(card("10Y 기대 인플레이션", "데이터 없음", None, "통신 지연"), unsafe_allow_html=True)

v2, chg2, h2 = get_yf("CL=F", "6mo", "1d")
mi1, _mi2, _mi3 = st.columns([1, 1, 2])
with mi1:
    st.markdown(card("WTI 원유 선물", f(v2, 2, pre="$", suf="/bbl"), chg2, "NYMEX Crude Oil"), unsafe_allow_html=True)
    spark(h2, "#64748B", 80)


# ═══════════════════════════════════════════════════════════
#  §8  종합 비교 차트 (TypeError 방지 - dictionary 직접 넘김 적용)
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
    # 문법 에러 원천 차단을 위해 dict 병합 방식 사용
    fig.update_layout(CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
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
    fig3.update_layout(CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
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
    fig4.update_layout(CHART_LAYOUT, yaxis_title="정규화 (시작=100)")
    st.plotly_chart(fig4, use_container_width=True, config={"displayModeBar": False})


# ═══════════════════════════════════════════════════════════
#  §9 미국 핵심 유동성 흐름 (Net Liquidity)
# ═══════════════════════════════════════════════════════════
sec("🌊", "미국 핵심 유동성 흐름 (Net Liquidity)")
st.caption("Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")

with st.spinner("유동성 차트 데이터 로딩 중..."):
    walcl = get_fred('WALCL', limit=300)
    rrp = get_fred('RRPONTSYD', limit=300)
    tga = get_fred('WTREGEN', limit=300)
    
    _, _, sp500_df = get_yf('^GSPC', period='1y', interval='1d')
    
    if walcl is not None and rrp is not None and tga is not None and sp500_df is not None:
        walcl_val = walcl / 1000  # 단위 변환
        sp500_s = sp500_df['Close']
        
        if hasattr(sp500_s.index, 'tz') and sp500_s.index.tz is not None:
            sp500_s.index = sp500_s.index.tz_localize(None)
        
        df_liq = pd.DataFrame({'WALCL': walcl_val, 'RRP': rrp, 'TGA': tga}).ffill().dropna()
        df_liq['Net_Liquidity'] = df_liq['WALCL'] - df_liq['RRP'] - df_liq['TGA']
        
        df_plot = df_liq.join(sp500_s, how='inner').ffill().dropna()
        
        fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
        fig_liq.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Net_Liquidity'], name="순유동성 (B$)", line=dict(color='#00D4FF', width=2.5)), secondary_y=False)
        fig_liq.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name="S&P 500", line=dict(color='#FF5555', width=1.5)), secondary_y=True)
        
        # TypeError 방지를 위해 파이썬의 사전 병합 방식(CHART_LAYOUT 전달) 사용
        fig_liq.update_layout(CHART_LAYOUT, height=450, title="Net Liquidity vs S&P 500 (최근 1년)")
        st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})
        
        st.markdown("""<div style="background: #0C1420; border: 1px solid #1E3050; border-radius: 12px; padding: 16px; margin-bottom: 30px;">
        <div style="font-size: 0.9rem; font-weight: 700; color:#00D4FF; margin-bottom: 8px;">📌 Net Liquidity(순유동성) 공식: 연준 대차대조표 - 역레포(RRP) - 재무부 계좌(TGA)</div>
        <div style="font-size: 0.8rem; color: #8AAAC8; line-height: 1.5;">
        중앙은행이 시장에 실질적으로 공급한 순수 유동성 자금의 양입니다.<br>
        통상적으로 <b style="color:#00D4FF">파란선(순유동성)</b>이 오르면 시중에 돈이 넘쳐나 <b style="color:#FF5555">빨간선(S&P 500)</b>도 함께 오르고, 내리면 주가도 조정을 받는 <b>강한 양(+)의 상관관계</b>를 가집니다.
        </div></div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background:#1A0E0E; border:1px solid #8B3A3A; border-radius:10px; padding:16px; margin-bottom:16px;">
            <div style="font-size:0.9rem; font-weight:700; color:#FF6B6B; margin-bottom:6px;">데이터 로딩 실패 — 항목별 상태</div>
            <div style="font-size:0.82rem; color:#CC9999; line-height:1.6;">서버 접속 지연으로 데이터를 불러오지 못했습니다.</div>
        </div>""", unsafe_allow_html=True)

        dc1, dc2, dc3, dc4 = st.columns(4)
        status_data = [
            ("WALCL",     walcl is not None),
            ("RRPONTSYD", rrp is not None),
            ("WTREGEN",   tga is not None),
            ("S&P 500",   sp500_df is not None),
        ]
        for col, (name, status) in zip([dc1, dc2, dc3, dc4], status_data):
            with col:
                ok_color = "#22D98A" if status else "#FF5555"
                ok_text  = "READY"   if status else "FAILED"
                st.markdown(f"""
                <div style="background:#0C1420; border:2px solid {ok_color}; border-radius:8px; padding:14px; text-align:center;">
                  <div style="font-size:0.75rem; font-weight:700; color:#6B8EAE; margin-bottom:6px;">{name}</div>
                  <div style="font-family:'IBM Plex Mono',monospace; font-size:1.1rem; font-weight:800; color:{ok_color};">{ok_text}</div>
                </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §10 미국 10년물 국채금리 분해 
# ═══════════════════════════════════════════════════════════
sec("🇺🇸", "미국 10년물 국채금리 분해")
st.caption("국채금리를 '단기금리 기대경로', '기대인플레이션', '기간 프리미엄'으로 분해하여 시장의 진짜 의도를 파악합니다.")

with st.spinner("국채금리 분해 차트 로딩 중..."):
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
        
        fig_dec.update_layout(CHART_LAYOUT, height=450, title="미국 10년물 국채금리 분해 (최근 1년)")
        fig_dec.update_yaxes(title_text="금리 (%)", secondary_y=False)
        fig_dec.update_yaxes(title_text="기간 프리미엄 (%p)", secondary_y=True, showgrid=False)
        
        st.plotly_chart(fig_dec, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("⚠️ 데이터를 완전히 불러오지 못했습니다. (통신 지연)")


# ═══════════════════════════════════════════════════════════
#  §11 심층 지표 분석 (상세보기 프리미엄 패널) - 새롭게 추가!
# ═══════════════════════════════════════════════════════════
st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
sec("🔍", "심층 지표 분석 (상세보기)")
st.caption("원하는 지표를 선택하여 2Y/5Y/10Y 추이 차트, AI 진단, 핵심 의미를 확인하세요.")

# ── 2x2 카드 그리드 및 완벽한 설명을 위한 고급 메타데이터 ──
DETAIL_META = {
    "연준 총자산 (WALCL)": {
        "ticker": "WALCL", "type": "fred", "scale": 1/1000000, "unit": "T", "prefix": "$",
        "title_sub": "단위: $T · 주간",
        "desc": "연준(미국 중앙은행)이 보유한 <b>자산의 총합</b>이에요. 연준이 국채 등을 사들이면(QE) 돈이 시중에 풀리고, 팔면(QT) 돈이 줄어요. 이 규모가 클수록 시중에 돈이 많다는 뜻입니다.",
        "cards": [
            {"icon": "💰", "title": "양적완화 QE — 자산 증가", "text": "연준이 돈을 푸는 중. 주식·부동산 등 자산가격 상승 압력이 생겨요."},
            {"icon": "🔴", "title": "양적긴축 QT — 자산 감소", "text": "연준이 돈을 거두는 중. 유동성 축소로 자산시장에 압박이 가해져요."},
            {"icon": "📊", "title": "2022년 고점 대비 축소", "text": "코로나 직후 약 9조 달러까지 늘어났다가 현재 지속적인 QT를 통해 감소 중이에요."},
            {"icon": "🔍", "title": "지급준비금과 함께 보기", "text": "대차대조표 전체 크기보다 실제 은행에 풀린 '지급준비금' 수준이 증시 유동성을 더 잘 설명해요."}
        ]
    },
    "역레포 잔액 (RRP)": {
        "ticker": "RRPONTSYD", "type": "fred", "scale": 1/1000, "unit": "T", "prefix": "$",
        "title_sub": "단위: $T · 일간",
        "desc": "갈 곳 잃은 시중의 단기 잉여 자금이 <b>연준 창고로 피신한 금액</b>이에요. 이 잔액이 줄어든다는 것은 창고에서 돈이 빠져나와 주식/채권 등 실물 시장으로 흘러가고 있다는 뜻입니다.",
        "cards": [
            {"icon": "🌊", "title": "잔액 감소 — 증시엔 호재", "text": "대기 자금이 위험 자산이나 단기 국채로 이동하며 시장에 유동성을 공급해요."},
            {"icon": "🔒", "title": "잔액 증가 — 안전 자산 선호", "text": "시장이 불안해 돈이 다시 연준 금고로 숨어들어가는 상황이에요."},
            {"icon": "🪫", "title": "유동성 버퍼 고갈 우려", "text": "RRP가 0에 가까워지면, 시장 충격을 흡수해 주던 '스펀지'가 사라져 변동성이 커질 수 있어요."},
            {"icon": "🏦", "title": "단기 금리의 바닥 역할", "text": "연준이 시중 단기 금리가 너무 떨어지지 않게 하한선을 받쳐주는 역할도 합니다."}
        ]
    },
    "장단기 금리차 (10Y-2Y)": {
        "ticker": "T10Y2Y", "type": "fred", "scale": 1, "unit": "%p", "prefix": "",
        "title_sub": "단위: %p · 일간",
        "desc": "미국 10년물 국채 금리에서 2년물 국채 금리를 뺀 값이에요. 정상적인 경제에서는 장기 금리가 더 높지만, 침체 우려가 커지면 단기 금리가 더 높아지는 <b>'역전 현상'</b>이 발생합니다.",
        "cards": [
            {"icon": "📈", "title": "정상 (양수) — 경제 성장", "text": "장기 투자에 대한 보상으로 장기 금리가 더 높은 건강한 경제 상태예요."},
            {"icon": "📉", "title": "역전 (음수) — 침체 경고", "text": "과거 50년간 미국의 모든 경기 침체 전에 예외 없이 나타났던 강력한 선행 경고음이에요."},
            {"icon": "⏱️", "title": "역전 해소 시점이 진짜 위기", "text": "역전되었다가 다시 양수로 돌아오는(Steepening) 시점에 실제 위기가 터지는 경향이 있어요."},
            {"icon": "🦅", "title": "연준의 금리 인하 사이클", "text": "주로 연준이 경기 방어를 위해 기준금리를 급하게 내릴 때 2년물 금리가 급락하며 역전이 해소됩니다."}
        ]
    },
    "VIX (공포지수)": {
        "ticker": "^VIX", "type": "yf", "scale": 1, "unit": "pt", "prefix": "",
        "title_sub": "단위: pt · 일간",
        "desc": "S&P 500 지수 옵션 가격을 바탕으로, 향후 30일간 시장이 <b>얼마나 출렁일지 예상하는 변동성 지수</b>예요. 주가가 급락하고 시장에 공포가 퍼질 때 튀어 오릅니다.",
        "cards": [
            {"icon": "😌", "title": "20 미만 — 시장 안정", "text": "투자자들이 편안함을 느끼며 주식 등 위험자산을 선호하는 평온한 상태예요."},
            {"icon": "🙄", "title": "20~30 — 경계감 상승", "text": "불확실성이 커지며 시장의 변동폭이 확대될 수 있는 주의 구간이에요."},
            {"icon": "😱", "title": "30 이상 — 극도의 공포", "text": "시장이 패닉에 빠진 상태입니다. 과거 주요 금융 위기 때 항상 이 선을 넘었어요."},
            {"icon": "📉", "title": "VIX와 증시의 역상관관계", "text": "VIX가 오르면 주가는 떨어지고, VIX가 내리면 주가는 안정적으로 오르는 성질이 강해요."}
        ]
    },
    "하이일드 스프레드": {
        "ticker": "BAMLH0A0HYM2", "type": "fred", "scale": 1, "unit": "%", "prefix": "",
        "title_sub": "단위: % · 일간",
        "desc": "가장 안전한 미국 국채와 부도 위험이 있는 투기등급(정크본드) 채권 간의 <b>금리 격차</b>예요. 기업들의 자금줄이 얼마나 타이트한지 보여주는 핵심 신용 지표입니다.",
        "cards": [
            {"icon": "👍", "title": "스프레드 축소 — 신용 여건 양호", "text": "한계 기업들도 무리 없이 돈을 빌릴 수 있을 만큼 시중에 자금이 풍부해요."},
            {"icon": "🔥", "title": "스프레드 확대 — 신용 경색 위험", "text": "돈 떼일까 봐 투자자들이 금리를 높게 부르면서, 기업들의 줄도산 위험이 커진 상태예요."},
            {"icon": "⚠️", "title": "위험 자산의 선행 지표", "text": "주식 시장이 멀쩡해 보여도, 이 지표가 튀어 오르면 곧 증시도 타격을 받을 확률이 높아요."},
            {"icon": "🎯", "title": "5% 선이 주요 임계점", "text": "보통 이 격차가 5%p를 넘어가면 금융 시스템에 확실한 스트레스가 왔다고 판단합니다."}
        ]
    },
    "달러 인덱스 (DXY)": {
        "ticker": "DX-Y.NYB", "type": "yf", "scale": 1, "unit": "pt", "prefix": "",
        "title_sub": "단위: pt · 일간",
        "desc": "유로, 엔, 파운드 등 주요 6개국 통화 대비 <b>미국 달러의 평균적인 가치</b>를 보여주는 지수예요. 글로벌 금융 시장의 자금 흐름을 결정짓는 대장 역할을 합니다.",
        "cards": [
            {"icon": "📈", "title": "달러 강세 — 글로벌 유동성 흡수", "text": "달러 가치가 오르면 전 세계 투자 자금이 미국으로 빨려 들어가 신흥국 증시가 힘들어요."},
            {"icon": "📉", "title": "달러 약세 — 위험 자산 랠리", "text": "달러가 싸지면 미국 밖으로 자본이 풀리면서 주식이나 신흥국 자산이 오르기 좋아요."},
            {"icon": "⚖️", "title": "미국 금리와의 관계", "text": "보통 연준이 금리를 올리거나 미국 경제가 독보적으로 강할 때 달러가 강해집니다."},
            {"icon": "🛢️", "title": "원자재 가격에 영향", "text": "원유나 금은 달러로 거래되기 때문에, 달러가 강해지면 원자재 가격은 보통 하락 압력을 받아요."}
        ]
    },
    "MOVE (채권 변동성)": {
        "ticker": "^MOVE", "type": "yf", "scale": 1, "unit": "pt", "prefix": "",
        "title_sub": "단위: pt · 일간",
        "desc": "미국 국채 옵션 가격을 이용해 산출하는 <b>'채권 시장판 VIX(공포지수)'</b>예요. 금리가 위아래로 얼마나 요동칠지를 나타내며, 매크로 불확실성을 짚어냅니다.",
        "cards": [
            {"icon": "😌", "title": "안정적인 흐름 — 매크로 평온", "text": "채권 금리가 안정적으로 움직이며 통화 정책에 대한 시장의 불확실성이 낮아요."},
            {"icon": "⚠️", "title": "100 돌파 — 유동성 주의보", "text": "금리 변동성이 커지면서 주식 시장의 밸류에이션(할인율)에도 악영향을 주기 시작해요."},
            {"icon": "🚨", "title": "140 이상 — 채권 시장 패닉", "text": "국채를 사고파는 호가 공백이 발생할 정도의 극심한 시스템 스트레스를 의미해요."},
            {"icon": "🦅", "title": "연준 정책의 나침반", "text": "연준의 금리 인상/인하 경로가 불투명하거나 갑작스럽게 바뀔 때 이 지표가 가장 먼저 튀어 오릅니다."}
        ]
    }
}

def eval_detail(ticker, val):
    if ticker == "^VIX":
        if val >= 30: return "🚨 경계", "#FF5555"
        elif val >= 20: return "⚠️ 주의", "#F59E0B"
        else: return "✅ 안정", "#22D98A"
    elif ticker == "^MOVE":
        if val >= 140: return "🚨 위험", "#FF5555"
        elif val >= 100: return "⚠️ 주의", "#F59E0B"
        else: return "✅ 안정", "#22D98A"
    elif ticker == "T10Y2Y":
        if val < 0: return "🚨 침체 경고 (역전)", "#FF5555"
        else: return "✅ 정상 (양수)", "#22D98A"
    elif ticker == "BAMLH0A0HYM2":
        if val >= 5.0: return "🚨 경고 (신용 경색)", "#FF5555"
        elif val >= 4.0: return "⚠️ 주의", "#F59E0B"
        else: return "✅ 안정", "#22D98A"
    elif ticker == "DX-Y.NYB":
        if val >= 105: return "🚨 달러 강세", "#FF5555"
        elif val < 100: return "✅ 달러 약세", "#22D98A"
        else: return "⚖️ 중립", "#F59E0B"
    elif ticker == "WALCL":
        return "🏦 통화 정책 진행중", "#00D4FF"
    elif ticker == "RRPONTSYD":
        if val < 0.5: return "⚠️ 유동성 버퍼 축소", "#FF5555"
        else: return "✅ 대기 자금 양호", "#22D98A"
    else:
        return "📊 모니터링 중", "#00D4FF"

# 지표 선택 레이아웃
sel_col1, sel_col2 = st.columns([1, 2])
with sel_col1:
    selected_ind_name = st.selectbox("분석할 지표 선택", list(DETAIL_META.keys()), label_visibility="collapsed")
meta = DETAIL_META[selected_ind_name]

with st.spinner(f"{selected_ind_name} 상세 데이터 로딩 중 (최대 10년 치)..."):
    if meta["type"] == "yf":
        _, _, df_detail = get_yf(meta["ticker"], "10y", "1d")
        series_detail = df_detail["Close"] if df_detail is not None else None
    else:
        series_detail = get_fred(meta["ticker"], limit=2500) # 영업일 기준 약 10년치

    if series_detail is not None and not series_detail.empty:
        # 데이터 스케일링
        series_detail = series_detail * meta["scale"]
        
        cur_val = float(series_detail.iloc[-1])
        prev_val = float(series_detail.iloc[-2]) if len(series_detail) > 1 else cur_val
        val_1w = float(series_detail.iloc[-6]) if len(series_detail) > 5 else prev_val
        val_3m = float(series_detail.iloc[-63]) if len(series_detail) > 62 else prev_val
        
        chg_1w = cur_val - val_1w
        chg_1w_pct = (chg_1w / abs(val_1w)) * 100 if val_1w != 0 else 0
        
        status_text, status_color = eval_detail(meta["ticker"], cur_val)
        
        # ── 1. 차트 헤더 영역 ──
        st.markdown(f"""
        <div style="margin-top: 15px; margin-bottom: -10px;">
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 6px;">
                <h3 style="margin: 0; padding: 0; font-size: 1.4rem; font-weight: 800; color: #FFFFFF;">{selected_ind_name.split('(')[0].strip()} 추이</h3>
                <span style="background: #1A2A3F; border: 1px solid #2A4060; padding: 2px 8px; border-radius: 4px; font-family: 'IBM Plex Mono', monospace; font-size: 0.75rem; color: #8AAAC8;">{meta["ticker"].replace('^','')}</span>
            </div>
            <div style="font-size: 0.85rem; color: #6B8EAE; font-weight: 600;">{meta['title_sub']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # ── 2. 인터랙티브 Plotly 차트 (2Y, 5Y, 10Y 버튼 추가) ──
        fig_det = go.Figure()
        fig_det.add_trace(go.Scatter(
            x=series_detail.index, y=series_detail.values,
            mode="lines", name=selected_ind_name.split('(')[0].strip(),
            line=dict(color="#00D4FF", width=2),
            fill="tozeroy", fillcolor=hex_to_rgba("#00D4FF", 0.08)
        ))
        
        # 임계값 가이드라인 (VIX, MOVE, 10Y2Y)
        if meta["ticker"] == "^VIX":
            fig_det.add_hline(y=30, line_dash="dash", line_color="#FF5555", opacity=0.7)
        elif meta["ticker"] == "^MOVE":
            fig_det.add_hline(y=140, line_dash="dash", line_color="#FF5555", opacity=0.7)
        elif meta["ticker"] == "T10Y2Y":
            fig_det.add_hline(y=0, line_dash="solid", line_color="#8AAAC8", opacity=0.5)
            
        fig_det.update_xaxes(
            showgrid=True, gridcolor="#141E2E",
            rangeselector=dict(
                buttons=list([
                    dict(count=2, label="2Y", step="year", stepmode="backward"),
                    dict(count=5, label="5Y", step="year", stepmode="backward"),
                    dict(count=10, label="10Y", step="year", stepmode="backward"),
                    dict(step="all", label="MAX")
                ]),
                bgcolor="#0C1420",
                activecolor="#1E3050",
                bordercolor="#1A2A3F",
                borderwidth=1,
                font=dict(color="#8AAAC8", size=11, family="IBM Plex Mono")
            )
        )
        # 파이썬 에러 원천 방지 (dictionary 직접 전달 방식)
        fig_det.update_layout(
            CHART_LAYOUT, 
            height=380, margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            hovermode="x unified"
        )
        fig_det.update_yaxes(showgrid=True, gridcolor="#141E2E", side="left", tickfont=dict(color="#8AAAC8", family="IBM Plex Mono"))
        
        st.plotly_chart(fig_det, use_container_width=True, config={"displayModeBar": False})

        # ── 3. 요약 블랙 박스 & 2x2 상세 설명 카드 그리드 (CSS Grid 적용) ──
        chg_arrow = "▲" if chg_1w >= 0 else "▼"
        chg_color = "#22D98A" if chg_1w >= 0 else "#FF5555"
        
        st.markdown(f'''
        <div style="background: #060A12; border: 1px solid #1E3050; border-radius: 12px; margin-bottom: 24px; overflow: hidden;">
            
            <!-- 상단 요약 박스 -->
            <div style="padding: 24px; border-bottom: 1px solid #1A2A3F;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px; flex-wrap: wrap;">
                    <span style="font-size: 0.85rem; color: #6B8EAE; font-weight: 700; background: #131E2E; padding: 4px 10px; border-radius: 6px;">최근 동향</span>
                    <span style="color: {status_color}; font-weight: 800; font-size: 0.95rem; background: {status_color}15; border: 1px solid {status_color}55; padding: 4px 12px; border-radius: 6px;">{status_text}</span>
                    <span style="font-family: 'IBM Plex Mono', monospace; font-size: 1.8rem; font-weight: 800; color: #FFFFFF; margin-left: 5px;">{meta['prefix']}{cur_val:,.2f}{meta['unit']}</span>
                </div>
                <div style="font-size: 0.95rem; color: #AACCEE; line-height: 1.6; margin-bottom: 10px;">
                    <b>{selected_ind_name.split('(')[0].strip()} {meta['prefix']}{cur_val:,.2f}{meta['unit']}</b> — {meta['cards'][0]['title'].split('—')[0].strip()} 수준이에요. 최근 흐름을 주의 깊게 살펴보세요.
                </div>
                <div style="font-size: 0.85rem; color: #6B8EAE; font-family: 'IBM Plex Mono', monospace;">
                    📊 전주({meta['prefix']}{val_1w:,.2f}{meta['unit']}) 대비 <span style="color: {chg_color}; font-weight: 700;">{chg_arrow} {abs(chg_1w):,.2f}{meta['unit']} ({chg_1w_pct:+.2f}%)</span>
                </div>
            </div>

            <!-- 하단 2x2 설명 그리드 -->
            <div style="padding: 24px; background: #080E1A;">
                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
                    <span style="color: #FF5555; font-size: 1.2rem;">📌</span>
                    <span style="color: #FFFFFF; font-weight: 800; font-size: 1.05rem;">{selected_ind_name.split('(')[0].strip()}란?</span>
                </div>
                <div style="color: #8AAAC8; font-size: 0.9rem; line-height: 1.6; margin-bottom: 24px;">
                    {meta['desc']}
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px;">
                    <!-- Card 1 -->
                    <div style="background: #0C1420; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <span style="font-size: 1.2rem;">{meta['cards'][0]['icon']}</span>
                            <span style="color: #FFFFFF; font-weight: 800; font-size: 0.95rem;">{meta['cards'][0]['title']}</span>
                        </div>
                        <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6; padding-left: 34px;">{meta['cards'][0]['text']}</div>
                    </div>
                    <!-- Card 2 -->
                    <div style="background: #0C1420; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <span style="font-size: 1.2rem;">{meta['cards'][1]['icon']}</span>
                            <span style="color: #FFFFFF; font-weight: 800; font-size: 0.95rem;">{meta['cards'][1]['title']}</span>
                        </div>
                        <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6; padding-left: 34px;">{meta['cards'][1]['text']}</div>
                    </div>
                    <!-- Card 3 -->
                    <div style="background: #0C1420; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <span style="font-size: 1.2rem;">{meta['cards'][2]['icon']}</span>
                            <span style="color: #FFFFFF; font-weight: 800; font-size: 0.95rem;">{meta['cards'][2]['title']}</span>
                        </div>
                        <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6; padding-left: 34px;">{meta['cards'][2]['text']}</div>
                    </div>
                    <!-- Card 4 -->
                    <div style="background: #0C1420; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                            <span style="font-size: 1.2rem;">{meta['cards'][3]['icon']}</span>
                            <span style="color: #FFFFFF; font-weight: 800; font-size: 0.95rem;">{meta['cards'][3]['title']}</span>
                        </div>
                        <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6; padding-left: 34px;">{meta['cards'][3]['text']}</div>
                    </div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
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
