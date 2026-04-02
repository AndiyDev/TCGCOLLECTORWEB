import streamlit as st
import pandas as pd
from database import get_conn, get_user_portfolio
import io

st.set_page_config(page_title="My Profile", page_icon="👤", layout="wide")

# 1. SÄKERHETSKOLL
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
    # Hämta fördelning av skick (Condition)
    condition_stats = conn.query("""
        SELECT condition_rank, COUNT(*) as count 
        FROM user_items WHERE user_id = :uid 
        GROUP BY condition_rank
    """, params={"uid": uid})
    
    # Hämta fördelning av varianter
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
            
    st.divider()
    
    # Pack Luck (Booster ROI)
    st.write("**Pack Luck (Genomsnittlig ROI per Booster)**")
    # Vi räknar ut ROI för varje öppnat paket
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
        # Skapa Excel i minnet
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
    
    new_currency = st.selectbox("Valuta", ["SEK", "EUR", "USD"], index=0)
    st.session_state.currency = new_currency
    
    display_mode = st.radio("Standardvy i Galleri", ["Grid (Bilder)", "Lista (Kompakt)"])
    
    st.divider()
    
    if st.button("🔴 Radera Mitt Konto", type="secondary"):
        st.error("Detta raderar ALL din data permanent. Är du absolut säker?")
        if st.button("JA, RADERA ALLT"):
            # Här skulle en DELETE-logik ligga
            st.info("Funktionen är låst för att förhindra olyckor.")

    st.success("Inställningar sparade lokalt för denna session.")