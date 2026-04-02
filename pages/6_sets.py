import streamlit as st
import requests
from database import get_user_portfolio, add_item_to_user
from currency_utils import convert_price

# 1. SÄKERHETSSPÄRR - Förhindrar KeyError: user_id
if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("Vänligen logga in på startsidan först.")
    st.stop()

st.title("Pokémon Sets")

# --- API FUNKTIONER ---
@st.cache_data(ttl=86400)
def get_all_sets():
    res = requests.get("https://api.pokemontcg.io/v2/sets?orderBy=-releaseDate")
    return res.json().get("data", []) if res.status_code == 200 else []

@st.cache_data(ttl=3600)
def get_cards_in_set(set_id):
    res = requests.get(f"https://api.pokemontcg.io/v2/cards?q=set.id:{set_id}&orderBy=number")
    return res.json().get("data", []) if res.status_code == 200 else []

# --- POP-UP RUTA (DIALOG) ---
@st.dialog("Kortdetaljer", width="large")
def show_card_dialog(card):
    c1, c2 = st.columns([1, 1])
    
    with c2:
        st.title(card['name'])
        st.caption(f"{card['set']['name']} • #{card['number']}")
        
        # Hämta marknadspris och konvertera
        base_price = card.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
        currency = st.session_state.get("currency", "SEK")
        local_price = convert_price(base_price, currency)
        st.subheader(f"Marknadsvärde: {local_price:,.2f} {currency}")

        st.divider()
        
        # Val för tillägg
        var_sel = st.selectbox("Välj variant", ["Normal", "Reverse Holofoil", "Holofoil"], key=f"sel_var_{card['id']}")
        p_price = st.number_input(f"Ditt inköpspris ({currency})", min_value=0.0, format="%.2f", key=f"pp_{card['id']}")
        
        if st.button("➕ Lägg till i samling", use_container_width=True, type="primary"):
            # Anropa den nya v3-funktionen
            add_item_to_user(
                uid=st.session_state.user_id, 
                card_data=card, 
                variant=var_sel, 
                p_price=p_price
            )
            st.success(f"Lade till {card['name']} ({var_sel})!")
            st.rerun() # Laddar om för att uppdatera "Äger"-räknaren i bakgrunden

    with c1:
        # Visa stor bild med live-effekt baserat på dropdown-valet
        current_variant = st.session_state.get(f"sel_var_{card['id']}", "Normal")
        img_url = card['images']['large']
        
        if "Reverse" in current_variant:
            st.markdown(f'<div class="card-wrapper"><img src="{img_url}"><div class="reverse-holo-overlay"></div></div>', unsafe_allow_html=True)
        elif "Holo" in current_variant:
            st.markdown(f'<div class="card-wrapper"><img src="{img_url}"><div class="holo-overlay"></div></div>', unsafe_allow_html=True)
        else:
            st.image(img_url, use_container_width=True)

# --- HUVUDLOGIK FÖR SIDAN ---

# Kontrollera om vi navigerat in i ett set via URL-parameter
selected_set_id = st.query_params.get("set_id")

if not selected_set_id:
    # --- VY 1: VISA ALLA SETS ---
    all_sets = get_all_sets()
    user_portfolio = get_user_portfolio(st.session_state.user_id)
    
    st.write("Välj ett set för att utforska alla kort.")
    st.divider()
    
    cols = st.columns(4)
    for idx, s_data in enumerate(all_sets):
        with cols[idx % 4]:
            # Centrerad logotyp-box med fast höjd för snygg linjering
            st.markdown(f"""
                <div style="height: 120px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px;">
                    <img src="{s_data['images']['logo']}" style="max-height: 100%; max-width: 100%; object-fit: contain;">
                </div>
            """, unsafe_allow_html=True)
            
            # Räkna unika kort ägda i detta set
            owned_count = 0
            if not user_portfolio.empty:
                owned_count = user_portfolio[user_portfolio['set_id'] == s_data['id']]['api_id'].nunique()
            
            st.markdown(f"<p style='text-align: center; color: #888;'>Samlat: {owned_count} / {s_data['printedTotal']}</p>", unsafe_allow_html=True)
            
            if st.button("Visa kort", key=f"set_btn_{s_data['id']}", use_container_width=True):
                st.query_params["set_id"] = s_data['id']
                st.rerun()
            st.divider()

else:
    # --- VY 2: VISA KORT I VALT SET ---
    if st.button("← Tillbaka till alla Sets"):
        del st.query_params["set_id"]
        st.rerun()
        
    cards = get_cards_in_set(selected_set_id)
    if not cards:
        st.error("Kunde inte hämta kort.")
        st.stop()
        
    st.subheader(f"Set: {cards[0]['set']['name']}")
    
    # Hämta portföljen igen för att visa "Äger"-mängd live
    user_portfolio = get_user_portfolio(st.session_state.user_id)
    
    cols = st.columns(4)
    for idx, card in enumerate(cards):
        with cols[idx % 4]:
            # Kolla om vi äger kortet
            num_owned = 0
            if not user_portfolio.empty:
                num_owned = len(user_portfolio[user_portfolio['api_id'] == card['id']])
            
            # Badge för antal ägda
            if num_owned > 0:
                st.markdown(f"<div style='background: #1a231c; border: 1px solid #00ff88; color: #00ff88; padding: 4px; border-radius: 5px; text-align: center; font-weight: bold; margin-bottom: 5px;'>📦 Äger: {num_owned}</div>", unsafe_allow_html=True)
            else:
                st.markdown("<div style='height: 34px;'></div>", unsafe_allow_html=True)

            st.image(card['images']['small'], use_container_width=True)
            
            # Öppna dialogen vid klick på namnet/knappen
            if st.button(f"🔍 {card['name']}", key=f"inspect_{card['id']}", use_container_width=True):
                show_card_dialog(card)
                
            st.caption(f"#{card['number']} • {card['rarity'] if 'rarity' in card else ''}")
            st.divider()