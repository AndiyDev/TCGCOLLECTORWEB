import streamlit as st
import math
from database import get_user_collection, delete_from_collection
from currency_utils import convert_price

st.title("Portfolio")
df = get_user_collection(st.session_state.user_id)
currency = st.session_state.currency

if df.empty:
    st.info("Samlingen är tom.")
    st.stop()

# --- Sök & Filtrering ---
c_search, c_sort = st.columns([2, 1])
with c_search:
    search_q = st.text_input("🔍 Sök kortnamn...", label_visibility="collapsed", placeholder="Sök i samlingen...")
with c_sort:
    sort_by = st.selectbox("Sortera", ["Nyast tillagd", "Värde (Högst)", "Värde (Lägst)", "A-Ö"], label_visibility="collapsed")

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

if df.empty:
    st.warning("Inga kort matchade sökningen.")
    st.stop()

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
        st.image(row['image_url'], use_container_width=True)
        st.markdown(f"**{row['item_name']}**")
        price = convert_price(row['market_value'], currency)
        st.write(f"**{price:,.2f} {currency}**")
        st.caption(f"Qty: {row['quantity']} | {row['variant']}")
        
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