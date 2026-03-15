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
<meta name="robots" content="notranslate">
<style>
/* 전반적인 폰트 및 여백 조정 */
div[data-testid="stVerticalBlock"] > div {
    padding-bottom: 0.5rem;
}
hr {
    margin-top: 3rem;
    margin-bottom: 3rem;
    border-color: rgba(128,128,128,0.2);
}
</style>
<div class="notranslate">
""", unsafe_allow_html=True)

st.title("🌐 시장 경제 지표 대시보드")
st.markdown("시장의 핵심 유동성 흐름과 매크로 지표를 심층적으로 추적합니다. (데이터는 매일 자동 갱신됩니다)")

# --- 기간 선택 컨트롤 ---
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### ⏱️ 추이 기준 기간 선택")
period_options = {"1개월": 21, "3개월": 63, "6개월": 126, "1년": 252, "3년": 756}
selected_period_label = st.radio("기간", list(period_options.keys()), index=3, horizontal=True, label_visibility="collapsed")
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

# --- 색상 테마 설정 ---
COLOR_SAFE = "#1976D2"   # 긍정/안정 (파랑 - 눈 피로 완화)
COLOR_WARN = "#E67E22"   # 주의 (선명한 귤색/주황색 - 빨강과 명확히 구분됨)
COLOR_DANGER = "#D32F2F" # 경계/위험 (진한 빨강)
COLOR_NEUTRAL = "#607D8B" # 중립 (블루 그레이 - 안정의 파랑과 구분)

# --- 지표별 평가 함수 및 메타데이터 ---
def eval_vix(v, d):
    if v >= 30: return "경계", COLOR_DANGER, "투자자들이 겁먹은 상태입니다. 과거 주요 시장 충격 때 항상 이 구간을 넘었어요."
    elif v >= 20: return "주의", COLOR_WARN, "불안이 커지고 있어요. 포지션 점검과 방어적 자산 비중 확대를 고려할 때예요."
    else: return "안정", COLOR_SAFE, "시장이 조용하고 투자자들이 편안한 상태예요. 주식 등 위험자산을 선호합니다."

def eval_move(v, d):
    if v >= 140: return "위험", COLOR_DANGER, "채권 시장이 패닉에 빠졌어요. 금융 시스템 스트레스를 강하게 경계해야 합니다."
    elif v >= 100: return "주의", COLOR_WARN, "채권 금리가 요동치고 있어요. 유동성 흐름을 주의 깊게 관찰하세요."
    else: return "안정", COLOR_SAFE, "채권 시장이 평온하게 움직이고 있어 거시 경제 불확실성이 낮습니다."

def eval_10y2y(v, d):
    if v < 0: return "침체 경고 (역전)", COLOR_DANGER, "단기금리가 장기금리를 역전했어요. 과거 50년간 모든 침체 전에 나타났던 경고 신호입니다."
    else: return "정상 (양수)", COLOR_SAFE, "장기금리>단기금리로 경제 성장 기대가 반영된 일반적인 건강한 상태입니다."

def eval_fsi(v, d):
    if v > 0: return "스트레스", COLOR_DANGER, "금융 시스템 내에 자금 경색 등 긴장 상태가 평균 이상으로 높아졌습니다."
    else: return "안정", COLOR_SAFE, "금융 시스템이 원활하게 작동하고 있으며 신용 경색 우려가 없습니다."

def eval_hy(v, d):
    if v >= 5.0: return "경고", COLOR_DANGER, "정크본드 금리가 급등했어요. 기업들의 자금줄이 마르고 부도 위험이 커진 상태입니다."
    elif v >= 4.0: return "주의", COLOR_WARN, "한계 기업들의 자금 조달 여건이 빡빡해지기 시작했습니다."
    else: return "안정", COLOR_SAFE, "하이일드 채권 시장이 안정적이며 전반적인 기업 신용 위험이 낮습니다."

def eval_fed(v, d):
    if d > 0: return "팽창 (QE)", COLOR_SAFE, "연준이 자산을 늘리며 시중에 유동성을 쏟아내고 있어요. 증시엔 강한 호재입니다."
    else: return "긴축 (QT)", COLOR_DANGER, "연준이 자산을 축소하며 시중의 달러를 흡수하고 있어요. 유동성 축소에 대비하세요."

def eval_reserves(v, d):
    if d > 0: return "확대", COLOR_SAFE, "은행들의 금고가 두둑해졌어요. 대출과 투자가 원활해져 증시에 활력을 줍니다."
    else: return "축소", COLOR_DANGER, "은행들의 자금 여력이 줄어들고 있어요. 신용 공급 둔화와 변동성 확대에 유의하세요."

def eval_rrp(v, d):
    if v == 0: return "고갈", COLOR_DANGER, "역레포 대기 자금이 완전히 소진되었어요. 시장 충격을 흡수할 완충재가 사라졌습니다."
    elif v < 1000: return "바닥 근접", COLOR_WARN, "증시를 밀어올리던 잉여 자금이 거의 바닥을 드러내고 있어요."
    elif d > 0: return "위험 회피", COLOR_DANGER, "불안해진 시중 자금이 다시 연준 금고(역레포)로 대피하고 있습니다."
    else: return "위험 선호", COLOR_SAFE, "역레포 자금이 방출되며 증시 등 위험 자산으로 흘러들어가고 있습니다."

def eval_tga(v, d):
    if d > 0: return "자금 흡수", COLOR_DANGER, "재무부가 국채 발행/세금으로 시중 자금을 블랙홀처럼 흡수 중이라 단기 악재입니다."
    else: return "재정 지출", COLOR_SAFE, "재무부가 예산을 집행하며 시중에 자금을 펌핑하고 있어 증시에 긍정적입니다."

def eval_totll(v, d):
    if d > 0: return "신용 팽창", COLOR_SAFE, "상업은행 대출이 늘어나 실물 경제에 자금이 핏줄처럼 잘 돌고 있습니다."
    elif d < 0: return "신용 축소", COLOR_DANGER, "은행이 대출 문턱을 높였어요(Credit Crunch). 실물 경제 침체의 전조증상입니다."
    else: return "정체", COLOR_WARN, "대출 규모가 유지되며 관망세를 보이고 있습니다."

def eval_sofr(v, d):
    if v > 0.05: return "발작 조짐", COLOR_DANGER, "기준금리보다 시장 조달금리가 비싸졌어요. 극심한 달러 가뭄 현상이 발생했습니다!"
    elif v > 0: return "타이트", COLOR_WARN, "단기 자금 시장의 달러 유동성이 빠듯해지고 있습니다."
    else: return "안정", COLOR_SAFE, "0% 부근에서 단기 레포 시장의 달러 융통이 원활하게 이루어지고 있습니다."

def eval_emerg(v, d):
    if v > 500: return "위기", COLOR_DANGER, "은행들이 연준에서 긴급 자금을 대거 빌려가고 있어요. 뱅크런이나 유동성 위기를 경고합니다!"
    elif v > 0: return "주의", COLOR_WARN, "일부 은행이 연준의 긴급 차입을 이용했습니다. 국지적인 스트레스가 있습니다."
    else: return "매우 안정", COLOR_SAFE, "은행 시스템이 건강하여 연준의 긴급 대출 잔액이 '0'입니다. 완벽히 정상입니다."

def eval_mmf(v, d):
    if d > 0: return "자금 대피", COLOR_WARN, "시장 불안으로 투자자들이 단기 현금(MMF)으로 피신 중입니다."
    else: return "위험 선호", COLOR_SAFE, "MMF 대기 자금이 주식 등 위험 자산으로 유입되고 있습니다."

def eval_dxy(v, d):
    if v >= 105: return "강세", COLOR_DANGER, "강달러 현상으로 신흥국 자본 이탈 및 글로벌 유동성 축소가 우려됩니다."
    elif v < 100: return "약세", COLOR_SAFE, "달러 약세로 글로벌 증시와 위험 자산 랠리에 매우 우호적인 환경입니다."
    else: return "중립", COLOR_NEUTRAL, "달러가 박스권에서 안정적으로 유지되며 시장에 미치는 영향이 중립적입니다."

def eval_bei(v, d):
    if v >= 2.5: return "물가 불안", COLOR_DANGER, "인플레이션 고착화 우려로 연준의 금리 인하가 지연될 가능성이 큽니다."
    elif v <= 2.0: return "디스인플레", COLOR_WARN, "물가가 너무 빨리 식으며 오히려 경기 둔화 및 침체 우려가 부각되는 구간입니다."
    else: return "골디락스", COLOR_SAFE, "연준의 물가 목표치(2%) 근방에서 안정적으로 움직이는 최고의 상태입니다."

INDICATOR_META = {
    'VIX': {'name': 'VIX 공포지수', 'unit': 'pt', 'inverted': True, 'meta': '단위: 포인트 · 일간 · 20 이상 = 주의 / 30 이상 = 경계', 
            'desc': '시장이 앞으로 얼마나 출렁일지 예상하는 지수예요. 쉽게 말해 투자자들의 불안감을 숫자로 표현한 것으로, 주가가 급락할 때 VIX는 급등합니다.', 
            'eval': eval_vix, 'levels': [("20 미만", "안정", COLOR_SAFE, "😌", "시장이 조용하고 투자자들이 편안한 상태. 주식 등 위험자산 선호."), ("20~30", "주의", COLOR_WARN, "🙄", "불확실성이 커지는 구간. 변동성이 높아질 수 있어 조심할 필요가 있어요."), ("30 이상", "경계", COLOR_DANGER, "😱", "투자자들이 겁먹은 상태. 과거 주요 시장 충격 때 항상 이 구간을 넘었어요.")]},
    'MOVE': {'name': 'MOVE 채권 변동성 지수', 'unit': 'pt', 'inverted': True, 'meta': '단위: 포인트 · 일간 · 100 이상 = 주의', 
             'desc': '미국 국채 시장의 변동성을 보여주는 채권판 VIX입니다. 주식 시장의 공포지수보다 채권 시장의 발작이 거시적 금융 위기를 훨씬 더 빨리, 정확하게 잡아냅니다.', 
             'eval': eval_move, 'levels': [("100 미만", "안정", COLOR_SAFE, "😌", "채권 금리가 안정적으로 움직이며 거시 경제 불확실성이 낮음."), ("100~140", "주의", COLOR_WARN, "⚠️", "금리 변동성이 확대되며 유동성 흐름에 주의가 필요한 구간."), ("140 이상", "위험", COLOR_DANGER, "🚨", "시스템 리스크 및 금융 위기 징후 발생. 극도의 경계 필요.")]},
    '10Y_2Y': {'name': '미국 장단기 금리차 (10Y-2Y)', 'unit': '%', 'inverted': False, 'meta': '단위: % · 일간 · 음수 = 역전 (침체 경고)', 
               'desc': '10년 금리에서 2년 금리를 뺀 값이에요. 보통은 장기(10년) 금리가 더 높아 양수(+)인데, 이게 음수(-)로 뒤집히면 "역전"이라고 해요. 역전은 역사적으로 경기침체 전에 항상 나타났던 강력한 경고 신호입니다.', 
               'eval': eval_10y2y, 'levels': [("양수(+) — 정상", "안정", COLOR_SAFE, "📈", "장기금리 > 단기금리. 경기 확장 기대가 반영된 일반적인 건강한 상태."), ("음수(-) — 역전", "침체 경고", COLOR_DANGER, "📉", "단기금리 > 장기금리. 과거 50년간 모든 미국 경기침체 전에 나타났어요."), ("역전 후 상승 전환", "주의", COLOR_WARN, "⏱️", "역전이 풀리며 다시 양수로 올라오는 시점이 실제 침체 시작과 맞물리는 경향이 있어요.")]},
    'FSI': {'name': '금융 스트레스 지수 (FSI)', 'unit': 'pt', 'inverted': True, 'meta': '단위: 포인트 · 주간 · 0 이상 = 스트레스 상태', 
            'desc': '18개 주요 금융 시장 지표를 종합하여 미국 금융 시스템이 얼마나 긴장하고 있는지 전반적인 스트레스 수준을 측정합니다. 0을 기준으로 평가합니다.', 
            'eval': eval_fsi, 'levels': [("0 미만", "안정", COLOR_SAFE, "✅", "금융 시스템이 원활하게 작동하고 자금 융통에 문제 없음."), ("0 이상", "스트레스", COLOR_DANGER, "💥", "평균 이상의 시스템 긴장 상태. 신용 경색 및 유동성 부족 우려.")]},
    'HY_Spread': {'name': '하이일드 스프레드', 'unit': '%', 'inverted': True, 'meta': '단위: % · 일간 · 5% 이상 = 경색 경고', 
                  'desc': '가장 안전한 미국 국채와 부도 위험이 있는 정크본드(하이일드 채권) 간의 금리 격차입니다. 이 격차가 벌어지면 기업들의 자금줄이 마르고 있다는 뜻입니다.', 
                  'eval': eval_hy, 'levels': [("4% 미만", "안정", COLOR_SAFE, "👍", "한계 기업들도 무리 없이 자금을 조달할 수 있는 풍부한 유동성 환경."), ("4~5%", "주의", COLOR_WARN, "🤔", "신용 경계감 상승. 기업 대출 문턱이 조금씩 높아지는 구간."), ("5% 이상", "경고", COLOR_DANGER, "🔥", "자금줄이 마르고 기업 부도 위험이 급상승하는 신용 경색 구간.")]},
    
    'Fed_BS': {'name': '연준 대차대조표 총자산', 'unit': '억 달러', 'inverted': False, 'meta': '단위: 억 달러 · 주간 · 상승 = 유동성 공급', 
               'desc': '미국 중앙은행(Fed)이 돈을 찍어내어 보유하고 있는 자산의 총합입니다. 이 숫자가 커지면 시중에 돈을 푸는 것(양적완화)이고, 작아지면 돈을 거둬들이는 것(양적긴축)입니다.', 
               'eval': eval_fed, 'levels': [("상승 (QE)", "팽창", COLOR_SAFE, "💸", "시중에 자금을 쏟아내어 증시와 위험자산에 강한 상승 압력 제공."), ("하락 (QT)", "긴축", COLOR_DANGER, "🧽", "시중의 달러를 흡수하여 자산 가격의 상단을 제한하고 조정을 유발.")]},
    'Reserves': {'name': '지급준비금 (Reserves)', 'unit': '억 달러', 'inverted': False, 'meta': '단위: 억 달러 · 주간 · 실제 금융권 유동성 체력', 
                 'desc': '상업은행들이 대출을 내주기 위해 연준 금고에 예치해둔 대기 자금입니다. 은행이 실물 경제와 주식 시장에 신용을 공급할 수 있는 핵심 체력입니다.', 
                 'eval': eval_reserves, 'levels': [("상승/유지", "확대", COLOR_SAFE, "🏦", "은행의 자금 여력이 증가하여 대출과 투자가 원활해지는 긍정적 환경."), ("하락", "축소", COLOR_DANGER, "🏜️", "유동성이 마르기 시작하여 시장 변동성 확대 및 신용 경색 대비 필요.")]},
    'RRP': {'name': '역레포 잔액 (RRP)', 'unit': '억 달러', 'inverted': True, 'meta': '단위: 억 달러 · 일간 · 하락 = 증시로 자금 유입', 
            'desc': '시중에 갈 곳을 잃은 단기 잉여 자금이 연준 창고로 들어간 금액입니다. 이 잔액이 줄어든다는 것은 돈이 창고에서 빠져나와 주식이나 채권 시장(실물)으로 흘러가고 있다는 좋은 신호입니다.', 
            'eval': eval_rrp, 'levels': [("방출 (감소)", "위험 선호", COLOR_SAFE, "🌊", "대기 자금이 연준 창고에서 나와 실물 및 증시로 유입되는 강세 요인."), ("흡수 (증가)", "위험 회피", COLOR_DANGER, "🔒", "시장 불안으로 시중 자금이 다시 연준 금고로 피신하는 약세 요인."), ("0 근접", "고갈 경고", COLOR_WARN, "🪫", "충격을 흡수해 주던 대기 자금이 바닥나 유동성 절벽 우려.")]},
    'TGA': {'name': '재무부 일반 계좌 (TGA)', 'unit': '억 달러', 'inverted': True, 'meta': '단위: 억 달러 · 주간 · 정부의 마이너스 통장', 
            'desc': '미국 정부가 사용하는 메인 통장입니다. 세금을 걷거나 국채를 새로 발행해서 돈을 빌리면 이 통장에 돈이 쌓이고(시중 자금 흡수), 예산을 쓰면 잔고가 줄어듭니다(시중에 돈이 풀림).', 
            'eval': eval_tga, 'levels': [("잔액 감소", "재정 지출", COLOR_SAFE, "🚀", "정부가 예산을 적극적으로 집행하여 시중에 돈을 펌핑하는 긍정적 상태."), ("잔액 증가", "자금 흡수", COLOR_DANGER, "🕳️", "세금이나 국채 대규모 발행으로 시중 유동성을 블랙홀처럼 빨아들이는 단기 악재.")]},
    
    'TOTLL': {'name': 'H.8 상업은행 총대출', 'unit': '억 달러', 'inverted': False, 'meta': '단위: 억 달러 · 주간 · 실물 경제 신용 공급 지표', 
              'desc': '미국 내 상업은행들이 기업과 가계에 실제로 빌려준 대출의 총액입니다. 거시 경제의 핏줄과 같으며, 이 수치가 늘어나야 실물 경제가 성장합니다.', 
              'eval': eval_totll, 'levels': [("대출 증가", "신용 팽창", COLOR_SAFE, "🟢", "경제가 활력을 띠고 가계와 기업으로 자금이 원활히 공급됨."), ("대출 감소", "신용 축소", COLOR_DANGER, "🔴", "은행이 대출 문턱을 높인 상태(Credit Crunch). 강력한 경기 침체 전조증상.")]},
    'SOFR_IORB_Spread': {'name': '단기 조달 스프레드 (SOFR - IORB)', 'unit': '%', 'inverted': True, 'meta': '단위: % · 일간 · 0.05% 이상 = 단기 자금 발작', 
                         'desc': '은행간 하루짜리 실제 조달금리(SOFR)에서 연준이 보장하는 예치금리(IORB)를 뺀 값입니다. 이 값이 0보다 커진다는 것은 시장에서 달러 구하기가 연준 기준보다 비싸졌다는 뜻으로, 단기 유동성 발작을 나타냅니다.', 
                         'eval': eval_sofr, 'levels': [("0% 이하", "안정", COLOR_SAFE, "😌", "단기 자금 시장에 달러가 풍부하여 조달이 매우 원활한 상태."), ("0 ~ 0.05%", "주의", COLOR_WARN, "⚡", "레포 시장의 유동성이 타이트해지며 경계감이 형성되는 구간."), ("0.05% 이상", "발작 경고", COLOR_DANGER, "💥", "단기 자금 시장에 극심한 달러 가뭄 현상 발생. 연준의 개입 필요.")]},
    'Emergency_Loans': {'name': '연준 긴급대출 총액 (할인창구 + BTFP)', 'unit': '억 달러', 'inverted': True, 'meta': '단위: 억 달러 · 주간 · 은행 시스템 위기 지표', 
                        'desc': '유동성 위기에 처한 은행들이 연준의 비상 창구(Discount Window)나 BTFP 프로그램을 통해 긴급하게 빌려간 구제 자금의 총합입니다. 정상적인 은행은 낙인효과 때문에 이 돈을 쓰지 않습니다.', 
                        'eval': eval_emerg, 'levels': [("0 (또는 극소액)", "안정", COLOR_SAFE, "🏥", "위기 없음. 모든 은행들이 시장에서 자체적으로 자금 조달 가능."), ("수백억 달러 급등", "위기 발생", COLOR_DANGER, "🚑", "일부 은행권에 심각한 뱅크런이나 유동성 위기 발생 (예: SVB 사태).")]},
    
    'MMF': {'name': '머니마켓펀드 (MMF) 총 잔액', 'unit': '억 달러', 'inverted': True, 'meta': '단위: 억 달러 · 주간 · 기관/개인의 대기 자금', 
            'desc': '투자자들이 언제든 현금화할 수 있는 초단기 금융상품(MMF)에 파킹해둔 자금 총액입니다. 시장이 불안하면 주식을 팔고 이리로 도망오고, 시장이 좋으면 여기서 돈을 빼서 주식을 삽니다.', 
            'eval': eval_mmf, 'levels': [("잔액 감소", "위험 선호", COLOR_SAFE, "💸", "안전 자산에서 돈을 빼서 주식 등 위험 자산으로 적극적으로 투자하는 긍정적 신호."), ("잔액 증가", "자금 대피", COLOR_WARN, "🛡️", "시장 하락이나 불확실성을 우려해 투자를 멈추고 현금으로 관망하는 상태.")]},
    'DXY': {'name': 'DXY 달러 인덱스', 'unit': 'pt', 'inverted': True, 'meta': '단위: 포인트 · 일간 · 글로벌 달러 가치', 
            'desc': '유로, 엔 등 주요 6개국 통화 대비 미국 달러의 평균 가치를 보여줍니다. 달러가 비싸지면(강세) 글로벌 투자 자금이 미국으로 빨려 들어가 신흥국 증시는 피를 말리게 됩니다.', 
            'eval': eval_dxy, 'levels': [("100 미만", "약세", COLOR_SAFE, "📉", "달러 약세. 미국 외 국가(신흥국)로 자본이 유입되며 글로벌 증시 랠리에 매우 유리."), ("100~105", "중립", COLOR_NEUTRAL, "⚖️", "달러 가치가 박스권 내에서 안정적으로 유지되며 시장 영향이 중립적임."), ("105 이상", "강세", COLOR_DANGER, "📈", "달러 초강세. 글로벌 유동성 흡수 및 신흥국 통화 가치 하락으로 증시 부담 가중.")]},
    'T10YIE': {'name': '10년물 기대인플레이션 (BEI)', 'unit': '%', 'inverted': False, 'meta': '단위: % · 일간 · 채권 시장의 물가 전망', 
               'desc': '일반 국채 금리와 물가연동국채(TIPS) 금리의 차이로 계산하며, 채권 시장 참여자들이 예상하는 향후 10년간의 평균 인플레이션율입니다. 연준의 통화 정책(금리 인하/인상)을 결정짓는 핵심 잣대입니다.', 
               'eval': eval_bei, 'levels': [("2.0% ~ 2.5%", "골디락스", COLOR_SAFE, "🎯", "연준의 장기 목표치(2%)에 부합. 경제가 뜨겁지도 차갑지도 않은 최적의 상태."), ("2.0% 미만", "디스인플레", COLOR_WARN, "❄️", "물가가 너무 빨리 식으며 오히려 경기 침체 및 수요 둔화 우려가 반영됨."), ("2.5% 이상", "인플레 고착화", COLOR_DANGER, "🔥", "고물가가 지속될 것이란 우려. 연준의 금리 인하가 지연되거나 추가 긴축 가능성.")]}
}

# --- 공통 포맷팅 헬퍼 ---
def format_val(v, unit):
    if unit == '%': return f"{v:.3f}%" if "SOFR" in unit else f"{v:.2f}%"
    if unit == 'pt': return f"{v:.2f}"
    if unit == '억 달러': return f"{v:,.0f}억 달러"
    return str(v)

def format_chg_text(cur, prev, unit, is_inverted, is_sofr=False):
    chg = cur - prev
    pct = (chg / prev * 100) if prev != 0 else 0
    abs_chg = abs(chg)
    
    if chg == 0:
        return f"<span style='color: gray; font-weight: bold;'>변동 없음</span>", "gray"
    
    if unit == '%': 
        val_str = f"{abs_chg:.3f}%p" if is_sofr else f"{abs_chg:.2f}%p"
    elif unit == 'pt': 
        val_str = f"{abs_chg:.2f}pt"
    else: 
        val_str = f"{abs_chg:,.0f}억 달러"

    # 지표 특성에 따른 긍정/부정 판단 및 색상 매핑
    if chg > 0:
        dir_text = "상승" if unit in ['pt', '%'] else "증가"
        arrow = "▲"
        color = COLOR_DANGER if is_inverted else COLOR_SAFE
    else:
        dir_text = "하락" if unit in ['pt', '%'] else "감소"
        arrow = "▼"
        color = COLOR_SAFE if is_inverted else COLOR_DANGER

    html_str = f"<span style='color: {color}; font-weight: bold;'>{arrow}{val_str} {dir_text}</span>"
    return html_str, color

def hex_to_rgba(hex_color, alpha=0.15):
    hex_color = hex_color.lstrip('#')
    r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    return f'rgba({r},{g},{b},{alpha})'

# --- 프리미엄 디테일 카드 렌더링 함수 ---
def render_detailed_indicator(key, df, days):
    if key not in df.columns: return
    meta = INDICATOR_META[key]
    
    sub_df = df[key].dropna().tail(days)
    if len(sub_df) < 2: return
    
    cur = sub_df.iloc[-1]
    val_1w = sub_df.iloc[-min(6, len(sub_df))] # 약 1주 전
    val_3m = df[key].dropna().tail(min(63, len(df[key].dropna()))).iloc[0] # 약 3개월 전
    
    chg_1w = cur - val_1w
    status_label, status_color, status_text = meta['eval'](cur, chg_1w)
    
    is_sofr = (key == 'SOFR_IORB_Spread')
    is_inverted = meta['inverted']
    
    chg_1w_html, _ = format_chg_text(cur, val_1w, meta['unit'], is_inverted, is_sofr)
    chg_3m_html, _ = format_chg_text(cur, val_3m, meta['unit'], is_inverted, is_sofr)
    
    # 1. 헤더 (타이틀 및 메타 정보)
    st.markdown(f"<h3 style='margin-bottom: 5px;'>{meta['name']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<div style='color: #888; font-size: 14px; margin-bottom: 15px;'>{meta['meta']}</div>", unsafe_allow_html=True)
    
    # 2. Plotly 차트
    fig = plotly_go.Figure()
    fig.add_trace(plotly_go.Scatter(
        x=sub_df.index, y=sub_df, mode='lines',
        line=dict(color=status_color, width=2.5),
        fill='tozeroy', fillcolor=hex_to_rgba(status_color, 0.1)
    ))
    # 차트 기준선 추가 로직 (VIX 30, MOVE 100, 금리차 0 등)
    if key == '10Y_2Y': fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    elif key == 'VIX': fig.add_hline(y=30, line_dash="dash", line_color="red", opacity=0.3)
    elif key == 'MOVE': fig.add_hline(y=140, line_dash="dash", line_color="red", opacity=0.3)
    elif key == 'SOFR_IORB_Spread': fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        height=280, margin=dict(l=0, r=0, t=10, b=0),
        xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)'),
        yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', side='right'),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # 3. 요약 박스 (Summary Box) - 들여쓰기 제거
    summary_html = f"""<div style="background-color: rgba(128,128,128,0.06); border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 20px; margin-top: 10px; margin-bottom: 20px;">
<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
<span style="background-color: rgba(128,128,128,0.2); padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: bold; opacity: 0.8;">최근 {selected_period_label}</span>
<span style="background-color: {status_color}20; color: {status_color}; border: 1px solid {status_color}50; padding: 4px 10px; border-radius: 6px; font-size: 13px; font-weight: bold;">{status_label}</span>
<span style="font-size: 26px; font-weight: 900;">{format_val(cur, meta['unit'])}</span>
</div>
<div style="font-size: 15.5px; margin-bottom: 10px;">
<b>{meta['name'].split(' ')[0]} {format_val(cur, meta['unit'])}</b> — {status_text}
</div>
<div style="font-size: 14px; opacity: 0.85; margin-bottom: 12px;">
1주 전({format_val(val_1w, meta['unit'])}) 대비 {chg_1w_html} · 3개월 전({format_val(val_3m, meta['unit'])}) 대비 {chg_3m_html}
</div>
<div style="font-size: 13px; opacity: 0.6; display: flex; align-items: center; gap: 5px;">
📊 최근 {selected_period_label} 구간: 최저 {format_val(sub_df.min(), meta['unit'])} / 최고 {format_val(sub_df.max(), meta['unit'])}
</div>
</div>"""
    st.markdown(summary_html, unsafe_allow_html=True)
    
    # 4. 설명 박스 (Explanation Grid) - 들여쓰기 제거
    level_cards_html = ""
    for lvl in meta['levels']:
        level_cards_html += f"""<div style="border: 1px solid rgba(128,128,128,0.15); border-left: 4px solid {lvl[2]}; border-radius: 8px; padding: 15px; background-color: rgba(128,128,128,0.03);">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 8px;">
<span style="font-size: 18px;">{lvl[3]}</span>
<span style="font-weight: bold; font-size: 14.5px;">{lvl[0]} — <span style="color:{lvl[2]}">{lvl[1]}</span></span>
</div>
<div style="font-size: 13.5px; opacity: 0.75; line-height: 1.5;">{lvl[4]}</div>
</div>"""
        
    expl_html = f"""<div style="background-color: rgba(128,128,128,0.02); border: 1px solid rgba(128,128,128,0.1); border-radius: 12px; padding: 25px; margin-bottom: 60px;">
<div style="font-size: 16px; font-weight: bold; margin-bottom: 12px;">📌 {meta['name'].split('(')[0].strip()}란?</div>
<div style="font-size: 14.5px; opacity: 0.8; margin-bottom: 22px; line-height: 1.6;">{meta['desc']}</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 15px;">
{level_cards_html}
</div>
</div>"""
    st.markdown(expl_html, unsafe_allow_html=True)


# ==========================================
# 대시보드 렌더링 시작
# ==========================================

# --- 영웅 섹션: Net Liquidity vs SP500 ---
st.header("🌊 핵심: 미국 유동성 흐름 (Net Liquidity)")
if 'Net_Liquidity' in df.columns and 'SP500' in df.columns:
    fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['Net_Liquidity'].tail(selected_days), name="순유동성 (억 달러)", line=dict(color='#1976D2', width=2.5)), secondary_y=False)
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['SP500'].tail(selected_days), name="S&P 500", line=dict(color='#D32F2F', width=1.5)), secondary_y=True)
    fig_liq.update_layout(title_text=f"Net Liquidity vs S&P 500 ({selected_period_label})", height=450, hovermode="x unified", margin=dict(t=50, b=0, l=0, r=0))
    fig_liq.update_yaxes(title_text="Net Liquidity (억 달러)", secondary_y=False)
    fig_liq.update_yaxes(title_text="S&P 500 Index", secondary_y=True)
    st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("""<div style="background-color: rgba(128,128,128,0.06); border: 1px solid rgba(128,128,128,0.2); border-radius: 12px; padding: 20px; margin-bottom: 60px;">
<div style="font-size: 16px; font-weight: bold; margin-bottom: 10px;">📌 Net Liquidity(순유동성) 공식: 연준 대차대조표 - 역레포(RRP) - 재무부 계좌(TGA)</div>
<div style="font-size: 14.5px; opacity: 0.85; line-height: 1.6;">
중앙은행이 시장에 실질적으로 공급한 순수 유동성 자금의 양입니다.<br>
통상적으로 <b style="color:#1976D2">파란선(순유동성)</b>이 오르면 시중에 돈이 넘쳐나 <b style="color:#D32F2F">빨간선(S&P 500)</b>도 함께 오르고, 내리면 주가도 조정을 받는 <b>강한 양(+)의 상관관계</b>를 가집니다.
</div>
</div>""", unsafe_allow_html=True)


# --- 1. 시장 리스크 지표 ---
st.markdown("<hr>", unsafe_allow_html=True)
st.header("🚨 1. 시장 리스크 및 스트레스 지표")
render_detailed_indicator('VIX', df, selected_days)
render_detailed_indicator('MOVE', df, selected_days)
render_detailed_indicator('10Y_2Y', df, selected_days)
render_detailed_indicator('HY_Spread', df, selected_days)
render_detailed_indicator('FSI', df, selected_days)

# --- 2. 유동성 창구 지표 ---
st.markdown("<hr>", unsafe_allow_html=True)
st.header("🏦 2. 유동성을 좌우하는 핵심 3대 창구")
render_detailed_indicator('Fed_BS', df, selected_days)
render_detailed_indicator('Reserves', df, selected_days)
render_detailed_indicator('TGA', df, selected_days)

# --- 3. 자금 시장 및 신용 지표 ---
st.markdown("<hr>", unsafe_allow_html=True)
st.header("💰 3. 은행 신용 및 단기 자금 시장 (기관 자금 흐름)")
render_detailed_indicator('RRP', df, selected_days)
render_detailed_indicator('MMF', df, selected_days)
render_detailed_indicator('TOTLL', df, selected_days)
render_detailed_indicator('SOFR_IORB_Spread', df, selected_days)
render_detailed_indicator('Emergency_Loans', df, selected_days)

# --- 4. 글로벌 매크로 지표 ---
st.markdown("<hr>", unsafe_allow_html=True)
st.header("🌍 4. 인플레이션 및 글로벌 매크로")
render_detailed_indicator('DXY', df, selected_days)
render_detailed_indicator('T10YIE', df, selected_days)

# --- 5. AI 리포트 ---
st.markdown("<hr>", unsafe_allow_html=True)
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
