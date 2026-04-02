import streamlit as st
from database import get_user_portfolio, get_user_sealed
from currency_utils import convert_price

st.title("Portfolio")
currency = st.session_state.currency
uid = st.session_state.user_id

df = get_user_portfolio(uid)

if not df.empty:
    # Gruppera för att visa antal (Quantity)
    # Vi grupperar på api_id OCH variant (e.g. 1 normal, 2 reverse)
    display_df = df.groupby(['api_id', 'variant', 'name', 'image_url', 'market_price']).size().reset_index(name='qty')
    
    cols = st.columns(4)
    for idx, row in display_df.iterrows():
        with cols[idx % 4]:
            # Applicera Holo-CSS baserat på variant
            var = row['variant']
            img = row['image_url']
            
            if "Reverse" in var:
                st.markdown(f'<div class="card-wrapper"><img src="{img}"><div class="reverse-holo-overlay"></div></div>', unsafe_allow_html=True)
            elif "Holo" in var:
                st.markdown(f'<div class="card-wrapper"><img src="{img}"><div class="holo-overlay"></div></div>', unsafe_allow_html=True)
            else:
                st.image(img, width="stretch")
            
            st.markdown(f"**{row['name']}**")
            val = convert_price(row['market_price'], currency)
            st.write(f"**{val:,.2f} {currency}**")
            st.caption(f"Antal: {row['qty']} | {var}")
            st.divider()
else:
    st.info("Din samling är tom.")