import streamlit as st
from database import init_db, verify_user

st.set_page_config(page_title="Collectr Pro", layout="wide", initial_sidebar_state="collapsed")
init_db()

if "logged_in" not in st.session_state:
    st.session_state.update({"logged_in": False, "user_id": None, "currency": "SEK"})

    if not st.session_state.logged_in:
        st.title("Collectr Clone")
            u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                    if st.button("Login"):
                            uid = verify_user(u, p)
                                    if uid:
                                                st.session_state.update({"logged_in": True, "user_id": uid})
                                                            st.rerun()
                                                                st.stop()

                                                                # Navigation (Mobil-liknande bottenmeny simuleras här)
                                                                pg = st.navigation([
                                                                    st.Page("pages/1_dashboard.py", title="Home", icon="🏠"),
                                                                        st.Page("pages/3_add_item.py", title="Search", icon="🔍"),
                                                                            st.Page("pages/2_collection.py", title="Portfolio", icon="📁"),
                                                                                st.Page("pages/6_sets.py", title="Sets", icon="🗃️"),
                                                                                    st.Page("pages/7_card_details.py", title="Details", icon="📄")
                                                                                    ])
                                                                                    pg.run()
                                                                                    