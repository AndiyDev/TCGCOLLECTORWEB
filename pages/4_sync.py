import streamlit as st
import requests
import time
from datetime import date
from sqlalchemy import text
from database import get_conn

st.title("🔄 Sync Market Prices")
st.write("Hämtar dagsfärska priser från API:et.")

if st.button("Start Sync", type="primary"):
    conn = get_conn()
    uid = st.session_state.user_id
    
    unique_cards = conn.query("SELECT DISTINCT api_id FROM collection WHERE user_id = :u", params={"u": uid})
    
    if unique_cards.empty:
        st.warning("Samlingen är tom.")
        st.stop()

    progress_bar = st.progress(0)
    status_text = st.empty()
    total = len(unique_cards)
    updated = 0

    with conn.session as s:
        for i, row in unique_cards.iterrows():
            api_id = row['api_id']
            try:
                res = requests.get(f"https://api.pokemontcg.io/v2/cards/{api_id}")
                if res.status_code == 200:
                    card_data = res.json().get('data', {})
                    new_price = card_data.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
                    
                    s.execute(text("""
                        UPDATE collection 
                        SET market_value = :p 
                        WHERE user_id = :u AND api_id = :aid AND is_graded = FALSE
                    """), {"p": new_price, "u": uid, "aid": api_id})
                    updated += 1
            except Exception:
                pass 
            
            time.sleep(0.2)
            progress_bar.progress((i + 1) / total)
            status_text.text(f"Synkroniserar {i+1}/{total}...")
        
        s.commit()

    with conn.session as s:
        tot_res = s.execute(text("SELECT SUM(market_value * quantity) FROM collection WHERE user_id = :u"), {"u": uid}).scalar()
        tot_val = tot_res or 0.0
        
        s.execute(text("""
            INSERT INTO portfolio_history (user_id, recorded_date, total_value) 
            VALUES (:u, :d, :v)
            ON DUPLICATE KEY UPDATE total_value = :v
        """), {"u": uid, "d": date.today(), "v": tot_val})
        s.commit()

    progress_bar.empty()
    status_text.empty()
    st.success(f"Synk slutförd! {updated} kort uppdaterades och dagens portföljvärde har loggats.")