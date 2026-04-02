import streamlit as st
from database import init_db, verify_user, register_user

# 1. Konfiguration av sidan
st.set_page_config(
    page_title="Collectr Pro",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Initiera Session State (Säkerhetsspärr mot krascher)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "currency" not in st.session_state:
    st.session_state.currency = "SEK"

# 3. Custom CSS för Design & Holo-effekter
def load_custom_css():
    st.markdown("""
    <style>
    /* Dölj Deploy-knappen men behåll menyn */
    .stAppDeployButton {display:none;}
    
    /* Metrics Design */
    [data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
    }

    /* HOLO & REVERSE HOLO CSS-SHADERS */
    .card-wrapper {
        position: relative;
        display: inline-block;
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
    }
    
    .holo-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(125deg, rgba(255,255,255,0) 30%, rgba(255,255,255,0.3) 40%, rgba(255,255,255,0) 50%);
        background-size: 200% 200%;
        animation: shimmer 3s infinite linear;
        pointer-events: none;
        mix-blend-mode: color-dodge;
    }

    .reverse-holo-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(125deg, rgba(255,0,0,0.1) 0%, rgba(0,255,0,0.1) 50%, rgba(0,0,255,0.1) 100%);
        background-size: 300% 300%;
        animation: shimmer 5s infinite linear;
        pointer-events: none;
        mix-blend-mode: overlay;
        opacity: 0.7;
    }

    @keyframes shimmer {
        0% { background-position: 100% 100%; }
        100% { background-position: 0% 0%; }
    }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# 4. Databas-initiering
try:
    init_db()
except Exception as e:
    st.error(f"Kunde inte ansluta till databasen: {e}")

# 5. Inloggningsskärm
def login_screen():
    st.title("🔮 Collectr Pro v3.0")
    
    # System Reset (Dold i en expander för säkerhets skull)
    with st.expander("⚠️ Systemåterställning (Använd vid krasch eller uppgradering)"):
        st.write("Denna knapp raderar ALL data och skapar nya tabeller för v3.0.")
        if st.button("🚨 FORCE RESET DATABASE"):
            from sqlalchemy import text
            conn = st.connection("mysql", type="sql")
            with conn.session as s:
                # Tabeller raderas i rätt ordning för att undvika Foreign Key-fel
                tables = ["user_items", "global_cards", "sealed_collection", "users", "wishlist", "portfolio_history", "collection"]
                for t in tables:
                    s.execute(text(f"DROP TABLE IF EXISTS {t}"))
                s.commit()
            init_db()
            st.success("Databasen är rensad! Ladda om sidan (F5).")
            st.stop()

    tab_login, tab_register = st.tabs(["Logga in", "Skapa konto"])
    
    with tab_login:
        u_login = st.text_input("Användarnamn", key="login_user")
        p_login = st.text_input("Lösenord", type="password", key="login_pass")
        if st.button("Logga in", use_container_width=True, type="primary"):
            uid = verify_user(u_login, p_login)
            if uid:
                st.session_state.logged_in = True
                st.session_state.user_id = uid
                st.session_state.username = u_login
                st.rerun()
            else:
                st.error("Fel användarnamn eller lösenord.")

    with tab_register:
        u_reg = st.text_input("Välj användarnamn", key="reg_user")
        p_reg = st.text_input("Välj lösenord", type="password", key="reg_pass")
        if st.button("Registrera konto", use_container_width=True):
            if u_reg and p_reg:
                if register_user(u_reg, p_reg):
                    st.success("Konto skapat! Du kan nu logga in.")
                else:
                    st.error("Användarnamnet är redan upptaget.")
            else:
                st.warning("Fyll i alla fält.")

# 6. Navigering & Sidor
if not st.session_state.logged_in:
    # Om ej inloggad, visa bara login-sidan och dölj menyn
    pg = st.navigation([st.Page(login_screen, title="Login", icon="🔒")])
else:
    # Definiera sidorna för inloggade användare
    app_pages = [
        st.Page("pages/1_dashboard.py", title="Dashboard", icon="📊", default=True),
        st.Page("pages/6_sets.py", title="Sets & Explorer", icon="🗃️"),
        st.Page("pages/2_collection.py", title="My Portfolio", icon="📁"),
        st.Page("pages/3_add_item.py", title="Add Products", icon="➕"),
        st.Page("pages/4_sync.py", title="Sync Prices", icon="🔄"),
    ]
    
    # Sidomeny-header
    st.sidebar.title(f"Välkommen {st.session_state.username}!")
    st.sidebar.selectbox("Valuta", ["SEK", "USD", "EUR"], key="currency")
    
    if st.sidebar.button("Logga ut", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.user_id = None
        st.rerun()
        
    pg = st.navigation(app_pages)

# Kör appen
pg.run()