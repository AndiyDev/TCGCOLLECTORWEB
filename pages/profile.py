import streamlit as st
import pandas as pd
from database import get_conn, get_user_portfolio
from sqlalchemy import text
import io

# BUG FIX #5: Removed st.set_page_config() — must only be called once in app.py

# --- AUTH GUARD ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Logga in för att se din profil.")
    st.stop()

uid = st.session_state.user_id
username = st.session_state.username

st.title(f"👤 Profil: {username}")
st.caption(f"Medlem sedan: {st.session_state.get('member_since', '2024-05-01')}")

# --- FLIKAR ---
tab1, tab2, tab3 = st.tabs(["📊 Avancerad Statistik", "📥 Export & Backup", "⚙️ Inställningar"])

# --- FLIK 1: AVANCERAD STATISTIK ---
with tab1:
    st.subheader("Din Samlar-resa")

    conn = get_conn()
    condition_stats = conn.query("""
        SELECT condition_rank, COUNT(*) as count 
        FROM user_items WHERE user_id = :uid 
        GROUP BY condition_rank
    """, params={"uid": uid})

    variant_stats = conn.query("""
        SELECT variant, COUNT(*) as count 
        FROM user_items WHERE user_id = :uid 
        GROUP BY variant
    """, params={"uid": uid})

    c1, c2 = st.columns(2)
    with c1:
        st.write("**Skick-fördelning**")
        if not condition_stats.empty:
            st.bar_chart(condition_stats.set_index('condition_rank'))
        else:
            st.info("Ingen data än.")

    with c2:
        st.write("**Varianter i samlingen**")
        if not variant_stats.empty:
            st.table(variant_stats)
        else:
            st.info("Ingen data än.")

    st.divider()

    st.write("**Pack Luck (Genomsnittlig ROI per Booster)**")
    luck_query = """
        SELECT 
            bo.set_intern_id,
            bo.purchase_price,
            SUM(CASE 
                WHEN ui.variant = 'Holo' THEN gc.price_holo_nm
                WHEN ui.variant = 'Reverse' THEN gc.price_reverse_nm
                ELSE gc.price_normal_nm
            END) as current_value
        FROM booster_openings bo
        JOIN user_items ui ON bo.id = ui.opening_id
        JOIN global_cards gc ON ui.api_id = gc.api_id
        WHERE bo.user_id = :uid
        GROUP BY bo.id
    """
    luck_df = conn.query(luck_query, params={"uid": uid})

    if not luck_df.empty:
        luck_df['profit'] = luck_df['current_value'] - luck_df['purchase_price']
        avg_profit = luck_df['profit'].mean()
        st.metric("Snittvinst per Booster", f"{avg_profit:.2f} SEK", delta=f"{avg_profit:.2f}")
    else:
        st.info("Öppna några boosters för att se din 'Pack Luck'!")

# --- FLIK 2: EXPORT & BACKUP ---
with tab2:
    st.subheader("Exportera din Data")
    st.write("Ladda ner din samling som en Excel-fil för att ha en lokal backup.")

    df_full = get_user_portfolio(uid)

    if not df_full.empty:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_full.to_excel(writer, index=False, sheet_name='Min Samling')

        st.download_button(
            label="📥 Ladda ner Portfolio (.xlsx)",
            data=buffer.getvalue(),
            file_name=f"TCG_Collection_{username}.xlsx",
            mime="application/vnd.ms-excel",
            type="primary"
        )
    else:
        st.warning("Ingen data att exportera.")

# --- FLIK 3: INSTÄLLNINGAR ---
with tab3:
    st.subheader("App-inställningar")

    current_currency = st.session_state.get("currency", "SEK")
    currency_options = ["SEK", "EUR", "USD"]
    currency_index = currency_options.index(current_currency) if current_currency in currency_options else 0

    new_currency = st.selectbox("Valuta", currency_options, index=currency_index)
    if new_currency != current_currency:
        st.session_state.currency = new_currency
        st.success(f"Valuta ändrad till {new_currency}.")

    st.divider()

    st.write("**Radera konto**")
    st.warning("Att radera kontot raderar ALL din data permanent och kan inte ångras.")

    # BUG FIX #12: Replaced impossible nested st.button with a session-state confirm pattern
    if "confirm_delete_account" not in st.session_state:
        st.session_state.confirm_delete_account = False

    if not st.session_state.confirm_delete_account:
        if st.button("🔴 Radera Mitt Konto", type="secondary"):
            st.session_state.confirm_delete_account = True
            st.rerun()
    else:
        st.error("Detta raderar ALL din data permanent. Är du absolut säker?")
        col_yes, col_no = st.columns(2)
        if col_yes.button("JA, RADERA ALLT", type="primary"):
            conn = get_conn()
            with conn.session as s:
                s.execute(text("DELETE FROM user_items WHERE user_id = :uid"), {"uid": uid})
                s.execute(text("DELETE FROM booster_openings WHERE user_id = :uid"), {"uid": uid})
                s.execute(text("DELETE FROM user_transactions WHERE user_id = :uid"), {"uid": uid})
                s.execute(text("DELETE FROM users WHERE id = :uid"), {"uid": uid})
                s.commit()
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Kontot har raderats. Du loggas ut.")
            st.rerun()
        if col_no.button("Avbryt"):
            st.session_state.confirm_delete_account = False
            st.rerun()
