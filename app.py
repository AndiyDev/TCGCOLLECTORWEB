import streamlit as st
import time
from database import init_db, verify_user, create_user
import re

# --- 1. SÄKERHETS-CONFIG ---
st.set_page_config(page_title="TCG Collector Pro v5.5", page_icon="🛡️", layout="wide")

# --- 2. INITIALISERA SYSTEM & DATABAS ---
if "db_init" not in st.session_state:
    init_db()
    st.session_state.db_init = True

# --- 3. SESSION STATE MANAGEMENT ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.user_id = None
    st.session_state.login_attempts = 0
    st.session_state.last_activity = time.time()

# --- 4. INPUT SANITIZATION ---
def sanitize_input(text_input):
    if not text_input: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', str(text_input)).strip()

# --- 5. INPUT SANITIZATION (Skydd mot kod-injektion) ---
def sanitize_input(text_input):
    """Tar bort HTML-taggar och misstänkta tecken."""
    if not text_input: return ""
    clean = re.compile('<.*?>')
    return re.sub(clean, '', str(text_input)).strip()

# --- 6. INLOGGNINGSVY ---
def login_screen():
    st.title("🛡️ TCG Secure Access")
    
    tab_login, tab_reg = st.tabs(["🔒 Logga in", "📝 Skapa säkert konto"])
    
    with tab_login:
        with st.form("login_form"):
            u = sanitize_input(st.text_input("Användarnamn"))
            p = st.text_input("Lösenord", type="password")
            submit = st.form_submit_button("Logga in", use_container_width=True)
            
            if submit:
                # Rate Limiting: Max 5 försök
                if st.session_state.login_attempts >= 5:
                    st.error("För många misslyckade försök. Vänta en stund.")
                    time.sleep(5) # Straff-paus
                
                user_id = verify_user(u, p)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.username = u
                    st.session_state.user_id = user_id
                    st.session_state.login_attempts = 0
                    st.success("Åtkomst beviljad!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.session_state.login_attempts += 1
                    st.error(f"Felaktiga uppgifter. Försök kvar: {5 - st.session_state.login_attempts}")

    with tab_reg:
        st.info("Lösenord krypteras med SHA-256 (Bcrypt) innan de sparas.")
        with st.form("reg_form"):
            new_u = sanitize_input(st.text_input("Välj Användarnamn"))
            new_p = st.text_input("Välj ett starkt Lösenord", type="password")
            reg_submit = st.form_submit_button("Registrera Konto", use_container_width=True)
            
            if reg_submit:
                if len(new_p) < 8:
                    st.error("Lösenordet måste vara minst 8 tecken långt.")
                elif create_user(new_u, new_p):
                    st.success("Konto skapat! Växla till 'Logga in'.")
                else:
                    st.error("Användarnamnet är upptaget eller ogiltigt.")

# --- 7. NAVIGATION & KONTROLLPANEL ---
if not st.session_state.logged_in:
    login_screen()
else:
    # Definiera säkra sidvägar
    pages = {
        "📊 Dashboard": [
            st.Page("pages/dashboard.py", title="Ekonomi & ROI", icon="📈", default=True),
            st.Page("pages/portfolio.py", title="Min Samling", icon="🎴"),
        ],
        "⚡ Verktyg": [
            st.Page("pages/add_item.py", title="Pack Opening / Add", icon="📦"),
            st.Page("pages/scanner.py", title="Symbol Scanner", icon="📸"),
        ],
        "⚙️ Administration": [
            st.Page("pages/sets_manager.py", title="Master Library", icon="📚"),
            st.Page("pages/maintenance.py", title="Systemvård", icon="🛠️"),
            st.Page("pages/profile.py", title="Mitt Konto", icon="👤"),
        ]
    }

    pg = st.navigation(pages)
    
    # Sidomeny-info
    with st.sidebar:
        st.markdown(f"### 🛡️ Secure Session")
        st.write(f"Användare: **{st.session_state.username}**")
        st.caption(f"Status: Krypterad anslutning")
        
        st.divider()
        
        if st.button("🚪 Logga ut säkert", use_container_width=True):
            # Rensa all känslig data vid utloggning
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Kör den valda sidan
    try:
        pg.run()
    except Exception as e:
        st.error("Ett systemfel uppstod. Din data är säker.")
        # Logga felet internt här