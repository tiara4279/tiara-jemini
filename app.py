import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
import datetime
import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots
import numpy as np

# --- 페이지 설정 ---
st.set_page_config(page_title="Global Macro & Liquidity Dashboard", layout="wide")

# --- 커스텀 CSS 및 메타 태그 ---
st.markdown("""
<meta name="google" content="notranslate">
<style>
/* 탭 및 전반적인 여백 조정 */
div[data-testid="stTabs"] {
    margin-top: 20px;
}
</style>
<div class="notranslate">
""", unsafe_allow_html=True)

st.title("🌐 시장 경제 지표 대시보드")
st.markdown("시장의 핵심 유동성 흐름과 매크로 지표를 심층적으로 추적합니다.")

# --- 기간 선택 컨트롤 ---
st.markdown("### ⏱️ 추이 기준 기간 선택")
period_options = {"1개월": 21, "3개월": 63, "6개월": 126, "1년": 252, "3년": 756}
selected_period_label = st.radio("기간", list(period_options.keys()), index=1, horizontal=True, label_visibility="collapsed")
selected_days = period_options[selected_period_label]
st.write("")

# --- 데이터 로드 함수 ---
@st.cache_data(ttl=3600*12) 
def load_data():
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365*3) 
    
    fred_series = {
        'VIX': 'VIXCLS', 'HY_Spread': 'BAMLH0A0HYM2', 'FSI': 'STLFSI4', '10Y_2Y': 'T10Y2Y',               
        'Fed_BS': 'WALCL', 'Reserves': 'WRESBAL', 'RRP': 'RRPONTSYD', 'TGA': 'WTREGEN',                 
        'MMF': 'MMMFFAQ027S', 'TOTLL': 'TOTLL', 'SOFR': 'SOFR', 'IORB': 'IORB',                   
        'T10YIE': 'T10YIE', 'Discount_Window': 'WLCFLPCL', 'BTFP': 'H41RESPALBFRB'           
    }
    
    df_fred = pd.DataFrame()
    for name, series_id in fred_series.items():
        try:
            data = web.DataReader(series_id, 'fred', start, end)
            df_fred[name] = data[series_id]
        except Exception as e:
            pass 

    # 단위 환산 (억 달러)
    if 'Fed_BS' in df_fred.columns: df_fred['Fed_BS'] = df_fred['Fed_BS'] / 100
    if 'Reserves' in df_fred.columns: df_fred['Reserves'] = df_fred['Reserves'] / 100
    if 'TGA' in df_fred.columns: df_fred['TGA'] = df_fred['TGA'] / 100
    if 'MMF' in df_fred.columns: df_fred['MMF'] = df_fred['MMF'] / 100
    if 'RRP' in df_fred.columns: df_fred['RRP'] = df_fred['RRP'] * 10
    if 'TOTLL' in df_fred.columns: df_fred['TOTLL'] = df_fred['TOTLL'] * 10 
    if 'Discount_Window' in df_fred.columns: df_fred['Discount_Window'] = df_fred['Discount_Window'] / 100
    if 'BTFP' in df_fred.columns: df_fred['BTFP'] = df_fred['BTFP'] / 100

    tickers = ['^GSPC', '^MOVE', 'DX-Y.NYB']
    df_yf = pd.DataFrame()
    try:
        yf_data = yf.download(tickers, start=start, end=end, progress=False)
        if 'Close' in yf_data.columns: df_yf = yf_data['Close']
        else: df_yf = yf_data
        df_yf = df_yf.rename(columns={'^GSPC': 'SP500', '^MOVE': 'MOVE', 'DX-Y.NYB': 'DXY'})
    except Exception as e:
        pass

    df_merged = pd.concat([df_fred, df_yf], axis=1).ffill().bfill().fillna(0)
    
    if all(col in df_merged.columns for col in ['Fed_BS', 'RRP', 'TGA']):
        df_merged['Net_Liquidity'] = df_merged['Fed_BS'] - df_merged['RRP'] - df_merged['TGA']
    else: df_merged['Net_Liquidity'] = 0
        
    if all(col in df_merged.columns for col in ['SOFR', 'IORB']):
        df_merged['SOFR_IORB_Spread'] = df_merged['SOFR'] - df_merged['IORB']
    else: df_merged['SOFR_IORB_Spread'] = 0.0
        
    if all(col in df_merged.columns for col in ['Discount_Window', 'BTFP']):
        df_merged['Emergency_Loans'] = df_merged['Discount_Window'] + df_merged['BTFP']
    else: df_merged['Emergency_Loans'] = 0.0
    
    return df_merged

with st.spinner('데이터를 수집하고 분석하는 중입니다...'):
    df = load_data()

if df.empty or len(df) < 6:
    st.error("🚨 데이터를 가져오는 데 실패했습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

# --- 지표별 메타데이터 및 분석 로직 설정 ---
COLOR_SAFE = "#09ab3b" # 초록
COLOR_WARN = "#f2a900" # 노랑
COLOR_DANGER = "#ff4b4b" # 빨강
COLOR_NEUTRAL = "#007bff" # 파랑/중립

def eval_vix(v, d):
    if v >= 30: return "경계", COLOR_DANGER, "투자자들이 겁먹은 상태입니다. 시장의 극심한 변동성에 대비하세요."
    elif v >= 20: return "주의", COLOR_WARN, "불확실성이 커지고 있습니다. 포지션을 점검할 때입니다."
    else: return "안정", COLOR_SAFE, "시장이 조용하고 투자자들이 편안한 상태입니다."

def eval_move(v, d):
    if v >= 140: return "위험", COLOR_DANGER, "채권 시장이 패닉 상태입니다. 은행/금융 시스템 스트레스를 경계하세요."
    elif v >= 100: return "주의", COLOR_WARN, "채권 변동성이 높아지고 있습니다."
    else: return "안정", COLOR_SAFE, "채권 시장이 평온하게 움직이고 있습니다."

def eval_10y2y(v, d):
    if v < 0: return "침체 경고", COLOR_DANGER, "금리가 역전되었습니다! 과거 경기 침체 전 항상 나타났던 현상입니다."
    else: return "정상", COLOR_SAFE, "단기 금리가 장기 금리보다 낮은 정상적인 경제 성장 국면입니다."

def eval_fsi(v, d):
    if v > 0: return "스트레스", COLOR_DANGER, "금융 시스템 내에 자금 경색 등 스트레스 요인이 발생했습니다."
    else: return "안정", COLOR_SAFE, "금융 시스템이 원활하게 작동하고 있습니다."

def eval_hy(v, d):
    if v >= 5.0: return "경고", COLOR_DANGER, "정크본드 금리가 급등하며 신용 경색 조짐이 보입니다."
    elif v >= 4.0: return "주의", COLOR_WARN, "기업들의 자금 조달 여건이 빡빡해지고 있습니다."
    else: return "안정", COLOR_SAFE, "하이일드 채권 시장이 안정적이며 신용 위험이 낮습니다."

def eval_fed(v, d):
    if d > 0: return "팽창", COLOR_SAFE, "연준이 자산을 늘리며 시중에 유동성을 공급하고 있습니다."
    else: return "긴축(QT)", COLOR_DANGER, "연준이 자산을 축소하며 시중의 유동성을 흡수하고 있습니다."

def eval_reserves(v, d):
    if d > 0: return "확대", COLOR_SAFE, "은행들의 자금 여력이 늘어나 대출과 투자가 원활해집니다."
    else: return "축소", COLOR_DANGER, "은행들의 자금 여력이 줄어들어 신용 공급이 둔화될 수 있습니다."

def eval_rrp(v, d):
    if v == 0: return "고갈", COLOR_DANGER, "역레포 대기 자금이 완전히 소진되어 추가 유동성 완충재가 없습니다."
    elif v < 1000: return "바닥 근접", COLOR_WARN, "증시를 밀어올리던 잉여 자금이 거의 바닥을 드러내고 있습니다."
    elif d > 0: return "위험 회피", COLOR_DANGER, "시중 자금이 연준 금고(역레포)로 대피하고 있습니다."
    else: return "위험 선호", COLOR_SAFE, "역레포 자금이 방출되며 증시 등 실물로 흘러가고 있습니다."

def eval_tga(v, d):
    if d > 0: return "자금 흡수", COLOR_DANGER, "재무부가 국채 발행/세금으로 시중 자금을 블랙홀처럼 흡수 중입니다."
    else: return "재정 지출", COLOR_SAFE, "재무부가 예산을 집행하며 시중에 자금을 펌핑하고 있습니다."

def eval_mmf(v, d):
    if d > 0: return "자금 이탈", COLOR_WARN, "투자자들이 주식을 팔고 안전한 단기 현금성 자산(MMF)으로 피신 중입니다."
    else: return "위험 선호", COLOR_SAFE, "MMF 자금이 빠져나와 주식 등 위험 자산으로 이동 중입니다."

def eval_totll(v, d):
    if d > 0: return "신용 팽창", COLOR_SAFE, "상업은행 대출이 늘어나 실물 경제에 자금이 잘 돌고 있습니다."
    else: return "신용 축소", COLOR_DANGER, "상업은행이 대출 문턱을 높여 실물 경제 자금줄이 마르고 있습니다."

def eval_sofr(v, d):
    if v > 0.05: return "발작 조짐", COLOR_DANGER, "기준금리(IORB)보다 시장금리(SOFR)가 비쌉니다. 달러 구하기가 힘듭니다!"
    elif v > 0: return "타이트", COLOR_WARN, "단기 자금 시장의 달러 유동성이 빠듯해지고 있습니다."
    else: return "안정", COLOR_SAFE, "단기 레포 시장에서 달러 융통이 원활하게 이루어지고 있습니다."

def eval_emerg(v, d):
    if v > 500: return "위기", COLOR_DANGER, "은행들이 연준에서 긴급 자금을 대거 빌려가고 있습니다. 뱅크런 우려!"
    elif v > 0: return "주의", COLOR_WARN, "일부 은행이 연준의 긴급 차입(할인창구 등)을 이용했습니다."
    else: return "안정", COLOR_SAFE, "은행 시스템이 건강하여 연준의 긴급 대출을 쓰지 않고 있습니다."

def eval_dxy(v, d):
    if v >= 105: return "강세", COLOR_DANGER, "달러가 강해지며 신흥국 자본 이탈 및 글로벌 유동성 축소가 우려됩니다."
    elif v < 100: return "약세", COLOR_SAFE, "달러 약세로 글로벌 증시와 위험 자산에 우호적인 환경입니다."
    else: return "중립", COLOR_NEUTRAL, "달러가 박스권에서 안정적으로 유지되고 있습니다."

def eval_bei(v, d):
    if v >= 2.5: return "물가 불안", COLOR_DANGER, "인플레이션 고착화 우려로 연준의 금리 인하가 지연될 수 있습니다."
    elif v <= 2.0: return "디스인플레", COLOR_WARN, "경기 둔화 및 침체 우려가 부각되는 구간입니다."
    else: return "골디락스", COLOR_SAFE, "연준의 물가 목표치(2%) 근방에서 안정적으로 움직이고 있습니다."

INDICATOR_META = {
    'VIX': {'name': 'VIX 공포지수', 'unit': 'pt', 'desc': '시장이 앞으로 얼마나 출렁일지 예상하는 지수입니다. 투자자들의 불안감을 숫자로 표현합니다.', 'eval': eval_vix, 'levels': [("20 미만", "안정", COLOR_SAFE, "😌", "시장이 조용하고 투자자들이 편안한 상태"), ("20~30", "주의", COLOR_WARN, "🙄", "불확실성이 커지는 구간. 변동성 유의"), ("30 이상", "경계", COLOR_DANGER, "😱", "과거 주요 시장 충격 때 항상 넘었던 공포 구간")]},
    'MOVE': {'name': 'MOVE 채권 변동성 지수', 'unit': 'pt', 'desc': '미국 국채 시장의 변동성을 보여주는 채권판 VIX입니다. 주식보다 채권 발작이 시스템 위기를 더 잘 잡아냅니다.', 'eval': eval_move, 'levels': [("100 미만", "안정", COLOR_SAFE, "😌", "채권 시장 평온"), ("100~140", "주의", COLOR_WARN, "⚠️", "채권 금리 급등락. 유동성 주의"), ("140 이상", "위험", COLOR_DANGER, "🚨", "시스템 리스크 및 금융 위기 징후")]},
    '10Y_2Y': {'name': '장단기 금리차 (10Y-2Y)', 'unit': '%', 'desc': '미국 10년물 국채와 2년물 국채의 금리 차이입니다. 경제의 미래 전망을 가장 정확히 예측하는 선행지표입니다.', 'eval': eval_10y2y, 'levels': [("0% 이상", "정상", COLOR_SAFE, "📈", "장기 금리가 더 높은 건강한 경제 성장 구간"), ("0% 미만", "침체 경고", COLOR_DANGER, "📉", "금리 역전 현상. 역대 모든 경기침체 전 발생")]},
    'FSI': {'name': '금융 스트레스 지수 (FSI)', 'unit': 'pt', 'desc': '18개 금융 시장 지표를 종합하여 미국 금융 시스템의 전반적인 스트레스 수준을 측정합니다.', 'eval': eval_fsi, 'levels': [("0 미만", "안정", COLOR_SAFE, "✅", "금융 시스템 원활"), ("0 이상", "스트레스", COLOR_DANGER, "💥", "평균 이상의 시스템 긴장 상태")]},
    'HY_Spread': {'name': '하이일드 스프레드', 'unit': '%', 'desc': '안전한 국채와 위험한 정크본드(하이일드) 간의 금리 격차입니다. 신용 경색을 파악하는 핵심입니다.', 'eval': eval_hy, 'levels': [("4% 미만", "안정", COLOR_SAFE, "👍", "기업들 자금 조달 원활"), ("4~5%", "주의", COLOR_WARN, "🤔", "신용 경계감 상승"), ("5% 이상", "경고", COLOR_DANGER, "🔥", "자금줄이 마르고 기업 부도 위험 상승")]},
    
    'Fed_BS': {'name': '연준 대차대조표 총자산', 'unit': '억 달러', 'desc': '연준(Fed)이 찍어내어 보유하고 있는 자산의 총합입니다. 시중에 풀린 본원 통화의 양을 의미합니다.', 'eval': eval_fed, 'levels': [("상승 (QE)", "팽창", COLOR_SAFE, "💸", "시중에 자금을 쏟아내어 증시 상승 압력"), ("하락 (QT)", "긴축", COLOR_DANGER, "🧽", "시중의 달러를 흡수하여 자산 가격 조정 압력")]},
    'Reserves': {'name': '지급준비금 (Reserves)', 'unit': '억 달러', 'desc': '상업은행들이 연준에 맡겨둔 대기 자금입니다. 은행이 실물 경제에 신용을 공급할 수 있는 체력입니다.', 'eval': eval_reserves, 'levels': [("상승", "확대", COLOR_SAFE, "🏦", "은행 대출 및 자산 매입 여력 증가"), ("하락", "축소", COLOR_DANGER, "🏜️", "유동성이 줄어들며 시장 변동성 확대 대비")]},
    'RRP': {'name': '역레포 잔액 (RRP)', 'unit': '억 달러', 'desc': '시중의 남아도는 단기 잉여 자금이 연준 창고로 들어간 금액입니다. 증시를 방어하는 유동성 완충재 역할을 합니다.', 'eval': eval_rrp, 'levels': [("방출 (감소)", "위험 선호", COLOR_SAFE, "🌊", "연준 창고에서 돈이 나와 실물/증시로 유입"), ("흡수 (증가)", "위험 회피", COLOR_DANGER, "🔒", "시장 불안으로 단기 자금이 연준으로 피신"), ("0 근접", "고갈", COLOR_WARN, "🪫", "충격을 흡수할 대기 자금 바닥 임박")]},
    'TGA': {'name': '재무부 계좌 (TGA)', 'unit': '억 달러', 'desc': '미국 정부의 마이너스 통장입니다. 세금을 걷거나 국채를 발행하면 여기에 돈이 쌓입니다.', 'eval': eval_tga, 'levels': [("잔액 감소", "재정 지출", COLOR_SAFE, "🚀", "정부가 예산을 집행하여 시중에 돈을 뿌림"), ("잔액 증가", "자금 흡수", COLOR_DANGER, "🕳️", "세금/국채로 시중 유동성을 빨아들여 단기 악재")]},
    
    'TOTLL': {'name': 'H.8 상업은행 총대출', 'unit': '억 달러', 'desc': '미국 상업은행들이 기업과 가계에 실제로 빌려준 대출 총액입니다. 실물 경제의 핏줄입니다.', 'eval': eval_totll, 'levels': [("대출 증가", "신용 팽창", COLOR_SAFE, "🟢", "경제가 활력을 띠고 자금이 원활히 공급됨"), ("대출 감소", "신용 축소", COLOR_DANGER, "🔴", "은행 대출 태도 강화(Credit Crunch), 침체 전조")]},
    'SOFR_IORB_Spread': {'name': '단기 조달 스프레드 (SOFR-IORB)', 'unit': '%', 'desc': '은행간 하루짜리 조달금리(SOFR)에서 연준 예치금리(IORB)를 뺀 값입니다. 단기 자금시장의 발작 여부를 측정합니다.', 'eval': eval_sofr, 'levels': [("0% 이하", "안정", COLOR_SAFE, "😌", "단기 시장 달러 넘침. 조달 원활"), ("0~0.05%", "주의", COLOR_WARN, "⚡", "레포 시장 유동성 약간 빡빡함"), ("0.05% 이상", "발작", COLOR_DANGER, "💥", "극심한 달러 가뭄 현상")]},
    'Emergency_Loans': {'name': '연준 H.4.1 긴급대출 총액', 'unit': '억 달러', 'desc': '위기에 처한 은행들이 연준의 할인창구나 BTFP를 통해 긴급하게 빌려간 자금입니다.', 'eval': eval_emerg, 'levels': [("0 근접", "안정", COLOR_SAFE, "🏥", "위기 없음. 은행들 자체 조달 원활"), ("수백억 달러", "뱅크런 경고", COLOR_DANGER, "🚑", "일부 은행 유동성 위기 발생 (SVB 사태 등)")]},
    'MMF': {'name': 'MMF 총 잔액', 'unit': '억 달러', 'desc': '언제든 현금화할 수 있는 머니마켓펀드 총액입니다. 기관/개인 대기 자금의 규모를 보여줍니다.', 'eval': eval_mmf, 'levels': [("잔액 감소", "위험 선호", COLOR_SAFE, "💸", "안전자산에서 돈을 빼서 주식 등 위험자산 투자"), ("잔액 증가", "자금 대피", COLOR_WARN, "🛡️", "시장 하락을 우려해 단기 현금으로 파킹 중")]},
    
    'DXY': {'name': 'DXY 달러 인덱스', 'unit': 'pt', 'desc': '주요 6개국 통화 대비 미국 달러의 가치입니다. 글로벌 유동성 환경을 좌우합니다.', 'eval': eval_dxy, 'levels': [("100 미만", "약세", COLOR_SAFE, "📉", "달러 약세. 신흥국 및 위험자산 랠리에 유리"), ("100~105", "중립", COLOR_NEUTRAL, "⚖️", "안정적인 박스권 유지"), ("105 이상", "강세", COLOR_DANGER, "📈", "글로벌 유동성 흡수, 신흥국 증시 부담 작용")]},
    'T10YIE': {'name': '10년물 기대인플레이션 (BEI)', 'unit': '%', 'desc': '채권 시장이 예상하는 향후 10년간의 평균 인플레이션율입니다.', 'eval': eval_bei, 'levels': [("2.0% 미만", "디스인플레", COLOR_WARN, "❄️", "침체 및 디플레이션 우려 반영"), ("2.0~2.5%", "골디락스", COLOR_SAFE, "🎯", "연준의 2% 목표 부합. 가장 안정적"), ("2.5% 이상", "인플레 고착화", COLOR_DANGER, "🔥", "고물가 지속 우려. 연준 금리 인하 지연")]}
}

# --- 공통 포맷팅 헬퍼 ---
def format_val(v, unit):
    if unit == '%': return f"{v:.3f}%" if "SOFR" in unit else f"{v:.2f}%"
    if unit == 'pt': return f"{v:.2f}"
    if unit == '억 달러': return f"{v:,.0f}억 달러"
    return str(v)

def format_chg(v, unit, is_sofr=False):
    prefix = "▲" if v > 0 else "▼" if v < 0 else "-"
    v_abs = abs(v)
    if unit == '%': return f"{prefix}{v_abs:.3f}%p" if is_sofr else f"{prefix}{v_abs:.2f}%p"
    if unit == 'pt': return f"{prefix}{v_abs:.2f}"
    if unit == '억 달러': return f"{prefix}{v_abs:,.0f}억 달러"
    return str(v)

def hex_to_rgba(hex_color, alpha=0.15):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{alpha})'

# --- 프리미엄 디테일 카드 렌더링 함수 ---
def render_premium_card(key, df, days):
    if key not in df.columns: return
    config = INDICATOR_META[key]
    
    sub_df = df[key].dropna().tail(days)
    if len(sub_df) < 2: return
    
    cur = sub_df.iloc[-1]
    val_1w = sub_df.iloc[-min(6, len(sub_df))] # 약 1주(5영업일) 전
    
    # 3개월 전 (approx 63일)
    hist_df = df[key].dropna()
    val_3m = hist_df.tail(min(63, len(hist_df))).iloc[0]
    
    chg_1w = cur - val_1w
    chg_3m = cur - val_3m
    
    status_label, status_color, status_text = config['eval'](cur, chg_1w)
    
    # Plotly Chart
    fig = plotly_go.Figure()
    fig.add_trace(plotly_go.Scatter(
        x=sub_df.index, y=sub_df, mode='lines',
        line=dict(color=status_color, width=2.5),
        fill='tozeroy', fillcolor=hex_to_rgba(status_color, 0.1)
    ))
    fig.update_layout(
        height=220, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', visible=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', side='right'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # HTML Component
    chg_color = "#ff4b4b" if chg_1w > 0 else "#09ab3b"
    if "Fed" in key or "Reserves" in key or "TOTLL" in key: chg_color = "#09ab3b" if chg_1w > 0 else "#ff4b4b"
    if chg_1w == 0: chg_color = "gray"
    
    is_sofr = (key == 'SOFR_IORB_Spread')
    
    level_cards_html = ""
    for lvl in config['levels']:
        level_cards_html += f"""
        <div style="flex: 1; min-width: 220px; background: rgba(128,128,128,0.04); border: 1px solid rgba(128,128,128,0.1); border-left: 4px solid {lvl[2]}; padding: 15px; border-radius: 8px;">
            <div style="font-weight: bold; font-size: 15px; margin-bottom: 6px;">{lvl[3]} {lvl[0]} — <span style="color:{lvl[2]}">{lvl[1]}</span></div>
            <div style="font-size: 13px; color: #888;">{lvl[4]}</div>
        </div>
        """
        
    html = f"""
    <div style="background: rgba(128,128,128,0.03); border: 1px solid rgba(128,128,128,0.15); border-radius: 12px; padding: 20px; margin-bottom: 30px;">
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
            <span style="background: {status_color}; color: white; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: bold; letter-spacing: 0.5px;">{status_label}</span>
            <span style="font-size: 30px; font-weight: 800; letter-spacing: -0.5px;">{format_val(cur, config['unit'])}</span>
        </div>
        <div style="font-size: 16px; font-weight: bold; margin-bottom: 8px; color: {status_color};">{config['name']} — <span style="color: inherit; font-weight: normal;">{status_text}</span></div>
        <div style="font-size: 14px; color: #777; margin-bottom: 25px;">
            1주 전 대비 <span style="color: {chg_color}; font-weight:bold;">{format_chg(chg_1w, config['unit'], is_sofr)}</span> · 3개월 전 대비 {format_chg(chg_3m, config['unit'], is_sofr)}
            <div style="font-size:12.5px; margin-top:6px;">📊 최근 {selected_days}일 기준 구간: 최저 {format_val(sub_df.min(), config['unit'])} / 최고 {format_val(sub_df.max(), config['unit'])}</div>
        </div>
        
        <div style="border-top: 1px solid rgba(128,128,128,0.15); padding-top: 20px;">
            <div style="font-size: 17px; font-weight: bold; margin-bottom: 12px;">📌 {config['name']}란?</div>
            <div style="font-size: 14.5px; color: #999; margin-bottom: 18px; line-height: 1.5;">{config['desc']}</div>
            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                {level_cards_html}
            </div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

# --- 상단 Hero 차트 (Net Liquidity vs SP500) ---
st.header("🌊 핵심 유동성 지표 (Net Liquidity)")
if 'Net_Liquidity' in df.columns and 'SP500' in df.columns:
    fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['Net_Liquidity'].tail(selected_days), name="순유동성 (억 달러)", line=dict(color='#007bff', width=2.5)), secondary_y=False)
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['SP500'].tail(selected_days), name="S&P 500", line=dict(color='#ff4b4b', width=1.5)), secondary_y=True)
    fig_liq.update_layout(title_text=f"Net Liquidity vs S&P 500 ({selected_period_label})", height=450, hovermode="x unified", margin=dict(t=50, b=0, l=0, r=0))
    fig_liq.update_yaxes(title_text="Net Liquidity (억 달러)", secondary_y=False)
    fig_liq.update_yaxes(title_text="S&P 500 Index", secondary_y=True)
    st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("""
    <div style="background: rgba(128,128,128,0.05); padding: 15px; border-radius: 10px; font-size:14px; margin-bottom: 30px;">
        💡 <b>Net Liquidity(순유동성)</b>은 연준의 대차대조표에서 RRP와 TGA를 뺀 값으로, 실제 시중에 공급된 순수 유동성을 뜻합니다. 파란선(유동성)이 오르면 빨간선(주가)도 오르는 강한 상관관계를 가집니다.
    </div>
    """, unsafe_allow_html=True)

# --- 탭을 활용한 카테고리별 디테일 카드 배치 ---
tab1, tab2, tab3, tab4 = st.tabs(["🚨 시장 리스크 지표", "🏦 유동성 창구", "💰 신용 및 자금시장", "🌍 글로벌 매크로"])

with tab1:
    st.markdown("#### 핵심 위험 관리 지표")
    render_premium_card('VIX', df, selected_days)
    render_premium_card('MOVE', df, selected_days)
    render_premium_card('10Y_2Y', df, selected_days)
    render_premium_card('HY_Spread', df, selected_days)
    render_premium_card('FSI', df, selected_days)

with tab2:
    st.markdown("#### 유동성을 좌우하는 3대 창구")
    render_premium_card('Fed_BS', df, selected_days)
    render_premium_card('Reserves', df, selected_days)
    render_premium_card('RRP', df, selected_days)
    render_premium_card('TGA', df, selected_days)

with tab3:
    st.markdown("#### 실물 경제 신용 및 조달 스트레스")
    render_premium_card('TOTLL', df, selected_days)
    render_premium_card('SOFR_IORB_Spread', df, selected_days)
    render_premium_card('Emergency_Loans', df, selected_days)
    render_premium_card('MMF', df, selected_days)

with tab4:
    st.markdown("#### 인플레이션 및 글로벌 자금 흐름")
    render_premium_card('DXY', df, selected_days)
    render_premium_card('T10YIE', df, selected_days)

st.divider()

# --- 6. AI 기반 종합 시황 리포트 ---
st.header("📝 AI 기반 매크로 종합 시황 리포트")
def generate_report(df, days):
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
    
    report = []
    report.append(f"### 📌 시장 심리 및 시스템 리스크 ({selected_period_label} 기준)")
    if vix > 30: report.append(f"- **[위험 심리]** VIX가 {vix:.2f}로 공포 심리가 팽배합니다.")
    else: report.append(f"- **[위험 심리]** VIX가 {vix:.2f}로 시장이 안정적인 흐름을 유지하고 있습니다.")
    
    if emerg_loans > 500 or move > 140: report.append("- **[시스템 경고]** 연준 긴급 대출이나 채권 변동성(MOVE)이 높아 스트레스 징후가 관찰됩니다.")
    else: report.append(f"- **[시스템 안정]** 긴급 대출 잔액이 {emerg_loans:,.0f}억 달러로 시스템 위기 징후는 나타나지 않고 있습니다.")

    report.append("\n### 📌 은행 신용 및 달러 펀딩 환경")
    if sofr_spread > 0.05: report.append(f"- **[조달 스트레스]** SOFR-IORB 스프레드가 {sofr_spread:.3f}%로 확대되어 단기 시장 달러 경색 조짐이 보입니다.")
    else: report.append(f"- **[조달 안정화]** SOFR-IORB 스프레드가 {sofr_spread:.3f}%로 단기 레포 시장의 달러 유동성이 원활합니다.")
    
    if totll_chg < 0: report.append(f"- **[신용 축소]** 상업은행 대출이 {abs(totll_chg):,.0f}억 달러 감소하여 실물 경제 신용 공급이 둔화되었습니다.")
    elif totll_chg > 0: report.append(f"- **[신용 팽창]** 상업은행 대출이 {totll_chg:,.0f}억 달러 증가하며 신용 창출이 이어지고 있습니다.")

    report.append("\n### 📌 매크로 경제 및 인플레이션")
    if yield_curve < 0: report.append(f"- **[침체 선행]** 장단기 금리차가 {yield_curve:.2f}%로 역전 상태를 보이며 경기 둔화 가능성을 암시합니다.")
    else: report.append(f"- **[안정적 금리차]** 장단기 금리차가 {yield_curve:.2f}%로 우상향 곡선을 회복했습니다.")
    
    if bei > 2.5: report.append(f"- **[물가 불안]** 10년물 기대인플레(BEI)가 {bei:.2f}%로 연준의 금리 인하 스탠스를 제약할 수 있습니다.")
    else: report.append(f"- **[물가 안정]** 기대인플레(BEI)가 {bei:.2f}%로 연준의 물가 목표 궤적에 부합합니다.")

    report.append("\n### 💡 종합 자산 배분 전략")
    if (yield_curve < 0 and hy_spread > 5.0) or sofr_spread > 0.1:
        report.append(f"👉 **[보수적 대응 권고]** 침체 시그널과 펀딩 스트레스가 겹쳤습니다. 현금 비중 확대를 권장합니다.")
    elif liq_change > 0 and dxy < 105 and sofr_spread <= 0:
        report.append(f"👉 **[위험 자산 선호]** 순유동성이 증가(+{liq_change:,.0f}억 달러)하고 달러({dxy:.2f})가 안정적입니다. 주식 등 위험 자산 랠리가 지지받을 환경입니다.")
    else:
        report.append("👉 **[관망 및 퀄리티 주식 집중]** 거시 지표들이 혼재되어 있습니다. 우량 기업 위주로 선별적인 접근이 필요합니다.")

    return "\n".join(report)

st.info(generate_report(df, selected_days))
st.caption(f"마지막 데이터 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (기준일자: {df.index[-1].strftime('%Y-%m-%d')})")
st.markdown("</div>", unsafe_allow_html=True)
