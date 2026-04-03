import streamlit as st
import pandas as pd
import yfinance as yf
import datetime
import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots
import numpy as np
import urllib.request
import json

# --- 페이지 설정 ---
st.set_page_config(page_title="Global Macro & Liquidity Dashboard", layout="wide")

st.markdown("""<style>
@import url("https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.8/dist/web/variable/pretendardvariable.css");
.stApp {
    background-color: #121824 !important;
    background-image: linear-gradient(180deg, #1a2235 0%, #0f151f 100%) !important;
    scroll-behavior: smooth;
}
html, body, [class*="css"], [class*="st-"] {
    font-family: "Pretendard Variable", Pretendard, -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #e2e8f0 !important;
}
[data-testid="block-container"] { max-width: 60% !important; padding-top: 2rem !important; }
div[data-testid="stVerticalBlock"] > div {padding-bottom: 0.1rem;}
.stRadio label { color: #fef08a !important; font-size: 0.85rem !important; }
hr { margin-top: 2.5rem; margin-bottom: 2.5rem; border: 0; height: 1px; background: linear-gradient(to right, rgba(212,175,55,0), rgba(212,175,55,0.4), rgba(212,175,55,0)); }
::-webkit-scrollbar {width: 6px; height: 6px;}
::-webkit-scrollbar-track {background: rgba(255,255,255,0.02);}
::-webkit-scrollbar-thumb {background: rgba(255,255,255,0.15); border-radius: 3px;}
::-webkit-scrollbar-thumb:hover {background: rgba(212,175,55,0.5);}
a.custom-link { text-decoration: none !important; color: inherit !important; display: block; height: 100%; }
.hover-card { transition: transform 0.2s ease, box-shadow 0.2s ease; cursor: pointer; }
.hover-card:hover { transform: translateY(-4px); box-shadow: 0 10px 25px rgba(0,0,0,0.5) !important; }
</style>""", unsafe_allow_html=True)

def custom_header(icon, title, desc):
    html = f"""<div style="margin-top: 0.5rem; margin-bottom: 1.5rem;"><div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;"><span style="font-size: 1.8rem;">{icon}</span><h2 style="margin: 0; padding: 0; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px; color: #f8fafc;">{title}</h2></div><div style="font-size: 0.9rem; color: #fef08a; opacity: 0.9; font-weight: 500; margin-left: 4px;">{desc}</div></div>"""
    st.markdown(html, unsafe_allow_html=True)

custom_header("👑", "시장 경제 지표 대시보드", "시장의 핵심 유동성 흐름과 매크로 지표를 심층적으로 추적합니다. (데이터 매일 자동 갱신)")

st.markdown("""<div style="font-size: 0.85rem; font-weight: 700; color: #D4AF37; margin-bottom: 6px; margin-top: 15px;">⏱️ 추이 기준 기간 선택</div>""", unsafe_allow_html=True)
period_options = {"1주일": 5, "1개월": 21, "3개월": 63, "6개월": 126, "1년": 252, "3년": 756}
selected_period_label = st.radio("기간", list(period_options.keys()), index=4, horizontal=True, label_visibility="collapsed")
selected_days = period_options[selected_period_label]
st.write("")

# ============================================================
# [핵심 수정 1] CNN Fear & Greed
# ============================================================
@st.cache_data(ttl=3600*2)
def fetch_cnn_fng():
    try:
        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Referer": "https://edition.cnn.com/",
            "Origin": "https://edition.cnn.com",
        }
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as response:  # [수정] 3초→10초
            data = json.loads(response.read().decode('utf-8'))
            return int(round(data['fear_and_greed']['score']))
    except Exception:
        return None

# ============================================================
# [핵심 수정 2] FRED 개별 로드 - 타임아웃 증가 + 날짜 필터 타입 수정
# ============================================================
@st.cache_data(ttl=3600*6, show_spinner=False)
def fetch_single_fred(name, series_id, start_str, end_str):
    """
    [수정] start/end를 string으로 받아 타입 충돌 완전 제거
    [수정] 타임아웃 3초 → 15초로 증가
    [수정] 컬럼명이 series_id가 아닐 경우도 처리
    """
    try:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as response:  # [수정] 15초
            data = pd.read_csv(response, index_col='DATE', parse_dates=True, na_values=['.', '', 'nan'])
            # [수정] 컬럼명이 series_id와 다를 수 있으므로 첫 번째 컬럼을 name으로 rename
            if len(data.columns) > 0:
                data = data.rename(columns={data.columns[0]: name})
            # [수정] string으로 날짜 필터 (타입 불일치 완전 제거)
            data = data.loc[start_str:end_str]
            data[name] = pd.to_numeric(data[name], errors='coerce')
            data = data.dropna()
            if not data.empty:
                return data
    except Exception as e:
        pass
    return pd.DataFrame()

# ============================================================
# [핵심 수정 3] Yahoo Finance - MultiIndex 처리 완전 재작성
# ============================================================
@st.cache_data(ttl=3600*6, show_spinner=False)
def fetch_yahoo_data(start_str, end_str):
    tickers = ['^GSPC', '^MOVE', 'DX-Y.NYB', '^KS11', '^KQ11', 'KRW=X', 'JPY=X', 'CL=F', 'EURUSD=X', 'GBPUSD=X', 'CNY=X', '^IXIC', 'ES=F', 'NQ=F']
    rename_map = {
        '^GSPC': 'SP500', '^MOVE': 'MOVE', 'DX-Y.NYB': 'DXY',
        '^KS11': 'KOSPI', '^KQ11': 'KOSDAQ', 'KRW=X': 'USDKRW',
        'JPY=X': 'USDJPY', 'CL=F': 'WTI', 'EURUSD=X': 'EURUSD',
        'GBPUSD=X': 'GBPUSD', 'CNY=X': 'USDCNY', '^IXIC': 'NASDAQ',
        'ES=F': 'ES_F', 'NQ=F': 'NQ_F'
    }
    try:
        # [수정] auto_adjust=True 명시, group_by 제거
        raw = yf.download(tickers, start=start_str, end=end_str, progress=False, auto_adjust=True)
        
        # [수정] MultiIndex 처리를 더 견고하게
        if isinstance(raw.columns, pd.MultiIndex):
            # 'Close' 레벨이 있으면 추출, 없으면 'Adj Close' 시도
            if 'Close' in raw.columns.get_level_values(0):
                df_yf = raw['Close'].copy()
            elif 'Adj Close' in raw.columns.get_level_values(0):
                df_yf = raw['Adj Close'].copy()
            else:
                # 첫 번째 레벨의 첫 항목 사용
                first_level = raw.columns.get_level_values(0)[0]
                df_yf = raw[first_level].copy()
        else:
            # 단일 컬럼인 경우 (티커 1개일 때)
            df_yf = raw.copy()
        
        df_yf = df_yf.rename(columns=rename_map)
        
        # [수정] timezone 제거
        if hasattr(df_yf.index, 'tz') and df_yf.index.tz is not None:
            df_yf.index = df_yf.index.tz_localize(None)
        
        return df_yf
    except Exception as e:
        st.error(f"Yahoo Finance 오류: {e}")
        return pd.DataFrame()

# ============================================================
# [핵심 수정 4] FRED 시리즈 ID 수정 + string 날짜 전달
# ============================================================
def load_all_data_sequentially():
    end_dt = datetime.datetime.today()
    start_dt = end_dt - datetime.timedelta(days=365*3)
    
    # [수정] string 형식으로 변환 (FRED/yfinance 모두 string이 안전)
    start_str = start_dt.strftime('%Y-%m-%d')
    end_str = end_dt.strftime('%Y-%m-%d')
    
    status_container = st.empty()
    progress_bar = st.progress(0)
    
    status_container.info("🔄 1단계: 야후 파이낸스 데이터 우선 로딩 중...")
    df_yf = fetch_yahoo_data(start_str, end_str)
    progress_bar.progress(20)
    
    if df_yf.empty:
        status_container.warning("⚠️ Yahoo Finance 데이터 로드 실패. FRED 데이터만으로 진행합니다.")
    else:
        status_container.success(f"✅ Yahoo Finance 로드 완료 ({len(df_yf.columns)}개 컬럼)")
    
    # [수정] FRED 시리즈 ID 검증 완료 버전
    fred_series = {
        'VIX':             'VIXCLS',        # VIX (CBOE)
        'HY_Spread':       'BAMLH0A0HYM2',  # HY OAS 스프레드
        'FSI':             'STLFSI2',       # [수정] STLFSI4 → STLFSI2
        '10Y_2Y':          'T10Y2Y',        # 장단기 금리차
        '10Y':             'DGS10',         # 10년물
        '2Y':              'DGS2',          # 2년물
        'Fed_BS':          'WALCL',         # 연준 총자산 (단위: 백만달러)
        'WRESBAL_Ind':     'WRESBAL',       # 은행 준비금
        'Reserves':        'WRESBAL',       # 동일
        'RRP':             'RRPONTSYD',     # 역레포
        'TGA':             'WTREGEN',       # TGA
        'MMF':             'WRMFSL',        # [수정] WRMFNS → WRMFSL (소매 MMF)
        'TOTLL':           'TOTLL',         # 상업은행 총대출
        'SOFR':            'SOFR',          # SOFR
        'IORB':            'IORB',          # IORB
        'EFFR':            'EFFR',          # EFFR
        'T10YIE':          'T10YIE',        # 기대인플레이션
        'Discount_Window': 'WLCFLL',        # [수정] WLCFLPCL → WLCFLL (할인창구)
        'BTFP':            'H41RESPALBFRB', # BTFP
        'ACMTP10':         'ACMTP10',       # 기간 프리미엄
    }
    
    fred_list = []
    total = len(fred_series)
    
    for i, (name, sid) in enumerate(fred_series.items()):
        status_container.info(f"🔄 2단계: FRED 지표 로딩 중... [{name} ({sid})] ({i+1}/{total})")
        
        # [수정] string 날짜 전달
        df_s = fetch_single_fred(name, sid, start_str, end_str)
        
        if not df_s.empty:
            # [수정] 단위 스케일링 - WALCL은 백만달러 단위이므로 /100 → 억달러
            if name in ['Fed_BS', 'WRESBAL_Ind', 'Reserves', 'TGA', 'Discount_Window', 'BTFP']:
                df_s[name] = df_s[name] / 100  # 백만 → 억
            elif name in ['MMF', 'RRP', 'TOTLL']:
                df_s[name] = df_s[name] * 10   # 십억 → 억 (FRED 단위가 billions)
            fred_list.append(df_s)
        else:
            status_container.warning(f"⚠️ {name} ({sid}) 로드 실패 - 건너뜀")
        
        progress_bar.progress(20 + int(70 * (i+1)/total))
    
    status_container.info("🔄 3단계: 데이터 병합 및 파생 지표 계산 중...")
    
    df_fred = pd.concat(fred_list, axis=1) if fred_list else pd.DataFrame()
    
    # [수정] concat 전 빈 df 체크를 더 안전하게
    dfs_to_concat = [x for x in [df_fred, df_yf] if not x.empty]
    if dfs_to_concat:
        df_raw = pd.concat(dfs_to_concat, axis=1)
        df_raw = df_raw.sort_index()
        # [수정] 중복 컬럼 제거 (WRESBAL이 두 번 들어갈 경우)
        df_raw = df_raw.loc[:, ~df_raw.columns.duplicated(keep='first')]
    else:
        df_raw = pd.DataFrame()
    
    df_merged = df_raw.ffill().bfill().fillna(0) if not df_raw.empty else pd.DataFrame()
    
    # 파생 지표 계산
    if not df_merged.empty:
        if all(c in df_merged.columns for c in ['Fed_BS', 'RRP', 'TGA']):
            df_merged['Net_Liquidity'] = df_merged['Fed_BS'] - df_merged['RRP'] - df_merged['TGA']
            df_raw['Net_Liquidity'] = df_raw['Fed_BS'] - df_raw['RRP'] - df_raw['TGA']
        
        if all(c in df_merged.columns for c in ['SOFR', 'IORB']):
            df_merged['SOFR_IORB_Spread'] = df_merged['SOFR'] - df_merged['IORB']
            df_raw['SOFR_IORB_Spread'] = df_raw['SOFR'] - df_raw['IORB']
        
        if all(c in df_merged.columns for c in ['SOFR', 'EFFR']):
            df_merged['SOFR_EFFR_Spread'] = df_merged['SOFR'] - df_merged['EFFR']
            df_raw['SOFR_EFFR_Spread'] = df_raw['SOFR'] - df_raw['EFFR']
        
        if all(c in df_merged.columns for c in ['Discount_Window', 'BTFP']):
            df_merged['Emergency_Loans'] = df_merged['Discount_Window'] + df_merged['BTFP']
            df_raw['Emergency_Loans'] = df_raw['Discount_Window'] + df_raw['BTFP']
        elif 'Discount_Window' in df_merged.columns:
            # BTFP가 없어도 Discount Window만으로 Emergency_Loans 구성
            df_merged['Emergency_Loans'] = df_merged['Discount_Window']
            df_raw['Emergency_Loans'] = df_raw['Discount_Window']
    
    status_container.empty()
    progress_bar.empty()
    
    return df_merged, df_raw

# ============================================================
# 데이터 로드
# ============================================================
df, df_raw = load_all_data_sequentially()

# [수정] 로드된 컬럼 현황 디버그 표시 (개발 중에만)
with st.expander("🔧 [디버그] 로드된 데이터 현황", expanded=False):
    if not df.empty:
        st.write(f"✅ 로드된 컬럼 수: {len(df.columns)}")
        st.write(f"✅ 로드된 컬럼 목록: {sorted(df.columns.tolist())}")
        st.write(f"✅ 데이터 기간: {df.index[0].date()} ~ {df.index[-1].date()}")
        st.write(f"✅ 데이터 행 수: {len(df)}")
    else:
        st.error("❌ 데이터 로드 완전 실패")

missing_cols = [c for c in ['VIX', '10Y_2Y', 'Fed_BS', 'SP500'] if c not in df.columns]
if missing_cols:
    st.warning(f"🚨 일부 지표({', '.join(missing_cols)})가 누락되었습니다. 새로고침하거나 잠시 후 다시 시도하세요.")

# --- 색상 상수 ---
COLOR_SAFE    = "#4ade80"
COLOR_WARN    = "#facc15"
COLOR_DANGER  = "#f87171"
COLOR_NEUTRAL = "#fef08a"
ACCENT_GOLD   = "#D4AF37"
ACCENT_KOREA  = "#10b981"
ACCENT_US     = "#3b82f6"

# --- 평가 함수들 ---
def eval_vix(v, d):
    if v >= 30: return "경계", COLOR_DANGER, "투자자들이 겁먹은 상태입니다."
    elif v >= 20: return "주의", COLOR_WARN, "불안이 커지고 있습니다."
    else: return "안정", COLOR_SAFE, "시장이 조용하고 투자자들이 편안한 상태입니다."

def eval_move(v, d):
    if v >= 140: return "위험", COLOR_DANGER, "채권 시장이 패닉에 빠졌습니다."
    elif v >= 100: return "주의", COLOR_WARN, "채권 금리가 요동치고 있습니다."
    else: return "안정", COLOR_SAFE, "채권 시장이 평온합니다."

def eval_10y2y(v, d):
    if v < 0: return "침체 경고 (역전)", COLOR_DANGER, "단기금리가 장기금리를 역전했습니다."
    else: return "정상 (양수)", COLOR_SAFE, "장기금리>단기금리로 경제 성장 기대가 반영된 상태입니다."

def eval_fsi(v, d):
    if v > 0: return "스트레스", COLOR_DANGER, "금융 시스템 내에 긴장 상태가 높아졌습니다."
    else: return "안정", COLOR_SAFE, "금융 시스템이 원활하게 작동하고 있습니다."

def eval_hy(v, d):
    if v >= 5.0: return "경고", COLOR_DANGER, "기업들의 자금줄이 마르고 부도 위험이 커진 상태입니다."
    elif v >= 4.0: return "주의", COLOR_WARN, "자금 조달 여건이 빡빡해지고 있습니다."
    else: return "안정", COLOR_SAFE, "하이일드 채권 시장이 안정적입니다."

def eval_fed(v, d):
    if d > 0: return "팽창 (QE)", COLOR_SAFE, "연준이 시중에 유동성을 공급 중입니다."
    else: return "긴축 (QT)", COLOR_DANGER, "연준이 시중의 달러를 흡수하고 있습니다."

def eval_reserves(v, d):
    if d > 0: return "확대", COLOR_SAFE, "은행들의 금고가 두둑해졌습니다."
    else: return "축소", COLOR_DANGER, "은행들의 자금 여력이 줄어들고 있습니다."

def eval_rrp(v, d):
    if v == 0: return "고갈", COLOR_DANGER, "역레포 대기 자금이 소진되었습니다."
    elif v < 1000: return "바닥 근접", COLOR_WARN, "잉여 자금이 거의 바닥을 드러내고 있습니다."
    elif d > 0: return "위험 회피", COLOR_DANGER, "시중 자금이 연준 금고로 대피하고 있습니다."
    else: return "위험 선호", COLOR_SAFE, "역레포 자금이 증시로 흘러들어가고 있습니다."

def eval_tga(v, d):
    if d > 0: return "자금 흡수", COLOR_DANGER, "재무부가 시중 자금을 흡수 중입니다."
    else: return "재정 지출", COLOR_SAFE, "재무부가 시중에 자금을 펌핑하고 있습니다."

def eval_totll(v, d):
    if d > 0: return "신용 팽창", COLOR_SAFE, "상업은행 대출이 늘어나고 있습니다."
    elif d < 0: return "신용 축소", COLOR_DANGER, "은행이 대출 문턱을 높였습니다(Credit Crunch)."
    else: return "정체", COLOR_WARN, "대출 규모가 관망세를 보이고 있습니다."

def eval_sofr(v, d):
    if v > 0.05: return "발작 조짐", COLOR_DANGER, "극심한 달러 가뭄 현상이 발생했습니다!"
    elif v > 0: return "타이트", COLOR_WARN, "단기 자금 시장의 달러 유동성이 빠듯해지고 있습니다."
    else: return "안정", COLOR_SAFE, "단기 레포 시장의 달러 융통이 원활합니다."

def eval_sofr_effr(v, d):
    if v >= 0.05: return "경색 경고", COLOR_DANGER, "단기 자금 시장에 심각한 경색이 발생했습니다."
    elif v > 0: return "주의", COLOR_WARN, "레포 시장의 달러 유동성이 타이트해지고 있습니다."
    else: return "안정", COLOR_SAFE, "단기 자금 조달 시장이 안정적으로 작동하고 있습니다."

def eval_emerg(v, d):
    if v > 500: return "위기", COLOR_DANGER, "은행들이 연준에서 긴급 자금을 대거 빌려가고 있습니다!"
    elif v > 0: return "주의", COLOR_WARN, "일부 은행이 연준의 긴급 차입을 이용했습니다."
    else: return "매우 안정", COLOR_SAFE, "연준의 긴급 대출 잔액이 '0'으로 완벽히 정상입니다."

def eval_mmf(v, d):
    if d > 0: return "자금 대피", COLOR_WARN, "투자자들이 단기 현금(MMF)으로 피신 중입니다."
    else: return "위험 선호", COLOR_SAFE, "MMF 대기 자금이 위험 자산으로 유입되고 있습니다."

def eval_dxy(v, d):
    if v >= 105: return "강세", COLOR_DANGER, "강달러로 신흥국 자본 이탈 및 글로벌 유동성 축소가 우려됩니다."
    elif v < 100: return "약세", COLOR_SAFE, "달러 약세로 글로벌 증시 랠리에 매우 우호적입니다."
    else: return "중립", COLOR_NEUTRAL, "달러가 박스권에서 안정적으로 유지됩니다."

def eval_bei(v, d):
    if v >= 2.5: return "물가 불안", COLOR_DANGER, "인플레이션 고착화 우려로 연준의 금리 인하가 지연될 가능성이 큽니다."
    elif v <= 2.0: return "디스인플레", COLOR_WARN, "물가가 너무 빨리 식으며 경기 둔화 우려가 있습니다."
    else: return "골디락스", COLOR_SAFE, "연준의 물가 목표치(2%) 근방에서 안정적으로 움직이고 있습니다."

INDICATOR_META = {
    'VIX': {'name': 'VIX 변동성 지수', 'short_name': 'VIX', 'unit': 'pt', 'inverted': True,
            'meta': '단위: 포인트 · 일간 · 20 이상 = 주의 / 30 이상 = 경계',
            'desc': '시장이 앞으로 얼마나 출렁일지 예상하는 지수입니다. 주가가 급락할 때 VIX는 급등합니다.',
            'eval': eval_vix,
            'levels': [("20 미만", "안정", COLOR_SAFE, "😌", "시장이 조용하고 위험자산 선호."),
                       ("20~30", "주의", COLOR_WARN, "🙄", "불확실성이 커지는 구간입니다."),
                       ("30 이상", "경계", COLOR_DANGER, "😱", "과거 주요 시장 충격 때 항상 이 구간을 넘었습니다.")]},
    'MOVE': {'name': 'MOVE 채권 변동성 지수', 'short_name': 'MOVE', 'unit': 'pt', 'inverted': True,
             'meta': '단위: 포인트 · 일간 · 100 이상 = 주의',
             'desc': '미국 국채 시장의 변동성을 보여주는 채권판 VIX입니다.',
             'eval': eval_move,
             'levels': [("100 미만", "안정", COLOR_SAFE, "😌", "채권 금리가 안정적입니다."),
                        ("100~140", "주의", COLOR_WARN, "⚠️", "금리 변동성이 확대되고 있습니다."),
                        ("140 이상", "위험", COLOR_DANGER, "🚨", "시스템 리스크 발생 구간입니다.")]},
    '10Y_2Y': {'name': '미국 장단기 금리차 (10Y-2Y)', 'short_name': '장단기 금리차', 'unit': '%', 'inverted': False,
               'meta': '단위: % · 일간 · 음수 = 역전 (침체 경고)',
               'desc': '10년 금리에서 2년 금리를 뺀 값입니다. 역전은 경기침체의 강력한 경고 신호입니다.',
               'eval': eval_10y2y,
               'levels': [("양수(+) — 정상", "안정", COLOR_SAFE, "📈", "경제 성장 기대가 반영된 건강한 상태입니다."),
                          ("음수(-) — 역전", "침체 경고", COLOR_DANGER, "📉", "과거 50년간 모든 미국 경기침체 전에 나타났습니다."),
                          ("역전 후 상승 전환", "주의", COLOR_WARN, "⏱️", "역전 해소 시점이 실제 침체 시작과 맞물리는 경향이 있습니다.")]},
    'FSI': {'name': '금융 스트레스 지수 (FSI)', 'short_name': 'FSI', 'unit': 'pt', 'inverted': True,
            'meta': '단위: 포인트 · 주간 · 0 이상 = 스트레스 상태',
            'desc': '18개 주요 금융 시장 지표를 종합한 미국 금융 시스템 스트레스 지수입니다.',
            'eval': eval_fsi,
            'levels': [("0 미만", "안정", COLOR_SAFE, "✅", "금융 시스템이 원활하게 작동하고 있습니다."),
                       ("0 이상", "스트레스", COLOR_DANGER, "💥", "평균 이상의 시스템 긴장 상태입니다.")]},
    'HY_Spread': {'name': '하이일드 스프레드', 'short_name': '하이일드 스프레드', 'unit': '%', 'inverted': True,
                  'meta': '단위: % · 일간 · 5% 이상 = 경색 경고',
                  'desc': '미국 국채와 정크본드 간의 금리 격차입니다.',
                  'eval': eval_hy,
                  'levels': [("4% 미만", "안정", COLOR_SAFE, "👍", "풍부한 유동성 환경입니다."),
                             ("4~5%", "주의", COLOR_WARN, "🤔", "신용 경계감이 상승하고 있습니다."),
                             ("5% 이상", "경고", COLOR_DANGER, "🔥", "신용 경색 구간입니다.")]},
    'Fed_BS': {'name': '연준 대차대조표 총자산', 'short_name': '연준 총자산', 'unit': '억 달러', 'inverted': False,
               'meta': '단위: 억 달러 · 주간 · 상승 = 유동성 공급',
               'desc': '미국 중앙은행(Fed)이 보유하고 있는 자산의 총합입니다.',
               'eval': eval_fed,
               'levels': [("상승 (QE)", "팽창", COLOR_SAFE, "💸", "시중에 자금을 공급합니다."),
                          ("하락 (QT)", "긴축", COLOR_DANGER, "🧽", "시중의 달러를 흡수합니다.")]},
    'WRESBAL_Ind': {'name': 'WRESBAL (은행 준비금)', 'short_name': 'WRESBAL', 'unit': '억 달러', 'inverted': False,
                    'meta': '단위: 억 달러 · 주간 · 상승 = 유동성 공급',
                    'desc': '상업은행들이 연방준비제도(Fed) 계좌에 예치해둔 준비금 잔액입니다.',
                    'eval': eval_reserves,
                    'levels': [("잔액 증가", "확대", COLOR_SAFE, "🏦", "은행의 자금 여력이 증가합니다."),
                               ("잔액 감소", "축소", COLOR_DANGER, "🏜️", "유동성이 마르기 시작합니다.")]},
    'Reserves': {'name': '지급준비금 (Reserves)', 'short_name': '지급준비금', 'unit': '억 달러', 'inverted': False,
                 'meta': '단위: 억 달러 · 주간 · 실제 금융권 유동성 체력',
                 'desc': '상업은행들이 연준 금고에 예치해둔 대기 자금입니다.',
                 'eval': eval_reserves,
                 'levels': [("상승/유지", "확대", COLOR_SAFE, "🏦", "은행의 자금 여력이 증가합니다."),
                            ("하락", "축소", COLOR_DANGER, "🏜️", "유동성이 마르기 시작합니다.")]},
    'RRP': {'name': '역레포 잔액 (RRP)', 'short_name': '역레포 잔액', 'unit': '억 달러', 'inverted': True,
            'meta': '단위: 억 달러 · 일간 · 하락 = 증시로 자금 유입',
            'desc': '시중에 갈 곳을 잃은 단기 잉여 자금이 연준 창고로 들어간 금액입니다.',
            'eval': eval_rrp,
            'levels': [("방출 (감소)", "위험 선호", COLOR_SAFE, "🌊", "실물 및 증시로 유입되는 강세 요인입니다."),
                       ("흡수 (증가)", "위험 회피", COLOR_DANGER, "🔒", "시중 자금이 연준 금고로 피신하는 약세 요인입니다."),
                       ("0 근접", "고갈 경고", COLOR_WARN, "🪫", "유동성 절벽이 우려됩니다.")]},
    'TGA': {'name': '재무부 일반 계좌 (TGA)', 'short_name': 'TGA 잔액', 'unit': '억 달러', 'inverted': True,
            'meta': '단위: 억 달러 · 주간 · 정부의 마이너스 통장',
            'desc': '미국 정부가 사용하는 메인 통장입니다.',
            'eval': eval_tga,
            'levels': [("잔액 감소", "재정 지출", COLOR_SAFE, "🚀", "시중에 돈을 펌핑하는 긍정적 상태입니다."),
                       ("잔액 증가", "자금 흡수", COLOR_DANGER, "🕳️", "시중 유동성을 빨아들이는 단기 악재입니다.")]},
    'TOTLL': {'name': 'H.8 상업은행 총대출', 'short_name': '상업은행 총대출', 'unit': '억 달러', 'inverted': False,
              'meta': '단위: 억 달러 · 주간 · 실물 경제 신용 공급 지표',
              'desc': '미국 내 상업은행들이 기업과 가계에 실제로 빌려준 대출의 총액입니다.',
              'eval': eval_totll,
              'levels': [("대출 증가", "신용 팽창", COLOR_SAFE, "🟢", "경제가 활력을 띠고 있습니다."),
                         ("대출 감소", "신용 축소", COLOR_DANGER, "🔴", "Credit Crunch 경기 침체 전조증상입니다.")]},
    'SOFR_IORB_Spread': {'name': '단기 조달 스프레드 (SOFR - IORB)', 'short_name': '조달 스프레드', 'unit': '%', 'inverted': True,
                         'meta': '단위: % · 일간 · 0.05% 이상 = 단기 자금 발작',
                         'desc': '은행간 실제 조달금리(SOFR)에서 연준 예치금리(IORB)를 뺀 값입니다.',
                         'eval': eval_sofr,
                         'levels': [("0% 이하", "안정", COLOR_SAFE, "😌", "달러 조달이 매우 원활합니다."),
                                    ("0 ~ 0.05%", "주의", COLOR_WARN, "⚡", "유동성이 타이트해지고 있습니다."),
                                    ("0.05% 이상", "발작 경고", COLOR_DANGER, "💥", "극심한 달러 가뭄 현상입니다.")]},
    'SOFR_EFFR_Spread': {'name': 'SOFR / EFFR 스프레드', 'short_name': 'SOFR-EFFR', 'unit': '%', 'inverted': True,
                         'meta': '단위: % · 일간 · 0.05% 이상 = 경색 경고',
                         'desc': '담보 대출금리(SOFR)와 무담보 대출금리(EFFR)의 차이입니다.',
                         'eval': eval_sofr_effr,
                         'levels': [("0% 이하", "안정", COLOR_SAFE, "😌", "정상적으로 작동 중입니다."),
                                    ("0 ~ 0.05%", "주의", COLOR_WARN, "⚡", "기현상이 발생하기 시작했습니다."),
                                    ("0.05% 이상", "경계", COLOR_DANGER, "💥", "시스템 리스크가 커지고 있습니다.")]},
    'Emergency_Loans': {'name': '연준 긴급대출 총액 (할인창구 + BTFP)', 'short_name': '긴급대출 잔액', 'unit': '억 달러', 'inverted': True,
                        'meta': '단위: 억 달러 · 주간 · 은행 시스템 위기 지표',
                        'desc': '유동성 위기에 처한 은행들이 연준의 비상 창구를 통해 긴급하게 빌려간 구제 자금의 총합입니다.',
                        'eval': eval_emerg,
                        'levels': [("0 (또는 극소액)", "안정", COLOR_SAFE, "🏥", "위기 징후 없음."),
                                   ("수백억 달러 급등", "위기 발생", COLOR_DANGER, "🚑", "뱅크런이나 유동성 위기가 발생했습니다.")]},
    'MMF': {'name': '머니마켓펀드 (MMF) 잔액', 'short_name': 'MMF 잔액', 'unit': '억 달러', 'inverted': True,
            'meta': '단위: 억 달러 · 주간 · 대기 자금 흐름',
            'desc': '투자자들이 초단기 금융상품(MMF)에 파킹해둔 자금 총액입니다.',
            'eval': eval_mmf,
            'levels': [("잔액 감소", "위험 선호", COLOR_SAFE, "💸", "위험 자산으로 적극 투자하는 긍정적 신호입니다."),
                       ("잔액 증가", "자금 대피", COLOR_WARN, "🛡️", "현금으로 관망하는 상태입니다.")]},
    'DXY': {'name': 'DXY 달러 인덱스', 'short_name': '달러 인덱스', 'unit': 'pt', 'inverted': True,
            'meta': '단위: 포인트 · 일간 · 글로벌 달러 가치',
            'desc': '유로, 엔 등 주요 6개국 통화 대비 미국 달러의 평균 가치를 보여줍니다.',
            'eval': eval_dxy,
            'levels': [("100 미만", "약세", COLOR_SAFE, "📉", "달러 약세로 글로벌 증시 랠리에 유리합니다."),
                       ("100~105", "중립", COLOR_NEUTRAL, "⚖️", "시장 영향이 중립적입니다."),
                       ("105 이상", "강세", COLOR_DANGER, "📈", "달러 초강세로 증시 부담이 가중됩니다.")]},
    'T10YIE': {'name': '10년물 기대인플레이션 (BEI)', 'short_name': '기대인플레이션', 'unit': '%', 'inverted': False,
               'meta': '단위: % · 일간 · 채권 시장의 물가 전망',
               'desc': '채권 시장 참여자들이 예상하는 향후 10년간의 평균 인플레이션율입니다.',
               'eval': eval_bei,
               'levels': [("2.0% ~ 2.5%", "골디락스", COLOR_SAFE, "🎯", "연준의 장기 목표치에 부합합니다."),
                          ("2.0% 미만", "디스인플레", COLOR_WARN, "❄️", "경기 침체 및 수요 둔화 우려가 반영된 구간입니다."),
                          ("2.5% 이상", "인플레 고착화", COLOR_DANGER, "🔥", "연준의 금리 인하가 지연될 수 있습니다.")]}
}

# --- 공통 헬퍼 함수들 ---
def hex_to_rgba(hex_color, alpha=0.15):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{alpha})'

def format_val(v, unit, is_sofr=False):
    if unit == '%': return f"{v:.3f}%" if is_sofr else f"{v:.2f}%"
    if unit == 'pt': return f"{v:.2f}"
    if unit == '억 달러': return f"{v:,.0f}억 달러"
    return str(v)

def format_chg_text(cur, prev, unit, is_inverted, is_sofr=False):
    diff = cur - prev
    color = COLOR_SAFE if (diff < 0 if is_inverted else diff > 0) else COLOR_DANGER
    if abs(diff) < 0.001: color = COLOR_NEUTRAL
    arrow = "▼" if diff < 0 else "▲" if diff > 0 else "-"
    val_str = (f"{abs(diff):.3f}%p" if is_sofr else f"{abs(diff):.2f}%p") if unit == '%' else \
              (f"{abs(diff):.2f}pt" if unit == 'pt' else f"{abs(diff):,.0f}억 달러")
    dir_text = "상승" if (diff > 0 and unit in ['pt', '%']) else "증가" if diff > 0 else "하락" if unit in ['pt', '%'] else "감소"
    if abs(diff) < 0.001:
        return "<span style='color: #fef08a; opacity: 0.8; font-weight: bold;'>변동 없음</span>", color
    return f"<span style='color: {color}; font-weight: bold;'>{arrow} {val_str} {dir_text}</span>", color

def get_last_two(series, scale=1.0):
    clean = series.dropna()
    if len(clean) >= 2:
        return clean.values[-2:] * scale
    elif len(clean) == 1:
        return np.array([clean.values[0] * scale, clean.values[0] * scale])
    return np.array([0.0, 0.0])

def make_diff_str(cur, prev, unit='', invert=False, period='전일 대비'):
    diff = cur - prev
    color = COLOR_SAFE if (diff < 0 if invert else diff > 0) else COLOR_DANGER
    if abs(diff) < 0.001: color = COLOR_NEUTRAL
    arrow = "▼" if diff < 0 else "▲" if diff > 0 else "-"
    if unit == '원': val_str = f"{abs(diff):.0f}원"
    elif unit == '엔': val_str = f"{abs(diff):.1f}엔"
    elif unit == '%': val_str = f"{abs(diff):.2f}%p"
    elif unit == 'B': val_str = f"${abs(diff):.2f}B"
    elif unit == 'T': val_str = f"${abs(diff):.2f}T"
    else: val_str = f"{abs(diff):.2f}"
    if abs(diff) < 0.001: return "변동 없음", color
    return f"{arrow} {val_str} {period}", color

def render_mini_card(title, val_str, diff_data, footer, accent_color, target_id="", is_highlight=False):
    diff_text, diff_color = diff_data
    bg_color = hex_to_rgba(diff_color, 0.15) if diff_color.startswith('#') else "rgba(148,163,184,0.15)"
    card_bg = "linear-gradient(145deg, rgba(249,115,22,0.2) 0%, rgba(249,115,22,0.05) 100%)" if is_highlight else "#1e293b"
    border_css = "border: 1px solid rgba(249,115,22,0.4);" if is_highlight else "border: 1px solid rgba(255,255,255,0.05);"
    title_color = "#ffffff" if is_highlight else "#fef08a"
    footer_color = "rgba(255,255,255,0.8)" if is_highlight else "#fef08a"
    footer_opacity = "1.0" if is_highlight else "0.7"
    card_html = f'<div class="hover-card" style="background: {card_bg}; {border_css} border-radius: 12px; padding: 20px; position: relative; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.2); height: 100%;"><div style="position: absolute; top: 0; left: 0; bottom: 0; width: 4px; background: {accent_color};"></div><div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; padding-left: 8px;"><div style="color: {title_color}; font-size: 0.9rem; font-weight: 700; letter-spacing: -0.3px;">{title}</div><div style="background: {bg_color}; color: {diff_color}; padding: 4px 8px; border-radius: 6px; font-size: 0.75rem; font-weight: 800;">{diff_text}</div></div><div style="color: #ffffff; font-size: 1.7rem; font-weight: 800; padding-left: 8px; line-height: 1.2; margin-bottom: 8px;">{val_str}</div><div style="color: {footer_color}; opacity: {footer_opacity}; font-size: 0.75rem; padding-left: 8px; font-weight: 500;">{footer}</div></div>'
    if target_id:
        return f'<a href="#{target_id}" class="custom-link">{card_html}</a>'
    return card_html

def render_detailed_indicator(key, df, days):
    if key not in df.columns:
        st.warning(f"⚠️ {INDICATOR_META[key]['name']} 데이터를 불러오지 못했습니다.")
        return
    meta = INDICATOR_META[key]
    sub_df = df[key].dropna().tail(days)
    if len(sub_df) < 2: return
    cur = sub_df.iloc[-1]
    val_1w = sub_df.iloc[-min(6, len(sub_df))]
    val_3m = df[key].dropna().tail(min(63, len(df[key].dropna()))).iloc[0]
    chg_1w = cur - val_1w
    status_label, status_color, status_text = meta['eval'](cur, chg_1w)
    is_sofr = (key in ['SOFR_IORB_Spread', 'SOFR_EFFR_Spread'])
    is_inverted = meta['inverted']
    chg_1w_html, _ = format_chg_text(cur, val_1w, meta['unit'], is_inverted, is_sofr)
    chg_3m_html, _ = format_chg_text(cur, val_3m, meta['unit'], is_inverted, is_sofr)

    extra_info_html = ""
    if key == '10Y_2Y' and '10Y' in df.columns and '2Y' in df.columns:
        try:
            val_10y = df['10Y'].dropna().iloc[-1]
            val_2y  = df['2Y'].dropna().iloc[-1]
            extra_info_html = f'<div style="font-size: 0.85rem; background-color: rgba(255,255,255,0.05); padding: 12px 16px; border-radius: 10px; margin-top: 10px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);"><b style="color: {ACCENT_GOLD};">💡 상세 분석:</b> 현재 미국 10년물 국채 금리는 <b>{val_10y:.2f}%</b>, 2년물 국채 금리는 <b>{val_2y:.2f}%</b>입니다. 따라서 두 금리의 차이(10년물 - 2년물)는 <b style="color:{status_color}">{cur:.2f}%</b>가 됩니다.</div>'
        except: pass

    header_html = f'<div id="{key}" style="margin-top: 1rem; scroll-margin-top: 80px;"><div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 2px;"><h3 style="margin: 0; padding: 0; font-size: 1.2rem; font-weight: 800; letter-spacing: -0.5px; color: #f8fafc;">{meta["name"]}</h3></div><div style="color: #fef08a; opacity: 0.9; font-size: 0.75rem; font-weight: 500; margin-bottom: 0.5rem;">{meta["meta"]}</div></div>'
    st.markdown(header_html, unsafe_allow_html=True)

    is_10y2y = (key == '10Y_2Y' and '10Y' in df.columns and '2Y' in df.columns)
    if is_10y2y:
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(plotly_go.Scatter(x=sub_df.index, y=df['10Y'].tail(days), mode='lines', name='10년물 금리', line=dict(color='#60a5fa', width=1.5, dash='dot'), opacity=0.7), secondary_y=True)
        fig.add_trace(plotly_go.Scatter(x=sub_df.index, y=df['2Y'].tail(days), mode='lines', name='2년물 금리', line=dict(color='#f87171', width=1.5, dash='dot'), opacity=0.7), secondary_y=True)
        fig.add_trace(plotly_go.Scatter(x=sub_df.index, y=sub_df, mode='lines', name='금리차(10Y-2Y)', line=dict(color='#a3e635', width=3.0), fill='tozeroy', fillcolor=hex_to_rgba('#a3e635', 0.15)), secondary_y=False)
        min_spread, max_spread = sub_df.min(), sub_df.max()
        pad_sp = (max_spread - min_spread) * 0.2 if max_spread != min_spread else 0.5
        fig.update_yaxes(range=[min_spread - pad_sp, max_spread + pad_sp], secondary_y=False, showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#a3e635'), zeroline=True, zerolinecolor='rgba(255,255,255,0.4)')
        min_rate = min(df['10Y'].tail(days).min(), df['2Y'].tail(days).min())
        max_rate = max(df['10Y'].tail(days).max(), df['2Y'].tail(days).max())
        pad_rate = (max_rate - min_rate) * 0.2 if max_rate != min_rate else 0.5
        fig.update_yaxes(range=[min_rate - pad_rate, max_rate + pad_rate], secondary_y=True, showgrid=False, tickfont=dict(color='#fef08a'), zeroline=False)
    else:
        fig = plotly_go.Figure()
        fig.add_trace(plotly_go.Scatter(x=sub_df.index, y=sub_df, mode='lines', line=dict(color=status_color, width=2.5), fill='tozeroy', fillcolor=hex_to_rgba(status_color, 0.15)))
        min_val, max_val = sub_df.min(), sub_df.max()
        padding = (max_val - min_val) * 0.15
        if padding == 0: padding = abs(min_val) * 0.05 if min_val != 0 else 1
        fig.update_yaxes(range=[min_val - padding, max_val + padding], showgrid=True, gridcolor='rgba(255,255,255,0.05)', side='right', zeroline=False, tickfont=dict(color='#fef08a'))

    fig.update_xaxes(tickformat="%y.%m.%d", showgrid=True, gridcolor='rgba(255,255,255,0.05)', zeroline=False, tickfont=dict(color='#fef08a'))
    if key == 'VIX': fig.add_hline(y=30, line_dash="dash", line_color="rgba(248,113,113,0.6)", opacity=0.8)
    elif key == 'MOVE': fig.add_hline(y=140, line_dash="dash", line_color="rgba(248,113,113,0.6)", opacity=0.8)
    elif key in ['SOFR_IORB_Spread', 'SOFR_EFFR_Spread']: fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.4)", opacity=0.8)

    fig.update_layout(
        template="plotly_dark", height=440,
        margin=dict(l=10, r=10, t=30 if is_10y2y else 10, b=10),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified', showlegend=is_10y2y,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(color='#fef08a')) if is_10y2y else None
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False}, key=f"chart_{key}")

    level_cards_html = ""
    for lvl in meta['levels']:
        level_cards_html += f'<div style="flex: 1; min-width: 200px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-left: 4px solid {lvl[2]}; border-radius: 8px; padding: 14px;"><div style="display: flex; align-items: center; gap: 6px; margin-bottom: 6px;"><span style="font-size: 16px;">{lvl[3]}</span><span style="font-weight: 800; font-size: 12px; color: #f8fafc;">{lvl[0]} <span style="color:{lvl[2]}; opacity:0.9;">· {lvl[1]}</span></span></div><div style="font-size: 11.5px; color: #fef08a; opacity: 0.9; line-height: 1.5;">{lvl[4]}</div></div>'

    unified_card_html = f'<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.1); border-radius: 14px; padding: 20px; margin-top: 8px; margin-bottom: 40px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);"><div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 20px; margin-bottom: 20px; gap: 16px;"><div style="flex: 1; min-width: 260px;"><div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;"><span style="background: {status_color}20; color: {status_color}; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 800; border: 1px solid {status_color}40;">{status_label}</span><span style="font-size: 11.5px; color: #fef08a; opacity: 0.9; font-weight: 600;">최근 {selected_period_label} 기준</span></div><div style="font-size: 1.8rem; font-weight: 800; line-height: 1.1; margin-bottom: 6px; letter-spacing: -0.5px; color: #f8fafc;">{format_val(cur, meta["unit"], is_sofr)}</div><div style="font-size: 0.95rem; color: #fef08a; opacity: 0.9; font-weight: 600;"><b style="color: {ACCENT_GOLD};">{meta["short_name"]}</b> — {status_text}</div></div><div style="display: flex; gap: 24px; background: rgba(255,255,255,0.02); padding: 14px 20px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);"><div><div style="font-size: 11px; color: #fef08a; opacity: 0.9; font-weight: 600; margin-bottom: 4px;">1주 전 대비</div><div style="font-size: 1rem;">{chg_1w_html}</div></div><div style="width: 1px; background: rgba(255,255,255,0.1);"></div><div><div style="font-size: 11px; color: #fef08a; opacity: 0.9; font-weight: 600; margin-bottom: 4px;">3개월 전 대비</div><div style="font-size: 1rem;">{chg_3m_html}</div></div></div></div>{extra_info_html}<div><div style="font-size: 0.95rem; font-weight: 800; margin-bottom: 8px; color: {ACCENT_GOLD};"><span style="margin-right: 6px;">📌</span>{meta["short_name"]}란?</div><div style="font-size: 0.85rem; color: #fef08a; opacity: 0.9; margin-bottom: 16px; line-height: 1.6;">{meta["desc"]}</div><div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 10px;">{level_cards_html}</div></div></div>'
    st.markdown(unified_card_html, unsafe_allow_html=True)


# ============================================================
# 대시보드 렌더링
# ============================================================

# --- 세계 외환 지표 ---
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-bottom: 15px; margin-top: 30px;'><span style='margin-right: 8px;'>💱</span> 세계 외환 지표</div>", unsafe_allow_html=True)

if all(col in df.columns for col in ['EURUSD', 'USDJPY', 'USDCNY', 'GBPUSD']):
    eur_cur  = df['EURUSD'].dropna().iloc[-1];  eur_prev  = df['EURUSD'].dropna().iloc[-2]
    jpy_cur  = df['USDJPY'].dropna().iloc[-1];  jpy_prev  = df['USDJPY'].dropna().iloc[-2]
    cny_cur  = df['USDCNY'].dropna().iloc[-1];  cny_prev  = df['USDCNY'].dropna().iloc[-2]
    gbp_cur  = df['GBPUSD'].dropna().iloc[-1];  gbp_prev  = df['GBPUSD'].dropna().iloc[-2]

    def pct_str(cur, prev): 
        c = (cur/prev-1)*100
        return (f"▲ {c:.2f}%", COLOR_SAFE) if c >= 0 else (f"▼ {abs(c):.2f}%", COLOR_DANGER)

    eur_s, eur_c = pct_str(eur_cur, eur_prev)
    jpy_s, jpy_c = pct_str(jpy_cur, jpy_prev)
    cny_s, cny_c = pct_str(cny_cur, cny_prev)
    gbp_s, gbp_c = pct_str(gbp_cur, gbp_prev)

    st.markdown(f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 2rem;">
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(212,175,55,0.15); border-radius: 12px; padding: 20px;"><div style="color: #D4AF37; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">유로/달러 (EUR/USD)</div><div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{eur_cur:.4f}</div><div style="color: {eur_c}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">{eur_s} 전일</div><div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div><div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">1 유로당 달러</div></div>
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(212,175,55,0.15); border-radius: 12px; padding: 20px;"><div style="color: #D4AF37; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">달러/엔 (USD/JPY)</div><div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{jpy_cur:.2f}</div><div style="color: {jpy_c}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">{jpy_s} 전일</div><div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div><div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">1 달러당 엔화</div></div>
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(212,175,55,0.15); border-radius: 12px; padding: 20px;"><div style="color: #D4AF37; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">달러/위안 (USD/CNY)</div><div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{cny_cur:.4f}</div><div style="color: {cny_c}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">{cny_s} 전일</div><div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div><div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">1 달러당 위안화</div></div>
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(212,175,55,0.15); border-radius: 12px; padding: 20px;"><div style="color: #D4AF37; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">파운드/달러 (GBP/USD)</div><div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{gbp_cur:.4f}</div><div style="color: {gbp_c}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">{gbp_s} 전일</div><div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div><div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">1 파운드당 달러</div></div>
    </div>""", unsafe_allow_html=True)
else:
    st.info("💡 외환 데이터를 불러오는 중입니다. 잠시 후 새로고침하세요.")

# --- 한국 경제 지표 ---
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-bottom: 15px; margin-top: 10px;'><span style='margin-right: 8px;'>🇰🇷</span> 한국 경제 지표</div>", unsafe_allow_html=True)

if all(col in df.columns for col in ['KOSPI', 'KOSDAQ', 'USDKRW']):
    kospi_cur  = df['KOSPI'].dropna().iloc[-1];  kospi_ath  = df['KOSPI'].max()
    kosdaq_cur = df['KOSDAQ'].dropna().iloc[-1]; kosdaq_ath = df['KOSDAQ'].max()
    usdkrw_cur = df['USDKRW'].dropna().iloc[-1]; usdkrw_prev = df['USDKRW'].dropna().iloc[-2]

    kospi_dd  = (kospi_cur / kospi_ath - 1) * 100
    kosdaq_dd = (kosdaq_cur / kosdaq_ath - 1) * 100
    usdkrw_diff = usdkrw_cur - usdkrw_prev

    st.markdown(f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 3rem;">
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(16,185,129,0.15); border-radius: 12px; padding: 20px;"><div style="color: {ACCENT_KOREA}; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">코스피</div><div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{f'+{kospi_dd:.1f}%' if kospi_dd > 0 else f'{kospi_dd:.1f}%'}</div><div style="color: {COLOR_DANGER if kospi_dd < -5 else COLOR_WARN if kospi_dd < 0 else COLOR_SAFE}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">ATH 대비 낙폭</div><div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div><div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">현재가: {kospi_cur:,.2f}</div></div>
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(16,185,129,0.15); border-radius: 12px; padding: 20px;"><div style="color: {ACCENT_KOREA}; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">코스닥</div><div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{f'+{kosdaq_dd:.1f}%' if kosdaq_dd > 0 else f'{kosdaq_dd:.1f}%'}</div><div style="color: {COLOR_DANGER if kosdaq_dd < -5 else COLOR_WARN if kosdaq_dd < 0 else COLOR_SAFE}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">ATH 대비 낙폭</div><div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div><div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">현재가: {kosdaq_cur:,.2f}</div></div>
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(16,185,129,0.15); border-radius: 12px; padding: 20px;"><div style="color: {ACCENT_KOREA}; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">원달러 환율</div><div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{usdkrw_cur:,.0f}원</div><div style="color: {COLOR_DANGER if usdkrw_diff >= 0 else COLOR_SAFE}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">{'▲' if usdkrw_diff >= 0 else '▼'} {abs(usdkrw_diff):.0f}원 전일</div><div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div><div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">KRW/USD</div></div>
    </div>""", unsafe_allow_html=True)
else:
    st.info("💡 한국 지표 데이터를 불러오는 중입니다.")



# --- 미국 증시 및 선물 섹션 ---
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-bottom: 15px; margin-top: 10px;'><span style='margin-right: 8px;'>🇺🇸</span> 미국 지수 및 선물</div>".replace('\n', ''), unsafe_allow_html=True)

if all(col in df.columns for col in ['SP500', 'NASDAQ', 'ES_F', 'NQ_F']):
    sp500_cur = df['SP500'].iloc[-1]
    sp500_ath = df['SP500'].max()
    sp500_dd = (sp500_cur / sp500_ath - 1) * 100
    sp500_dd_str = f"+{sp500_dd:.1f}%" if sp500_dd > 0 else f"{sp500_dd:.1f}%"
    sp500_color = COLOR_DANGER if sp500_dd < -5 else COLOR_WARN if sp500_dd < 0 else COLOR_SAFE

    nasdaq_cur = df['NASDAQ'].iloc[-1]
    nasdaq_ath = df['NASDAQ'].max()
    nasdaq_dd = (nasdaq_cur / nasdaq_ath - 1) * 100
    nasdaq_dd_str = f"+{nasdaq_dd:.1f}%" if nasdaq_dd > 0 else f"{nasdaq_dd:.1f}%"
    nasdaq_color = COLOR_DANGER if nasdaq_dd < -5 else COLOR_WARN if nasdaq_dd < 0 else COLOR_SAFE

    es_cur = df['ES_F'].iloc[-1]
    es_prev = df['ES_F'].iloc[-2]
    es_chg = (es_cur / es_prev - 1) * 100
    es_chg_str = f"▲ {es_chg:.2f}%" if es_chg >= 0 else f"▼ {abs(es_chg):.2f}%"
    es_color = COLOR_SAFE if es_chg >= 0 else COLOR_DANGER

    nq_cur = df['NQ_F'].iloc[-1]
    nq_prev = df['NQ_F'].iloc[-2]
    nq_chg = (nq_cur / nq_prev - 1) * 100
    nq_chg_str = f"▲ {nq_chg:.2f}%" if nq_chg >= 0 else f"▼ {abs(nq_chg):.2f}%"
    nq_color = COLOR_SAFE if nq_chg >= 0 else COLOR_DANGER

    us_assets_html = f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 3rem;">
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(59,130,246,0.15); border-radius: 12px; padding: 20px;">
            <div style="color: {ACCENT_US}; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">S&P 500</div>
            <div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{sp500_dd_str}</div>
            <div style="color: {sp500_color}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">ATH 대비 낙폭</div>
            <div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div>
            <div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">현재가: {sp500_cur:,.2f}</div>
        </div>
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(59,130,246,0.15); border-radius: 12px; padding: 20px;">
            <div style="color: {ACCENT_US}; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">나스닥 종합</div>
            <div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{nasdaq_dd_str}</div>
            <div style="color: {nasdaq_color}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">ATH 대비 낙폭</div>
            <div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div>
            <div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">현재가: {nasdaq_cur:,.2f}</div>
        </div>
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(59,130,246,0.15); border-radius: 12px; padding: 20px;">
            <div style="color: {ACCENT_US}; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">S&P 500 선물</div>
            <div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{es_cur:,.2f}</div>
            <div style="color: {es_color}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">{es_chg_str} 전일 대비</div>
            <div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div>
            <div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">ES=F · 실시간 야간 지표</div>
        </div>
        <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(59,130,246,0.15); border-radius: 12px; padding: 20px;">
            <div style="color: {ACCENT_US}; font-size: 0.95rem; font-weight: 700; margin-bottom: 8px;">나스닥 100 선물</div>
            <div style="color: #ffffff; font-size: 2.2rem; font-weight: 900; line-height: 1.2;">{nq_cur:,.2f}</div>
            <div style="color: {nq_color}; font-size: 0.95rem; font-weight: 700; margin-top: 5px;">{nq_chg_str} 전일 대비</div>
            <div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 15px 0 10px 0;"></div>
            <div style="color: #fef08a; opacity: 0.8; font-size: 0.8rem;">NQ=F · 실시간 야간 지표</div>
        </div>
    </div>
    """.replace('\n', '')
    st.markdown(us_assets_html, unsafe_allow_html=True)


# --- 핵심 매크로 및 유동성 요약 보드 (클릭 앵커 추가 & 3가지 카테고리로 재구성) ---
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-bottom: 15px; margin-top: 10px;'><span style='margin-right: 8px;'>📋</span> 핵심 지표 요약 보드</div>".replace('\n', ''), unsafe_allow_html=True)

# 앵커 연결을 위해 요청하신 세부 지표들과 1:1 완벽 맵핑
req_cols = ['VIX', 'MOVE', '10Y_2Y', 'HY_Spread', 'FSI', 'Fed_BS', 'Reserves', 'TGA', 'RRP', 'MMF', 'TOTLL', 'SOFR_IORB_Spread', 'SOFR_EFFR_Spread', 'Emergency_Loans']

if all(c in df_raw.columns for c in req_cols):
    
    # [1] 시장 리스크 및 스트레스 지표 그룹 데이터 추출
    v_vix = get_last_two(df_raw['VIX'])
    v_move = get_last_two(df_raw['MOVE'])
    v_10y2y = get_last_two(df_raw['10Y_2Y'])
    v_hy = get_last_two(df_raw['HY_Spread'])
    v_fsi = get_last_two(df_raw['FSI'])
    
    # 공포탐욕지수 (CNN 실제 데이터 호출, 실패시 SP500+VIX+HY 역산 초정밀 추정치로 Fallback)
    real_fng = fetch_cnn_fng()
    if real_fng is not None:
        fng_score = real_fng
        fng_desc = "CNN Fear & Greed"
    else:
        if 'SP500' in df_raw.columns and len(df_raw['SP500'].dropna()) > 125:
            sp500_close = df_raw['SP500'].dropna().iloc[-1]
            sp500_125ma = df_raw['SP500'].dropna().tail(125).mean()
            mom_score = (sp500_close / sp500_125ma - 1) * 100
            mom_norm = np.clip(50 + mom_score * 12, 0, 100)
        else:
            mom_norm = 50
        vix_norm = np.clip(100 - (v_vix[-1] - 12) * 5, 0, 100)
        hy_norm = np.clip(100 - (v_hy[-1] - 3.0) * 15, 0, 100)
        
        fng_score = int(round(mom_norm * 0.5 + vix_norm * 0.3 + hy_norm * 0.2))
        fng_desc = "CNN Fear & Greed (Proxy)"
        
    if fng_score <= 24: fng_state, fng_col = "극단적 공포 · extreme fear", COLOR_DANGER
    elif fng_score <= 44: fng_state, fng_col = "공포 · fear", COLOR_WARN
    elif fng_score <= 55: fng_state, fng_col = "중립 · neutral", COLOR_NEUTRAL
    elif fng_score <= 74: fng_state, fng_col = "탐욕 · greed", COLOR_SAFE
    else: fng_state, fng_col = "극단적 탐욕 · extreme greed", COLOR_SAFE
    
    fng_diff_data = (fng_state, fng_col)
    
    v_dxy = get_last_two(df_raw['DXY'])
    v_10y = get_last_two(df_raw['10Y'])
    v_wti = get_last_two(df_raw['WTI'])
    
    # [2] 유동성을 좌우하는 핵심 창구 그룹 데이터 추출
    v_fed = get_last_two(df_raw['Fed_BS'], 1/10000) # Trillion 단위 변환
    v_res = get_last_two(df_raw['Reserves'], 1/10000)
    v_tga = get_last_two(df_raw['TGA'], 1/10)       # Billion 단위 변환
    
    # [3] 은행 신용 및 단기 자금 시장 그룹 데이터 추출
    v_rrp = get_last_two(df_raw['RRP'], 1/10)       # Billion 단위 변환
    v_mmf = get_last_two(df_raw['MMF'], 1/10000)    # Trillion 단위 변환
    v_totll = get_last_two(df_raw['TOTLL'], 1/10000)# Trillion 단위 변환
    v_sofr_iorb = get_last_two(df_raw['SOFR_IORB_Spread'])
    v_sofr_effr = get_last_two(df_raw['SOFR_EFFR_Spread'])
    v_emerg = get_last_two(df_raw['Emergency_Loans'], 1/10) # Billion 단위 변환

    board_html = f"""
    <div style="margin-bottom: 3rem; background: rgba(255,255,255,0.01); padding: 24px; border-radius: 16px; border: 1px solid rgba(255,255,255,0.05);">
        
        <!-- Group 1: 시장 동향 및 매크로 (Merged & 2-Row Split) -->
        <div style="margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                <div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(249,115,22,0.15); display: flex; justify-content: center; align-items: center; font-size: 1.1rem;">📈</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #e2e8f0; letter-spacing: -0.5px;">시장 동향 및 매크로</div>
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 16px;">
                {render_mini_card("공포탐욕지수", f"{fng_score}", fng_diff_data, fng_desc, "#f97316", "", is_highlight=True)}
                {render_mini_card("VIX 변동성 지수", f"{v_vix[-1]:.2f}", make_diff_str(v_vix[-1], v_vix[-2], invert=True), "20↓ 안정 · 30↑ 경계", "#f97316", "VIX")}
                {render_mini_card("장단기 금리차", f"{v_10y2y[-1]:.2f}%", make_diff_str(v_10y2y[-1], v_10y2y[-2], unit='%'), "10Y - 2Y · 음수 = 역전", "#f97316", "10Y_2Y")}
                {render_mini_card("하이일드 스프레드", f"{v_hy[-1]:.2f}%", make_diff_str(v_hy[-1], v_hy[-2], unit='%', invert=True), "신용시장 스트레스", "#f97316", "HY_Spread")}
            </div>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                {render_mini_card("달러인덱스", f"{v_dxy[-1]:.2f}", make_diff_str(v_dxy[-1], v_dxy[-2], invert=True), "DXY · ICE 달러인덱스", "#a855f7", "DXY")}
                {render_mini_card("10년물 금리", f"{v_10y[-1]:.2f}%", make_diff_str(v_10y[-1], v_10y[-2], unit='%', invert=True), "미국 장기금리 기준", "#a855f7", "10Y_2Y")}
                {render_mini_card("WTI 원유", f"${v_wti[-1]:.1f}", make_diff_str(v_wti[-1], v_wti[-2], invert=True), "USD/배럴", "#a855f7", "")}
            </div>
        </div>

        <!-- Group 2: 유동성을 좌우하는 핵심 창구 -->
        <div style="margin-bottom: 2rem;">
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                <div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(59,130,246,0.15); display: flex; justify-content: center; align-items: center; font-size: 1.1rem;">🏦</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #e2e8f0; letter-spacing: -0.5px;">유동성을 좌우하는 핵심 창구</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px;">
                {render_mini_card("연준 총자산", f"{v_fed[-1]:.2f}T", make_diff_str(v_fed[-1], v_fed[-2], unit='T', period='전주 대비'), "클릭하여 상세 차트 보기", "#3b82f6", "Fed_BS")}
                {render_mini_card("지급준비금", f"{v_res[-1]:.2f}T", make_diff_str(v_res[-1], v_res[-2], unit='T', period='전주 대비'), "클릭하여 상세 차트 보기", "#3b82f6", "Reserves")}
                {render_mini_card("TGA 잔액", f"{v_tga[-1]:.1f}B", make_diff_str(v_tga[-1], v_tga[-2], unit='B', invert=True, period='전주 대비'), "클릭하여 상세 차트 보기", "#3b82f6", "TGA")}
            </div>
        </div>

        <!-- Group 3: 은행 신용 및 단기 자금 시장 -->
        <div>
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                <div style="width: 34px; height: 34px; border-radius: 8px; background: rgba(16,185,129,0.15); display: flex; justify-content: center; align-items: center; font-size: 1.1rem;">💰</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #e2e8f0; letter-spacing: -0.5px;">은행 신용 및 단기 자금 시장</div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                {render_mini_card("역레포(RRP) 잔액", f"{v_rrp[-1]:.2f}B", make_diff_str(v_rrp[-1], v_rrp[-2], unit='B', invert=True), "클릭하여 상세 차트 보기", "#10b981", "RRP")}
                {render_mini_card("MMF 잔액", f"{v_mmf[-1]:.2f}T", make_diff_str(v_mmf[-1], v_mmf[-2], unit='T', period='전주 대비'), "클릭하여 상세 차트 보기", "#10b981", "MMF")}
                {render_mini_card("상업은행 총대출", f"{v_totll[-1]:.2f}T", make_diff_str(v_totll[-1], v_totll[-2], unit='T', period='전주 대비'), "클릭하여 상세 차트 보기", "#10b981", "TOTLL")}
                {render_mini_card("조달 스프레드 (SOFR-IORB)", f"{v_sofr_iorb[-1]:.3f}%", make_diff_str(v_sofr_iorb[-1], v_sofr_iorb[-2], unit='%', invert=True), "클릭하여 상세 차트 보기", "#10b981", "SOFR_IORB_Spread")}
                {render_mini_card("SOFR / EFFR 스프레드", f"{v_sofr_effr[-1]:.3f}%", make_diff_str(v_sofr_effr[-1], v_sofr_effr[-2], unit='%', invert=True), "클릭하여 상세 차트 보기", "#10b981", "SOFR_EFFR_Spread")}
                {render_mini_card("긴급대출 잔액", f"${v_emerg[-1]:.1f}B", make_diff_str(v_emerg[-1], v_emerg[-2], unit='B', invert=True, period='전주 대비'), "클릭하여 상세 차트 보기", "#10b981", "Emergency_Loans")}
            </div>
        </div>
    </div>
    """.replace('\n', '')
    st.markdown(board_html, unsafe_allow_html=True)


custom_header("🌊", "미국 핵심 유동성 흐름", "Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")

if 'Net_Liquidity' in df.columns and 'SP500' in df.columns:
    fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['Net_Liquidity'].tail(selected_days), name="순유동성 (억 달러)", line=dict(color='#60a5fa', width=2.5)), secondary_y=False)
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['SP500'].tail(selected_days), name="S&P 500", line=dict(color='#f87171', width=1.5)), secondary_y=True)
    
    fig_liq.update_layout(
        title_text=f"Net Liquidity vs S&P 500 ({selected_period_label})", 
        title_font=dict(color='#fef08a'),
        height=600, hovermode="x unified", margin=dict(t=50, b=0, l=10, r=10),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickformat="%y.%m.%d", tickfont=dict(color='#fef08a')),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickfont=dict(color='#fef08a')),
        yaxis2=dict(showgrid=False, tickfont=dict(color='#fef08a')),
        legend=dict(font=dict(color='#fef08a'))
    )
    fig_liq.update_yaxes(title_text="Net Liquidity (억 달러)", secondary_y=False, title_font=dict(color='#fef08a'))
    fig_liq.update_yaxes(title_text="S&P 500 Index", secondary_y=True, title_font=dict(color='#fef08a'))
    st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False}, key="net_liq_chart")
    
    st.markdown("""<div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(212,175,55,0.3); border-radius: 14px; padding: 20px; margin-top: 15px; margin-bottom: 50px; box-shadow: 0 4px 20px rgba(0,0,0,0.3);">
<div style="font-size: 0.95rem; font-weight: 800; margin-bottom: 10px; color:#D4AF37;">📌 Net Liquidity(순유동성) 공식: 연준 대차대조표 - 역레포(RRP) - 재무부 계좌(TGA)</div>
<div style="font-size: 0.85rem; color: #fef08a; opacity: 0.9; line-height: 1.6;">
중앙은행이 시장에 실질적으로 공급한 순수 유동성 자금의 양입니다.<br>
통상적으로 <b style="color:#60a5fa">파란선(순유동성)</b>이 오르면 시중에 돈이 넘쳐나 <b style="color:#f87171">빨간선(S&P 500)</b>도 함께 오르고, 내리면 주가도 조정을 받는 <b>강한 양(+)의 상관관계</b>를 가집니다.
</div>
</div>""".replace('\n', ''), unsafe_allow_html=True)

# --- 미국 10년물 국채금리 분해 (Decomposition) ---
st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
custom_header("🇺🇸", "미국 10년물 국채금리 분해 (Decomposition)", "국채금리를 '단기금리 기대경로', '기대인플레이션', '기간 프리미엄'으로 분해하여 시장의 진짜 의도를 파악합니다.")

if all(col in df.columns for col in ['10Y', 'T10YIE', 'ACMTP10']):
    short_rate = df['10Y'] - df['T10YIE'] - df['ACMTP10']

    fig_decomp = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig_decomp.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['10Y'].tail(selected_days), name="US 10 Year (좌)", line=dict(color='#3b82f6', width=2.5)), secondary_y=False)
    fig_decomp.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=short_rate.tail(selected_days), name="Short Rate (좌)", line=dict(color='#7dd3fc', width=2)), secondary_y=False)
    fig_decomp.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['T10YIE'].tail(selected_days), name="10 Year EI Rate (좌)", line=dict(color='#94a3b8', width=2)), secondary_y=False)
    
    fig_decomp.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['ACMTP10'].tail(selected_days), name="10 Year TP (우)", line=dict(color='#f97316', width=2)), secondary_y=True)

    fig_decomp.update_layout(
        height=600, hovermode="x unified", margin=dict(t=30, b=0, l=10, r=10),
        template="plotly_dark", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, font=dict(color='#fef08a'))
    )
    fig_decomp.update_yaxes(title_text="금리 (%)", secondary_y=False, showgrid=True, gridcolor='rgba(255,255,255,0.05)', title_font=dict(color='#fef08a'), tickfont=dict(color='#fef08a'))
    fig_decomp.update_yaxes(title_text="기간 프리미엄 (%p)", secondary_y=True, showgrid=False, title_font=dict(color='#fef08a'), tickfont=dict(color='#fef08a'))
    fig_decomp.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.05)', tickformat="%y.%m.%d", tickfont=dict(color='#fef08a'))
    
    st.plotly_chart(fig_decomp, use_container_width=True, config={'displayModeBar': False})
else:
    st.info("💡 현재 연준(FRED) 서버에서 '기간 프리미엄(ACMTP10)' 등의 데이터를 일시적으로 제공하지 않아 차트를 생략합니다. (API 연동 지연)")


st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
custom_header("🚨", "1. 시장 리스크 및 스트레스 지표", "시장의 공포 심리와 시스템 위기 가능성을 경고합니다.")
render_detailed_indicator('VIX', df, selected_days)
render_detailed_indicator('MOVE', df, selected_days)
render_detailed_indicator('10Y_2Y', df, selected_days)
render_detailed_indicator('HY_Spread', df, selected_days)
render_detailed_indicator('FSI', df, selected_days)

st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
custom_header("🏦", "2. 유동성을 좌우하는 핵심 창구", "연준과 재무부의 실질적인 달러 공급/흡수 현황입니다.")
render_detailed_indicator('Fed_BS', df, selected_days)
render_detailed_indicator('WRESBAL_Ind', df, selected_days)
render_detailed_indicator('Reserves', df, selected_days)
render_detailed_indicator('TGA', df, selected_days)

st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
custom_header("💰", "3. 은행 신용 및 단기 자금 시장", "실물 경제로의 자금 조달 여건과 기관 자금의 대피 흐름입니다.")
render_detailed_indicator('RRP', df, selected_days)
render_detailed_indicator('MMF', df, selected_days)
render_detailed_indicator('TOTLL', df, selected_days)
render_detailed_indicator('SOFR_IORB_Spread', df, selected_days)
render_detailed_indicator('SOFR_EFFR_Spread', df, selected_days)
render_detailed_indicator('Emergency_Loans', df, selected_days)

st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
custom_header("🌍", "4. 인플레이션 및 글로벌 매크로", "글로벌 달러 유동성 환경과 향후 금리 인하 기대감을 측정합니다.")
render_detailed_indicator('DXY', df, selected_days)
render_detailed_indicator('T10YIE', df, selected_days)

st.markdown("<hr>".replace('\n', ''), unsafe_allow_html=True)
custom_header("📝", "AI 매크로 종합 시황 진단", "모든 데이터를 종합하여 현재의 거시 경제 국면을 판독합니다.")

def generate_report_html(df, days):
    sub_df = df.tail(days)
    if len(sub_df) < 2: return "데이터가 충분하지 않습니다."
    
    latest, start = sub_df.iloc[-1], sub_df.iloc[0]
    def safe(row, col): return row[col] if col in row.index else 0.0
    
    vix, move = safe(latest, 'VIX'), safe(latest, 'MOVE')
    yield_curve, hy_spread = safe(latest, '10Y_2Y'), safe(latest, 'HY_Spread')
    liq_change = safe(latest, 'Net_Liquidity') - safe(start, 'Net_Liquidity')
    sofr_spread = safe(latest, 'SOFR_IORB_Spread')
    totll_chg = safe(latest, 'TOTLL') - safe(start, 'TOTLL')
    dxy, bei, emerg_loans = safe(latest, 'DXY'), safe(latest, 'T10YIE'), safe(latest, 'Emergency_Loans')
    
    if vix > 30: vix_msg = f"<b style='color:{COLOR_DANGER};'>위험 심리:</b> VIX가 {vix:.2f}로 시장에 공포 심리가 팽배합니다."
    else: vix_msg = f"<b style='color:{COLOR_SAFE};'>위험 심리:</b> VIX가 {vix:.2f}로 시장이 안정적인 흐름을 유지 중입니다."
    if emerg_loans > 500 or move > 140: sys_msg = f"<b style='color:{COLOR_DANGER};'>시스템 경고:</b> 연준 긴급 대출이나 채권 변동성이 높아 스트레스 징후가 관찰됩니다."
    else: sys_msg = f"<b style='color:{COLOR_SAFE};'>시스템 안정:</b> 긴급 대출 잔액({emerg_loans:,.0f}억 달러)이 낮아 시스템 위기 징후는 없습니다."
    
    if sofr_spread > 0.05: sofr_msg = f"<b style='color:{COLOR_DANGER};'>조달 스트레스:</b> SOFR-IORB 스프레드({sofr_spread:.3f}%)가 확대되어 단기 달러 경색 조짐이 보입니다."
    else: sofr_msg = f"<b style='color:{COLOR_SAFE};'>조달 안정:</b> SOFR-IORB 스프레드가 {sofr_spread:.3f}%로 단기 레포 시장 융통이 원활합니다."
    if totll_chg < 0: totll_msg = f"<b style='color:{COLOR_DANGER};'>신용 축소:</b> 상업은행 대출이 감소({abs(totll_chg):,.0f}억 달러)하여 신용 공급 둔화 우려가 있습니다."
    elif totll_chg > 0: totll_msg = f"<b style='color:{COLOR_SAFE};'>신용 팽창:</b> 상업은행 대출이 증가({totll_chg:,.0f}억 달러)하며 신용 창출이 이어지고 있습니다."
    else: totll_msg = f"<b style='color:{COLOR_WARN};'>신용 정체:</b> 상업은행 대출 규모가 관망세를 보이고 있습니다."

    if yield_curve < 0: yield_msg = f"<b style='color:{COLOR_DANGER};'>침체 선행:</b> 장단기 금리차({yield_curve:.2f}%) 역전으로 경기 둔화 가능성이 암시됩니다."
    else: yield_msg = f"<b style='color:{COLOR_SAFE};'>성장 기대:</b> 장단기 금리차({yield_curve:.2f}%)가 우상향 곡선을 회복했습니다."
    if bei > 2.5: bei_msg = f"<b style='color:{COLOR_DANGER};'>물가 불안:</b> 기대인플레({bei:.2f}%)가 높아 연준의 금리 인하 스탠스를 제약할 수 있습니다."
    else: bei_msg = f"<b style='color:{COLOR_SAFE};'>물가 안정:</b> 기대인플레({bei:.2f}%)가 연준의 장기 목표 궤적에 부합합니다."

    if (yield_curve < 0 and hy_spread > 5.0) or sofr_spread > 0.1:
        strategy = f"침체 시그널과 펀딩 스트레스가 중첩되었습니다. <b>현금 및 채권 방어적 포트폴리오 비중 확대</b>를 강력히 권장합니다."
        s_color = COLOR_DANGER
    elif liq_change > 0 and dxy < 105 and sofr_spread <= 0:
        strategy = f"순유동성이 증가(+{liq_change:,.0f}억 달러)하고 달러 가치가 안정적입니다. <b>위험 자산(주식)의 비중 유지 및 랠리 동참</b>이 유리한 환경입니다."
        s_color = COLOR_SAFE
    else:
        strategy = f"거시 지표 방향성이 혼재되어 있습니다. <b>관망세 유지 및 대출 의존도가 낮은 우량(Quality) 기업 위주의 선별적 접근</b>이 필요합니다."
        s_color = COLOR_WARN

    html_report = f"""
    <div style="background: linear-gradient(145deg, rgba(212,175,55,0.06) 0%, rgba(212,175,55,0.02) 100%); border: 1px solid rgba(212,175,55,0.3); border-radius: 16px; padding: 26px; margin-bottom: 24px; box-shadow: 0 8px 32px rgba(0,0,0,0.3);">
        <div style="font-size: 1.05rem; font-weight: 800; color: #D4AF37; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 1.2rem;">💡</span> 핵심 자산 배분 전략
        </div>
        <div style="font-size: 1rem; font-weight: 500; line-height: 1.6; margin-bottom: 24px; color: {s_color}; background: rgba(0,0,0,0.2); padding: 14px 18px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.05);">
            {strategy}
        </div>
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 18px;">
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="font-weight: 800; font-size: 0.95rem; margin-bottom: 12px; color: #D4AF37; border-bottom: 1px solid rgba(212,175,55,0.3); padding-bottom: 6px;">📌 시장 심리 및 유동성</div>
                <div style="line-height: 1.8; font-size: 0.85rem; color: #fef08a;">
                    <div>• {vix_msg}</div>
                    <div>• {sys_msg}</div>
                </div>
            </div>
            <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 18px; box-shadow: 0 4px 12px rgba(0,0,0,0.1);">
                <div style="font-weight: 800; font-size: 0.95rem; margin-bottom: 12px; color: #D4AF37; border-bottom: 1px solid rgba(212,175,55,0.3); padding-bottom: 6px;">📌 매크로 및 신용 환경</div>
                <div style="line-height: 1.8; font-size: 0.85rem; color: #fef08a;">
                    <div>• {sofr_msg}</div>
                    <div>• {totll_msg}</div>
                    <div>• {yield_msg}</div>
                    <div>• {bei_msg}</div>
                </div>
            </div>
        </div>
    </div>
    """.replace('\n', '')
    return html_report

st.markdown(generate_report_html(df, selected_days), unsafe_allow_html=True)
st.caption(f"마지막 데이터 갱신: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (기준일자: {df.index[-1].strftime('%Y-%m-%d')})")
st.markdown("</div>".replace('\n', ''), unsafe_allow_html=True)
