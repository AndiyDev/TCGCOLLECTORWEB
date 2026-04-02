import streamlit as st
from database import get_user_portfolio, delete_user_item, get_conn
import pandas as pd

st.set_page_config(page_title="My Portfolio", page_icon="🎴", layout="wide")

# --- CSS FÖR EFFEKTER ---
st.markdown("""
<style>
    .card-container {
        position: relative;
        border-radius: 10px;
        overflow: hidden;
        transition: transform 0.3s;
    }
    .card-container:hover {
        transform: scale(1.03);
    }
    .holo-effect {
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        background: linear-gradient(125deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0) 100%);
        background-size: 200% 200%;
        animation: shine 3s infinite;
        pointer-events: none;
        z-index: 1;
    }
    @keyframes shine {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }
    .wishlist-tag {
        background-color: #FFD700;
        color: black;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 12px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- DIALOG: DETALJERAD VY ---
@st.dialog("Kortdetaljer & Hantering")
def show_card_details(card):
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.image(card['image_url'], use_container_width=True)
        st.caption(f"ID: {card['unique_id']}")
    
    with c2:
        st.header(card['name'])
        status = "⭐ Önskelista" if card['is_wishlist'] else "📦 I samlingen"
        st.subheader(status)
        
        st.write(f"**Set:** {card['set_intern_id']}")
        st.write(f"**Variant:** {card['variant']}")
        st.write(f"**Skick:** {card['condition_rank']}")
        
        st.divider()
        
        # Prisberäkning
        buy_p = float(card['purchase_price'] or 0)
        multipliers = {"NM": 1.0, "EX": 0.85, "GD": 0.70, "LP": 0.50, "PL": 0.25}
        
        # Hämta baspris baserat på variant
        if card['variant'] == 'Holo': base = float(card['price_holo_nm'] or 0)
        elif card['variant'] == 'Reverse': base = float(card['price_reverse_nm'] or 0)
        else: base = float(card['price_normal_nm'] or 0)
        
        current_val = base * multipliers.get(card['condition_rank'], 1.0)
        
        st.metric("Marknadsvärde", f"{current_val:.2f} SEK", delta=f"{current_val - buy_p:.2f} SEK" if not card['is_wishlist'] else None)
        
        # Åtgärder
        if card['is_wishlist']:
            if st.button("✅ Jag har köpt detta kort!", type="primary", use_container_width=True):
                # Här kör vi en SQL UPDATE för att ändra is_wishlist till 0 och is_bought till 1
                st.info("Uppdaterar status...")
                st.rerun()
        
        if st.button("🗑️ Ta bort helt", type="secondary", use_container_width=True):
            delete_user_item(card['unique_id'], st.session_state.user_id)
            st.rerun()

# --- HUVUDSIDA ---
st.title("🎴 Portfolio & Önskelista")

# Hämta all data för användaren
df = get_user_portfolio(st.session_state.user_id)

if df.empty:
    st.info("Din portfolio är tom. Börja med att lägga till kort eller fyll på din önskelista!")
else:
    # 1. Topp-statistik
    owned_count = len(df[df['is_wishlist'] == 0])
    wish_count = len(df[df['is_wishlist'] == 1])
    
    col_s1, col_s2, col_s3 = st.columns(3)
    col_s1.metric("Ägda Kort", owned_count)
    col_s2.metric("På Önskelistan", wish_count)
    
    st.divider()

    # 2. Tabbar för att separera Samling och Önskelista
    tab_owned, tab_wish = st.tabs(["📖 Min Pärm", "⭐ Önskelista"])

    def render_grid(data):
        if data.empty:
            st.write("Här var det tomt...")
            return
            
        cols = st.columns(4)
        for idx, row in data.reset_index().iterrows():
            with cols[idx % 4]:
                with st.container(border=True):
                    # CSS Wrapper för Holo
                    is_shiny = row['variant'] in ['Holo', 'Reverse']
                    
                    st.markdown('<div class="card-container">', unsafe_allow_html=True)
                    if is_shiny:
                        st.markdown('<div class="holo-effect"></div>', unsafe_allow_html=True)
                    
                    st.image(row['image_url'], use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    st.write(f"**{row['name']}**")
                    st.caption(f"#{row['card_number']} | {row['condition_rank']}")
                    
                    if st.button("Visa Detaljer", key=f"btn_{row['unique_id']}", use_container_width=True):
                        show_card_details(row)

    with tab_owned:
        render_grid(df[df['is_wishlist'] == 0])

    with tab_wish:
        render_grid(df[df['is_wishlist'] == 1])