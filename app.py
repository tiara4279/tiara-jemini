<<<<
# --- 데이터 로드 함수 ---
@st.cache_data(ttl=3600*12) 
def load_data():
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365*3) 
    
    fred_series = {
        'VIX': 'VIXCLS', 'HY_Spread': 'BAMLH0A0HYM2', 'FSI': 'STLFSI4', '10Y_2Y': 'T10Y2Y',
        '10Y': 'DGS10', '2Y': 'DGS2',
        'Fed_BS': 'WALCL', 'WRESBAL_Ind': 'WRESBAL', 'Reserves': 'WRESBAL', 'RRP': 'RRPONTSYD', 'TGA': 'WTREGEN',                 
        'MMF': 'WRMFSL', 'TOTLL': 'TOTLL', 'SOFR': 'SOFR', 'IORB': 'IORB',                   
        'T10YIE': 'T10YIE', 'Discount_Window': 'WLCFLPCL', 'BTFP': 'H41RESPALBFRB'           
    }
====
# --- 데이터 로드 함수 ---
@st.cache_data(ttl=3600*12) 
def load_data():
    end = datetime.datetime.today()
    start = end - datetime.timedelta(days=365*3) 
    
    fred_series = {
        'VIX': 'VIXCLS', 'HY_Spread': 'BAMLH0A0HYM2', 'FSI': 'STLFSI4', '10Y_2Y': 'T10Y2Y',
        '10Y': 'DGS10', '2Y': 'DGS2',
        'Fed_BS': 'WALCL', 'WRESBAL_Ind': 'WRESBAL', 'Reserves': 'WRESBAL', 'RRP': 'RRPONTSYD', 'TGA': 'WTREGEN',                 
        'MMF': 'WRMFNS', 'TOTLL': 'TOTLL', 'SOFR': 'SOFR', 'IORB': 'IORB',                   
        'T10YIE': 'T10YIE', 'Discount_Window': 'WLCFLPCL', 'BTFP': 'H41RESPALBFRB'           
    }
>>>>

<<<<
    'MMF': {'name': '머니마켓펀드 (MMF) 총 잔액', 'short_name': 'MMF 총 잔액', 'unit': '억 달러', 'inverted': True, 'meta': '단위: 억 달러 · 분기별(Quarterly) 업데이트 · 기관/개인의 대기 자금', 
            'desc': '투자자들이 언제든 현금화할 수 있는 초단기 금융상품(MMF)에 파킹해둔 자금 총액입니다. 시장이 불안하면 주식을 팔고 현금으로 도피하며, 시장이 좋으면 현금을 빼서 주식을 삽니다.<br><br><b style="color: #D4AF37;">💡 [데이터 안내] FRED 연준 데이터 특성상 이 지표는 3개월(분기)에 한 번씩만 수치가 발표됩니다. 따라서 다음 발표일까지는 그래프가 계단식 평행선으로 유지되며, 단기 변동률이 "변동 없음"으로 나오는 것은 정상입니다.</b>', 
            'eval': eval_mmf, 'levels': [("잔액 감소", "위험 선호", COLOR_SAFE, "💸", "안전 자산에서 돈을 빼서 주식 등 위험 자산으로 적극적으로 투자하는 긍정적 신호입니다."), ("잔액 증가", "자금 대피", COLOR_WARN, "🛡️", "시장 하락이나 불확실성을 우려해 투자를 멈추고 현금으로 관망하는 상태입니다.")]},
====
    'MMF': {'name': '머니마켓펀드 (MMF) 잔액', 'short_name': 'MMF 잔액', 'unit': '억 달러', 'inverted': True, 'meta': '단위: 억 달러 · 주간 · 대기 자금 흐름', 
            'desc': '투자자들이 언제든 현금화할 수 있는 초단기 금융상품(MMF)에 파킹해둔 자금 총액입니다. 시장이 불안하면 주식을 팔고 현금으로 도피하며, 시장이 좋으면 현금을 빼서 주식을 삽니다.<br><br><b style="color: #D4AF37;">💡 [데이터 안내] 주식 시장의 단기 자금 흐름을 가장 정확하고 빠르게 추적하기 위해, 연준(FRED)에서 매주 업데이트되는 소매용 MMF(Retail Money Funds) 지표를 기준으로 분석합니다.</b>', 
            'eval': eval_mmf, 'levels': [("잔액 감소", "위험 선호", COLOR_SAFE, "💸", "안전 자산에서 돈을 빼서 주식 등 위험 자산으로 적극적으로 투자하는 긍정적 신호입니다."), ("잔액 증가", "자금 대피", COLOR_WARN, "🛡️", "시장 하락이나 불확실성을 우려해 투자를 멈추고 현금으로 관망하는 상태입니다.")]},
>>>>
