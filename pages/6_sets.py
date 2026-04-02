import streamlit as st
import requests
from database import get_user_collection

st.title("Pokemon Sets")

@st.cache_data(ttl=86400)
def get_all_sets():
    res = requests.get("https://api.pokemontcg.io/v2/sets")
    if res.status_code == 200:
        return res.json().get("data", [])
    return []

all_sets = get_all_sets()
user_df = get_user_collection(st.session_state.user_id)

if not all_sets:
    st.error("Kunde inte ladda sets.")
    st.stop()

cols = st.columns(2)
for idx, s_data in enumerate(all_sets[:20]):
    with cols[idx % 2]:
        set_id = s_data['id']
        owned_in_set = len(user_df[user_df['set_code'] == set_id])
        total_in_set = s_data['printedTotal']
        
        progress = owned_in_set / total_in_set if total_in_set > 0 else 0
        progress = min(progress, 1.0)
        
        st.image(s_data['images']['logo'], width=150)
        st.write(f"**Progress: {owned_in_set}/{total_in_set}**")
        st.progress(progress)