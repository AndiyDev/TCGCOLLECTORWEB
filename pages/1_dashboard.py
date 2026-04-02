import streamlit as st
from database import get_conn, get_portfolio_history, get_wishlist
import pandas as pd

st.title("Overview")
conn = get_conn()
uid = st.session_state.user_id

# Wishlist Alerts
w_df = get_wishlist(uid)
if not w_df.empty:
    alerts = w_df[w_df['current_price'] <= w_df['target_price']]
    if not alerts.empty:
        st.error(f"🔔 {len(alerts)} kort på din önskelista har nått ditt målpris!")

# Totalvärde
res = conn.query("SELECT SUM(market_value * quantity) as tot FROM collection WHERE user_id = :u", params={"u": uid})
total = res.iloc[0]['tot'] or 0.0
st.header(f"{total:,.2f} {st.session_state.currency}")

# Graf
hist = get_portfolio_history(uid)
if not hist.empty:
    st.area_chart(hist.set_index('recorded_date'), color="#00ff88")

# Most Valuable
st.write("### Most Valuable")
top = conn.query("SELECT item_name, market_value, variant, card_condition FROM collection WHERE user_id = :u ORDER BY market_value DESC LIMIT 5", params={"u": uid})
for _, r in top.iterrows():
    st.markdown(f"**{r['item_name']}** <span style='float:right;'>{r['market_value']} {st.session_state.currency}</span><br><small>{r['variant']} • {r['card_condition']}</small>", unsafe_allow_html=True)