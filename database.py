import streamlit as st
from sqlalchemy import text
import pandas as pd
import hashlib

def get_conn():
    return st.connection("mysql", type="sql")

# --- KRYPTERING FÖR LÖSENORD ---
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def init_db():
    conn = get_conn()
    with conn.session as s:
        # 1. Användare
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE,
                password VARCHAR(255)
            )
        """))
        
        # 2. Global Katalog
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
        
        # 3. Användarens objekt (Portfolio)
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

        # 4. Sealed Products
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

# --- INLOGGNINGSFUNKTIONER ---
def register_user(username, password):
    conn = get_conn()
    hashed = hash_password(password)
    with conn.session as s:
        try:
            s.execute(text("INSERT INTO users (username, password) VALUES (:u, :p)"), {"u": username, "p": hashed})
            s.commit()
            return True
        except:
            return False

def verify_user(username, password):
    conn = get_conn()
    hashed = hash_password(password)
    with conn.session as s:
        res = s.execute(text("SELECT id FROM users WHERE username = :u AND password = :p"), {"u": username, "p": hashed}).fetchone()
        return res[0] if res else None

def get_user_id_by_name(username):
    conn = get_conn()
    with conn.session as s:
        res = s.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username}).fetchone()
        return res[0] if res else None

# --- PORTFOLIO FUNKTIONER ---
def add_item_to_user(uid, card_data, variant, p_price, is_graded=False, g_comp=None, g_val=None, cert=None):
    conn = get_conn()
    with conn.session as s:
        s.execute(text("""
            INSERT INTO global_cards (api_id, name, set_id, set_name, card_number, image_url, market_price)
            VALUES (:aid, :n, :sid, :sn, :num, :img, :mp)
            ON DUPLICATE KEY UPDATE market_price = :mp, image_url = :img
        """), {
            "aid": card_data['id'], "n": card_data['name'], "sid": card_data['set']['id'],
            "sn": card_data['set']['name'], "num": card_data['number'], 
            "img": card_data['images']['small'], "mp": card_data.get('cardmarket', {}).get('prices', {}).get('averageSellPrice', 0.0)
        })
        
        s.execute(text("""
            INSERT INTO user_items (user_id, api_id, variant, purchase_price, is_graded, grade_company, grade_value, cert_number)
            VALUES (:uid, :aid, :var, :pp, :ig, :gc, :gv, :cert)
        """), {
            "uid": uid, "aid": card_data['id'], "var": variant, "pp": p_price,
            "ig": is_graded, "gc": g_comp, "gv": g_val, "cert": cert
        })
        s.commit()

def get_user_portfolio(uid):
    conn = get_conn()
    query = """
        SELECT ui.*, gc.name, gc.image_url, gc.market_price, gc.set_name
        FROM user_items ui
        JOIN global_cards gc ON ui.api_id = gc.api_id
        WHERE ui.user_id = :uid
    """
    return conn.query(query, params={"uid": uid}, ttl=0)

# --- SEALED FUNKTIONER ---
def get_user_sealed(uid):
    conn = get_conn()
    return conn.query("SELECT * FROM sealed_collection WHERE user_id = :uid", params={"uid": uid}, ttl=0)

def add_sealed_product(uid, name, p_type, qty, p_price, m_val, img):
    conn = get_conn()
    with conn.session as s:
        s.execute(text('''
            INSERT INTO sealed_collection (user_id, product_name, product_type, quantity, purchase_price, market_value, image_url)
            VALUES (:uid, :n, :t, :q, :pp, :mv, :img)
        '''), {"uid": uid, "n": name, "t": p_type, "q": qty, "pp": p_price, "mv": m_val, "img": img})
        s.commit()