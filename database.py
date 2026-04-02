import streamlit as st
import bcrypt
from sqlalchemy import text
import time

# --- ANSLUTNING ---
def get_conn():
    """Hanterar anslutningen till Streamlit MySQL."""
    return st.connection("mysql", type="sql")

# --- INITIALISERING ---
def init_db():
    """Skapar alla nödvändiga tabeller om de inte finns."""
    conn = get_conn()
    with conn.session as s:

        # 1. MASTER SETS (Bibliotekets mappar)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS global_sets (
                set_intern_id VARCHAR(50) PRIMARY KEY, 
                set_name VARCHAR(255),
                total_cards INT,
                symbol_path VARCHAR(500)
            )
        """))

        # 2. MASTER CARDS (Det globala arkivet med NM-priser)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS global_cards (
                api_id VARCHAR(100) PRIMARY KEY,
                set_intern_id VARCHAR(50),
                name VARCHAR(255),
                hp INT,
                card_number VARCHAR(20),
                image_url VARCHAR(500),
                price_normal_nm DECIMAL(10,2) DEFAULT 0,
                price_holo_nm DECIMAL(10,2) DEFAULT 0,
                price_reverse_nm DECIMAL(10,2) DEFAULT 0,
                is_holo TINYINT(1) DEFAULT 0,
                is_reverse TINYINT(1) DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (set_intern_id) REFERENCES global_sets(set_intern_id)
            )
        """))

        # 3. BOOSTER OPENINGS (Loggbok för öppnade paket)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS booster_openings (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                set_intern_id VARCHAR(50),
                purchase_price DECIMAL(10,2),
                date_opened TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 4. USER ITEMS (Dina specifika exemplar / Portfölj / Önskelista)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS user_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                unique_id VARCHAR(100) UNIQUE,
                user_id INT,
                api_id VARCHAR(100),
                opening_id INT DEFAULT NULL, 
                
                -- Status-flaggor
                variant VARCHAR(50) DEFAULT 'Normal',
                condition_rank VARCHAR(10) DEFAULT 'NM',
                is_bought TINYINT(1) DEFAULT 0,
                is_wishlist TINYINT(1) DEFAULT 0, -- ⭐ Här är din integrerade önskelista
                is_sold TINYINT(1) DEFAULT 0,     -- För budget-spårning
                
                -- Pris och Analys
                purchase_price DECIMAL(10,2) DEFAULT 0,
                sale_price DECIMAL(10,2) DEFAULT 0,
                user_image_url VARCHAR(500),
                detection_notes TEXT, 
                
                -- Spårning
                edit_count INT DEFAULT 0,         -- Max 2 ändringar per booster-innehåll
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                
                FOREIGN KEY (api_id) REFERENCES global_cards(api_id) ON DELETE CASCADE,
                FOREIGN KEY (opening_id) REFERENCES booster_openings(id) ON DELETE SET NULL
            )
        """))

        # 5. TRANSACTIONS (Budget och Historik)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS user_transactions (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT,
                trans_type ENUM('Inköp', 'Försäljning') NOT NULL,
                item_name VARCHAR(255),
                category EN_TYPE('Kort', 'Sealed', 'Booster', 'Annat'),
                amount DECIMAL(10,2),
                date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # 6. PRICE HISTORY (För grafer och trender)
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS price_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                api_id VARCHAR(100),
                price_nm DECIMAL(10,2),
                price_type ENUM('Normal', 'Holo', 'Reverse'),
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (api_id) REFERENCES global_cards(api_id) ON DELETE CASCADE
            )
        """))

        # 7. Users-tabellen
        s.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        s.commit()

# --- FUNKTIONER FÖR PORTFÖLJ ---

def add_item_to_user(user_id, api_id, variant='Normal', condition='NM', price=0, is_bought=0, opening_id=None, notes=None, is_wishlist=0):
    unique_id = f"USR{user_id}-{int(time.time())}"
    conn = get_conn()
    with conn.session as s:
        # HÄR ANVÄNDER VI PARAMETRAR (:uid, :user OSV)
        s.execute(text("""
            INSERT INTO user_items (unique_id, user_id, api_id, variant, condition_rank, purchase_price, is_bought, opening_id, detection_notes, is_wishlist)
            VALUES (:uid, :user, :api, :var, :cond, :price, :bought, :oid, :notes, :wish)
        """), {
            "uid": unique_id, "user": user_id, "api": api_id, "var": variant, 
            "cond": condition, "price": price, "bought": is_bought, "oid": opening_id, 
            "notes": notes, "wish": is_wishlist
        })
        s.commit()
    return unique_id

def delete_user_item(unique_id, user_id):
    conn = get_conn()
    with conn.session as s:
        # Mycket säkrare än f-strings
        s.execute(text("DELETE FROM user_items WHERE unique_id = :uid AND user_id = :user"), 
                  {"uid": unique_id, "user": user_id})
        s.commit()

def get_user_portfolio(user_id):
    """Hämtar hela samlingen med Master-data (Namn, Bild, Priser)."""
    conn = get_conn()
    query = """
        SELECT ui.*, gc.name, gc.image_url, gc.set_intern_id, 
               gc.price_normal_nm, gc.price_holo_nm, gc.price_reverse_nm
        FROM user_items ui
        JOIN global_cards gc ON ui.api_id = gc.api_id
        WHERE ui.user_id = :uid
        ORDER BY ui.date_added DESC
    """
    return conn.query(query, params={"uid": user_id}, ttl=0)

# --- FUNKTIONER FÖR BOOSTER-ÖPPNING ---

def create_booster_opening(user_id, set_id, price):
    """Skapar en post för en booster-öppning och loggar kostnaden."""
    conn = get_conn()
    with conn.session as s:
        result = s.execute(text("""
            INSERT INTO booster_openings (user_id, set_intern_id, purchase_price)
            VALUES (:uid, :sid, :price)
        """), {"uid": user_id, "sid": set_id, "price": price})
        opening_id = result.lastrowid
        log_transaction(user_id, 'Inköp', f"Booster: {set_id}", price)
        s.commit()
        return opening_id

def get_booster_details(opening_id):
    """Hämtar alla kort som hör till en specifik booster-öppning."""
    conn = get_conn()
    query = """
        SELECT ui.*, gc.name, gc.image_url, gc.price_normal_nm
        FROM user_items ui
        JOIN global_cards gc ON ui.api_id = gc.api_id
        WHERE ui.opening_id = :oid
    """
    return conn.query(query, params={"oid": opening_id}, ttl=0)

# --- FUNKTIONER FÖR BUDGET ---

def log_transaction(user_id, t_type, name, amount):
    """Loggar en pengatransaktion till budget-tabellen."""
    conn = get_conn()
    with conn.session as s:
        s.execute(text("""
            INSERT INTO user_transactions (user_id, trans_type, item_name, amount)
            VALUES (:uid, :type, :name, :amount)
        """), {"uid": user_id, "type": t_type, "name": name, "amount": amount})
        s.commit()

def get_financial_summary(user_id):
    """Hämtar totalt spenderat och totalt tjänat."""
    conn = get_conn()
    query = """
        SELECT 
            SUM(CASE WHEN trans_type = 'Inköp' THEN amount ELSE 0 END) as total_spent,
            SUM(CASE WHEN trans_type = 'Försäljning' THEN amount ELSE 0 END) as total_earned
        FROM user_transactions WHERE user_id = :uid
    """
    return conn.query(query, params={"uid": user_id}).iloc[0]

# Uppdaterad funktion i database.py
def create_booster_item(user_id, set_id, price, status='Sealed'):
    """Skapar en booster i databasen. Status kan vara 'Sealed' eller 'Opened'."""
    unique_pack_id = f"PACK{user_id}-{int(time.time())}"
    conn = get_conn()
    with conn.session as s:
        s.execute(text("""
            INSERT INTO booster_openings (unique_id, user_id, set_intern_id, purchase_price, status)
            VALUES (:uid, :user, :sid, :price, :status)
        """), {
            "uid": unique_pack_id, "user": user_id, "sid": set_id, "price": price, "status": status
        })
        s.commit()
    return unique_pack_id

def create_user(username, password):
    conn = get_conn()
    # Generera salt och hasha lösenordet
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    try:
        with conn.session as s:
            s.execute(text("INSERT INTO users (username, password_hash) VALUES (:u, :p)"),
                      {"u": username, "p": hashed.decode('utf-8')}) # Spara som string i DB
            s.commit()
        return True
    except Exception as e:
        print(f"Fel vid registrering: {e}")
        return False

def verify_user(username, password):
    conn = get_conn()
    res = conn.query("SELECT id, password_hash FROM users WHERE username = :u", 
                     params={"u": username})
    
    if not res.empty:
        stored_hash = res.iloc[0]['password_hash'].encode('utf-8')
        # Jämför det inskickade lösenordet med det lagrade hashet
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return res.iloc[0]['id']
    return None