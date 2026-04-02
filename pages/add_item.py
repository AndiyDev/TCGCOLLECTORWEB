import streamlit as st
import time
import pandas as pd
from database import get_conn, add_item_to_user, create_booster_opening, init_db
from sqlalchemy import text

# Säkerställ databas-v5
init_db()

st.set_page_config(page_title="Add Items", page_icon="➕", layout="wide")

# --- SESSION STATE FÖR ANIMATION ---
if "opening_results" not in st.session_state:
    st.session_state.opening_results = None

st.title("➕ Add to Collection")

# --- NAVBAR / FLIKAR ---
mode = st.radio("Välj metod:", ["Sök & Lägg till Singel", "📦 Öppna Booster Pack"], horizontal=True)

st.divider()

# --- MODUS 1: SÖK & LÄGG TILL SINGEL ---
if mode == "Sök & Lägg till Singel":
    col1, col2 = st.columns([2, 1])
    
    with col1:
        query = st.text_input("Sök i ditt Master-arkiv", placeholder="Namn eller kortnummer (t.ex. Pikachu)")
        
        if query:
            conn = get_conn()
            # SÄKER SÖKNING:
            search_results = conn.query("""
                SELECT * FROM global_cards 
                WHERE name LIKE :term OR card_number = :term_exact
                LIMIT 20
            """, params={"term": f"%{query}%", "term_exact": query})

            if not search_results.empty:
                for _, card in search_results.iterrows():
                    with st.container(border=True):
                        c_img, c_info = st.columns([1, 3])
                        c_img.image(card['image_url'], width=120)
                        with c_info:
                            st.subheader(f"{card['name']} (#{card['card_number']})")
                            st.caption(f"Set ID: {card['set_intern_id']} | HP: {card['hp']}")
                            
                            # Inställningar för ditt exemplar
                            v_col, c_col, p_col = st.columns(3)
                            variant = v_col.selectbox("Variant", ["Normal", "Holo", "Reverse"], key=f"var_{card['api_id']}")
                            condition = c_col.selectbox("Skick", ["NM", "EX", "GD", "LP", "PL"], index=0, key=f"cond_{card['api_id']}")
                            price = p_col.number_input("Inköpspris (SEK)", min_value=0.0, key=f"pri_{card['api_id']}")
                            
                            is_bought = st.toggle("Är detta ett köp?", value=True, key=f"tog_{card['api_id']}")
                            
                            if st.button("💾 Spara till Portfolio", key=f"btn_{card['api_id']}", type="primary"):
                                uid = add_item_to_user(
                                    st.session_state.user_id, 
                                    card['api_id'], 
                                    variant=variant, 
                                    condition=condition, 
                                    price=price, 
                                    is_bought=is_bought
                                )
                                st.success(f"Sparad! Unique ID: {uid}")
            else:
                st.warning("Hittade inget i arkivet. Importera setet i 'Sets Manager' först!")

# --- MODUS 2: BOOSTER OPENING ---
else:
    st.subheader("📦 Digital Booster Opening")
    
    conn = get_conn()
    available_sets = conn.query("SELECT set_intern_id, set_name FROM global_sets")
    
    with st.expander("1. Konfigurera din Booster", expanded=True):
        col_s, col_p = st.columns(2)
        selected_set = col_s.selectbox("Välj Set", available_sets['set_name'])
        set_id = available_sets[available_sets['set_name'] == selected_set]['set_intern_id'].values[0]
        pack_price = col_p.number_input("Vad betalade du för packat? (SEK)", min_value=0.0, value=65.0)
        
        st.write("### Skriv in kortnumren (1-10)")
        input_cols = st.columns(5)
        card_numbers = []
        for i in range(10):
            num = input_cols[i % 5].text_input(f"Kort {i+1}", key=f"card_in_{i}")
            card_numbers.append(num)

    if st.button("✨ ÖPPNA BOOSTER ✨", type="primary", use_container_width=True):
        # Validering
        valid_cards = []
        error = False
        for num in card_numbers:
            res = conn.query("SELECT * FROM global_cards WHERE set_intern_id = :sid AND card_number = :num", 
                             params={"sid": set_id, "num": num})
            if res.empty:
                st.error(f"Kort nummer {num} hittades inte i {selected_set}!")
                error = True
                break
            valid_cards.append(res.iloc[0])
        
        if not error:
            # 1. Skapa Booster-id i databasen
            opening_id = create_booster_opening(st.session_state.user_id, set_id, pack_price)
            
            # 2. Animation
            placeholder = st.empty()
            skip_anim = st.checkbox("Skippa animation")
            
            opened_cards_data = []
            total_value = 0
            
            for i, card in enumerate(valid_cards):
                # Spara i databasen direkt
                add_item_to_user(
                    st.session_state.user_id, 
                    card['api_id'], 
                    opening_id=opening_id, 
                    is_bought=False # Det är en pull, inte ett singelköp
                )
                
                total_value += float(card['price_normal_nm'] or 0)
                opened_cards_data.append(card)
                
                if not skip_anim:
                    with placeholder.container():
                        st.markdown(f"<h2 style='text-align:center;'>Kort {i+1}/10</h2>", unsafe_allow_html=True)
                        st.image(card['image_url'], use_container_width=True)
                        st.balloons() if i == 9 else None # Fira sista kortet
                        time.sleep(1.2)
            
            placeholder.empty()
            st.session_state.opening_results = {
                "cards": opened_cards_data,
                "value": total_value,
                "price": pack_price
            }

    # --- VISA RESULTAT ---
    if st.session_state.opening_results:
        res = st.session_state.opening_results
        st.divider()
        st.header("📊 Resultat från öppningen")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Kostnad", f"{res['price']} SEK")
        c2.metric("Värde (NM)", f"{res['value']} SEK")
        profit = res['value'] - res['price']
        c3.metric("ROI", f"{profit} SEK", delta=f"{profit}", delta_color="normal")
        
        cols = st.columns(5)
        for idx, card in enumerate(res['cards']):
            cols[idx % 5].image(card['image_url'], caption=card['name'])

        if st.button("Rensa och öppna ny"):
            st.session_state.opening_results = None
            st.rerun()