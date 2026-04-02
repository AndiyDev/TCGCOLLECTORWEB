import streamlit as st
import requests
from database import get_user_collection, add_to_collection

st.title("Pokemon Sets")

# Cachea set-listan i ett dygn så den laddar direkt
@st.cache_data(ttl=86400)
def get_all_sets():
    res = requests.get("https://api.pokemontcg.io/v2/sets?orderBy=-releaseDate")
    return res.json().get("data", []) if res.status_code == 200 else []

# Cachea korten i ett specifikt set i en timme
@st.cache_data(ttl=3600)
def get_cards_in_set(set_id):
    res = requests.get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{set_id}&orderBy=number")
    return res.json().get("data", []) if res.status_code == 200 else []

# Kolla om användaren har klickat in på ett set (sparas i URL:en)
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
    
    # 3 kolumner för ett snyggt grid av logotyper
    cols = st.columns(3)
    for idx, s_data in enumerate(all_sets):
        with cols[idx % 3]:
            # Visa logotypen
            st.image(s_data['images']['logo'], width="stretch")
            
            # Räkna ut progress (hur många kort du äger i just detta set)
            owned_in_set = user_df[user_df['set_code'] == s_data['id']]['api_id'].nunique()
            total_in_set = s_data['printedTotal']
            st.caption(f"Samlat: {owned_in_set} / {total_in_set}")
            
            # Knapp för att dyka in i setet
            if st.button("Visa kort", key=f"btn_{s_data['id']}", width="stretch"):
                st.query_params["set_id"] = s_data['id']
                st.rerun()
            st.divider()

else:
    # --- VY 2: VISA ALLA KORT I DET VALDA SETET ---
    
    # Tillbaka-knapp för att rensa URL-parametern
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
    owned_card_ids = user_df['api_id'].values
    
    # Visa korten i ett grid (4 kolumner)
    cols = st.columns(4)
    for idx, card in enumerate(cards):
        with cols[idx % 4]:
            is_owned = card['id'] in owned_card_ids
            
            # Visa tydligt om du redan äger kortet
            if is_owned:
                st.success("✅ I samlingen")
            else:
                st.write("") # Tomt utrymme så designen håller sig i linje
            
            st.image(card['images']['small'], width="stretch")
            st.write(f"**{card['name']}**")
            st.caption(f"#{card['number']}")
            
            # Lägg till-knapp direkt under varje kort
            price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
            if st.button("➕ Lägg till", key=f"add_{card['id']}", width="stretch"):
                add_to_collection(st.session_state.user_id, card['id'], card['name'], card['set']['id'], card['number'], price, card['images']['small'])
                st.toast(f"{card['name']} tillagd!")
                st.rerun() # Ladda om för att visa ✅
            st.divider()