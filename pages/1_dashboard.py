import streamlit as st
from database import get_conn
import pandas as pd

st.title("Overview")
conn = get_conn()
uid = st.session_state.user_id

# Totalvärde
res = conn.query("SELECT SUM(market_value * quantity) as tot FROM collection WHERE user_id = :u", params={"u": uid})
total = res.iloc[0]['tot'] or 0.0
st.header(f"kr{total:,.2f} SEK")

# Graf
hist = conn.query("SELECT recorded_date, total_value FROM portfolio_history WHERE user_id = :u ORDER BY recorded_date", params={"u": uid})
if not hist.empty:
    st.area_chart(hist.set_index('recorded_date'), color="#00ff88")

    # Most Valuable
    st.write("### Most Valuable")
    top = conn.query("SELECT item_name, market_value, variant FROM collection WHERE user_id = :u ORDER BY market_value DESC LIMIT 5", params={"u": uid})
    for _, r in top.iterrows():
        st.markdown(f"**{r['item_name']}** ({r['variant']}) <span style='float:right;'>kr{r['market_value']}</span>", unsafe_allow_html=True)
        