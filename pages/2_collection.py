import streamlit as st
from database import get_user_collection, delete_from_collection

st.title("Min Samling")

df = get_user_collection(st.session_state.user_id)

if df.empty:
    st.warning("Inga objekt hittades.")
    st.stop()

# Mobilvänligt Grid (4 kolumner på desktop, Streamlit wrappar automatiskt på mobil)
cols = st.columns(4)
for idx, row in df.iterrows():
    with cols[idx % 4]:
        img_src = row['image_url'] if row['image_url'] else "https://via.placeholder.com/300x400?text=Inget+Foto"
        st.image(img_src, use_column_width=True)
        st.markdown(f"**{row['item_name']}**")
        st.write(f"{row['market_value']} kr")
        
        # Unik nyckel för varje knapp
        if st.button("Ta bort", key=f"del_{row['id']}", type="secondary"):
            delete_from_collection(row['id'], st.session_state.user_id)
            st.rerun()
