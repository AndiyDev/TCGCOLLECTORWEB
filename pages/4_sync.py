import streamlit as st
import requests
import time
from database import get_user_portfolio, get_user_sealed, update_card_market_value, record_portfolio_history

# Säkerhetsspärr
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in först.")
    st.stop()

st.title("🔄 Sync Market Prices")
st.write("Hämta de allra senaste priserna för din samling från marknaden och spara din historik.")

if st.button("🚀 Starta Synkronisering", type="primary", use_container_width=True):
    uid = st.session_state.user_id
    # Hämta portföljen med det nya funktionsnamnet
    df = get_user_portfolio(uid)
    
    if df.empty:
        st.warning("Din samling är tom, inget att synkronisera.")
    else:
        # Hämta unika api_ids för att spara på API-anrop
        unique_cards = df['api_id'].unique()
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        updated_count = 0
        for i, api_id in enumerate(unique_cards):
            status_text.text(f"Uppdaterar kort {i+1} av {len(unique_cards)}...")
            
            try:
                res = requests.get(f"https://api.pokemontcg.io/v2/cards/{api_id}")
                if res.status_code == 200:
                    card_data = res.json().get('data', {})
                    # Hämta priset från Cardmarket
                    new_price = card_data.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
                    # Uppdatera i global_cards
                    update_card_market_value(api_id, new_price)
                    updated_count += 1
            except Exception:
                pass
                
            time.sleep(0.2) # API-vänlig paus
            progress_bar.progress((i + 1) / len(unique_cards))
        
        # Räkna ut det nya totalvärdet efter uppdateringen
        new_df_cards = get_user_portfolio(uid)
        new_df_sealed = get_user_sealed(uid)
        
        val_cards = new_df_cards['market_price'].sum() if not new_df_cards.empty else 0.0
        val_sealed = (new_df_sealed['market_value'] * new_df_sealed['quantity']).sum() if not new_df_sealed.empty else 0.0
        total_val = val_cards + val_sealed
        
        # Spara i historiken för grafen
        record_portfolio_history(uid, total_val)
        
        status_text.text("Synkronisering klar!")
        st.success(f"Uppdaterade {updated_count} unika kort. Ditt nya portföljvärde har loggats!")
        st.balloons()