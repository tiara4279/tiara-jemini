<<<<
    # 나스닥, 금, 비트코인 및 한국 자산(코스피, 코스닥, 삼성전자, 환율) 데이터 수집 추가
    tickers = ['^GSPC', '^MOVE', 'DX-Y.NYB', '^IXIC', 'GC=F', 'BTC-USD', '^KS11', '^KQ11', '005930.KS', 'KRW=X']
    df_yf = pd.DataFrame()
    try:
        yf_data = yf.download(tickers, start=start, end=end, progress=False)
        if 'Close' in yf_data.columns: df_yf = yf_data['Close']
        else: df_yf = yf_data
        df_yf = df_yf.rename(columns={
            '^GSPC': 'SP500', '^MOVE': 'MOVE', 'DX-Y.NYB': 'DXY', 
            '^IXIC': 'NASDAQ', 'GC=F': 'GOLD', 'BTC-USD': 'BTC',
            '^KS11': 'KOSPI', '^KQ11': 'KOSDAQ', '005930.KS': 'SAMSUNG', 'KRW=X': 'USDKRW'
        })
    except Exception as e:
        pass
====
    # 나스닥, 금, 비트코인, 한국 자산 및 매크로 지표(WTI, 엔화) 데이터 수집 추가
    tickers = ['^GSPC', '^MOVE', 'DX-Y.NYB', '^IXIC', 'GC=F', 'BTC-USD', '^KS11', '^KQ11', '005930.KS', 'KRW=X', 'JPY=X', 'CL=F']
    df_yf = pd.DataFrame()
    try:
        yf_data = yf.download(tickers, start=start, end=end, progress=False)
        if 'Close' in yf_data.columns: df_yf = yf_data['Close']
        else: df_yf = yf_data
        df_yf = df_yf.rename(columns={
            '^GSPC': 'SP500', '^MOVE': 'MOVE', 'DX-Y.NYB': 'DXY', 
            '^IXIC': 'NASDAQ', 'GC=F': 'GOLD', 'BTC-USD': 'BTC',
            '^KS11': 'KOSPI', '^KQ11': 'KOSDAQ', '005930.KS': 'SAMSUNG', 'KRW=X': 'USDKRW',
            'JPY=X': 'USDJPY', 'CL=F': 'WTI'
        })
    except Exception as e:
        pass
>>>>

<<<<
    """
    st.markdown(korean_assets_html, unsafe_allow_html=True)

custom_header("🌊", "미국 핵심 유동성 흐름", "Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")
====
    """
    st.markdown(korean_assets_html, unsafe_allow_html=True)

# --- 핵심 매크로 및 유동성 요약 보드 (신규 추가) ---
st.markdown("<div style='font-size: 1.1rem; font-weight: 800; color: #f8fafc; margin-bottom: 15px; margin-top: 10px;'><span style='margin-right: 8px;'>📋</span> 핵심 지표 요약 보드</div>", unsafe_allow_html=True)

def make_diff_str(cur, prev, unit='', invert=False, period='전일'):
    diff = cur - prev
    color = COLOR_SAFE if (diff < 0 if invert else diff > 0) else COLOR_DANGER
    if abs(diff) < 0.001: color = "rgba(255,255,255,0.4)"
    arrow = "▼" if diff < 0 else "▲" if diff > 0 else "-"
    
    if unit == '원': val_str = f"{abs(diff):.0f}원"
    elif unit == '엔': val_str = f"{abs(diff):.1f}엔"
    elif unit == '%': val_str = f"{abs(diff):.2f}"
    elif unit == 'B': val_str = f"${abs(diff):.2f}B"
    elif unit == 'T': val_str = f"${abs(diff):.2f}T"
    else: val_str = f"{abs(diff):.2f}"
    
    return f"<span style='color:{color};'>{arrow} {val_str} {period} 대비</span>"

def render_mini_card(title, val_str, diff_html, footer, rgb_color):
    return f'''
    <div style="background: rgba(255,255,255,0.02); border: 1px solid rgba({rgb_color}, 0.25); border-radius: 12px; padding: 18px;">
        <div style="color: rgb({rgb_color}); font-size: 0.85rem; font-weight: 700; margin-bottom: 8px;">{title}</div>
        <div style="color: #ffffff; font-size: 1.8rem; font-weight: 900; line-height: 1.2;">{val_str}</div>
        <div style="font-size: 0.85rem; font-weight: 700; margin-top: 8px;">{diff_html}</div>
        <div style="border-top: 1px solid rgba(255,255,255,0.05); margin: 12px 0 8px 0;"></div>
        <div style="color: rgba(255,255,255,0.4); font-size: 0.75rem;">{footer}</div>
    </div>
    '''

req_cols = ['VIX', '10Y_2Y', 'HY_Spread', 'DXY', 'USDJPY', '10Y', 'WTI', 'Fed_BS', 'Reserves', 'RRP', 'TGA']
if all(c in df.columns for c in req_cols):
    # 1. 시장 데이터
    v_vix = df['VIX'].dropna().values[-2:]
    v_10y2y = df['10Y_2Y'].dropna().values[-2:]
    v_hy = df['HY_Spread'].dropna().values[-2:]
    
    # 공포탐욕지수 프록시 계산 (VIX 역산 추정치)
    fng_score = int(max(0, min(100, 100 - (v_vix[-1] - 10) * 3.33)))
    if fng_score <= 25: fng_state, fng_col = "극단적 공포 · extreme fear", COLOR_DANGER
    elif fng_score <= 45: fng_state, fng_col = "공포 · fear", COLOR_WARN
    elif fng_score <= 55: fng_state, fng_col = "중립 · neutral", COLOR_NEUTRAL
    elif fng_score <= 75: fng_state, fng_col = "탐욕 · greed", COLOR_SAFE
    else: fng_state, fng_col = "극단적 탐욕 · extreme greed", COLOR_SAFE
    
    fng_diff_str = f"<span style='color:{fng_col};'>{fng_state}</span>"
    
    # 2. 매크로 데이터
    v_dxy = df['DXY'].dropna().values[-2:]
    v_jpy = df['USDJPY'].dropna().values[-2:]
    v_10y = df['10Y'].dropna().values[-2:]
    v_wti = df['WTI'].dropna().values[-2:]
    
    # 3. 유동성 데이터
    v_fed = df['Fed_BS'].dropna().values[-2:] / 10000  # Trillion 변환
    v_res = df['Reserves'].dropna().values[-2:] / 10000 # Trillion 변환
    v_rrp = df['RRP'].dropna().values[-2:] / 10      # Billion 변환
    v_tga = df['TGA'].dropna().values[-2:] * 100     # Billion 변환 (기존 코드가 /100 상태이므로 *100 복구)

    board_html = f'''
    <div style="margin-bottom: 3rem;">
        <!-- 1. 시장 -->
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 0.95rem; font-weight: 800; color: rgba(255,255,255,0.8); margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                <span style="color: rgb(249, 115, 22);">📈</span> 시장
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                {render_mini_card("공포탐욕지수 (추정)", f"{fng_score}", fng_diff_str, "VIX 기반 추정치", "249, 115, 22")}
                {render_mini_card("VIX 변동성", f"{v_vix[-1]:.2f}", make_diff_str(v_vix[-1], v_vix[-2], invert=True), "20↓ 안정 · 30↑ 경계", "249, 115, 22")}
                {render_mini_card("장단기 금리차", f"{v_10y2y[-1]:.2f}%", make_diff_str(v_10y2y[-1], v_10y2y[-2], unit='%'), "10Y - 2Y · 음수 = 역전", "249, 115, 22")}
                {render_mini_card("하이일드 스프레드", f"{v_hy[-1]:.2f}%", make_diff_str(v_hy[-1], v_hy[-2], unit='%', invert=True), "신용시장 스트레스", "249, 115, 22")}
            </div>
        </div>

        <!-- 2. 매크로 -->
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 0.95rem; font-weight: 800; color: rgba(255,255,255,0.8); margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                <span style="color: rgb(168, 85, 247);">🌐</span> 매크로
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                {render_mini_card("달러인덱스", f"{v_dxy[-1]:.2f}", make_diff_str(v_dxy[-1], v_dxy[-2], invert=True), "DXY · ICE 달러인덱스", "168, 85, 247")}
                {render_mini_card("달러/엔", f"{v_jpy[-1]:.1f}엔", make_diff_str(v_jpy[-1], v_jpy[-2], unit='엔', invert=True), "엔화 강세/약세", "168, 85, 247")}
                {render_mini_card("10년물 금리", f"{v_10y[-1]:.2f}%", make_diff_str(v_10y[-1], v_10y[-2], unit='%', invert=True), "미국 장기금리 기준", "168, 85, 247")}
                {render_mini_card("WTI 원유", f"${v_wti[-1]:.1f}", make_diff_str(v_wti[-1], v_wti[-2], invert=True), "USD/배럴", "168, 85, 247")}
            </div>
        </div>

        <!-- 3. 유동성 -->
        <div style="margin-bottom: 1.5rem;">
            <div style="font-size: 0.95rem; font-weight: 800; color: rgba(255,255,255,0.8); margin-bottom: 10px; display: flex; align-items: center; gap: 6px;">
                <span style="color: rgb(59, 130, 246);">💧</span> 유동성
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                {render_mini_card("연준 총자산", f"{v_fed[-1]:.2f}T", make_diff_str(v_fed[-1], v_fed[-2], unit='T', period='전주'), "연준 대차대조표 · QE/QT", "59, 130, 246")}
                {render_mini_card("연준 지급준비금", f"{v_res[-1]:.2f}T", make_diff_str(v_res[-1], v_res[-2], unit='T', period='전주'), "은행 시스템 총 준비금", "59, 130, 246")}
                {render_mini_card("역레포(RRP) 잔액", f"{v_rrp[-1]:.2f}B", make_diff_str(v_rrp[-1], v_rrp[-2], unit='B', invert=True), "연준 초과유동성 흡수액", "59, 130, 246")}
                {render_mini_card("TGA 잔액", f"{v_tga[-1]:.1f}B", make_diff_str(v_tga[-1], v_tga[-2], unit='B', invert=True, period='전주'), "재무부 일반계정 잔고", "59, 130, 246")}
            </div>
        </div>
    </div>
    '''
    st.markdown(board_html, unsafe_allow_html=True)


custom_header("🌊", "미국 핵심 유동성 흐름", "Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")
>>>>
