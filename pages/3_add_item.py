import streamlit as st
import requests
from database import add_to_collection

st.title("Sök och lägg till kort")

search_term = st.text_input("Sök Pokémon-kort (ex. 'Charizard')")

if st.button("Sök API", type="primary"):
    if search_term.strip():
            with st.spinner("Hämtar data..."):
                        # Hämtar max 12 resultat för att ladda snabbt
                                    url = f"https://api.pokemontcg.io/v2/cards?q=name:\"{search_term}\"&pageSize=12"
                                                res = requests.get(url)
                                                            
                                                                        if res.status_code == 200:
                                                                                        st.session_state.search_results = res.json().get("data", [])
                                                                                                    else:
                                                                                                                    st.error("Kunde inte nå Pokémon TCG API.")

                                                                                                                    if "search_results" in st.session_state and st.session_state.search_results:
                                                                                                                        st.divider()
                                                                                                                            cols = st.columns(3) # Bättre anpassat för mobila skärmar
                                                                                                                                
                                                                                                                                    for idx, card in enumerate(st.session_state.search_results):
                                                                                                                                            with cols[idx % 3]:
                                                                                                                                                        img_url = card.get("images", {}).get("small", "")
                                                                                                                                                                    name = card.get("name", "Okänd")
                                                                                                                                                                                set_name = card.get("set", {}).get("name", "")
                                                                                                                                                                                            
                                                                                                                                                                                                        # Försök hämta pris från Cardmarket, annars 0
                                                                                                                                                                                                                    price = card.get("cardmarket", {}).get("prices", {}).get("averageSellPrice", 0.0)
                                                                                                                                                                                                                                
                                                                                                                                                                                                                                            if img_url:
                                                                                                                                                                                                                                                            st.image(img_url, use_column_width=True)
                                                                                                                                                                                                                                                                        st.markdown(f"**{name}**")
                                                                                                                                                                                                                                                                                    st.caption(f"Set: {set_name}")
                                                                                                                                                                                                                                                                                                st.write(f"**Värde:** {price} EUR")
                                                                                                                                                                                                                                                                                                            
                                                                                                                                                                                                                                                                                                                        # Unik nyckel per knapp är ett krav i Streamlit loopar
                                                                                                                                                                                                                                                                                                                                    if st.button("Lägg till", key=f"add_{card['id']}"):
                                                                                                                                                                                                                                                                                                                                                    add_to_collection(st.session_state.user_id, f"{name} ({set_name})", float(price), img_url)
                                                                                                                                                                                                                                                                                                                                                                    st.success("Tillagd i samlingen!")
                                                                                                                                                                                                                                                                                                                                                                    