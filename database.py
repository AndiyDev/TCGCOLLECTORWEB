import streamlit as st
from sqlalchemy import text
import pandas as pd

def get_conn():
    return st.connection("mysql", type="sql")

def init_db():
    conn = get_conn()
    with conn.session as s:
        # 1. Tabell för användare
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                password VARCHAR(255)
            )
        """))
        
        # 2. GLOBAL KATALOG (Här sparas kortdata bara en gång)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS global_cards (
                api_id VARCHAR(100) PRIMARY KEY,
                name VARCHAR(255),
                set_id VARCHAR(100),
                set_name VARCHAR(255),
                card_number VARCHAR(20),
                image_url VARCHAR(500),
                market_price DECIMAL(10, 2) DEFAULT 0.00,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """))
        
        # 3. ANVÄNDARENS KORT (Dina unika exemplar)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS user_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                api_id VARCHAR(100),
                variant VARCHAR(50) DEFAULT 'Normal',
                purchase_price DECIMAL(10, 2) DEFAULT 0.00,
                is_bought BOOLEAN DEFAULT TRUE,
                is_graded BOOLEAN DEFAULT FALSE,
                grade_company VARCHAR(20),
                grade_value VARCHAR(10),
                cert_number VARCHAR(50),
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (api_id) REFERENCES global_cards(api_id)
            )
        """))

        # 4. SEALED PRODUCTS (Behålls som förut men med user_id koppling)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS sealed_collection (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                product_name VARCHAR(255),
                product_type VARCHAR(50),
                quantity INT DEFAULT 1,
                purchase_price DECIMAL(10, 2) DEFAULT 0.00,
                market_value DECIMAL(10, 2) DEFAULT 0.00,
                image_url VARCHAR(500),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """))
        s.commit()

# --- LOGIK FÖR ATT LÄGGA TILL ---
def add_item_to_user(uid, card_data, variant, p_price, is_graded=False, g_comp=None, g_val=None, cert=None):
    conn = get_conn()
    with conn.session as s:
        # 1. Uppdatera/Spara i Global Katalog först
        s.execute(text("""
            INSERT INTO global_cards (api_id, name, set_id, set_name, card_number, image_url, market_price)
            VALUES (:aid, :n, :sid, :sn, :num, :img, :mp)
            ON DUPLICATE KEY UPDATE market_price = :mp, image_url = :img
        """), {
            "aid": card_data['id'], "n": card_data['name'], "sid": card_data['set']['id'],
            "sn": card_data['set']['name'], "num": card_data['number'], 
            "img": card_data['images']['small'], "mp": card_data.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
        })
        
        # 2. Skapa det unika exemplaret i användarens samling
        s.execute(text("""
            INSERT INTO user_items (user_id, api_id, variant, purchase_price, is_graded, grade_company, grade_value, cert_number)
            VALUES (:uid, :aid, :var, :pp, :ig, :gc, :gv, :cert)
        """), {
            "uid": uid, "aid": card_data['id'], "var": variant, "pp": p_price,
            "ig": is_graded, "gc": g_comp, "gv": g_val, "cert": cert
        })
        s.commit()

# --- HÄMTA PORTFÖLJ (Med JOIN för att få bild/namn från globala katalogen) ---
def get_user_portfolio(uid):
    conn = get_conn()
    query = """
        SELECT ui.*, gc.name, gc.image_url, gc.market_price, gc.set_name
        FROM user_items ui
        JOIN global_cards gc ON ui.api_id = gc.api_id
        WHERE ui.user_id = :uid
    """
    return conn.query(query, params={"uid": uid}, ttl=0)

# [Behåll dina funktioner för User login, Sealed, Wishlist och Profile name här under...]