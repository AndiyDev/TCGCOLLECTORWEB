import streamlit as st
import cv2
import numpy as np
import requests
from PIL import Image
from database import get_conn, add_item_to_user
import io

st.set_page_config(page_title="Card Scanner", page_icon="📸")

# --- FUNKTION: HÄMTA & PREPPA SYMBOLER ---
@st.cache_data
def get_all_symbols():
    conn = get_conn()
    sets = conn.query("SELECT set_intern_id, symbol_path FROM global_sets")
    symbol_library = {}
    
    for _, row in sets.iterrows():
        try:
            res = requests.get(row['symbol_path'])
            img = Image.open(io.BytesIO(res.content)).convert('L') # Gråskala
            symbol_library[row['set_intern_id']] = np.array(img)
        except:
            continue
    return symbol_library

# --- DIALOG: MATCH HITTAD ---
@st.dialog("Symbol Identifierad!")
def match_found_dialog(set_id):
    conn = get_conn()
    set_info = conn.query("SELECT set_name FROM global_sets WHERE set_intern_id = :sid", 
                          params={"sid": set_id}).iloc[0]
    
    st.success(f"Detta ser ut som ett kort från: **{set_info['set_name']}**")
    st.write("Skriv in kortnumret för att hämta detaljer:")
    
    card_num = st.text_input("Kortnummer (t.ex. 36)")
    
    if card_num:
        card = conn.query("SELECT * FROM global_cards WHERE set_intern_id = :sid AND card_number = :num",
                          params={"sid": set_id, "num": card_num})
        
        if not card.empty:
            c = card.iloc[0]
            st.image(c['image_url'], width=150)
            st.write(f"**{c['name']}**")
            
            if st.button("➕ Lägg till i samling"):
                add_item_to_user(st.session_state.user_id, c['api_id'])
                st.success("Kortet sparat!")
                st.rerun()
        else:
            st.warning("Kortet hittades inte i biblioteket. Har du skrapat detta set?")

# --- HUVUDSIDA ---
st.title("📸 Symbol Scanner")
st.write("Håll upp kortets symbol (nere till höger/vänster) mot kameran.")

symbols = get_all_symbols()

if not symbols:
    st.warning("Inga symboler hittades i biblioteket. Registrera sets i 'Sets Manager' först!")
    st.stop()

# Starta kameran
img_file = st.camera_input("Ta en bild på symbolen")

if img_file:
    # Konvertera bilden till OpenCV-format
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, 1)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    best_match = None
    max_val = 0

    # Template Matching (Algoritmisk jämförelse)
    for set_id, symbol_img in symbols.items():
        # Skala om symbolen för att matcha kamerans storlek (enkelt exempel)
        res = cv2.matchTemplate(gray_frame, symbol_img, cv2.TM_CCOEFF_NORMED)
        _, current_max, _, _ = cv2.minMaxLoc(res)
        
        if current_max > max_val:
            max_val = current_max
            best_match = set_id

    # Om vi har en matchning över 70% säkerhet
    if max_val > 0.7:
        match_found_dialog(best_match)
    else:
        st.error(f"Kunde inte identifiera symbolen säkert (Max likhet: {max_val:.2f}). Försök igen med bättre ljus.")

st.divider()
st.subheader("💡 Tips för bättre scanning")
st.write("""
1. **Ljussättning:** Se till att symbolen inte har starka reflexer.
2. **Närbild:** Fokusera kameran så nära symbolen som möjligt.
3. **Bibliotek:** Kontrollera att setet är importerat i 'Sets Manager'.
""")