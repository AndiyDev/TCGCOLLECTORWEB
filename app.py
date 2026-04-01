import streamlit as st
from database import init_db, verify_user, create_user

st.set_page_config(page_title="Collectr Clone", layout="wide")

# Initiera databasstrukturen vid start
try:
    init_db()
except Exception as e:
    st.error(f"Kunde inte ansluta till databasen. Kontrollera secrets.toml. Fel: {e}")
    st.stop()

# Sessionshantering
if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "user_id": None, "username": None})

# Auth-vy om utloggad
if not st.session_state.logged_in:
    st.title("Collectr Clone")
    tab1, tab2 = st.tabs(["Logga in", "Registrera"])
    
    with tab1:
        with st.form("login_form"):
            user = st.text_input("Användarnamn")
            pwd = st.text_input("Lösenord", type="password")
            if st.form_submit_button("Logga in"):
                uid = verify_user(user, pwd)
                if uid:
                    st.session_state.update({"logged_in": True, "user_id": uid, "username": user})
                    st.rerun()
                else:
                    st.error("Ogiltiga inloggningsuppgifter.")
                    
    with tab2:
        with st.form("reg_form"):
            new_user = st.text_input("Välj Användarnamn")
            new_pwd = st.text_input("Välj Lösenord", type="password")
            if st.form_submit_button("Skapa konto"):
                if create_user(new_user, new_pwd):
                    st.success("Konto skapat. Byt flik för att logga in.")
                else:
                    st.error("Användarnamnet är upptaget.")
    st.stop()

# Inloggad vy - Sidebar och routing
st.sidebar.markdown(f"**Inloggad som:** {st.session_state.username}")
if st.sidebar.button("Logga ut", type="primary"):
    st.session_state.clear()
    st.rerun()

pg = st.navigation([
    st.Page("pages/1_dashboard.py", title="Dashboard", icon="📊"),
    st.Page("pages/2_collection.py", title="Min Samling", icon="🗃️"),
    st.Page("pages/3_add_item.py", title="Lägg till kort", icon="➕")
])
pg.run()
