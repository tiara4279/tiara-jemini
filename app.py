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
/* 폰트 및 여백 미세조정 */
div[data-testid="stVerticalBlock"] > div {
    padding-bottom: 0.5rem;
}
</style>
<div class="notranslate">
""", unsafe_allow_html=True)

st.title("🌐 시장 경제 지표 대시보드")
st.markdown("시장의 위험 심리, 경기 사이클, 그리고 핵심 유동성 흐름을 매일 추적합니다.")

# --- 기간 선택 컨트롤 (글로벌) ---
st.markdown("### ⏱️ 추이 기준 기간 선택")
period_options = {"1개월": 21, "3개월": 63, "6개월": 126, "1년": 252}
selected_period_label = st.radio("기간", list(period_options.keys()), horizontal=True, label_visibility="collapsed")
selected_days = period_options[selected_period_label]
st.write("") # 간격 띄우기

# --- 데이터 로드 함수 ---
@st.cache_data(ttl=3600*12) 
def load_data():
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365*3) 
    
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
        'TOTLL': 'TOTLL',                 
        'SOFR': 'SOFR',                   
        'IORB': 'IORB',                   
        'T10YIE': 'T10YIE',               
        'Discount_Window': 'WLCFLPCL',    
        'BTFP': 'H41RESPALBFRB'           
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

with st.spinner('데이터를 분석 중입니다...'):
    df = load_data()

if df.empty or len(df) < 6:
    st.error("🚨 데이터를 가져오는 데 실패했습니다. 잠시 후 다시 시도해 주세요.")
    st.stop()

# --- 스파크라인 카드 렌더링 함수 ---
def render_sparkline_card(title, series_col, df, days, is_pct=False, reverse_color=False, status_func=None):
    if series_col not in df.columns:
        return
        
    sub_df = df[[series_col]].dropna()
    if len(sub_df) == 0: return
        
    sub_df = sub_df.tail(days)
    if len(sub_df) < 2: return
    
    current_val = sub_df.iloc[-1, 0]
    start_val = sub_df.iloc[0, 0]
    delta_val = current_val - start_val
    
    pct_chg = (delta_val / start_val * 100) if start_val != 0 else 0.0
    
    # 오르면 나쁜 지표(reverse_color=True)는 빨간색, 오르면 좋은 지표는 초록색
    if delta_val > 0:
        color_hex = "#ff4b4b" if reverse_color else "#09ab3b" 
        color_name = "red" if reverse_color else "green"
    elif delta_val < 0:
        color_hex = "#09ab3b" if reverse_color else "#ff4b4b"
        color_name = "green" if reverse_color else "red"
    else:
        color_hex = "#7f7f7f"
        color_name = "gray"
        
    with st.container(border=True):
        st.markdown(f"<div style='font-size:14px; font-weight:bold; color:#555;'>{title}</div>", unsafe_allow_html=True)
        
        # 포맷팅
        if is_pct:
            val_str = f"{current_val:.3f}%" if "SOFR" in title else f"{current_val:.2f}%"
            delta_str = f"{delta_val:+.3f}%p" if "SOFR" in title else f"{delta_val:+.2f}%p"
        elif "DXY" in title or "FSI" in title or "VIX" in title or "MOVE" in title:
            val_str = f"{current_val:.2f}"
            delta_str = f"{delta_val:+.2f}"
        else:
            val_str = f"{current_val:,.0f}억 달러"
            delta_str = f"{delta_val:+,.0f}억 달러"
            
        st.markdown(f"<h3 style='margin:0; padding:0; font-size:26px;'>{val_str}</h3>", unsafe_allow_html=True)
        st.markdown(f"<div style='color:{color_name}; font-weight:bold; font-size:13px; margin-bottom:10px;'>변동: {delta_str} ({pct_chg:+.2f}%)</div>", unsafe_allow_html=True)
        
        # Plotly 미니 차트 (스파크라인)
        def hex_to_rgba(hex_color, alpha=0.15):
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            return f'rgba({r},{g},{b},{alpha})'
            
        fig = plotly_go.Figure(plotly_go.Scatter(
            x=sub_df.index, y=sub_df.iloc[:, 0],
            mode='lines+markers',
            line=dict(color=color_hex, width=2),
            marker=dict(size=3, color=color_hex),
            fill='tozeroy', fillcolor=hex_to_rgba(color_hex)
        ))
        fig.update_layout(
            height=70, margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(visible=False, showgrid=False), yaxis=dict(visible=False, showgrid=False),
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
        
        if status_func:
            st.caption(status_func(current_val, delta_val))

# 상태 체크 헬퍼 함수들
def check_status(value, threshold, condition, danger_msg, safe_msg):
    if condition == 'greater' and value > threshold: return f"🔴 {danger_msg}"
    elif condition == 'less' and value < threshold: return f"🔴 {danger_msg}"
    else: return f"🟢 {safe_msg}"

# --- 1. 시장 리스크 경고 시스템 ---
st.header("🚨 1. 시장 리스크 경고 시스템")
c1 = st.columns(5)
with c1[0]: render_sparkline_card("VIX (옵션 변동성)", 'VIX', df, selected_days, reverse_color=True, status_func=lambda v, d: check_status(v, 30, 'greater', '시장 공포 극대화', '안정적'))
with c1[1]: render_sparkline_card("MOVE (채권 변동성)", 'MOVE', df, selected_days, reverse_color=True, status_func=lambda v, d: check_status(v, 140, 'greater', '채권 시스템 스트레스', '안정적'))
with c1[2]: render_sparkline_card("10Y-2Y 금리차", '10Y_2Y', df, selected_days, is_pct=True, reverse_color=False, status_func=lambda v, d: check_status(v, 0, 'less', '장단기 금리 역전', '정상'))
with c1[3]: render_sparkline_card("금융 스트레스 (FSI)", 'FSI', df, selected_days, reverse_color=True, status_func=lambda v, d: check_status(v, 0, 'greater', '금융 시스템 스트레스', '유동성 원활'))
with c1[4]: render_sparkline_card("하이일드 스프레드", 'HY_Spread', df, selected_days, is_pct=True, reverse_color=True, status_func=lambda v, d: check_status(v, 5.0, 'greater', '신용 경색 경보', '안정적'))

st.divider()

# --- 2. 핵심 유동성 흐름 분석 ---
st.header("🌊 2. 미국 유동성 흐름 (핵심)")
if 'Net_Liquidity' in df.columns and 'SP500' in df.columns:
    fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['Net_Liquidity'].tail(selected_days), name="US Net Liquidity (억 달러)", line=dict(color='blue')), secondary_y=False)
    fig_liq.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['SP500'].tail(selected_days), name="S&P 500", line=dict(color='red', width=2)), secondary_y=True)
    fig_liq.update_layout(title_text=f"Net Liquidity vs S&P 500 ({selected_period_label} 추이)", height=500, hovermode="x unified", margin=dict(t=50, b=0))
    fig_liq.update_yaxes(title_text="Net Liquidity (억 달러)", secondary_y=False)
    fig_liq.update_yaxes(title_text="S&P 500 Index", secondary_y=True)
    st.plotly_chart(fig_liq, use_container_width=True)

st.subheader("📊 주요 유동성 창구 증감")
c2 = st.columns(4)
with c2[0]: render_sparkline_card("연준 대차대조표", 'Fed_BS', df, selected_days, reverse_color=False, status_func=lambda v, d: "🟢 [유동성 팽창] 자금 공급" if d > 0 else ("🔴 [QT 진행] 자산 축소" if d < 0 else "➖ 변동 없음"))
with c2[1]: render_sparkline_card("지급준비금 (Reserves)", 'Reserves', df, selected_days, reverse_color=False, status_func=lambda v, d: "🟢 [신용 확대] 은행 여력 증가" if d > 0 else ("🔴 [신용 축소] 은행 여력 감소" if d < 0 else "➖ 변동 없음"))
with c2[2]: render_sparkline_card("역레포 (RRP)", 'RRP', df, selected_days, reverse_color=True, status_func=lambda v, d: "⚠️ [바닥 근접] 완충재 고갈 임박" if v < 1000 and v > 0 else ("🔴 [위험 회피] 자금 연준 회귀" if d > 0 else "🟢 [위험 선호] 자금 증시 이동"))
with c2[3]: render_sparkline_card("TGA (재무부 계좌)", 'TGA', df, selected_days, reverse_color=True, status_func=lambda v, d: "🔴 [자금 흡수] 국채발행 등 흡수" if d > 0 else ("🟢 [재정 지출] 시중 자금 펌핑" if d < 0 else "➖ 변동 없음"))

st.divider()

# --- 3. [신규] 은행 신용 & 단기 자금시장 (H.8 & SOFR) ---
st.header("🏦 3. 신용 창출 및 단기 자금시장 (H.8 & SOFR)")
st.markdown("상업은행의 실제 신용 창출 여부와 단기 달러 자금 시장의 발작(스트레스) 여부를 진단합니다.")
c3 = st.columns(3)
with c3[0]: 
    render_sparkline_card("H.8 상업은행 총대출", 'TOTLL', df, selected_days, reverse_color=False, status_func=lambda v, d: "🟢 [신용 팽창] 실물 경제 자금 공급" if d > 0 else ("🔴 [신용 축소] 대출 태도 강화" if d < 0 else "➖ [대출 정체] 규모 유지"))
with c3[1]: 
    # SOFR 상태 설명 명확화
    def sofr_status(v, d):
        if v == 0.0: return "🟢 [정상] 기준금리와 조달금리 일치"
        elif v > 0.05: return "🔴 [경고] 단기 자금 달러 부족(발작 조짐)"
        elif v > 0: return "⚠️ [주의] 레포 시장 유동성 타이트"
        else: return "🟢 [안정] 단기 자금 조달 매우 원활"
    render_sparkline_card("SOFR - IORB 스프레드", 'SOFR_IORB_Spread', df, selected_days, is_pct=True, reverse_color=True, status_func=sofr_status)
with c3[2]: 
    render_sparkline_card("연준 H.4.1 긴급대출", 'Emergency_Loans', df, selected_days, reverse_color=True, status_func=lambda v, d: "🔴 [위험] 뱅크런 징후 발생" if v > 500 else ("⚠️ [주의] 연준 긴급 차입 발생" if v > 0 else "🟢 [매우 안정] 시스템 위기 없음(대출 0)"))

st.divider()

# --- 4. [신규] 글로벌 달러 및 인플레이션 (DXY & BEI) ---
st.header("🌍 4. 글로벌 유동성 및 인플레이션 (DXY & BEI)")
c4 = st.columns(2)
with c4[0]: 
    render_sparkline_card("DXY (달러 인덱스)", 'DXY', df, selected_days, reverse_color=True, status_func=lambda v, d: "🔴 [달러 강세] 글로벌 유동성 흡수" if v > 105 else ("🟢 [달러 약세] 위험자산 우호적" if v < 100 else "➖ [중립] 박스권 안정세"))
with c4[1]: 
    render_sparkline_card("10Y BEI (기대인플레이션)", 'T10YIE', df, selected_days, is_pct=True, reverse_color=True, status_func=lambda v, d: "🔴 [물가 불안] 인플레 고착화 우려" if v > 2.5 else ("⚠️ [디스인플레] 경기 둔화 우려" if v < 2.0 else "🟢 [골디락스] 물가 안정화"))

st.divider()

# --- 5. 자금 이동 (MMF vs RRP) ---
st.header("🔄 5. 기관 자금 이동 (MMF vs 역레포)")
if 'MMF' in df.columns and 'RRP' in df.columns:
    fig_flow = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1, subplot_titles=("MMF 총 잔액 추이", "역레포(RRP) 잔액 추이"))
    fig_flow.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['MMF'].tail(selected_days), name="MMF", fill='tozeroy', line=dict(color='purple')), row=1, col=1)
    fig_flow.add_trace(plotly_go.Scatter(x=df.index[-selected_days:], y=df['RRP'].tail(selected_days), name="RRP", fill='tozeroy', line=dict(color='orange')), row=2, col=1)
    fig_flow.update_layout(height=500, hovermode="x unified", showlegend=False, margin=dict(t=30, b=0))
    fig_flow.update_xaxes(rangeslider_visible=False, row=1, col=1)
    fig_flow.update_xaxes(rangeslider_visible=False, row=2, col=1)
    st.plotly_chart(fig_flow, use_container_width=True)

st.divider()

# --- 6. AI 기반 종합 시황 리포트 ---
st.header("📝 6. AI 기반 매크로 종합 시황 리포트")
def generate_report(df, days):
    sub_df = df.tail(days)
    if len(sub_df) < 2: return "데이터가 충분하지 않습니다."
    
    latest = sub_df.iloc[-1]
    start = sub_df.iloc[0]
    
    def safe(row, col): return row[col] if col in row.index else 0.0
    
    vix, move, fsi = safe(latest, 'VIX'), safe(latest, 'MOVE'), safe(latest, 'FSI')
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
