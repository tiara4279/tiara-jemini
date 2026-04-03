# ═══════════════════════════════════════════════════════════
#  §9 Net Liquidity (수정본)
# ═══════════════════════════════════════════════════════════
sec("🌊", "미국 핵심 유동성 흐름 (Net Liquidity)")
st.caption("Net Liquidity와 주식 시장(S&P 500)의 상관관계를 파악합니다.")

try:
    walcl = get_fred('WALCL', limit=300)
    rrp = get_fred('RRPONTSYD', limit=300)
    tga = get_fred('WTREGEN', limit=300)
    _, _, sp500_df = get_yf('^GSPC', period='1y', interval='1d')
    
    if all([walcl is not None, rrp is not None, tga is not None, sp500_df is not None and len(sp500_df) > 10]):
        try:
            walcl_b = walcl / 1000.0
            rrp_b = rrp / 1000.0
            tga_b = tga / 1000.0
            
            df_liq = pd.DataFrame({
                'WALCL': walcl_b,
                'RRP': rrp_b,
                'TGA': tga_b
            })
            df_liq['Net_Liquidity'] = df_liq['WALCL'] - df_liq['RRP'] - df_liq['TGA']
            
            sp500_s = sp500_df['Close'].copy()
            if hasattr(sp500_s.index, 'tz') and sp500_s.index.tz is not None:
                sp500_s.index = sp500_s.index.tz_localize(None)
            
            df_liq.index = pd.to_datetime(df_liq.index).normalize()
            sp500_s.index = pd.to_datetime(sp500_s.index).normalize()
            
            df_plot = df_liq[['Net_Liquidity']].join(sp500_s.rename('Close'), how='inner').dropna()
            
            if len(df_plot) > 10:
                fig_liq = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig_liq.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['Net_Liquidity'], name="순유동성 (T$)",
                               line=dict(color='#00D4FF', width=2.5)),
                    secondary_y=False
                )
                fig_liq.add_trace(
                    go.Scatter(x=df_plot.index, y=df_plot['Close'], name="S&P 500",
                               line=dict(color='#FF5555', width=1.5)),
                    secondary_y=True
                )
                
                # ✅ height 제거! (CHART_LAYOUT에 이미 포함됨)
                fig_liq.update_layout(
                    **CHART_LAYOUT,
                    title_text="Net Liquidity vs S&P 500 (최근 1년)"
                )
                fig_liq.update_yaxes(title_text="순유동성 (T$)", secondary_y=False, color="#00D4FF")
                fig_liq.update_yaxes(title_text="S&P 500", secondary_y=True, color="#FF5555")
                
                st.plotly_chart(fig_liq, use_container_width=True, config={'displayModeBar': False})
                
                st.markdown("""<div style="background: #0C1420; border: 1px solid #1E3050; border-radius: 12px; padding: 16px; margin-bottom: 30px;">
                <div style="font-size: 0.9rem; font-weight: 700; color:#00D4FF; margin-bottom: 8px;">📌 Net Liquidity 공식</div>
                <div style="font-family:'IBM Plex Mono'; font-size: 0.85rem; color:#AACCEE; margin-bottom: 12px; background:#060A12; padding:10px; border-radius:6px;">
                순유동성 = 연준 총자산(WALCL) - 역레포(RRPONTSYD) - TGA(WTREGEN)
                </div>
                <div style="font-size: 0.8rem; color: #8AAAC8; line-height: 1.6;">
                파란선(순유동성)이 오르면 S&P 500도 함께 오르고, 내리면 조정을 받는 강한 양(+)의 상관관계를 보입니다.
                </div></div>""", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ 차트 생성 오류: {str(e)}")
    else:
        st.warning("⚠️ 필요한 데이터를 불러오지 못했습니다.")
except Exception as e:
    st.error(f"유동성 섹션 오류: {str(e)}")


# ═══════════════════════════════════════════════════════════
#  §10 국채금리 분해 (수정본)
# ═══════════════════════════════════════════════════════════
sec("🇺🇸", "미국 10년물 국채금리 분해")
st.caption("국채금리 구성 요소를 분석합니다.")

try:
    dgs10 = get_fred('DGS10', limit=300)
    t10yie = get_fred('T10YIE', limit=300)
    dfedtru = get_fred('DFEDTRU', limit=300)
    
    if all([dgs10 is not None, t10yie is not None, dfedtru is not None]):
        try:
            df_dec = pd.DataFrame({
                '10Y': dgs10,
                'T10YIE': t10yie,
                'DFEDTRU': dfedtru
            }).ffill().dropna()
            
            df_dec['Term_Premium'] = df_dec['10Y'] - df_dec['DFEDTRU'] - df_dec['T10YIE']
            
            if len(df_dec) > 20:
                fig_dec = make_subplots(specs=[[{"secondary_y": True}]])
                
                fig_dec.add_trace(
                    go.Scatter(x=df_dec.index, y=df_dec['10Y'], name="10Y 금리",
                               line=dict(color='#3B82F6', width=2.5)),
                    secondary_y=False
                )
                fig_dec.add_trace(
                    go.Scatter(x=df_dec.index, y=df_dec['DFEDTRU'], name="단기금리 (FFR)",
                               line=dict(color='#06B6D4', width=1.5)),
                    secondary_y=False
                )
                fig_dec.add_trace(
                    go.Scatter(x=df_dec.index, y=df_dec['T10YIE'], name="기대인플레이션",
                               line=dict(color='#8AAAC8', width=1.5)),
                    secondary_y=False
                )
                fig_dec.add_trace(
                    go.Scatter(x=df_dec.index, y=df_dec['Term_Premium'], name="기간 프리미엄",
                               line=dict(color='#F59E0B', width=2.5)),
                    secondary_y=True
                )
                
                # ✅ height 제거! (CHART_LAYOUT에 이미 포함됨)
                fig_dec.update_layout(
                    **CHART_LAYOUT,
                    title_text="10년물 국채금리 분해"
                )
                fig_dec.update_yaxes(title_text="금리 (%)", secondary_y=False, color="#AACCEE")
                fig_dec.update_yaxes(title_text="기간 프리미엄 (%p)", secondary_y=True, color="#F59E0B", showgrid=False)
                
                st.plotly_chart(fig_dec, use_container_width=True, config={'displayModeBar': False})
                
                st.markdown("""<div style="background: #0C1420; border: 1px solid #1E3050; border-radius: 12px; padding: 16px; margin-bottom: 30px;">
                <div style="font-size: 0.9rem; font-weight: 700; color:#00D4FF; margin-bottom: 8px;">📌 금리 분해 공식</div>
                <div style="font-family:'IBM Plex Mono'; font-size: 0.8rem; color:#AACCEE; margin-bottom: 12px; background:#060A12; padding:10px; border-radius:6px; line-height:1.6;">
                10Y = 단기금리(FFR) + 기대인플레이션 + 기간 프리미엄
                </div></div>""", unsafe_allow_html=True)
        except Exception as e:
            st.warning(f"⚠️ 차트 생성 오류: {str(e)}")
    else:
        st.warning("⚠️ 필요한 데이터를 불러오지 못했습니다.")
except Exception as e:
    st.error(f"금리 분해 섹션 오류: {str(e)}")
