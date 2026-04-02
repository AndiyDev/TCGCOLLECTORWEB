import streamlit as st
import requests
from database import add_to_collection

st.title("Search Products")
query = st.text_input("Search name or set...", placeholder="e.g. Charizard")

if query:
    api_url = f"https://api.pokemontcg.io/v2/cards?q=name:*{query}* OR set.name:*{query}*&orderBy=-set.releaseDate&pageSize=10"
    
    # Den här raden saknades! Det är den som faktiskt hämtar datan.
    res = requests.get(api_url)
    
    if res.status_code == 200:
        data = res.json().get('data', [])
        
        if not data:
            st.warning("Inga kort hittades. Testa en annan sökning.")
            
        cols = st.columns(2)
        for i, card in enumerate(data):
            with cols[i % 2]:
                st.image(card['images']['small'])
                st.write(f"**{card['name']}**")
                st.caption(f"{card['set']['name']} • {card['number']}")
                price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
                
                if st.button("➕ Add Normal", key=f"n_{card['id']}"):
                    add_to_collection(st.session_state.user_id, card['id'], card['name'], card['set']['id'], card['number'], price, card['images']['small'], "Normal")
                    st.toast(f"{card['name']} (Normal) tillagd!")
                
                if st.button("➕ Add Reverse Holo", key=f"r_{card['id']}"):
                    add_to_collection(st.session_state.user_id, card['id'], card['name'], card['set']['id'], card['number'], price * 1.2, card['images']['small'], "Reverse Holofoil")
                    st.toast(f"{card['name']} (Reverse Holo) tillagd!")
    else:
        st.error("Kunde inte nå API:et.")