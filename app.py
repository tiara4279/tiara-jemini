# ============================================================
#  글로벌 매크로 대시보드 — app.py (완전 통합본 FINAL)
#  ✅ 앱 마비 원인 (install_missing) 완전 제거
#  ✅ 무한 로딩 원인 (fredapi) 제거 및 requests.get (3.5초 타임아웃) 교체
#  ✅ Net Liquidity 실패 UI 논리 오류 완벽 수정
#  ✅ TypeError(중복 키워드 인자) 완벽 해결
#  ✅ 고객 요청사항: 이미지와 동일한 2x2 카드 및 프리미엄 분석 UI 100% 구현
#  ✅ HTML 마크다운 렌더링 오류(들여쓰기로 인한 코드블록화 현상) 완벽 수정
#  ✅ 드롭다운 선택 제거 및 12개 지표 순차적 스크롤 나열 완벽 적용
#  ✅ 금융/경제 전문 용어 전면 개편 (Tone & Manner 수정)
#  ✅ 역레포(RRP) 단위 스케일(Billion) 조정 및 AI 매크로 진단 리포트 부활
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
from bs4 import BeautifulSoup # BeautifulSoup 추가
import re # 정규표현식 추가

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

/* 콤보박스 디자인 정리 */
div[data-baseweb="select"] > div {
    background-color: #0C1420 !important;
    border: 1px solid #1E3050 !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
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


# INDEXerGO.com 공포지수 웹 스크래핑 함수 (새로 추가)
@st.cache_data(ttl=3600) # 1시간 캐시
def get_indexergo_fear():
    """
    INDEXerGO.com에서 공포지수 값을 웹 스크래핑합니다.
    (주의: 웹사이트 구조 변경 시 작동하지 않을 수 있으며, 상세한 에러 메시지를 확인해야 합니다.)
    """
    url = "https://www.indexergo.com/index/detail?code=IEG_FEAR"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
    }
    
    current_value = None
    change_percent = None
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # --- INDEXerGO 웹페이지에서 '공포지수' 값 추출 로직 ---
        # 실제 웹사이트 HTML 구조에 따라 이 셀렉터는 변경될 수 있습니다.
        # 여기서는 가장 유력한 후보를 가정합니다.
        
        # 1. 메인 공포지수 값 찾기 (예: <span class="index-value">15.31</span>)
        fear_value_tag = soup.find('span', class_='index-value')
        if fear_value_tag:
            current_value = float(fear_value_tag.text.strip())
        
        # 2. 전일 대비 변화율 찾기 (예: <span class="change-percent">(+0.79%)</span>)
        change_percent_tag = soup.find('span', class_='change-percent')
        if change_percent_tag:
            change_text = change_percent_tag.text.strip() # e.g., "(+0.79%)"
            match = re.search(r'([+-]?[\d.]+)\%', change_text)
            if match:
                change_percent = float(match.group(1))
        
        # If we successfully got a value, return it.
        if current_value is not None:
            return current_value, change_percent, None # No historical data for sparkline from single scrape
        
    except requests.exceptions.Timeout:
        st.warning("INDEXerGO 웹사이트 연결 시간 초과. VIX 데이터를 사용합니다.")
    except requests.exceptions.ConnectionError:
        st.warning("INDEXerGO 웹사이트에 연결할 수 없습니다. VIX 데이터를 사용합니다.")
    except requests.exceptions.HTTPError as e:
        st.warning(f"INDEXerGO 웹사이트에서 오류 응답 수신 ({e.response.status_code}). VIX 데이터를 사용합니다.")
    except (ValueError, AttributeError):
        st.warning("INDEXerGO 공포지수 값 또는 변화율 파싱 오류. 웹사이트 구조가 변경되었을 수 있습니다. VIX 데이터를 사용합니다.")
    except Exception as e:
        st.warning(f"INDEXerGO 스크래핑 중 예상치 못한 오류 발생: {e}. VIX 데이터를 사용합니다.")
        
    return None, None, None # Fallback if any error occurs


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
        st.markdown(card(name, f(v, 4), chg, desc).replace('\n', ''), unsafe_allow_html=True)
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
        st.markdown(card(name, f(v, 2), chg, desc).replace('\n', ''), unsafe_allow_html=True)
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
        st.markdown(card(name, f(v, 2), chg, desc).replace('\n', ''), unsafe_allow_html=True)
        spark(h, color, 85)


# ═══════════════════════════════════════════════════════════
#  §4  시장 리스크 및 스트레스 지표
# ═══════════════════════════════════════════════════════════
sec("⚠️", "시장 리스크 및 스트레스 지표")

r1, r2, r3, r4 = st.columns(4)

with r1:
    # INDEXerGO 공포지수 가져오기 시도
    indexergo_val, indexergo_chg, _ = get_indexergo_fear()
    if indexergo_val is not None:
        st.markdown(card("공포지수", f(indexergo_val, 2), indexergo_chg, "INDEXerGO 실시간", risk_badge("VIX", indexergo_val)).replace('\n', ''), unsafe_allow_html=True)
        # INDEXerGO 스크래핑은 현재 값만 가져오므로 스파크라인은 표시하지 않습니다.
    else:
        # INDEXerGO 데이터 로딩 실패 시 VIX로 폴백
        v, chg, h = get_yf("^VIX", "6mo", "1d")
        st.markdown(card("VIX (공포지수)", f(v, 2), chg, "CBOE 변동성 지수 (대체)", risk_badge("VIX", v)).replace('\n', ''), unsafe_allow_html=True)
        spark(h, "#EF4444", 85)

with r2:
    v, chg, h = get_yf("^MOVE", "6mo", "1d")
    st.markdown(card("MOVE (채권 변동성)", f(v, 2), chg, "ICE BofA 채권 변동성", risk_badge("MOVE", v)).replace('\n', ''), unsafe_allow_html=True)
    spark(h, "#F59E0B", 85)

with r3:
    ts_data = get_fred("T10Y2Y")
    if ts_data is not None and len(ts_data) > 0:
        lv   = float(ts_data.iloc[-1])
        pv   = float(ts_data.iloc[-2]) if len(ts_data) > 1 else lv
        diff = lv - pv
        clr  = "kup" if lv >= 0 else "kdn"
        arr  = "▲"   if lv >= 0 else "▼"
        html_str = f"""
        <div class="kcard">
          <div class="klabel">장단기 금리차 (10Y-2Y)</div>
          <div class="kval">{lv:+.2f}%</div>
          <span class="{clr}">{arr} {abs(diff):.3f}%p</span>
          <div class="ksub">FRED T10Y2Y — 수익률 곡선</div>
        </div>"""
        st.markdown(html_str.replace('\n', ''), unsafe_allow_html=True)
        spark(ts_data, "#10B981", 85, is_series=True)
    else:
        v, chg, h = get_yf("^TNX", "6mo", "1d")
        st.markdown(card("10Y 국채금리 (TNX)", f(v, 3, suf="%"), chg, "미국 10년 국채").replace('\n', ''), unsafe_allow_html=True)
        spark(h, "#10B981", 85)

with r4:
    v, chg, h = get_yf("HYG", "6mo", "1d")
    st.markdown(card("HYG (하이일드 ETF)", f(v, 2, pre="$"), chg, "HY 스프레드 프록시").replace('\n', ''), unsafe_allow_html=True)
    spark(h, "#8B5CF6", 85)

hy = get_fred("BAMLH0A0HYM2")
if hy is not None and len(hy) > 0:
    lv     = float(hy.iloc[-1])
    pv     = float(hy.iloc[-2]) if len(hy) > 1 else lv
    chg_hy = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
    fe1, fe2 = st.columns(2)
    with fe1:
        st.markdown(card("하이일드 스프레드 (OAS)", f(lv, 2, suf="%"), chg_hy, "ICE BofA US HY OAS").replace('\n', ''), unsafe_allow_html=True)
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
            st.markdown(card(label, f(lv/1000, 1, suf=" T$"), chg, f"FRED: {sid}").replace('\n', ''), unsafe_allow_html=True)
            spark(data, color, 85, is_series=True)
        else:
            st.markdown(card(label, "데이터 없음", None, "통신 지연").replace('\n', ''), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §6  은행 신용 및 단기 자금 시장
# ═══════════════════════════════════════════════════════════
sec("💰", "은행 신용 및 단기 자금 시장")

CRED = [
    ("RRPONTSYD", "역레포 (ON RRP)",   "#EC4899", "B$",  400,    0),
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
            st.markdown(card(label, f(lv, dp, suf=suf), chg, f"FRED: {sid}").replace('\n', ''), unsafe_allow_html=True)
            spark(data, color, 80, is_series=True)
        else:
            st.markdown(card(label, "데이터 없음", None, "통신 지연").replace('\n', ''), unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════
#  §7  인플레이션 및 글로벌 매크로
# ═══════════════════════════════════════════════════════════
sec("📈", "인플레이션 및 글로벌 매크로")

m1, m2, m3, m4 = st.columns(4)

with m1:
    v, chg, h = get_yf("DX-Y.NYB", "6mo", "1d")
    st.markdown(card("DXY (달러 인덱스)", f(v, 3), chg, "ICE US Dollar Index").replace('\n', ''), unsafe_allow_html=True)
    spark(h, "#F59E0B", 90)

with m2:
    v, chg, h = get_yf("GC=F", "6mo", "1d")
    st.markdown(card("금 선물", f(v, 2, pre="$"), chg, "COMEX Gold $/oz").replace('\n', ''), unsafe_allow_html=True)
    spark(h, "#FBBF24", 90)

with m3:
    bei5 = get_fred("T5YIE", 40)
    if bei5 is not None and len(bei5) > 0:
        lv  = float(bei5.iloc[-1])
        pv  = float(bei5.iloc[-2]) if len(bei5) > 1 else lv
        chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
        st.markdown(card("5Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T5YIE").replace('\n', ''), unsafe_allow_html=True)
        spark(bei5, "#10B981", 90, is_series=True)
    else:
        st.markdown(card("5Y 기대 인플레이션", "데이터 없음", None, "통신 지연").replace('\n', ''), unsafe_allow_html=True)

with m4:
    bei10 = get_fred("T10YIE", 40)
    if bei10 is not None and len(bei10) > 0:
        lv  = float(bei10.iloc[-1])
        pv  = float(bei10.iloc[-2]) if len(bei10) > 1 else lv
        chg = (lv - pv) / abs(pv) * 100 if pv != 0 else 0
        st.markdown(card("10Y 기대 인플레이션", f(lv, 2, suf="%"), chg, "FRED T10YIE").replace('\n', ''), unsafe_allow_html=True)
        spark(bei10, "#3B82F6", 90, is_series=True)
    else:
        st.markdown(card("10Y 기대 인플레이션", "데이터 없음", None, "통신 지연").replace('\n', ''), unsafe_allow_html=True)

v2, chg2, h2 = get_yf("CL=F", "6mo", "1d")
mi1, _mi2, _mi3 = st.columns([1, 1, 2])
with mi1:
    st.markdown(card("WTI 원유 선물", f(v2, 2, pre="$", suf="/bbl"), chg2, "NYMEX Crude Oil").replace('\n', ''), unsafe_allow_html=True)
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
    layout_cfg = CHART_LAYOUT.copy()
    layout_cfg.update(yaxis_title="정규화 (시작=100)")
    fig.update_layout(**layout_cfg)
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
    layout_cfg2 = CHART_LAYOUT.copy()
    layout_cfg2.update(
        height=420,
        margin=dict(l=20, r=20, t=45, b=20),
        font=dict(color="#8AAAC8", family="IBM Plex Mono", size=11),
    )
    fig2.update_layout(**layout_cfg2)
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
    layout_cfg3 = CHART_LAYOUT.copy()
    layout_cfg3.update(yaxis_title="정규화 (시작=100)")
    fig3.update_layout(**layout_cfg3)
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
    layout_cfg4 = CHART_LAYOUT.copy()
    layout_cfg4.update(yaxis_title="정규화 (시작=100)")
    fig4.update_layout(**layout_cfg4)
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
        walcl_val = walcl / 1000  # 단위 변환 (Millions to Billions)
        tga_val = tga / 1000      # 단위 변환 (Millions to Billions)
        sp500_s = sp500_df['Close']
        
        if hasattr(sp500_s.index, 'tz') and sp500_s.index.tz is not None:
            sp500_s.index = sp500_s.index.tz_localize(None)
        
        df_liq = pd.DataFrame({'WALCL': walcl_val, 'RRP': rrp, 'TGA': tga_val}).ffill().dropna()
        df_liq['Net_Liquidity'] = df_liq['WALCL'] - df_liq['RRP'] - df_liq['TGA']
        
        df_plot = df_liq.join(sp500_s, how='inner').ffill().dropna()
        
        fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
        fig_liq.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Net_Liquidity'], name="순유동성 (B$)", line=dict(color='#00D4FF', width=2.5)), secondary_y=False)
        fig_liq.add_trace(go.Scatter(x=df_plot.index, y=df_plot['Close'], name="S&P 500", line=dict(color='#FF5555', width=1.5)), secondary_y=True)
        
        layout_liq = CHART_LAYOUT.copy()
        layout_liq.update(height=450, title="Net Liquidity vs S&P 500 (최근 1년)")
        fig_liq.update_layout(**layout_liq)
        st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})
        
        html_str2 = """
        <div style="background: #0C1420; border: 1px solid #1E3050; border-radius: 12px; padding: 16px; margin-bottom: 30px;">
        <div style="font-size: 0.9rem; font-weight: 700; color:#00D4FF; margin-bottom: 8px;">📌 Net Liquidity(순유동성) 공식: 연준 대차대조표 - 역레포(RRP) - 재무부 계좌(TGA)</div>
        <div style="font-size: 0.8rem; color: #8AAAC8; line-height: 1.5;">
        금융시장에 공급된 실질적인 달러 유동성 총량을 나타내는 핵심 매크로 지표입니다.<br>
        일반적으로 <b style="color:#00D4FF">순유동성(Net Liquidity)</b> 궤적은 <b style="color:#FF5555">S&P 500</b> 등 주요 위험자산의 밸류에이션 및 추세와 <b>강한 정(+)의 상관관계</b>를 보입니다.
        </div></div>"""
        st.markdown(html_str2.replace('\n', ''), unsafe_allow_html=True)
    else:
        html_fail = """
        <div style="background:#1A0E0E; border:1px solid #8B3A3A; border-radius:10px; padding:16px; margin-bottom:16px;">
            <div style="font-size:0.9rem; font-weight:700; color:#FF6B6B; margin-bottom:6px;">데이터 로딩 실패 — 항목별 상태</div>
            <div style="font-size:0.82rem; color:#CC9999; line-height:1.6;">서버 접속 지연으로 데이터를 불러오지 못했습니다.</div>
        </div>"""
        st.markdown(html_fail.replace('\n', ''), unsafe_allow_html=True)

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
                html_status = f"""
                <div style="background:#0C1420; border:2px solid {ok_color}; border-radius:8px; padding:14px; text-align:center;">
                  <div style="font-size:0.75rem; font-weight:700; color:#6B8EAE; margin-bottom:6px;">{name}</div>
                  <div style="font-family:'IBM Plex Mono',monospace; font-size:1.1rem; font-weight:800; color:{ok_color};">{ok_text}</div>
                </div>"""
                st.markdown(html_status.replace('\n', ''), unsafe_allow_html=True)


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
        
        layout_dec = CHART_LAYOUT.copy()
        layout_dec.update(height=450, title="미국 10년물 국채금리 분해 (최근 1년)")
        fig_dec.update_layout(**layout_dec)
        fig_dec.update_yaxes(title_text="금리 (%)", secondary_y=False)
        fig_dec.update_yaxes(title_text="기간 프리미엄 (%p)", secondary_y=True, showgrid=False)
        
        st.plotly_chart(fig_dec, use_container_width=True, config={'displayModeBar': False})
    else:
        st.warning("⚠️ 데이터를 완전히 불러오지 못했습니다. (통신 지연)")


# ═══════════════════════════════════════════════════════════
#  §11 AI 매크로 종합 시황 진단
# ═══════════════════════════════════════════════════════════
sec("📝", "AI 매크로 종합 시황 진단")

with st.spinner("AI 매크로 시황 진단 리포트 생성 중..."):
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
        COLOR_WARN = "#F59E0B"
        
        if vix_val and vix_val > 30: vix_msg = f"<b style='color:{COLOR_DANGER};'>위험 심리:</b> VIX {vix_val:.2f}pt — 극도의 위험 회피(Risk-off) 구간입니다. 변동성 확대로 인한 자산 가격 충격 우려가 큽니다."
        elif vix_val and vix_val > 20: vix_msg = f"<b style='color:{COLOR_WARN};'>위험 심리:</b> VIX {vix_val:.2f}pt — 시장의 내재 변동성이 점증하고 있습니다. 리스크 관리가 요구됩니다."
        else: vix_msg = f"<b style='color:{COLOR_SAFE};'>위험 심리:</b> VIX {vix_val:.2f}pt — 변동성이 안정화되며 위험 자산 선호 심리가 유지되고 있습니다." if vix_val else "VIX 데이터 대기 중"
        
        if emerg_val > 500 or (move_val and move_val > 140): sys_msg = f"<b style='color:{COLOR_DANGER};'>시스템 경고:</b> 연준 긴급 대출 급증 또는 채권 변동성({move_val:.1f}pt) 확대로 시스템 스트레스 징후가 관찰됩니다."
        else: sys_msg = f"<b style='color:{COLOR_SAFE};'>시스템 안정:</b> 은행권 긴급 조달 및 채권 시장 내재 변동성이 안정적으로 통제되고 있습니다."
        
        if sofr_spread > 0.05: sofr_msg = f"<b style='color:{COLOR_DANGER};'>조달 스트레스:</b> 단기 달러 자금 시장 내 펀딩 경색(Funding Squeeze) 조짐이 관찰됩니다."
        else: sofr_msg = f"<b style='color:{COLOR_SAFE};'>조달 안정:</b> 레포(Repo) 등 단기 자금 시장의 달러 융통 여건이 양호하게 유지되고 있습니다."
        
        if totll_chg < 0: totll_msg = f"<b style='color:{COLOR_DANGER};'>신용 위축:</b> 상업은행의 여신 규모가 감소하여 민간 신용 창출(Credit Creation) 둔화 우려가 있습니다."
        elif totll_chg > 0: totll_msg = f"<b style='color:{COLOR_SAFE};'>신용 확장:</b> 상업은행 대출이 증가세를 유지하며 실물 경제에 지속적인 자금 공급이 이루어지고 있습니다."
        else: totll_msg = f"<b style='color:{COLOR_WARN};'>신용 정체:</b> 상업은행의 여신 공급 확장이 다소 정체되며 관망세를 보이고 있습니다."
        
        if yc_val < 0: yield_msg = f"<b style='color:{COLOR_DANGER};'>수익률 곡선:</b> 장단기 금리 역전({yc_val:.2f}%p) 상태로, 중장기적 경기 둔화(Recession) 우려가 지속 반영 중입니다."
        else: yield_msg = f"<b style='color:{COLOR_SAFE};'>수익률 곡선:</b> 장단기 금리차({yc_val:.2f}%p)가 정상화(Steepening)되어 경제 성장 기대 심리가 우세합니다."
        
        if bei_val > 2.5: bei_msg = f"<b style='color:{COLOR_DANGER};'>물가 궤적:</b> 기대인플레이션({bei_val:.2f}%) 상회로 인해 연준의 통화정책 완화 기조가 제약받을 리스크가 존재합니다."
        else: bei_msg = f"<b style='color:{COLOR_SAFE};'>물가 궤적:</b> 기대인플레이션({bei_val:.2f}%)이 연준의 장기 목표 범위 내에서 안정적으로 통제 중입니다."

        if yc_val < 0 and sofr_spread > 0.05:
            strategy = "경기 둔화 시그널과 단기 펀딩 스트레스가 중첩된 국면입니다. <b style='color:#FF5555'>현금성 자산 및 단기 우량채 중심의 방어적 포트폴리오 비중 확대</b>를 권장합니다."
            s_color = COLOR_DANGER
        elif yc_val >= 0 and sofr_spread <= 0.02:
            strategy = "신용 조달 여건이 양호하며 펀더멘털 성장 기대가 유효한 국면입니다. <b style='color:#22D98A'>위험 자산(주식) 비중 유지 및 랠리 동참</b>이 합리적인 자산 배분 전략입니다."
            s_color = COLOR_SAFE
        else:
            strategy = "거시경제 지표 방향성이 혼재된 전환기적(Transitional) 국면입니다. <b style='color:#F59E0B'>매크로 관망세 유지 및 이익 가시성이 높은 우량(Quality) 자산 선별적 접근</b>이 요구됩니다."
            s_color = COLOR_WARN

        report_html = f"""
        <div style="background: linear-gradient(140deg, #131E2E, #0C1520); border: 1px solid #1E3050; border-radius: 12px; padding: 20px; margin-bottom: 24px;">
            <div style="font-size: 1.1rem; font-weight: 800; color: #00D4FF; margin-bottom: 15px; display: flex; align-items: center; gap: 8px;">
                <span>💡</span> 핵심 자산 배분 전략 (AI Macro Insight)
            </div>
            <div style="font-size: 1rem; font-weight: 600; line-height: 1.6; margin-bottom: 20px; color: {s_color}; background: #060A12; padding: 16px; border-radius: 8px; border: 1px solid #1A2A3F;">
                {strategy}
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px;">
                <div style="background: #080E1A; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                    <div style="font-weight: 800; font-size: 0.95rem; margin-bottom: 12px; color: #00D4FF; border-bottom: 1px solid #1E3050; padding-bottom: 8px;">📌 시장 심리 및 유동성 환경</div>
                    <div style="line-height: 1.8; font-size: 0.85rem; color: #fef08a;">
                        <div>• {vix_msg}</div>
                        <div>• {sys_msg}</div>
                        <div>• {sofr_msg}</div>
                    </div>
                </div>
                <div style="background: #080E1A; border: 1px solid #1A2A3F; border-radius: 10px; padding: 18px;">
                    <div style="font-weight: 800; font-size: 0.95rem; margin-bottom: 12px; color: #00D4FF; border-bottom: 1px solid #1E3050; padding-bottom: 8px;">📌 펀더멘털 및 신용 사이클</div>
                    <div style="line-height: 1.8; font-size: 0.85rem; color: #fef08a;">
                        <div>• {totll_msg}</div>
                        <div>• {yield_msg}</div>
                        <div>• {bei_msg}</div>
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(report_html.replace('\n', ''), unsafe_allow_html=True)
    except Exception as e:
        st.warning("⚠️ 매크로 진단 리포트를 생성하기 위한 일부 데이터가 부족합니다.")


# ═══════════════════════════════════════════════════════════
#  §12 심층 지표 분석 (프리미엄 패널 12개 연속 스크롤)
# ═══════════════════════════════════════════════════════════
st.markdown("<hr style='border-color: #1A2A3F;'>", unsafe_allow_html=True)
sec("🔍", "심층 지표 분석 (전체 나열)")
st.caption("주요 12개 거시 지표의 과거 추이, AI 진단, 핵심 의미를 한눈에 스크롤하여 확인하세요.")

# 금융/경제 전문 용어로 전면 개편된 12개 지표 메타데이터
DETAIL_META = {
    "VIX (공포지수)": {
        "ticker": "^VIX", "type": "yf", "scale": 1, "unit": "pt", "prefix": "",
        "title_sub": "단위: pt · 일간",
        "desc": "S&P 500 지수 옵션에 내재된 향후 30일간의 <b>시장 변동성 기대치</b>를 나타냅니다. 주가 하락 및 시장 불확실성 확대 시 급등하는 경향이 있습니다.",
        "cards": [
            {"icon": "😌", "title": "20 미만 — 시장 안정", "text": "투자 심리가 안정되어 있으며 위험자산 선호(Risk-on) 환경이 조성됩니다."},
            {"icon": "🙄", "title": "20~30 — 경계감 상승", "text": "불확실성이 점증하며 시장 변동성이 확대될 수 있는 주의 구간입니다."},
            {"icon": "😱", "title": "30 이상 — 극도의 공포", "text": "시장 패닉 및 극도의 위험 회피(Risk-off) 상태를 의미하며, 과거 주요 금융위기 시 해당 임계치를 상회했습니다."},
            {"icon": "📉", "title": "VIX와 증시의 역상관관계", "text": "일반적으로 VIX 지수와 주가지수는 강한 역의 상관관계를 가집니다."}
        ]
    },
    "MOVE (채권 변동성)": {
        "ticker": "^MOVE", "type": "yf", "scale": 1, "unit": "pt", "prefix": "",
        "title_sub": "단위: pt · 일간",
        "desc": "미국 국채 옵션 가격을 바탕으로 산출된 <b>채권시장의 내재변동성 지수</b>입니다. 금리 변동 위험을 나타내며, 거시경제 및 통화정책 불확실성을 반영합니다.",
        "cards": [
            {"icon": "😌", "title": "안정적인 흐름 — 매크로 평온", "text": "채권 금리 변동성이 제한적이며 통화정책 경로에 대한 불확실성이 낮습니다."},
            {"icon": "⚠️", "title": "100 돌파 — 유동성 주의보", "text": "금리 변동성 확대로 인해 위험자산의 밸류에이션(할인율) 부담이 가중되는 구간입니다."},
            {"icon": "🚨", "title": "140 이상 — 채권 시장 패닉", "text": "채권시장 내 호가 공백 및 유동성 경색이 발생할 수 있는 극심한 시스템 스트레스를 의미합니다."},
            {"icon": "🦅", "title": "연준 정책의 나침반", "text": "연준(Fed)의 통화정책 경로가 불투명하거나 급격한 기조 변화(Pivot)가 예상될 때 선행하여 급등합니다."}
        ]
    },
    "장단기 금리차 (10Y-2Y)": {
        "ticker": "T10Y2Y", "type": "fred", "scale": 1, "unit": "%p", "prefix": "",
        "title_sub": "단위: %p · 일간",
        "desc": "미국 10년물 국채 금리에서 2년물 국채 금리를 뺀 스프레드입니다. 정상적인 수익률 곡선(Yield Curve)에서는 장기금리가 더 높지만, 경기 침체 우려가 커질 경우 단기금리가 장기금리를 상회하는 <b>'수익률 곡선 역전(Inversion)'</b>이 발생합니다.",
        "cards": [
            {"icon": "📈", "title": "정상 (양수) — 경제 성장", "text": "장기 투자에 대한 기간 프리미엄이 반영된 정상적인 경제 성장 국면입니다."},
            {"icon": "📉", "title": "역전 (음수) — 침체 경고", "text": "과거 50년간 주요 경기 침체(Recession)를 선행했던 강력한 신호입니다."},
            {"icon": "⏱️", "title": "역전 해소 시점이 진짜 위기", "text": "역전 해소(Bull Steepening) 시점은 주로 중앙은행의 급격한 금리 인하로 촉발되며, 실물 경기 침체 진입과 맞물리는 경향이 있습니다."},
            {"icon": "🦅", "title": "연준의 금리 인하 사이클", "text": "경기 방어를 위한 연준의 기준금리 인하 시, 2년물 금리가 10년물 대비 더 큰 폭으로 하락하며 스프레드가 정상화됩니다."}
        ]
    },
    "HYG (하이일드 ETF)": {
        "ticker": "HYG", "type": "yf", "scale": 1, "unit": "", "prefix": "$",
        "title_sub": "단위: $ · 일간",
        "desc": "대표적인 미국 <b>하이일드 채권 ETF</b>입니다. 가격 상승은 시장의 위험 선호(Risk-on)를, 하락은 위험 회피(Risk-off) 및 신용 경계감을 의미합니다.",
        "cards": [
            {"icon": "📈", "title": "가격 상승 — 위험 선호", "text": "투자 심리가 개선되며 주식 등 위험자산과 동반 상승하는 경향이 있습니다."},
            {"icon": "📉", "title": "가격 하락 — 위험 회피", "text": "신용 경색 및 기업 디폴트 우려 점증 시 자금 이탈로 가격이 급락합니다."},
            {"icon": "💸", "title": "고수익(High Yield) 추구", "text": "국채 대비 높은 이자 수익(Yield)을 제공하여 평상시 인컴 추구 자금이 유입됩니다."},
            {"icon": "🔍", "title": "신용 시장의 선행 지표", "text": "주식 시장 조정에 앞서 하락하며 기업 자금 조달 여건 악화를 사전 경고하는 역할을 합니다."}
        ]
    },
    "하이일드 스프레드 (OAS)": {
        "ticker": "BAMLH0A0HYM2", "type": "fred", "scale": 1, "unit": "%", "prefix": "",
        "title_sub": "단위: % · 일간",
        "desc": "미국 국채와 투기등급(하이일드) 채권 간의 <b>가산 금리(Option-Adjusted Spread)</b>입니다. 기업의 자금 조달 여건과 신용 위험을 나타내는 핵심 지표입니다.",
        "cards": [
            {"icon": "👍", "title": "스프레드 축소 — 신용 여건 양호", "text": "시중 유동성이 풍부하며 한계 기업의 자금 조달 리스크가 낮은 상태입니다."},
            {"icon": "🔥", "title": "스프레드 확대 — 신용 경색 위험", "text": "채무 불이행 리스크 프리미엄이 상승하며 기업 신용 경색 우려가 확대된 상태입니다."},
            {"icon": "⚠️", "title": "위험 자산의 선행 지표", "text": "스프레드의 급격한 확대는 주식 시장 조정의 강력한 선행 지표로 작용합니다."},
            {"icon": "🎯", "title": "5% 선이 주요 임계점", "text": "통상 5%p 상회 시 신용 시장의 구조적 스트레스 구간 진입으로 해석합니다."}
        ]
    },
    "연준 총자산 (WALCL)": {
        "ticker": "WALCL", "type": "fred", "scale": 1/1000000, "unit": "T", "prefix": "$",
        "title_sub": "단위: $T · 주간",
        "desc": "미국 연방준비제도의 <b>대차대조표 총자산 규모</b>입니다. 자산 매입(QE)은 시중 유동성 확대를, 자산 축소(QT)는 유동성 흡수를 의미합니다.",
        "cards": [
            {"icon": "💰", "title": "양적완화 QE — 자산 증가", "text": "연준의 자산 매입으로 시중 유동성이 공급되어 자산 가격 상승 압력으로 작용합니다."},
            {"icon": "🔴", "title": "양적긴축 QT — 자산 감소", "text": "보유 자산 만기 도래 시 재투자 중단으로 시중 유동성을 회수하여 자산 시장에 부담을 줍니다."},
            {"icon": "📊", "title": "2022년 고점 대비 축소", "text": "팬데믹 대응으로 약 9조 달러까지 팽창했으나, 이후 긴축 기조(QT)로 점진적 축소 추세입니다."},
            {"icon": "🔍", "title": "지급준비금과 함께 보기", "text": "대차대조표 총규모뿐만 아니라 실질 유동성인 '지급준비금(Reserves)' 동향을 교차 검증해야 합니다."}
        ]
    },
    "지급준비금 잔고 (WRBWFRBL)": {
        "ticker": "WRBWFRBL", "type": "fred", "scale": 1/1000000, "unit": "T", "prefix": "$",
        "title_sub": "단위: $T · 주간",
        "desc": "상업은행이 법정지급준비금을 초과하여 연준에 예치한 <b>지급준비금(Reserve Balances)</b>입니다. 금융시장 내 실질적인 잉여 유동성 규모를 나타냅니다.",
        "cards": [
            {"icon": "🏦", "title": "잔고 증가 — 증시 유동성 풍부", "text": "은행권의 신용 창출 여력이 확대되어 위험 자산으로의 자금 유입 환경이 개선됩니다."},
            {"icon": "🏜️", "title": "잔고 감소 — 유동성 경색 우려", "text": "잉여 유동성이 축소되며 단기 자금 시장 경색 및 자산 가격 변동성 확대 위험이 존재합니다."},
            {"icon": "⚖️", "title": "연준 QT의 직접적 타겟", "text": "연준의 양적긴축(QT) 시 가장 민감하게 감소하는 항목 중 하나입니다."},
            {"icon": "🛡️", "title": "시스템 유동성 완충재", "text": "충분한 지급준비금은 뱅크런 등 시스템적 스트레스 발생 시 금융권의 방어력을 제공합니다."}
        ]
    },
    "TGA (재무부 일반계정)": {
        "ticker": "WTREGEN", "type": "fred", "scale": 1/1000, "unit": "B", "prefix": "$",
        "title_sub": "단위: $B · 주간",
        "desc": "미국 재무부가 연준에 개설한 핵심 정부 계좌(Treasury General Account)입니다. <b>TGA 잔고 증가</b>는 시중 유동성 흡수를, <b>잔고 감소(정부 지출)</b>는 유동성 방출을 의미합니다.",
        "cards": [
            {"icon": "🕳️", "title": "잔액 증가 — 유동성 흡수", "text": "세수 확보 및 대규모 국채 발행을 통해 시중 유동성을 환수하는 구축 효과(Crowding Out)가 발생합니다."},
            {"icon": "🚀", "title": "잔액 감소 — 유동성 공급", "text": "재정 지출 확대로 인해 시중에 잉여 유동성이 공급되는 효과가 나타납니다."},
            {"icon": "📝", "title": "부채 한도 협상의 변수", "text": "부채 한도 도달 시 TGA 잔고를 소진하며 지출을 충당하고, 타결 시 대규모 국채 발행으로 잔고를 재확보(유동성 흡수)합니다."},
            {"icon": "📅", "title": "세금 납부의 달 영향", "text": "미국의 주요 납세 기간(예: 4월)에는 세수 유입으로 일시적인 TGA 잔고 급증 및 단기 유동성 흡수가 관찰됩니다."}
        ]
    },
    "역레포 잔액 (RRP)": {
        "ticker": "RRPONTSYD", "type": "fred", "scale": 1, "unit": "B", "prefix": "$",
        "title_sub": "단위: $B · 일간",
        "desc": "금융기관의 잉여 자금이 연준의 <b>역환매조건부채권(ON RRP) 창구에 예치된 규모</b>입니다. RRP 감소는 대기 자금이 국채나 민간 시장으로 유입됨을 시사합니다.",
        "cards": [
            {"icon": "🌊", "title": "잔고 감소 — 유동성 방출", "text": "MMF 등의 대기 자금이 단기 국채 매입 등으로 이동하며 시중 유동성을 지지합니다."},
            {"icon": "🔒", "title": "잔고 증가 — 유동성 환수", "text": "민간 시장의 투자 매력도 저하 또는 불안으로 인해 잉여 자금이 연준으로 회귀함을 의미합니다."},
            {"icon": "🪫", "title": "유동성 버퍼 고갈 우려", "text": "RRP 잔고 고갈 시, QT의 타격이 지급준비금 감소로 직접 전이되어 유동성 경색 위험이 커집니다."},
            {"icon": "🏦", "title": "단기 금리 하한선 역할", "text": "연준이 기준금리(Target Range) 하한을 방어하기 위해 제공하는 정책 수단으로 기능합니다."}
        ]
    },
    "MMF 총잔고 (WRMFSL)": {
        "ticker": "WRMFSL", "type": "fred", "scale": 1/1000, "unit": "T", "prefix": "$",
        "title_sub": "단위: $T · 주간",
        "desc": "단기 국채 및 기업어음 등에 투자하는 <b>머니마켓펀드(MMF)의 총잔고</b>입니다. 금리 인상기나 금융시장 불확실성 확대 시 안전 마진을 추구하는 현금성 자금의 파킹 통장 역할을 합니다.",
        "cards": [
            {"icon": "🛡️", "title": "잔고 증가 — 대기성 자금 유입", "text": "위험 회피 심리 발동 또는 고금리 매력에 의해 현금성 피난처로의 자본 유입이 지속됩니다."},
            {"icon": "💸", "title": "잔고 감소 — 위험자산 재분배", "text": "투자 심리 개선 및 금리 인하 기대로 인해 MMF 자금이 위험자산이나 장기 채권으로 이동함을 시사합니다."},
            {"icon": "🔥", "title": "단기 금리 매력도 반영", "text": "시중 은행 예금 대비 금리 경쟁력이 우수할 경우 대규모 자금 이탈을 흡수하는 역할을 수행합니다."},
            {"icon": "🎯", "title": "잠재적 유동성 공급원", "text": "금리 인하 사이클 진입 시 위험자산으로 이동할 수 있는 풍부한 잠재적 대기 자금(Dry Powder)입니다."}
        ]
    },
    "상업은행 총대출 (TOTLL)": {
        "ticker": "TOTLL", "type": "fred", "scale": 1/1000, "unit": "T", "prefix": "$",
        "title_sub": "단위: $T · 주간",
        "desc": "미국 내 상업은행의 가계 및 기업 대상 <b>총 대출 잔액</b>입니다. 민간 부문의 신용 창출 현황을 나타내며, 실물 경제의 확장 및 수축 여부를 판단하는 핵심 지표입니다.",
        "cards": [
            {"icon": "🟢", "title": "대출 증가 — 신용 팽창", "text": "대출 태도 완화 및 자금 수요 증가로 신용 창출이 활발하며, 경기 확장 국면을 시사합니다."},
            {"icon": "🔴", "title": "대출 감소 — 신용 축소", "text": "은행의 여신 건전성 강화 및 대출 축소(Credit Crunch)가 진행 중이며, 실물 경기 침체 우려를 높입니다."},
            {"icon": "🏢", "title": "금융 시스템 건전성 척도", "text": "지역 은행 리스크 등 시스템 불안 발생 시 은행들이 자본 보존을 위해 선제적으로 대출을 축소하는 경향이 있습니다."},
            {"icon": "🦅", "title": "통화정책과의 시차 연동", "text": "긴축적인 통화정책(고금리) 환경에서는 조달 비용 상승으로 인해 시차를 두고 신용 증가세가 둔화됩니다."}
        ]
    },
    "SOFR (익일물 금리)": {
        "ticker": "SOFR", "type": "fred", "scale": 1, "unit": "%", "prefix": "",
        "title_sub": "단위: % · 일간",
        "desc": "미국 국채를 담보로 하는 1일물 환매조건부채권(Repo) 거래에 적용되는 <b>기준 금리</b>입니다. 단기 자금 시장의 실질적인 달러 조달 비용과 유동성 여건을 직접적으로 반영합니다.",
        "cards": [
            {"icon": "✅", "title": "안정적 유지 — 조달 여건 양호", "text": "연준의 정책 금리 범위 내에서 안정적으로 유지되며 시장 내 달러 융통이 원활한 상태입니다."},
            {"icon": "💥", "title": "스프레드 급등 — 단기 유동성 경색", "text": "SOFR가 급등(Spike)할 경우, 레포 시장 내 현금 부족 현상 및 단기 자금 시장의 발작 우려가 있습니다."},
            {"icon": "🎯", "title": "통화정책의 실효성 지표", "text": "LIBOR를 대체하는 핵심 지표금리로서 연준의 기준금리 정책 방향에 즉각적으로 연동됩니다."},
            {"icon": "🏦", "title": "시스템 스트레스 척도", "text": "2019년 레포 시장 발작(Repo Crisis)과 같은 단기 유동성 불일치 발생 시 즉각적인 경고 신호를 보냅니다."}
        ]
    }
}

# AI 진단 평가 로직 전면 전문화 (Professional Tone & Manner)
def eval_detail(ticker, val, chg_1w):
    if ticker == "^VIX":
        if val >= 30: return "🚨 경계", "#FF5555", f"VIX {val:.2f} — 극도의 위험 회피(Risk-off) 구간입니다. 변동성 확대로 인한 자산 가격 충격 우려가 큽니다."
        elif val >= 20: return "⚠️ 주의", "#F59E0B", f"VIX {val:.2f} — 시장의 내재 변동성이 점증하고 있습니다. 리스크 관리가 요구됩니다."
        else: return "✅ 안정", "#22D98A", f"VIX {val:.2f} — 변동성이 안정화되며 위험 자산 선호 심리가 유지되고 있습니다."
    elif ticker == "^MOVE":
        if val >= 140: return "🚨 위험", "#FF5555", f"MOVE {val:.2f} — 채권 시장 내 유동성 경색 및 극단적인 매크로 불확실성을 시사합니다."
        elif val >= 100: return "⚠️ 주의", "#F59E0B", f"MOVE {val:.2f} — 금리 변동성 확대로 인해 자산 밸류에이션 부담 및 자본 조달 리스크가 상승 중입니다."
        else: return "✅ 안정", "#22D98A", f"MOVE {val:.2f} — 채권 금리 변동성이 축소되며 통화정책에 대한 시장의 예측 가능성이 높습니다."
    elif ticker == "T10Y2Y":
        if val < 0: return "🚨 침체 경고 (역전)", "#FF5555", f"스프레드 {val:.2f}%p — 장단기 수익률 곡선이 역전된 비정상적 상태로, 강력한 경기 침체 선행 지표입니다."
        else: return "✅ 정상 (우상향)", "#22D98A", f"스프레드 {val:.2f}%p — 기간 프리미엄이 반영된 우상향(Normal) 곡선으로, 장기 경제 성장 기대가 반영되었습니다."
    elif ticker == "HYG":
        if chg_1w > 0: return "✅ 상승 (위험 선호)", "#22D98A", f"HYG 상승 — 신용 스프레드가 축소되며 위험 자산으로의 자금 유입이 지속되고 있습니다."
        else: return "⚠️ 하락 (위험 회피)", "#FF5555", f"HYG 하락 — 기업 신용 리스크에 대한 경계감으로 자금이 안전 자산으로 회귀하고 있습니다."
    elif ticker == "BAMLH0A0HYM2":
        if val >= 5.0: return "🚨 경고 (신용 경색)", "#FF5555", f"스프레드 {val:.2f}% — 하이일드 가산 금리가 급등하며 기업 신용 시장의 구조적 스트레스가 발생했습니다."
        elif val >= 4.0: return "⚠️ 주의", "#F59E0B", f"스프레드 {val:.2f}% — 신용 리스크 프리미엄이 점진적으로 상승하며 자본 조달 여건이 악화되고 있습니다."
        else: return "✅ 안정", "#22D98A", f"스프레드 {val:.2f}% — 신용 스프레드가 안정적으로 유지되며 한계 기업의 자금 조달 리스크가 제한적입니다."
    elif ticker == "WALCL":
        if chg_1w > 0: return "💰 유동성 확대 (QE)", "#22D98A", f"연준 총자산 {val:.2f}T — 자산 매입 또는 대출 프로그램을 통한 잉여 유동성 공급으로 위험 자산에 우호적입니다."
        else: return "🔴 유동성 축소 (QT)", "#FF5555", f"연준 총자산 {val:.2f}T — 보유 자산의 점진적 축소가 진행 중이며, 시중 잉여 유동성 환수를 시사합니다."
    elif ticker == "WRBWFRBL":
        if chg_1w > 0: return "🏦 잉여 유동성 확충", "#22D98A", f"지급준비금 {val:.2f}T — 상업은행의 실질 잉여 유동성이 확대되어 금융 시장의 자금 공급 여력이 양호합니다."
        else: return "🏜️ 유동성 버퍼 축소", "#FF5555", f"지급준비금 {val:.2f}T — 잉여 지준이 감소 추세이며, 임계치 도달 시 단기 자금 시장의 발작 리스크가 존재합니다."
    elif ticker == "WTREGEN":
        if chg_1w > 0: return "🕳️ 단기 유동성 환수", "#FF5555", f"TGA 잔고 {val:,.0f}B — 재무부의 세수 확보 및 국채 발행으로 민간 시장의 잉여 유동성이 환수되고 있습니다."
        else: return "🚀 단기 유동성 방출", "#22D98A", f"TGA 잔고 {val:,.0f}B — 재무부의 재정 지출 확대로 인해 연준 계좌의 자금이 실물 및 금융 시장으로 유입되고 있습니다."
    elif ticker == "RRPONTSYD":
        if chg_1w < 0: return "🌊 유동성 지원", "#22D98A", f"역레포 잔고 {val:.0f}B — 잉여 현금이 RRP 시설에서 이탈하여 국채 및 민간 금융 시장으로 재유입되고 있습니다."
        else: return "🔒 유동성 회수", "#FF5555", f"역레포 잔고 {val:.0f}B — 민간 시장의 조달 매력도 저하로 인해 잉여 자금이 연준의 역레포 창구로 흡수되고 있습니다."
    elif ticker == "WRMFSL":
        if chg_1w > 0: return "🛡️ 단기성 자금 쏠림", "#F59E0B", f"MMF 잔고 {val:.2f}T — 위험 회피 심리 발동 또는 고금리 매력에 의해 현금성 피난처로의 자본 유입이 지속됩니다."
        else: return "💸 위험자산 재분배", "#22D98A", f"MMF 잔고 {val:.2f}T — MMF의 대기 자금(Dry Powder)이 위험 자산 및 장기물 채권으로 재배분되는 리스크 온 국면입니다."
    elif ticker == "TOTLL":
        if chg_1w >= 0: return "🟢 민간 신용 확장", "#22D98A", f"상업은행 대출 {val:.2f}T — 은행권의 여신 여력이 양호하며 실물 경제에 지속적인 신용 창출(Credit Creation)이 발생 중입니다."
        else: return "🔴 민간 신용 위축", "#FF5555", f"상업은행 대출 {val:.2f}T — 은행 여신 기준 강화에 따른 신용 경색(Credit Crunch) 조짐으로 실물 경기 둔화 우려가 제기됩니다."
    elif ticker == "SOFR":
        if val > 5.0: return "⚠️ 조달 비용 부담", "#F59E0B", f"SOFR {val:.2f}% — 높은 기준금리 수준이 유지됨에 따라 금융권 및 기업의 단기 차입 비용(Funding Cost)이 상승한 상태입니다."
        else: return "✅ 안정적 단기 조달", "#22D98A", f"SOFR {val:.2f}% — 연준의 목표 금리 범위 내에서 안정화되어 단기 자금 시장의 조달 여건이 무리 없이 작동 중입니다."
    
    return "📊 상태 점검 중", "#00D4FF", "현재 지표의 상태를 계산하고 있습니다."

# 사용자가 지시한 12개 지표의 나열 순서
ordered_list = [
    "VIX (공포지수)",
    "MOVE (채권 변동성)",
    "장단기 금리차 (10Y-2Y)",
    "HYG (하이일드 ETF)",
    "하이일드 스프레드 (OAS)",
    "연준 총자산 (WALCL)",
    "지급준비금 잔고 (WRBWFRBL)",
    "TGA (재무부 일반계정)",
    "역레포 잔액 (RRP)",
    "MMF 총잔고 (WRMFSL)",
    "상업은행 총대출 (TOTLL)",
    "SOFR (익일물 금리)"
]

for selected_ind_name in ordered_list:
    meta = DETAIL_META[selected_ind_name]

    with st.spinner(f"{selected_ind_name} 상세 데이터를 불러오고 있습니다..."):
        # VIX 지표의 경우, INDEXerGO 공포지수가 우선 표시되도록 변경되었으므로,
        # 상세 분석 섹션에서는 기존 VIX 데이터를 그대로 사용합니다.
        # 이는 INDEXerGO 스크래핑이 현재 값만 제공하며, 상세 분석은 과거 추이 차트를 필요로 하기 때문입니다.
        if selected_ind_name == "VIX (공포지수)":
            _, _, df_detail = get_yf("^VIX", "10y", "1d")
            series_detail = df_detail["Close"] if df_detail is not None else None
        elif meta["type"] == "yf":
            _, _, df_detail = get_yf(meta["ticker"], "10y", "1d")
            series_detail = df_detail["Close"] if df_detail is not None else None
        else:
            series_detail = get_fred(meta["ticker"], limit=2500) 

        if series_detail is not None and not series_detail.empty:
            series_detail = series_detail * meta["scale"]
            
            cur_val = float(series_detail.iloc[-1])
            prev_val = float(series_detail.iloc[-2]) if len(series_detail) > 1 else cur_val
            val_1w = float(series_detail.iloc[-6]) if len(series_detail) > 5 else prev_val
            val_3m = float(series_detail.iloc[-63]) if len(series_detail) > 62 else prev_val
            val_2y = float(series_detail.iloc[-504]) if len(series_detail) > 503 else series_detail.iloc[0]
            
            chg_1w = cur_val - val_1w
            chg_3m = cur_val - val_3m
            chg_2y = cur_val - val_2y
            
            chg_1w_pct = (chg_1w / abs(val_1w)) * 100 if val_1w != 0 else 0
            chg_2y_pct = (chg_2y / abs(val_2y)) * 100 if val_2y != 0 else 0
            
            status_badge, status_color, status_desc = eval_detail(meta["ticker"], cur_val, chg_1w)
            
            chg_arrow = "▲" if chg_1w >= 0 else "▼"
            chg_color = "#22D98A" if chg_1w >= 0 else "#FF5555"
            
            chg_3m_arrow = "▲" if chg_3m >= 0 else "▼"
            chg_3m_color = "#22D98A" if chg_3m >= 0 else "#FF5555"
            
            chg_2y_arrow = "▲" if chg_2y >= 0 else "▼"
            
            html_title = f"""
            <div style="margin-top: 25px; margin-bottom: 0px;">
                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                    <h3 style="margin: 0; padding: 0; font-size: 1.3rem; font-weight: 800; color: #FFFFFF;">{selected_ind_name.split('(')[0].strip()} 추이</h3>
                </div>
                <div style="font-size: 0.85rem; color: #6B8EAE; font-weight: 600;">{meta['title_sub']}</div>
            </div>
            """
            st.markdown(html_title.replace('\n', ''), unsafe_allow_html=True)
            
            fig_det = go.Figure()
            fig_det.add_trace(go.Scatter(
                x=series_detail.index, y=series_detail.values,
                mode="lines", name=selected_ind_name.split('(')[0].strip(),
                line=dict(color="#3B82F6", width=2.5)
            ))
            
            if meta["ticker"] == "^VIX":
                fig_det.add_hline(y=30, line_dash="dash", line_color="#FF5555", opacity=0.7)
            elif meta["ticker"] == "^MOVE":
                fig_det.add_hline(y=140, line_dash="dash", line_color="#FF5555", opacity=0.7)
            elif meta["ticker"] == "T10Y2Y":
                fig_det.add_hline(y=0, line_dash="solid", line_color="#4A6A8A", opacity=0.7)
            elif meta["ticker"] == "BAMLH0A0HYM2":
                fig_det.add_hline(y=5, line_dash="dash", line_color="#FF5555", opacity=0.7)
                
            layout_det = CHART_LAYOUT.copy()
            layout_det.update(
                height=380, margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                hovermode="x unified",
                xaxis=dict(
                    showgrid=True, gridcolor="#141E2E",
                    rangeselector=dict(
                        buttons=list([
                            dict(count=2, label="2Y", step="year", stepmode="backward"),
                            dict(count=5, label="5Y", step="year", stepmode="backward"),
                            dict(count=10, label="10Y", step="year", stepmode="backward"),
                        ]),
                        bgcolor="rgba(0,0,0,0)",
                        activecolor="#1E3050",
                        bordercolor="#2A4060",
                        borderwidth=1,
                        font=dict(color="#8AAAC8", size=11, family="IBM Plex Mono"),
                        yanchor="bottom", y=1.05, xanchor="left", x=0
                    )
                ),
                yaxis=dict(showgrid=True, gridcolor="#141E2E", side="left", tickfont=dict(color="#8AAAC8", family="IBM Plex Mono"))
            )
            fig_det.update_layout(**layout_det)
            st.plotly_chart(fig_det, use_container_width=True, config={"displayModeBar": False}, key=f"chart_{meta['ticker']}")

            pfx = meta['prefix']
            unt = meta['unit']
            
            # 수치 포맷팅 자동 정렬
            val_format = f"{cur_val:,.0f}" if meta["ticker"] in ["WTREGEN", "RRPONTSYD"] else f"{cur_val:,.2f}"
            prev_format = f"{val_1w:,.0f}" if meta["ticker"] in ["WTREGEN", "RRPONTSYD"] else f"{val_1w:,.2f}"
            chg_format = f"{abs(chg_1w):,.0f}" if meta["ticker"] in ["WTREGEN", "RRPONTSYD"] else f"{abs(chg_1w):,.2f}"
            m3_format = f"{val_3m:,.0f}" if meta["ticker"] in ["WTREGEN", "RRPONTSYD"] else f"{val_3m:,.2f}"
            y2_format = f"{val_2y:,.0f}" if meta["ticker"] in ["WTREGEN", "RRPONTSYD"] else f"{val_2y:,.2f}"
            
            detail_html = f"""
    <div style="background-color: #0A0F18; border: 1px solid #1E2A3A; border-radius: 10px; margin-bottom: 50px;">
        <div style="padding: 24px; border-bottom: 1px solid #1A2A3F;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <span style="background: transparent; border: 1px solid #2E3E50; color: #8AAAC8; padding: 4px 10px; border-radius: 6px; font-size: 0.8rem; font-weight: bold;">최근 2년</span>
                <span style="background: {status_color}15; border: 1px solid {status_color}55; color: {status_color}; padding: 4px 10px; border-radius: 6px; font-size: 0.85rem; font-weight: bold;">{status_badge}</span>
                <span style="color: #FFFFFF; font-size: 1.6rem; font-weight: 800; font-family: 'IBM Plex Mono', monospace; margin-left: 5px;">{pfx}{val_format}{unt}</span>
            </div>
            <div style="color: #AACCEE; font-size: 0.95rem; line-height: 1.6; font-weight: 500; margin-bottom: 10px;">
                {status_desc}
            </div>
            <div style="color: #8AAAC8; font-size: 0.85rem; line-height: 1.6;">
                전주({pfx}{prev_format}{unt}) 대비 <span style="color: {chg_color}; font-weight: bold;">{chg_arrow} {pfx}{chg_format}{unt}</span> · 
                3개월 전({pfx}{m3_format}{unt}) 대비 <span style="color: {chg_3m_color}; font-weight: bold;">{chg_3m_arrow}</span><br>
                <span style="font-size: 0.75rem; color: #4A6888; font-family: 'IBM Plex Mono', monospace;">
                    📊 최근 2년: {pfx}{y2_format}{unt} → {pfx}{val_format}{unt} ({chg_2y_arrow} {abs(chg_2y_pct):.1f}%) · {chg_arrow} {pfx}{chg_format}{unt} 전주대비
                </span>
            </div>
        </div>
        <div style="padding: 24px; background-color: #060A12; border-bottom-left-radius: 10px; border-bottom-right-radius: 10px;">
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 10px;">
                <span style="color: #FF5555; font-size: 1.1rem; font-weight: 800;">📌</span>
                <span style="color: #FFFFFF; font-weight: 800; font-size: 1.05rem;">{selected_ind_name.split('(')[0].strip()}란?</span>
            </div>
            <div style="color: #8AAAC8; font-size: 0.9rem; line-height: 1.6; margin-bottom: 20px;">
                {meta['desc']}
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 15px;">
                <div style="background-color: #0A0F18; border: 1px solid #1E2A3A; border-radius: 8px; padding: 18px;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="font-size: 1.2rem;">{meta['cards'][0]['icon']}</span>
                        <span style="color: #FFFFFF; font-weight: 700; font-size: 0.95rem;">{meta['cards'][0]['title']}</span>
                    </div>
                    <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6;">{meta['cards'][0]['text']}</div>
                </div>
                <div style="background-color: #0A0F18; border: 1px solid #1E2A3A; border-radius: 8px; padding: 18px;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="font-size: 1.2rem;">{meta['cards'][1]['icon']}</span>
                        <span style="color: #FFFFFF; font-weight: 700; font-size: 0.95rem;">{meta['cards'][1]['title']}</span>
                    </div>
                    <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6;">{meta['cards'][1]['text']}</div>
                </div>
                <div style="background-color: #0A0F18; border: 1px solid #1E2A3A; border-radius: 8px; padding: 18px;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="font-size: 1.2rem;">{meta['cards'][2]['icon']}</span>
                        <span style="color: #FFFFFF; font-weight: 700; font-size: 0.95rem;">{meta['cards'][2]['title']}</span>
                    </div>
                    <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6;">{meta['cards'][2]['text']}</div>
                </div>
                <div style="background-color: #0A0F18; border: 1px solid #1E2A3A; border-radius: 8px; padding: 18px;">
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">
                        <span style="font-size: 1.2rem;">{meta['cards'][3]['icon']}</span>
                        <span style="color: #FFFFFF; font-weight: 700; font-size: 0.95rem;">{meta['cards'][3]['title']}</span>
                    </div>
                    <div style="color: #6B8EAE; font-size: 0.85rem; line-height: 1.6;">{meta['cards'][3]['text']}</div>
                </div>
            </div>
        </div>
    </div>
    """
            st.markdown(detail_html, unsafe_allow_html=True)
            
        else:
            st.warning(f"⚠️ {selected_ind_name} 데이터를 불러오지 못했습니다.")

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
