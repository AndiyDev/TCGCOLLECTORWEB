import streamlit as st
from database import init_db, verify_user, register_user

# 1. Konfiguration (Måste ligga allra först)
st.set_page_config(page_title="Collectr Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. Initiera säker session_state
defaults = {"logged_in": False, "user_id": None, "username": None, "currency": "SEK"}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# 3. Initiera databas
try:
    init_db()
except Exception as e:
    st.error(f"Databasfel: {e}")
    st.stop()

# 4. Skapa inloggningsskärmen som en funktion
def login_screen():
    st.title("Collectr Pro")
    
    tab_login, tab_register = st.tabs(["Logga in", "Skapa konto"])
    
    with tab_login:
        u_login = st.text_input("Användarnamn", key="login_u")
        p_login = st.text_input("Lösenord", type="password", key="login_p")
        
        if st.button("Logga in", type="primary"):
            uid = verify_user(u_login, p_login)
            if uid:
                st.session_state.logged_in = True
                st.session_state.user_id = uid
                st.session_state.username = u_login
                st.rerun()
            else:
                st.error("Ogiltigt användarnamn eller lösenord.")
                
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

# 5. Definiera alla inloggade sidor
app_pages = [
    st.Page("pages/1_dashboard.py", title="Home", icon="🏠"),
    st.Page("pages/3_add_item.py", title="Search", icon="🔍"),
    st.Page("pages/2_collection.py", title="Portfolio", icon="📁"),
    st.Page("pages/6_sets.py", title="Sets", icon="🗃️"),
    st.Page("pages/5_wishlist.py", title="Wishlist", icon="🎯"),
    st.Page("pages/4_sync.py", title="Sync Prices", icon="🔄"),
    st.Page("pages/7_card_details.py", title="Details", icon="📄"),
    st.Page("pages/8_profile.py", title="Profile", icon="👤")
]

# 6. Dynamisk Navigation (Låser systemet)
if not st.session_state.logged_in:
    # Om utloggad: Skapa en "Inloggning"-sida och visa BARA den
    login_page = st.Page(login_screen, title="Autentisering", icon="🔒")
    pg = st.navigation([login_page])
else:
    # Om inloggad: Visa alla appens riktiga sidor
    pg = st.navigation(app_pages)

# Kör navigeringen!
pg.run()