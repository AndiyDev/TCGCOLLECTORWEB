import streamlit as st
import requests
import pandas as pd
from database import update_quantity, add_to_collection, get_user_collection
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
    st.image(card['images']['large'], width="stretch")
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
        st.link_button("Cardmarket", f"https://www.cardmarket.com/en/Pokemon/Products/Search?searchString={cm_search}", width="stretch")
    with col_links2:
        st.link_button("Tradera", f"https://www.tradera.com/search?q={search_q}", width="stretch")
    with col_links3:
        st.link_button("eBay", f"https://www.ebay.com/sch/i.html?_nkw={search_q}", width="stretch")

    st.divider()

    # --- LÄGG TILL KORT (Raw & Graded) ---
    st.write("### Add to Collection")
    tab_raw, tab_graded = st.tabs(["Raw (Ograderad)", "Graded (PSA/BGS/CGC)"])
    
    with tab_raw:
        var_sel = st.selectbox("Variant", ["Normal", "Reverse Holofoil", "Holofoil"], key="raw_var")
        p_price = st.number_input(f"Inköpspris (Valfritt) i {st.session_state.currency}", min_value=0.0, format="%.2f", key="raw_price")
        
        if st.button("➕ Lägg till i samling", key="btn_raw"):
            # Konvertera inköpspris tillbaka till basvalutan (EUR/USD beroende på system) vid sparande, eller spara direkt. 
            # För enkelhetens skull sparar vi inköpspriset direkt som input nu.
            price_mult = 1.2 if "Holo" in var_sel else 1.0
            add_to_collection(st.session_state.user_id, card_id, card['name'], card['set']['id'], card['number'], base_price * price_mult, card['images']['small'], var_sel, 1, p_price)
            st.success("Tillagd i samlingen!")
            
    with tab_graded:
        g_comp = st.selectbox("Företag", ["PSA", "BGS", "CGC", "SGC"], key="g_comp")
        g_val = st.selectbox("Betyg (Grade)", ["10", "9.5", "9", "8", "7", "6", "5", "4", "3", "2", "1"], key="g_val")
        cert_num = st.text_input("Certifikatnummer (Valfritt)", key="g_cert")
        p_price_g = st.number_input(f"Inköpspris i {st.session_state.currency}", min_value=0.0, format="%.2f", key="g_price")
        
        # Graderade kort är ofta värda 2-10x mer än ograderade. Låt användaren justera marknadsvärdet.
        est_val = st.number_input("Estimerat Marknadsvärde (API visar bara raw)", value=float(local_price*3), format="%.2f", key="g_est")
        
        if st.button("➕ Lägg till Graderat Kort", key="btn_graded"):
            add_to_collection(st.session_state.user_id, card_id, card['name'], card['set']['id'], card['number'], est_val, card['images']['small'], "Normal", 1, p_price_g, True, g_comp, g_val, cert_num)
            st.success("Graderat kort tillagt!")

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