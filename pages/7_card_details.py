import streamlit as st
import requests
import pandas as pd
from database import update_quantity, add_to_collection
from currency_utils import convert_price

card_id = st.query_params.get("card_id")
if not card_id:
    st.error("Inget kort valt.")
    st.stop()

@st.cache_data
def get_card(cid):
    res = requests.get(f"https://api.pokemontcg.io/v2/cards/{cid}")
    if res.status_code == 200:
        return res.json().get("data")
    return None

card = get_card(card_id)
if not card:
    st.error("Kunde inte hämta kortdata.")
    st.stop()

if st.button("← Back to Portfolio"):
    st.switch_page("pages/2_collection.py")

c1, c2 = st.columns([1, 1])
with c1:
    st.image(card['images']['large'], use_container_width=True)
with c2:
    st.title(card['name'])
    st.caption(f"{card['set']['name']} • {card['number']}")
    
    base_price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
    local_price = convert_price(base_price, st.session_state.currency)
    st.subheader(f"{local_price:,.2f} {st.session_state.currency}")

    # --- Smarta Marknadsplatslänkar (Din logik) ---
    st.write("🔍 **Sök på marknadsplatser:**")
    
    # Bygg söksträngar
    raw_search = f"{card['name']} {card['set']['name']} {card['number']}"
    search_q = raw_search.replace(" ", "+")
    cm_search = card['name'].replace(' ', '+')
    
    col_links1, col_links2, col_links3 = st.columns(3)
    with col_links1:
        st.link_button("Cardmarket", f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={cm_search}", use_container_width=True)
    with col_links2:
        st.link_button("Tradera", f"https://www.tradera.com/search?q={search_q}", use_container_width=True)
    with col_links3:
        st.link_button("eBay", f"https://www.ebay.com/sch/i.html?_nkw={search_q}", use_container_width=True)

    st.divider()

    st.divider()
    st.write("### Manage Quantity")
    
    def qty_row(variant_name, price_mult=1.0):
        c_name, c_minus, c_plus = st.columns([2, 1, 1])
        with c_name:
            st.write(f"**{variant_name}**")
        with c_minus:
            if st.button("−", key=f"min_{variant_name}"):
                update_quantity(st.session_state.user_id, card_id, variant_name, -1)
                st.toast("Uppdaterad!")
        with c_plus:
            if st.button("➕", key=f"add_{variant_name}"):
                add_to_collection(
                    st.session_state.user_id, card_id, card['name'], 
                    card['set']['id'], card['number'], base_price * price_mult, 
                    card['images']['small'], variant_name, 1
                )
                st.toast("Tillagd!")

    qty_row("Normal", 1.0)
    qty_row("Reverse Holofoil", 1.2)