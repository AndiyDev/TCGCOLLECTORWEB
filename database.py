import streamlit as st
from sqlalchemy import text
import bcrypt
import logging
from datetime import date

def get_conn():
    return st.connection("mysql", type="sql")

def init_db():
    conn = get_conn()
    with conn.session as s:
        try:
            s.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY, 
                    username VARCHAR(255) UNIQUE, 
                    password_hash VARCHAR(255)
                )
            """))
            s.execute(text("""
                CREATE TABLE IF NOT EXISTS collection (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    api_id VARCHAR(100),
                    item_name VARCHAR(255),
                    set_code VARCHAR(50),
                    card_number VARCHAR(50),
                    variant VARCHAR(50) DEFAULT 'Normal',
                    card_condition VARCHAR(20) DEFAULT 'NM',
                    quantity INT DEFAULT 1,
                    market_value DECIMAL(10, 2) DEFAULT 0.00,
                    purchase_price DECIMAL(10, 2) DEFAULT 0.00,
                    image_url VARCHAR(500),
                    is_graded BOOLEAN DEFAULT FALSE,
                    UNIQUE KEY unique_card (user_id, api_id, variant, is_graded),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            
            # --- Smarta kolumn-uppdateringar (Körs utan att krascha om de redan finns) ---
            alter_queries = [
                "ALTER TABLE collection ADD COLUMN grade_company VARCHAR(50)",
                "ALTER TABLE collection ADD COLUMN grade_value VARCHAR(10)",
                "ALTER TABLE collection ADD COLUMN cert_number VARCHAR(100)"
            ]
            for q in alter_queries:
                try:
                    s.execute(text(q))
                    s.commit()
                except Exception:
                    pass

            s.execute(text("""
                CREATE TABLE IF NOT EXISTS portfolio_history (
                    id INT AUTO_INCREMENT PRIMARY KEY, 
                    user_id INT, 
                    recorded_date DATE, 
                    total_value DECIMAL(10, 2), 
                    UNIQUE KEY unique_history (user_id, recorded_date),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
            s.execute(text("""
                CREATE TABLE IF NOT EXISTS wishlist (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    item_name VARCHAR(255) NOT NULL,
                    set_code VARCHAR(50),
                    card_number VARCHAR(50),
                    target_price DECIMAL(10, 2),
                    current_price DECIMAL(10, 2),
                    image_url VARCHAR(500),
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
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
        except Exception as e:
            logging.error(f"Databas initieringsfel: {e}")

def verify_user(username, password):
    conn = get_conn()
    with conn.session as s:
        res = s.execute(text("SELECT id, password_hash FROM users WHERE username = :u"), {"u": username}).fetchone()
        if res:
            if bcrypt.checkpw(password.encode(), res[1].encode()):
                return int(res[0])
    return None

def register_user(username, password):
    conn = get_conn()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with conn.session as s:
        try:
            s.execute(text("INSERT INTO users (username, password_hash) VALUES (:u, :p)"), {"u": username, "p": hashed})
            s.commit()
            return True
        except Exception:
            return False

def get_user_collection(uid):
    conn = get_conn()
    # ttl=0 tvingar Streamlit att strunta i cachen och alltid hämta live från MySQL
    return conn.query("SELECT * FROM collection WHERE user_id = :uid", params={"uid": uid}, ttl=0)

# UPPDATERAD: Tar nu in inköpspris och graderingsinfo
def add_to_collection(uid, api_id, name, set_c, num, val, img, var="Normal", qty=1, p_price=0.0, is_graded=False, g_comp=None, g_val=None, cert=None):
    conn = get_conn()
    with conn.session as s:
        # Om det är ett graderat kort, skapa alltid en ny rad (ignorera DUPLICATE KEY)
        if is_graded:
            s.execute(text('''
                INSERT INTO collection (user_id, api_id, item_name, set_code, card_number, market_value, purchase_price, image_url, variant, quantity, is_graded, grade_company, grade_value, cert_number)
                VALUES (:uid, :aid, :n, :sc, :num, :val, :pp, :img, :var, :q, :ig, :gc, :gv, :cert)
            '''), {"uid": uid, "aid": api_id, "n": name, "sc": set_c, "num": num, "val": val, "pp": p_price, "img": img, "var": var, "q": qty, "ig": True, "gc": g_comp, "gv": g_val, "cert": cert})
        else:
            s.execute(text('''
                INSERT INTO collection (user_id, api_id, item_name, set_code, card_number, market_value, purchase_price, image_url, variant, quantity, is_graded)
                VALUES (:uid, :aid, :n, :sc, :num, :val, :pp, :img, :var, :q, FALSE)
                ON DUPLICATE KEY UPDATE quantity = quantity + :q, purchase_price = purchase_price + :pp
            '''), {"uid": uid, "aid": api_id, "n": name, "sc": set_c, "num": num, "val": val, "pp": p_price, "img": img, "var": var, "q": qty})
        s.commit()

def delete_from_collection(cid, uid):
    conn = get_conn()
    with conn.session as s:
        s.execute(text("DELETE FROM collection WHERE id = :id AND user_id = :uid"), {"id": cid, "uid": uid})
        s.commit()

def update_quantity(uid, api_id, var, change):
    conn = get_conn()
    with conn.session as s:
        res = s.execute(text('''
            SELECT id, quantity FROM collection 
            WHERE user_id = :u AND api_id = :aid AND variant = :v AND is_graded = FALSE LIMIT 1
        '''), {"u": uid, "aid": api_id, "v": var}).fetchone()
        
        if res:
            new_qty = max(0, res[1] + change)
            if new_qty == 0:
                s.execute(text("DELETE FROM collection WHERE id = :id"), {"id": res[0]})
            else:
                s.execute(text("UPDATE collection SET quantity = :q WHERE id = :id"), {"q": new_qty, "id": res[0]})
            s.commit()

def get_portfolio_history(uid):
    conn = get_conn()
    return conn.query("SELECT recorded_date, total_value FROM portfolio_history WHERE user_id = :uid ORDER BY recorded_date", params={"uid": uid}, ttl=0)
    
def get_wishlist(uid):
    conn = get_conn()
    return conn.query("SELECT * FROM wishlist WHERE user_id = :uid", params={"uid": uid}, ttl=0)

def add_to_wishlist(uid, name, set_code, card_num, target, current, img):
    conn = get_conn()
    with conn.session as s:
        s.execute(text('''
            INSERT INTO wishlist (user_id, item_name, set_code, card_number, target_price, current_price, image_url)
            VALUES (:uid, :n, :sc, :c, :t, :curr, :img)
        '''), {"uid": uid, "n": name, "sc": set_code, "c": card_num, "t": target, "curr": current, "img": img})
        s.commit()

def delete_from_wishlist(wid, uid):
    conn = get_conn()
    with conn.session as s:
        s.execute(text("DELETE FROM wishlist WHERE id = :id AND user_id = :uid"), {"id": wid, "uid": uid})
        s.commit()

# Lägg till dessa funktioner längst ner i database.py
def add_sealed_product(uid, name, p_type, qty, p_price, m_val, img):
    conn = get_conn()
    with conn.session as s:
        s.execute(text('''
            INSERT INTO sealed_collection (user_id, product_name, product_type, quantity, purchase_price, market_value, image_url)
            VALUES (:uid, :n, :t, :q, :pp, :mv, :img)
        '''), {"uid": uid, "n": name, "t": p_type, "q": qty, "pp": p_price, "mv": m_val, "img": img})
        s.commit()

def get_user_sealed(uid):
    conn = get_conn()
    return conn.query("SELECT * FROM sealed_collection WHERE user_id = :uid", params={"uid": uid}, ttl=0)

def delete_sealed(sid, uid):
    conn = get_conn()
    with conn.session as s:
        s.execute(text("DELETE FROM sealed_collection WHERE id = :id AND user_id = :uid"), {"id": sid, "uid": uid})
        s.commit()

def get_user_id_by_name(username):
    conn = get_conn()
    with conn.session as s:
        res = s.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username}).fetchone()
        if res:
            return int(res[0])
    return None