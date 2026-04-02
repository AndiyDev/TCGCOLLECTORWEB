import streamlit as st
from database import init_db, verify_user, register_user

# 1. Sidokonfiguration
st.set_page_config(
    page_title="Collectr Pro",
    page_icon="🔮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Initiera Session State (Säkerhetsspärr mot krascher på undersidor)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "currency" not in st.session_state:
    st.session_state.currency = "SEK"

# 3. Custom CSS - Design & Holo-effekter
def load_custom_css():
    st.markdown("""
    <style>
    /* Dölj Streamlits standard-deployknapp */
    .stAppDeployButton {display:none;}
    
    /* Snyggare Metrics-boxar */
    [data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }

    /* HOLO & REVERSE HOLO EFFEKTER (Används i hela appen) */
    .card-wrapper {
        position: relative;
        display: inline-block;
        width: 100%;
        border-radius: 10px;
        overflow: hidden;
    }
    
    .holo-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(125deg, 
            rgba(255,255,255,0) 30%, 
            rgba(255,255,255,0.3) 40%, 
            rgba(255,255,255,0) 50%);
        background-size: 200% 200%;
        animation: shimmer 3s infinite linear;
        pointer-events: none;
        mix-blend-mode: color-dodge;
    }

    .reverse-holo-overlay {
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(125deg, 
            rgba(255,0,0,0.1) 0%, 
            rgba(0,255,0,0.1) 50%, 
            rgba(0,0,255,0.1) 100%);
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

    /* Knappar med hover-effekt */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        border-color: #00ff88;
        color: #00ff88;
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# 4. Försök initiera databasen
try:
    init_db()
except Exception as e:
    st.error(f"Kunde inte ansluta till databasen: {e}")

# 5. Inloggnings- och registreringsvy
def login_screen():
    st.title("🔮 Collectr Pro v3.0")
    st.write("Din personliga TCG-portfolio och marknadskoll.")
    
    # Systemåterställning - Viktig vid första körning eller större uppdateringar
    with st.expander("⚠️ Systemåterställning (Använd om appen kraschar efter uppdatering)"):
        st.write("Denna knapp raderar ALLA tabeller och bygger upp dem på nytt enligt v3-strukturen.")
        if st.button("🚨 FORCE RESET DATABASE"):
            from sqlalchemy import text
            conn = st.connection("mysql", type="sql")
            with conn.session as s:
                # Radera i ordning pga Foreign Keys
                tables = ["user_items", "global_cards", "sealed_collection", "portfolio_history", "wishlist", "users", "collection"]
                for t in tables:
                    s.execute(text(f"DROP TABLE IF EXISTS {t}"))
                s.commit()
            init_db()
            st.success("Databasen återställd! Ladda om sidan nu (F5).")
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
                st.warning("Vänligen fyll i båda fälten.")

# 6. Navigeringslogik
if not st.session_state.logged_in:
    # Visa bara inloggning om man inte är inloggad
    pg = st.navigation([st.Page(login_screen, title="Login", icon="🔒")])
else:
    # Sidor tillgängliga efter inloggning
    # Se till att filerna ligger i mappen /pages/
    app_pages = [
        st.Page("pages/1_dashboard.py", title="Dashboard", icon="📊", default=True),
        st.Page("pages/6_sets.py", title="Sets & Explorer", icon="🗃️"),
        st.Page("pages/2_collection.py", title="My Portfolio", icon="📁"),
        st.Page("pages/3_add_item.py", title="Add Products", icon="➕"),
        st.Page("pages/4_sync.py", title="Sync Prices", icon="🔄"),
    ]
    
    # Sidomeny för användarinställningar
    with st.sidebar:
        st.title(f"Hej {st.session_state.username}!")
        st.selectbox("Välj valuta", ["SEK", "USD", "EUR"], key="currency")
        st.divider()
        if st.button("Logga ut", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.user_id = None
            st.rerun()
        
    pg = st.navigation(app_pages)

# Starta navigeringen
pg.run()