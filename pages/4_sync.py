import streamlit as st
import requests
import time
from database import get_user_collection, get_user_sealed, update_card_market_value, record_portfolio_history

st.title("🔄 Sync Market Prices")
st.write("Hämta de allra senaste priserna för din samling från marknaden och spara din historik. Kör denna en gång i veckan för att få en snygg graf!")

if st.button("🚀 Starta Synkronisering", type="primary", use_container_width=True):
    uid = st.session_state.user_id
    df = get_user_collection(uid)
    
    if df.empty:
        st.warning("Din samling är tom, inget att synkronisera.")
    else:
        # Få ut unika api_ids (för att inte fråga API:et flera gånger om du har dubbletter)
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
                    new_price = card_data.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
                    update_card_market_value(uid, api_id, new_price)
                    updated_count += 1
            except Exception:
                pass
                
            # Liten paus för att inte spamma API:et och bli blockerad
            time.sleep(0.2)
            progress_bar.progress((i + 1) / len(unique_cards))
        
        # När alla kort är klara, räkna ut nya totalvärdet och spara i historiken
        new_df_cards = get_user_collection(uid)
        new_df_sealed = get_user_sealed(uid)
        
        val_cards = (new_df_cards['market_value'] * new_df_cards['quantity']).sum() if not new_df_cards.empty else 0.0
        val_sealed = (new_df_sealed['market_value'] * new_df_sealed['quantity']).sum() if not new_df_sealed.empty else 0.0
        total_val = val_cards + val_sealed
        
        record_portfolio_history(uid, total_val)
        
        status_text.text("Synkronisering klar!")
        st.success(f"{updated_count} kort uppdaterades och portföljens värde är nu loggat i din historik!")
        st.balloons()