import streamlit as st
import pandas as pd
from database import get_conn, get_financial_summary, get_user_portfolio
import time

# --- AUTH GUARD ---
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

st.title(f"🚀 {st.session_state.username}'s Dashboard")
uid = st.session_state.user_id
currency = st.session_state.get("currency", "SEK")

# --- HÄMTA DATA ---
stats = get_financial_summary(uid)
df_portfolio = get_user_portfolio(uid)

# --- BERÄKNINGAR ---
total_spent = float(stats['total_spent'] or 0)
total_earned = float(stats['total_earned'] or 0)

def calculate_market_val(row):
    if row['variant'] == 'Holo':
        return float(row['price_holo_nm'] or 0)
    elif row['variant'] == 'Reverse':
        return float(row['price_reverse_nm'] or 0)
    else:
        return float(row['price_normal_nm'] or 0)

if not df_portfolio.empty:
    df_portfolio['current_val'] = df_portfolio.apply(calculate_market_val, axis=1)
    current_assets_value = df_portfolio['current_val'].sum()
else:
    current_assets_value = 0

total_roi = (current_assets_value + total_earned) - total_spent

# --- SEKTION 1: EKONOMI-ÖVERSIKT ---
st.write("### 💰 Ekonomi & Budget")
m1, m2, m3, m4 = st.columns(4)

m1.metric("Total Investering", f"{total_spent:,.0f} {currency}")
m2.metric("Nuvarande Värde", f"{current_assets_value:,.0f} {currency}")
m3.metric("Sålt för (Cash)", f"{total_earned:,.0f} {currency}")

roi_color = "normal" if total_roi >= 0 else "inverse"
m4.metric("Netto Vinst/Förlust", f"{total_roi:,.0f} {currency}", delta=f"{total_roi:,.0f}", delta_color=roi_color)

st.divider()

# --- SEKTION 2: SENASTE AKTIVITET ---
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("🕒 Senaste Köp & Öppningar")

    conn = get_conn()

    # BUG FIX #8: Some MySQL drivers reject a named parameter used twice in one query.
    # Split the UNION ALL into two separate queries and concatenate in Python instead.
    recent_cards = conn.query("""
        SELECT 'Kort' as type, gc.name as label, ui.purchase_price as cost, ui.date_added as dt
        FROM user_items ui
        JOIN global_cards gc ON ui.api_id = gc.api_id
        WHERE ui.user_id = :uid
        ORDER BY ui.date_added DESC
        LIMIT 5
    """, params={"uid": uid})

    recent_boosters = conn.query("""
        SELECT 'Booster' as type, set_intern_id as label, purchase_price as cost, date_opened as dt
        FROM booster_openings
        WHERE user_id = :uid
        ORDER BY date_opened DESC
        LIMIT 5
    """, params={"uid": uid})

    recent_activity = (
        pd.concat([recent_cards, recent_boosters], ignore_index=True)
        .sort_values("dt", ascending=False)
        .head(5)
    )

    if not recent_activity.empty:
        for _, row in recent_activity.iterrows():
            with st.expander(f"{row['type']}: {row['label']} — {row['cost']} {currency}"):
                st.write(f"Inköpt/Öppnat: {row['dt']}")
                if row['type'] == 'Booster':
                    st.info("Klicka på 'Booster Historik' i menyn för att se innehållet.")
    else:
        st.info("Ingen aktivitet loggad än.")

with col_right:
    st.subheader("📦 Snabbstatistik")
    total_items = len(df_portfolio)
    unique_sets = df_portfolio['set_intern_id'].nunique() if not df_portfolio.empty else 0

    st.write(f"**Antal kort:** {total_items}")
    st.write(f"**Antal unika sets:** {unique_sets}")

    st.write("Mål: 1000 kort")
    st.progress(min(total_items / 1000, 1.0))

st.divider()

# --- SEKTION 3: BOOSTER-ANALYS ---
st.subheader("🧪 Top Performing Packs (ROI)")
if not df_portfolio.empty and 'opening_id' in df_portfolio.columns:
    booster_roi = (
        df_portfolio[df_portfolio['opening_id'].notna()]
        .groupby('opening_id')
        .agg(total_card_value=('current_val', 'sum'))
        .reset_index()
    )

    if not booster_roi.empty:
        booster_prices = conn.query(
            "SELECT id, purchase_price, set_intern_id FROM booster_openings WHERE user_id = :uid",
            params={"uid": uid}
        )
        booster_roi = booster_roi.merge(booster_prices, left_on='opening_id', right_on='id', how='left')
        booster_roi['roi'] = booster_roi['total_card_value'] - booster_roi['purchase_price']
        booster_roi = booster_roi.sort_values('roi', ascending=False)

        st.dataframe(
            booster_roi[['set_intern_id', 'purchase_price', 'total_card_value', 'roi']].rename(columns={
                'set_intern_id': 'Set',
                'purchase_price': 'Kostnad (SEK)',
                'total_card_value': 'Värde (SEK)',
                'roi': 'ROI (SEK)'
            }),
            use_container_width=True
        )
    else:
        st.caption("Statistik för dina öppningar dyker upp här när du börjar öppna paket.")
else:
    st.info("Börja öppna boosters för att se din 'Pack Luck' statistik!")
