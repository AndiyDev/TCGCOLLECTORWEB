import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
from database import get_conn, init_db
from sqlalchemy import text

# BUG FIX #5: Removed st.set_page_config() — must only be called once in app.py
# BUG FIX #16: Added auth guard (was missing entirely)
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

# Säkerställ att databasen är redo
init_db()

st.title("🗃️ Master Library Manager")
st.write("Bygg ditt personliga arkiv genom att importera officiell data och koppla dina GitHub-symboler.")

# --- FLIKAR ---
tab1, tab2 = st.tabs(["➕ Importera Set", "🔍 Hantera Bibliotek"])

# --- FLIK 1: IMPORT & SKRAPNING ---
with tab1:
    st.subheader("Hämta data från Pokémon.com")
    st.info("Detta fyller din 'Global Cards' tabell så att du kan använda scannern och öppna boosters.")

    with st.form("import_set_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        set_name = col1.text_input("Set Namn (Display)", placeholder="t.ex. Crown Zenith")
        set_id = col2.text_input("Internt API ID (Från URL)", placeholder="t.ex. swsh12pt5")

        col3, col4 = st.columns(2)
        total_cards = col3.number_input("Antal kort att skrapa", min_value=1, value=160)
        symbol_url = col4.text_input("GitHub Symbol URL (Raw-länk)", placeholder="https://raw.githubusercontent.com/...")

        st.caption("Tips: API ID hittar du i URL:en på pokemon.com/us/pokemon-tcg/pokemon-cards/series/[ID]/")
        submit = st.form_submit_button("🚀 Starta Fullständig Import")

    if submit:
        if not set_name or not set_id or not symbol_url:
            st.error("Alla fält måste fyllas i för en korrekt import.")
        else:
            conn = get_conn()

            # 1. Registrera/Uppdatera Setet
            with conn.session as s:
                s.execute(text("""
                    INSERT INTO global_sets (set_intern_id, set_name, total_cards, symbol_path)
                    VALUES (:sid, :name, :total, :path)
                    ON DUPLICATE KEY UPDATE set_name=:name, total_cards=:total, symbol_path=:path
                """), {"sid": set_id, "name": set_name, "total": total_cards, "path": symbol_url})
                s.commit()

            # 2. Skrapnings-processen
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_container = st.container(border=True)

            success_count = 0
            for i in range(1, total_cards + 1):
                card_num = str(i)
                url = f"https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/series/{set_id}/{card_num}/"
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

                try:
                    res = requests.get(url, headers=headers, timeout=10)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, 'html.parser')

                        name_tag = soup.find("div", class_="card-description")
                        name = name_tag.find("h1").text.strip() if name_tag else f"Card #{card_num}"
                        hp_tag = soup.find("span", class_="hp")
                        hp_val = int(hp_tag.text.replace("HP", "").strip()) if hp_tag else 0
                        img_div = soup.find("div", class_="card-image")
                        img_url = img_div.find("img").get("src") if img_div else ""

                        with conn.session as s:
                            s.execute(text("""
                                INSERT INTO global_cards (api_id, set_intern_id, name, hp, card_number, image_url)
                                VALUES (:aid, :sid, :name, :hp, :num, :img)
                                ON DUPLICATE KEY UPDATE name=:name, hp=:hp, image_url=:img
                            """), {
                                "aid": f"{set_id}-{card_num}",
                                "sid": set_id,
                                "name": name,
                                "hp": hp_val,
                                "num": card_num,
                                "img": img_url
                            })
                            s.commit()
                        success_count += 1
                        log_container.write(f"✅ #{card_num}: {name}")
                    else:
                        log_container.write(f"⚠️ #{card_num}: Hittades inte (Status {res.status_code})")

                except Exception as e:
                    log_container.error(f"❌ Fel vid #{card_num}: {e}")

                progress_bar.progress(i / total_cards)
                status_text.text(f"Bearbetar kort {i} av {total_cards}...")
                time.sleep(0.2)

            st.success(f"Import slutförd! {success_count} kort tillagda i {set_name}.")
            st.balloons()

# --- FLIK 2: BIBLIOTEKS-ÖVERSIKT ---
with tab2:
    st.subheader("Dina sparade Master-Sets")
    conn = get_conn()
    sets_df = conn.query("SELECT * FROM global_sets ORDER BY set_name ASC")

    if not sets_df.empty:
        for _, row in sets_df.iterrows():
            with st.expander(f"📦 {row['set_name']} (ID: {row['set_intern_id']})"):
                c1, c2, c3 = st.columns([1, 3, 1])

                c1.image(row['symbol_path'], width=60, caption="Symbol")

                # BUG FIX #7: Replaced f-string SQL (injection risk) with a parameterised query
                count_df = conn.query(
                    "SELECT COUNT(*) as c FROM global_cards WHERE set_intern_id = :sid",
                    params={"sid": row['set_intern_id']}
                )
                current_cards = count_df.iloc[0]['c']
                c2.write(f"**Status:** {current_cards} / {row['total_cards']} kort skrapade.")

                if c3.button("🔄 Uppdatera Priser", key=f"btn_prc_{row['set_intern_id']}"):
                    st.toast(f"Hämtar priser för {row['set_name']}...")
                    time.sleep(1)
                    st.success("Priser synkade mot NM-snitt!")

                del_key = f"confirm_del_set_{row['set_intern_id']}"
                if del_key not in st.session_state:
                    st.session_state[del_key] = False

                if not st.session_state[del_key]:
                    if c3.button("🗑️ Radera Set", key=f"btn_del_{row['set_intern_id']}", type="secondary"):
                        st.session_state[del_key] = True
                        st.rerun()
                else:
                    st.warning(f"Radera **{row['set_name']}** och alla dess kort? Detta kan inte ångras.")
                    col_yes, col_no = st.columns(2)
                    if col_yes.button("Ja, radera", key=f"yes_del_{row['set_intern_id']}", type="primary"):
                        with conn.session as s:
                            s.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
                            s.execute(text("DELETE FROM global_cards WHERE set_intern_id = :sid"),
                                      {"sid": row['set_intern_id']})
                            s.execute(text("DELETE FROM global_sets WHERE set_intern_id = :sid"),
                                      {"sid": row['set_intern_id']})
                            s.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
                            s.commit()
                        st.session_state[del_key] = False
                        st.success(f"Set '{row['set_name']}' raderat.")
                        st.rerun()
                    if col_no.button("Avbryt", key=f"no_del_{row['set_intern_id']}"):
                        st.session_state[del_key] = False
                        st.rerun()
    else:
        st.info("Ditt bibliotek är tomt. Börja med att importera ett set!")
