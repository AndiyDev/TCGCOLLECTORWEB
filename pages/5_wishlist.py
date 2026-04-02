import streamlit as st
import requests
from database import add_to_wishlist, get_wishlist, delete_from_wishlist
from currency_utils import convert_price

st.title("🎯 Wishlist")
currency = st.session_state.currency

with st.expander("Lägg till i önskelista"):
    search = st.text_input("Sök kort att bevaka")
    if st.button("Sök"):
        res = requests.get(f"https://api.pokemontcg.io/v2/cards?q=name:\"{search}\"&pageSize=5").json()
        for card in res.get("data", []):
            col1, col2 = st.columns([1, 3])
            price = card.get("cardmarket", {}).get("prices", {}).get("averageSellPrice", 0.0)
            with col1:
                st.image(card["images"]["small"])
            with col2:
                st.write(f"**{card['name']}**")
                target = st.number_input(f"Målpris ({currency})", key=f"targ_{card['id']}")
                if st.button("Bevaka", key=f"btn_{card['id']}"):
                    add_to_wishlist(st.session_state.user_id, card['name'], card['set']['id'], card['number'], target, price, card["images"]["small"])
                    st.success("Tillagd!")

st.divider()
w_df = get_wishlist(st.session_state.user_id)
for _, row in w_df.iterrows():
    c1, c2, c3 = st.columns([1, 2, 1])
    with c1:
        st.image(row["image_url"])
    with c2:
        st.write(f"**{row['item_name']}**")
        st.write(f"Target: {row['target_price']} | Nu: {row['current_price']} EUR")
        if row['current_price'] <= row['target_price']:
            st.success("🔥 Pris nått!")
    with c3:
        if st.button("🗑️", key=f"delw_{row['id']}"):
            delete_from_wishlist(row['id'], st.session_state.user_id)
            st.rerun()