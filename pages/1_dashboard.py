import streamlit as st
import pandas as pd
from database import get_user_portfolio, get_user_sealed, get_portfolio_history, get_wishlist
from currency_utils import convert_price

if not st.session_state.get("logged_in"): st.stop()

st.title(f"Dashboard - {st.session_state.username}")
uid = st.session_state.user_id; curr = st.session_state.currency

df_p = get_user_portfolio(uid); df_s = get_user_sealed(uid); df_h = get_portfolio_history(uid)

val_p = df_p['market_price'].sum() if not df_p.empty else 0
val_s = (df_s['market_value'] * df_s['quantity']).sum() if not df_s.empty else 0
total = val_p + val_s

c1, c2, c3 = st.columns(3)
c1.metric("Värde", f"{convert_price(total, curr):,.0f} {curr}")
c2.metric("Kort", f"{len(df_p)} st")
c3.metric("Sealed", f"{int(df_s['quantity'].sum()) if not df_s.empty else 0} st")

if not df_h.empty:
    st.line_chart(df_h.set_index('recorded_date')['total_value'])
else:
    st.info("Kör en synk för att se din graf!")