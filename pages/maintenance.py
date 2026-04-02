import streamlit as st
import requests
from database import get_conn, init_db
from sqlalchemy import text
import time
import json

# BUG FIX #5: Removed st.set_page_config() — must only be called once in app.py

# --- AUTH GUARD ---
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
        st.caption("Kör 'init_db' igen för att säkerställa att alla tabeller är korrekt skapade.")
        if st.button("Kör DB Init", use_container_width=True):
            init_db()
            st.success("Tabeller validerade!")

    st.divider()

    st.subheader("Farliga Åtgärder")
    st.warning("Dessa åtgärder kan inte ångras.")

    # Use session-state confirm pattern (not nested buttons)
    if "confirm_truncate" not in st.session_state:
        st.session_state.confirm_truncate = False

    if not st.session_state.confirm_truncate:
        if st.button("🗑️ Rensa alla 'Global Cards' (Master-arkiv)", type="secondary"):
            st.session_state.confirm_truncate = True
            st.rerun()
    else:
        st.error("Är du säker? Detta raderar ALLA kort i Master-arkivet och kan inte ångras!")
        col_yes, col_no = st.columns(2)
        if col_yes.button("Ja, rensa Master-arkivet", type="primary"):
            conn = get_conn()
            with conn.session as s:
                s.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                s.execute(text("TRUNCATE TABLE global_cards"))
                s.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                s.commit()
            st.session_state.confirm_truncate = False
            st.success("Master-arkivet är nu tomt. Gå till Sets Manager för att skrapa igen.")
            st.rerun()
        if col_no.button("Avbryt"):
            st.session_state.confirm_truncate = False
            st.rerun()

# --- FLIK 2: BILDVALIDERING ---
with tab2:
    st.subheader("Validera Bildlänkar")
    st.write("Kontrollerar om bilderna från Pokémon.com fortfarande är tillgängliga.")

    if st.button("Starta Bild-Check"):
        conn = get_conn()
        cards = conn.query("SELECT api_id, image_url FROM global_cards LIMIT 50")

        if cards.empty:
            st.info("Inga kort i arkivet att validera.")
        else:
            progress_bar = st.progress(0)
            broken_links = []
            total = len(cards)

            # BUG FIX #6: Use enumerate with explicit counter; progress uses (i+1)/total
            for i, (_, row) in enumerate(cards.iterrows()):
                try:
                    res = requests.head(row['image_url'], timeout=5)
                    if res.status_code != 200:
                        broken_links.append(row['api_id'])
                except Exception:
                    broken_links.append(row['api_id'])

                progress_bar.progress((i + 1) / total)

            if not broken_links:
                st.success("✅ Alla testade bilder är online!")
            else:
                st.error(f"❌ Hittade {len(broken_links)} trasiga länkar: {', '.join(broken_links)}")

# --- FLIK 3: SYSTEMSTATISTIK ---
with tab3:
    st.subheader("Databas-analys")
    conn = get_conn()

    tables = ['global_sets', 'global_cards', 'user_items', 'booster_openings', 'user_transactions']
    stats_data = []

    for table in tables:
        count = conn.query(f"SELECT COUNT(*) as c FROM {table}").iloc[0]['c']
        stats_data.append({"Tabell": table, "Antal Rader": int(count)})

    st.table(stats_data)

    st.divider()

    st.write("**Senaste korten som skrapats till Master-arkivet:**")
    recent_master = conn.query(
        "SELECT api_id, name, last_updated FROM global_cards ORDER BY last_updated DESC LIMIT 5"
    )
    if recent_master.empty:
        st.info("Inga kort i Master-arkivet än.")
    else:
        st.dataframe(recent_master, use_container_width=True)

# --- DATABASSKYDD / BACKUP ---
st.divider()
st.subheader("📦 Databasskydd")
if st.button("Skapa Total Backup (JSON)"):
    conn = get_conn()
    user_data = conn.query(
        "SELECT * FROM user_items WHERE user_id = :uid",
        params={"uid": st.session_state.user_id}
    )

    json_string = user_data.to_json(orient='records', date_format='iso')
    st.download_button(
        label="Ladda ner Backup-fil",
        data=json_string,
        file_name=f"backup_user_{st.session_state.user_id}.json",
        mime="application/json"
    )
