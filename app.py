import streamlit as st
import pandas as pd
import yfinance as yf
import pandas_datareader.data as web
import datetime
import plotly.graph_objects as plotly_go
from plotly.subplots import make_subplots

# --- 페이지 설정 ---
st.set_page_config(page_title="Global Macro & Liquidity Dashboard", layout="wide")
st.title("🌐 매크로 & 유동성 분석 대시보드")
st.markdown("시장의 위험 심리, 경기 사이클, 그리고 핵심 유동성 흐름을 매일 추적합니다.")

# --- 데이터 로드 함수 (캐싱하여 속도 향상) ---
@st.cache_data(ttl=3600*12) # 12시간마다 갱신
def load_data():
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365*3) # 과거 3년 데이터
    
    # 1. FRED 데이터 가져오기 (무료 매크로 데이터)
    fred_series = {
        'VIX': 'VIXCLS',                  # VIX
        'HY_Spread': 'BAMLH0A0HYM2',      # 하이일드 스프레드
        'FSI': 'STLFSI4',                 # 금융 스트레스 지수
        '10Y_2Y': 'T10Y2Y',               # 장단기 금리차
        'Fed_BS': 'WALCL',                # 연준 대차대조표 (Millions)
        'Reserves': 'WRESBAL',            # 지급준비금 (Billions)
        'RRP': 'RRPONTSYD',               # 역레포 (Billions)
        'TGA': 'WTREGEN',                 # TGA (Billions)
        'MMF': 'MMMFFAQ027S'              # MMF 총 잔액 (Millions) - *FRED 분기/월간 베이스, 주간/일간은 유료API 필요하나 추세용으로 사용
    }
    
    df_fred = pd.DataFrame()
    for name, series_id in fred_series.items():
        try:
            df_fred[name] = web.DataReader(series_id, 'fred', start, end)
        except:
            pass # 데이터 로드 실패시 패스

    # 단위 통일 (Billions -> Millions로 변환하여 Fed BS와 맞추거나, 전부 Billions로 맞춤)
    # 여기서는 보기 편하게 모두 Billions(10억 달러) 단위로 통일
    if 'Fed_BS' in df_fred.columns: df_fred['Fed_BS'] = df_fred['Fed_BS'] / 1000
    if 'MMF' in df_fred.columns: df_fred['MMF'] = df_fred['MMF'] / 1000

    # 전일 데이터로 빈칸 채우기 (휴일 등)
    df_fred = df_fred.ffill().dropna()

    # 2. Yahoo Finance 데이터 가져오기 (S&P 500, MOVE)
    # MOVE Index는 야후에 ^MOVE 로 존재, S&P 500은 ^GSPC
    tickers = ['^GSPC', '^MOVE']
    df_yf = yf.download(tickers, start=start, end=end)['Close']
    df_yf.columns = ['SP500', 'MOVE']
    df_yf = df_yf.ffill().dropna()

    # 데이터 병합
    df_merged = pd.concat([df_fred, df_yf], axis=1).ffill().dropna()
    
    # 3. 파생 변수 계산
    # Net Liquidity = Fed BS - RRP - TGA
    df_merged['Net_Liquidity'] = df_merged['Fed_BS'] - df_merged['RRP'] - df_merged['TGA']
    
    # 주간 증감폭 계산 (5영업일 기준)
    df_merged['Reserves_1W_Chg'] = df_merged['Reserves'].diff(5)
    df_merged['TGA_1W_Chg'] = df_merged['TGA'].diff(5)
    df_merged['MMF_1W_Chg'] = df_merged['MMF'].diff(5)
    
    return df_merged

# 데이터 로딩
with st.spinner('데이터를 불러오는 중입니다... (FRED & Yahoo Finance)'):
    df = load_data()

# 최신 데이터 추출
latest = df.iloc[-1]
prev_week = df.iloc[-6] # 1주일 전 (약 5영업일)

# --- 1. 시장 리스크 경고 시스템 (최상단) ---
st.header("🚨 1. 시장 리스크 경고 시스템")

col1, col2, col3, col4 = st.columns(4)

def check_status(value, threshold, condition, danger_msg, safe_msg):
    if condition == 'greater' and value > threshold:
        return f"🔴 {danger_msg}"
    elif condition == 'less' and value < threshold:
        return f"🔴 {danger_msg}"
    else:
        return f"🟢 {safe_msg}"

with col1:
    vix_status = check_status(latest['VIX'], 30, 'greater', "시장 공포 극대화", "안정적")
    st.metric(label="VIX (옵션 변동성)", value=f"{latest['VIX']:.2f}", delta=f"{latest['VIX'] - prev_week['VIX']:.2f} (1W)")
    st.caption(f"상태: {vix_status}")

with col2:
    move_status = check_status(latest['MOVE'], 140, 'greater', "채권/은행 시스템 스트레스", "안정적")
    st.metric(label="MOVE Index (채권 VIX)", value=f"{latest['MOVE']:.2f}", delta=f"{latest['MOVE'] - prev_week['MOVE']:.2f} (1W)")
    st.caption(f"상태: {move_status}")

with col3:
    yield_status = check_status(latest['10Y_2Y'], 0, 'less', "장단기 금리 역전 (침체 선행)", "정상")
    st.metric(label="10Y-2Y 금리차", value=f"{latest['10Y_2Y']:.2f}%", delta=f"{latest['10Y_2Y'] - prev_week['10Y_2Y']:.2f}% (1W)")
    st.caption(f"상태: {yield_status}")

with col4:
    fsi_status = check_status(latest['FSI'], 0, 'greater', "금융 시스템 스트레스 발생", "유동성 원활")
    st.metric(label="금융 스트레스 지수 (FSI)", value=f"{latest['FSI']:.2f}", delta=f"{latest['FSI'] - prev_week['FSI']:.2f} (1W)")
    st.caption(f"상태: {fsi_status}")

st.divider()

# --- 2. 핵심 유동성 흐름 분석 ---
st.header("🌊 2. 미국 유동성 흐름 (핵심)")

st.markdown("""
**공식:** `Net Liquidity = 연준 대차대조표(Fed BS) - 역레포(RRP) - 미 재무부 계좌(TGA)`  
*이 지표는 S&P 500 등 주식 시장과 강한 양의 상관관계를 가집니다.*
""")

# Net Liquidity vs S&P 500 차트
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

# 유동성 세부 지표 변화량
st.subheader("📊 주요 유동성 창구 주간 증감 (단위: Billions $)")
col_l1, col_l2, col_l3, col_l4 = st.columns(4)
col_l1.metric("연준 대차대조표", f"{latest['Fed_BS']:,.0f}", f"{latest['Fed_BS'] - prev_week['Fed_BS']:,.0f}")
col_l2.metric("지급준비금 (Reserves)", f"{latest['Reserves']:,.0f}", f"{latest['Reserves_1W_Chg']:,.0f}")
col_l3.metric("역레포 (RRP)", f"{latest['RRP']:,.0f}", f"{latest['RRP'] - prev_week['RRP']:,.0f}")
col_l4.metric("TGA (재무부 계좌)", f"{latest['TGA']:,.0f}", f"{latest['TGA_1W_Chg']:,.0f}")

st.divider()

# --- 3. 자금 이동 (MMF vs RRP) ---
st.header("🔄 3. 기관 자금 이동 (MMF vs 역레포)")
st.markdown("""
* **MMF 증가 + RRP 증가:** 시장 위험 회피 (안전 자산 선호)
* **MMF 감소 + RRP 감소:** 위험 자산 선호 증가 (주식 시장으로 자금 유입)
""")

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
    
    # 1. 심리 및 리스크
    report.append("### 📌 시장 심리 및 리스크 진단")
    if latest['VIX'] > 30:
        report.append("- **[경고]** VIX가 30을 초과했습니다. 옵션 시장이 향후 큰 변동성을 예상하며 시장에 공포 심리가 팽배합니다.")
    elif latest['VIX'] < 20:
        report.append("- **[안정]** VIX가 20 미만으로 시장은 비교적 평온하며 탐욕/안정 구간에 있습니다.")
        
    if latest['MOVE'] > 140:
        report.append("- **[위험]** 채권 VIX인 MOVE 지수가 140을 넘었습니다. 은행/채권 시스템의 스트레스가 우려됩니다.")
    
    if latest['FSI'] > 0:
        report.append("- **[주의]** 금융 스트레스 지수(FSI)가 0을 상회하고 있습니다. 시스템적 신용 경색 조짐을 모니터링해야 합니다.")

    # 2. 경기 사이클
    report.append("\n### 📌 경기 사이클 진단")
    if latest['10Y_2Y'] < 0:
        report.append("- **[침체 신호]** 장단기 금리(10Y-2Y)가 역전된 상태입니다. 역사적으로 경기 침체의 강력한 선행 지표입니다.")
        if latest['HY_Spread'] > prev['HY_Spread'] * 1.1:
             report.append("  - 특히 하이일드 스프레드가 급등하고 있어 신용 경색 및 침체 가능성이 매우 높아지고 있습니다.")
    else:
        report.append("- 장단기 금리차는 정상 구간에 있습니다.")

    # 3. 유동성 방향
    report.append("\n### 📌 유동성 흐름 및 향후 전망")
    liq_change = latest['Net_Liquidity'] - prev['Net_Liquidity']
    if liq_change > 0:
        report.append(f"- **[긍정적]** 지난주 대비 Net Liquidity(순유동성)가 약 ${abs(liq_change):.0f}B 증가했습니다. 주식 시장에 긍정적인 자금 환경입니다.")
    else:
        report.append(f"- **[부정적]** 지난주 대비 Net Liquidity(순유동성)가 약 ${abs(liq_change):.0f}B 감소했습니다. 유동성 축소로 인한 자산 가격 조정에 유의해야 합니다.")
        
    if latest['TGA_1W_Chg'] > 0:
        report.append("- TGA 계좌 잔고가 증가하고 있습니다. 이는 시중의 돈을 정부가 흡수하고 있다는 의미로 단기적 유동성 압박 요인입니다.")
    else:
        report.append("- TGA 계좌 잔고가 감소하며 시중에 돈이 풀리고 있습니다.")

    # 4. 기관 자금 동향
    mmf_chg = latest['MMF_1W_Chg']
    rrp_chg = latest['RRP'] - prev['RRP']
    if mmf_chg > 0 and rrp_chg > 0:
        report.append("- **[자금 흐름]** MMF와 역레포 잔액이 동반 상승 중입니다. 기관들이 투자를 꺼리고 단기 현금성 자산으로 대피(위험 회피)하는 징후입니다.")
    elif mmf_chg < 0 and rrp_chg < 0:
        report.append("- **[자금 흐름]** MMF와 역레포 잔액이 감소하고 있습니다. 대기 자금이 위험 자산(주식 등)으로 이동(위험 선호)하고 있을 가능성이 높습니다.")
    
    # 종합 전망 결론
    report.append("\n### 💡 종합 미래 전망")
    if latest['10Y_2Y'] < 0 and latest['FSI'] > 0 and liq_change < 0:
        report.append("👉 **[보수적 대응 권고]** 경기 침체 시그널과 유동성 축소가 겹치고 있습니다. 주식 비중을 축소하고 현금/채권 비중 확대를 고려할 시점입니다.")
    elif liq_change > 0 and latest['VIX'] < 25:
        report.append("👉 **[위험 자산 비중 유지/확대]** 유동성이 공급되고 있으며 시장 심리가 안정적입니다. 주식 등 위험 자산의 우상향 랠리가 지속될 확률이 높습니다.")
    else:
        report.append("👉 **[관망 및 종목 장세]** 매크로 지표가 혼재되어 있습니다. 지수 방향성보다는 개별 실적과 이슈에 집중하는 전략이 필요합니다.")

    return "\n".join(report)

# 리포트 출력 구역
report_text = generate_report(latest, prev_week)
st.info(report_text)

st.caption(f"마지막 데이터 업데이트: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (기준일자: {df.index[-1].strftime('%Y-%m-%d')})")
st.caption("*참고: 공포탐욕지수 및 글로벌 중앙은행(ECB, BOJ, PBOC) 통합 데이터는 무료 API 제공처의 한계로 인해 대표적인 대리 지표(VIX 등)와 연준(Fed) 중심의 데이터로 최적화하여 구현되었습니다.")
