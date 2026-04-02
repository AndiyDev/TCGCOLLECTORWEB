import streamlit as st
import requests
from database import get_conn, init_db
from sqlalchemy import text
import time
import json

st.set_page_config(page_title="System Maintenance", page_icon="🛠️", layout="wide")

# 1. SÄKERHETSKOLL (Endast för Admin/Inloggad)
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Logga in för att komma åt systemverktygen.")
    st.stop()

st.title("🛠️ System Maintenance & DB Health")
st.write("Verktyg för att optimera ditt lokala arkiv och validera Master-data.")

# --- FLIKAR ---
tab1, tab2, tab3 = st.tabs(["🧹 Databasstädning", "🖼️ Bildvalidering", "📊 Systemstatistik"])

# --- FLIK 1: STÄDNING & CACHE ---
with tab1:
    st.subheader("Optimering")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Streamlit Cache**")
        st.caption("Rensar tillfälliga filer och sparade symboler för att tvinga fram en omhämtning.")
        if st.button("Rensa Cache", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache rensad!")

    with col2:
        st.write("**Databas-omstart**")
        st.caption("Kör 'init_db' igen för att säkerställa att alla v5.5-tabeller är korrekt skapade.")
        if st.button("Kör DB Init", use_container_width=True):
            init_db()
            st.success("Tabeller validerade!")

    st.divider()
    
    st.subheader("Farliga Åtgärder")
    st.warning("Dessa åtgärder kan inte ångras.")
    
    if st.button("🗑️ Rensa alla 'Global Cards' (Master-arkiv)", type="secondary"):
        conn = get_conn()
        with conn.session as s:
            s.execute(text("SET FOREIGN_KEY_CHECKS = 0;"))
            s.execute(text("TRUNCATE TABLE global_cards;"))
            s.execute(text("SET FOREIGN_KEY_CHECKS = 1;"))
            s.commit()
        st.success("Master-arkivet är nu tomt. Gå till Sets Manager för att skrapa igen.")

# --- FLIK 2: BILDVALIDERING ---
with tab2:
    st.subheader("Validera Bildlänkar")
    st.write("Kontrollerar om bilderna från Pokémon.com fortfarande är tillgängliga.")
    
    if st.button("Starta Bild-Check"):
        conn = get_conn()
        cards = conn.query("SELECT api_id, image_url FROM global_cards LIMIT 50") # Vi kollar ett urval
        
        progress_bar = st.progress(0)
        broken_links = []
        
        for i, row in cards.iterrows():
            try:
                res = requests.head(row['image_url'], timeout=5)
                if res.status_code != 200:
                    broken_links.append(row['api_id'])
            except:
                broken_links.append(row['api_id'])
            
            progress_bar.progress((i + 1) / len(cards))
        
        if not broken_links:
            st.success("✅ Alla testade bilder är online!")
        else:
            st.error(f"❌ Hittade {len(broken_links)} trasiga länkar: {', '.join(broken_links)}")

# --- FLIK 3: SYSTEMSTATISTIK ---
with tab3:
    st.subheader("Databas-analys")
    conn = get_conn()
    
    # Räkna rader i alla tabeller
    tables = ['global_sets', 'global_cards', 'user_items', 'booster_openings', 'user_transactions']
    stats_data = []
    
    for table in tables:
        count = conn.query(f"SELECT COUNT(*) as c FROM {table}").iloc[0]['c']
        stats_data.append({"Tabell": table, "Antal Rader": count})
    
    st.table(stats_data)
    
    st.divider()
    
    # Visa senaste tillagda korten i systemet (Globalt)
    st.write("**Senaste korten som skrapats till Master-arkivet:**")
    recent_master = conn.query("SELECT api_id, name, last_updated FROM global_cards ORDER BY last_updated DESC LIMIT 5")
    st.dataframe(recent_master, use_container_width=True)


st.subheader("📦 Databasskydd")
if st.button("Skapa Total Backup (JSON)"):
    conn = get_conn()
    # Hämta all användardata
    user_data = conn.query("SELECT * FROM user_items WHERE user_id = :uid", 
                           params={"uid": st.session_state.user_id})
    
    json_string = user_data.to_json(orient='records')
    st.download_button(
        label="Ladda ner Backup-fil",
        data=json_string,
        file_name=f"backup_user_{st.session_state.user_id}.json",
        mime="application/json"
    )