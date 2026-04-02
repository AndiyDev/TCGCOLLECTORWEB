import streamlit as st
from database import get_conn, get_portfolio_history, get_wishlist
import pandas as pd
from currency_utils import convert_price

st.title("Overview")
conn = get_conn()
uid = st.session_state.user_id
currency = st.session_state.currency

# Wishlist Alerts
w_df = get_wishlist(uid)
if not w_df.empty:
    alerts = w_df[w_df['current_price'] <= w_df['target_price']]
    if not alerts.empty:
        st.error(f"🔔 {len(alerts)} kort på din önskelista har nått ditt målpris!")

# --- Totalvärde & ROI ---
res = conn.query("SELECT SUM(market_value * quantity) as tot_val, SUM(purchase_price * quantity) as tot_cost FROM collection WHERE user_id = :u", params={"u": uid})
total_value = res.iloc[0]['tot_val'] or 0.0
total_cost = res.iloc[0]['tot_cost'] or 0.0

total_value_curr = convert_price(total_value, currency)
total_cost_curr = convert_price(total_cost, currency)
profit = total_value_curr - total_cost_curr

col1, col2 = st.columns(2)
with col1:
    st.metric("Portfolio Value", f"{total_value_curr:,.2f} {currency}")
with col2:
    st.metric("Total Profit/Loss", f"{profit:,.2f} {currency}", delta=f"{(profit/total_cost_curr*100) if total_cost_curr > 0 else 0:.1f}%")

st.divider()

# Graf
hist = get_portfolio_history(uid)
if not hist.empty:
    st.area_chart(hist.set_index('recorded_date'), color="#00ff88")

# Most Valuable
st.write("### Most Valuable Cards")
top = conn.query("SELECT item_name, market_value, variant, grade_company, grade_value FROM collection WHERE user_id = :u ORDER BY market_value DESC LIMIT 5", params={"u": uid})
for _, r in top.iterrows():
    grade_info = f" • {r['grade_company']} {r['grade_value']}" if r['grade_company'] else ""
    local_val = convert_price(r['market_value'], currency)
    st.markdown(f"**{r['item_name']}** <span style='float:right;'>{local_val:,.2f} {currency}</span><br><small>{r['variant']}{grade_info}</small>", unsafe_allow_html=True)