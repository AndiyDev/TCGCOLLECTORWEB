import streamlit as st
from database import init_db, verify_user

# Måste ligga allra först
st.set_page_config(page_title="Collectr Pro", layout="wide", initial_sidebar_state="collapsed")

# Initiera säker session_state
defaults = {"logged_in": False, "user_id": None, "username": None, "currency": "SEK"}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

try:
    init_db()
except Exception as e:
    st.error(f"Databasfel: {e}")
    st.stop()

if not st.session_state.logged_in:
    st.title("Collectr Pro - Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    
    if st.button("Login", type="primary"):
        uid = verify_user(u, p)
        if uid:
            st.session_state.logged_in = True
            st.session_state.user_id = uid
            st.session_state.username = u
            st.rerun()
        else:
            st.error("Ogiltigt användarnamn eller lösenord.")

    # --- FLIK 2: REGISTRERA ---
    with tab_register:
        u_reg = st.text_input("Välj Användarnamn", key="reg_u")
        p_reg = st.text_input("Välj Lösenord", type="password", key="reg_p")
        p_reg2 = st.text_input("Bekräfta Lösenord", type="password", key="reg_p2")
        
        if st.button("Registrera mig", type="primary"):
            if p_reg != p_reg2:
                st.error("Lösenorden matchar inte.")
            elif len(u_reg) < 3 or len(p_reg) < 6:
                st.error("Användarnamnet måste vara minst 3 tecken och lösenordet minst 6 tecken.")
            else:
                success = register_user(u_reg, p_reg)
                if success:
                    st.success("Konto skapat! Byt till fliken 'Logga in' för att fortsätta.")
                else:
                    st.error("Användarnamnet är redan upptaget. Välj ett annat.")
    
    st.stop()

pg = st.navigation([
    st.Page("pages/1_dashboard.py", title="Home", icon="🏠"),
    st.Page("pages/3_add_item.py", title="Search", icon="🔍"),
    st.Page("pages/2_collection.py", title="Portfolio", icon="📁"),
    st.Page("pages/6_sets.py", title="Sets", icon="🗃️"),
    st.Page("pages/5_wishlist.py", title="Wishlist", icon="🎯"),
    st.Page("pages/4_sync.py", title="Sync Prices", icon="🔄"),
    st.Page("pages/7_card_details.py", title="Details", icon="📄"),
    st.Page("pages/8_profile.py", title="Profile", icon="👤")
])

pg.run()