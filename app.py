import streamlit as st
from database import init_db, verify_user, register_user, get_user_id_by_name, get_user_collection, get_user_sealed
from currency_utils import convert_price

    # 1. Konfiguration
st.set_page_config(page_title="Collectr Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. Design & PWA
def load_custom_css():
    st.markdown("""
    <style>
    /* Dölj Streamlits standardmenyer och footer, men BEHÅLL headern för sidomenyns knapp! */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Dölj istället specifikt "Deploy"-knappen uppe till höger */
    .stAppDeployButton {display:none;}

    /* Modern kort-design för Metrics (Siffrorna på Dashboarden) */
    [data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: transform 0.2s ease;
    }
    [data-testid="metric-container"]:hover {
        transform: translateY(-2px);
    }

    /* Snyggare knappar med hover-effekt */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 255, 136, 0.2);
        border-color: #00ff88;
        color: #00ff88;
    }

    /* Design för flikar (Tabs) */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        background-color: #161a20;
        border: 1px solid #333;
        border-bottom: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #1e1e1e;
        border-top: 2px solid #00ff88;
    }
    
    /* Avskiljare */
    hr {
        border-top: 1px solid #333;
    }
    </style>
    """, unsafe_allow_html=True)

def setup_pwa():
    st.html("""
        <script>
            const doc = window.parent.document;
            if (!doc.querySelector("link[rel='manifest']")) {
                const manifest = doc.createElement('link'); manifest.rel = 'manifest'; manifest.href = '/app/static/manifest.json'; doc.head.appendChild(manifest);
            }
            if (!doc.querySelector("link[rel='apple-touch-icon']")) {
                const appleIcon = doc.createElement('link'); appleIcon.rel = 'apple-touch-icon'; appleIcon.href = 'https://upload.wikimedia.org/wikipedia/commons/5/53/Pok%C3%A9_Ball_icon.svg'; doc.head.appendChild(appleIcon);
            }
            if ('serviceWorker' in window.parent.navigator) {
                window.parent.navigator.serviceWorker.register('/app/static/sw.js').catch(err => console.log('PWA SW failed:', err));
            }
        </script>
    """)

load_custom_css()
setup_pwa()

# 3. Initiera databas
try:
    init_db()
except Exception as e:
    st.error(f"Databasfel: {e}")
    st.stop()

# --- NY KOD: KONTROLLERA OM DET ÄR EN DELNINGSLÄNK (PUBLIC MODE) ---
target_user = st.query_params.get("user")

if target_user:
    # Skapa en skräddarsydd vy som inte kräver inloggning
    def public_showcase():
        uid = get_user_id_by_name(target_user)
        if not uid:
            st.error(f"Kunde inte hitta användaren: {target_user}")
            st.stop()
            
        st.title(f"🏆 {target_user.capitalize()}'s Showcase")
        st.caption("Detta är en skrivskyddad vy. Inköpspriser är dolda för integritet.")
        
        df_cards = get_user_collection(uid)
        df_sealed = get_user_sealed(uid)
        
        # Räkna ut värdet
        val_cards = (df_cards['market_value'] * df_cards['quantity']).sum() if not df_cards.empty else 0.0
        val_sealed = (df_sealed['market_value'] * df_sealed['quantity']).sum() if not df_sealed.empty else 0.0
        total_val = val_cards + val_sealed
        
        st.metric("Total Market Value", f"{total_val:,.2f} SEK")
        st.divider()
        
        # Visa Korten
        st.subheader("Card Collection")
        if not df_cards.empty:
            cols = st.columns(4)
            for idx, row in df_cards.iterrows():
                with cols[idx % 4]:
                    st.image(row['image_url'], width="stretch")
                    st.markdown(f"**{row['item_name']}**")
                    grade_info = f" | {row['grade_company']} {row['grade_value']}" if row.get('is_graded') else ""
                    st.caption(f"Qty: {row['quantity']} | {row['variant']}{grade_info}")
        else:
            st.info("Inga kort i samlingen.")
            
        st.divider()
        
        # Visa Sealed
        st.subheader("Sealed Collection")
        if not df_sealed.empty:
            cols2 = st.columns(4)
            for idx, row in df_sealed.iterrows():
                with cols2[idx % 4]:
                    st.image(row['image_url'], width="stretch")
                    st.markdown(f"**{row['product_name']}**")
                    st.caption(f"Qty: {row['quantity']} | {row['product_type']}")
        else:
            st.info("Inga oöppnade produkter.")

    # Kör ENDAST Showcase-sidan och stäng sedan ute resten av appen
    pg = st.navigation([st.Page(public_showcase, title=f"{target_user}'s Collection", icon="👀")])
    pg.run()
    st.stop()
# -------------------------------------------------------------------

# 4. Standard inloggnings-flöde (om det INTE är en public länk)
defaults = {"logged_in": False, "user_id": None, "username": None, "currency": "SEK"}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

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
                st.error("Minst 3 tecken för namn och 6 för lösenord.")
            else:
                success = register_user(u_reg, p_reg)
                if success:
                    st.success("Konto skapat! Byt till fliken 'Logga in'.")
                else:
                    st.error("Användarnamnet är redan upptaget.")

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

if not st.session_state.logged_in:
    login_page = st.Page(login_screen, title="Autentisering", icon="🔒")
    pg = st.navigation([login_page])
else:
    pg = st.navigation(app_pages)

pg.run()