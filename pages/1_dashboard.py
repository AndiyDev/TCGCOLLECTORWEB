import streamlit as st
import pandas as pd
from database import get_user_portfolio, get_user_sealed, get_portfolio_history, get_wishlist
from currency_utils import convert_price

# Säkerhetsspärr
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in först.")
    st.stop()

st.title(f"Välkommen, {st.session_state.username}! 👋")
currency = st.session_state.get("currency", "SEK")
uid = st.session_state.user_id

# 1. Hämta data
df_cards = get_user_portfolio(uid)
df_sealed = get_user_sealed(uid)
df_history = get_portfolio_history(uid)

# 2. Beräkna värden
val_cards = df_cards['market_price'].sum() if not df_cards.empty else 0.0
val_sealed = (df_sealed['market_value'] * df_sealed['quantity']).sum() if not df_sealed.empty else 0.0
total_val = val_cards + val_sealed

# 3. Visa Metrics
c1, c2, c3 = st.columns(3)
c1.metric("Totalt Värde", f"{convert_price(total_val, currency):,.2f} {currency}")
c2.metric("Antal Kort", f"{len(df_cards)} st")
c3.metric("Sealed Items", f"{int(df_sealed['quantity'].sum()) if not df_sealed.empty else 0} st")

st.divider()

# 4. Graf över portföljens utveckling
st.subheader("Portföljens Utveckling")
if not df_history.empty:
    df_history['recorded_date'] = pd.to_datetime(df_history['recorded_date'])
    # Konvertera historiska värden till vald valuta (förenklat)
    df_history['value_local'] = df_history['total_value'].apply(lambda x: convert_price(x, currency))
    st.line_chart(df_history.set_index('recorded_date')['value_local'])
else:
    st.info("Kör en 'Sync Prices' för att börja bygga din historik-graf!")

# 5. Prisbevakning (Wishlist Alerts)
st.divider()
st.subheader("🎯 Prisbevakning & Alerts")
wish_df = get_wishlist(uid)

if not wish_df.empty:
    # Kolla om något kort på wishlist ligger under målpris
    alerts = wish_df[wish_df['current_price'] <= wish_df['target_price']]
    if not alerts.empty:
        for _, row in alerts.iterrows():
            st.success(f"🔥 KÖPLÄGE: {row['item_name']} ligger nu på {convert_price(row['current_price'], currency):,.2f} {currency}!")
    else:
        st.write("Inga aktiva reor just nu. Vi bevakar marknaden åt dig...")
else:
    st.write("Din wishlist är tom.")