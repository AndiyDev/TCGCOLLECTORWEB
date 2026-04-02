import streamlit as st
import requests
from database import add_to_collection, add_sealed_product

st.title("Add Products")

tab_cards, tab_sealed = st.tabs(["Search Cards", "Add Sealed Product"])

with tab_cards:
    query = st.text_input("Search card name or set...", placeholder="e.g. Charizard")
    if query:
        params = {"q": f'name:"{query}" OR set.name:"{query}"', "orderBy": "-set.releaseDate", "pageSize": 10}
        res = requests.get("https://api.pokemontcg.io/v2/cards", params=params)
        if res.status_code == 200:
            data = res.json().get('data', [])
            cols = st.columns(2)
            for i, card in enumerate(data):
                with cols[i % 2]:
                    st.image(card['images']['small'])
                    st.write(f"**{card['name']}**")
                    price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
                    if st.button("➕ Add Raw", key=f"n_{card['id']}"):
                        add_to_collection(st.session_state.user_id, card['id'], card['name'], card['set']['id'], card['number'], price, card['images']['small'])
                        st.toast("Tillagd!")
        else:
            st.error("API Error")

with tab_sealed:
    st.subheader("Manual Entry for Sealed Products")
    with st.form("sealed_form"):
        p_name = st.text_input("Product Name (e.g. 151 Elite Trainer Box)")
        p_type = st.selectbox("Type", ["Booster Box", "Elite Trainer Box", "Blister Pack", "Collection Box", "Special Set"])
        p_qty = st.number_input("Quantity", min_value=1, value=1)
        p_cost = st.number_input("Your Purchase Price (SEK)", min_value=0.0)
        p_market = st.number_input("Current Market Value (SEK)", min_value=0.0)
        p_img = st.text_input("Image URL (Right click an image online and 'Copy image address')")
        
        if st.form_submit_button("Add Sealed Product to Portfolio"):
            if p_name and p_img:
                add_sealed_product(st.session_state.user_id, p_name, p_type, p_qty, p_cost, p_market, p_img)
                st.success(f"{p_name} added!")
            else:
                st.warning("Please fill in name and image URL.")