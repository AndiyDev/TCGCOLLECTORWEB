import streamlit as st
import requests
from database import get_wishlist, add_to_wishlist, delete_from_wishlist
from currency_utils import convert_price

st.title("🎯 Wishlist & Price Alerts")
st.write("Sätt ett målpris på kort du letar efter. Om marknadspriset sjunker under din gräns får du en notis!")

currency = st.session_state.currency

# --- LÄGG TILL ---
with st.expander("➕ Sök och lägg till kort för bevakning", expanded=False):
    query = st.text_input("Sök kortnamn...")
    if query:
        params = {"q": f'name:"{query}" OR set.name:"{query}"', "orderBy": "-set.releaseDate", "pageSize": 5}
        res = requests.get("https://api.pokemontcg.io/v2/cards", params=params)
        if res.status_code == 200:
            data = res.json().get('data', [])
            cols = st.columns(5)
            for i, card in enumerate(data):
                with cols[i % 5]:
                    st.image(card['images']['small'], width="stretch")
                    base_price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
                    local_price = convert_price(base_price, currency)
                    
                    st.caption(f"Nu: {local_price:,.2f} {currency}")
                    target_local = st.number_input("Ditt maxpris", min_value=0.0, value=float(local_price), key=f"t_{card['id']}")
                    
                    if st.button("Bevaka", key=f"w_{card['id']}"):
                        # Konvertera målet tillbaka till basvalutan i bakgrunden så larmet fungerar oavsett vilken valuta man har
                        ratio = base_price / local_price if local_price > 0 else 1
                        target_base = target_local * ratio
                        
                        add_to_wishlist(st.session_state.user_id, card['name'], card['set']['name'], card['number'], target_base, base_price, card['images']['small'])
                        st.success("Tillagd!")
                        st.rerun()

st.divider()

# --- VISA ÖNSKELISTAN ---
df = get_wishlist(st.session_state.user_id)
if not df.empty:
    cols = st.columns(4)
    for idx, row in df.iterrows():
        with cols[idx % 4]:
            st.image(row['image_url'], width="stretch")
            st.markdown(f"**{row['item_name']}**")
            
            c_price = convert_price(row['current_price'], currency)
            t_price = convert_price(row['target_price'], currency)
            
            st.write(f"Nuvarande: **{c_price:,.2f}** {currency}")
            
            # Kolla om det är köpläge
            if c_price <= t_price:
                st.success(f"Mål: {t_price:,.2f} {currency} 📉 Köpläge!")
            else:
                st.warning(f"Mål: {t_price:,.2f} {currency}")
                
            if st.button("🗑️ Ta bort", key=f"delw_{row['id']}"):
                delete_from_wishlist(row['id'], st.session_state.user_id)
                st.rerun()
else:
    st.info("Din önskelista är tom. Dags att jaga lite grails!")