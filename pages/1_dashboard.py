import streamlit as st
from database import get_user_collection

st.title("Dashboard")

df = get_user_collection(st.session_state.user_id)

if df.empty:
    st.info("Din portfölj är tom. Gå till 'Lägg till kort'.")
else:
    total_value = df['market_value'].sum()
    st.metric("Totalt Portföljvärde", f"{total_value:,.2f} kr")
    
    st.subheader("Översikt")
    # Visar en komprimerad tabell utan bild-URL
    st.dataframe(df[['item_name', 'market_value']], hide_index=True, use_container_width=True)
