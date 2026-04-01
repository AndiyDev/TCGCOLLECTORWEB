import streamlit as st
import requests
import pandas as pd
from database import get_conn

card_id = st.query_params.get("card_id", "sv3pt5-1")
card = requests.get(f"https://api.pokemontcg.io/v2/cards/{card_id}").json().get('data')

st.image(card['images']['large'], use_column_width=True)
st.title(card['name'])
st.caption(f"{card['set']['name']} • {card['number']}/{card['set']['printedTotal']}")

# Prisgraf (Mockad trend)
st.subheader("Price History")
chart_data = pd.DataFrame({"Price": [100, 110, 95, 105, 120, 115]})
st.line_chart(chart_data, color="#00ff88")

st.write("### Ungraded")
# Här läggs kvantitetskontroller (+/-)
