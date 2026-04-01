import streamlit as st
from database import init_db, verify_user

# 1. Konfiguration (Måste vara först)
st.set_page_config(page_title="Collectr Pro", layout="wide", initial_sidebar_state="collapsed")

# 2. Initiera Session State
if "logged_in" not in st.session_state:
    st.session_state.update({
            "logged_in": False, 
                    "user_id": None, 
                            "username": None,
                                    "currency": "SEK"
                                        })

                                        # 3. Initiera Databas
                                        try:
                                            init_db()
                                            except Exception as e:
                                                st.error(f"Database connection failed: {e}")
                                                    st.stop()

                                                    # 4. Autentiseringsvy
                                                    if not st.session_state.logged_in:
                                                        st.title("Collectr Pro - Login")
                                                            
                                                                # Använd en container för att hålla ordning på indenteringen
                                                                    with st.container():
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
                                                                                                                                                                                                                        st.error("Invalid username or password.")
                                                                                                                                                                                                                            st.stop()

                                                                                                                                                                                                                            # 5. Navigation (Visas endast om inloggad)
                                                                                                                                                                                                                            pg = st.navigation([
                                                                                                                                                                                                                                st.Page("pages/1_dashboard.py", title="Home", icon="🏠"),
                                                                                                                                                                                                                                    st.Page("pages/3_add_item.py", title="Search", icon="🔍"),
                                                                                                                                                                                                                                        st.Page("pages/2_collection.py", title="Portfolio", icon="📁"),
                                                                                                                                                                                                                                            st.Page("pages/6_sets.py", title="Sets", icon="🗃️"),
                                                                                                                                                                                                                                                st.Page("pages/7_card_details.py", title="Details", icon="📄")
                                                                                                                                                                                                                                                ])

                                                                                                                                                                                                                                                pg.run()
                                                                                                                                                                                                                                                