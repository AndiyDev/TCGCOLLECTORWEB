import streamlit as st
from database import init_db, verify_user, register_user

st.set_page_config(page_title="Collectr Pro", layout="wide")

# Initiera session state
for key, val in {"logged_in": False, "user_id": None, "username": None, "currency": "SEK"}.items():
    if key not in st.session_state: st.session_state[key] = val

try: init_db()
except: pass

def login_screen():
    st.title("Collectr Pro v3.0")
    with st.expander("🚨 RESET SYSTEM"):
        if st.button("Radera & Uppgradera"):
            conn = st.connection("mysql", type="sql")
            with conn.session as s:
                for t in ["user_items", "global_cards", "sealed_collection", "users", "portfolio_history", "wishlist"]:
                    s.execute(text(f"DROP TABLE IF EXISTS {t}"))
                s.commit()
            init_db(); st.rerun()

    t1, t2 = st.tabs(["Logga in", "Skapa konto"])
    with t1:
        u = st.text_input("Användarnamn"); p = st.text_input("Lösenord", type="password")
        if st.button("Logga in", type="primary"):
            uid = verify_user(u, p)
            if uid:
                st.session_state.logged_in = True; st.session_state.user_id = uid; st.session_state.username = u; st.rerun()
    with t2:
        u_reg = st.text_input("Nytt användarnamn"); p_reg = st.text_input("Nytt lösenord", type="password")
        if st.button("Registrera"):
            if register_user(u_reg, p_reg): st.success("Klart! Logga in.")

if not st.session_state.logged_in:
    pg = st.navigation([st.Page(login_screen)])
else:
    pg = st.navigation([
        st.Page("pages/1_dashboard.py", title="Dashboard", icon="📊"),
        st.Page("pages/6_sets.py", title="Sets", icon="🗃️"),
        st.Page("pages/2_collection.py", title="Portfolio", icon="📁")
    ])
pg.run()