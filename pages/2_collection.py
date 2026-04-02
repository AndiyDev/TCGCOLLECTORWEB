import streamlit as st
import math
from database import get_user_collection, delete_from_collection, get_user_sealed, delete_sealed
from currency_utils import convert_price

st.title("Portfolio")
currency = st.session_state.currency

# FIX: Nu använder vi vår korrekta funktion från databasen istället för conn.query!
df = get_user_collection(st.session_state.user_id)

# --- Sök & Filtrering ---
c_search, c_sort = st.columns([2, 1])
with c_search:
    search_q = st.text_input("🔍 Sök kortnamn...", label_visibility="collapsed", placeholder="Sök i samlingen...")
with c_sort:
    sort_by = st.selectbox("Sortera", ["Nyast tillagd", "Värde (Högst)", "Värde (Lägst)", "A-Ö"], label_visibility="collapsed")

if not df.empty:
    if search_q:
        df = df[df['item_name'].str.contains(search_q, case=False, na=False)]

    if sort_by == "Värde (Högst)":
        df = df.sort_values(by="market_value", ascending=False)
    elif sort_by == "Värde (Lägst)":
        df = df.sort_values(by="market_value", ascending=True)
    elif sort_by == "A-Ö":
        df = df.sort_values(by="item_name", ascending=True)
    else:
        df = df.sort_values(by="id", ascending=False)

    if not df.empty:
        # --- Paginering ---
        ITEMS_PER_PAGE = 24
        total_pages = math.ceil(len(df) / ITEMS_PER_PAGE)

        if "current_page" not in st.session_state:
            st.session_state.current_page = 1

        if "last_search" not in st.session_state or st.session_state.last_search != search_q:
            st.session_state.current_page = 1
            st.session_state.last_search = search_q

        if st.session_state.current_page > total_pages:
            st.session_state.current_page = total_pages

        st.divider()

        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_df = df.iloc[start_idx:end_idx]

        cols = st.columns(4)
        for idx, row in page_df.reset_index(drop=True).iterrows():
            with cols[idx % 4]:
                # Streamlit-uppdatering: width="stretch"
                # -- KONTROLLERA HOLO/REVERSE HOLO --
                variant = row.get('variant', 'Normal')
                
                if "Reverse Holo" in variant:
                    # Visa kortet med regnbågs-filter
                    st.markdown(f"""
                    <div class="card-wrapper">
                        <img src="{row['image_url']}">
                        <div class="reverse-holo-overlay"></div>
                    </div>
                    """, unsafe_allow_html=True)
                elif "Holo" in variant:
                    # Visa kortet med standard-blänk
                    st.markdown(f"""
                    <div class="card-wrapper">
                        <img src="{row['image_url']}">
                        <div class="holo-overlay"></div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # Visa vanligt kort utan effekter
                    st.image(row['image_url'], width="stretch")
                    
                st.markdown(f"**{row['item_name']}**")
                price = convert_price(row['market_value'], currency)
                st.write(f"**{price:,.2f} {currency}**")
                
                grade_info = f" | {row['grade_company']} {row['grade_value']}" if row.get('is_graded') else ""
                st.caption(f"Qty: {row['quantity']} | {row['variant']}{grade_info}")
                
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Details", key=f"det_{row['id']}"):
                        st.query_params["card_id"] = row['api_id']
                        st.switch_page("pages/7_card_details.py")
                with c2:
                    if st.button("🗑️", key=f"del_{row['id']}"):
                        delete_from_collection(row['id'], st.session_state.user_id)
                        st.rerun()

        st.divider()
        col_prev, col_page, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("⬅️ Föregående", disabled=(st.session_state.current_page == 1)):
                st.session_state.current_page -= 1
                st.rerun()
        with col_page:
            st.markdown(f"<div style='text-align: center;'>Sida {st.session_state.current_page} av {total_pages}</div>", unsafe_allow_html=True)
        with col_next:
            if st.button("Nästa ➡️", disabled=(st.session_state.current_page == total_pages)):
                st.session_state.current_page += 1
                st.rerun()
    else:
        st.warning("Inga kort matchade sökningen.")
else:
    st.info("Inga singelkort i samlingen än.")

# --- SEALED COLLECTION ---
st.divider()
st.header("Sealed Collection")
sealed_df = get_user_sealed(st.session_state.user_id)

if not sealed_df.empty:
    cols2 = st.columns(4)
    for idx, row in sealed_df.iterrows():
        with cols2[idx % 4]:
            # Streamlit-uppdatering: width="stretch"
            st.image(row['image_url'], width="stretch")
            st.markdown(f"**{row['product_name']}**")
            st.write(f"{convert_price(row['market_value'], currency):,.2f} {currency}")
            st.caption(f"Qty: {row['quantity']} | {row['product_type']}")
            if st.button("🗑️ Ta bort", key=f"dels_{row['id']}"):
                delete_sealed(row['id'], st.session_state.user_id)
                st.rerun()
else:
    st.info("Inga oöppnade produkter än.")