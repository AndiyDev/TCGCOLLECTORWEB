import streamlit as st
import pandas as pd
from database import get_user_portfolio, get_user_sealed, get_portfolio_history, get_wishlist
from currency_utils import convert_price

# 1. SÄKERHETSSPÄRR - Förhindrar krasch om sessionen dör
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

st.title(f"Dashboard - {st.session_state.username} 👋")

# Hämta globala inställningar
currency = st.session_state.get("currency", "SEK")
uid = st.session_state.user_id

# --- DATAHÄMTNING ---
# Vi hämtar all data parallellt för att bygga översikten
df_cards = get_user_portfolio(uid)
df_sealed = get_user_sealed(uid)
df_history = get_portfolio_history(uid)
df_wish = get_wishlist(uid)

# --- BERÄKNINGAR ---
# Räknar ut totalvärdet baserat på marknadspriser (i basvaluta, konverteras sen)
val_cards = df_cards['market_price'].sum() if not df_cards.empty else 0.0
val_sealed = (df_sealed['market_value'] * df_sealed['quantity']).sum() if not df_sealed.empty else 0.0
total_market_val = val_cards + val_sealed

# Räknar ut total vinst/förlust (ROI) om inköpspris finns angivet
# För kort: Marknadsvärde minus vad man faktiskt betalade
purchase_cards = df_cards['purchase_price'].sum() if not df_cards.empty else 0.0
roi_val = val_cards - purchase_cards

# --- METRICS (Huvudstatistik) ---
st.write("### Din Portfölj i siffror")
m1, m2, m3, m4 = st.columns(4)

with m1:
    st.metric("Totalvärde", f"{convert_price(total_market_val, currency):,.0f} {currency}")
with m2:
    st.metric("Antal Kort", f"{len(df_cards)} st")
with m3:
    st.metric("Sealed Items", f"{int(df_sealed['quantity'].sum()) if not df_sealed.empty else 0} st")
with m4:
    # Visa ROI i grönt eller rött beroende på vinst/förlust
    st.metric("Total ROI (Cards)", f"{convert_price(roi_val, currency):,.0f} {currency}", 
              delta=f"{convert_price(roi_val, currency):,.2f}", delta_color="normal")

st.divider()

# --- GRAF: Portföljens Utveckling ---
st.subheader("📈 Portföljens värdeutveckling")
if not df_history.empty:
    # Skapa en kopia för grafen och konvertera datum
    chart_data = df_history.copy()
    chart_data['recorded_date'] = pd.to_datetime(chart_data['recorded_date'])
    
    # Konvertera värdet i grafen till användarens valda valuta
    chart_data['value_local'] = chart_data['total_value'].apply(lambda x: convert_price(x, currency))
    
    # Rita ut grafen
    st.line_chart(chart_data.set_index('recorded_date')['value_local'], use_container_width=True)
else:
    st.info("Ingen historik tillgänglig än. Kör 'Sync Prices' för att börja logga ditt värde över tid!")

st.divider()

# --- ALERTS & WISHLIST ---
c_left, c_right = st.columns([2, 1])

with c_left:
    st.subheader("🎯 Prisbevakning")
    if not df_wish.empty:
        # Loopa igenom önskelistan och kolla efter "Deals"
        for _, row in df_wish.iterrows():
            curr_p = convert_price(row['current_price'], currency)
            targ_p = convert_price(row['target_price'], currency)
            
            if curr_p <= targ_p:
                st.success(f"🔥 **KÖPLÄGE:** {row['item_name']} ligger nu på {curr_p:,.2f} {currency} (Mål: {targ_p:,.2f})")
            else:
                st.write(f"⏳ {row['item_name']}: {curr_p:,.2f} {currency} (Väntar på {targ_p:,.2f})")
    else:
        st.write("Inga kort i din wishlist än.")

with c_right:
    st.subheader("📂 Senast tillagda")
    if not df_cards.empty:
        # Visa de 5 senast tillagda korten
        latest = df_cards.sort_values(by='date_added', ascending=False).head(5)
        for _, card in latest.iterrows():
            st.markdown(f"- **{card['name']}** ({card['variant']})")
    else:
        st.write("Samlingen är tom.")