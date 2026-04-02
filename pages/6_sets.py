import streamlit as st
import requests
from database import get_user_collection, add_to_collection

st.title("Pokemon Sets & Explorer")

@st.cache_data(ttl=86400) # Cacha set-listan i 24h
def get_all_sets():
    res = requests.get("https://api.pokemontcg.io/v2/sets?orderBy=-releaseDate")
    return res.json().get("data", []) if res.status_code == 200 else []

@st.cache_data(ttl=3600) # Cacha korten i ett set i 1h
def get_cards_in_set(set_id):
    res = requests.get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{set_id}&orderBy=number")
    return res.json().get("data", []) if res.status_code == 200 else []

all_sets = get_all_sets()
user_df = get_user_collection(st.session_state.user_id)

# Välj vy: Översikt eller Specifikt Set
selected_set_id = st.selectbox("Välj ett set att utforska", [s['id'] for s in all_sets], format_func=lambda x: next(s['name'] for s in all_sets if s['id'] == x))

if selected_set_id:
    set_data = next(s for s in all_sets if s['id'] == selected_set_id)
    st.subheader(f"Utforskar {set_data['name']}")
    
    # Visa statistik för setet
    owned_in_set = user_df[user_df['set_code'] == selected_set_id]['api_id'].nunique()
    total_in_set = set_data['printedTotal']
    st.write(f"Du äger **{owned_in_set}** av **{total_in_set}** kort i detta set.")
    st.progress(min(owned_in_set / total_in_set, 1.0) if total_in_set > 0 else 0)

    # Hämta alla kort i setet
    cards = get_cards_in_set(selected_set_id)
    
    # Visa korten i ett snyggt grid
    cols = st.columns(3)
    for idx, card in enumerate(cards):
        with cols[idx % 3]:
            # Kolla om användaren redan äger kortet
            is_owned = card['id'] in user_df['api_id'].values
            border_style = "2px solid #00ff88" if is_owned else "1px solid #333"
            
            st.markdown(f"""
                <div style="border: {border_style}; padding: 5px; border-radius: 5px; text-align: center;">
                    <p style="margin:0; font-size: 0.8rem;">#{card['number']}</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.image(card['images']['small'])
            st.write(f"**{card['name']}**")
            
            # Snabb-knapp för att lägga till
            price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
            if st.button("➕", key=f"add_set_{card['id']}"):
                add_to_collection(st.session_state.user_id, card['id'], card['name'], card['set']['id'], card['number'], price, card['images']['small'])
                st.toast(f"{card['name']} tillagd!")
                st.rerun()