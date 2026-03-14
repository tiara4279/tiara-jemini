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
st.title("🌐 매크로 & 유동성 분석 대시보드")
st.markdown("시장의 위험 심리, 경기 사이클, 그리고 핵심 유동성 흐름을 매일 추적합니다.")

# --- 데이터 로드 함수 (결측치 및 에러 처리 강화) ---
@st.cache_data(ttl=3600*12) # 12시간마다 갱신
def load_data():
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365*3) # 과거 3년 데이터
    
    # 1. FRED 데이터 가져오기
    fred_series = {
        'VIX': 'VIXCLS',                  
        'HY_Spread': 'BAMLH0A0HYM2',      
        'FSI': 'STLFSI4',                 
        '10Y_2Y': 'T10Y2Y',               
        'Fed_BS': 'WALCL',                
        'Reserves': 'WRESBAL',            
        'RRP': 'RRPONTSYD',               
        'TGA': 'WTREGEN',                 
        'MMF': 'MMMFFAQ027S'              
    }
    
    df_fred = pd.DataFrame()
    for name, series_id in fred_series.items():
        try:
            # FRED 데이터를 시리즈 형태로 가져와서 바로 할당
            data = web.DataReader(series_id, 'fred', start, end)
            df_fred[name] = data[series_id]
        except Exception as e:
            pass # 일부 데이터 로드 실패 시 무시하고 진행

    # 단위 통일 (Billions -> Millions 방지, 모두 Billions 단위로 맞춤)
    if 'Fed_BS' in df_fred.columns: df_fred['Fed_BS'] = df_fred['Fed_BS'] / 1000
    if 'MMF' in df_fred.columns: df_fred['MMF'] = df_fred['MMF'] / 1000

    # 2. Yahoo Finance 데이터 가져오기
    tickers = ['^GSPC', '^MOVE']
    df_yf = pd.DataFrame()
    try:
        yf_data = yf.download(tickers, start=start, end=end, progress=False)
        # yfinance 최신 버전에 따른 MultiIndex 대응
        if 'Close' in yf_data.columns:
            df_yf = yf_data['Close']
        else:
            df_yf = yf_data
        
        df_yf = df_yf.rename(columns={'^GSPC': 'SP500', '^MOVE': 'MOVE'})
    except Exception as e:
        pass

    # 3. 데이터 병합 및 결측치(NaN) 강력 방어
    df_merged = pd.concat([df_fred, df_yf], axis=1)
    
    # dropna() 대신 이전 값으로 채우기(ffill) -> 그래도 없으면 뒤의 값으로 채우기(bfill)
    df_merged = df_merged.ffill().bfill()
    
    # 마지막까지 남는 빈칸은 0으로 채워서 에러 방지
    df_merged = df_merged.fillna(0)
    
    # 4. 파생 변수 계산
    # Net Liquidity = Fed BS - RRP - TGA
    if all(col in df_merged.columns for col in ['Fed_BS', 'RRP', 'TGA']):
        df_merged['Net_Liquidity'] = df_merged['Fed_BS'] - df_merged['RRP'] - df_merged['TGA']
    else:
        df_merged['Net_Liquidity'] = 0
    
    # 주간 증감폭 계산 (안전을 위해 빈칸은 0처리)
    if 'Reserves' in df_merged.columns: 
        df_merged['Reserves_1W_Chg'] = df_merged['Reserves'].diff(5).fillna(0)
    else: 
        df_merged['Reserves_1W_Chg'] = 0
        
    if 'TGA' in df_merged.columns: 
        df_merged['TGA_1W_Chg'] = df_merged['TGA'].diff(5).fillna(0)
    else: 
        df_merged['TGA_1W_Chg'] = 0
        
    if 'MMF' in df_merged.columns: 
        df_merged['MMF_1W_Chg'] = df_merged['MMF'].diff(5).fillna(0)
    else: 
        df_merged['MMF_1W_Chg'] = 0
    
    return df_merged

# 데이터 로딩
with st.spinner('데이터를 분석 중입니다... (FRED & Yahoo Finance)'):
    df = load_data()

# 데이터 로딩에 완전 실패했거나 너무 짧은 경우 예외 처리
if df.empty or len(df) < 6:
    st.error("🚨 API 서버에서 데이터를 가져오는 데 실패했습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

# 최신 데이터 추출
latest = df.iloc[-1]
prev_week = df.iloc[-6] # 1주일 전 (약 5영업일)

# 안전한 값 추출 헬퍼 함수
def get_safe_val(row, col_name):
    return row[col_name] if col_name in row.index else 0.0

# --- 1. 시장 리스크 경고 시스템 (최상단) ---
st.header("🚨 1. 시장 리스크 경고 시스템")

col1, col2, col3, col4 = st.columns(4)

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

with col1:
    vix_status = check_status(vix_val, 30, 'greater', "시장 공포 극대화", "안정적")
    st.metric(label="VIX (옵션 변동성)", value=f"{vix_val:.2f}", delta=f"{vix_val - get_safe_val(prev_week, 'VIX'):.2f} (1W)")
    st.caption(f"상태: {vix_status}")

with col2:
    move_status = check_status(move_val, 140, 'greater', "채권/은행 시스템 스트레스", "안정적")
    st.metric(label="MOVE Index (채권 VIX)", value=f"{move_val:.2f}", delta=f"{move_val - get_safe_val(prev_week, 'MOVE'):.2f} (1W)")
    st.caption(f"상태: {move_status}")

with col3:
    yield_status = check_status(yield_val, 0, 'less', "장단기 금리 역전 (침체 선행)", "정상")
    st.metric(label="10Y-2Y 금리차", value=f"{yield_val:.2f}%", delta=f"{yield_val - get_safe_val(prev_week, '10Y_2Y'):.2f}% (1W)")
    st.caption(f"상태: {yield_status}")

with col4:
    fsi_status = check_status(fsi_val, 0, 'greater', "금융 시스템 스트레스 발생", "유동성 원활")
    st.metric(label="금융 스트레스 지수 (FSI)", value=f"{fsi_val:.2f}", delta=f"{fsi_val - get_safe_val(prev_week, 'FSI'):.2f} (1W)")
    st.caption(f"상태: {fsi_status}")

st.divider()

# --- 2. 핵심 유동성 흐름 분석 ---
st.header("🌊 2. 미국 유동성 흐름 (핵심)")

st.markdown("""
**공식:** `Net Liquidity = 연준 대차대조표(Fed BS) - 역레포(RRP) - 미 재무부 계좌(TGA)`  
*이 지표는 S&P 500 등 주식 시장과 강한 양의 상관관계를 가집니다.*
""")

if 'Net_Liquidity' in df.columns and 'SP500' in df.columns:
    fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
    fig_liq.add_trace(
        plotly_go.Scatter(x=df.index, y=df['Net_Liquidity'], name="US Net Liquidity (Billions $)", line=dict(color='blue')),
        secondary_y=False,
    )
    fig_liq.add_trace(
        plotly_go.Scatter(x=df.index, y=df['SP500'], name="S&P 500", line=dict(color='red', width=1)),
        secondary_y=True,
    )
    fig_liq.update_layout(title_text="Net Liquidity vs S&P 500 추이", height=500, hovermode="x unified")
    fig_liq.update_yaxes(title_text="Net Liquidity (B$)", secondary_y=False)
    fig_liq.update_yaxes(title_text="S&P 500 Index", secondary_y=True)
    st.plotly_chart(fig_liq, use_container_width=True)

st.subheader("📊 주요 유동성 창구 주간 증감 (단위: Billions $)")
col_l1, col_l2, col_l3, col_l4 = st.columns(4)

fed_bs_val = get_safe_val(latest, 'Fed_BS')
reserves_val = get_safe_val(latest, 'Reserves')
rrp_val = get_safe_val(latest, 'RRP')
tga_val = get_safe_val(latest, 'TGA')

col_l1.metric("연준 대차대조표", f"{fed_bs_val:,.0f}", f"{fed_bs_val - get_safe_val(prev_week, 'Fed_BS'):,.0f}")
col_l2.metric("지급준비금 (Reserves)", f"{reserves_val:,.0f}", f"{get_safe_val(latest, 'Reserves_1W_Chg'):,.0f}")
col_l3.metric("역레포 (RRP)", f"{rrp_val:,.0f}", f"{rrp_val - get_safe_val(prev_week, 'RRP'):,.0f}")
col_l4.metric("TGA (재무부 계좌)", f"{tga_val:,.0f}", f"{get_safe_val(latest, 'TGA_1W_Chg'):,.0f}")

st.divider()

# --- 3. 자금 이동 (MMF vs RRP) ---
st.header("🔄 3. 기관 자금 이동 (MMF vs 역레포)")
st.markdown("""
* **MMF 증가 + RRP 증가:** 시장 위험 회피 (안전 자산 선호)
* **MMF 감소 + RRP 감소:** 위험 자산 선호 증가 (주식 시장으로 자금 유입)
""")

if 'MMF' in df.columns and 'RRP' in df.columns:
    fig_flow = plotly_go.Figure()
    fig_flow.add_trace(plotly_go.Scatter(x=df.index, y=df['MMF'], name="MMF 총 잔액", fill='tozeroy', line=dict(color='purple')))
    fig_flow.add_trace(plotly_go.Scatter(x=df.index, y=df['RRP'], name="역레포 (RRP)", fill='tozeroy', line=dict(color='orange')))
    fig_flow.update_layout(title_text="MMF vs RRP 자금 흐름 추이", height=400, hovermode="x unified")
    st.plotly_chart(fig_flow, use_container_width=True)

st.divider()

# --- 4. 자동 매크로 리포트 생성 ---
st.header("📝 4. AI 기반 자동 매크로 시황 리포트")

def generate_report(latest, prev):
    report = []
    
    # 안전 값 가져오기
    vix = get_safe_val(latest, 'VIX')
    move = get_safe_val(latest, 'MOVE')
    fsi = get_safe_val(latest, 'FSI')
    yield_curve = get_safe_val(latest, '10Y_2Y')
    hy_spread = get_safe_val(latest, 'HY_Spread')
    prev_hy = get_safe_val(prev, 'HY_Spread')
    liq_change = get_safe_val(latest, 'Net_Liquidity') - get_safe_val(prev, 'Net_Liquidity')
    tga_chg = get_safe_val(latest, 'TGA_1W_Chg')
    mmf_chg = get_safe_val(latest, 'MMF_1W_Chg')
    rrp_chg = get_safe_val(latest, 'RRP') - get_safe_val(prev, 'RRP')
    
    # 1. 심리 및 리스크
    report.append("### 📌 시장 심리 및 리스크 진단")
    if vix > 30:
        report.append("- **[경고]** VIX가 30을 초과했습니다. 옵션 시장이 향후 큰 변동성을 예상하며 시장에 공포 심리가 팽배합니다.")
    elif 0 < vix < 20:
        report.append("- **[안정]** VIX가 20 미만으로 시장은 비교적 평온하며 탐욕/안정 구간에 있습니다.")
        
    if move > 140:
        report.append("- **[위험]** 채권 VIX인 MOVE 지수가 140을 넘었습니다. 은행/채권 시스템의 스트레스가 우려됩니다.")
    
    if fsi > 0:
        report.append("- **[주의]** 금융 스트레스 지수(FSI)가 0을 상회하고 있습니다. 시스템적 신용 경색 조짐을 모니터링해야 합니다.")

    # 2. 경기 사이클
    report.append("\n### 📌 경기 사이클 진단")
    if yield_curve < 0 and yield_curve != 0:
        report.append("- **[침체 신호]** 장단기 금리(10Y-2Y)가 역전된 상태입니다. 역사적으로 경기 침체의 강력한 선행 지표입니다.")
        if hy_spread > prev_hy * 1.1:
             report.append("  - 특히 하이일드 스프레드가 급등하고 있어 신용 경색 및 침체 가능성이 매우 높아지고 있습니다.")
    else:
        report.append("- 장단기 금리차는 안정적 구간에 있습니다.")

    # 3. 유동성 방향
    report.append("\n### 📌 유동성 흐름 및 향후 전망")
    if liq_change > 0:
        report.append(f"- **[긍정적]** 지난주 대비 Net Liquidity(순유동성)가 약 ${abs(liq_change):,.0f}B 증가했습니다. 주식 시장에 긍정적인 자금 환경입니다.")
    elif liq_change < 0:
        report.append(f"- **[부정적]** 지난주 대비 Net Liquidity(순유동성)가 약 ${abs(liq_change):,.0f}B 감소했습니다. 유동성 축소로 인한 자산 가격 조정에 유의해야 합니다.")
        
    if tga_chg > 0:
        report.append("- TGA 계좌 잔고가 증가하고 있습니다. 이는 시중의 돈을 정부가 흡수하고 있다는 의미로 단기적 유동성 압박 요인입니다.")
    elif tga_chg < 0:
        report.append("- TGA 계좌 잔고가 감소하며 시중에 돈이 풀리고 있습니다.")

    # 4. 기관 자금 동향
    if mmf_chg > 0 and rrp_chg > 0:
        report.append("- **[자금 흐름]** MMF와 역레포 잔액이 동반 상승 중입니다. 기관들이 투자를 꺼리고 단기 현금성 자산으로 대피(위험 회피)하는 징후입니다.")
    elif mmf_chg < 0 and rrp_chg < 0:
        report.append("- **[자금 흐름]** MMF와 역레포 잔액이 감소하고 있습니다. 대기 자금이 위험 자산(주식 등)으로 이동(위험 선호)하고 있을 가능성이 높습니다.")
    
    # 종합 전망 결론
    report.append("\n### 💡 종합 미래 전망")
    if yield_curve < 0 and fsi > 0 and liq_change < 0:
        report.append("👉 **[보수적 대응 권고]** 경기 침체 시그널과 유동성 축소가 겹치고 있습니다. 주식 비중을 축소하고 현금/채권 비중 확대를 고려할 시점입니다.")
    elif liq_change > 0 and (0 < vix < 25):
        report.append("👉 **[위험 자산 비중 유지/확대]** 유동성이 공급되고 있으며 시장 심리가 안정적입니다. 주식 등 위험 자산의 우상향 랠리가 지속될 확률이 높습니다.")
    else:
        report.append("👉 **[관망 및 종목 장세]** 매크로 지표가 혼재되어 있습니다. 지수 방향성보다는 개별 실적과 이슈에 집중하는 전략이 필요합니다.")

    return "\n".join(report)

# 리포트 출력 구역
report_text = generate_report(latest, prev_week)
st.info(report_text)

st.caption(f"마지막 데이터 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (기준일자: {df.index[-1].strftime('%Y-%m-%d')})")
