import streamlit as st
import cv2
import numpy as np
import os
import pytesseract
import requests
from database import add_item_to_user
from set_mapping import SET_MAP # Importen från steg 1

st.title("🗃️ Manuell Symbol-Scanner")

# Kamerainmatning
img_file = st.camera_input("Fokusera på set-symbolen och numret")

if img_file:
    # 1. Läs in bilden
    file_bytes = np.asarray(bytearray(img_file.read()), dtype=np.uint8)
    user_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    gray_user = cv2.cvtColor(user_img, cv2.COLOR_BGR2GRAY)

    best_match_id = None
    max_val = 0

    # 2. LOOPA IGENOM DINA MAPPAR (Ingen AI, bara jämförelse)
    # Vi letar i dina mappar som vi såg på bilderna
    base_path = "images/Set Symbols"
    
    with st.spinner("Letar efter matchande symbol i biblioteket..."):
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith(".png"):
                    template_path = os.path.join(root, file)
                    template = cv2.imread(template_path, 0)
                    if template is None: continue
                    
                    # Template Matching - Matematisk jämförelse
                    res = cv2.matchTemplate(gray_user, template, cv2.TM_CCOEFF_NORMED)
                    _, val, _, _ = cv2.minMaxLoc(res)
                    
                    if val > max_val:
                        max_val = val
                        # Matcha filnamnet (t.ex. "Jungle") mot vårt Set ID (base2)
                        clean_name = file.replace(".png", "")
                        best_match_id = SET_MAP.get(clean_name)

    # 3. RESULTAT & NUMMER-CHECK
    if max_val > 0.70 and best_match_id:
        st.success(f"Hittade symbolen för: **{best_match_id}** (Match: {max_val:.2%})")
        
        # Nu kör vi en enkel OCR-läsning för att hitta siffrorna
        # Vi letar efter tal i den nedre delen av bilden
        h, w = gray_user.shape
        roi = gray_user[int(h*0.7):, :] # Bara botten av kortet
        card_num_text = pytesseract.image_to_string(roi, config='--psm 11 -c tessedit_char_whitelist=0123456789/')
        
        # Extrahera siffror (t.ex. från "44/64")
        import re
        match = re.search(r'(\d+)', card_num_text)
        
        if match:
            card_num = match.group(1)
            st.write(f"Identifierat nummer: **{card_num}**")
            
            # 4. HÄMTA FRÅN API (Enda gången vi använder nätet)
            if st.button("Hämta kortinfo och bekräfta"):
                api_url = f"https://api.pokemontcg.io/v2/cards?q=set.id:{best_match_id} number:{card_num}"
                data = requests.get(api_url).json().get('data')
                
                if data:
                    card = data[0]
                    st.image(card['images']['small'])
                    st.write(f"Är detta **{card['name']}**?")
                    if st.button("Spara i samling"):
                        add_item_to_user(st.session_state.user_id, card, "Normal", 0.0)
                        st.balloons()
                else:
                    st.error("Kunde inte hitta ett kort med det numret i det setet.")
    else:
        st.warning("Kunde inte matcha symbolen. Försök hålla kameran stadigare eller närmare symbolen.")