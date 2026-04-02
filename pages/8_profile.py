import streamlit as st
from database import get_conn, get_user_collection
from sqlalchemy import text
import pandas as pd

st.title("Profile & Settings")

st.write(f"Inloggad som: **{st.session_state.username}**")

st.subheader("Preferences")
new_currency = st.selectbox("Valuta", ["SEK", "EUR", "USD"], index=["SEK", "EUR", "USD"].index(st.session_state.currency))
if new_currency != st.session_state.currency:
    st.session_state.currency = new_currency
    st.success(f"Valuta ändrad till {new_currency}.")
    st.rerun()

st.divider()

# --- CSV EXPORT ---
st.subheader("Data Management")
st.write("Exportera hela din portfölj till en CSV-fil (kan öppnas i Excel).")

df = get_user_collection(st.session_state.user_id)
if not df.empty:
    # Formatera CSV-datan
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Ladda ner Samling (CSV)",
        data=csv_data,
        file_name='min_pokemon_samling.csv',
        mime='text/csv',
    )
else:
    st.info("Din samling är tom, inget att exportera.")

st.divider()

st.subheader("Account Management")
st.warning("Varning: Radering av konto tar permanent bort all samlingsdata och historik.")

confirm_delete = st.checkbox("Jag förstår att detta inte kan ångras.")
if st.button("Radera Konto", type="primary", disabled=not confirm_delete):
    conn = get_conn()
    with conn.session as s:
        s.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": st.session_state.user_id})
        s.commit()
    
    st.session_state.clear()
    st.success("Konto raderat.")
    st.rerun()

st.divider()

if st.button("Logga Ut", width="stretch"):
    st.session_state.clear()
    st.rerun()