import streamlit as st
import requests
from database import get_user_portfolio, add_item_to_user
from currency_utils import convert_price

# 1. SÄKERHETSSPÄRR - Förhindrar krasch om sessionen dör
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

st.title("Pokémon Sets & Explorer")

# --- API FUNKTIONER ---
@st.cache_data(ttl=86400)
def get_all_sets():
    """Hämtar alla officiella Pokémon-sets sorterat på releasedatum."""
    res = requests.get("https://api.pokemontcg.io/v2/sets?orderBy=-releaseDate")
    return res.json().get("data", []) if res.status_code == 200 else []

@st.cache_data(ttl=3600)
def get_cards_in_set(set_id):
    """Hämtar alla kort i ett specifikt set."""
    res = requests.get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{set_id}&orderBy=number")
    return res.json().get("data", []) if res.status_code == 200 else []

# --- POP-UP DIALOG (Kortdetaljer) ---
@st.dialog("Lägg till i samlingen", width="large")
def show_card_dialog(card):
    col_img, col_info = st.columns([1, 1])
    
    with col_info:
        st.subheader(card['name'])
        st.caption(f"{card['set']['name']} • #{card['number']}")
        
        # Prisberäkning
        base_price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
        currency = st.session_state.get("currency", "SEK")
        local_price = convert_price(base_price, currency)
        st.metric("Marknadsvärde", f"{local_price:,.2f} {currency}")

        st.divider()
        
        # Inmatning för samlingen
        var_sel = st.selectbox("Välj variant", ["Normal", "Reverse Holofoil", "Holofoil"], key=f"dlg_var_{card['id']}")
        p_price = st.number_input(f"Ditt inköpspris ({currency})", min_value=0.0, format="%.2f", key=f"dlg_pp_{card['id']}")
        
        if st.button("➕ Bekräfta & Lägg till", use_container_width=True, type="primary"):
            # Anropar den nya v3-funktionen som skapar en unik rad i databasen
            add_item_to_user(
                uid=st.session_state.user_id, 
                card_data=card, 
                variant=var_sel, 
                p_price=p_price
            )
            st.success(f"{card['name']} har lagts till!")
            st.rerun() # Uppdaterar "Äger"-mätaren i bakgrunden

    with col_img:
        # Visar bilden med din snygga CSS-Holo-effekt baserat på valet i dropdownen
        current_var = st.session_state.get(f"dlg_var_{card['id']}", "Normal")
        img_url = card['images']['large']
        
        if "Reverse" in current_var:
            st.markdown(f'<div class="card-wrapper"><img src="{img_url}" style="width:100%"><div class="reverse-holo-overlay"></div></div>', unsafe_allow_html=True)
        elif "Holo" in current_var:
            st.markdown(f'<div class="card-wrapper"><img src="{img_url}" style="width:100%"><div class="holo-overlay"></div></div>', unsafe_allow_html=True)
        else:
            st.image(img_url, use_container_width=True)

# --- HUVUDLOGIK ---

# Kontrollera om vi är inne i ett specifikt set
selected_set_id = st.query_params.get("set_id")

if not selected_set_id:
    # --- VY 1: LISTA ALLA SETS ---
    all_sets = get_all_sets()
    # Hämta portföljen för att visa samlingsstatistik per set
    user_portfolio = get_user_portfolio(st.session_state.user_id)
    
    st.write("Välj en expansion för att se kortlistan.")
    st.divider()
    
    cols = st.columns(4)
    for idx, s_data in enumerate(all_sets):
        with cols[idx % 4]:
            # Fast höjd på loggan för att knapparna ska hamna på samma rad
            st.markdown(f"""
                <div style="height: 120px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <img src="{s_data['images']['logo']}" style="max-height: 100%; max-width: 100%; object-fit: contain;">
                </div>
            """, unsafe_allow_html=True)
            
            # Statistik för setet
            owned_in_set = 0
            if not user_portfolio.empty:
                # Räknar unika kort (api_id) som användaren äger i detta set
                owned_in_set = user_portfolio[user_portfolio['set_id'] == s_data['id']]['api_id'].nunique()
            
            st.markdown(f"<p style='text-align: center; font-size: 0.85rem; color: #888;'>Samlat: {owned_in_set} / {s_data['printedTotal']}</p>", unsafe_allow_html=True)
            
            if st.button("Utforska", key=f"set_{s_data['id']}", use_container_width=True):
                st.query_params["set_id"] = s_data['id']
                st.rerun()
            st.divider()

else:
    # --- VY 2: VISA ALLA KORT I DET VALDA SETET ---
    if st.button("← Tillbaka till alla Sets"):
        del st.query_params["set_id"]
        st.rerun()
        
    cards = get_cards_in_set(selected_set_id)
    if not cards:
        st.error("Kunde inte ladda korten.")
        st.stop()
        
    st.subheader(f"Expansion: {cards[0]['set']['name']}")
    
    # Hämta portföljdata för att markera kort man redan äger
    user_portfolio = get_user_portfolio(st.session_state.user_id)
    
    cols = st.columns(4)
    for idx, card in enumerate(cards):
        with cols[idx % 4]:
            # Räkna totalt antal av just detta kort i samlingen
            num_owned = 0
            if not user_portfolio.empty:
                num_owned = len(user_portfolio[user_portfolio['api_id'] == card['id']])
            
            # Visar en grön badge om man äger kortet, annars en tom ruta för balansen
            if num_owned > 0:
                st.markdown(f"<div style='background: #1a231c; border: 1px solid #00ff88; color: #00ff88; padding: 4px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 5px;'>📦 Äger: {num_owned}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height: 34px;'></div>", unsafe_allow_html=True)

            st.image(card['images']['small'], use_container_width=True)
            
            # Klickar man på knappen öppnas den stora Dialog-rutan
            if st.button(f"🔍 {card['name']}", key=f"btn_{card['id']}", use_container_width=True):
                show_card_dialog(card)
                
            st.caption(f"#{card['number']} • {card.get('rarity', 'Common')}")
            st.divider()