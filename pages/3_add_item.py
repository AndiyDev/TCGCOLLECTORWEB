import streamlit as st
from database import add_to_collection

st.title("Lägg till kort")

with st.form("add_form"):
    name = st.text_input("Kortets namn (ex. Charizard 1st Ed)")
    val = st.number_input("Marknadsvärde (kr)", min_value=0.0, step=10.0)
    img = st.text_input("Bild-URL (frivilligt)")
    
    if st.form_submit_button("Spara till samling", type="primary"):
        if name.strip():
            add_to_collection(st.session_state.user_id, name, val, img)
            st.success(f"'{name}' har lagts till i din samling!")
        else:
            st.error("Kortets namn är obligatoriskt.")
