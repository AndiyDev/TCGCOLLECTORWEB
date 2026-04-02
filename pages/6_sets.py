import streamlit as st
import requests
from database import get_user_collection, add_item_to_user

st.title("Pokemon Sets")

@st.cache_data(ttl=86400)
def get_all_sets():
    res = requests.get("https://api.pokemontcg.io/v2/sets?orderBy=-releaseDate")
    return res.json().get("data", []) if res.status_code == 200 else []

@st.cache_data(ttl=3600)
def get_cards_in_set(set_id):
    res = requests.get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{set_id}&orderBy=number")
    return res.json().get("data", []) if res.status_code == 200 else []

selected_set = st.query_params.get("set_id")

if not selected_set:
    # --- VY 1: VISA ALLA SETS (LOGOTYPER) ---
    all_sets = get_all_sets()
    user_df = get_user_collection(st.session_state.user_id)
    
    if not all_sets:
        st.error("Kunde inte ladda sets.")
        st.stop()
        
    st.write("Välj ett set för att se alla kort.")
    st.divider()
    
    cols = st.columns(4) 
    for idx, s_data in enumerate(all_sets):
        with cols[idx % 4]:
            st.markdown(f"""
                <div style="height: 120px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <img src="{s_data['images']['logo']}" style="max-height: 100%; max-width: 100%; object-fit: contain;">
                </div>
            """, unsafe_allow_html=True)
            
            owned_in_set = user_df[user_df['set_code'] == s_data['id']]['api_id'].nunique()
            total_in_set = s_data['printedTotal']
            
            st.markdown(f"<p style='text-align: center; color: #888; font-size: 0.9rem; margin-bottom: 10px;'>Samlat: {owned_in_set} / {total_in_set}</p>", unsafe_allow_html=True)
            
            if st.button("Visa kort", key=f"btn_{s_data['id']}", use_container_width=True):
                st.query_params["set_id"] = s_data['id']
                st.rerun()
            st.divider()

else:
    # --- VY 2: VISA ALLA KORT I DET VALDA SETET ---
    if st.button("← Tillbaka till alla Sets"):
        del st.query_params["set_id"]
        st.rerun()
        
    cards = get_cards_in_set(selected_set)
    if not cards:
        st.error("Kunde inte ladda korten för detta set.")
        st.stop()
        
    st.subheader(f"Utforskar: {cards[0]['set']['name']}")
    st.divider()
    
    user_df = get_user_collection(st.session_state.user_id)
    
    cols = st.columns(4)
    for idx, card in enumerate(cards):
        with cols[idx % 4]:
            # --- RÄKNA UT ANTAL ÄGDA KORT ---
            if not user_df.empty:
                owned_rows = user_df[user_df['api_id'] == card['id']]
                total_owned = int(owned_rows['quantity'].sum()) if not owned_rows.empty else 0
            else:
                total_owned = 0
            
            # Visa mängd eller en tom utfyllnadsruta för att behålla den raka designen
            if total_owned > 0:
                st.markdown(f"<div style='background-color: #1a231c; border: 1px solid #00ff88; color: #00ff88; padding: 6px; border-radius: 6px; text-align: center; font-weight: bold; margin-bottom: 10px;'>📦 Äger: {total_owned} st</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height: 40px; margin-bottom: 10px;'></div>", unsafe_allow_html=True) 
            
            st.image(card['images']['small'], width="stretch")
            st.write(f"**{card['name']}**")
            st.caption(f"#{card['number']}")
            
            # --- VÄLJ VARIANT ---
            var_options = ["Normal", "Reverse Holofoil", "Holofoil"]
            sel_var = st.selectbox("Välj variant", var_options, key=f"var_{card['id']}", label_visibility="collapsed")
            
            price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
            
            if st.button("➕ Lägg till", key=f"add_{card['id']}", use_container_width=True):
                # Justera priset lite om det är Holo/Reverse för att det ska bli mer realistiskt innan sync
                final_price = price * 1.2 if "Holo" in sel_var else price
                
                add_item_to_user(st.session_state.user_id, card, var_sel, p_price)
                st.toast(f"{card['name']} ({sel_var}) tillagd!")
                st.rerun() 
            st.divider()