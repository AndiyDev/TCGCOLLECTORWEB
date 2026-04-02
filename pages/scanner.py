import streamlit as st
import cv2
import numpy as np
import requests
from PIL import Image
from database import get_conn, add_item_to_user
import io

# BUG FIX #5: Removed st.set_page_config() — must only be called once in app.py

# --- AUTH GUARD ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

# --- FUNKTION: HÄMTA & PREPPA SYMBOLER ---
@st.cache_data
def get_all_symbols():
    conn = get_conn()
    sets = conn.query("SELECT set_intern_id, symbol_path FROM global_sets")
    symbol_library = {}

    for _, row in sets.iterrows():
        try:
            res = requests.get(row['symbol_path'], timeout=10)
            res.raise_for_status()
            img = Image.open(io.BytesIO(res.content)).convert('L')  # Gråskala
            symbol_library[row['set_intern_id']] = np.array(img)
        except Exception:
            continue
    return symbol_library

# --- DIALOG: MATCH HITTAD ---
@st.dialog("Symbol Identifierad!")
def match_found_dialog(set_id):
    conn = get_conn()
    set_rows = conn.query(
        "SELECT set_name FROM global_sets WHERE set_intern_id = :sid",
        params={"sid": set_id}
    )
    if set_rows.empty:
        st.error("Set-information hittades inte i databasen.")
        return

    set_info = set_rows.iloc[0]
    st.success(f"Detta ser ut som ett kort från: **{set_info['set_name']}**")
    st.write("Skriv in kortnumret för att hämta detaljer:")

    card_num = st.text_input("Kortnummer (t.ex. 36)")

    if card_num:
        card = conn.query(
            "SELECT * FROM global_cards WHERE set_intern_id = :sid AND card_number = :num",
            params={"sid": set_id, "num": card_num.strip()}
        )

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

img_file = st.camera_input("Ta en bild på symbolen")

if img_file:
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    frame_h, frame_w = gray_frame.shape[:2]

    best_match = None
    max_val = 0

    for set_id, symbol_img in symbols.items():
        sym_h, sym_w = symbol_img.shape[:2]

        # BUG FIX #10: Skip symbols larger than the camera frame to prevent matchTemplate crash
        if sym_h > frame_h or sym_w > frame_w:
            # Downscale the symbol to fit within the frame while preserving aspect ratio
            scale = min(frame_h / sym_h, frame_w / sym_w) * 0.5
            new_w = max(1, int(sym_w * scale))
            new_h = max(1, int(sym_h * scale))
            symbol_img = cv2.resize(symbol_img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            sym_h, sym_w = symbol_img.shape[:2]

        # Final guard: if still too large after resize, skip
        if sym_h > frame_h or sym_w > frame_w:
            continue

        try:
            res = cv2.matchTemplate(gray_frame, symbol_img, cv2.TM_CCOEFF_NORMED)
            _, current_max, _, _ = cv2.minMaxLoc(res)

            if current_max > max_val:
                max_val = current_max
                best_match = set_id
        except cv2.error:
            continue

    if best_match and max_val > 0.7:
        match_found_dialog(best_match)
    else:
        st.error(
            f"Kunde inte identifiera symbolen säkert (Bästa likhet: {max_val:.2f}). "
            "Försök igen med bättre ljus och närbild."
        )

st.divider()
st.subheader("💡 Tips för bättre scanning")
st.write("""
1. **Ljussättning:** Se till att symbolen inte har starka reflexer.
2. **Närbild:** Fokusera kameran så nära symbolen som möjligt.
3. **Bibliotek:** Kontrollera att setet är importerat i 'Sets Manager'.
""")
