import streamlit as st
import requests
from database import add_to_collection

st.title("Search Products")
query = st.text_input("Search name or set...", placeholder="e.g. 151")

if query:
    data = requests.get(f"https://api.pokemontcg.io/v2/cards?q=name:\"{query}\" OR set.name:\"{query}\"&pageSize=10").json().get('data', [])
        
            cols = st.columns(2)
                for i, card in enumerate(data):
                        with cols[i % 2]:
                                    st.image(card['images']['small'])
                                                st.write(f"**{card['name']}**")
                                                            price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
                                                                        
                                                                                    if st.button("Add Normal", key=f"n_{card['id']}"):
                                                                                                    add_to_collection(st.session_state.user_id, card['id'], card['name'], card['set']['id'], card['number'], price, card['images']['small'], "Normal")
                                                                                                                    st.toast("Added!")
                                                                                                                                
                                                                                                                                            if st.button("Add Reverse", key=f"r_{card['id']}"):
                                                                                                                                                            add_to_collection(st.session_state.user_id, card['id'], card['name'], card['set']['id'], card['number'], price*1.2, card['images']['small'], "Reverse Holo")
                                                                                                                                                                            st.toast("Added!")
                                                                                                                                                                            