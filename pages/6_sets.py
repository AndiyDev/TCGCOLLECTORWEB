import streamlit as st
import requests
from database import get_user_portfolio, add_item_to_user

if not st.session_state.get("logged_in"): st.stop()

@st.cache_data(ttl=3600)
def get_cards(sid):
    r = requests.get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{sid}&orderBy=number")
    return r.json().get('data', []) if r.status_code == 200 else []

@st.dialog("Lägg till kort")
def add_card_ui(card):
    var = st.selectbox("Variant", ["Normal", "Reverse Holo", "Holo"])
    price = st.number_input("Inköpspris", 0.0)
    if st.button("Spara"):
        add_item_to_user(st.session_state.user_id, card, var, price)
        st.rerun()

# Logik för att välja set...
sid = st.query_params.get("set_id")
if sid:
    cards = get_cards(sid); p = get_user_portfolio(st.session_state.user_id)
    cols = st.columns(4)
    for i, c in enumerate(cards):
        with cols[i%4]:
            owned = len(p[p['api_id'] == c['id']]) if not p.empty else 0
            if owned > 0: st.success(f"Äger: {owned}")
            st.image(c['images']['small'])
            if st.button(f"Visa {c['name']}", key=c['id']): add_card_ui(c)
else:
    st.write("Välj ett set...") # Lägg till din Set-lista här