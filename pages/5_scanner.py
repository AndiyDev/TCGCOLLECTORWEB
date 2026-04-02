import streamlit as st
import cv2
import numpy as np
import json
import pytesseract
import requests
import re
from database import add_item_to_user

# Ladda din master-lista
try:
    with open("set_mapping.json", "r", encoding="utf-8") as f:
        SET_LIBRARY = json.load(f)
except:
    st.error("Kör mapping-scriptet först för att skapa set_mapping.json!")
    st.stop()

st.title("🔍 Smart Card Scanner")

img_file = st.camera_input("Ta en tydlig bild på kortets symbol och nummer")

if img_file:
    # 1. Bildbehandling
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    best_match = None
    max_score = 0

    # 2. Hitta Set Symbol (Template Matching - Ingen AI)
    with st.spinner("Identifierar Set..."):
        for name, data in SET_LIBRARY.items():
            template = cv2.imread(data['symbol_local_path'], 0)
            if template is None: continue
            
            res = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
            _, val, _, _ = cv2.minMaxLoc(res)
            
            if val > max_score:
                max_score = val
                best_match = data

    # Tröskelvärde för matchning (0.7-0.8 brukar vara bra)
    if best_match and max_score > 0.75:
        st.success(f"Hittade symbol: **{best_match['set_name']}** ({max_score:.1%})")
        
        # 3. Läs Nummer (OCR)
        # Vi tittar specifikt efter mönster som "44/64" eller "150/149"
        ocr_text = pytesseract.image_to_string(gray, config='--psm 11')
        num_match = re.search(r'(\d+)\s*/\s*(\d+)', ocr_text)
        
        if num_match:
            card_num = num_match.group(1)
            set_max = int(num_match.group(2))
            
            st.info(f"Läste nummer: {card_num}/{set_max}")

            # 4. Logisk Validering (Fake-check utan AI)
            is_fake_suspect = False
            reasons = []

            # Check: Stämmer setets maxnummer?
            if set_max != best_match['printed_total']:
                is_fake_suspect = True
                reasons.append(f"Felaktigt max-nummer för detta set (Väntat: {best_match['printed_total']})")

            # Check: Är numret helt orimligt (Secret rares inkluderade)?
            if int(card_num) > best_match['total_including_secrets']:
                is_fake_suspect = True
                reasons.append(f"Numret {card_num} existerar inte i detta set (Max inkl. secrets: {best_match['total_including_secrets']})")

            if is_fake_suspect:
                st.error("⚠️ Misstänkt Fake!")
                for r in reasons: st.write(f"- {r}")
            else:
                # 5. Hämta exakt data från API
                if st.button(f"Bekräfta {best_match['set_name']} #{card_num}"):
                    res = requests.get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{best_match['api_id']} number:{card_num}")
                    card_data = res.json().get('data')
                    if card_data:
                        st.image(card_data[0]['images']['small'])
                        if st.button("Spara i Portfölj"):
                            add_item_to_user(st.session_state.user_id, card_data[0], "Normal", 0.0)
                            st.balloons()
    else:
        st.warning("Kunde inte identifiera symbolen. Prova bättre ljus eller håll kameran närmare.")