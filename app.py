# ═══════════════════════════════════════════════════════════
#  §9 Net Liquidity (실제 데이터 적용 버전)
# ═══════════════════════════════════════════════════════════
sec("🌊", "미국 핵심 유동성 흐름 (Net Liquidity)")
st.caption("Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")

try:
    walcl  = get_fred('WALCL',     limit=300)
    rrp    = get_fred('RRPONTSYD', limit=300)
    tga    = get_fred('WTREGEN',   limit=300)
    _, _, sp500_df = get_yf('^GSPC', period='1y', interval='1d')

    if all([
        walcl is not None, rrp is not None, tga is not None,
        sp500_df is not None and len(sp500_df) > 10
    ]):
        # ── 단위 변환 (M$ → T$)
        walcl_t = walcl / 1_000_000.0
        rrp_t   = rrp   / 1_000_000.0
        tga_t   = tga   / 1_000_000.0

        df_liq = pd.DataFrame({
            'WALCL': walcl_t,
            'RRP':   rrp_t,
            'TGA':   tga_t,
        })
        df_liq['Net_Liquidity'] = df_liq['WALCL'] - df_liq['RRP'] - df_liq['TGA']

        # ── S&P500 타임존 제거
        sp500_s = sp500_df['Close'].copy()
        if hasattr(sp500_s.index, 'tz') and sp500_s.index.tz is not None:
            sp500_s.index = sp500_s.index.tz_localize(None)

        # ── 날짜 정규화 후 병합
        df_liq.index  = pd.to_datetime(df_liq.index).normalize()
        sp500_s.index = pd.to_datetime(sp500_s.index).normalize()

        # FRED는 주간 → S&P500(일간)에 ffill 후 병합
        df_plot = df_liq[['Net_Liquidity', 'WALCL', 'RRP', 'TGA']] \
                    .reindex(sp500_s.index, method='ffill') \
                    .join(sp500_s.rename('Close')) \
                    .dropna()

        if len(df_plot) > 10:
            # ── 최신값 추출
            latest_walcl = df_plot['WALCL'].iloc[-1]
            latest_rrp   = df_plot['RRP'].iloc[-1]
            latest_tga   = df_plot['TGA'].iloc[-1]
            latest_nl    = df_plot['Net_Liquidity'].iloc[-1]
            latest_sp    = df_plot['Close'].iloc[-1]
            latest_date  = df_plot.index[-1].strftime('%Y-%m-%d')

            prev_nl = df_plot['Net_Liquidity'].iloc[-6]   # ~1주 전
            nl_chg  = latest_nl - prev_nl
            nl_chg_arrow = "▲" if nl_chg >= 0 else "▼"
            nl_chg_color = "#22D98A" if nl_chg >= 0 else "#FF5555"

            # ── 차트
            fig_liq = make_subplots(specs=[[{"secondary_y": True}]])

            fig_liq.add_trace(
                go.Scatter(
                    x=df_plot.index, y=df_plot['Net_Liquidity'],
                    name="순유동성 (T$)",
                    line=dict(color='#00D4FF', width=2.5),
                    fill='tozeroy',
                    fillcolor='rgba(0,212,255,0.06)'
                ),
                secondary_y=False
            )
            fig_liq.add_trace(
                go.Scatter(
                    x=df_plot.index, y=df_plot['Close'],
                    name="S&P 500",
                    line=dict(color='#FF5555', width=1.8)
                ),
                secondary_y=True
            )

            fig_liq.update_layout(
                **CHART_LAYOUT,
                title_text="Net Liquidity vs S&P 500 (최근 1년)"
            )
            fig_liq.update_yaxes(
                title_text="순유동성 (T$)", secondary_y=False, color="#00D4FF"
            )
            fig_liq.update_yaxes(
                title_text="S&P 500", secondary_y=True, color="#FF5555"
            )

            st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})

            # ── 실제 데이터 적용 공식 박스
            st.markdown(f"""
<div style="background:#0C1420; border:1px solid #1E3050; border-radius:14px; padding:20px; margin-bottom:24px;">

  <div style="font-size:0.95rem; font-weight:800; color:#00D4FF; margin-bottom:14px;">
    📌 Net Liquidity 실시간 계산 &nbsp;<span style="font-size:0.75rem; color:#4A6888; font-weight:600;">기준일: {latest_date}</span>
  </div>

  <!-- 공식 계산식 -->
  <div style="font-family:'IBM Plex Mono',monospace; background:#060A12; border:1px solid #1A2A3F; border-radius:10px; padding:16px; margin-bottom:16px; line-height:2;">

    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
      <span style="color:#3B82F6; font-size:1.05rem; font-weight:700;">연준 총자산</span>
      <span style="color:#4A6888;">(WALCL)</span>
      <span style="background:#1A2A3F; padding:4px 12px; border-radius:6px; color:#FFFFFF; font-size:1.1rem; font-weight:700;">${latest_walcl:.2f} T</span>
    </div>

    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-top:4px;">
      <span style="color:#FF5555; font-size:1.2rem; font-weight:900;">−</span>
      <span style="color:#EC4899; font-size:1.05rem; font-weight:700;">역레포 (RRP)</span>
      <span style="color:#4A6888;">(RRPONTSYD)</span>
      <span style="background:#1A2A3F; padding:4px 12px; border-radius:6px; color:#FFFFFF; font-size:1.1rem; font-weight:700;">${latest_rrp:.2f} T</span>
    </div>

    <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-top:4px;">
      <span style="color:#FF5555; font-size:1.2rem; font-weight:900;">−</span>
      <span style="color:#F59E0B; font-size:1.05rem; font-weight:700;">재무부 계좌 (TGA)</span>
      <span style="color:#4A6888;">(WTREGEN)</span>
      <span style="background:#1A2A3F; padding:4px 12px; border-radius:6px; color:#FFFFFF; font-size:1.1rem; font-weight:700;">${latest_tga:.2f} T</span>
    </div>

    <div style="border-top:1px solid #1E3050; margin-top:12px; padding-top:12px; display:flex; align-items:center; gap:10px; flex-wrap:wrap;">
      <span style="color:#22D98A; font-size:1.2rem; font-weight:900;">=</span>
      <span style="color:#00D4FF; font-size:1.1rem; font-weight:800;">순유동성 (Net Liquidity)</span>
      <span style="background:rgba(0,212,255,0.15); border:1px solid #00D4FF55; padding:5px 16px; border-radius:8px; color:#00D4FF; font-size:1.25rem; font-weight:900;">${latest_nl:.2f} T</span>
      <span style="color:{nl_chg_color}; font-size:0.85rem; font-weight:700;">{nl_chg_arrow} {abs(nl_chg):.3f} T (주간 변화)</span>
    </div>

  </div>

  <!-- 해석 -->
  <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px;">
    <div style="background:#080E1A; border:1px solid #1A2A3F; border-radius:10px; padding:14px;">
      <div style="font-size:0.78rem; font-weight:700; color:#6B8EAE; letter-spacing:.08em; margin-bottom:8px;">S&P 500 최근 종가</div>
      <div style="font-family:'IBM Plex Mono',monospace; font-size:1.3rem; font-weight:700; color:#FF5555;">{latest_sp:,.0f}</div>
    </div>
    <div style="background:#080E1A; border:1px solid #1A2A3F; border-radius:10px; padding:14px;">
      <div style="font-size:0.78rem; font-weight:700; color:#6B8EAE; letter-spacing:.08em; margin-bottom:8px;">유동성 신호</div>
      <div style="font-family:'IBM Plex Mono',monospace; font-size:1.0rem; font-weight:700; color:{nl_chg_color};">
        {"📈 유동성 공급 확대" if nl_chg >= 0 else "📉 유동성 흡수 진행"}
      </div>
    </div>
  </div>

  <div style="margin-top:12px; font-size:0.78rem; color:#4A6888; line-height:1.6;">
    💡 순유동성이 증가하면 시장에 돈이 풀려 <b style="color:#00D4FF">주가 상승</b> 압력,
    감소하면 유동성 회수로 <b style="color:#FF5555">주가 조정</b> 가능성이 높아집니다.
  </div>

</div>
""", unsafe_allow_html=True)

        else:
            st.warning("⚠️ 병합된 데이터가 부족합니다.")
    else:
        st.warning("⚠️ FRED 데이터를 불러오지 못했습니다.")

except Exception as e:
    st.error(f"유동성 섹션 오류: {str(e)}")
