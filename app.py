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

# --- 커스텀 CSS 및 자동 번역 방지 메타 태그 ---
st.markdown("""
<meta name="google" content="notranslate">
<meta name="robots" content="notranslate">
<style>
/* st.metric 의 라벨(제목) 폰트 크기 및 굵기 변경 */
[data-testid="stMetricLabel"] > div {
    font-size: 20px !important;
    font-weight: 800 !important;
}
</style>
""", unsafe_allow_html=True)

st.title("🌐 시장 경제 지표 대시보드")
st.markdown("시장의 위험 심리, 경기 사이클, 그리고 핵심 유동성 흐름을 매일 추적합니다.")

# --- 데이터 로드 함수 (결측치 및 에러 처리 강화) ---
@st.cache_data(ttl=3600*12) # 12시간마다 갱신
def load_data():
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365*3) # 과거 3년 데이터
    
    # 1. FRED 데이터 가져오기 (기존 + 신규 지표 추가)
    fred_series = {
        'VIX': 'VIXCLS',                  
        'HY_Spread': 'BAMLH0A0HYM2',      
        'FSI': 'STLFSI4',                 
        '10Y_2Y': 'T10Y2Y',               
        'Fed_BS': 'WALCL',                
        'Reserves': 'WRESBAL',            
        'RRP': 'RRPONTSYD',               
        'TGA': 'WTREGEN',                 
        'MMF': 'MMMFFAQ027S',             
        # [신규 추가 지표]
        'TOTLL': 'TOTLL',                 # H.8 상업은행 총대출 (Billions)
        'SOFR': 'SOFR',                   # SOFR 금리 (%)
        'IORB': 'IORB',                   # 지급준비금 이리 (%)
        'T10YIE': 'T10YIE',               # 10년물 기대인플레이션(BEI) (%)
        'Discount_Window': 'WLCFLPCL',    # H.4.1 연준 할인창구 대출 (Millions)
        'BTFP': 'H41RESPALBFRB'           # H.4.1 BTFP 긴급대출 (Millions)
    }
    
    df_fred = pd.DataFrame()
    for name, series_id in fred_series.items():
        try:
            data = web.DataReader(series_id, 'fred', start, end)
            df_fred[name] = data[series_id]
        except Exception as e:
            pass 

    # --- 단위 환산 (금액 데이터는 모두 '억 달러(100 Millions)'로 통일) ---
    if 'Fed_BS' in df_fred.columns: df_fred['Fed_BS'] = df_fred['Fed_BS'] / 100
    if 'Reserves' in df_fred.columns: df_fred['Reserves'] = df_fred['Reserves'] / 100
    if 'TGA' in df_fred.columns: df_fred['TGA'] = df_fred['TGA'] / 100
    if 'MMF' in df_fred.columns: df_fred['MMF'] = df_fred['MMF'] / 100
    if 'RRP' in df_fred.columns: df_fred['RRP'] = df_fred['RRP'] * 10
    
    # 신규 지표 단위 환산
    if 'TOTLL' in df_fred.columns: df_fred['TOTLL'] = df_fred['TOTLL'] * 10 # Billions -> 억 달러
    if 'Discount_Window' in df_fred.columns: df_fred['Discount_Window'] = df_fred['Discount_Window'] / 100
    if 'BTFP' in df_fred.columns: df_fred['BTFP'] = df_fred['BTFP'] / 100

    # 2. Yahoo Finance 데이터 가져오기 (DXY 달러 인덱스 추가)
    tickers = ['^GSPC', '^MOVE', 'DX-Y.NYB']
    df_yf = pd.DataFrame()
    try:
        yf_data = yf.download(tickers, start=start, end=end, progress=False)
        if 'Close' in yf_data.columns:
            df_yf = yf_data['Close']
        else:
            df_yf = yf_data
        
        df_yf = df_yf.rename(columns={'^GSPC': 'SP500', '^MOVE': 'MOVE', 'DX-Y.NYB': 'DXY'})
    except Exception as e:
        pass

    # 3. 데이터 병합 및 결측치 방어
    df_merged = pd.concat([df_fred, df_yf], axis=1)
    df_merged = df_merged.ffill().bfill()
    df_merged = df_merged.fillna(0)
    
    # 4. 파생 변수 계산
    if all(col in df_merged.columns for col in ['Fed_BS', 'RRP', 'TGA']):
        df_merged['Net_Liquidity'] = df_merged['Fed_BS'] - df_merged['RRP'] - df_merged['TGA']
    else:
        df_merged['Net_Liquidity'] = 0
        
    # SOFR - IORB 스프레드 계산
    if all(col in df_merged.columns for col in ['SOFR', 'IORB']):
        df_merged['SOFR_IORB_Spread'] = df_merged['SOFR'] - df_merged['IORB']
    else:
        df_merged['SOFR_IORB_Spread'] = 0.0
        
    # 연준 H.4.1 긴급 대출 총합
    if all(col in df_merged.columns for col in ['Discount_Window', 'BTFP']):
        df_merged['Emergency_Loans'] = df_merged['Discount_Window'] + df_merged['BTFP']
    else:
        df_merged['Emergency_Loans'] = 0.0
    
    # 주간 증감폭
    if 'Reserves' in df_merged.columns: df_merged['Reserves_1W_Chg'] = df_merged['Reserves'].diff(5).fillna(0)
    else: df_merged['Reserves_1W_Chg'] = 0
    if 'TGA' in df_merged.columns: df_merged['TGA_1W_Chg'] = df_merged['TGA'].diff(5).fillna(0)
    else: df_merged['TGA_1W_Chg'] = 0
    if 'MMF' in df_merged.columns: df_merged['MMF_1W_Chg'] = df_merged['MMF'].diff(5).fillna(0)
    else: df_merged['MMF_1W_Chg'] = 0
    if 'TOTLL' in df_merged.columns: df_merged['TOTLL_1W_Chg'] = df_merged['TOTLL'].diff(5).fillna(0)
    else: df_merged['TOTLL_1W_Chg'] = 0
    
    return df_merged

# 데이터 로딩
with st.spinner('데이터를 분석 중입니다... (FRED & Yahoo Finance)'):
    df = load_data()

if df.empty or len(df) < 6:
    st.error("🚨 API 서버에서 데이터를 가져오는 데 실패했습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

latest = df.iloc[-1]
prev_week = df.iloc[-6] 

def get_safe_val(row, col_name):
    return row[col_name] if col_name in row.index else 0.0

# --- 1. 시장 리스크 경고 시스템 ---
st.header("🚨 1. 시장 리스크 경고 시스템")

col1, col2, col3, col4, col5 = st.columns(5)

def check_status(value, threshold, condition, danger_msg, safe_msg):
    if value == 0.0: return "데이터 없음"
    if condition == 'greater' and value > threshold:
        return f"🔴 {danger_msg}"
    elif condition == 'less' and value < threshold:
        return f"🔴 {danger_msg}"
    else:
        return f"🟢 {safe_msg}"

vix_val = get_safe_val(latest, 'VIX')
move_val = get_safe_val(latest, 'MOVE')
yield_val = get_safe_val(latest, '10Y_2Y')
fsi_val = get_safe_val(latest, 'FSI')
hy_val = get_safe_val(latest, 'HY_Spread')

with col1:
    st.metric(label="VIX (옵션 변동성)", value=f"{vix_val:.2f}", delta=f"{vix_val - get_safe_val(prev_week, 'VIX'):.2f} (1W)")
    st.caption(f"상태: {check_status(vix_val, 30, 'greater', '시장 공포 극대화', '안정적')}")
with col2:
    st.metric(label="MOVE Index (채권 VIX)", value=f"{move_val:.2f}", delta=f"{move_val - get_safe_val(prev_week, 'MOVE'):.2f} (1W)")
    st.caption(f"상태: {check_status(move_val, 140, 'greater', '채권/은행 시스템 스트레스', '안정적')}")
with col3:
    st.metric(label="10Y-2Y 금리차", value=f"{yield_val:.2f}%", delta=f"{yield_val - get_safe_val(prev_week, '10Y_2Y'):.2f}% (1W)")
    st.caption(f"상태: {check_status(yield_val, 0, 'less', '장단기 금리 역전 (침체 선행)', '정상')}")
with col4:
    st.metric(label="금융 스트레스 지수 (FSI)", value=f"{fsi_val:.2f}", delta=f"{fsi_val - get_safe_val(prev_week, 'FSI'):.2f} (1W)")
    st.caption(f"상태: {check_status(fsi_val, 0, 'greater', '금융 시스템 스트레스 발생', '유동성 원활')}")
with col5:
    st.metric(label="하이일드 스프레드", value=f"{hy_val:.2f}%", delta=f"{hy_val - get_safe_val(prev_week, 'HY_Spread'):.2f}% (1W)")
    st.caption(f"상태: {check_status(hy_val, 5.0, 'greater', '신용 경색 경보', '안정적')}")

st.divider()

# --- 2. 핵심 유동성 흐름 분석 ---
st.header("🌊 2. 미국 유동성 흐름 (핵심)")

if 'Net_Liquidity' in df.columns and 'SP500' in df.columns:
    fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
    fig_liq.add_trace(plotly_go.Scatter(x=df.index, y=df['Net_Liquidity'], name="US Net Liquidity (억 달러)", line=dict(color='blue')), secondary_y=False)
    fig_liq.add_trace(plotly_go.Scatter(x=df.index, y=df['SP500'], name="S&P 500", line=dict(color='red', width=1)), secondary_y=True)
    fig_liq.update_layout(title_text="Net Liquidity vs S&P 500 추이", height=600, hovermode="x unified")
    fig_liq.update_xaxes(rangeslider_visible=False, rangeselector=dict(buttons=list([
        dict(count=1, label="1개월", step="month", stepmode="backward"), dict(count=3, label="3개월", step="month", stepmode="backward"),
        dict(count=6, label="6개월", step="month", stepmode="backward"), dict(count=1, label="1년", step="year", stepmode="backward"),
        dict(step="all", label="전체")
    ])))
    st.plotly_chart(fig_liq, use_container_width=True)

st.subheader("📊 주요 유동성 창구 주간 증감")
col_l1, col_l2, col_l3, col_l4 = st.columns(4)

fed_bs_val = get_safe_val(latest, 'Fed_BS')
reserves_val = get_safe_val(latest, 'Reserves')
rrp_val = get_safe_val(latest, 'RRP')
tga_val = get_safe_val(latest, 'TGA')

with col_l1:
    fed_chg = fed_bs_val - get_safe_val(prev_week, 'Fed_BS')
    st.metric("연준 대차대조표", f"{fed_bs_val:,.0f}억 달러", f"{fed_chg:,.0f}억 달러")
    if fed_chg > 0: st.caption("🟢 **[유동성 팽창]** 시중에 자금 공급")
    elif fed_chg < 0: st.caption("🔴 **[QT 진행]** 연준 자산 축소중")
with col_l2:
    res_chg = get_safe_val(latest, 'Reserves_1W_Chg')
    st.metric("지급준비금 (Reserves)", f"{reserves_val:,.0f}억 달러", f"{res_chg:,.0f}억 달러")
    if res_chg > 0: st.caption("🟢 **[신용 확대]** 은행 대출/투자 여력 증가")
    elif res_chg < 0: st.caption("🔴 **[신용 축소]** 은행 자금 여력 감소")
with col_l3:
    rrp_chg = rrp_val - get_safe_val(prev_week, 'RRP')
    st.metric("역레포 (RRP)", f"{rrp_val:,.0f}억 달러", f"{rrp_chg:,.0f}억 달러")
    if rrp_val < 1000 and rrp_val > 0.0: st.caption("⚠️ **[바닥 근접]** 완충재 고갈 임박")
    elif rrp_chg > 0: st.caption("🔴 **[위험 회피]** 시장 자금 연준으로 회귀")
    else: st.caption("🟢 **[위험 선호]** 대기 자금 위험자산 이동중")
with col_l4:
    tga_chg = get_safe_val(latest, 'TGA_1W_Chg')
    st.metric("TGA (재무부 계좌)", f"{tga_val:,.0f}억 달러", f"{tga_chg:,.0f}억 달러")
    if tga_chg > 0: st.caption("🔴 **[자금 흡수]** 국채 발행으로 유동성 흡수")
    elif tga_chg < 0: st.caption("🟢 **[재정 지출]** 시중에 정부 자금 펌핑중")

st.divider()

# --- 3. 자금 이동 (MMF vs RRP) ---
st.header("🔄 3. 기관 자금 이동 (MMF vs 역레포)")
if 'MMF' in df.columns and 'RRP' in df.columns:
    fig_flow = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=("MMF 총 잔액 추이", "역레포(RRP) 잔액 추이"))
    fig_flow.add_trace(plotly_go.Scatter(x=df.index, y=df['MMF'], name="MMF", fill='tozeroy', line=dict(color='purple')), row=1, col=1)
    fig_flow.add_trace(plotly_go.Scatter(x=df.index, y=df['RRP'], name="RRP", fill='tozeroy', line=dict(color='orange')), row=2, col=1)
    fig_flow.update_layout(height=500, hovermode="x unified", showlegend=False)
    fig_flow.update_xaxes(rangeslider_visible=False, row=1, col=1)
    fig_flow.update_xaxes(rangeslider_visible=False, row=2, col=1)
    st.plotly_chart(fig_flow, use_container_width=True)

st.divider()

# --- 4. [신규] 은행 신용 & 단기 자금시장 (H.8 & SOFR) ---
st.header("🏦 4. 신용 창출 및 단기 자금시장 (H.8 & SOFR)")
st.markdown("상업은행의 실제 신용 창출 여부와 단기 달러 자금 시장의 발작(스트레스) 여부를 진단합니다.")

col_b1, col_b2, col_b3 = st.columns(3)

totll_val = get_safe_val(latest, 'TOTLL')
totll_chg = get_safe_val(latest, 'TOTLL_1W_Chg')
sofr_spread = get_safe_val(latest, 'SOFR_IORB_Spread')
emerg_loans = get_safe_val(latest, 'Emergency_Loans')

with col_b1:
    st.metric("H.8 상업은행 총대출", f"{totll_val:,.0f}억 달러", f"{totll_chg:,.0f}억 달러 (1W)")
    if totll_chg > 0: st.caption("🟢 **[신용 팽창]** 실물 경제로 자금 공급 원활")
    elif totll_chg < 0: st.caption("🔴 **[신용 축소]** 은행 대출 태도 강화 (침체 우려)")

with col_b2:
    st.metric("SOFR - IORB 스프레드", f"{sofr_spread:.3f}%", f"{sofr_spread - get_safe_val(prev_week, 'SOFR_IORB_Spread'):.3f}% (1W)")
    if sofr_spread > 0.05: st.caption("🔴 **[경고]** 단기 자금시장 달러 부족 (발작 조짐)")
    elif sofr_spread > 0: st.caption("⚠️ **[주의]** 레포 시장 유동성 타이트")
    else: st.caption("🟢 **[안정]** 단기 자금 조달 원활 (SOFR < IORB)")

with col_b3:
    st.metric("연준 H.4.1 긴급대출 (할인창구+BTFP)", f"{emerg_loans:,.0f}억 달러", f"{emerg_loans - get_safe_val(prev_week, 'Emergency_Loans'):,.0f}억 달러 (1W)")
    if emerg_loans > 500: st.caption("🔴 **[위험]** 은행권 뱅크런/스트레스 징후 발생")
    else: st.caption("🟢 **[안정]** 은행권 연준 긴급 차입 미미함")

st.divider()

# --- 5. [신규] 글로벌 달러 및 인플레이션 (DXY & BEI) ---
st.header("🌍 5. 글로벌 유동성 및 인플레이션 (DXY & BEI)")
col_m1, col_m2 = st.columns(2)

dxy_val = get_safe_val(latest, 'DXY')
bei_val = get_safe_val(latest, 'T10YIE')

with col_m1:
    st.metric("DXY (달러 인덱스)", f"{dxy_val:.2f}", f"{dxy_val - get_safe_val(prev_week, 'DXY'):.2f} (1W)")
    if dxy_val > 105: st.caption("🔴 **[달러 강세]** 글로벌 유동성 흡수 및 EM 부담")
    elif dxy_val < 100: st.caption("🟢 **[달러 약세]** 위험자산 및 신흥국 증시 우호적 환경")
    else: st.caption("➖ **[중립]** 박스권 안정세")

with col_m2:
    st.metric("10Y BEI (기대인플레이션)", f"{bei_val:.2f}%", f"{bei_val - get_safe_val(prev_week, 'T10YIE'):.2f}% (1W)")
    if bei_val > 2.5: st.caption("🔴 **[물가 불안]** 인플레이션 고착화 우려 (금리 인하 지연)")
    elif bei_val < 2.0: st.caption("⚠️ **[디스인플레/침체]** 경기 둔화 우려 증가")
    else: st.caption("🟢 **[골디락스]** 연준 목표치(2%) 부합")

st.divider()

# --- 6. 자동 매크로 시황 리포트 생성 (신규 지표 통합) ---
st.header("📝 6. AI 기반 자동 매크로 종합 시황 리포트")

def generate_report(latest, prev):
    report = []
    
    vix, move, fsi = get_safe_val(latest, 'VIX'), get_safe_val(latest, 'MOVE'), get_safe_val(latest, 'FSI')
    yield_curve, hy_spread, prev_hy = get_safe_val(latest, '10Y_2Y'), get_safe_val(latest, 'HY_Spread'), get_safe_val(prev, 'HY_Spread')
    liq_change = get_safe_val(latest, 'Net_Liquidity') - get_safe_val(prev, 'Net_Liquidity')
    
    # 신규 지표 추출
    sofr_spread = get_safe_val(latest, 'SOFR_IORB_Spread')
    totll_chg = get_safe_val(latest, 'TOTLL_1W_Chg')
    dxy = get_safe_val(latest, 'DXY')
    bei = get_safe_val(latest, 'T10YIE')
    emerg_loans = get_safe_val(latest, 'Emergency_Loans')
    
    report.append("### 📌 시장 심리 및 시스템 리스크")
    if vix > 30: report.append("- **[위험 심리]** VIX가 30을 초과하여 시장 공포가 팽배합니다.")
    else: report.append("- **[위험 심리]** VIX 지수는 정상 범위 내에서 비교적 안정적인 투자 심리를 보입니다.")
    
    if emerg_loans > 500 or move > 140:
        report.append("- **[시스템 경고]** 연준 긴급 차입액이 높거나 MOVE 지수가 급등했습니다. 은행권 스트레스를 주의하세요.")
        
    report.append("\n### 📌 은행 신용 및 달러 펀딩 환경 (새로운 지표)")
    if sofr_spread > 0.05:
        report.append("- **[달러 접근성 악화]** SOFR 금리가 IORB를 상회하며 단기 자금시장에서 달러 구하기가 어려워지는 '발작 조짐'이 관찰됩니다.")
    else:
        report.append("- **[달러 접근성 양호]** SOFR-IORB 스프레드가 안정적이며 단기 레포 시장의 달러 유동성은 원활합니다.")
        
    if totll_chg < 0:
        report.append("- **[신용 축소 우려]** H.8 상업은행 대출이 전주 대비 감소했습니다. 실물 경제로의 자금 공급이 둔화(Credit Crunch)될 우려가 있습니다.")
    else:
        report.append("- **[신용 팽창]** 상업은행의 대출 여력이 유지되며 실물 경제로 신용 창출이 이어지고 있습니다.")

    report.append("\n### 📌 매크로 경제 및 인플레이션")
    if yield_curve < 0: report.append("- **[침체 선행]** 장단기 금리 역전이 지속되고 있어 향후 경기 침체 압박이 존재합니다.")
    
    if dxy > 105:
        report.append("- **[글로벌 유동성 부담]** 달러 강세(DXY > 105)로 인해 미국 외 국가(특히 신흥국)의 자본 이탈 및 유동성 축소 압박이 커지고 있습니다.")
    elif dxy < 100:
        report.append("- **[글로벌 유동성 우호적]** 달러 약세 흐름은 글로벌 위험 자산에 긍정적인 촉매가 됩니다.")
        
    if bei > 2.5:
        report.append("- **[물가 고착화]** 기대인플레이션(BEI)이 2.5%를 상회하여 연준의 비둘기파적 스탠스(금리 인하)를 제약할 가능성이 큽니다.")

    report.append("\n### 📌 종합 자산 배분 전략")
    if (yield_curve < 0 and hy_spread > 5.0) or sofr_spread > 0.1:
        report.append("👉 **[보수적 대응 권고]** 경기 침체 시그널과 달러 펀딩 스트레스가 동시에 겹쳤습니다. 현금 확보 및 보수적 포트폴리오 운영을 권장합니다.")
    elif liq_change > 0 and dxy < 105 and sofr_spread <= 0:
        report.append("👉 **[위험 자산 선호 유지]** 미국 국내외 달러 유동성이 풍부하게 공급되고 있습니다. 주식 등 위험 자산의 우상향 랠리가 지속될 환경입니다.")
    else:
        report.append("👉 **[관망 및 퀄리티 주식 집중]** 거시 지표가 혼재되어 있습니다. 지수 전반의 랠리보다는 재무 건전성이 뛰어나고 대출 의존도가 낮은 우량 기업 위주로 접근하세요.")

    return "\n".join(report)

report_text = generate_report(latest, prev_week)
st.info(report_text)

st.caption(f"마지막 데이터 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (기준일자: {df.index[-1].strftime('%Y-%m-%d')})")
