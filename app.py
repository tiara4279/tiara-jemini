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
sofr_val = get_safe_val(latest, 'SOFR')
sofr_spread = get_safe_val(latest, 'SOFR_IORB_Spread')
emerg_loans = get_safe_val(latest, 'Emergency_Loans')

with col_b1:
    # H.8 대출 증감폭을 정확히 전주 데이터와 비교하여 계산
    totll_chg = totll_val - get_safe_val(prev_week, 'TOTLL')
    st.metric("H.8 상업은행 총대출", f"{totll_val:,.0f}억 달러", f"{totll_chg:,.0f}억 달러 (1W)")
    if totll_chg > 0: 
        st.caption("🟢 **[신용 팽창]** 실물 경제로 자금 공급 원활")
    elif totll_chg < 0: 
        st.caption("🔴 **[신용 축소]** 은행 대출 태도 강화 (침체 우려)")
    else: 
        st.caption("➖ **[대출 정체]** 전주 대비 상업은행 대출 규모 유지")

with col_b2:
    # SOFR 데이터가 안 들어왔을 경우 방어 코드 및 실제 SOFR 금리 병기
    prev_sofr_spread = get_safe_val(prev_week, 'SOFR_IORB_Spread')
    if sofr_val == 0.0:
        st.metric("SOFR - IORB 스프레드", "데이터 지연")
        st.caption("➖ API 업데이트 대기중")
    else:
        st.metric("SOFR - IORB 스프레드", f"{sofr_spread:.3f}%", f"{sofr_spread - prev_sofr_spread:.3f}% (1W)")
        if sofr_spread > 0.05: 
            st.caption(f"🔴 **[경고]** 단기 자금시장 달러 부족 (SOFR: {sofr_val:.2f}%)")
        elif sofr_spread > 0: 
            st.caption(f"⚠️ **[주의]** 레포 시장 유동성 타이트 (SOFR: {sofr_val:.2f}%)")
        else: 
            st.caption(f"🟢 **[안정]** 단기 자금 조달 원활 (SOFR: {sofr_val:.2f}%)")

with col_b3:
    # 긴급 대출 증감폭 계산
    emerg_chg = emerg_loans - get_safe_val(prev_week, 'Emergency_Loans')
    st.metric("연준 H.4.1 긴급대출 (할인창구+BTFP)", f"{emerg_loans:,.0f}억 달러", f"{emerg_chg:,.0f}억 달러 (1W)")
    if emerg_loans > 500: 
        st.caption("🔴 **[위험]** 은행권 뱅크런/스트레스 징후 발생")
    elif emerg_loans > 0:
        st.caption("⚠️ **[주의]** 일부 은행권 연준 긴급 차입 발생")
    else: 
        st.caption("🟢 **[매우 안정]** 위기 없음 (긴급 대출 0)")

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
    yield_curve, hy_spread = get_safe_val(latest, '10Y_2Y'), get_safe_val(latest, 'HY_Spread')
    liq_change = get_safe_val(latest, 'Net_Liquidity') - get_safe_val(prev, 'Net_Liquidity')
    
    sofr_spread = get_safe_val(latest, 'SOFR_IORB_Spread')
    totll_val = get_safe_val(latest, 'TOTLL')
    totll_chg = totll_val - get_safe_val(prev, 'TOTLL')
    dxy = get_safe_val(latest, 'DXY')
    bei = get_safe_val(latest, 'T10YIE')
    emerg_loans = get_safe_val(latest, 'Emergency_Loans')
    
    report.append("### 📌 시장 심리 및 시스템 리스크")
    if vix > 30: 
        report.append(f"- **[위험 심리]** 현재 VIX 지수가 {vix:.2f}를 기록하며 30을 초과했습니다. 이는 옵션 시장 참여자들이 향후 극심한 변동성을 예상하고 있음을 의미하며, 시장에 공포 심리가 팽배한 상태입니다.")
    elif vix < 20: 
        report.append(f"- **[안정]** 현재 VIX 지수는 {vix:.2f}로 20 미만을 기록하고 있습니다. 시장 참여자들의 불안감이 낮고 비교적 평온한 탐욕/안정 구간에 머물러 있습니다.")
    else: 
        report.append(f"- **[중립]** 현재 VIX 지수는 {vix:.2f}로 20~30 사이의 일반적인 경계감을 유지하는 평균적인 구간입니다.")
    
    system_msg = f"- **[시스템 진단]** 채권 변동성(MOVE)이 {move:.2f}, 연준 긴급 대출 잔액이 {emerg_loans:,.0f}억 달러를 기록 중입니다. "
    if emerg_loans > 500 or move > 140:
        system_msg += "평균치를 상회하는 자금 조달 및 채권 시장의 스트레스 징후가 관찰되므로 은행권 시스템 위험에 대한 주의가 필요합니다."
    else:
        system_msg += "긴급 대출이 거의 없고 지표가 안정적이므로, 현재 시장의 시스템적 위험 수위는 매우 안전한 범위 내에서 통제되고 있습니다."
    report.append(system_msg)
        
    report.append("\n### 📌 은행 신용 및 달러 펀딩 환경 (새로운 지표)")
    if sofr_spread > 0.05:
        report.append(f"- **[달러 접근성 악화]** 단기 자금 시장의 핵심인 SOFR-IORB 스프레드가 {sofr_spread:.3f}%로 크게 확대되었습니다. 이는 단기 자금시장에서 달러 구하기가 어려워지는 '발작 조짐'을 시사합니다.")
    else:
        report.append(f"- **[달러 접근성 양호]** SOFR-IORB 스프레드가 {sofr_spread:.3f}% 수준으로 0% 근방에서 안정적입니다. 단기 레포 시장에서 글로벌 기관들의 달러 유동성 융통이 무리 없이 원활하게 이루어지고 있음을 의미합니다.")
        
    if totll_chg < 0:
        report.append(f"- **[신용 축소 우려]** H.8 상업은행 총대출이 전주 대비 {abs(totll_chg):,.0f}억 달러 감소했습니다. 은행들의 대출 태도가 깐깐해지며 실물 경제로의 자금 공급 둔화(Credit Crunch)가 우려됩니다.")
    elif totll_chg > 0:
        report.append(f"- **[신용 팽창]** H.8 상업은행 총대출이 전주 대비 {totll_chg:,.0f}억 달러 증가했습니다. 상업은행의 대출 여력이 유지되며 실물 경제로 신용 창출이 긍정적으로 이어지고 있습니다.")
    else:
        report.append(f"- **[신용 유지]** H.8 상업은행 총대출 규모가 전주 수준을 유지하며 급격한 신용 위축 없이 안정적인 상태를 보이고 있습니다.")

    report.append("\n### 📌 매크로 경제 및 인플레이션")
    if yield_curve < 0: 
        report.append(f"- **[침체 선행]** 10년-2년 국채 금리차가 {yield_curve:.2f}%로 역전 상태가 지속되고 있습니다. 이는 역사적으로 향후 경기 침체(Recession) 압박을 예고하는 강력한 선행 지표로 작용합니다.")
    else:
        report.append(f"- **[안정적 금리차]** 10년-2년 국채 금리차가 {yield_curve:.2f}%로 정상적인 우상향 곡선을 보이며 경기 침체 우려가 완화된 상태입니다.")
        
    if dxy > 105:
        report.append(f"- **[글로벌 유동성 부담]** 달러 인덱스(DXY)가 {dxy:.2f}로 105를 상회하는 강세를 보이고 있습니다. 이는 미국 외 국가(특히 신흥국)의 자본 이탈 및 유동성 축소 압박을 키우는 요인입니다.")
    elif dxy < 100:
        report.append(f"- **[글로벌 유동성 우호적]** 달러 인덱스(DXY)가 {dxy:.2f}로 100 이하의 약세 흐름을 보이고 있습니다. 이는 글로벌 위험 자산과 신흥국 증시에 긍정적인 촉매가 됩니다.")
    else:
        report.append(f"- **[달러화 중립]** 달러 인덱스(DXY)가 {dxy:.2f}로 박스권 내 움직임을 보이며 글로벌 유동성에 미치는 환율 영향은 중립적입니다.")
        
    if bei > 2.5:
        report.append(f"- **[물가 고착화 우려]** 10년물 기대인플레이션(BEI)이 {bei:.2f}%를 상회하고 있습니다. 물가가 쉽게 잡히지 않을 것이라는 시장의 우려가 반영되어 연준의 비둘기파적 스탠스(금리 인하)를 강하게 제약할 수 있습니다.")
    elif bei < 2.0:
        report.append(f"- **[디스인플레이션]** 10년물 기대인플레이션(BEI)이 {bei:.2f}%를 밑돌고 있습니다. 오히려 경기 둔화 및 디스인플레이션 우려가 커지는 국면입니다.")
    else:
        report.append(f"- **[물가 안정화]** 10년물 기대인플레이션(BEI)이 {bei:.2f}%로 연준의 장기 목표치(2%) 근방에서 부합하는 안정적인 물가 궤적을 보이고 있습니다.")

    report.append("\n### 📌 종합 자산 배분 전략")
    if (yield_curve < 0 and hy_spread > 5.0) or sofr_spread > 0.1:
        report.append(f"👉 **[보수적 대응 권고]** 장단기 금리 역전({yield_curve:.2f}%)과 함께 하이일드 스프레드({hy_spread:.2f}%) 상승, 혹은 달러 펀딩 스트레스({sofr_spread:.3f}%)가 복합적으로 나타나고 있습니다. 시장 시스템 리스크가 커지고 있으므로 현금 확보 및 보수적 포트폴리오(채권 우위) 운영을 강력히 권장합니다.")
    elif liq_change > 0 and dxy < 105 and sofr_spread <= 0:
        report.append(f"👉 **[위험 자산 선호 유지]** 순유동성(Net Liquidity)이 증가(+{liq_change:,.0f}억 달러)하고 달러 가치({dxy:.2f})가 안정적이며 펀딩 시장도 원활합니다. 주식 등 위험 자산의 우상향 랠리를 뒷받침할 훌륭한 매크로 환경이 조성되어 있으므로 비중 유지를 권고합니다.")
    else:
        report.append("👉 **[관망 및 퀄리티 주식 집중]** 거시 지표들의 방향성이 혼재되어 있어 단기적으로 뚜렷한 추세를 예단하기 어렵습니다. 지수 전반의 베타(Beta) 랠리보다는 재무 건전성이 뛰어나고 대출 의존도가 낮은 우량 기업(Quality) 위주로 선별적인 접근이 필요합니다.")

    return "\n".join(report)

report_text = generate_report(latest, prev_week)
st.info(report_text)

st.caption(f"마지막 데이터 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (기준일자: {df.index[-1].strftime('%Y-%m-%d')})")
