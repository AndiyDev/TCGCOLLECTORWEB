import streamlit as st
from database import get_user_portfolio, get_user_sealed
from currency_utils import convert_price

# 1. Säkerhetsspärr - Stoppa sidan om användaren inte är inloggad
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

st.title("My Collection & Portfolio")

# Hämta användarens inställningar
currency = st.session_state.get("currency", "SEK")
uid = st.session_state.user_id

# Skapa flikar för att separera kort och oöppnade boxar
tab_cards, tab_sealed = st.tabs(["🎴 Single Cards", "📦 Sealed Products"])

# --- FLIK 1: SINGLE CARDS ---
with tab_cards:
    df = get_user_portfolio(uid)

    if df.empty:
        st.info("Din samling är tom. Gå till 'Sets' för att lägga till dina första kort!")
    else:
        # Gruppera korten så att vi ser antal (Quantity) per variant
        # Vi grupperar på api_id, variant och namn för att visa dem snyggt
        display_df = df.groupby(['api_id', 'variant', 'name', 'image_url', 'market_price', 'set_name']).size().reset_index(name='qty')
        
        # Visa statistik högst upp
        total_items = df.shape[0]
        total_value = (df['market_price']).sum()
        local_total = convert_price(total_value, currency)
        
        col_stat1, col_stat2 = st.columns(2)
        col_stat1.metric("Totalt antal kort", f"{total_items} st")
        col_stat2.metric("Portföljvärde (Marknad)", f"{local_total:,.2f} {currency}")
        
        st.divider()

        # Rita ut korten i ett rutnät
        cols = st.columns(4)
        for idx, row in display_df.iterrows():
            with cols[idx % 4]:
                variant = row['variant']
                img_url = row['image_url']
                
                # Applicera Holo/Reverse-effekt baserat på varianten i databasen
                if "Reverse" in variant:
                    st.markdown(f"""
                        <div class="card-wrapper">
                            <img src="{img_url}" style="width:100%">
                            <div class="reverse-holo-overlay"></div>
                        </div>
                    """, unsafe_allow_html=True)
                elif "Holo" in variant:
                    st.markdown(f"""
                        <div class="card-wrapper">
                            <img src="{img_url}" style="width:100%">
                            <div class="holo-overlay"></div>
                        </div>
                    """, unsafe_allow_html=True)
                else:
                    st.image(img_url, use_container_width=True)

                # Kortinfo
                st.markdown(f"**{row['name']}**")
                st.caption(f"{row['set_name']}")
                
                # Pris i vald valuta
                price_local = convert_price(row['market_price'], currency)
                st.write(f"**{price_local:,.2f} {currency}**")
                
                # Visa mängd och variant som en liten badge
                st.markdown(f"""
                    <div style="display: flex; gap: 5px; margin-top: 5px;">
                        <span style="background: #333; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">x{row['qty']}</span>
                        <span style="background: #1e1e1e; border: 1px solid #444; padding: 2px 8px; border-radius: 4px; font-size: 0.8rem;">{variant}</span>
                    </div>
                """, unsafe_allow_html=True)
                
                st.divider()

# --- FLIK 2: SEALED PRODUCTS ---
with tab_sealed:
    sealed_df = get_user_sealed(uid)
    
    if sealed_df.empty:
        st.info("Inga oöppnade produkter registrerade.")
    else:
        cols_s = st.columns(3)
        for idx, row in sealed_df.iterrows():
            with cols_s[idx % 3]:
                st.image(row['image_url'], use_container_width=True)
                st.subheader(row['product_name'])
                st.write(f"Typ: {row['product_type']}")
                st.write(f"Antal: {row['quantity']}")
                
                m_val = convert_price(row['market_value'], currency)
                st.write(f"Marknadsvärde: **{m_val:,.2f} {currency}**")
                st.divider()