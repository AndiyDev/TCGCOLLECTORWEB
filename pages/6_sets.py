import streamlit as st
import requests
from bs4 import BeautifulSoup
from database import get_conn
from sqlalchemy import text
import pandas as pd
import time
import urllib.parse

# 1. Säkerhetsspärr
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

st.title("🏛️ Master Library & Set Manager")
st.write("Bygg ditt eget oberoende arkiv genom att koppla GitHub-symboler till officiell data.")

# --- KONFIGURATION FÖR GITHUB ---
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/AndiyDev/TCGCOLLECTORWEB/main/images/"

# --- FUNKTION: SKRAPA & SPARA KORT ---
def scrape_and_store_card(set_intern_id, card_num):
    url = f"https://www.pokemon.com/us/pokemon-tcg/pokemon-cards/series/{set_intern_id}/{card_num}/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200: return False
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # Extrahera data
        name = soup.find("div", class_="card-description").find("h1").text.strip()
        hp_tag = soup.find("span", class_="hp")
        hp = hp_tag.text.replace("HP", "").strip() if hp_tag else "0"
        img_url = soup.find("div", class_="card-image").find("img").get("src")

        # Spara i global_cards
        api_id = f"{set_intern_id}-{card_num}"
        conn = get_conn()
        with conn.session as s:
            s.execute(text("""
                INSERT INTO global_cards (api_id, set_intern_id, name, hp, card_number, image_url)
                VALUES (:aid, :sid, :n, :hp, :num, :img)
                ON DUPLICATE KEY UPDATE name = :n, hp = :hp, image_url = :img
            """), {"aid": api_id, "sid": set_intern_id, "n": name, "hp": hp, "num": card_num, "img": img_url})
            s.commit()
        return True
    except:
        return False

# --- UI: SKAPA/UPPDATERA SET ---
with st.expander("✨ 1. Registrera nytt Set (Koppla till GitHub Symbol)"):
    st.info("Här kopplar du dina uppladdade bilder på GitHub till ett Set i databasen.")
    
    with st.form("set_reg_form"):
        col1, col2 = st.columns(2)
        s_name = col1.text_input("Set Namn", placeholder="t.ex. Neo Discovery")
        s_intern = col2.text_input("Intern Kod (URL-kod)", placeholder="t.ex. neo2")
        
        col3, col4 = st.columns(2)
        s_number_id = col3.text_input("Set Number ID (Text-box)", placeholder="t.ex. TEF (lämna tom för grafik)")
        s_total = col4.number_input("Totalt antal kort", min_value=1, value=100)
        
        # Sökväg på GitHub (baserat på din mappstruktur)
        github_subpath = st.text_input("Sökväg på GitHub efter /images/", placeholder="Set Symbols/03 Neo/Neo Discovery.png")
        
        if st.form_submit_button("Spara Set-information"):
            # Skapa korrekt URL (hanterar mellanslag)
            encoded_path = urllib.parse.quote(github_subpath)
            full_symbol_url = f"{GITHUB_RAW_BASE}{encoded_path}"
            
            conn = get_conn()
            with conn.session as s:
                s.execute(text("""
                    INSERT INTO global_sets (set_intern_id, set_name, set_number_id, total_cards, symbol_path)
                    VALUES (:sid, :name, :nid, :total, :path)
                    ON DUPLICATE KEY UPDATE set_name = :name, set_number_id = :nid, total_cards = :total, symbol_path = :path
                """), {"sid": s_intern, "name": s_name, "nid": s_number_id, "total": s_total, "path": full_symbol_url})
                s.commit()
            st.success(f"Setet '{s_name}' har sparats!")
            st.image(full_symbol_url, width=100, caption="Länkad Symbol")

# --- UI: MASS IMPORT ---
with st.expander("📥 2. Mass-importera Kort (Från Pokémon.com)"):
    conn = get_conn()
    registered_sets = conn.query("SELECT set_intern_id, set_name, total_cards FROM global_sets")
    
    if not registered_sets.empty:
        target_set_row = st.selectbox("Välj set att importera kort till:", registered_sets.index, 
                                      format_func=lambda x: f"{registered_sets.loc[x, 'set_name']} ({registered_sets.loc[x, 'set_intern_id']})")
        
        t_id = registered_sets.loc[target_set_row, 'set_intern_id']
        t_total = int(registered_sets.loc[target_set_row, 'total_cards'])
        
        if st.button(f"Starta Import av {t_total} kort"):
            p_bar = st.progress(0)
            status = st.empty()
            for i in range(1, t_total + 1):
                status.text(f"Hämtar kort {i} av {t_total}...")
                scrape_and_store_card(t_id, i)
                p_bar.progress(i / t_total)
                time.sleep(0.3)
            st.success("Import färdig!")
            st.rerun()
    else:
        st.warning("Registrera ett set först i steg 1.")

st.divider()

# --- UI: BLÄDDRA I ARKIVET ---
st.subheader("📁 Ditt Lokala Arkiv")
if not registered_sets.empty:
    view_set = st.selectbox("Visa set:", registered_sets['set_name'])
    v_id = registered_sets[registered_sets['set_name'] == view_set]['set_intern_id'].values[0]
    
    # Visa symbolen högst upp
    set_info = conn.query("SELECT symbol_path FROM global_sets WHERE set_intern_id = :sid", params={"sid": v_id})
    if not set_info.empty:
        st.image(set_info.iloc[0]['symbol_path'], width=80)

    # Hämta korten
    cards = conn.query("SELECT * FROM global_cards WHERE set_intern_id = :sid ORDER BY CAST(card_number AS UNSIGNED) ASC", params={"sid": v_id})
    
    cols = st.columns(4)
    for idx, row in cards.iterrows():
        with cols[idx % 4]:
            st.image(row['image_url'], use_container_width=True)
            st.caption(f"#{row['card_number']} - {row['name']} (HP {row['hp']})")
            if st.button("➕ Samling", key=f"add_{row['api_id']}"):
                # Logik för att lägga till i user_items
                st.toast("Tillagd!")